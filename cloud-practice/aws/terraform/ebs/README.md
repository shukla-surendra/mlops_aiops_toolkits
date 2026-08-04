# Terraform: EBS volumes, encryption & automated backups

Creates a small EC2 instance and attaches **KMS-encrypted** EBS volumes to it, plus a **Data Lifecycle Manager** policy that snapshots them daily. Demonstrates the concepts in [`../../docs/ebs/`](../../docs/ebs/README.md): the network-attached volume, same-AZ attachment, encryption via a customer-managed key, gp3 vs io2, and production-standard backups.

> ⚠️ **Creates billable resources** (EC2 + EBS volumes + KMS key + snapshots). Run `terraform destroy` when done. `terraform plan` alone is free.

## What it creates

```
KMS key (customer-managed, rotation on)
EC2 instance (AL2023, encrypted gp3 root)
 ├── gp3 data volume (encrypted, /dev/sdf → /dev/nvme1n1)   [Backup=true]
 └── io2 data volume (optional, /dev/sdg)                    [Backup=true]
DLM policy → daily snapshot of Backup=true volumes, keep 7
```

## Files
| File | Purpose |
|---|---|
| `versions.tf` | Provider pins + default tags |
| `variables.tf` | Region/AZ, volume sizing, io2 toggle, DLM toggle |
| `main.tf` | KMS key, instance, gp3 + optional io2 volumes, attachments |
| `dlm.tf` | DLM IAM role + daily backup policy |
| `outputs.tf` | IDs + a `next_steps` runbook |

## Usage
```bash
cd aws/terraform/ebs
cp terraform.tfvars.example terraform.tfvars   # edit as needed
terraform init
terraform plan            # free — inspect
terraform apply           # creates resources ($)
terraform output next_steps
terraform destroy         # clean up
```

## Things to try (mini-labs)
1. `plan` with `create_io2 = true` vs `false` — see the provisioned-IOPS volume + attachment appear.
2. Bump `gp3_iops`/`gp3_throughput` and `apply` — an **Elastic Volumes** modify in place (no recreate).
3. Change `gp3_size_gib` up and `apply`, then in the guest `xfs_growfs` to see volume-vs-filesystem resize.
4. Inspect the DLM policy in the console; after a day, confirm snapshots appear tagged `SnapshotCreator=dlm`.

## Deliberately minimal
- No SSM instance profile wired (add `AmazonSSMManagedInstanceCore` to connect via Session Manager), no security group beyond default. This module is about **storage**, not access — see the VPC module for networking.
