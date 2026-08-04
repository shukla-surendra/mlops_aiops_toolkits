# SageMaker Cheatsheet

One-page recall. Full detail in [`../docs/sagemaker/`](../docs/sagemaker/README.md).

## Mental model
**Managed ML-lifecycle platform.** Core primitive: **container (ECR) + data (S3) + instance spec + execution role** → ephemeral **job** (train) or persistent **endpoint** (serve). Everything is a job or an endpoint.

## Component map
Build: **Studio**, Notebooks, **JumpStart**, Autopilot · Prep: **Processing**, Data Wrangler, **Feature Store**, Ground Truth · Train: **Training jobs**, **HPO**, Experiments · Deploy: **Endpoints** (real-time/serverless/async), **Batch Transform** · Ops: **Model Registry**, **Pipelines**, **Model Monitor**, Clarify.

## Training
- Data in: **File** (download all) · **Pipe** (stream) · **FastFile** (lazy POSIX) · **FSx-Lustre** (S3-linked, HPC).
- **Managed Spot** (~90% off) + **S3 checkpoints** = cheap, resumable.
- Distributed: data-parallel (SMDDP/DDP) vs model-parallel (SMP); EFA for fast interconnect.
- Script mode (framework container + `train.py`) vs BYOC (`/opt/ml` contract).
- Container paths: `/opt/ml/input` · `/opt/ml/model` · `/opt/ml/output/failure` · `/opt/ml/code`.

## Inference (pick by traffic)
| Option | Use | Cost |
|---|---|---|
| **Real-time** | steady low-latency | instances 24/7 (idle trap!) |
| **Serverless** | spiky, scale-to-zero | per request (cold starts) |
| **Async** | big payloads/long jobs | scales to zero |
| **Batch Transform** | offline dataset | job duration |
Serving container: `GET /ping` + `POST /invocations`. Many models → **MME / Inference Components**. Safe deploy → variants + canary/blue-green + **shadow** + auto-rollback.

## MLOps
**Pipelines** (DAG CI/CD) → **Model Registry** (versions + approval gate) → deploy → **Model Monitor** (drift → alarm → retrain). **Feature Store** (online+offline) kills train/serve skew. Experiments + Lineage = reproducibility.

## Security
Two IAM identities: API caller vs **execution role** (least-priv S3/ECR/KMS). **VPC mode** (ENIs in your subnets) + **network isolation** (no internet) + private endpoints + CMK = regulated pattern. `aws:SourceVpc` on buckets stops exfil.

## Cost (model stable; rates live)
Pay **instance-seconds**: training (Spot!) · **real-time endpoint 24/7 = #1 trap** · GPU notebooks left on · serverless/async scale-to-zero. Levers: kill idle endpoints → serverless/async · Spot+checkpoint · auto-shutdown notebooks · MME utilization · Savings Plans.
**Live pricing:** https://aws.amazon.com/sagemaker/pricing/ · calc https://calculator.aws/ · CUR `Host:ml.*`/`Train:ml.*`/`Notebk:ml.*`.

## Debug
Logs `/aws/sagemaker/...`. Train fail → role AccessDenied (S3/ECR/KMS), OOM, quota, script error (`/opt/ml/output/failure`). Endpoint fail → `/ping` unhealthy, artifact mismatch, VPC can't reach S3/ECR. Slow → `ModelLatency`/GPU util; Profiler for input-pipeline bottleneck.

## Terraform / boto3
`aws_sagemaker_model` · `aws_sagemaker_endpoint_configuration` · `aws_sagemaker_endpoint` · `aws_iam_role` (exec) · autoscaling target. SDK: `estimator.fit()` → `model.register()` → `deploy()` → `predictor.predict()`. Examples: [`../terraform/sagemaker/`](../terraform/sagemaker/README.md), [`../boto3/sagemaker/`](../boto3/sagemaker/README.md).

## SageMaker vs Bedrock
Custom training/hosting your own weights → **SageMaker**. Just call a managed foundation model via API → **Bedrock**.
