# Bedrock — Troubleshooting & debugging

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [models-inference.md](models-inference.md), [security.md](security.md).

Spec section 14. Bedrock issues cluster into: **can't call the model**, **throttled**, **guardrail blocked it**, **bad/hallucinated answers (RAG)**, and **cost/latency**.

---

## 1. "Can't invoke the model"
1. **`AccessDeniedException`** — either the **IAM policy** lacks `bedrock:InvokeModel`/`Converse` on that model's ARN, **or** the account hasn't **enabled model access** for that family in this Region (control-plane gate). Check both. CloudTrail shows the denied call.
2. **`ValidationException: use an inference profile`** — the model requires **cross-region inference**; call the geo-prefixed ID (`us.anthropic.claude-opus-4-8`) instead of the bare `anthropic.claude-...`.
3. **`ResourceNotFoundException` / wrong Region** — the model isn't offered in that Region, or you targeted the wrong endpoint. Models/features vary by Region — check availability.
4. **Bad request body** — `InvokeModel` needs the model's **native** shape (Claude: `anthropic_version: "bedrock-2023-05-31"` + `messages` + `max_tokens`); a `Converse`-shaped body to `InvokeModel` (or vice-versa) fails. Prefer `Converse` unless you need native params.
5. **Custom model won't invoke** — custom models require **Provisioned Throughput**; you can't call them on-demand.

## 2. "Throttled" (`ThrottlingException`)
- You hit the account/model **RPM/TPM quota** or a burst. Fixes: **exponential backoff + retry** (SDKs do some automatically), **cross-region inference profiles** (spread load), request a **quota increase**, or buy **Provisioned Throughput** for guaranteed capacity. Watch `InvocationThrottles` in CloudWatch.

## 3. "Guardrail blocked / redacted my content"
- A response came back blocked, or with `[PII]`/masked text → a **Guardrail** intervened (content filter, denied topic, PII redaction, or grounding check). Inspect the Guardrail **trace/assessment** in the response to see *which* policy fired and at what strength, then tune the filter level, denied-topic definitions, or PII handling. Don't just disable it — adjust the policy.

## 4. "RAG answers are wrong / hallucinated / say 'I don't know'"
Walk the RAG chain:
1. **Retrieval empty/irrelevant?** Test `Retrieve` alone — are the right chunks coming back? If not: re-check **chunking**, the **embedding model**, **top-k**, and whether the **sync/ingestion** actually indexed the docs.
2. **Right chunks, wrong answer?** The generation model isn't using context well → stronger model, better prompt, or a **reranker**.
3. **Hallucinating beyond context?** Add a **contextual-grounding Guardrail** and/or instruct "answer only from the provided context."
4. **Cross-tenant leakage / stale docs?** Fix **metadata filtering** and re-sync the data source.

## 5. "Slow / expensive"
- **Latency** scales with output length + model size → **stream**, cap `maxTokens`, use a smaller model where quality allows.
- **Cost spike** → wrong (too-big) model, unbounded tokens, forgotten **Provisioned Throughput**, or a chatty KB vector store. Check CUR by model + application inference profile.

## 6. Tools
- **CloudWatch** Bedrock metrics (throttles, latency, token counts, errors).
- **Model invocation logging** (S3/CloudWatch) — see the exact prompt/response that failed or hallucinated.
- **CloudTrail** — who called what; access-denied diagnosis.
- **Guardrail trace** + **Agent trace** — see which policy/step caused the behavior.
- **`Retrieve`** (KB) in isolation — separate retrieval failures from generation failures.

---

## Sources
- AWS docs: *Bedrock error messages / quotas*, *Cross-region inference*, *Guardrails assessments*, *Knowledge Base troubleshooting*, *Model invocation logging*.

---

## Self-check
1. `AccessDeniedException` on a first-ever call to a model. Name the two independent causes to check.
2. A model returns "use an inference profile." What exactly do you change?
3. Your RAG bot says "I don't know" for facts that are in the docs. What do you test first, and what three ingestion settings might be at fault?
4. Under load you get `ThrottlingException`. Give three mitigations.
5. A custom fine-tuned model won't invoke on-demand. Why, and what's required to serve it?
