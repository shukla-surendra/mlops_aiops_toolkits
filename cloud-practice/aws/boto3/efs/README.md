# boto3: EFS operations

`efs_operations.py` walks the EFS lifecycle in Python — create filesystem → mount targets → access point → lifecycle → cleanup — **polling `LifeCycleState`** (EFS calls are async and mostly lack built-in waiters, so this shows the real state machine).

Ties to [`../../docs/efs/`](../../docs/efs/README.md).

## Setup
```bash
pip install boto3
export AWS_PROFILE=your-profile   # needs EFS + EC2 permissions
```

## Examples
```bash
# List filesystems + their mount targets
python efs_operations.py --region us-east-1 show

# Create an encrypted, elastic-throughput filesystem (lifecycle → IA after 30d)
python efs_operations.py create --name demo-efs

# Add a mount target in a subnet (SG must allow NFS 2049 from your clients)
python efs_operations.py mount-target --fs-id fs-0abc --subnet-id subnet-0def --sg-ids sg-0ghi

# Create an Access Point pinned to /app as uid/gid 1001
python efs_operations.py access-point --fs-id fs-0abc --path /app

# Tear everything down (access points -> mount targets -> filesystem)
python efs_operations.py cleanup --fs-id fs-0abc
```

## What to notice
- **Explicit polling** of `LifeCycleState` (`creating`→`available`, `deleting`→gone) — the honest way to handle EFS async ops.
- **Delete ordering:** you can't delete a filesystem until its **mount targets** are gone — the code waits for each to reach `deleted`.
- **One mount target per AZ**; the SG on it is what gates who can mount (NFS 2049).
- **Access Point** encodes the per-tenant POSIX identity + root dir in a single object.

⚠️ Billable — always `cleanup`.
