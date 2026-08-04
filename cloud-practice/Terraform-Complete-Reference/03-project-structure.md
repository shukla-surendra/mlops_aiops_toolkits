# 3. Project Structure & Organization

> How to organize Terraform so it scales from one engineer to many teams without becoming a monolith: root vs child modules, module design, repo layouts, environments, workspaces, and ownership.

Related: [State & backends](02-state-and-backends.md) · [Variables, CI/CD & operations](04-variables-cicd-and-operations.md)

---

## Why organization matters

Writing Terraform is straightforward. **Operating** it across many applications, environments, and teams is where most failures happen. A good structure should:

- Be easy to understand
- Minimize merge conflicts
- Support multiple environments
- Keep state isolated
- Match team ownership
- Encourage reuse
- Reduce deployment blast radius

---

## The biggest structural mistake: environment-first

Many teams start by making the top-level split *environments*:

```text
terraform/
├── dev/
├── qa/
├── prod/
├── main.tf
└── variables.tf
```

This works for a demo but breaks down at scale: oversized state files, poor ownership boundaries, slower plans, larger blast radius, more merge conflicts. If one team changes a shared state (say a security group), another team is blocked even though they're deploying a different application.

> **The real lesson:** scope Terraform state to logically related, **independently deployable** infrastructure — not to environments at the top level.

## Think in deployable units

Organize around projects, workloads, or platform domains:

```text
terraform/
├── customer-portal/
├── payments/
├── analytics/
├── networking/
├── security/
└── shared-services/
```

Each directory represents one deployable root module (or a clearly grouped set). Environment separation still matters — but it lives *inside* each workload via separate directories, backend keys, pipelines, or repositories (see below).

---

## Root module vs child module

Every deployable unit has **one root module** — the directory where Terraform commands run:

```text
payments/
├── main.tf
├── variables.tf
└── outputs.tf
```

The root module **assembles** reusable child modules instead of duplicating infrastructure:

```hcl
module "vpc" {
  source = "git::https://git.company.com/terraform-modules.git//networking/vpc?ref=v2.0.0"
}

module "database" {
  source = "git::https://git.company.com/terraform-modules.git//database/rds?ref=v1.4.1"
}
```

> **Rule:** one root module per deployable unit; many child modules where reuse makes sense. Pin module versions with `?ref=`.

---

## Good module design

A module should have **one responsibility**. Good examples: VPC, RDS, ECS, EKS, IAM Role, S3 Bucket. Avoid "mega modules" that build an entire application stack.

Standard module layout:

```text
modules/
└── vpc/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── versions.tf
    ├── README.md
    └── examples/
```

Keep modules reusable, small, documented, versioned. Add `examples/` for common usage, variable validation for safer inputs, and `sensitive = true` on outputs that shouldn't be displayed casually.

### Why separate reusable modules?

If five applications each copy-paste similar networking/IAM/database resources, you get drift and review fatigue. Extracting them into versioned modules gives less duplication, easier maintenance, more consistent security controls, cleaner reviews, and safer upgrades.

```text
terraform-modules/
├── vpc/
├── iam-role/
├── rds/
└── s3-bucket/
```

---

## Variables, locals, and outputs

```hcl
# Variables — receive input
variable "environment" {
  type = string
}

# Locals — avoid repeated values
locals {
  common_tags = {
    Project = "Payments"
  }
}

# Outputs — expose values
output "vpc_id" {
  value = aws_vpc.main.id
}
```

Use variable validation when invalid inputs would create unsafe or expensive infrastructure. **How variable values are supplied and overridden per environment** is covered in [Variables, CI/CD & operations](04-variables-cicd-and-operations.md).

---

## Environment strategy

Most real systems need multiple environments (`dev`, `qa`, `uat`, `stage`, `prod`, `dr`). Recommended: separate state, backend key, pipeline, and credentials/roles where access boundaries differ.

Three common ways to model them:

