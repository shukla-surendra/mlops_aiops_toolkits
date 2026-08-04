# Bedrock Cheatsheet

One-page recall. Full detail in [`../docs/bedrock/`](../docs/bedrock/README.md).

## Mental model
**Serverless multiplexer in front of many foundation models.** Send `{model_id + messages + params}` to a regional `bedrock-runtime` endpoint (IAM/SigV4); AWS runs inference on provider-hosted models and streams tokens. No GPUs, endpoints, or scaling groups. Consume FMs (vs SageMaker = build/host your own).

## Two APIs
- **`Converse` / `ConverseStream`** — provider-agnostic (swap models by ID); unified tool use. **Default.**
- **`InvokeModel`** — model's **native** body. Claude: `{"anthropic_version":"bedrock-2023-05-31","messages":[...],"max_tokens":N}`.

## Model IDs (Claude on Bedrock)
`anthropic.` prefix: `anthropic.claude-opus-4-8` · `anthropic.claude-sonnet-5` · `anthropic.claude-haiku-4-5` · `anthropic.claude-fable-5`. Cross-region profile adds geo: `us.anthropic.claude-opus-4-8` (often the required on-demand path). Providers: Anthropic, Amazon Nova/Titan, Meta Llama, Mistral, Cohere, AI21, Stability.

## Two gates before first call
1. **Enable model access** for the family in the Region (control plane).
2. **IAM** `bedrock:InvokeModel`/`Converse*` on the model ARN.

## Managed building blocks
- **Knowledge Bases** = managed **RAG** (S3 → chunk → embed → vector store → `RetrieveAndGenerate` with citations). Vector stores: OpenSearch Serverless / Aurora pgvector / Pinecone / …
- **Agents** = plan→act→observe loop with **action groups** (Lambda/APIs) + KB + memory + trace. `InvokeAgent`.
- **Flows** = visual deterministic pipelines. **Prompt Management** = versioned prompt catalog.
- **Guardrails** = content filters + denied topics + PII redact + word filters + **grounding check** (model-agnostic).

## Customization ladder
prompt → **RAG** (knowledge) → **fine-tune** (behavior/format) → continued pre-training (domain) → **distillation** (cheaper student). Custom model ⇒ served on **Provisioned Throughput**.

## Cost (model stable; rates live)
On-demand per **input+output token** (right-size the model!) · **Provisioned Throughput** = model-unit-hours (idle trap) · **Batch** ~50% off · KB embeddings + vector store · Guardrails per text unit.
Levers: right-size model → token caps + prompt cache → batch → on-demand+cross-region before provisioned → RAG over fine-tune → attribute via **application inference profiles**.
**Live pricing:** https://aws.amazon.com/bedrock/pricing/ · calc https://calculator.aws/

## Security
IAM per-model ARN + model-access gating + SCPs · **data privacy** (prompts/outputs not used to train base models, stay in-account/Region) · **Guardrails** · **PrivateLink** VPC endpoints (no internet) · **KMS** · model invocation logging + CloudTrail.

## Debug
AccessDenied → IAM *or* model-access not enabled · "use inference profile" → geo-prefixed ID · `ThrottlingException` → backoff / cross-region / quota / provisioned · redacted → Guardrail trace · RAG wrong → test `Retrieve` alone (chunking/embedding/top-k/sync) · custom model won't invoke → needs Provisioned Throughput.

## boto3 (Converse)
```python
brt = boto3.client("bedrock-runtime")
r = brt.converse(modelId="anthropic.claude-opus-4-8",
    messages=[{"role":"user","content":[{"text":"hi"}]}],
    inferenceConfig={"maxTokens":512})
print(r["output"]["message"]["content"][0]["text"], r["usage"])
```

## Terraform / boto3
`aws_bedrock_guardrail` · `aws_bedrock_model_invocation_logging_configuration` · `aws_iam_role/policy` (invoke) · `aws_bedrockagent_knowledge_base`/`agent` (advanced). Examples: [`../terraform/bedrock/`](../terraform/bedrock/README.md), [`../boto3/bedrock/`](../boto3/bedrock/README.md).

## Bedrock vs Claude Platform on AWS vs Anthropic API
Bedrock = AWS-operated, multi-provider, `anthropic.`-prefixed, feature subset · Claude Platform on AWS = Anthropic-operated via AWS (SigV4, same-day parity, bare IDs) · Anthropic API = first-party.
