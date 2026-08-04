# Amazon Bedrock — Complete documentation set

Deep-dive on the managed foundation-model (FM) service, beginner → advanced. Read in order.

## Study order

1. **[architecture.md](architecture.md)** — *Why Bedrock exists · the "serverless foundation models via one API" mental model · internal architecture* (control/data plane, the multi-provider model plane, how a token request flows, cross-region inference). **Start here.**
2. **[models-inference.md](models-inference.md)** — the model catalog (incl. Claude), `InvokeModel` vs the unified `Converse` API, streaming, inference parameters, inference profiles / cross-region inference.
3. **[knowledge-bases.md](knowledge-bases.md)** — managed RAG: Knowledge Bases, embeddings, vector stores, retrieval + `RetrieveAndGenerate`.
4. **[agents.md](agents.md)** — Bedrock Agents (action groups, orchestration, memory), plus Flows and Prompt Management.
5. **[customization.md](customization.md)** — fine-tuning, continued pre-training, distillation, model evaluation, and **Provisioned Throughput**.
6. **[security.md](security.md)** — IAM, data privacy guarantees, **Guardrails**, PrivateLink/VPC, KMS.
7. **[best-practices.md](best-practices.md)** — cost model (per-token vs provisioned), monitoring, anti-patterns, production patterns.
8. **[troubleshooting.md](troubleshooting.md)** — access/throttling/region errors, guardrail blocks, RAG quality, latency/cost.
9. **[interview.md](interview.md)** — junior→principal Q&A, scenarios, incidents.

## Quick reference
- **[Bedrock cheatsheet](../../cheatsheets/bedrock.md)**

## Hands-on
- **[Terraform: Bedrock](../../terraform/bedrock/README.md)** — invoke IAM role, a Guardrail, and model-invocation logging.
- **[boto3: Bedrock](../../boto3/bedrock/README.md)** — Converse + InvokeModel + streaming + Guardrail, using Claude on Bedrock.
- **[Labs: Bedrock](../../labs/bedrock/README.md)** — beginner→advanced, each with objectives/validation/cleanup.

## Related
- **[SageMaker docs](../sagemaker/README.md)** — the build-vs-consume contrast: SageMaker = train/host *your* models; Bedrock = consume managed FMs via API. Read after SageMaker.

---
*Convention:* claims tagged **[Documented]** (AWS docs / re:Invent / the Anthropic Claude-on-Bedrock reference) or **[Inferred]** (reconstruction from behavior). Model IDs and pricing move fast — verify live.
