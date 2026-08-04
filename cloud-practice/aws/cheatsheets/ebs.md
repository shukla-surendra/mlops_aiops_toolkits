# EBS Cheatsheet

One-page recall. Full detail in [`../docs/ebs/`](../docs/ebs/README.md).

## Mental model
**A volume is a network storage service impersonating a local NVMe disk** (Nitro presents it). Every I/O = network round trip. Blocks live on an in-AZ storage fleet, **replicated in one AZ**. VPC faked a network; EBS fakes a disk.

## Volume types
| Type | Media | Use | Max IOPS | Max MB/s |
|---|---|---|---|---|
| **gp3** | SSD | default | 16,000 | 1,000 |
| gp2 | SSD | legacy (burst) | 16,000 | 250 |
| **io2 Block Express** | SSD | DBs, sub-ms, 99.999% | 256,000 | 4,000 |
| io1/io2 | SSD | provisioned IOPS | 64,000 | 1,000 |
| st1 | HDD | throughput/sequential | 500 | 500 |
| sc1 | HDD | cold | 250 | 250 |

Default **gp3**. `throughput ≈ IOPS × IO_size` (SSD 256KiB, HDD 1MiB). Need **queue depth** for high IOPS. **Perf = min(volume, instance EBS ceiling).**

## Durability / DR
- Volume: gp 99.8–99.9% · io2 **99.999%** — **single-AZ**.
- **Snapshots = incremental, block-level, in S3 (multi-AZ)** → your DR escape hatch.
- DLM = automated snapshot schedules/retention/cross-Region. FSR = instant restore (per-AZ-hr $). Archive = cheap cold. Recycle Bin = undelete.
- Crash-consistent by default; quiesce for app-consistent; multi-volume snapshot for RAID/striped.

## Encryption
Nitro AES-256, envelope: per-volume **DEK** wrapped by **KMS key**. Covers at-rest + in-transit + snapshots + derived volumes. **Encryption by default** (account setting). **Delete KMS key = data gone.** Can't share default-key snapshots — use CMK + share grant.

## Multi-Attach
io2, ≤16 instances, same AZ, **shared block not shared FS** → cluster FS or corruption. Shared files across AZ = **EFS**.

## Elastic Volumes
Modify size/type/IOPS **live** → optimization period. **Grow FS yourself:** `growpart` + `resize2fs`/`xfs_growfs`.

## Cost traps
Bills **provisioned** capacity (not used): provisioned GB · provisioned IOPS above baseline · snapshots (orphans!) · **FSR per-AZ-hr** · cross-Region copy. **gp2→gp3 = cheaper + faster (do first).**
**Rates change → check live:** https://aws.amazon.com/ebs/pricing/ · calc https://calculator.aws/ · CUR `usageType` `EBS:VolumeUsage.gp3`/`SnapshotUsage`/`VolumeP-IOPS`/`FastSnapshotRestore`.

## Key metrics
`VolumeQueueLength` (saturation) · `BurstBalance` (gp2 cliff — alarm) · `VolumeThroughputPercentage` (io2 under-provision) · instance `EBSIOBalance%`/`EBSByteBalance%` (instance ceiling).

## Debug "slow"
instance ceiling? → burst out? → under-provisioned? → queue/parallelism? → I/O size? → restored (lazy-load→FSR)? → optimization period? In guest: `iostat -xz 1`, `fio`.

## Internals name-drops
Nitro card (data path + encryption) · **Physalia** (tiny-Paxos control plane, blast-radius containment; NSDI 2020) · re-mirroring · 2011 outage.

## CLI
```bash
aws ec2 create-volume --size 100 --volume-type gp3 --availability-zone us-east-1a --encrypted
aws ec2 attach-volume --volume-id vol-x --instance-id i-x --device /dev/sdf
aws ec2 create-snapshot --volume-id vol-x --description "backup"
aws ec2 modify-volume --volume-id vol-x --size 500 --volume-type gp3 --iops 6000
aws ec2 describe-volume-status --volume-id vol-x
```

## Terraform primitives
`aws_ebs_volume` · `aws_volume_attachment` · `aws_ebs_snapshot` · `aws_ebs_encryption_by_default` · `aws_dlm_lifecycle_policy` · `aws_kms_key`. Example: [`../terraform/ebs/`](../terraform/ebs/README.md).
