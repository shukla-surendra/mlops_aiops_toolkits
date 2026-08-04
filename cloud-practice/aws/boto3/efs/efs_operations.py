#!/usr/bin/env python3
"""EFS operations with boto3 — filesystem lifecycle in Python.

Workflow the docs describe:
  create filesystem -> mount targets (per subnet/AZ) -> access point ->
  lifecycle tiering -> cleanup.

EFS API calls are asynchronous and (mostly) lack built-in waiters, so this
polls LifeCycleState explicitly — a good illustration of the real state machine.

Requires: boto3 + AWS creds with EFS/EC2 permissions.
    pip install boto3
    python efs_operations.py --help

⚠️ Creates billable resources. Use `cleanup` and destroy when done.
"""

from __future__ import annotations

import argparse
import sys
import time

import boto3
from botocore.exceptions import ClientError


def efs(region: str):
    return boto3.client("efs", region_name=region)


def _wait_fs(client, fs_id: str, target="available", timeout=180) -> None:
    """Poll a filesystem until it reaches target LifeCycleState."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        fs = client.describe_file_systems(FileSystemId=fs_id)["FileSystems"][0]
        state = fs["LifeCycleState"]
        if state == target:
            return
        print(f"  {fs_id}: {state} ...")
        time.sleep(5)
    raise TimeoutError(f"{fs_id} did not reach {target}")


def _wait_mt(client, mt_id: str, target="available", timeout=180) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            mt = client.describe_mount_targets(MountTargetId=mt_id)["MountTargets"][0]
        except ClientError:
            if target == "deleted":
                return
            raise
        if mt["LifeCycleState"] == target:
            return
        print(f"  mount target {mt_id}: {mt['LifeCycleState']} ...")
        time.sleep(5)


def create_filesystem(region: str, name: str, throughput_mode="elastic",
                      encrypted=True, transition_to_ia="AFTER_30_DAYS") -> str:
    c = efs(region)
    fs = c.create_file_system(
        CreationToken=name,           # idempotency token
        Encrypted=encrypted,          # KMS at rest
        ThroughputMode=throughput_mode,
        Tags=[{"Key": "Name", "Value": name}],
    )
    fs_id = fs["FileSystemId"]
    print(f"creating filesystem {fs_id} ...")
    _wait_fs(c, fs_id, "available")
    if transition_to_ia:
        c.put_lifecycle_configuration(
            FileSystemId=fs_id,
            LifecyclePolicies=[{"TransitionToIA": transition_to_ia}],
        )
        print(f"  lifecycle: files -> IA {transition_to_ia}")
    print(f"  available: {fs_id}")
    return fs_id


def add_mount_target(region: str, fs_id: str, subnet_id: str, sg_ids: list[str]) -> str:
    """Create a mount target (an ENI) in a subnet. One per AZ; the SG must allow NFS 2049."""
    c = efs(region)
    mt = c.create_mount_target(FileSystemId=fs_id, SubnetId=subnet_id, SecurityGroups=sg_ids)
    mt_id = mt["MountTargetId"]
    print(f"creating mount target {mt_id} in {subnet_id} ...")
    _wait_mt(c, mt_id, "available")
    print(f"  available: {mt_id} (IP {mt['IpAddress']})")
    return mt_id


def create_access_point(region: str, fs_id: str, path="/app", uid=1001, gid=1001) -> str:
    """Access Point: pin a POSIX identity + root dir (per-app/tenant isolation)."""
    c = efs(region)
    ap = c.create_access_point(
        FileSystemId=fs_id,
        PosixUser={"Uid": uid, "Gid": gid},
        RootDirectory={"Path": path,
                       "CreationInfo": {"OwnerUid": uid, "OwnerGid": gid, "Permissions": "0755"}},
        Tags=[{"Key": "Name", "Value": f"ap{path}"}],
    )
    ap_id = ap["AccessPointId"]
    print(f"created access point {ap_id} ({path} as {uid}:{gid})")
    return ap_id


def show(region: str) -> None:
    c = efs(region)
    for fs in c.describe_file_systems()["FileSystems"]:
        name = next((t["Value"] for t in fs.get("Tags", []) if t["Key"] == "Name"), "-")
        size = fs["SizeInBytes"]["Value"]
        print(f"{fs['FileSystemId']}  {fs['LifeCycleState']:<10}  "
              f"{fs['ThroughputMode']:<10}  {size/1e6:.1f} MB  enc={fs['Encrypted']}  name={name}")
        for mt in c.describe_mount_targets(FileSystemId=fs["FileSystemId"])["MountTargets"]:
            print(f"    mt {mt['MountTargetId']}  {mt['AvailabilityZoneName']}  {mt['IpAddress']}  {mt['LifeCycleState']}")


def cleanup(region: str, fs_id: str) -> None:
    """Delete access points + mount targets (wait) + the filesystem. Order matters."""
    c = efs(region)
    for ap in c.describe_access_points(FileSystemId=fs_id)["AccessPoints"]:
        c.delete_access_point(AccessPointId=ap["AccessPointId"])
        print(f"deleted access point {ap['AccessPointId']}")
    mts = c.describe_mount_targets(FileSystemId=fs_id)["MountTargets"]
    for mt in mts:
        c.delete_mount_target(MountTargetId=mt["MountTargetId"])
        print(f"deleting mount target {mt['MountTargetId']} ...")
    for mt in mts:
        _wait_mt(c, mt["MountTargetId"], "deleted")
    # A filesystem can only be deleted once all mount targets are gone.
    try:
        c.delete_file_system(FileSystemId=fs_id)
        print(f"deleted filesystem {fs_id}")
    except ClientError as e:
        print(f"  filesystem {fs_id}: {e}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--region", default="us-east-1")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("show")
    cf = sub.add_parser("create"); cf.add_argument("--name", default="boto3-efs-demo")
    mt = sub.add_parser("mount-target"); mt.add_argument("--fs-id", required=True)
    mt.add_argument("--subnet-id", required=True); mt.add_argument("--sg-ids", nargs="+", required=True)
    ap = sub.add_parser("access-point"); ap.add_argument("--fs-id", required=True)
    ap.add_argument("--path", default="/app")
    cl = sub.add_parser("cleanup"); cl.add_argument("--fs-id", required=True)

    args = p.parse_args()
    if args.cmd == "show":
        show(args.region)
    elif args.cmd == "create":
        create_filesystem(args.region, args.name)
    elif args.cmd == "mount-target":
        add_mount_target(args.region, args.fs_id, args.subnet_id, args.sg_ids)
    elif args.cmd == "access-point":
        create_access_point(args.region, args.fs_id, args.path)
    elif args.cmd == "cleanup":
        cleanup(args.region, args.fs_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
