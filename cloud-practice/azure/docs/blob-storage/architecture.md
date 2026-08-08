# Blob Storage — Module 1: Why it exists, the mental model, and the internal architecture

> Part of the Azure track. See [PROGRESS.md](../../../PROGRESS.md) for the full plan.
> **Epistemics:** claims tagged **[Documented]** (Microsoft Learn / the cited SOSP paper) or
> **[Inferred]**. Verified against Microsoft Learn and the primary systems paper cited below
> — not assumed from memory or older tutorials.
>
> **AWS contrast note:** unlike Entra ID (no equivalent AWS-side doc yet), Azure Storage's
> internals are unusually well documented for the whole industry — better, in fact, than
> S3's own internals are publicly documented. That's not just an Azure-flavor detail, it's a
> genuinely interesting interview-relevant fact in its own right, covered in §3.

**Module scope:** spec sections 1–3 + 17. Covers *why Blob Storage exists*, the *Storage
Account mental model* (the real structural divergence from S3), and the *internal
architecture* — Front-End / Partition / Stream layers, from a peer-reviewed systems paper
Microsoft actually published.

---

## 1. Why does this service exist?

### The problem in one sentence

Applications need to store an effectively unlimited number of immutable-ish binary objects
(images, backups, logs, model artifacts, video) durably, cheaply, and accessible over HTTP —
without provisioning a filesystem, a server, or capacity in advance, and without objects
being limited by any single machine's disk size.

### How companies solved this before object storage existed

Pre-cloud: a filesystem (NFS/SAN) with a directory hierarchy, capacity-planned and
provisioned ahead of need, or a database BLOB column for smaller binaries. Both hit the same
wall at scale: filesystems don't horizontally scale storage capacity or request throughput
gracefully, and directory-hierarchy metadata (millions of files in one directory) becomes a
bottleneck long before disk capacity does.

### Why Microsoft built Blob Storage the way it did

[Documented]: Blob Storage launched as part of **Windows Azure Storage** in 2008/2010,
architected from the start as a **flat, HTTP-addressable object store** — not a hierarchical
filesystem pretending to scale — with the property that **redundancy and durability are
handled by the platform**, never something the caller manages (no RAID config, no replica
count decision at the object level, unlike running your own storage cluster).

### What if it didn't exist?

- Every application team would provision and capacity-plan its own storage — the exact
  "someone has to own disk sizing" problem cloud storage exists to remove.
- No cheap, durable place to put unstructured data at the volume modern
  logging/backup/ML-artifact workloads need — you'd be back to filesystems that don't scale
  storage and request-rate independently of each other.

---

## 2. The core mental model — Storage Account, the real structural divergence from S3

> **A Blob is stored inside a Container, which lives inside a Storage Account — and a single
> Storage Account is also the shared home for Table, Queue, and File storage, not just
> Blobs.** This is the single biggest structural difference from S3, worth internalizing
> before anything else in this module.

```
AWS:    AWS Account ─── (flat) ─── S3 Bucket ─── Object
                                    (one namespace, one service, globally unique bucket name)

Azure:  Subscription ─┬─ Storage Account ─┬─ Blob service   ─── Container ─── Blob
                       │  (billing +        ├─ Table service  ─── Table    ─── Entity
                       │   security +       ├─ Queue service  ─── Queue    ─── Message
                       │   redundancy       └─ File service   ─── Share    ─── File
                       │   config, shared
                       │   across all four)
                       └─ (can hold many Storage Accounts)
```

The [Documented] consequence: **Blob, Table, Queue, and File storage in Azure aren't four
separate services the way S3, DynamoDB, SQS, and EFS are in AWS** — they're four data
abstractions sharing one **Storage Account** resource, which is what actually holds the
account-level settings that matter architecturally: the **redundancy tier** (§3d),
**access keys / Shared Access Signatures**, **network rules (firewall, private endpoints)**,
and **performance tier (Standard vs. Premium)**. This is *why* "S3-like Table Storage" as a
phrase undersells what's going on — Table Storage isn't Azure's S3-equivalent (Blob is); it's
a NoSQL key-value store that happens to share billing/security/redundancy infrastructure
with Blob Storage because Microsoft built one underlying platform (the Stream layer, §3c)
that all four services sit on top of.

