# EFS — Interview preparation

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> Spec section 15. Answers = the version an interviewer wants. Say them aloud.

---

## Junior
**Q. What is EFS?** A fully-managed, elastic, multi-AZ NFS (POSIX) filesystem you mount from many Linux instances/containers concurrently. Pay for what you use.

**Q. EFS vs EBS?** EFS = shared file (NFS), multi-AZ, many clients, elastic. EBS = block, single-instance, single-AZ, provisioned. Shared files → EFS; one box's disk/DB → EBS.

**Q. How do you mount it?** Via a **mount target** (an ENI/IP per AZ) over NFS 2049, ideally with `amazon-efs-utils` (`-o tls`).

## Senior
**Q. EFS vs EBS vs S3 — one line each.** EFS = shared POSIX file, multi-AZ; EBS = single-attach block, single-AZ; S3 = object over HTTP, 11-nines. Different interfaces for different access patterns.

**Q. Why is EFS higher-latency than EBS?** It's a network filesystem — every op is an NFS round trip to a mount target over a distributed multi-AZ store. Great aggregate throughput, but per-op latency (~ms) hurts tiny-file/metadata workloads.

**Q. Throughput modes?** Elastic (auto-scale, pay-per-use — default), Bursting (scales with size + burst credits; small FS = low baseline), Provisioned (fixed MB/s you pay for). Use Elastic unless steady/predictable.

**Q. Standard vs One Zone?** Standard = multi-AZ redundancy; One Zone = single AZ, ~½ cost, no AZ resilience. One Zone for dev/reconstructible data.

**Q. How do you isolate many tenants on one filesystem?** Access Points — each enforces a POSIX uid/gid + root directory, so each app/container is pinned to its own path/identity. Add IAM auth + filesystem policy.

## Principal / architecture
**Q. Design shared persistent storage for stateful containers across AZs.** EFS (Standard, encrypted, Elastic throughput) + EFS CSI driver + one Access Point per app (uid + root dir isolation) + mount-target SG allowing 2049 only from node SG + `-o tls`/`-o iam` + Lifecycle Management for cold data. Multi-AZ so a zone loss doesn't drop the volume.

**Q. When NOT to use EFS?** Transactional DBs (latency → EBS io2), Windows/SMB (→ FSx for Windows), extreme HPC throughput (→ FSx for Lustre), pure object/data-lake (→ S3), or single-instance disks (→ EBS).

**Q. How does EFS stay available through an AZ failure when EBS can't?** Standard EFS stores data redundantly across multiple AZs, and each AZ has its own mount target; EBS keeps all replicas in one AZ for low write latency. Different point on the latency-vs-availability tradeoff.

## Scenario
**Q. "Mount hangs on new instances."** Almost always the mount-target SG missing 2049 from the client SG (a hang, not an error). Confirm with `nc -vz mount-target 2049`; fix the SG; check per-AZ mount target + NACL ephemerals.

**Q. "EFS is slow for our CI checkouts."** Tiny-file/metadata latency on a network FS, possibly Bursting on a small FS. Parallelize, larger I/O, switch to Elastic; consider whether these artifacts belong in S3.

**Q. "Cut our EFS bill."** Lifecycle → IA/Archive for cold files, One Zone for non-critical, Elastic (pay-per-use) vs over-provisioned, AZ-local mounts. Watch IA retrieval charges on scan-heavy jobs.

## Incident
**Q. "Half our fleet lost the EFS mount during an AZ event."** Clients in the failed AZ lost their AZ-local mount target; Standard data is safe (multi-AZ). Ensure mount targets + clients span ≥2 AZs and that remounts prefer surviving AZs; One Zone filesystems would have lost availability entirely.

**Q. "Sensitive data was readable on the wire."** Plain `nfs4` mount, no TLS. Enforce TLS via filesystem policy (`aws:SecureTransport`), mount `-o tls` with efs-utils, and confirm encryption at rest (KMS).

---

## Rapid-fire
- EFS = managed elastic multi-AZ NFS (POSIX); pay for used GB.
- Mount target = per-AZ ENI on 2049; SG controls who mounts.
- Standard multi-AZ vs One Zone (½ cost, 1 AZ).
- Elastic throughput default; Bursting scales with size (small = slow).
- Access Points = per-tenant uid + root dir isolation.
- Encrypt at rest (KMS) + in transit (efs-utils `-o tls`).
- Higher per-op latency than EBS; bad for DBs/tiny-file serial.
- Lifecycle → IA/Archive for cost; watch retrieval charges.

---

## Self-check
Answer any 3 Principal/scenario/incident questions aloud in <90s each without reading.
