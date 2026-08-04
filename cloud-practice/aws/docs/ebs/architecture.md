# EBS — Module 1: Why it exists, the mental model, and the internal architecture

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Epistemics:** **[Documented]** = AWS docs / re:Invent / the Physalia paper · **[Inferred]** = reconstruction from behavior + standard designs.
> **Related:** the Nitro data-plane story from [VPC internals](../vpc/internals.md) is the same silicon that presents EBS as NVMe.

**Scope:** spec sections 1–3 + 17. Why EBS exists, the one mental model that unlocks it, and the internal architecture (in-AZ replication, control/data plane, Nitro NVMe, the Physalia control-plane database, and the 2011 outage as a design lesson).

---

## 1. Why does EBS exist?

### The problem in one sentence
A virtual machine needs a disk that is **durable, persistent across the instance's life, detachable/reattachable, snapshottable, and resizable** — none of which a physical disk bolted inside the host can provide in a fleet where instances come and go and hosts fail.

### History: instance store (ephemeral) was all you had
Early EC2 (2006) gave you only **instance store** ("ephemeral disk") — physical disks *local to the host* your VM landed on. Fast, but:
- **Ephemeral:** stop or terminate the instance, or lose the host → **data gone**. It doesn't survive a stop/start (which moves you to a new host).
- **Not detachable:** the disk is welded to that host; you can't move it to another instance.
- **No snapshots, no resize, no independent lifecycle.**

That's fine for scratch/cache, useless for a database or anything you care about.

### How companies solved this before the cloud
On-prem, "durable block storage" meant a **SAN** (Storage Area Network): a dedicated array (NetApp, EMC, Dell) exporting block volumes (**LUNs**) to servers over **Fibre Channel** or **iSCSI**. The server sees a block device; the array handles RAID, replication, snapshots. Powerful but: expensive, specialized hardware, capacity you buy up front, and a team to run it. **DAS** (direct-attached disks) was cheaper but non-shared and non-durable — the instance-store problem.

EBS is, essentially, **"a SAN as a service"**: network-attached block volumes with array-class features (snapshots, replication, resize), billed per-GB-month, provisioned by an API call.

### Why instance store was insufficient
1. **Durability/lifecycle:** real workloads need data that outlives the instance and survives host failure.
2. **Mobility:** detach a volume from a dead instance, attach to a replacement — keep the data.
3. **Operations:** snapshots for backup/clone/DR; resize without downtime; change performance on the fly.
4. **Elasticity:** provision 16 TiB in seconds via API instead of racking disks.

### Why AWS built EBS (2008)
To give every instance a **network-attached, durable, API-managed block device** that behaves like a local disk but has the lifecycle of a managed service — decoupling *storage* from *compute* so each can fail, scale, and be replaced independently. This decoupling is the same philosophy as VPC decoupling the network from the host: **virtualize the resource, run it as a distributed service, present it through a familiar interface.**

### What if EBS didn't exist?
- No stateful workloads on EC2 without building your own replicated storage.
- No boot volumes that survive stop/start; no "stop to save money, start later" for stateful boxes.
- No snapshots → no easy backup/DR/AMI pipeline (AMIs are backed by EBS snapshots).
- Databases would run on ephemeral disk with app-level replication as the only safety net.

EBS is what makes EC2 usable for anything that remembers.

---

## 2. The core mental model — burn this in

> **An EBS volume is not a disk. It is a network storage service that impersonates a local disk.** The blocks live on a fleet of remote storage servers across the AZ; your instance reaches them over the network; the Nitro card makes it look like an NVMe drive plugged into the PCIe bus.

This is the exact sibling of the VPC insight. VPC faked a *network*; EBS fakes a *disk*. Consequences that fall straight out of this one idea:

