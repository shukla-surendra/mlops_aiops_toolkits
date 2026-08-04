# Bedrock — Module 1: Why it exists, the mental model, and the internal architecture

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Epistemics:** **[Documented]** = AWS docs / re:Invent / the Anthropic *Claude on Amazon Bedrock* reference · **[Inferred]** = reconstruction from behavior.

**Scope:** spec sections 1–3. Why Bedrock exists, the mental model, and the internal architecture (control/data plane, the multi-provider model plane, request flow, cross-region inference).

---

## 1. Why does Bedrock exist?

### The problem in one sentence
Teams want to build with **foundation models** (Claude, Llama, Amazon Nova, etc.) without provisioning GPUs, hosting models, managing scaling, or wiring up RAG/agents/guardrails from scratch — and enterprises need it with **their data staying private** and AWS-native security/billing.

### History: how you used LLMs before
- **Self-host** the weights on GPU clusters (or SageMaker) — you own inference infra, scaling, and optimization. Heavy, and impossible for closed models like Claude whose weights you can't download.
- **Call a single provider's public API** — simple, but a separate vendor relationship, separate billing, data leaving your cloud, and you're locked to one model family with its own SDK.
- Building **RAG, agents, and safety filters** meant assembling vector DBs, orchestration loops, and moderation yourself.

### Why AWS built Bedrock (2023)
**Bedrock is a single, serverless API to many foundation models**, plus managed building blocks (Knowledge Bases for RAG, Agents, Guardrails, customization) — all under **AWS IAM, VPC, KMS, CloudWatch/CloudTrail, and AWS billing**, with a **data-privacy guarantee** (your prompts/outputs aren't used to train the base models and don't leave your control). It's the "consume FMs the AWS-native way" service, the counterpart to SageMaker's "build/host your own."

### What if it didn't exist?
- Per-provider API integrations + separate billing/security reviews for each model vendor.
- DIY hosting for open models; no managed access to closed models within your AWS security boundary.
- Hand-built RAG/agents/guardrails.

> **Bedrock vs "Claude Platform on AWS" vs the Anthropic API** [Documented]: **Amazon Bedrock** is *AWS-operated* (AWS runs the service; model IDs are `anthropic.`-prefixed; feature set is a subset; release cadence can trail). **Claude Platform on AWS** is *Anthropic-operated* through AWS (SigV4 auth, AWS billing, same-day API parity, bare model IDs). The **Anthropic API** is first-party. Pick Bedrock when you want one AWS service spanning many providers with AWS-native IAM/VPC/billing.

---

## 2. The core mental model

> **Bedrock is a serverless multiplexer in front of many foundation models. You send a request (prompt + params + a model ID) to a regional API endpoint; AWS runs inference on managed, provider-hosted models and streams tokens back. You never see a GPU, an endpoint, or a scaling group.**

