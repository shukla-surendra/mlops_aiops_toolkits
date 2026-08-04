# EFS — Best practices, cost, monitoring & production

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** all prior EFS docs.

Spec sections 8, 9, 10, 11.

---

## 1. Best-practice checklist
- **Encrypt at rest** (KMS) at creation; **mount with `-o tls`** (efs-utils) for in-transit.
- **Elastic throughput + General Purpose** performance mode as the default.
- **Mount target per AZ**, SG allowing **2049 only from client SGs**.
- **Access Points** for per-app/per-container isolation (enforced uid + root dir); **IAM auth + filesystem policy** to scope who mounts.
- **Lifecycle Management** to tier cold files to IA/Archive.
- Use **`amazon-efs-utils`** (handles TLS/IAM/Access Points, DNS, retries) rather than raw `nfs4`.
- **One Zone** for non-critical/dev data to cut cost; **Standard** (multi-AZ) for anything needing AZ resilience.
- Drive **parallelism** for throughput; don't expect EBS-like single-op latency.
- IaC the filesystem, mount targets, SGs, access points.

## 2. Anti-patterns
| Anti-pattern | Why it hurts | Fix |
|---|---|---|
| EFS for a transactional DB | Per-op latency kills it | EBS io2 / Block Express |
| Millions of tiny files, serial access | Metadata latency compounds | Parallelize; reconsider S3 for objects |
| Open 2049 SG | Anyone in VPC mounts your data | SG from client SG only |
| Plain `nfs4`, no TLS | Cleartext data on wire | efs-utils `-o tls` |
| Bursting on a tiny filesystem | Low baseline → "slow" | Elastic throughput |
| Everyone mounts root | No tenant isolation | Access Points |
| Never tiering | Pay hot price for cold data | Lifecycle Management |
| Single mount target | Cross-AZ latency + AZ risk | One per AZ |

## 3. Cost model [Documented]

