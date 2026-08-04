# SageMaker — Interview preparation

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> Spec section 15. Answers = what an interviewer wants. Say them aloud.

---

## Junior
**Q. What is SageMaker?** A managed platform for the whole ML lifecycle — build, train, tune, deploy, monitor — so you focus on the model, not GPU infra.

**Q. Core primitive?** Give it a container (ECR) + data (S3) + instance spec + execution role; it runs an ephemeral **job** (training) or a persistent **endpoint** (inference).

**Q. Training job vs endpoint?** Job = ephemeral cluster, billed per second, writes a model to S3. Endpoint = persistent fleet serving `/invocations`, billed while running.

## Senior
**Q. The four inference options and when to use each?** Real-time (steady low-latency, pays 24/7), Serverless (spiky, scales to zero, cold starts), Async (large payloads/long inference, scales to zero), Batch Transform (offline dataset scoring). Choose by traffic shape + latency + payload.

**Q. How do you cut training cost?** Managed **Spot** (up to ~90% off) with S3 checkpointing so interruptions resume; right-size GPUs; FSx/FastFile to avoid re-downloading data; Savings Plans for steady usage.

**Q. Script mode vs BYOC?** Script mode = AWS framework container + your `train.py` (most cases). BYOC = your own Docker image honoring the `/opt/ml` contract, for custom needs.

**Q. How do you get big data into training efficiently?** File (download all), Pipe (stream), FastFile (lazy POSIX stream), or FSx for Lustre (S3-linked, HPC throughput) for huge reused datasets.

## Principal / architecture
**Q. Design a production MLOps loop on SageMaker.** Pipelines orchestrate processing→train→evaluate→(conditional)register; Model Registry with approval gate; deploy pipeline to an autoscaled endpoint with data capture; Model Monitor detects drift → alarm → retrain. Feature Store feeds offline (train) + online (serve) to kill skew. Experiments + Lineage for reproducibility/audit. Everything as code + IaC.

**Q. Regulated data — lock it down.** VPC mode (ENIs in your subnets) + network isolation (no internet) + S3 gateway + `sagemaker`/ECR interface endpoints + CMK encryption + least-privilege execution role + `aws:SourceVpc` on data buckets. No path for a container to exfiltrate.

**Q. Serve 5,000 per-tenant models cheaply.** Multi-Model Endpoints (or Inference Components) — load/unload from S3 on demand on a shared fleet; accept first-hit load latency for massive cost savings vs one endpoint each.

**Q. When NOT to use SageMaker?** If you just need a foundation model via API with no custom weights/hosting → **Bedrock**. If you're all-in on Kubernetes and want portability → Kubeflow/Ray on EKS. SageMaker shines when you want managed ML primitives without running the platform.

## Scenario
**Q. "Our SageMaker bill is huge with little traffic."** Almost always idle **real-time endpoints** and **GPU notebooks** left running. Move rare traffic to Serverless/Async, auto-shutdown notebooks, Spot for training. Confirm via CUR `Host:ml.*`/`Notebk:ml.*`.

**Q. "Predictions degraded over weeks."** Data/model drift. Model Monitor vs baseline should have alarmed; use lineage to find the training data/code, retrain via the pipeline, canary the new model with rollback.

**Q. "Training GPU utilization is 15%."** Input pipeline bottleneck (File-mode download / slow loader). Switch to FastFile/FSx, more loader workers, bigger batch; verify with Profiler.

## Incident
**Q. "New model version tanked conversion after deploy."** Should've been a canary/shadow with metric-gated rollout + auto-rollback on CloudWatch alarms. Roll back to the prior production variant, then re-test in shadow.

**Q. "Endpoint in VPC mode won't come up."** Its ENIs can't reach S3/ECR — missing S3 gateway endpoint / ECR interface endpoints / NAT. Add them; check the SG allows egress to the endpoints.

---

## Rapid-fire
- Give container + S3 + instance + role → job (ephemeral) or endpoint (persistent).
- 4 inference: real-time, serverless, async, batch transform.
- Spot + checkpoints = cheap training; idle real-time endpoint = #1 cost trap.
- Data modes: File / Pipe / FastFile / FSx-Lustre.
- MLOps: Pipelines + Registry(approval) + Feature Store + Model Monitor + Lineage.
- Regulated: VPC + network isolation + private endpoints + CMK.
- Many models → MME / Inference Components.
- No custom weights needed → Bedrock, not SageMaker.

---

## Self-check
Answer any 3 Principal/scenario/incident questions aloud in <90s each without reading.
