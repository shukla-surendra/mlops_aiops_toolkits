# boto3: SageMaker lifecycle

`sagemaker_lifecycle.py` runs the end-to-end flow with **low-level boto3** (so you see the real API): **train** (built-in XGBoost, Managed Spot) → **deploy** (Model → EndpointConfig → Endpoint) → **invoke** → **cleanup**.

Ties to [`../../docs/sagemaker/`](../../docs/sagemaker/README.md).

## Setup
```bash
pip install boto3
export AWS_PROFILE=your-profile     # SageMaker + S3 + IAM permissions
# You need: a SageMaker execution role ARN, and a training CSV in S3 (label in col 0).
```

## Flow
```bash
# 1) Train (Managed Spot on by default → cheaper, resumable)
python sagemaker_lifecycle.py --region us-east-1 train \
  --role-arn arn:aws:iam::123456789012:role/SageMakerExec \
  --train-s3 s3://my-bucket/data/train/ \
  --output-s3 s3://my-bucket/xgb/output/

# 2) Deploy the resulting model.tar.gz to a real-time endpoint
python sagemaker_lifecycle.py deploy \
  --role-arn arn:aws:iam::123456789012:role/SageMakerExec \
  --model-data s3://my-bucket/xgb/output/.../model.tar.gz --name xgb-endpoint

# 3) Invoke
python sagemaker_lifecycle.py invoke --name xgb-endpoint --body "5.1,3.5,1.4,0.2"

# 4) Tear down (ENDPOINTS BILL 24/7 — always do this)
python sagemaker_lifecycle.py cleanup --name xgb-endpoint
```

## What to notice
- **Waiters** (`training_job_completed_or_stopped`, `endpoint_in_service`) — jobs/endpoints are async.
- **Managed Spot** flags (`EnableManagedSpotTraining` + `MaxWaitTimeInSeconds`) — the cheap-training pattern.
- **The Model → EndpointConfig → Endpoint** three-step is the deploy contract; **cleanup deletes in reverse**.
- The built-in **XGBoost image URI** is Region-specific (account IDs differ) — the script maps a few; pass `--image` for others.

⚠️ Endpoints bill until deleted. Always `cleanup`.