> **Read this as: the billing *model* is [Documented] and stable — the dollar *rates* are not here on purpose.**
> AWS changes prices and they vary by Region, so **never** hardcode a remembered EFS price. Pull current numbers live:
> - **Live pricing:** https://aws.amazon.com/efs/pricing/
> - **Model your workload:** https://calculator.aws/ (AWS Pricing Calculator)
> - **Your actual spend:** Cost & Usage Report / Cost Explorer, filtered by `usageType` (see the `usageType` list below).
> - **Docs:** [How EFS billing works](https://docs.aws.amazon.com/efs/latest/ug/how-billing-works.html) · [Storage classes & metering](https://docs.aws.amazon.com/efs/latest/ug/storage-classes.html)

**The core idea:** EFS bills for **what you *use* (storage) + what you *move* (throughput / retrieval)** — *not* provisioned capacity (the opposite of EBS). There are **three independent axes**:

### Axis 1 — Storage (per GB-month, metered, by storage class)
You pay for **actual GB stored** (metered hourly → GB-month), at a rate that depends on which class each *file* currently sits in:

| Class | Resilience | Storage rate | Read (retrieval) fee? |
|---|---|---|---|
| Standard | Multi-AZ | highest | none |
| Standard-IA | Multi-AZ | much lower | **yes — per-GB retrieval** |
| Archive | Multi-AZ | lowest (multi-AZ) | **yes — higher retrieval** |
| One Zone | Single-AZ | ~½ of Standard | none |
| One Zone-IA / -Archive | Single-AZ | lowest overall | **yes — retrieval** |

**Lifecycle Management** moves idle files to colder classes automatically. Transitioning *into* a colder class is free; reading cold data costs (Axis 3).

### Axis 2 — Throughput (billed by your **throughput mode**)
- **Elastic** (default/recommended) — **pay per GB read and written** (writes priced higher than reads); no baseline charge. Pay-per-use; ideal for spiky load, but a sustained high-throughput workload can make this the *largest* line item.
- **Bursting** — **no separate throughput charge**; throughput is *included* and scales with stored GB (baseline ∝ size + burst credits). You pay storage only.
- **Provisioned** — **pay per MB/s-month** for throughput you reserve, *above* the baseline your stored data already includes. For guaranteed high throughput on a small dataset.

### Axis 3 — Data movement
- **IA / Archive retrieval** — a **per-GB fee every time you read a tiered-cold file**. This is the tiering **gotcha**: a job that scans the whole cold set can cost more in retrieval than it saved in storage. Tiering rewards a *truly cold tail*, punishes *cold-but-scanned* data.
- **Cross-AZ data transfer** — mounting a mount target in a *different* AZ incurs normal EC2 cross-AZ transfer charges. Mount the **AZ-local** target (efs-utils/DNS does this by default) → free.

### Not billed
Mount targets (the ENIs), number of clients/connections, EFS control-plane API calls, and same-AZ data transfer.

### Illustrative worked example *(ratios only — verify current rates at the pricing link above)*
1 TB on **Standard**, ~500 GB read + 100 GB written/month via **Elastic**, AZ-local clients:
`storage (1000 GB) + throughput (500 GB read + 100 GB write) + $0 transfer`.
Enable **Lifecycle** and if 800 GB goes cold → most of that 1 TB now bills at the much-lower **IA** rate — **but only a net win if that cold data isn't frequently scanned** (retrieval fees would erode it).

### `usageType` strings to find in your CUR / Cost Explorer
`…-TimedStorage-ByteHrs` (Standard) · `…-IATimedStorage-ByteHrs` (IA) · `…-ArchiveTimedStorage-ByteHrs` · `…-IADataAccess-Bytes` (IA retrieval) · `…-ElasticThroughput-…Bytes` (Elastic read/write) · `…-ProvisionedTP-MiBpsHrs` (Provisioned). Exact strings vary by Region prefix — grep for `EFS`.

**Cost levers, ranked:** Lifecycle→IA/Archive (biggest, mind retrieval) · One Zone for non-critical · Elastic (pay-per-use) vs over-provisioned · AZ-local mounts.

## 4. Monitoring (CloudWatch) [Documented]
- `PercentIOLimit` (General Purpose) → near 100% = ops/sec ceiling.
- `BurstCreditBalance` (Bursting) → **alarm near 0** (about to throttle to baseline).
- `MeteredIOBytes` / `TotalIOBytes`, `ClientConnections`, `PercentOfProvisioned...` (Provisioned).
- `StorageBytes` (by class — track IA vs Standard split).
- Client-side: NFS latency, `nfsiostat`, mount errors in `dmesg`.

## 5. Production patterns
- **Containers (EKS/ECS):** EFS CSI driver + **Access Points** per app → shared, persistent, multi-AZ volumes with per-app isolation. The go-to for stateful pods needing shared/RWX storage.
- **Web/CMS fleet:** shared document root/media across an autoscaling group in multiple AZs.
- **ML/analytics:** shared training data/checkpoints read by many workers (though **FSx for Lustre** wins for extreme HPC throughput).
- **Lift-and-shift NAS:** replace an on-prem NFS filer with minimal app change.
- **Home directories / dev shares:** POSIX permissions, per-user Access Points.

## 6. Choosing EFS vs EBS vs FSx vs S3
- Shared **POSIX Linux** files, multi-AZ, elastic → **EFS**.
- One instance's disk / DB → **EBS**.
- Windows/SMB, HPC Lustre, ONTAP/OpenZFS features → **FSx**.
- Objects / data lake / backups → **S3**.

---

## Sources
- AWS docs: *EFS pricing*, *Lifecycle management*, *EFS CloudWatch metrics*, *EFS CSI driver*, *Choosing storage*.
- Well-Architected: *Cost* & *Performance* pillars; *Storage services comparison*.

---

## Self-check
1. Rank the top three cost levers for a mostly-cold EFS dataset, and name the gotcha of the biggest one.
2. Which throughput + performance mode combo is the modern default, and why?
3. For EKS pods needing shared RWX storage with per-app isolation, what's the pattern (two features)?
4. Which two metrics do you alarm on, and what does each protect against?
5. Give a one-line rule for EFS vs EBS vs S3 vs FSx.
