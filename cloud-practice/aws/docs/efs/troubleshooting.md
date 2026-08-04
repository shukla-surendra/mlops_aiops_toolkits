# EFS — Troubleshooting & debugging

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [security.md](security.md), [performance.md](performance.md).

Spec section 14. EFS incidents cluster into: **can't mount**, **mount hangs**, **it's slow**, and **permission denied**.

---

## 1. "Mount fails / hangs"

The mount chain — check in order:
1. **Security Group:** does the **mount target SG allow TCP 2049 from the client's SG/IP**? Missing 2049 = the #1 cause; a hang (not an error) is the classic symptom.
2. **Mount target exists in the client's AZ?** No mount target in that AZ → no local door. Create one per AZ.
3. **NACL:** subnet NACL allows 2049 + ephemeral ports (stateless!).
4. **DNS:** the filesystem DNS name resolves only inside the VPC with **DNS resolution + hostnames enabled** (VPC attributes). From on-prem/peered VPCs you need the mount target IP or proper DNS. `nslookup fs-xxx.efs.region.amazonaws.com`.
5. **efs-utils / package:** using `-o tls` or `-o iam`? You need **`amazon-efs-utils`** installed; a plain `mount -t efs` without it fails.
6. **TLS/IAM policy:** if the filesystem policy **requires TLS** and you mount plain `nfs4`, you're denied — mount `-o tls`. If it requires IAM, mount `-o iam` with a role that's allowed.

Quick client test: `telnet fs-xxx.efs.region.amazonaws.com 2049` (or `nc -vz`) — connection refused/timeout ⇒ network/SG/NACL, not EFS.

## 2. "Permission denied on files"

- **POSIX mismatch:** the file's uid/gid vs the client's user. EFS enforces POSIX; a container running as uid 1001 can't write files owned by root unless permissions allow.
- **Access Point enforcement:** if mounting through an **Access Point**, you're pinned to its uid/gid + root dir — your process's own uid is overridden. Check the AP's `PosixUser`/`RootDirectory`.
- **IAM policy:** `ClientWrite` not granted → read-only or denied. Check the filesystem policy + the role.

## 3. "EFS is slow"

- **Bursting on a small filesystem** → low baseline; `BurstCreditBalance` near 0. → **Elastic** throughput.
- **Serial / tiny-file workload** → per-op latency dominates. → parallelize; larger I/O; reconsider whether these should be S3 objects.
- **General Purpose ops ceiling** → `PercentIOLimit` ~100%. Rare; redesign access pattern.
- **Cross-AZ mount** → mounting a non-local mount target adds latency + cross-AZ cost. → mount the AZ-local target (efs-utils/DNS handles this).
- **Cold IA data** → files tiered to IA have higher first-byte latency + retrieval cost on access.
- Measure with `nfsiostat`, and CloudWatch `PercentIOLimit` / `BurstCreditBalance` / throughput metrics.

## 4. "Mounts drop / stale file handle"

- Network blips or SG/NACL changes mid-session → NFS retries; `amazon-efs-utils` adds resilient mount options. Use it and the recommended mount options; consider `_netdev` + automount in fstab so boot doesn't hang waiting for the network.
- **Stale file handle** after aggressive changes → remount.

## 5. Tools
- Client: `mount | grep efs`, `nfsiostat`, `dmesg`, `telnet/nc host 2049`, `nslookup`.
- AWS: `describe-mount-targets`, `describe-file-systems`, CloudWatch EFS metrics, the mount target SG, filesystem policy, VPC Reachability Analyzer (client ENI → mount target ENI:2049).
- efs-utils logs: `/var/log/amazon/efs/mount.log`.

---

## Sources
- AWS docs: *Troubleshooting Amazon EFS*, *Mounting issues*, *amazon-efs-utils*, *Access Points*, *Filesystem policies*.

---

## Self-check
1. A mount command hangs (no error). What's the single most likely cause and how do you confirm it in 10 seconds?
2. From an on-prem host over VPN you can't mount by DNS name. What are the two likely issues?
3. A container gets "permission denied" writing to EFS. List the three layers you'd check.
4. A new small EFS is slow. Which metric + which mode change fixes it?
5. Which package must be installed to use `-o tls`/`-o iam`, and where are its mount logs?
