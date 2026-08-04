# 1. Terraform Fundamentals

> What Terraform is, its architecture and lifecycle, the files in a project, the core commands, and what happens during a run.

Related: [State & backends](02-state-and-backends.md) · [Project structure](03-project-structure.md)

---

## What is Terraform?

Terraform is an Infrastructure as Code (IaC) tool that provisions and manages infrastructure from declarative configuration.

**Benefits**
- Version controlled
- Repeatable
- Automated
- Reviewable
- Multi-cloud

---

## Architecture

```text
Terraform CLI
     |
Configuration (.tf)
     |
 Provider plugin
     |
 Cloud API (AWS/Azure/GCP)
```

Components:
- **CLI** — the command you run
- **Configuration** — your `.tf` files (HCL)
- **Provider** — plugin that knows a specific platform (AWS, Azure, GitHub, …)
- **State** — Terraform's record of what it manages
- **Backend** — where state lives (local disk or remote, e.g. S3)

---

## Lifecycle

```text
Write Code
    ↓
terraform init      # download providers, configure backend
    ↓
terraform fmt       # format
    ↓
terraform validate  # static checks
    ↓
terraform plan      # preview changes
    ↓
Review
    ↓
terraform apply     # execute
    ↓
Infrastructure
```

---

## Project files

A single directory is one **root module**; Terraform loads *all* `.tf` files in it together, so splitting files is for readability and ownership, not execution order.

```text
project/
├── main.tf
├── provider.tf
├── variables.tf
├── outputs.tf
├── versions.tf
├── terraform.tfvars
└── modules/
```

| File | Purpose |
|------|---------|
| `main.tf` | Resources |
| `provider.tf` | Provider configuration |
| `variables.tf` | Input variables |
| `outputs.tf` | Exported values |
| `versions.tf` | Terraform + provider version constraints |
| `terraform.tfvars` | Variable values for a specific use case |

As the project grows, split `main.tf` by concern (`network.tf`, `compute.tf`, `database.tf`, `security.tf`) — it's still one root module and one deployment unit.

A minimal end-to-end example:

```hcl
provider "aws" {
  region = "ap-south-1"
}

variable "instance_type" {
  type = string

  validation {
    condition     = contains(["t3.micro", "t3.small"], var.instance_type)
    error_message = "Use an approved instance type."
  }
}

resource "aws_instance" "web" {
  ami           = "ami-xxxxxxxx"
  instance_type = var.instance_type
}

output "instance_id" {
  value = aws_instance.web.id
}
```

---

## Core commands

```bash
terraform init        # initialize backend + download providers
terraform fmt         # format code
terraform validate    # static validation
terraform test        # run tests (terraform test framework)
terraform plan        # preview changes
terraform apply       # apply changes
terraform destroy     # tear down
terraform output      # show outputs
terraform show        # inspect state/plan
terraform providers   # list providers
terraform graph       # emit dependency graph
```

State subcommands are covered in [State & backends](02-state-and-backends.md).

---

## What happens during a run

1. Read the root module and child modules
2. Parse variables, locals, data sources, resources, outputs
3. Resolve provider requirements and download/reuse plugins (`init`)
4. Read current state from the backend
5. Build a dependency graph
6. Refresh / read real infrastructure via providers
7. Compare desired config against current state
8. Produce an execution plan
9. Execute the graph in dependency order (independent resources in parallel)
10. Update state after successful operations

Deeper internals are in [Internals & tool comparison](05-internals-and-comparison.md).

---

## Modules in one line

- **One root module** per deployment (the directory where you run `terraform`).
- **Many reusable child modules** called from the root.

```hcl
module "vpc" {
  source = "../modules/vpc"
}
```

Full module design and repo organization: [Project structure](03-project-structure.md).

---

## Best practices (intro)

- Keep modules small and focused
- Review every plan; save reviewed plans for production applies
- Pin Terraform and provider versions
- Store state remotely, one state per application/environment
- Never commit secrets or manually edit state
- Add variable validation; mark sensitive values
- Automate through CI/CD

## Common mistakes (intro)

- One giant state file / one huge `main.tf`
- Hardcoded values and credentials
- No module versioning
- Secrets in Git
- Manual state edits
- Applying without reviewing the plan
