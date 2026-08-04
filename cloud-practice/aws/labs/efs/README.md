# Labs: EFS

Hands-on labs, beginner → advanced. Each: **Objectives · Architecture · Implementation · Validation · Cleanup**. These build the muscle memory behind [`../../docs/efs/`](../../docs/efs/README.md). The headline lab (2) shows the thing EBS *cannot* do: shared multi-AZ writes.

> ⚠️ All labs create billable resources. **Do Cleanup.** Sandbox account recommended. Clients need `amazon-efs-utils` installed and their SG allowed on the mount-target SG (NFS 2049).

---

## Lab 1 — Create & mount from one instance (Beginner)
**Objectives:** mount a managed NFS filesystem, write a file.
**Architecture:** 1 EFS filesystem + 1 mount target + 1 EC2 client (same AZ).
**Implementation:** create the filesystem ([Terraform](../../terraform/efs/README.md) or [boto3](../../boto3/efs/README.md)); on the client `sudo yum install -y amazon-efs-utils`; `sudo mount -t efs -o tls fs-xxx:/ /mnt/efs`; `echo hi | sudo tee /mnt/efs/f.txt`.
**Validation:** `df -h` shows the EFS mount; file reads back.
**Cleanup:** unmount; destroy filesystem (delete mount targets first).

## Lab 2 — Shared multi-AZ access (the point of EFS) (Beginner→Intermediate)
**Objectives:** prove concurrent, cross-AZ shared POSIX access.
**Architecture:** Standard EFS + mount target in **two** AZs + one EC2 client **per AZ**.
**Implementation:** mount the same filesystem on both instances (`-o tls`). On client-A: `echo fromA | sudo tee /mnt/efs/shared.txt`. On client-B: `cat /mnt/efs/shared.txt`.
**Validation:** client-B (different AZ) immediately sees client-A's write → **shared, multi-AZ, read-after-write**. Contrast: EBS can't be attached to both.
**Cleanup:** unmount both; destroy.

## Lab 3 — Access Points & multi-tenant isolation (Intermediate)
**Objectives:** pin identity + root dir per app.
**Implementation:** create two Access Points (`/app-a` uid 1001, `/app-b` uid 1002). Mount each: `-o tls,accesspoint=fsap-a` and `...=fsap-b`.
**Validation:** files created under AP-A are owned by 1001 under `/app-a`; AP-B can't see AP-A's tree; each is jailed to its root dir.
**Cleanup:** unmount; delete access points; destroy.

## Lab 4 — Enforce TLS with a filesystem policy (Intermediate)
**Objectives:** deny plaintext NFS.
**Implementation:** apply the [filesystem policy](../../terraform/efs/README.md) that denies `aws:SecureTransport=false`. Try mounting **without** `-o tls` (plain `nfs4`), then **with** `-o tls`.
**Validation:** plaintext mount denied; TLS mount works.
**Cleanup:** as above.

## Lab 5 — Throughput modes & the small-FS trap (Intermediate)
**Objectives:** feel Bursting vs Elastic.
**Implementation:** create a small **Bursting** filesystem; run a throughput test (`dd`/`fio` writing a few GB). Watch `BurstCreditBalance`. Recreate with **Elastic** and compare.
**Validation:** Bursting throttles a small FS toward baseline; Elastic scales up. Confirm via CloudWatch.
**Cleanup:** destroy.

## Lab 6 — Lifecycle tiering to IA (Intermediate→Advanced)
**Objectives:** cost tiering + the retrieval gotcha.
**Implementation:** enable Lifecycle `AFTER_7_DAYS` (or shortest available); write files; observe `StorageBytes` split (Standard vs IA) over time. Then read cold files.
**Validation:** cold files move to IA (cheaper storage); reading them incurs retrieval + higher first-byte latency.
**Cleanup:** destroy.

## Lab 7 — EKS/ECS shared volume (Advanced)
**Objectives:** the real container use case.
**Implementation:** install the **EFS CSI driver**; create a StorageClass/PV using the filesystem + an Access Point; run 2+ pods (across AZs) mounting the same PVC (RWX).
**Validation:** pods share files; a pod rescheduled to another AZ keeps the data.
**Cleanup:** delete workloads, PV/PVC, driver; destroy filesystem.

## Lab 8 — Failure simulation: AZ mount-target loss (Advanced)
**Objectives:** multi-AZ resilience vs One Zone.
**Implementation:** with clients in 2 AZs, delete one AZ's mount target (simulating an AZ issue). Observe the client in that AZ; the other keeps working. Repeat conceptually for a **One Zone** filesystem.
**Validation:** Standard survives (surviving AZ fine, data intact); One Zone would lose availability entirely if its AZ is the one affected.
**Cleanup:** destroy.

---

### Suggested order
1 → 2 (the headline) → 3 → 4 (security) → 5 (perf) → 6 (cost) → 7 & 8 (advanced/failure).
