# Azure Track — Architecture & Internals

Same rigor, same learning contract as `aws/`: architecture/internals depth (not
certification-oriented), one service at a time, progressive **gated modules**, every
internal claim tagged **[Documented]** vs **[Inferred]**. See [PROGRESS.md](../PROGRESS.md)
for the master tracker — read it first in any session.

**Taught by contrast with AWS.** Every module leans on the AWS mental model already built
in `aws/docs/` rather than re-deriving networking/storage/compute from zero — the fastest
path to real Azure depth when the AWS internals are already solid. Where Azure's own
history, terminology, or architecture genuinely diverges (and it does, more than most
AWS-to-Azure "translation" content suggests), that divergence is called out explicitly
rather than papered over.

If you just need a fast service-mapping reference rather than the full gated curriculum,
see [`../aws-to-azure-transition-guide.md`](../aws-to-azure-transition-guide.md) — a
standalone bridge doc, not part of this track, written before this track existed.

## Current focus

Three services have M1 docs in progress at once (a deliberate breadth-over-strict-sequencing
choice — see `PROGRESS.md` Changelog, 2026-08-08 entry, for why the "one service at a time,
gate before advancing" rule was explicitly relaxed here rather than silently dropped):

- **#1 Virtual Network (VNet)** — direct contrast pair to `aws/`'s VPC.
  [`docs/vnet/architecture.md`](docs/vnet/architecture.md) ·
  gate: [`quizzes/vnet/module-1-gate.md`](quizzes/vnet/module-1-gate.md) — 🟡 OPEN
- **#4 Microsoft Entra ID + Azure RBAC** — direct contrast pair to `aws/`'s (not-yet-written)
  IAM. [`docs/entra-id/architecture.md`](docs/entra-id/architecture.md) ·
  gate: [`quizzes/entra-id/module-1-gate.md`](quizzes/entra-id/module-1-gate.md) — 🟡 OPEN
- **#5 Blob Storage** — direct contrast pair to `aws/`'s S3, including why a Storage Account
  also hosts Table/Queue/File storage.
  [`docs/blob-storage/architecture.md`](docs/blob-storage/architecture.md) ·
  gate: not yet written

## Layout

Mirrors `aws/`:

```
azure/
├── docs/<service>/{architecture,internals,networking,security,best-practices,troubleshooting,interview}.md
├── quizzes/<service>/
├── terraform/<service>/     # azurerm provider
├── python/<service>/        # Azure SDK for Python (azure-mgmt-*), the Azure analogue of aws/boto3/
├── labs/<service>/
└── cheatsheets/
```

Folders are created as each service/module is covered, not scaffolded empty upfront — same
convention as `aws/`.

## Planned service order (mirrors AWS's order, for direct contrast)

| # | Azure service | AWS contrast pair | Status |
|---|---|---|---|
| 1 | **Virtual Network (VNet)** | VPC | 🟡 M1 delivered, gate OPEN |
| 2 | Managed Disks | EBS | ⬜ Planned (note: built on Blob Storage's Page Blobs — see `blob-storage/architecture.md` §3e) |
| 3 | Azure Files | EFS | ⬜ Planned |
| 4 | **Microsoft Entra ID + Azure RBAC** | IAM (not yet written on the AWS side) | 🟡 M1 delivered, gate OPEN |
| 5 | **Blob Storage** | S3 | 🟡 M1 delivered, gate not yet written |
| 6 | Virtual Machines / Hyper-V | EC2 / Nitro | ⬜ Planned |
| 7 | Azure DNS | Route 53 | ⬜ Planned |
| 7 | Load Balancer / Application Gateway | ELB (ALB/NLB) | ⬜ Planned |
| 8 | Azure SQL Database / Cosmos DB | RDS/Aurora / DynamoDB | ⬜ Planned |
| 9 | Azure Functions | Lambda | ⬜ Planned |
| … | (Key Vault, Service Bus/Event Grid, Front Door/CDN, AKS, Monitor) | KMS, SQS/SNS, CloudFront, EKS, CloudWatch | ⬜ Backlog |

See [PROGRESS.md](../PROGRESS.md) for current position and the full learning contract.
