# EBS — Performance: volume types, IOPS/throughput, and limits

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md) (the "network disk" model — performance is *provisioned quota*, not spindle physics).
> **Epistemics:** numbers are **[Documented]** from AWS docs but *change over time* — always confirm current limits.

Spec section 7. The mental frame: an EBS volume delivers I/O up to **min(what the volume is provisioned for, what the instance can push)**. Both halves matter — a 256k-IOPS volume on a small instance is throttled by the instance.

---

## 1. The volume types (know the decision cold)

| Type | Media | Best for | IOPS (max) | Throughput (max) | Notes |
|---|---|---|---|---|---|
| **gp3** | SSD | **Default** general purpose | 16,000 | 1,000 MB/s | IOPS + throughput **provisioned independently of size**; ~20% cheaper/GB than gp2 |
| gp2 | SSD | Legacy general purpose | 16,000 | 250 MB/s | IOPS tied to size (3 IOPS/GB), **burst bucket** for small volumes |
| **io2 Block Express** | SSD | Latency-critical DBs (SAP HANA, Oracle) | 256,000 | 4,000 MB/s | Up to 64 TiB, **sub-ms**, **99.999%** durability, 1000:1 IOPS:GB |
| io1 / io2 | SSD | Provisioned IOPS | 64,000 | 1,000 MB/s | io2 = higher durability + IOPS ratio than io1 |
| **st1** | HDD | Big **sequential** (logs, big-data, streaming) | 500 (1 MiB I/O) | 500 MB/s | Throughput-optimized; terrible at random/small I/O |
| sc1 | HDD | **Cold**, infrequent | 250 | 250 MB/s | Cheapest per GB |

**Default choice = gp3.** Move to io2/Block Express only when you need sustained high IOPS or sub-ms latency (databases). Use st1 for throughput-bound sequential workloads; sc1 for archival-ish block data.

### gp3's key innovation
gp2 ties performance to size (3 IOPS/GB) — to get more IOPS you over-provision GB you don't need. **gp3 decouples them**: baseline 3,000 IOPS + 125 MB/s free at any size, then dial IOPS (→16,000) and throughput (→1,000 MB/s) *independently*. **Migrating gp2→gp3 usually saves money and often adds performance** — a top low-effort cost win (see [best-practices.md](best-practices.md)).

---

## 2. IOPS vs throughput vs I/O size

- **IOPS** = operations/sec. **Throughput** = bytes/sec. They're linked by **I/O size**: `throughput ≈ IOPS × IO_size`, capped by whichever ceiling you hit first.
- EBS SSD counts I/O in up to **256 KiB** chunks; HDD (st1/sc1) in **1 MiB** chunks. A 512 KiB SSD write = 2 IOPS. Larger I/Os = more throughput per IOP → **small random I/O is IOPS-bound; large sequential I/O is throughput-bound.**
- **Queue depth matters:** EBS is a networked store with latency; to reach high IOPS you need enough *outstanding* I/O (parallelism). A single-threaded `dd` won't saturate a 16k-IOPS volume; `fio --iodepth=32` will. Rule of thumb: `IOPS ≈ queue_depth / latency`.

---

## 3. Burst (the gp2/HDD gotcha)

- **gp2**: volumes < 1 TiB get a baseline of 3 IOPS/GB but can **burst to 3,000 IOPS** by spending **I/O credits** from a bucket that refills at the baseline rate. Sustained load past baseline **drains the bucket** → performance cliff. The **`BurstBalance`** CloudWatch metric hitting 0 is a classic "why did my small gp2 volume get slow" incident. **gp3 has no burst** — it's flat provisioned (simpler, predictable).
- **st1/sc1**: throughput works on a similar **credit** model (burst throughput above baseline, refilling with size). Great for bursty sequential reads, bad for sustained.

---

## 4. The instance-side ceiling (the half everyone forgets)

Each instance type has a **maximum EBS bandwidth and IOPS** (published per family/size), delivered over the Nitro data path. [Documented]
- Your volume can be provisioned huge, but **the instance caps aggregate EBS I/O across all its volumes.** A `db.large` can't push a Block Express volume's full 256k IOPS.
- **EBS-optimized**: on Nitro this is inherent (dedicated EBS bandwidth). On old instances it was a paid toggle. Choose an instance whose EBS ceiling matches your storage need — this is a real sizing step for DB hosts.
- Watch **`VolumeThroughputPercentage`** / instance-level EBS metrics to see if you're hitting the *instance* ceiling vs the *volume* ceiling.

---

## 5. Multi-Attach (io2) [Documented]

- `io2` (and io1) support **Multi-Attach**: one volume attached to **up to 16 instances in the same AZ** simultaneously, all with read/write.
- **Requires a cluster-aware filesystem** (GFS2, OCFS2) or an app that coordinates access. **ext4/xfs are NOT cluster-aware** — mounting a Multi-Attach volume on two nodes with xfs = **corruption**. Multi-Attach gives you shared *block* access, not a shared *filesystem*; the coordination is your job.
- Still **single-AZ**. For shared file access across instances/AZs, that's **EFS**, not EBS Multi-Attach — a key exam/interview distinction.

---

## 6. Elastic Volumes & initialization

- **Elastic Volumes** [Documented]: modify **size, type, IOPS, throughput live** — no detach, usually no downtime. After a change there's an **optimization period** (background migration) during which performance is intermediate. Growing the *volume* doesn't grow the *filesystem* — you still run `growpart` + `resize2fs`/`xfs_growfs` in the guest.
- **Initialization / lazy load**: a volume **created from a snapshot** loads blocks from S3 **on first access** → the first read of each block is slow. Old fix: "pre-warm" by reading the whole disk (`dd`/`fio`). Modern fix: **Fast Snapshot Restore (FSR)** — pre-provisions the snapshot so restored volumes are full-performance instantly (costs per-AZ-per-hour; see [snapshots-durability.md](snapshots-durability.md)).

---

## Sources
- AWS docs: *Amazon EBS volume types*, *EBS volume performance on Linux*, *Amazon EBS–optimized instances*, *Multi-Attach*, *Elastic Volumes*.
- re:Invent: *"Deep dive on Amazon EBS"* (STG track, updated yearly).

---

## Self-check
1. Your DB does tiny random reads and is slow despite a 16k-IOPS gp3 volume. Name two things (one volume-side, one instance/OS-side) that could be the real bottleneck.
2. Why does gp3 usually beat gp2 on both cost and performance? What did gp3 decouple?
3. A small gp2 volume is fast for 20 minutes then crawls. Which metric confirms the cause and why?
4. Two EC2 nodes mount the same io2 Multi-Attach volume with xfs and data corrupts. What did the team misunderstand about Multi-Attach?
5. You grew a volume from 100→500 GiB but `df` still shows 100 GiB. What's left to do and why doesn't EBS do it for you?
