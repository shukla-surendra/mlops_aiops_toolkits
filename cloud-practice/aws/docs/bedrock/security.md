# Bedrock — Security, data privacy & Guardrails

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md); [VPC security](../vpc/security.md).

Spec section 6. Bedrock security = **IAM (who can invoke what) + data-privacy guarantees + Guardrails (safe content) + private networking + encryption**.

---

## 1. IAM — least privilege for models [Documented]
- Every call is **IAM/SigV4**-authenticated. Gate the data-plane actions: `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, `bedrock:Converse*`, `bedrock-agent-runtime:RetrieveAndGenerate`, `bedrock:InvokeAgent`.
- **Scope by model:** the `Resource` is the model/inference-profile ARN — grant only the models an app needs (e.g. allow `anthropic.claude-haiku-4-5`, deny expensive models) using resource ARNs + conditions.
- **Model access is a separate control-plane gate:** an account must *enable access* to each model family per Region before anyone can invoke it — a deliberate governance step.
- Guard control-plane verbs (create/delete guardrails, KBs, agents, customization) tightly; use **SCPs** to enforce org-wide rules (e.g. "only approved models," "guardrail required").

## 2. Data privacy & residency [Documented]
- **Your prompts and completions are not used to train the base models**, are **not shared with model providers**, and stay within your **account + Region**. Fine-tuning creates a **private** model copy only you can access.
- **Region control:** data is processed in the Region you call; **cross-region inference profiles** may route within a *geography* (e.g. US Regions) — factor this into data-residency requirements.
- This guarantee is *the* reason regulated enterprises can use closed models (Claude) here rather than a public API.

## 3. Guardrails — configurable safety [Documented]
A **Guardrail** is a policy you attach to invocations (and Agents/KBs) that screens **input and output**:
- **Content filters** — block/attenuate hate, insults, sexual, violence, misconduct, and **prompt-attack** categories at configurable strengths.
- **Denied topics** — natural-language definitions of topics to refuse.
- **Word/profanity filters** — custom blocklists.
- **Sensitive information (PII)** — detect + **block or redact** PII (and custom regex) in prompts/outputs.
- **Contextual grounding & relevance checks** — verify an answer is grounded in the retrieved context and relevant to the query — anti-hallucination for RAG.
- Guardrails are **model-agnostic** (work across providers), versioned, and independently testable — apply the same safety policy no matter which FM you use.

## 4. Private networking & encryption [Documented]
- **PrivateLink:** interface **VPC endpoints** for `bedrock`/`bedrock-runtime`/`bedrock-agent-runtime` keep inference traffic on the AWS private network (no internet) — the regulated pattern (ties to [VPC endpoints](../vpc/networking.md)).
- **KMS:** encrypt custom-model artifacts, training data (S3), Knowledge Base data, and agent/session state with customer-managed keys.
- **Logging:** **model invocation logging** (prompts/responses → S3/CloudWatch, optionally KMS-encrypted) for audit; **CloudTrail** for the API actions; watch who invoked what.

## 5. Threat models

| Threat | Mechanism | Defense |
|---|---|---|
| **Prompt injection / jailbreak** | Malicious input hijacks the model or exfiltrates via tools | Guardrail prompt-attack filters + denied topics; least-priv tools; never trust model output as a command without validation |
| **PII leakage** | Model emits or logs sensitive data | Guardrail PII redaction; encrypt/limit invocation logs |
| **Cost/abuse** | Unbounded or expensive-model calls | IAM scoped to cheap models + `maxTokens`; quotas; budget alarms |
| **Data exfiltration** | App sends data to public model endpoints | PrivateLink + Region control + the data-privacy guarantee |
| **RAG data exposure** | Cross-tenant retrieval | KB metadata filtering + per-tenant scoping |
| **Over-broad model access** | Any app can call any model | Per-model IAM ARNs + model-access gating + SCPs |

---

## Sources
- AWS docs: *Data protection in Amazon Bedrock*, *Guardrails for Amazon Bedrock*, *IAM for Bedrock*, *VPC endpoints (PrivateLink)*, *Model invocation logging*, *Encryption of custom models*.

---

## Self-check
1. Name the two independent gates before an app can invoke a specific model in a Region.
2. State the Bedrock data-privacy guarantee in one sentence, and why it enables regulated use of closed models.
3. List four things a Guardrail can enforce, and which one fights RAG hallucination.
4. How do you keep inference traffic off the public internet, and which VPC feature is it?
5. Design the IAM so an app can call only a cheap model with a token cap — what two controls?
