# 2. State & Backends

> Terraform's memory: what state is, why it's required, local vs remote, backend config, locking, state scope, state commands, and the dependency graph.

Related: [Fundamentals](01-fundamentals.md) · [Project structure](03-project-structure.md)

---

## What is state?

State is Terraform's record of the infrastructure addresses, resource identities, and metadata for what it manages. It maps your configuration to real cloud resources.

```text
Terraform Code
      |
      v
terraform.tfstate
      |
      v
AWS Resources
```

Terraform uses state to know what already exists, what needs creating, updating, or deleting.

## Why is state required?

Without state, Terraform would have to rediscover every resource on every run. State stores:

- Resource IDs
- Metadata
- Dependencies
- Outputs

**Never edit the state file manually.**

---

## Local vs remote state

### Local state (`terraform.tfstate` on disk)

- **Pros:** simple, good for learning.
- **Cons:** not shared, easy to lose, poor fit for teams.

### Remote state (enterprise)

Typical AWS backend:

```text
Terraform
   |
S3 Bucket        (versioned, encrypted)
   |
S3 Lockfile      (use_lockfile = true)
```

- **Benefits:** shared, versioned, encrypted, locked, recoverable.
- **Never store state in Git.**

---

## Backend configuration

```hcl
terraform {
  backend "s3" {
    bucket       = "company-tf-state"
    key          = "payments/dev/terraform.tfstate"
    region       = "ap-south-1"
    use_lockfile = true
    encrypt      = true
  }
}
```

> Older configurations use a `dynamodb_table` for locking, but HashiCorp has **deprecated DynamoDB-based locking** for the S3 backend in favor of native **S3 lockfiles** (`use_lockfile = true`).

---

## State locking

Without locking, two engineers running `terraform apply` at once corrupt the same state:

```text
Engineer A ──> Lock Acquired ──> Apply ──> Release Lock
Engineer B ──> waits...
```

With `use_lockfile = true` on the S3 backend, Terraform acquires a lock before writing and releases it after, so concurrent applies serialize instead of colliding.

---

## One state or many?

**❌ One giant state** (`company.tfstate`) → slow, huge blast radius, merge conflicts.

**✅ One state per independently deployable project/environment:**

```text
payments/dev.tfstate
payments/prod.tfstate
crm/dev.tfstate
network/prod.tfstate
```

> **Rule:** one independently deployable project/environment = one state file. Smaller states reduce blast radius, speed up plans, and simplify approvals and ownership.

---

## State commands

```bash
terraform init                              # initialize backend
terraform state list                        # list resources
terraform state show aws_instance.web       # inspect a resource
terraform state mv OLD NEW                   # move/rename in state
terraform state rm RESOURCE                  # stop managing (doesn't delete real infra)
terraform import aws_s3_bucket.logs my-bucket  # bring existing infra under management
```

Prefer **declarative `import` blocks** over one-off CLI imports for team workflows — they're reviewable in a pull request:

```hcl
import {
  to = aws_s3_bucket.logs
  id = "my-bucket"
}
```

Avoid ad hoc `terraform state` surgery when a declarative approach exists.

---

## Dependency graph

Terraform builds a graph from references (resource attributes, module outputs, data sources, explicit `depends_on`) and deploys in dependency order — independent resources in parallel, dependent ones in sequence.

```text
VPC
 |
Subnets
 |
Security Group
 |
ECS Service
```

Emit it with:

```bash
terraform graph
```

---

## Day-to-day workflow

```text
init → fmt → validate → plan → Review → apply
```

In mature teams, `plan` and `apply` for shared environments run in **CI/CD**, not on a developer laptop — see [Variables, CI/CD & operations](04-variables-cicd-and-operations.md).

---

## Summary

- State is Terraform's memory.
- Backends make collaboration safe (shared, versioned, encrypted).
- Locking (`use_lockfile = true`) prevents corruption.
- Small, isolated states scale better.
- The dependency graph determines execution order.
