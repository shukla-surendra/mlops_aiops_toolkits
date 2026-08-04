# SageMaker — Best practices, cost & monitoring

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** all prior SageMaker docs.

Spec sections 8, 9, 10, 11. **Cost is the dominant operational topic** — GPUs and idle endpoints are where SageMaker bills quietly hurt.

---

## 1. Cost model (what actually bills) [Documented]

> **Model is [Documented] and stable; rates change & vary by Region/instance — verify live:**
> **Live pricing:** https://aws.amazon.com/sagemaker/pricing/ · **Calculator:** https://calculator.aws/ · **Your spend:** Cost Explorer / CUR by `usageType` (look for `…Train:ml.*`, `…Host:ml.*`, `…Notebk:ml.*`, `…ServerlessInf`, `…BatchTransform`).

You pay for **compute-seconds of the underlying `ml.*` instances**, per capability:
1. **Training jobs** — instance-seconds while running. **Managed Spot** cuts this up to ~90% (with checkpointing). Ephemeral → you only pay while training.
2. **Real-time endpoints** — **running instances 24/7, traffic or not** → the #1 hidden cost. Idle/dev endpoints are pure waste.
3. **Notebook/Studio compute** — instances left running (esp. GPU notebooks) bill continuously → auto-shutdown.
4. **Serverless / Async / Batch** — pay per use / while processing; **scale to zero** when idle.
5. **Storage & extras** — EBS on instances, S3 for data/artifacts, Feature Store, Model Monitor jobs, data processing.
6. **Data transfer** — cross-AZ/Region, and pulling data repeatedly (FSx/streaming can cut repeated download cost).

**Cost levers, ranked:**
1. **Kill idle real-time endpoints; use Serverless/Async for spiky/low traffic.**
2. **Managed Spot for training** (+ checkpoints).
3. **Auto-shutdown notebooks/Studio apps.**
4. **Right-size instances**; use MME/Inference Components to raise GPU utilization.
5. **Savings Plans** (SageMaker Savings Plans) for steady committed usage.
6. **FSx/streaming** to avoid re-downloading big datasets each job.

## 2. Best-practice checklist
- **Everything as code:** Pipelines + SDK + IaC, not click-ops; reproducible training.
- **Least-privilege execution roles**, scoped S3/KMS; VPC + isolation for sensitive data.
- **Model Registry + approval gate** before prod; **Model Monitor + data capture** on endpoints.
- **Autoscale endpoints**; pick the right inference option per traffic shape.
- **Checkpoint training** (Spot-safe + resumable).
- **Tag** jobs/endpoints (team, project, env) for cost allocation + cleanup.
- **Feature Store** to kill train/serve skew.
- **Auto-shutdown** idle notebooks; lifecycle configs.

## 3. Anti-patterns
| Anti-pattern | Why it hurts | Fix |
|---|---|---|
| Real-time endpoint for rare traffic | Pays 24/7 for idle | Serverless / Async |
| GPU notebook left on | Silent large bill | Auto-shutdown, right-size |
| On-demand for all training | 10× the Spot price | Managed Spot + checkpoints |
| `AdministratorAccess` execution role | Huge blast radius | Scope to buckets/keys |
| Notebook-driven "prod" | Not reproducible, no lineage | Pipelines + Registry |
| Re-download 5 TB each job | Wasted time + transfer | FSx for Lustre / FastFile |
| One giant endpoint per model (×1000s) | Cost explosion | Multi-Model Endpoints / Inference Components |
| No monitoring | Silent drift → bad predictions | Model Monitor + alarms |

## 4. Monitoring [Documented]
- **CloudWatch endpoint metrics:** `Invocations`, `InvocationsPerInstance`, `ModelLatency`, `OverheadLatency`, `Invocation4XX/5XXErrors`, instance `CPU/GPU/MemoryUtilization`, `DiskUtilization`.
- **Training metrics:** emitted to CloudWatch; **Debugger/Profiler** for system + framework bottlenecks (GPU under-utilization, stalls).
- **Model Monitor** → drift metrics + alarms.
- **CloudTrail** for API audit; **EventBridge** to react to job/endpoint state changes (e.g., alert on failed training, auto-deploy on model approval).

## 5. Production patterns
- **Online prediction service:** real-time endpoint + autoscaling + data capture + Model Monitor; canary/shadow for new versions.
- **Many small models (SaaS per-tenant):** Multi-Model Endpoints or Inference Components for utilization.
- **LLM serving:** GPU + LMI/Triton, tensor parallelism, async for long generations, or **use Bedrock instead** if you don't need custom weights (see [Bedrock](../bedrock/README.md)).
- **Batch scoring:** Batch Transform on a schedule via Pipelines/EventBridge.
- **Regulated:** VPC + network isolation + private endpoints + CMK.

---

## Sources
- AWS docs: *SageMaker pricing*, *Manage costs*, *Savings Plans*, *CloudWatch metrics*, *Debugger/Profiler*, *Automatic scaling for endpoints*.
- Well-Architected **Machine Learning Lens**.

---

## Self-check
1. Your SageMaker bill is dominated by "Host:ml.g5" with low traffic. Diagnose and give the two fixes.
2. Rank the top three cost levers for a team that trains daily and serves one low-traffic model.
3. Why is a notebook-driven prod workflow an anti-pattern even if it "works"?
4. Which metric tells you an endpoint is over-provisioned, and how do you act on it?
5. When should you *not* build on SageMaker at all and use Bedrock instead?