- **Every read/write is a network round trip** to the storage fleet (that's why EBS latency > instance-store latency, and why "EBS-optimized" bandwidth and Nitro matter).
- **The volume survives the instance** because the data was never on the instance's host in the first place.
- **You can detach and re-attach** — you're just repointing which instance is allowed to talk to that remote volume.
- **An AZ is the failure/availability domain.** The volume's replicas live within *one* AZ (see §3). That's why EBS is single-AZ and why you replicate *across* AZs at a higher layer (or via snapshots).
- **Performance is provisioned, not physical** — IOPS/throughput are quotas the service enforces, not properties of a spindle.

```
  What the OS believes                     What is actually happening
  ┌────────────────────┐                   ┌──────────────────────────────────┐
  │  /dev/nvme1n1       │                   │  Instance (Nitro card) ── network │
  │  a local NVMe disk  │  ═══ Nitro ═══►   │   │                              │
  │  4 TiB, 16k IOPS    │                   │   ▼  (in-AZ storage fabric)       │
  └────────────────────┘                   │  Storage srv A (primary) ⇄ srv B  │
                                            │   replicated copies of your blocks │
                                            └──────────────────────────────────┘
```

---

## 3. Internal architecture

### 3a. Replication: the volume is (at least) two copies in one AZ [Documented]
An EBS volume's data is **replicated synchronously across multiple storage servers within a single Availability Zone** — classically a **primary** replica and a secondary, on different servers/racks. A write is acknowledged to the instance **only after it's durably on the replicas**, so a single server or disk failure loses nothing.

- **Failure recovery = re-mirroring:** if a replica's server dies, EBS creates a fresh replica on another server from the surviving copy. During heavy re-mirroring the volume can see degraded performance (and, historically, worse — see §4).
- **Single-AZ by design:** replicas are all in one AZ → **an AZ failure can make a volume unavailable**. EBS trades cross-AZ durability for low, consistent write latency (cross-AZ synchronous replication would add milliseconds to every write). Cross-AZ/region durability is your job, via **snapshots** (which go to S3, which *is* multi-AZ) or app-level replication.
- **Durability numbers** [Documented]: gp2/gp3/st1/sc1 ≈ **99.8–99.9%** annual (≈0.1–0.2% AFR); **io2 / io2 Block Express ≈ 99.999%** — achieved with more replicas / stronger placement.

### 3b. Control plane vs data plane
Same split as everywhere (and the reason for the whole VPC analogy):
- **Data plane** — the storage servers + the network path that serve reads/writes at low latency. Must keep serving even when the control plane is busy.
- **Control plane** — creates/attaches/detaches volumes, drives placement, orchestrates re-mirroring, tracks *which servers hold which replicas and who is primary*. This last job — the **volume→server configuration and leadership** — is the hard, safety-critical part, and it has its own dedicated system: **Physalia** (§3d).

### 3c. Nitro: how the remote volume looks local [Documented]
On Nitro instances, an **EBS volume is presented to the guest as an NVMe block device** by the Nitro card. The card:
- terminates the NVMe commands from the guest and translates them into network I/O to the EBS storage fleet,
- handles **encryption** (AES-256, transparent, at line rate) so encrypted volumes cost ~no CPU,
- enforces the volume's **provisioned IOPS/throughput** limits,
- is why modern instances get high, consistent EBS performance without a "software" I/O tax.

Pre-Nitro, EBS attached over the network via software in the hypervisor (Xen), which was slower and noisier. "EBS-optimized" used to be a paid feature carving out dedicated bandwidth; on Nitro it's inherent.

### 3d. Physalia — the control-plane brain (and a great systems lesson) [Documented — NSDI 2020 paper "Millions of Tiny Databases"]
The most interesting internal piece. EBS must always know, for every volume, **which storage servers hold the replicas and which is the primary** — and it must update this correctly during failures *without* a giant shared database whose failure takes down the whole Region.

**Physalia** is AWS's answer: a database of **millions of tiny Paxos-replicated databases** ("cells"), one managing the configuration for a small set of volumes. Key ideas worth stealing for your own designs:
- **Consensus (Paxos) per cell** → the config for a volume is agreed by a small quorum, so leadership/placement decisions are consistent even during partitions.
- **Colocation for blast-radius reduction:** each tiny database is placed *close (in the network topology) to the data it describes*, so the failures that would partition the data are the same failures that partition its config — they fail together, not independently. This deliberately shrinks the blast radius.
- **Millions of small failure domains** instead of one big one: a problem takes out a few cells, not the Region.

This design was a direct response to the **2011 outage** (§4). It's a canonical example of *control-plane design for blast-radius containment* — bring it up in any "design a control plane" interview.

### 3e. Snapshots — incremental block backups to S3 [Documented]
- A snapshot is a **block-level, incremental** copy of the volume stored in **S3** (in AWS-managed buckets you don't see). The **first** snapshot copies all written blocks; each subsequent snapshot copies **only changed blocks** and references unchanged ones (copy-on-write chain).
- Because the backing store is **S3, snapshots are multi-AZ durable** — this is how you escape EBS's single-AZ limitation for backup/DR. Copy a snapshot to another Region for DR; create a new volume in any AZ from a snapshot.
- Snapshots are **crash-consistent** at the block layer (a point-in-time image). For **application-consistent** snapshots (databases), you quiesce/flush first (e.g., freeze the filesystem, or use DB-aware tooling), because the block image alone doesn't know about in-flight writes in the OS page cache.
- **AMIs are built on EBS snapshots** — the whole "golden image" pipeline sits on this.

---

## 4. The 2011 EBS outage — what happens when this goes wrong [Documented]

In April 2011 a network configuration change in one AZ caused a large set of EBS nodes to lose connectivity to their replicas. They all tried to **re-mirror simultaneously**, creating a "**re-mirroring storm**" that exhausted spare capacity; the control plane got overwhelmed, and volumes across the Region were impacted for days. Lessons AWS internalized (and you should):
- **Correlated failure + automatic recovery can amplify, not dampen** (a thundering herd of re-mirrors).
- **Control planes need blast-radius containment** → led to designs like **Physalia**.
- **Single-AZ dependency is real** → replicate across AZs at your layer; don't assume a volume is Regionally safe.

This incident is *the* reason to know EBS is single-AZ in your bones.

---

## 5. Where EBS sits vs. its neighbors (preview)

| | **EBS** | **Instance store** | **EFS** | **S3** |
|---|---|---|---|---|
| Type | Block | Block (local) | File (NFS) | Object |
| Attaches to | 1 instance (io2 multi-attach: few) | 1 host | Many instances | HTTP API |
| Scope | **Single-AZ** | Single host | **Multi-AZ** | Regional (multi-AZ) |
| Persistence | Survives instance | Ephemeral | Survives, shared | Durable 11 9s |
| Latency | Low (network block) | Lowest (local) | Higher (network file) | Highest (object) |

EFS (next service) is the multi-AZ, shared, POSIX file counterpart — a completely different internal design. That contrast is the whole point of studying them together.

---

## Sources
- **Paper:** Brooker, Chen, Ping — *"Millions of Tiny Databases"*, NSDI 2020 (Physalia). **Read this.**
- re:Invent: *"Deep dive on Amazon EBS"* (annual STG-track); *Nitro* sessions.
- AWS docs: *Amazon EBS features*, *EBS volume types*, *EBS snapshots*, *EBS encryption*.
- AWS post-mortem: *"Summary of the Amazon EC2 and Amazon RDS Service Disruption"* (April 2011).

---

## Self-check (do these before Module 2)
1. Using the mental model, explain why an EBS volume survives terminating its instance but an instance-store disk does not — in terms of *where the bytes physically are*.
2. Why is EBS single-AZ, and what does AWS trade to get low write latency? How do you get cross-AZ/region durability anyway?
3. What problem does Physalia solve that a single big control-plane database couldn't, and what's the "colocation" trick that shrinks blast radius?
4. A snapshot is "incremental" and "crash-consistent." Explain both, and what extra step a database needs for an *application-consistent* snapshot.
5. On a Nitro instance, your encrypted `io2` volume shows as `/dev/nvme1n1`. Trace what actually happens on a single 4 KB write, from the guest syscall to durability.
