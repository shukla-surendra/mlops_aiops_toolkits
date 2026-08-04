# boto3: EBS operations

`ebs_operations.py` walks the EBS lifecycle in Python — create → attach → snapshot → restore → modify → cleanup — using **boto3 waiters** (EBS calls are async; you wait for state transitions).

Ties to the docs in [`../../docs/ebs/`](../../docs/ebs/README.md).

## Setup
```bash
pip install boto3
export AWS_PROFILE=your-profile   # needs EC2 permissions
```

## Examples
```bash
# List all volumes in a region
python ebs_operations.py --region us-east-1 list

# Create a 10 GiB gp3 volume in an AZ
python ebs_operations.py --az us-east-1a create --size 10 --type gp3

# Attach to a running instance (same AZ!)
python ebs_operations.py attach --volume-id vol-0abc --instance-id i-0def --device /dev/sdf

# Snapshot it (incremental, to S3)
python ebs_operations.py snapshot --volume-id vol-0abc

# Restore a NEW volume from the snapshot in another AZ (cross-AZ move)
python ebs_operations.py --az us-east-1b restore --snapshot-id snap-0ghi

# Clean up (detach + delete volumes and snapshots)
python ebs_operations.py cleanup --volume-ids vol-0abc vol-0xyz --snapshot-ids snap-0ghi
```

## What to notice in the code
- **Waiters** (`volume_available`, `volume_in_use`, `snapshot_completed`) — the idiomatic way to handle EBS async state, instead of polling/sleeping.
- **AZ is mandatory** on create and must match the instance on attach — the single-AZ reality in code.
- **Restore-in-another-AZ** = snapshot (S3, multi-AZ) → new volume elsewhere: the concrete "escape the AZ" pattern.
- **`modify_volume`** = Elastic Volumes; the code comments remind you the *filesystem* still needs `growpart`/`resize2fs` in the guest.

⚠️ Creates billable resources — always `cleanup`.
