# Amazon EFS — Complete documentation set

Deep-dive on Elastic File System — the **multi-AZ, shared, POSIX (NFS) file** counterpart to EBS. Studied right after EBS so the contrast (block vs file, single-AZ vs multi-AZ, single-attach vs shared) does the teaching.

## Study order

1. **[architecture.md](architecture.md)** — *Why EFS exists · the "managed multi-AZ NFS" mental model · internal architecture* (distributed metadata, multi-AZ redundancy, mount targets as per-AZ ENIs, NFS v4.1, consistency). **Start here** (after EBS).
2. **[performance.md](performance.md)** — performance modes (General Purpose vs Max I/O), throughput modes (Elastic/Bursting/Provisioned), the tiny-file/metadata latency story, storage classes.
3. **[security.md](security.md)** — mount-target Security Groups (2049), encryption (rest + TLS), Access Points, IAM auth + filesystem policies, threat models.
4. **[best-practices.md](best-practices.md)** — checklist, anti-patterns, cost model + lifecycle tiering, monitoring, production patterns (EKS/ECS CSI).
5. **[troubleshooting.md](troubleshooting.md)** — mount-hang/permission/slow diagnosis, the mount chain, tools.
6. **[interview.md](interview.md)** — junior→principal Q&A, scenarios, incidents.

## Quick reference
- **[EFS cheatsheet](../../cheatsheets/efs.md)** — one-page recall.

## Hands-on
- **[Terraform: EFS](../../terraform/efs/README.md)** — encrypted filesystem, per-AZ mount targets, SG, Access Point, TLS-enforcing policy.
- **[boto3: EFS operations](../../boto3/efs/README.md)** — create/mount-targets/access-point/lifecycle/cleanup in Python.
- **[Labs: EFS](../../labs/efs/README.md)** — beginner→advanced, each with objectives/validation/cleanup.

## Related
- **[EBS docs](../ebs/README.md)** — read first; the contrast is the point.
- **[VPC docs](../vpc/README.md)** — EFS mount targets are ENIs; Security Groups gate NFS (2049).

---
*Convention:* claims tagged **[Documented]** / **[Inferred]**.
