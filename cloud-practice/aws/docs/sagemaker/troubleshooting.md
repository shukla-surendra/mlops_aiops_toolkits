# SageMaker — Troubleshooting & debugging

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [training.md](training.md), [inference.md](inference.md), [security.md](security.md).

Spec section 14. SageMaker failures cluster into: **training won't start / fails**, **endpoint won't deploy / errors**, **it's slow / OOM**, and **cost surprises**. Logs live in **CloudWatch** (`/aws/sagemaker/...`).

---

## 1. Training job fails
1. **Permissions (`AccessDenied`)** — execution role can't read the S3 data, pull the ECR image, or use the KMS key. Check the role policy + the KMS key state (disabled key = fail).
2. **Data/channel issues** — wrong S3 URI, empty channel, or the container can't find data under `/opt/ml/input/`. Check the input config vs where your script reads.
3. **`AlgorithmError` / exit code** — your script threw. Read the **CloudWatch training logs**; the failure reason is also written to `/opt/ml/output/failure`.
4. **OOM (CPU/GPU)** — batch too big, model too large. Reduce batch, use gradient accumulation, bigger instance, or model parallelism.
5. **Resource limits/quota** — GPU instance quota (`ml.p4d`, `ml.g5`) not raised in the Region → request a quota increase.
6. **Spot interruption without resume** — no checkpoint path, so it restarts from scratch (or fails). Add checkpointing.

## 2. Endpoint won't deploy / fails
1. **Container fails `/ping`** — the serving container didn't become healthy in time. Check its startup logs; ensure it binds the port and answers `GET /ping` 200.
2. **Model artifact / image mismatch** — wrong `model.tar.gz` structure or the inference code can't load it. Verify the artifact layout and `inference.py` handlers.
3. **`/invocations` errors (4XX/5XX)** — payload format mismatch (content-type/serializer), model exceptions, timeouts. Check `ModelLatency` + logs.
4. **Insufficient capacity / quota** — endpoint instance type quota, or capacity in the AZ.
5. **VPC misconfig** — in VPC mode, the endpoint's ENIs can't reach S3/ECR (no VPC endpoint/NAT) → deploy hangs/fails. Add S3 gateway + `sagemaker`/ECR interface endpoints or NAT.

## 3. Slow / expensive inference
- **High `ModelLatency`** → model too heavy for the instance, no GPU, no batching → bigger/GPU instance, compile (Neo), quantize, or batch.
- **High `OverheadLatency`** → serialization/cold model load (MME first-hit) → keep hot, pre-load, or fewer models per instance.
- **Autoscaling flapping / throttling** → tune target metric + cooldowns.
- **Idle cost** → wrong option; move to serverless/async.

## 4. Data & performance (training)
- **GPU under-utilized** (Profiler shows low GPU%) → input pipeline is the bottleneck (File-mode download, slow data loader) → FastFile/Pipe/FSx, more data-loader workers, bigger batch.
- **Distributed job hangs** → networking/NCCL/env mismatch across nodes; check the cluster env vars and interconnect (EFA).

## 5. Cost surprises
- **Bill spike** → a real-time endpoint or GPU notebook left running; forgotten tuning job with high parallelism; Warm Pools kept alive. Check CUR `usageType` `Host:ml.*` / `Notebk:ml.*` / `Train:ml.*`.

## 6. Tools
- **CloudWatch Logs** (`/aws/sagemaker/TrainingJobs`, `/Endpoints/<name>`) + **Metrics**.
- **Debugger / Profiler** for training bottlenecks + system stats.
- **`DescribeTrainingJob` / `DescribeEndpoint`** for status + `FailureReason`.
- **CloudTrail** for who/what API call; **data capture** to inspect real endpoint inputs/outputs.

---

## Sources
- AWS docs: *Troubleshooting Amazon SageMaker*, *CloudWatch logs & metrics*, *Debugger/Profiler*, *Endpoint troubleshooting*, *Give VPC access*.

---

## Self-check
1. A training job fails immediately with `AccessDenied`. List the three resources the execution role might lack access to.
2. An endpoint deploy hangs in VPC mode. What networking cause is most likely and how do you fix it?
3. Profiler shows GPU at 15% during training. Where's the bottleneck and what do you change?
4. `/invocations` returns 415 errors. What's the mismatch?
5. Bill doubled overnight, no traffic increase. Which two `usageType` lines do you inspect first?
