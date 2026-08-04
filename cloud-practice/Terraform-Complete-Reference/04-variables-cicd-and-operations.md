# 4. Variables, CI/CD & Operations

> How variable values get supplied and **overridden**, how Terraform runs in a **pipeline** (with a real GitHub Actions example), plus drift detection, imports, troubleshooting, and the pre-deploy checklist.

Related: [Project structure](03-project-structure.md) · [State & backends](02-state-and-backends.md)

---

## How variables get set — and overridden

This is the part most references skip. Terraform collects a variable's value from several sources, and when more than one provides a value, **the highest-precedence source wins**. From lowest to highest:

```text
1. default in the variable block          (lowest — fallback)
2. TF_VAR_<name> environment variable
3. terraform.tfvars  /  terraform.tfvars.json
4. *.auto.tfvars  /  *.auto.tfvars.json     (loaded alphabetically)
5. -var-file=... on the CLI                 (in the order given)
6. -var=... on the CLI                      (highest — last one wins)
```

Key rules:
- **Later source overrides earlier** for the same variable — so a `-var` on the command line beats everything, and a `default` is only used when nothing else supplies a value.
- `terraform.tfvars` and `*.auto.tfvars` are loaded **automatically**; any other `.tfvars` file must be passed explicitly with `-var-file`.
- Among `*.auto.tfvars` files, load order is **alphabetical**, so a later filename can override an earlier one.
- Environment variables use the prefix `TF_VAR_` (e.g. `TF_VAR_region=ap-south-1` sets `var.region`). This is how pipelines inject secrets without writing them to disk.

### Worked example

```hcl
# variables.tf
variable "instance_type" {
  type    = string
  default = "t3.micro"
}
```

```hcl
# terraform.tfvars
instance_type = "t3.small"
```

```bash
# env var (lower precedence than tfvars files)
export TF_VAR_instance_type="t3.medium"

# these both lose to the CLI flag below
terraform apply                                  # -> t3.small  (terraform.tfvars beats TF_VAR_ and default)
terraform apply -var-file=prod.tfvars            # -> whatever prod.tfvars says (beats terraform.tfvars)
terraform apply -var="instance_type=t3.large"    # -> t3.large  (CLI -var wins over everything)
```

### How this is used per environment

The idiomatic pattern is one root module, one `.tfvars` file per environment, selected at plan/apply time:

```text
payments/
├── main.tf
├── variables.tf
└── envs/
    ├── dev.tfvars
    ├── stage.tfvars
    └── prod.tfvars
```

```bash
terraform plan  -var-file=envs/prod.tfvars -out=tfplan
terraform apply tfplan
```

Secrets are **not** put in `.tfvars` in Git — they come from `TF_VAR_*` env vars sourced from a secrets store (Vault, AWS Secrets Manager, GitHub/GitLab CI secrets) in the pipeline.

> Related knobs: `-var`/`-var-file` also work for module inputs indirectly (a root variable feeds a `module` block argument). Backend config values (bucket/key) are **not** normal variables — override those with `terraform init -backend-config=...`, not `-var`.

---

## Terraform in CI/CD

Shared or production deployments should **not** rely on engineers running `terraform apply` from laptops. A typical pipeline:

```text
Developer
   │  git push / PR
   ▼
terraform fmt -check
   ▼
terraform validate
   ▼
tflint
   ▼
Security scan (Checkov / tfsec)
   ▼
terraform plan -out=tfplan        # per-environment -var-file
   ▼
Review & manual approval (for prod)
   ▼
terraform apply tfplan            # apply the exact reviewed artifact
   ▼
Notification
```

**Why:** consistent deployments, an audit trail, peer review, and reduced production risk. Local applies are fine for personal sandboxes, but a poor default for team-owned environments.

### A concrete GitHub Actions example

This runs `plan` on every PR and a gated `apply` on merge to `main`, uses **OIDC** to assume an AWS role (no long-lived keys), and injects the environment via `-var-file`:

```yaml
name: terraform

on:
  pull_request:
  push:
    branches: [main]

permissions:
  id-token: write        # required for OIDC
  contents: read

env:
  TF_IN_AUTOMATION: "true"
  ENVIRONMENT: prod

jobs:
  plan:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: payments
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.5     # pin the version

      # Assume an AWS role via OIDC — no static credentials
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/terraform-ci
          aws-region: ap-south-1

      - run: terraform init
      - run: terraform fmt -check
      - run: terraform validate
      - run: terraform plan -input=false -var-file=envs/${{ env.ENVIRONMENT }}.tfvars -out=tfplan

      - name: Save plan artifact
        uses: actions/upload-artifact@v4
        with:
          name: tfplan
          path: payments/tfplan

  apply:
    needs: plan
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: prod          # GitHub "Environment" gives the manual-approval gate
    defaults:
      run:
        working-directory: payments
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.5
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/terraform-ci
          aws-region: ap-south-1
      - uses: actions/download-artifact@v4
        with:
          name: tfplan
          path: payments
      - run: terraform init
      - run: terraform apply -input=false tfplan   # apply the reviewed artifact, no re-plan
```

Notes:
- **Secrets** (e.g. a DB password) come from `secrets` as `TF_VAR_*` env vars, not from files in Git:
  `env: { TF_VAR_db_password: ${{ secrets.DB_PASSWORD }} }`.
- The `environment: prod` block is where you attach **required reviewers** for the manual approval gate.
- Applying the saved `tfplan` guarantees you deploy exactly what was reviewed, even if `main` moved.

### Useful CI/CD tools

| Tool | Common usage |
|------|--------------|
| GitHub Actions | GitHub repositories |
| GitLab CI | GitLab projects |
| Jenkins | Legacy enterprises |
| AWS CodePipeline | AWS-native pipelines |
| HCP Terraform | Remote execution, state, policy, runs |
| Atlantis | PR-based Terraform workflows |

---

## Drift detection

Drift happens when infrastructure is changed outside Terraform (e.g. someone edits a security group in the console). Detect it with:

```bash
terraform plan
```

Enterprise teams schedule plans daily/weekly to catch unexpected changes. For production, save and apply the exact reviewed artifact:

```bash
terraform plan -out=tfplan
terraform apply tfplan
```

---

## Importing existing resources

Terraform can adopt resources created manually:

```bash
terraform import aws_s3_bucket.logs my-company-logs
```

After importing, make sure matching configuration exists so future plans stay clean. On current versions, prefer **`import` blocks** in configuration so imports are reviewable in a PR:

```hcl
import {
  to = aws_s3_bucket.logs
  id = "my-company-logs"
}
```

---

## Troubleshooting workflow

```text
terraform validate
   ↓
terraform plan
   ↓
Read the error carefully
   ↓
Check variables  →  Check state  →  Check backend / credentials  →  Check provider
   ↓
Fix
   ↓
Plan again
```

Avoid repeatedly running `apply` until something "works."

---

## Pre-deploy checklist

Before every deployment, verify:

- Terraform version pinned
- Provider versions pinned
- Backend configured, remote state enabled, locking enabled
- Variables validated
- Plan reviewed; saved plan used for production apply
- Module versions fixed
- Secrets stored securely (not in Git)
- Resources tagged
