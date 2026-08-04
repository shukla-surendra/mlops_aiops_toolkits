# Amazon EBS — Complete documentation set

Deep-dive on Elastic Block Store, from first principles to production. Read in order.

## Study order

1. **[architecture.md](architecture.md)** — *Why EBS exists · the "network disk pretending to be local" mental model · internal architecture* (in-AZ replication, control/data plane, Nitro NVMe, the **Physalia** control plane, the 2011 outage lesson). **Start here.**
2. **[performance.md](performance.md)** — volume types (gp3/io2/Block Express/st1/sc1), IOPS vs throughput, burst, the instance ceiling, Multi-Attach, Elastic Volumes.
3. **[snapshots-durability.md](snapshots-durability.md)** — incremental snapshots to S3, crash vs app consistency, DLM, Fast Snapshot Restore, cross-Region DR, archive/Recycle Bin.
4. **[security.md](security.md)** — encryption/KMS envelope, IAM, snapshot sharing, threat models.
5. **[best-practices.md](best-practices.md)** — right-sizing, anti-patterns, cost model, CloudWatch monitoring, production patterns.
6. **[troubleshooting.md](troubleshooting.md)** — the "EBS is slow" decision tree, attach/KMS failures, resize→grow-FS, corruption.
7. **[interview.md](interview.md)** — junior→principal Q&A, scenarios, incidents.

## Quick reference
- **[EBS cheatsheet](../../cheatsheets/ebs.md)** — one-page recall.

## Hands-on
- **[Terraform: EBS](../../terraform/ebs/README.md)** — KMS-encrypted gp3 + io2 volumes, attachment, DLM backup policy.
- **[boto3: EBS operations](../../boto3/ebs/README.md)** — create/attach/snapshot/restore/cleanup in Python.
- **[Labs: EBS](../../labs/ebs/README.md)** — beginner→advanced, each with objectives/validation/cleanup.

## Related
- **[EFS docs](../efs/README.md)** — the file-storage counterpart; read after EBS for the contrast.
- **[VPC docs](../vpc/README.md)** — EBS I/O rides the same Nitro data-plane story.

---
*Convention:* claims tagged **[Documented]** (AWS docs / re:Invent / patents / papers) or **[Inferred]** (reconstruction from behavior). Hold Inferred loosely.