---

## 3. Internal architecture

### 3a. Three layers — Front-End, Partition, Stream — and why this is unusually well documented

[Documented — primary source: **Calder et al., "Windows Azure Storage: A Highly Available
Cloud Storage Service with Strong Consistency," SOSP 2011**]. This is a peer-reviewed
systems paper Microsoft published describing the actual production architecture underneath
Blob/Table/Queue storage — genuinely more detailed public disclosure than Amazon has
published about S3's internals. Worth stating plainly as a real fact, not just Azure-track
flavor text: **if an interviewer asks you to describe object-storage internals, Azure
Storage's published architecture is the more citable answer of the two**, even in an
AWS-focused interview, precisely because it's peer-reviewed and public.

The three layers, request-path order:

```
Client Request (HTTPS)
        │
        ▼
┌─────────────────────────────────────────────┐
│ FRONT-END (FE) LAYER                          │
│ Stateless. Authenticates request (account key/ │
│ SAS/Azure RBAC), routes to the right Partition │
│ Server via the Partition Map, caches routing.  │
└─────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────┐
│ PARTITION LAYER                               │
│ Manages Range Partitions of the object         │
│ namespace across Partition Servers, load-      │
│ balances (splits/merges partitions as traffic   │
│ shifts), maintains index/metadata, handles      │
│ transaction ordering per partition.             │
│ A Partition Master assigns partitions to        │
│ servers and monitors their health.              │
└─────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────┐
│ STREAM LAYER                                  │
│ The actual replicated, append-only distributed │
│ filesystem underneath everything. Data is       │
│ stored as "extents" (the unit of replication),  │
│ chained into "streams." A Stream Manager tracks  │
│ extent placement and replica health, replicating │
│ synchronously (primary + secondaries) before an  │
│ append is acknowledged — this is where strong    │
│ durability + consistency actually comes from.    │
└─────────────────────────────────────────────┘
```

**Why this three-layer split exists, in one sentence per layer**: the Front-End layer exists
so authentication/routing scales independently of storage (stateless, trivially
horizontally scalable); the Partition layer exists so the *namespace and metadata* can be
load-balanced and scaled independently of raw bytes (splitting a hot partition doesn't move
any actual data, it just re-assigns index ranges); the Stream layer exists so *durability*
is handled once, generically, underneath all four data abstractions (Blob/Table/Queue/File
all write through the same replicated append-only log, rather than each service
reimplementing its own replication).

### 3b. Strong consistency — the historically significant contrast with S3

[Documented, well-established industry fact]: the SOSP 2011 paper's headline contribution
was providing **strong consistency** (read-after-write) for Azure Storage from the start.
**Amazon S3, by contrast, originally only offered eventual consistency** for overwrite
PUTs/DELETEs, and **only added strong read-after-write consistency in December 2020** —
roughly a decade after Azure Storage's paper described having it. This is a genuinely
citable historical fact worth having ready in an interview, not just trivia: it's a real
example of two major clouds making different early architectural trade-offs on the
same problem, with AWS's choice (eventual consistency, prioritizing availability/partition
tolerance per classic CAP reasoning) later walked back once the ecosystem cost of eventual
consistency outweighed its original benefit.

### 3c. Why Blob/Table/Queue/File share one platform — the Stream layer is the actual reason

