# Labs: EBS

Hands-on labs, beginner → advanced. Each has **Objectives · Architecture · Implementation · Validation · Cleanup**. Do them in order; they build the muscle memory behind [`../../docs/ebs/`](../../docs/ebs/README.md).

> ⚠️ All labs create billable resources. **Do the Cleanup step.** Prefer a sandbox account. Connect to instances via **SSM Session Manager** (attach `AmazonSSMManagedInstanceCore`) or EC2 Instance Connect — no SSH keys needed.

---

## Lab 1 — Create, attach, format, and prove persistence (Beginner)
**Objectives:** see that an EBS volume is a raw block device that survives the instance.
**Architecture:** 1 EC2 instance + 1 gp3 volume in the same AZ.
**Implementation:**
1. Launch a t3.micro (or use the [Terraform module](../../terraform/ebs/README.md)).
2. Create + attach a 10 GiB gp3 volume (console, CLI, or [boto3](../../boto3/ebs/README.md)).
3. In the guest: `lsblk` (find `/dev/nvme1n1`), `sudo mkfs -t xfs /dev/nvme1n1`, `sudo mkdir /data && sudo mount /dev/nvme1n1 /data`, `echo hello | sudo tee /data/f.txt`.
**Validation:** **stop/start** the instance (moves hosts), re-mount, confirm `/data/f.txt` survives. Contrast: instance-store would be gone.
**Cleanup:** unmount, detach, delete the volume; terminate instance.

## Lab 2 — Snapshot & restore into another AZ (Beginner→Intermediate)
**Objectives:** use snapshots (S3) to move data across AZs — escape single-AZ.
**Implementation:** snapshot the Lab 1 volume → create a new volume **from the snapshot in a different AZ** → attach to an instance there → mount → confirm `f.txt` is present.
**Validation:** data present in the new AZ; note the first read is slightly slow (lazy-load from S3).
**Cleanup:** delete new volume + snapshot.

## Lab 3 — Performance: gp3 vs burst, with `fio` (Intermediate)
**Objectives:** feel IOPS/throughput, queue depth, and the instance ceiling.
**Implementation:** on the mounted gp3 volume run:
```bash
sudo fio --name=randread --filename=/data/fio --size=2G --rw=randread \
  --bs=4k --iodepth=32 --numjobs=4 --time_based --runtime=60 --group_reporting
```
Then bump `gp3_iops`/`throughput` (Elastic Volumes) and rerun. Try `--iodepth=1` to see how low parallelism caps IOPS.
**Validation:** watch CloudWatch `VolumeReadOps`, `VolumeQueueLength`, and instance `EBSIOBalance%`. Identify whether you're hitting the **volume** or **instance** limit.
**Cleanup:** remove the fio file.

## Lab 4 — Resize live + grow the filesystem (Intermediate)
**Objectives:** Elastic Volumes; volume size ≠ filesystem size.
**Implementation:** `aws ec2 modify-volume --volume-id vol-x --size 40`; then in guest `sudo growpart` (if partitioned) + `sudo xfs_growfs /data`.
**Validation:** `df -h` shows the new size with **no downtime/detach**.
**Cleanup:** (volume shrinks aren't allowed; just delete when done.)

## Lab 5 — Encryption & KMS (Intermediate)
**Objectives:** envelope encryption; the KMS dependency.
**Implementation:** create a customer-managed KMS key; create an **encrypted** volume with it; attach/use. Then **disable the key** and try to attach a fresh volume / start an instance using it.
**Validation:** operations fail while the key is disabled → prove "KMS is a data dependency." Re-enable to recover.
**Cleanup:** delete volumes; schedule key deletion (note the waiting period).

## Lab 6 — Automated backups with DLM (Intermediate→Advanced)
**Objectives:** production-standard backups without cron.
**Implementation:** apply the [Terraform DLM policy](../../terraform/ebs/README.md) (or console); tag a volume `Backup=true`.
**Validation:** after the schedule fires, confirm snapshots appear tagged `SnapshotCreator=dlm`, and that retention prunes to the configured count.
**Cleanup:** disable/delete the DLM policy; delete snapshots.

## Lab 7 — Multi-Attach io2 (Advanced)
**Objectives:** understand shared **block** ≠ shared **filesystem**.
**Implementation:** create an io2 volume with Multi-Attach; attach to **two** instances in one AZ. Mount xfs on both.
**Validation:** observe corruption/inconsistency (do this only on throwaway data!) → the lesson: you need a cluster-aware FS (GFS2/OCFS2) or use **EFS** for shared files.
**Cleanup:** detach from both, delete.

## Lab 8 — Failure simulation: unclean detach under load (Advanced)
**Objectives:** crash-consistency vs application-consistency.
**Implementation:** write continuously to the volume, then **force-detach** it (simulating a crash). Re-attach elsewhere, mount, `fsck`.
**Validation:** journaling FS recovers to a crash-consistent state; note what a database would need (WAL replay / quiesced snapshot) for app-consistency.
**Cleanup:** delete resources.

---

### Suggested order
1 → 2 → 4 → 5 → 6 (core), then 3 (perf), 7 & 8 (advanced/failure).
