# EFS — Module 1: Why it exists, the mental model, and the internal architecture

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Epistemics:** **[Documented]** = AWS docs / re:Invent · **[Inferred]** = reconstruction from behavior + standard distributed-FS designs.
> **Read EBS first** — [EBS docs](../ebs/README.md). EFS is best understood as *the opposite design choices* from EBS.

**Scope:** spec sections 1–3 + 17. Why EFS exists, the mental model, and the internal architecture (multi-AZ distributed file system, mount targets as per-AZ ENIs, NFS v4.1, metadata).

---

## 1. Why does EFS exist?

### The problem in one sentence
Many instances (across AZs) need to read and write the **same files** through a normal **POSIX filesystem** — and EBS can't do that (single-attach, single-AZ) and S3 can't do that (object API, not a filesystem).

### The gap EBS and S3 leave
- **EBS** = block, single-attach, single-AZ. Great for one instance's disk; useless as shared storage for a fleet.
- **S3** = object, HTTP API, eventually-eventually-now-strong, but **not a filesystem** — no `open()/write()/rename()`, no POSIX permissions, no in-place partial writes with file semantics.
- Real workloads need shared files: web content across an autoscaling fleet, container persistent volumes, home directories, ML training data read by many workers, lift-and-shift apps that expect a mounted NAS.

