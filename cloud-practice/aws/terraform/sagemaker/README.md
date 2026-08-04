# Terraform: SageMaker real-time endpoint

Provisions the **serving layer**: a least-privilege execution role, a `Model` (container + trained artifact), an `EndpointConfig`, a real-time `Endpoint`, and **target-tracking autoscaling** on invocations-per-instance. Demonstrates [`../../docs/sagemaker/inference.md`](../../docs/sagemaker/inference.md).

> ⚠️ **A real-time endpoint bills for its instances 24/7 while it exists** — the #1 SageMaker cost trap. `terraform destroy` when done. `plan` is free.

## Prerequisite: you need a model
This module hosts an *existing* model. Produce one first:
- Train via [`../../boto3/sagemaker`](../../boto3/sagemaker/README.md) or [`../../labs/sagemaker`](../../labs/sagemaker/README.md) → it writes `model.tar.gz` to S3.
- Point `container_image` (the matching serving image) + `model_data_url` at it.

## What it creates
```
IAM execution role (demo: SageMakerFullAccess — scope down for prod)
 └── Model (image + model.tar.gz)
      └── EndpointConfig (ml.m5.large, variant "AllTraffic")
           └── Endpoint  ← persistent, billable
                └── App Auto Scaling (1→3 on InvocationsPerInstance)
```

## Usage
```bash
cd aws/terraform/sagemaker
cp terraform.tfvars.example terraform.tfvars   # set container_image + model_data_url
terraform init
terraform plan
terraform apply
terraform output invoke_example
terraform destroy      # STOP the meter
```

## Things to try
1. Change `min_capacity`/`max_capacity` and watch the autoscaling target update.
2. Uncomment `data_capture_config` (set a bucket) to enable Model Monitor input/output capture.
3. Add a second `production_variants` block with a different model + weights for a **canary/A-B** test.

## Deliberately scoped
- Serving layer only (no training infra here — that's in the boto3/labs).
- `AmazonSageMakerFullAccess` is for the demo; **replace with a bucket/ECR/KMS-scoped policy in production** (see [security.md](../../docs/sagemaker/security.md)).
