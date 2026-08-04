# Terraform: EFS filesystem, mount targets, Access Point & TLS policy

Creates an encrypted EFS filesystem with **per-AZ mount targets**, a Security Group gating **NFS 2049**, an **Access Point** (uid/gid + root dir isolation), lifecycle tiering to IA, and a **filesystem policy that refuses non-TLS mounts**. Demonstrates [`../../docs/efs/`](../../docs/efs/README.md).

> ⚠️ **Creates billable resources** (EFS storage + throughput). Cheap when empty, but run `terraform destroy` when done. `terraform plan` is free.

## What it creates
```
EFS filesystem (encrypted, elastic throughput, lifecycle → IA after 30d)
 ├── mount target per AZ (ENI + SG allowing NFS 2049 from clients)
 ├── Access Point /app (uid/gid 1001)  ← per-app isolation
 └── filesystem policy: DENY any mount without TLS
```

## Files
| File | Purpose |
|---|---|
| `versions.tf` | Provider pins + default tags |
| `variables.tf` | One Zone toggle, throughput mode, lifecycle, client CIDR |
| `main.tf` | VPC/subnet lookups, SG, filesystem, mount targets, Access Point, TLS policy |
| `outputs.tf` | IDs, DNS name, ready-to-paste `mount_command` |

## Usage
```bash
cd aws/terraform/efs
cp terraform.tfvars.example terraform.tfvars   # edit
terraform init
terraform plan
terraform apply
terraform output mount_command      # copy onto a client instance
terraform destroy
```

## Things to try (mini-labs)
1. `one_zone = true` vs `false` — watch the number of mount targets change (multi-AZ vs single).
2. `throughput_mode = "bursting"` vs `"elastic"` — inspect the plan; read [performance.md](../../docs/efs/performance.md) on why a small Bursting FS is slow.
3. Launch **two** EC2 instances in different AZs, mount the filesystem on both (`-o tls`), write from one, read from the other → **shared multi-AZ POSIX access** (the thing EBS can't do).
4. Mount via the **Access Point** and confirm files are created as uid 1001 under `/app`.
5. Try mounting **without** `-o tls` → denied by the filesystem policy.

## Deliberately minimal
- Uses the **default VPC** (one subnet/AZ) to stay self-contained; in production reference the [VPC module](../vpc/README.md) subnets and a **client SG** instead of a CIDR.
- No EC2 client is created here — bring your own (or the [EBS module's](../ebs/README.md) instance).