### History: NAS and self-managed NFS
On-prem, this was a **NAS** — a NetApp/EMC **filer** exporting **NFS** (Linux) or **SMB** (Windows). In early cloud you'd **run your own NFS server on EC2**: one instance with a big EBS volume exporting NFS. That's a **single point of failure**, a scaling ceiling (one box's CPU/network/EBS), and an ops burden (failover, capacity, patching).

### Why AWS built EFS (2016)
**EFS is a fully-managed, elastic, multi-AZ NFS filesystem.** You get an NFS endpoint; AWS runs the distributed storage behind it. It **grows and shrinks automatically** (no provisioning), is **redundant across AZs** (Standard class), and is mounted **concurrently by thousands of clients** across AZs. It replaces "run your own NFS filer" the way RDS replaced "run your own database."

### What if EFS didn't exist?
- Shared-file workloads = self-managed NFS (SPOF) or awkward S3-as-filesystem hacks (`s3fs`, sync jobs).
- No easy persistent shared volume for containers across AZs.
- Lift-and-shift of NAS-dependent apps would need re-architecting.

---

## 2. The core mental model

> **EFS is a distributed, multi-AZ filesystem that you reach through a per-AZ NFS door (a "mount target" — an ENI with an IP in your subnet).** You mount it like any NFS share; behind the door is a massive distributed storage system spanning multiple AZs, with capacity and throughput that scale automatically.

Contrast the three storage models — this is the whole reason to study EBS + EFS together:

| | **EBS** | **EFS** | **S3** |
|---|---|---|---|
| Interface | Block (NVMe) | **File (POSIX / NFS v4.1)** | Object (HTTP) |
| Sharing | 1 instance | **Thousands, concurrent** | Any (API) |
| AZ scope | **Single-AZ** | **Multi-AZ** (Standard) | Regional |
| Capacity | Provisioned | **Elastic (auto)** | Elastic |
| Latency | Low (network block) | Higher (network file, per-op ~ms) | Highest |
| Pay for | Provisioned GB | **GB used** | GB stored + requests |
| Best for | One box's disk, DBs | Shared files, containers, NAS | Objects, backups, data lake |

Key consequences of the model:
- **Every file op is an NFS round trip** over the network to a mount target → **per-operation latency is higher than EBS**, and **metadata-heavy / tiny-file workloads feel it most**. EFS is not where you put a latency-critical transactional DB (that's EBS io2).
- **Throughput scales with the filesystem** (and with the throughput mode) — it's a *distributed* system, so aggregate throughput across many clients can be very high even though single-op latency is modest.
- **You pay for what you use**, not what you provision (opposite of EBS).

---

## 3. Internal architecture

### 3a. Mount targets — the per-AZ entry point [Documented]
- You create **one mount target per AZ**, each an **ENI with an IP in one of your subnets**. Clients in that AZ mount the filesystem via its DNS name, which resolves to the **AZ-local mount target IP** (so traffic stays in-AZ where possible — latency + cross-AZ cost).
- A **Security Group** on the mount target gates **NFS (TCP 2049)** — this is how you control who can mount (see [security.md](security.md)).
- The mount target is just the door; the **actual data is not "on" the mount target** — it's in the distributed storage fleet behind it (same spirit as EBS: the volume isn't on your host).

### 3b. Multi-AZ redundancy [Documented]
- **Standard** storage class stores data **redundantly across multiple AZs** in the Region — so an AZ failure doesn't lose data *or* (for clients in surviving AZs) availability. This is the headline difference from EBS's single-AZ.
- **One Zone** storage class stores data in a **single AZ** (cheaper ~½) — you trade AZ-resilience for cost, like a "budget" EFS. Good for dev, or data you can reconstruct.

### 3c. The distributed filesystem [Documented that it's distributed + strongly consistent for many ops; internals Inferred]
- Data **and metadata** are spread across a large fleet of storage servers across AZs, with replication for durability. **Metadata (the directory tree, inodes, locks) is the hard part** of any distributed filesystem — it must stay consistent while thousands of clients create/rename/delete concurrently.
- **Consistency:** EFS provides **strong read-after-write consistency for most operations** and follows **NFS close-to-open** semantics (a client that closes a file, then another opens it, sees the writes). It's far stronger than "eventually consistent" object stores. [Documented: read-after-write consistency; close-to-open is the NFS model.]
- **Scaling:** because it's distributed, capacity is effectively unbounded and **throughput grows with the dataset** (Bursting) or on demand (Elastic) — no single filer bottleneck. [Documented behavior]

### 3d. NFS v4.1 & the client [Documented]
- EFS speaks **NFS v4.1**. On Linux you mount with the **`amazon-efs-utils`** package (the `efs` mount type), which adds conveniences: **in-transit TLS** (via a local stunnel), IAM authorization, and **Access Point** integration. Plain `nfs4` mounts also work but without those extras.
- Because it's standard NFS, POSIX permissions, file locking, and normal filesystem syscalls "just work" for apps that expect a filesystem.

---

## 4. Where EFS fits vs its cousins

- **EFS** — Linux/NFS, multi-AZ, elastic, general shared files & containers.
- **FSx** — managed file systems for other needs: **FSx for Windows** (SMB/AD), **FSx for Lustre** (HPC/ML high-throughput, S3-linked), **FSx for NetApp ONTAP** / **OpenZFS** (enterprise NAS features). Reach for FSx when you need Windows/SMB, extreme HPC throughput, or ONTAP features.
- **EBS** — one instance's block disk / databases.
- **S3** — objects, data lake, backups (EBS snapshots live here).

EFS is the answer to "I need a shared POSIX filesystem for many Linux clients across AZs, managed."

---

## Sources
- AWS docs: *How Amazon EFS works*, *EFS storage classes*, *Mount targets*, *EFS performance*, *amazon-efs-utils*.
- re:Invent: *"Deep dive on Amazon EFS"* (STG track).
- Contrast reading: [EBS architecture](../ebs/architecture.md) — the opposite design point.

---

## Self-check
1. Give the one-sentence reason EFS exists that neither EBS nor S3 can satisfy, and why each falls short.
2. What is a mount target, physically, and what controls who can mount through it?
3. Standard vs One Zone — what exactly are you trading, and when is One Zone acceptable?
4. Why does EFS have higher per-operation latency than EBS, and what workload characteristic makes that latency most painful?
5. EFS is "strongly consistent (read-after-write) with close-to-open semantics." Explain close-to-open in a two-client scenario.
