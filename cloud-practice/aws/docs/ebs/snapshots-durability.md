# EBS — Snapshots, durability & disaster recovery

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md) (single-AZ replication; snapshots live in S3).

Spec section 5 (durability/DR side). EBS is single-AZ; **snapshots are how you become multi-AZ and multi-Region durable.** This file is the backup/DR toolkit.

---

## 1. How snapshots really work [Documented]

- **Block-level, incremental, stored in S3** (AWS-managed buckets). First snapshot of a volume copies **all written blocks**; each later snapshot copies **only blocks changed since the previous** one and references the rest (a copy-on-write chain).
- **Deleting a snapshot is safe:** AWS only removes blocks *not* referenced by any other snapshot — you never corrupt the chain by deleting a middle snapshot.
- **Because the store is S3, snapshots are multi-AZ durable (11 nines class)** — independent of the volume's single-AZ risk. This is the escape hatch from EBS's AZ failure domain.
- **Restore = new volume, any AZ**, lazy-loading blocks from S3 on first access (→ [FSR](#4-fast-snapshot-restore-fsr) to avoid first-touch latency).

## 2. Consistency: crash vs application

- A snapshot is **crash-consistent**: a point-in-time image of the *block device*, equivalent to pulling power. Journaling filesystems recover fine; most databases recover via their WAL.
- **Application-consistent** needs a flush/quiesce first: freeze the filesystem (`fsfreeze`), flush DB buffers (`FLUSH TABLES WITH READ LOCK`, `pg_start_backup`/backup mode), or use crash-safe DB semantics. The block image alone can't know about dirty pages in the OS/DB cache.
- **Multi-volume consistency**: for a RAID/striped set or a DB spread across volumes, use **multi-volume snapshots** (one API call snapshots all attached volumes at the same instant) — otherwise the volumes' snapshots are from slightly different moments and won't reassemble cleanly.

## 3. Automating snapshots — Data Lifecycle Manager (DLM) [Documented]

- **DLM** runs **policy-based** snapshot schedules: "snapshot every volume tagged `Backup=true` every 12h, keep 14, copy to `us-west-2`." No Lambda/cron to maintain.
- Handles **retention** (count or age), **cross-Region/cross-account copy**, **fast-snapshot-restore**, and **archival**. This is the production-standard backup mechanism — hand-rolled snapshot scripts are an anti-pattern.

## 4. Fast Snapshot Restore (FSR) [Documented]

- Restored-from-snapshot volumes lazy-load from S3 → cold-block latency on first touch. **FSR** pre-provisions a snapshot in specific AZs so restored volumes are **full-performance immediately**.
- **Costs per-AZ, per-hour** while enabled — not free. Enable it for snapshots you restore under time pressure (AMIs for fast autoscaling, DR runbooks), not for everything.

## 5. Cross-Region / cross-account & archival

- **Copy snapshots cross-Region** for DR (and cross-account for sharing/isolation). Copy can **re-encrypt** with a different KMS key (required to share an encrypted snapshot — see [security.md](security.md)).
- **EBS Snapshots Archive**: move rarely-needed snapshots to a **cheaper archive tier** (lower storage cost, but restore takes hours and bills a retrieval). Good for long-term compliance retention; bad for active DR.
- **Recycle Bin**: retention rules that let you **recover deleted snapshots/AMIs** for a window — a guardrail against accidental/malicious deletion.

## 6. Durability numbers & DR patterns

- **AFR (annual failure rate)** [Documented]: gp2/gp3/st1/sc1 ≈ 0.1–0.2% (99.8–99.9%); **io2 / Block Express ≈ 0.001% (99.999%)**. "Durability" here = the *volume*; snapshots (S3) are far more durable and are your real backup.
- **DR ladder** (cheap→strong):
  1. **DLM snapshots in-Region** — recover from deletion/corruption; RPO = schedule interval.
  2. **Cross-Region snapshot copy** — survive a Region event; RPO = copy interval, RTO = restore + FSR.
  3. **Cross-Region + pre-baked AMIs + IaC** — fast rebuild in another Region.
  4. **App-level replication** (DB replica in another AZ/Region) — near-zero RPO, beyond EBS's job.
- **RAID note**: RAID 0 across EBS volumes boosts performance but multiplies failure probability and complicates consistent snapshots (quiesce or use multi-volume snapshots). RAID 1/5 on EBS is usually pointless — EBS already replicates within the AZ.

---

## Sources
- AWS docs: *EBS snapshots*, *Data Lifecycle Manager*, *Fast Snapshot Restore*, *EBS Snapshots Archive*, *Recycle Bin*, *Multi-volume snapshots*, *Crash consistency*.

---

## Self-check
1. Explain why deleting a *middle* snapshot in an incremental chain doesn't corrupt the others.
2. You snapshot a running MySQL volume with no prep and restore it — it mostly works but you're uneasy. What consistency level did you get, and what would make it application-consistent?
3. Your autoscaling group restores from a snapshot and the first minutes are slow. What's happening and which feature fixes it (and its cost catch)?
4. Design a 3-step DR posture for a single-AZ EBS-backed database that must survive a Region outage. State the RPO/RTO tradeoffs.
5. Why is RAID 1 across two EBS volumes usually redundant?
