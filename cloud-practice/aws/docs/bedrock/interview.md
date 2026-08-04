# Bedrock — Interview preparation

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> Spec section 15. Answers = what an interviewer wants. Say them aloud.

---

## Junior
**Q. What is Bedrock?** A serverless, single-API way to use foundation models from many providers (Claude, Llama, Amazon Nova, Mistral, …) with AWS IAM/VPC/KMS/billing and a data-privacy guarantee.

**Q. `Converse` vs `InvokeModel`?** `Converse` = unified, provider-agnostic messages API (swap models by ID). `InvokeModel` = pass the model's native request body for provider-specific features.

**Q. Bedrock vs SageMaker?** Bedrock = *consume* managed foundation models via API. SageMaker = *build/train/host* your own models. No custom weights needed → Bedrock; need your own model/training → SageMaker.

## Senior
**Q. How does a request flow and what auth?** IAM/SigV4 to a regional `bedrock-runtime` endpoint with a model ID; Bedrock checks IAM + model-access grant, routes to the provider-hosted model, applies any Guardrail on input/output, streams tokens; CloudWatch/CloudTrail record it.

**Q. What's a cross-region inference profile?** A geo-prefixed model ID (`us.anthropic.claude-opus-4-8`) that lets Bedrock route across Regions in a geography for availability/burst throughput — often the required on-demand path for popular models.

**Q. RAG on Bedrock?** Knowledge Bases: ingest S3 docs → chunk → embed → vector store (OpenSearch Serverless / Aurora pgvector / …) → `RetrieveAndGenerate` returns a grounded, cited answer. RAG grounds the model in *your* data without changing weights.

**Q. What are Guardrails?** Model-agnostic safety policies on input+output: content filters, denied topics, PII detect/redact, word filters, and contextual-grounding checks (anti-hallucination for RAG).

## Principal / architecture
**Q. Design a regulated enterprise RAG assistant on Bedrock.** Knowledge Base over KMS-encrypted S3 with metadata filtering per tenant; `RetrieveAndGenerate` with a strong Claude model; Guardrail (PII redaction + grounding + denied topics); PrivateLink VPC endpoints (no internet); least-priv IAM per model + model-access governance + SCPs; model invocation logging (encrypted) for audit; `Converse` for portability; cost attribution via application inference profiles.

**Q. Customization ladder — what and when?** Prompt → RAG (knowledge) → fine-tune (behavior/format) → continued pre-training (domain) → distillation (cheaper student). Exhaust prompt + RAG before training; a custom model must be served on **Provisioned Throughput**.

**Q. On-demand vs Provisioned Throughput?** On-demand = per-token, shared, can throttle. Provisioned = reserved model-unit capacity, guaranteed throughput/latency, required for custom models, but bills whether used (idle-capacity trap). Provision only for steady high volume / SLAs / custom models.

**Q. Bedrock vs Claude Platform on AWS vs Anthropic API?** Bedrock = AWS-operated, multi-provider, `anthropic.`-prefixed IDs, feature subset. Claude Platform on AWS = Anthropic-operated via AWS (SigV4, same-day parity, bare IDs). Anthropic API = first-party. Pick Bedrock for one AWS service across many providers with AWS-native security/billing.

## Scenario
**Q. "Our Bedrock bill exploded."** Usually the biggest model used for everything. Right-size (small model for simple tasks), cap `maxTokens`, prompt-cache stable context, batch non-interactive jobs, and check for forgotten Provisioned Throughput. Attribute with application inference profiles.

**Q. "The chatbot hallucinates."** RAG the answers (Knowledge Base) so it's grounded; add a contextual-grounding Guardrail; instruct "answer only from context." If retrieval is the problem, fix chunking/embeddings/top-k and test `Retrieve` alone.

**Q. "Design private access with no internet egress."** PrivateLink interface endpoints for `bedrock-runtime` + KMS + in-Region processing + the data-privacy guarantee.

## Incident
**Q. "Calls suddenly fail with AccessDenied after we added a new model."** Likely **model access not enabled** for that family in the Region (separate from IAM). Enable access; verify the IAM policy's model ARN. Confirm via CloudTrail.

**Q. "Under load, requests throttle and drop."** Hit RPM/TPM quota. Add exponential backoff, switch to a cross-region inference profile, request a quota increase, or buy Provisioned Throughput. Watch `InvocationThrottles`.

**Q. "Responses come back redacted/blocked unexpectedly."** A Guardrail fired. Read the Guardrail assessment/trace to see which policy + strength, then tune it — don't just disable safety.

---

## Rapid-fire
- One API, many FMs; `Converse` = portable, `InvokeModel` = native body.
- Enable model access per Region (control plane) *and* IAM per model — two gates.
- Cross-region inference profile = geo-prefixed ID for availability/burst.
- Knowledge Bases = managed RAG; `RetrieveAndGenerate` = grounded + cited.
- Guardrails = filters + denied topics + PII + grounding (model-agnostic).
- Ladder: prompt → RAG → fine-tune → continued pretrain → distill.
- Custom model ⇒ Provisioned Throughput to serve.
- Data privacy: prompts/outputs not used to train base models, stay in-account/Region.
- No custom weights needed → Bedrock; train/host your own → SageMaker.

---

## Self-check
Answer any 3 Principal/scenario/incident questions aloud in <90s each without reading.
