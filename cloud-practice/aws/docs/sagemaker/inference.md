# SageMaker — Inference & deployment

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md) (endpoints are persistent managed fleets; `/ping` + `/invocations`).

Spec sections 7, 8. Choosing the **right inference option** is the highest-leverage decision — it drives latency, cost, and operational shape.

---

## 1. The four inference options [Documented] — know when to use each

| Option | Shape | Best for | Cost basis | Cold start? |
|---|---|---|---|---|
| **Real-time endpoint** | Persistent fleet, ms latency | Steady, low-latency online traffic | **Running instances (24/7)** | No |
| **Serverless inference** | Scales to zero, per-request | Spiky/intermittent traffic, dev | Per-request (+ mem) | **Yes** (cold starts) |
| **Asynchronous inference** | Queue-based, near-real-time | Large payloads, long inference, bursty | Instances, **scales to zero** when idle | Some |
| **Batch Transform** | Offline job over an S3 dataset | Scoring a whole dataset, no endpoint | Job duration | N/A |

**Decision guide:**
- Constant low-latency online → **Real-time**.
- Infrequent/spiky, tolerate cold start → **Serverless** (no idle cost — fixes the "endpoint burning money" trap).
- Big payloads (video, large docs) or long/GPU-heavy inference, can wait seconds→minutes → **Async** (also scales to zero).
- Score a batch, no live endpoint needed → **Batch Transform**.

## 2. Real-time endpoints — the details
- `Model` + `EndpointConfig` + `Endpoint`. **Autoscaling** on `SageMakerVariantInvocationsPerInstance` (or custom/target-tracking) adjusts instance count.
- **Idle cost is the #1 trap:** a real-time endpoint bills for its instances whether or not it gets traffic. Turn dev endpoints off; use serverless/async for low utilization.
- **GPU serving:** for large models use GPU instances + optimized servers (Triton, TorchServe, or **Large Model Inference (LMI)** containers with tensor parallelism for LLMs).

## 3. Packing more into an endpoint [Documented]
- **Multi-Model Endpoints (MME)** — host **thousands of models** on one fleet, loading/unloading from S3 on demand. Huge cost win when you have many small, infrequently-used models (per-customer models). Tradeoff: first call to a not-loaded model pays a load latency.
- **Multi-Container Endpoints / Inference Pipelines** — chain containers (e.g., preprocess → model → postprocess) in one endpoint; a request flows through the pipeline.
- **Inference Components** (modern) — pack multiple models with fine-grained resource allocation + independent scaling on shared fleets, improving GPU utilization.

## 4. Safe deployment [Documented]
- **Production variants** — multiple model versions behind one endpoint with weighted traffic → **A/B testing** and **canary** (shift 5% → 100%).
- **Deployment guardrails** — **blue/green** with **canary or linear** traffic shifting + **auto-rollback** on CloudWatch alarms. **Shadow testing** — send a copy of live traffic to a new variant without affecting responses, to validate before promoting.
- Always gate promotion on metrics (latency, errors, model quality) — never flip 100% blind.

## 5. Optimization
- **Right-size instance + count** to your latency SLO and traffic; autoscale on invocations.
- **Model compilation/optimization** — **SageMaker Neo** / compilation, quantization, and optimized runtimes cut latency + cost.
- **Elastic/Serverless** for spiky; **MME/Inference Components** for many models to raise utilization.
- **Async** for large payloads keeps request handling off the hot path and scales to zero.

---

## Sources
- AWS docs: *Deploy models*, *Serverless Inference*, *Asynchronous Inference*, *Batch Transform*, *Multi-Model Endpoints*, *Inference Components*, *Deployment guardrails*, *Shadow tests*, *SageMaker Neo*, *Large Model Inference containers*.

---

## Self-check
1. Pick the inference option for: (a) a chatbot needing 50 ms responses 24/7, (b) a nightly scoring of 100M rows, (c) a rarely-used internal tool, (d) OCR on large PDFs taking 30 s each. Justify each.
2. Why is a real-time endpoint the classic cost trap, and what two options avoid idle cost?
3. You serve 5,000 per-customer models, each used rarely. Which feature, and what's its latency tradeoff?
4. Describe a safe rollout of a new model version with automatic rollback.
5. What is shadow testing and why is it safer than a canary for a risky model change?
