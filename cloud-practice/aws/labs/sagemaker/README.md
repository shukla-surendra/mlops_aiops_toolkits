# Labs: SageMaker

Hands-on labs, beginner → advanced. Each: **Objectives · Architecture · Implementation · Validation · Cleanup**. Build the muscle memory behind [`../../docs/sagemaker/`](../../docs/sagemaker/README.md).

> ⚠️ GPUs and endpoints cost real money. **Do Cleanup** — a forgotten endpoint or GPU notebook bills 24/7. Use a sandbox account + billing alarm.

---

## Lab 1 — Studio + train a built-in model (Beginner)
**Objectives:** run a training job; see the ephemeral-cluster + artifact-in-S3 flow.
**Implementation:** open Studio; upload a small CSV to S3; train built-in **XGBoost** ([boto3](../../boto3/sagemaker/README.md) or SDK). 
**Validation:** `DescribeTrainingJob` → `Completed`; `model.tar.gz` appears in the output S3 path; logs in CloudWatch.
**Cleanup:** nothing persistent (job is ephemeral); stop Studio apps.

## Lab 2 — Deploy a real-time endpoint & invoke (Beginner→Intermediate)
**Objectives:** the Model→EndpointConfig→Endpoint contract; `/invocations`.
**Implementation:** deploy the Lab 1 model ([Terraform](../../terraform/sagemaker/README.md) or boto3); invoke with a sample row.
**Validation:** get a prediction; see `Invocations`/`ModelLatency` in CloudWatch.
**Cleanup:** **delete the endpoint** (it bills continuously), config, model.

## Lab 3 — Managed Spot training (Intermediate)
**Objectives:** cut training cost ~70–90%.
**Implementation:** retrain with `EnableManagedSpotTraining=True` + a checkpoint S3 path.
**Validation:** `DescribeTrainingJob` shows `TrainingTimeInSeconds` vs `BillableTimeInSeconds` (savings %). 
**Cleanup:** none (ephemeral).

## Lab 4 — Serverless vs real-time (Intermediate)
**Objectives:** feel the cost/latency tradeoff.
**Implementation:** deploy the same model as a **Serverless** endpoint; compare first-call (cold start) vs warm latency to the real-time one.
**Validation:** serverless scales to zero (no idle cost); cold start visible on first call.
**Cleanup:** delete both endpoints.

## Lab 5 — Hyperparameter tuning (Intermediate)
**Objectives:** automatic model tuning.
**Implementation:** launch an HPO job over `eta`/`max_depth`/`num_round`, objective = validation metric, strategy Bayesian, `max_jobs=10`.
**Validation:** best training job + its hyperparameters; compare to the untuned baseline.
**Cleanup:** none (jobs ephemeral).

## Lab 6 — Multi-Model Endpoint (Advanced)
**Objectives:** host many models on one fleet cheaply.
**Implementation:** put several `model.tar.gz` under one S3 prefix; create an MME; invoke with `TargetModel=...`.
**Validation:** different models answer on one endpoint; first hit to an unloaded model shows load latency.
**Cleanup:** delete the endpoint.

## Lab 7 — Pipeline + Model Registry (Advanced)
**Objectives:** reproducible CI/CD for ML + approval gate.
**Implementation:** build a Pipeline: Processing → Training → Evaluation → Condition(metric) → RegisterModel. Approve the model version in the Registry.
**Validation:** pipeline DAG runs end-to-end; a versioned model sits in the Registry as `Approved`.
**Cleanup:** delete pipeline + any endpoints deployed.

## Lab 8 — Model Monitor drift detection (Advanced)
**Objectives:** catch data drift in production.
**Implementation:** enable **data capture** on an endpoint; create a baseline; schedule a monitoring job; send skewed traffic.
**Validation:** a monitoring run flags a violation + emits a CloudWatch metric/alarm.
**Cleanup:** delete monitor schedule + endpoint.

## Lab 9 — VPC + network isolation (Advanced/Security)
**Objectives:** the regulated-data posture.
**Implementation:** run a training job in **VPC mode** with **network isolation**; provide S3 access via a gateway endpoint; confirm the container has no internet.
**Validation:** job reads data via the channel but cannot reach the internet (test a curl in a processing job → fails).
**Cleanup:** none (ephemeral); remove endpoints if any.

## Lab 10 — Failure/cost sim: the idle-endpoint bill (Advanced/Cost)
**Objectives:** internalize the #1 cost trap.
**Implementation:** leave a real-time endpoint up with zero traffic for a day (in a sandbox); observe the bill; then switch to Serverless.
**Validation:** Cost Explorer shows `Host:ml.*` accruing with no invocations; serverless = ~zero idle.
**Cleanup:** delete everything; set a budget alarm.

---

### Suggested order
1 → 2 → 3 (cost) → 4 (options) → 5 (tuning) → 6 (MME) → 7 (MLOps) → 8 (monitor) → 9 (security) → 10 (cost reality).
