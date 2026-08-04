#!/usr/bin/env python3
"""EBS operations with boto3 — the volume lifecycle in Python.

Demonstrates the core EBS workflow the docs describe:
  create -> attach -> snapshot -> restore (new volume from snapshot) ->
  modify (Elastic Volumes) -> cleanup.

Uses boto3 waiters so calls block until the resource reaches the desired state
(EBS operations are asynchronous — you must wait, not sleep-and-hope).

Requires: boto3, and AWS credentials with EC2 permissions.
    pip install boto3
    python ebs_operations.py --help

⚠️ Several commands create BILLABLE resources. Use --cleanup and delete when done.
"""

from __future__ import annotations

import argparse
import sys

import boto3
from botocore.exceptions import ClientError


def ec2(region: str):
    return boto3.client("ec2", region_name=region)


def create_volume(region: str, az: str, size: int, vol_type: str = "gp3",
                  iops: int | None = None, throughput: int | None = None,
                  encrypted: bool = True) -> str:
    """Create an EBS volume in a specific AZ and block until 'available'."""
    c = ec2(region)
    params = {
        "AvailabilityZone": az,      # a volume is born into ONE AZ
        "Size": size,
        "VolumeType": vol_type,
        "Encrypted": encrypted,      # uses the account default KMS key unless KmsKeyId given
        "TagSpecifications": [{
            "ResourceType": "volume",
            "Tags": [{"Key": "Name", "Value": "boto3-demo"},
                     {"Key": "Backup", "Value": "true"}],
        }],
    }
    # gp3/io1/io2 accept provisioned IOPS; gp3 also accepts throughput.
    if iops is not None:
        params["Iops"] = iops
    if throughput is not None and vol_type == "gp3":
        params["Throughput"] = throughput

    vol_id = c.create_volume(**params)["VolumeId"]
    print(f"creating {vol_id} ({size} GiB {vol_type}) in {az} ...")
    c.get_waiter("volume_available").wait(VolumeIds=[vol_id])
    print(f"  available: {vol_id}")
    return vol_id


def attach_volume(region: str, vol_id: str, instance_id: str, device: str = "/dev/sdf") -> None:
    """Attach a volume to an instance (must be in the SAME AZ) and wait for 'in-use'."""
    c = ec2(region)
    c.attach_volume(VolumeId=vol_id, InstanceId=instance_id, Device=device)
    print(f"attaching {vol_id} -> {instance_id} as {device} ...")
    c.get_waiter("volume_in_use").wait(VolumeIds=[vol_id])
    print("  attached (now format + mount inside the guest; EBS gives you a raw block device)")


def snapshot_volume(region: str, vol_id: str, description: str = "boto3 snapshot") -> str:
    """Create an incremental, block-level snapshot (stored in S3) and wait for 'completed'."""
    c = ec2(region)
    snap_id = c.create_snapshot(
        VolumeId=vol_id, Description=description,
        TagSpecifications=[{"ResourceType": "snapshot",
                            "Tags": [{"Key": "Name", "Value": "boto3-demo-snap"}]}],
    )["SnapshotId"]
    print(f"snapshotting {vol_id} -> {snap_id} (waiting; first snapshot copies all blocks) ...")
    c.get_waiter("snapshot_completed").wait(SnapshotIds=[snap_id])
    print(f"  completed: {snap_id}")
    return snap_id


def volume_from_snapshot(region: str, snap_id: str, az: str, vol_type: str = "gp3") -> str:
    """Restore a NEW volume from a snapshot — this is how you move data across AZs."""
    c = ec2(region)
    vol_id = c.create_volume(SnapshotId=snap_id, AvailabilityZone=az, VolumeType=vol_type)["VolumeId"]
    print(f"restoring {snap_id} -> {vol_id} in {az} (blocks lazy-load from S3 on first touch) ...")
    c.get_waiter("volume_available").wait(VolumeIds=[vol_id])
    print(f"  available: {vol_id}")
    return vol_id


def modify_volume(region: str, vol_id: str, size: int | None = None,
                  iops: int | None = None, throughput: int | None = None) -> None:
    """Elastic Volumes: change size/IOPS/throughput live (no detach). Remember to grow the FS in-guest."""
    c = ec2(region)
    kwargs = {"VolumeId": vol_id}
    if size:
        kwargs["Size"] = size
    if iops:
        kwargs["Iops"] = iops
    if throughput:
        kwargs["Throughput"] = throughput
    c.modify_volume(**kwargs)
    print(f"modifying {vol_id}: {kwargs} (enters an optimization period; FS still needs growpart+resize)")


def list_volumes(region: str) -> None:
    c = ec2(region)
    for v in c.describe_volumes()["Volumes"]:
        name = next((t["Value"] for t in v.get("Tags", []) if t["Key"] == "Name"), "-")
        print(f"{v['VolumeId']}  {v['Size']:>5} GiB  {v['VolumeType']:<5}  "
              f"{v['State']:<10}  {v['AvailabilityZone']}  enc={v['Encrypted']}  name={name}")


def cleanup(region: str, vol_ids: list[str], snap_ids: list[str]) -> None:
    """Detach (if needed) + delete volumes and snapshots. Order matters: detach -> delete vol -> delete snap."""
    c = ec2(region)
    for vid in vol_ids:
        try:
            c.detach_volume(VolumeId=vid, Force=True)
            c.get_waiter("volume_available").wait(VolumeIds=[vid])
        except ClientError:
            pass  # already detached
        try:
            c.delete_volume(VolumeId=vid)
            print(f"deleted volume {vid}")
        except ClientError as e:
            print(f"  volume {vid}: {e}")
    for sid in snap_ids:
        try:
            c.delete_snapshot(SnapshotId=sid)
            print(f"deleted snapshot {sid}")
        except ClientError as e:
            print(f"  snapshot {sid}: {e}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--region", default="us-east-1")
    p.add_argument("--az", default="us-east-1a")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    c = sub.add_parser("create"); c.add_argument("--size", type=int, default=10)
    c.add_argument("--type", default="gp3")

    a = sub.add_parser("attach"); a.add_argument("--volume-id", required=True)
    a.add_argument("--instance-id", required=True); a.add_argument("--device", default="/dev/sdf")

    s = sub.add_parser("snapshot"); s.add_argument("--volume-id", required=True)

    r = sub.add_parser("restore"); r.add_argument("--snapshot-id", required=True)

    cl = sub.add_parser("cleanup"); cl.add_argument("--volume-ids", nargs="*", default=[])
    cl.add_argument("--snapshot-ids", nargs="*", default=[])

    args = p.parse_args()
    if args.cmd == "list":
        list_volumes(args.region)
    elif args.cmd == "create":
        create_volume(args.region, args.az, args.size, args.type)
    elif args.cmd == "attach":
        attach_volume(args.region, args.volume_id, args.instance_id, args.device)
    elif args.cmd == "snapshot":
        snapshot_volume(args.region, args.volume_id)
    elif args.cmd == "restore":
        volume_from_snapshot(args.region, args.snapshot_id, args.az)
    elif args.cmd == "cleanup":
        cleanup(args.region, args.volume_ids, args.snapshot_ids)
    return 0


if __name__ == "__main__":
    sys.exit(main())
