# EBS — Troubleshooting & debugging

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [performance.md](performance.md), [security.md](security.md).

Spec section 14. Most EBS incidents are: *it's slow*, *it won't attach*, *the filesystem didn't grow*, or *data looks wrong*. Diagnose with metrics + the guest, not guesswork.

---

## 1. "EBS is slow" — the decision tree

1. **Instance ceiling or volume ceiling?** Check instance-level EBS metrics (`EBSIOBalance%`, `EBSByteBalance%`) and family limits. A fast volume on a small instance is throttled by the *instance*. → resize instance.
2. **Out of burst?** gp2/st1/sc1: `BurstBalance` near 0 → you exceeded baseline. → gp3 (no burst) or bigger volume.
3. **Under-provisioned?** io1/io2: `VolumeThroughputPercentage`/consumed ops ~100% → bump IOPS/throughput (gp3/io2 are live-modifiable).
4. **Queue depth / parallelism?** High `VolumeQueueLength` + high latency = saturated; but *low* queue with low IOPS means the **workload isn't parallel enough** — single-threaded I/O can't reach high IOPS. → more concurrency (`fio --iodepth`).
5. **I/O size mismatch?** Tiny random I/O is IOPS-bound; you may be throughput-fine but IOPS-starved (or vice versa). Match volume type to pattern.
6. **Restored from snapshot?** First-touch of each block lazy-loads from S3 (slow cold reads). → **FSR**, or pre-read the volume.
7. **Optimization period?** Just modified the volume (Elastic Volumes) → performance is intermediate while it migrates. Wait it out.

**Confirm inside the guest** (via SSM): `iostat -xz 1` (await, %util, avgqu-sz), `fio` for controlled tests, `lsblk`/`nvme list`.

## 2. "Volume won't attach / I/O errors"

- **KMS**: encrypted volume + disabled key or missing `kms:Decrypt`/grant → can't attach/read. Check the key state + IAM. (A "storage" outage that's really an IAM/KMS problem.)
- **Wrong AZ**: a volume attaches only to an instance in **its AZ**. Cross-AZ = create a volume from the snapshot in the target AZ.
- **Already attached / stuck**: a volume is single-attach (unless io2 Multi-Attach). Detach (force if stuck, but risk FS corruption on unclean detach), verify instance state.
- **Device name / mount**: the guest may name it `/dev/nvme1n1` (Nitro NVMe) not `/dev/xvdf` — your `fstab` mapping can be stale. Use `nvme id-ctrl` / UUIDs in fstab.

## 3. "Resized the volume but it's still small"

Growing the *volume* ≠ growing the *filesystem*. In the guest:
```bash
lsblk                          # see new size on the device, old on the partition
sudo growpart /dev/nvme1n1 1   # grow the partition
sudo resize2fs /dev/nvme1n1p1  # ext4  (or: xfs_growfs /mountpoint  for xfs)
df -h                          # now reflects new size
```
EBS deliberately doesn't touch your filesystem.

## 4. "Data looks corrupted / inconsistent"

- **Multi-Attach + non-cluster FS** (ext4/xfs on 2 nodes) → guaranteed corruption. Fix: cluster FS or single-attach.
- **Unclean detach / crash** → run `fsck`; journaling FS usually recovers.
- **Snapshot restored inconsistent** → it was only crash-consistent; for DBs use application-consistent snapshots (quiesce).
- **RAID 0 snapshot mismatch** → member volumes snapshotted at different instants; use **multi-volume snapshots**.

## 5. Cost/ops surprises

- **Bill spike** → orphaned volumes/snapshots, forgotten **FSR** (per-AZ-hour), over-provisioned io2. Check CUR `usageType`.
- **Snapshots growing fast** → high block churn; expected, but prune retention via DLM.

## 6. Tools

- **CloudWatch** EBS + instance metrics (above).
- **SSM Session Manager** → in-guest `iostat`, `fio`, `lsblk`, `dmesg` (I/O errors), `nvme list`.
- **EBS volume status checks** (`describe-volume-status`) → impaired/warning states, re-mirroring.
- **CloudTrail** → who detached/modified/shared a volume or snapshot.

---

## Sources
- AWS docs: *Monitoring volume status*, *EBS-optimized instances*, *Elastic Volumes (extend filesystem)*, *Troubleshoot EBS performance*.

---

## Self-check
1. A DB on a 16k-IOPS gp3 volume is slow; `VolumeQueueLength` is low and IOPS is well under 16k. What's the most likely cause and fix?
2. An encrypted volume fails to attach with no instance change. Give the two KMS-side checks.
3. You resized 200→800 GiB; `df` still shows 200. Give the exact guest steps.
4. Why will io2 Multi-Attach + xfs corrupt data, and what are the two correct alternatives?
5. Bill jumped this month with no new volumes. Name three EBS line items to inspect.