**Option 1 — Separate directories**
```text
payments/
├── dev/
├── qa/
├── stage/
└── prod/
```

**Option 2 — Separate repositories**
```text
payments-dev-infra/
payments-prod-infra/
```

**Option 3 — Same repo, separate backend keys + pipelines**
```text
payments/
└── live/
    ├── dev/
    └── prod/
```

Typical per-environment differences: variable values, backend key/state location, pipeline approvals, resource sizing, integrations and access controls. Example backend keys:

```text
payments/dev/terraform.tfstate
payments/prod/terraform.tfstate
```

---

## Workspaces

Terraform workspaces give multiple states from one configuration:

```bash
terraform workspace list
terraform workspace new dev
terraform workspace select prod
```

Good for **personal testing** and small projects. Be careful using them for shared, long-lived environments (`dev`/`stage`/`prod`): large teams usually prefer separate directories, repositories, or backend keys because those are easier to understand, review, and audit. This matches HashiCorp's own guidance that workspaces are **not** a substitute for separate credentials and access boundaries.

---

## Repository layout options

There's no single correct structure — pick one that matches team size and ownership.

**Option 1 — Monorepo** (best for smaller platform teams)
```text
company-infra/
├── networking/
├── security/
├── shared-services/
├── payments/
├── hr/
└── analytics/
```
Pros: easy discovery, easier large-scale refactoring. Cons: more merge conflicts, broader CI/CD scope, harder ownership.

**Option 2 — Repository per project/domain** (common enterprise model)
```text
terraform-modules/
networking-infra/
security-infra/
payments-infra/
customer-portal-infra/
analytics-infra/
```
Pros: independent deployments, clear ownership, smaller pipelines, easier access control. Cons: more repos to manage.

---

## Enterprise case study

An org with 100+ applications, multiple business units, shared networking/security teams, platform engineers maintaining reusable modules, and dev/QA/UAT/prod/DR environments — wanting infrastructure that's version-controlled, repeatable, auditable, secure, and automated — often lands on:

```text
company/
├── terraform-modules/          # reusable child modules (Platform Team)
│   ├── networking/
│   ├── compute/
│   ├── storage/
│   ├── database/
│   └── security/
├── platform-live/              # shared foundation root modules
│   ├── networking/
│   ├── security/
│   ├── identity/
│   └── shared-services/
├── applications/               # per-app root modules (app teams)
│   ├── hr/
│   ├── finance/
│   ├── payments/
│   ├── analytics/
│   └── customer-portal/
└── docs/
```

| Area | Owner |
|------|-------|
| `terraform-modules` | Platform Team |
| `networking` | Network Team |
| `security` | Security Team |
| `shared-services` | Platform Team |
| `payments` | Payments Team |
| `customer-portal` | Customer Portal Team |

> Terraform structure should reflect **organizational boundaries, approval paths, and deployment ownership** — application teams consume approved module versions rather than copying infrastructure code.

---

## Design principles

- Organize by ownership and deployability first.
- Keep environments explicit.
- Keep state small and isolated (one per root module + environment).
- Separate reusable modules from live infrastructure; version shared modules.
- Reuse patterns instead of copying code.
- Keep repository boundaries clear; standardize layouts across teams.
- Treat Terraform like production code — review, test, CI/CD.
- Prefer declarative imports over ad hoc state surgery.

## Common mistakes

- One state file for unrelated systems
- One huge repository with unclear ownership
- Copy-pasting Terraform between applications
- Giant modules that build entire platforms
- Hardcoded values and credentials
- Mixing platform, networking, and application concerns without boundaries
- Using workspaces as the primary strategy for all shared environments
- Running production changes without review

---

## Summary

Terraform scales when root modules match deployable units, states are isolated per root module + environment, shared infrastructure is versioned as reusable modules, repository structure matches team ownership, and delivery happens through repeatable pipelines. The goal isn't tidy folders — it's letting many engineers change infrastructure safely at the same time.
