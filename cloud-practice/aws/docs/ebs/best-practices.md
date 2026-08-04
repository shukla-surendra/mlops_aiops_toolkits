# EBS — Best practices, cost, monitoring & production

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** all prior EBS docs.

Spec sections 8, 9, 10, 11.

---

## 1. Best-practice checklist

- **gp3 as the default** boot/data volume; io2/Block Express for latency-critical DBs; st1 for throughput/log workloads; sc1 for cold.
- **Encryption by default ON** (account/Region), customer-managed KMS key for anything you may share.
- **Right-size the instance's EBS ceiling** to the volume (a fast volume on a small instance is throttled).
- **Automate backups with DLM** (tag-driven), retention + cross-Region copy for DR. No hand-rolled snapshot cron.
- **`DeleteOnTermination`**: set intentionally — usually `true` for boot, often `false` for data volumes you don't want auto-deleted.
- **Grow the filesystem** after Elastic Volume resize (`growpart` + `resize2fs`/`xfs_growfs`).
- **Tag everything** (`Backup`, `Environment`, `Owner`) — drives DLM + cost allocation + cleanup.
- **Monitor burst (gp2), queue length, and throughput %**; alarm before the cliff.
- **IaC all of it**; never hand-attach production volumes.

## 2. Anti-patterns

| Anti-pattern | Why it hurts | Fix |
|---|---|---|
| Still on gp2 | Pays more, bursts to a cliff | Migrate gp2→gp3 (live, cheaper, faster) |
| Over-provisioned io2 "to be safe" | Provisioned IOPS are expensive | Measure, right-size; gp3 covers most |
| Hand-rolled snapshot scripts | Drift, gaps, no retention | DLM policies |
| Assuming volume = backup | Single-AZ; AZ loss = gone | Snapshots (S3) + cross-Region copy |
| Orphaned volumes/snapshots | Silent cost + data exposure | Lifecycle cleanup + Recycle Bin |
| RAID for durability on EBS | EBS already replicates in-AZ | RAID 0 only for perf, with care |
| Ignoring instance EBS ceiling | Volume throttled, "EBS is slow" | Match instance family/size |
| ext4/xfs on Multi-Attach | Corruption | Cluster FS or don't Multi-Attach |

## 3. Cost model (what actually bills) [Documented]

> **The billing *model* below is [Documented] and stable; *rates* change and vary by Region — verify live, never hardcode a remembered price:**
> **Live pricing:** https://aws.amazon.com/ebs/pricing/ · **Calculator:** https://calculator.aws/ · **Your spend:** Cost Explorer / CUR by `usageType` (see below).

Unlike EFS (which bills *used* storage), **EBS bills *provisioned* capacity.** The big ones [Documented]:

1. **Provisioned capacity, per GB-month, by type** — you pay for **provisioned size, not used** (a 500 GiB volume 10% full bills 500 GiB). Thin-provision by right-sizing + Elastic Volumes.
2. **Provisioned IOPS/throughput** — io1/io2 bill per provisioned IOPS; gp3 bills extra IOPS/throughput **above** the 3,000/125 baseline. Don't over-dial.
3. **Snapshots** — per GB-month of **incremental changed blocks** in S3 (cheap-ish, but **orphaned snapshots pile up**). Archive tier for cold retention; Recycle Bin has cost too.
4. **FSR** — **per-AZ, per-hour** while enabled. Easy to forget and expensive; enable only where restore speed matters.
5. **gp2→gp3 migration** is usually a straight cost cut *and* perf gain — do it first.
6. There's **no data-transfer charge** for I/O to a volume in the same AZ (unlike NAT/cross-AZ), but cross-AZ/Region **snapshot copy** transfers bill.

**Watch cost via** Cost Explorer / CUR `usageType` (`EBS:VolumeUsage.gp3`, `EBS:SnapshotUsage`, `EBS:VolumeP-IOPS`, `EBS:FastSnapshotRestore`). Alarm on unexpected FSR + snapshot growth.

## 4. Monitoring (CloudWatch) [Documented]

Key EBS metrics:
- `VolumeReadOps` / `VolumeWriteOps` → IOPS.
- `VolumeReadBytes` / `VolumeWriteBytes` → throughput.
- `VolumeQueueLength` → outstanding I/O; **high + high latency = saturated** (need more IOPS or bigger instance).
- `VolumeTotalReadTime` / `WriteTime` → latency.
- `BurstBalance` (gp2/st1/sc1) → **alarm near 0** (burst about to run out).
- `VolumeThroughputPercentage` / `VolumeConsumedReadWriteOps` (io1/io2) → how close to provisioned.
- Instance-level EBS metrics (`EBSIOBalance%`, `EBSByteBalance%` on smaller instances) → **instance ceiling** pressure.

Alarms worth having: `BurstBalance < 20%`, sustained `VolumeQueueLength` high, io2 `VolumeThroughputPercentage` ~100% (under-provisioned).

## 5. Production patterns

- **Relational DB (self-managed):** io2 Block Express (sub-ms, 99.999%), instance with matching EBS bandwidth, DLM app-consistent snapshots (quiesce), cross-Region copy for DR.
- **Boot volumes / fleet:** gp3, baked into AMIs (snapshot-backed), FSR on the AMI snapshot for fast autoscaling.
- **Big-data / log ingest:** st1 for cheap sequential throughput; RAID 0 across st1 for more.
- **Clustered app needing shared block:** io2 Multi-Attach + cluster FS (rare) — usually EFS is the better answer.
- **Everything:** encryption by default, tag-driven DLM, IaC, right-sized instance ceiling.

---

## Sources
- AWS docs: *EBS pricing*, *EBS CloudWatch metrics*, *Monitoring the status of your volumes*, *Cost optimization for EBS*.
- Well-Architected: *Cost Optimization* & *Performance Efficiency* pillars.

---

## Self-check
1. A 1 TiB gp3 volume is 5% used. What are you billed for, and how would you cut it?
2. Which two metrics together tell you a volume is saturated vs. the *instance* being the bottleneck?
3. Name the low-effort change that usually cuts cost *and* raises performance simultaneously.
4. Your bill has a growing `FastSnapshotRestore` line. What is it, why is it easy to leave on, and when is it justified?
5. Design monitoring for a self-managed Postgres on io2: which 3 alarms do you set and why?
