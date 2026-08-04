# Terraform: Bedrock guardrail, scoped IAM & invocation logging

Provisions the **governance layer** for using Bedrock safely: a least-privilege IAM role that can invoke **only** allowed model ARNs, a **Guardrail** (content filters + PII redaction), and **model invocation logging** to S3. Demonstrates [`../../docs/bedrock/security.md`](../../docs/bedrock/security.md) and [best-practices.md](../../docs/bedrock/best-practices.md).

> ⚠️ **Prerequisite:** you must **enable model access** for the model family in this Region (Bedrock console → *Model access*) before any invocation works — that's a separate control-plane gate from IAM. The Guardrail + logging resources here are cheap; you pay per token only when you actually invoke.

## What it creates
```
IAM role (app) → can Invoke/Converse ONLY the allowed model ARNs (+ ApplyGuardrail)
Guardrail       → content filters (hate/violence/…/prompt-attack) + PII ANONYMIZE
S3 bucket       → model invocation logs (prompts/responses) with a Bedrock write policy
Model invocation logging config → text + embedding delivery to that bucket
```

## Files
| File | Purpose |
|---|---|
| `versions.tf` | Provider pins + default tags |
| `variables.tf` | Region, allowed model ARNs, guardrail/logging toggles |
| `main.tf` | IAM role+policy, Guardrail, log bucket+policy, logging config |
| `outputs.tf` | Role ARN, guardrail id/version, log bucket, a runbook |

## Usage
```bash
cd aws/terraform/bedrock
cp terraform.tfvars.example terraform.tfvars   # set allowed_model_arns
terraform init
terraform plan
terraform apply
terraform output next_steps
terraform destroy
```

## Things to try
1. Add/remove a model ARN in `allowed_model_arns` and diff the IAM policy — see least-privilege in action.
2. Set `pii_entities_config` action to `BLOCK` vs `ANONYMIZE` and observe the difference on PII input.
3. Invoke with the guardrail id (`--guardrail-config`) and inspect the assessment when content is filtered.
4. Check the S3 log bucket after a few invocations to see captured prompts/responses (mind PII — encrypt in prod).

## Deliberately scoped
- Governance layer only — no Knowledge Base / Agent here (those need a vector store / Lambdas; see the docs + labs).
- Assume-role principal is `ec2.amazonaws.com` as a placeholder — change it to your app's principal (Lambda/ECS/etc.).