Two ideas unlock it:
- **One API, many models.** The **`Converse` API** gives a *provider-agnostic* message format so you can swap `anthropic.claude-opus-4-8` for `meta.llama...` or `amazon.nova...` by changing a model ID. (`InvokeModel` passes the model's *native* request/response body when you need provider-specific features.)
- **Managed building blocks on top.** Knowledge Bases (RAG), Agents (tool-using orchestration), Guardrails (safety), and Customization (fine-tuning) are AWS-managed services that call the same model plane — so you assemble a GenAI app from primitives instead of infrastructure.

```
   Your app                         Bedrock (managed, serverless)
   ┌───────────────┐   IAM/SigV4    ┌───────────────────────────────────────┐
   │ Converse /    │  ───────────►  │ Control plane: model access, config,   │
   │ InvokeModel   │                │  guardrails, KB/agent definitions      │
   │ + model_id    │                │ Data plane: run inference on the FM,   │
   │ + params      │  ◄─── tokens ─ │  stream tokens; apply guardrails;      │
   └───────────────┘   (stream)     │  RAG retrieval; agent tool loop        │
                                    │ Model plane: Anthropic / Meta / Amazon │
                                    │  / Mistral / Cohere / AI21 / Stability │
                                    └───────────────────────────────────────┘
```

This is the same "virtualize the resource, run it as a managed service, drive it by API" pattern as the rest of AWS — applied to **model inference**.

---

## 3. The model & feature plane (what's actually in "Bedrock")

| Capability | What it is |
|---|---|
| **Foundation models** | Serverless access to models from **Anthropic (Claude), Amazon (Nova/Titan), Meta (Llama), Mistral, Cohere, AI21, Stability**, plus **Bedrock Marketplace** models. Text, chat, embeddings, and image models. |
| **`Converse` / `ConverseStream`** | Unified, provider-agnostic messages API (roles, content blocks, tool use). The modern default. |
| **`InvokeModel` / `...WithResponseStream`** | Pass a model's **native** request body (e.g., the Anthropic Messages API JSON) for provider-specific features. |
| **Knowledge Bases** | Managed **RAG**: ingest docs → embeddings → vector store → retrieval + `RetrieveAndGenerate`. |
| **Agents** | Tool-using orchestration: the model plans, calls **action groups** (Lambda/APIs) and Knowledge Bases, and loops to a goal. |
| **Guardrails** | Configurable safety: content filters, denied topics, PII redaction, word filters, contextual grounding checks. |
| **Customization** | **Fine-tuning**, **continued pre-training**, **distillation**, **model evaluation**. |
| **Provisioned Throughput** | Reserve dedicated model capacity (model units) for guaranteed throughput / custom models. |
| **Flows / Prompt Management** | Visual orchestration of prompts + models + KBs + Lambdas; versioned prompt catalog. |
| **Inference profiles** | **Cross-region** inference routing + **application inference profiles** for cost attribution. |

You don't use all of it — a minimal app is just `Converse` with a model ID. The rest is GenAI-app maturity.

---

## 4. Internal architecture

### 4a. Control plane vs data plane [Documented behavior]
- **Control plane** (`bedrock` API): manage **model access** (you must *request/enable* access to each model family per Region), create guardrails, knowledge bases, agents, customization jobs, provisioned throughput.
- **Data plane** (`bedrock-runtime`, `bedrock-agent-runtime`): the actual inference — `Converse`, `InvokeModel`, `RetrieveAndGenerate`, `InvokeAgent`. This is where tokens flow and latency lives.

### 4b. How a request physically flows [Documented + Inferred]
1. Your app calls the **regional** `bedrock-runtime` endpoint with **SigV4 (IAM)** auth, a **model ID** (e.g. `anthropic.claude-opus-4-8`), and the request body.
2. Bedrock authenticates (IAM), checks you've been **granted model access**, and routes to the **provider-hosted model** in that Region (models run on AWS-managed, provider-isolated infrastructure).
3. If a **Guardrail** is attached, input is screened before inference and output is screened/redacted as it streams.
4. Inference runs; tokens **stream** back (`ConverseStream`/`...WithResponseStream`).
5. **CloudWatch** metrics + optional **model invocation logging** (to S3/CloudWatch) record the call; **CloudTrail** records the API action.

### 4c. Cross-region inference (inference profiles) [Documented]
- On-demand capacity for popular models is offered via **inference profiles** — model IDs prefixed by a geography (e.g. `us.anthropic.claude-opus-4-8`, `eu.anthropic...`) that let Bedrock **route the request across multiple Regions in that geography** for higher availability + throughput during spikes. For many current models the cross-region profile is the *required* way to get on-demand capacity.
- **Application inference profiles** wrap a model with tags so you can **attribute cost/usage** per app/team in Cost Explorer.

### 4d. Data privacy & isolation [Documented]
- **Your prompts and completions are not used to train the base FMs**, are not shared with model providers, and stay within your AWS account/Region boundary. Customization uses *your* data to make a **private** copy of the model that only you can access.
- Traffic can be kept off the public internet with **PrivateLink** (interface VPC endpoints for `bedrock-runtime`), and data encrypted with **KMS** (see [security.md](security.md)). This is why regulated enterprises can use closed models like Claude here.

### 4e. Claude on Bedrock specifics [Documented — Anthropic reference]
- Claude model IDs carry the **`anthropic.` prefix** (e.g. `anthropic.claude-opus-4-8`, `anthropic.claude-sonnet-5`, `anthropic.claude-haiku-4-5`); cross-region profiles add the geo prefix (`us.anthropic.claude-opus-4-8`).
- Two ways to call Claude: the **`Converse` API** (unified) or **`InvokeModel`** with the **Anthropic Messages API** body (`{"anthropic_version": "bedrock-2023-05-31", "messages": [...], "max_tokens": ...}`). The Anthropic SDK also ships a **Bedrock client** (`AnthropicBedrockMantle`) that speaks the Messages API against Bedrock.
- **Feature availability on Bedrock is a subset** of the first-party API — e.g. Message Batches, the Files API, web search/web fetch/code-execution server tools, automatic prompt caching, mid-conversation system messages, and fast mode are **not** available on Bedrock; extended/adaptive thinking, prompt caching, token counting, citations, and tool use **are**. Verify per feature before designing.

---

## Sources
- AWS docs: *What is Amazon Bedrock*, *Converse API*, *Supported models*, *Cross-region inference*, *Data protection in Bedrock*.
- Anthropic: *Claude on Amazon Bedrock* (model IDs, Mantle client, feature availability).
- re:Invent: *Bedrock* keynotes + deep dives.

---

## Self-check
1. In one sentence, what is Bedrock, and how does it differ from self-hosting a model on SageMaker?
2. `Converse` vs `InvokeModel` — what does each give you, and when do you reach for the native body?
3. What must you do *before* your first successful call to a given model in a Region, and which plane is that?
4. What is a cross-region inference profile, and what problem does the geo-prefixed model ID solve?
5. State the Bedrock data-privacy guarantee, and name two controls that keep inference traffic private.