Tying back to §2's "why does one Storage Account hold four different data abstractions"
question: [Inferred, but a direct and well-supported reading of the paper's architecture]
Table entities, Queue messages, and File shares are all, underneath the Partition/Stream
layers, ultimately durable data written through the **same replicated extent-based Stream
layer** that Blobs use — the layers above (Partition layer's indexing scheme, and the
service-specific API surface) differ per data abstraction, but the durability substrate is
shared. This is the actual engineering reason a Storage Account is the natural shared
container: Microsoft built one durable, replicated storage substrate once, then exposed four
different data models on top of it, rather than building four separately-architected
storage systems the way AWS built S3, DynamoDB, SQS, and EFS as genuinely separate services
with separate internals.

### 3d. Redundancy (LRS/ZRS/GRS/RA-GRS) vs. Access Tier (Hot/Cool/Archive) — two independent axes, one point of confusion

[Documented]: Azure Storage separates two decisions that S3's storage-class model bundles
into one choice per object:

- **Redundancy** — an account-level (or, for newer configurations, more granular) setting
  controlling *where and how many copies* exist: **LRS** (3 copies, one datacenter), **ZRS**
  (copies spread across Availability Zones in one region), **GRS** (LRS plus async-replicated
  copies in a paired region), **RA-GRS** (GRS, with the secondary region readable). This axis
  is about **physical placement and disaster-recovery scope**.
- **Access Tier** — **Hot / Cool / Cold / Archive**, a *per-blob* setting about **access
  frequency and retrieval cost/latency**, closer in spirit to S3's Standard/IA/Glacier tiers.

**S3's storage classes conflate both axes into one selection** (e.g. S3 Standard-IA implies
both a redundancy posture and an access-cost tier together); Azure asks you to choose them
**independently** — a Cool blob can still be GRS-redundant, or an Archive blob can still be
ZRS. Worth being explicit that this is a genuine modeling difference, not just more Azure
knobs for their own sake: it lets you tune disaster-recovery scope and cost-per-access
separately, which S3's bundled classes don't allow in one setting.

### 3e. Blob types — and the surprising internal connection to Managed Disks (service #2)

Three distinct blob types, chosen at creation, not just metadata:

- **Block Blobs** — the direct S3-object equivalent: upload in blocks, commit a block list,
  optimized for large sequential read/write (media, backups, general files).
- **Append Blobs** — optimized specifically for append-only writes (log files) — no clean S3
  equivalent without workarounds like multipart-upload gymnastics; Azure exposes append as a
  first-class blob type.
- **Page Blobs** — random-access, fixed-size-page-addressable storage. [Documented]: **this
  is what Azure Managed Disks (this track's service #2) are actually built on** — a Managed
  Disk's underlying storage is a Page Blob under the covers. Worth flagging now as a preview:
  when Managed Disks gets its own module, "it's page blobs with VM-disk semantics on top"
  will already make sense, the same way EBS-vs-EC2 internals connect once you've seen both.

---

## Distributed-systems concepts in play (preview of section-17 depth)

- **Separating metadata/index scaling from raw-byte durability** — the Partition-layer /
  Stream-layer split, the same principle behind separating a database's index from its
  heap storage, just at cloud-storage scale.
- **Replicated append-only log as a durability primitive** — the Stream layer's extents,
  conceptually close to how a distributed WAL or a system like GFS/Colossus/HDFS provides
  durability underneath higher-level abstractions.
- **CAP-theorem trade-off made concretely visible** — Azure Storage's early strong
  consistency vs. S3's early eventual consistency is a real, dated, citable example of two
  companies choosing differently on the same trade-off, not a textbook hypothetical.
- **One durable substrate, many data models on top** — the architectural reason a Storage
  Account spans Blob/Table/Queue/File, and a pattern that recurs anywhere a platform team
  builds one storage engine and exposes several APIs over it.

---

## Sources

- **Calder et al., "Windows Azure Storage: A Highly Available Cloud Storage Service with
  Strong Consistency," SOSP 2011.** The primary source for the entire §3a/3b architecture —
  read this paper directly before M2 if going deep; it's unusually readable for a systems
  paper.
- Microsoft Learn — *"Storage account overview"*, *"Blob storage overview"*, *"Access tiers
  for blob data"*, *"Azure Storage redundancy"* (§3d).
- Microsoft Learn — *"About page blobs"*, *"Azure managed disks overview"* (the Page
  Blob/Managed Disk connection in §3e — confirm depth when Managed Disks gets its own
  module).
- Industry-documented timeline for S3's December 2020 strong-consistency change (§3b) — a
  widely-reported AWS re:Invent 2020 announcement, useful as a dated comparison point.

---

## Gate

Module 1 gate for Blob Storage is not yet written — will be added alongside M2, once the
learner has cleared (or explicitly deferred, per `PROGRESS.md`) the earlier open gates in
this track. See [PROGRESS.md](../../../PROGRESS.md) for current gate status across all
Azure modules.
