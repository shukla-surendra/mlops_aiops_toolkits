# Bedrock — Best practices, cost & monitoring

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** all prior Bedrock docs.

Spec sections 8, 9, 10, 11. Cost is per-token by default, so **model choice and token discipline** are the dominant levers.

---

## 1. Cost model (what actually bills) [Documented]

> **Model is [Documented] and stable; per-token/per-unit rates change fast and vary by model/Region — verify live:**
> **Live pricing:** https://aws.amazon.com/bedrock/pricing/ · **Calculator:** https://calculator.aws/ · **Your spend:** Cost Explorer / CUR (use **application inference profiles** to attribute per app/team).

1. **On-demand inference** — pay per **input token + output token**, priced per model (bigger/smarter models cost more). Output tokens usually cost more than input. This is most apps' whole bill.
2. **Provisioned Throughput** — pay per **model unit-hour** for reserved capacity (required for custom models); bills whether used or not — the idle-endpoint trap.
3. **Batch** — asynchronous batch inference is discounted (~50%) vs on-demand for non-latency-sensitive jobs.
4. **Knowledge Bases** — embedding calls (per token) + the **vector store** (e.g. OpenSearch Serverless OCUs, or Aurora) + retrieval generation tokens. The vector store can dominate a small KB's cost.
5. **Customization** — training job cost + storage; then Provisioned Throughput to serve.
6. **Guardrails** — priced per unit of text evaluated.
7. **Data transfer / PrivateLink endpoints** — the usual VPC costs.

**Cost levers, ranked:**
1. **Right-size the model** — use a small/Haiku-class model for classification/extraction/routing; reserve the strongest model for hard reasoning. Often the single biggest saving.
2. **Token discipline** — cap `maxTokens`, trim prompts, and **prompt-cache** stable context where supported (big savings on repeated system prompts / RAG context).
3. **Batch** the non-interactive jobs (~50% off).
4. **On-demand + cross-region profiles** before Provisioned Throughput; buy provisioned only for steady high volume / SLAs / custom models.
5. **RAG over fine-tuning** for knowledge (no training/provisioned cost).
6. **Attribute cost** with application inference profiles → find the expensive app.

## 2. Best-practice checklist
- **Least-privilege IAM per model** + model-access gating + SCPs (approved models only).
- **Attach a Guardrail** to every production invocation (safety + PII + grounding).
- **Stream** responses for UX; cap `maxTokens`.
- **RAG (Knowledge Bases) before fine-tuning**; fine-tune only for behavior/format.
- **Prompt Management** for versioned prompts; evaluate model changes with **Model Evaluation** before rollout.
- **Retry with backoff** on `ThrottlingException`; use cross-region inference profiles for burst.
- **PrivateLink + KMS** for regulated data; **model invocation logging** for audit.
- **Model-agnostic code** (`Converse`) so you can swap models as better/cheaper ones ship.
- **Tag + application inference profiles** for cost allocation.

## 3. Anti-patterns
| Anti-pattern | Why it hurts | Fix |
|---|---|---|
| Biggest model for every task | 5–20× the token cost | Right-size; small model for simple tasks |
| Provisioned Throughput "to be safe" | Pays 24/7 for idle capacity | On-demand + cross-region until volume justifies |
| Fine-tuning to add knowledge | Expensive, stale fast | RAG (Knowledge Bases) |
| No Guardrail in prod | Unsafe output / PII leak / injection | Attach a versioned Guardrail |
| Hardcoded single model + native body | Locked in, can't swap | `Converse` + config |
| Unbounded `maxTokens` + fat prompts | Runaway token bill | Caps + prompt trimming + caching |
| No cost attribution | Can't find the expensive app | Application inference profiles + tags |
| Ignoring throttling | Failed requests under load | Backoff + cross-region + provisioned |

## 4. Monitoring [Documented]
- **CloudWatch Bedrock metrics:** `Invocations`, `InvocationLatency`, `InputTokenCount`, `OutputTokenCount`, `InvocationClientErrors`/`ServerErrors`, `InvocationThrottles` — watch throttles + token growth.
- **Model invocation logging** → S3/CloudWatch: full prompt/response capture for audit + quality review (mind PII; encrypt).
- **CloudTrail** — every control- and data-plane API call (who invoked what model).
- **Guardrail metrics** — how often content was blocked/redacted.
- **Cost Explorer / CUR** — per-model, per-app (inference profiles) spend + budget alarms.

## 5. Production patterns
- **RAG chatbot:** Knowledge Base + `RetrieveAndGenerate` + Guardrail (grounding check) + streaming; metadata filtering for multi-tenant.
- **Task agent:** Bedrock Agent (action groups + KB + memory + Guardrail), or `Converse`+tools if you want to own the loop.
- **High-volume classification:** small model, Batch or on-demand, tight `maxTokens`, prompt caching.
- **Regulated:** PrivateLink + KMS + model-access governance + invocation logging + Guardrails; keep to in-Region (mind cross-region profiles).
- **Model portability:** `Converse` + Prompt Management + Model Evaluation so you can adopt new models quickly.

---

## Sources
- AWS docs: *Bedrock pricing*, *Provisioned Throughput*, *Batch inference*, *CloudWatch metrics for Bedrock*, *Model invocation logging*, *Cost allocation with inference profiles*.
- Well-Architected **Generative AI Lens**.

---

## Self-check
1. Your Bedrock bill is dominated by one app using the largest model for simple tagging. Two fixes, in order of impact.
2. When is Provisioned Throughput justified, and what's its cost trap (name the analogous SageMaker trap)?
3. Knowledge vs behavior: which do you solve with RAG and which with fine-tuning, and why does that matter for cost?
4. Which metric warns you you're being throttled, and what are two mitigations?
5. How do you attribute Bedrock spend to a specific team/app?
