# Amazon SageMaker — Complete documentation set

Deep-dive on the managed ML platform, beginner → advanced. Read in order.

## Study order

1. **[architecture.md](architecture.md)** — *Why SageMaker exists · the "managed ML lifecycle platform" mental model · internal architecture* (control/data plane, the component map, how a training job and an endpoint actually run, the container contract). **Start here.**
2. **[training.md](training.md)** — training & processing jobs, data channels (S3/EFS/FSx, Pipe/FastFile), distributed training, Spot + checkpointing, hyperparameter tuning, script mode vs BYOC.
3. **[inference.md](inference.md)** — the four inference options (real-time, serverless, async, batch transform), autoscaling, multi-model/multi-container endpoints, deployment safety (canary/blue-green/shadow).
4. **[mlops.md](mlops.md)** — Pipelines, Model Registry, Experiments, Feature Store, Model Monitor, Clarify, Projects/CI-CD, lineage & governance.
5. **[security.md](security.md)** — IAM & execution roles, VPC mode + network isolation, KMS encryption, data protection, multi-tenancy.
6. **[best-practices.md](best-practices.md)** — cost model (the #1 topic), monitoring, right-sizing, anti-patterns, production patterns.
7. **[troubleshooting.md](troubleshooting.md)** — training failures, endpoint errors, OOM/GPU, data/permission issues, cost surprises.
8. **[interview.md](interview.md)** — junior→principal Q&A, scenarios, incidents.

## Quick reference
- **[SageMaker cheatsheet](../../cheatsheets/sagemaker.md)**

## Hands-on
- **[Terraform: SageMaker](../../terraform/sagemaker/README.md)** — execution role, model, endpoint config, real-time endpoint with autoscaling.
- **[boto3: SageMaker](../../boto3/sagemaker/README.md)** — train → register → deploy → invoke → cleanup.
- **[Labs: SageMaker](../../labs/sagemaker/README.md)** — beginner→advanced, each with objectives/validation/cleanup.

## Related
- **[Bedrock docs](../bedrock/README.md)** — when you want *managed foundation models via API* instead of training/hosting your own. Read after SageMaker for the build-vs-consume contrast.

---
*Convention:* claims tagged **[Documented]** (AWS docs / re:Invent) or **[Inferred]** (reconstruction from behavior). Hold Inferred loosely.
