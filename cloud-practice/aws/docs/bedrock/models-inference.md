# Bedrock — Models & inference

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md).
> **Epistemics:** model IDs/params from the AWS + Anthropic references; **they change fast — verify live.**

Spec sections 3, 7. How you actually call models: the catalog, `Converse` vs `InvokeModel`, streaming, parameters, and inference profiles.

---

## 1. The model catalog [Documented]
Bedrock offers serverless models across providers and modalities:
- **Anthropic Claude** — chat/reasoning/agentic/vision (`anthropic.claude-opus-4-8`, `anthropic.claude-sonnet-5`, `anthropic.claude-haiku-4-5`, `anthropic.claude-fable-5`).
- **Amazon Nova / Titan** — text, multimodal, embeddings, image generation.
- **Meta Llama**, **Mistral**, **Cohere** (text + **embeddings**), **AI21**, **Stability** (images), plus **Bedrock Marketplace** models.

Pick by task: reasoning/agentic/coding → a strong Claude model; cheap/fast classification → a small/Haiku-class model; embeddings → Titan/Cohere embeddings; images → Nova/Titan Image/Stability. **You must enable model access per model family, per Region** before use (a one-time control-plane step).

## 2. The two inference APIs [Documented]

### `Converse` / `ConverseStream` (modern default)
Provider-agnostic message format — roles, content blocks, tool use, system prompts, inference config — so switching models is a model-ID change:
```python
import boto3
brt = boto3.client("bedrock-runtime", region_name="us-east-1")
resp = brt.converse(
    modelId="anthropic.claude-opus-4-8",   # or us.anthropic.claude-opus-4-8 (cross-region)
    messages=[{"role": "user", "content": [{"text": "Explain VPC in 2 sentences."}]}],
    system=[{"text": "You are a precise cloud tutor."}],
    inferenceConfig={"maxTokens": 512, "temperature": 0.2},
)
print(resp["output"]["message"]["content"][0]["text"])
print(resp["usage"])  # inputTokens / outputTokens
```
- `toolConfig` adds **tool use** (function calling) in a unified shape.
- `ConverseStream` yields token deltas for low-latency UIs.

### `InvokeModel` (native body)
Pass the model's **own** request JSON when you need provider-specific features. For Claude, that's the **Anthropic Messages API** body:
```python
import json
resp = brt.invoke_model(
    modelId="anthropic.claude-opus-4-8",
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "messages": [{"role": "user", "content": "Explain VPC in 2 sentences."}],
    }),
)
print(json.loads(resp["body"].read())["content"][0]["text"])
```
Use `Converse` unless you need a native feature it doesn't expose; use `InvokeModel` (or the **Anthropic Bedrock SDK client**) for Claude-native params like adaptive thinking.

## 3. Inference parameters [Documented]
- **`maxTokens`** — output cap; too low truncates mid-answer.
- **`temperature` / `topP`** — randomness (lower = more deterministic). *Note:* the newest Claude models (Opus 4.8/4.7, Sonnet 5) reject non-default sampling params via the Anthropic-native path — steer with prompting instead; the `Converse` inferenceConfig still accepts the common knobs where the model supports them. Verify per model.
- **`stopSequences`**, **system prompt**, **tool config**. Streaming vs non-streaming is an API choice, not a parameter.

## 4. Inference profiles / cross-region inference [Documented]
- **Cross-region inference profiles** (geo-prefixed IDs like `us.anthropic.claude-opus-4-8`) let Bedrock route across Regions in a geography for better availability + burst throughput. For many current models this profile is the **on-demand** path — a bare `anthropic.claude-...` ID may return an error telling you to use the profile.
- **Application inference profiles** attach tags to a model reference so you can **attribute cost/usage** per app/team in Cost Explorer.

## 5. Multimodal & embeddings
- **Vision:** Claude and Nova accept images in the message content for understanding tasks.
- **Embeddings:** Titan/Cohere embedding models turn text into vectors — the backbone of Knowledge Bases / semantic search (see [knowledge-bases.md](knowledge-bases.md)).
- **Image generation:** Nova/Titan Image/Stability produce images from prompts.

## 6. Latency & throughput
- Latency scales with output length + model size; **stream** for responsiveness.
- On-demand throughput is subject to per-account/per-model **quotas** (RPM/TPM); bursts throttle (`ThrottlingException`) → retry with backoff, use cross-region profiles, or buy **Provisioned Throughput** (see [customization.md](customization.md)) for guaranteed capacity.

---

## Sources
- AWS docs: *Converse API reference*, *InvokeModel*, *Inference parameters*, *Cross-region inference*, *Supported foundation models*, *Model access*.
- Anthropic: *Claude on Amazon Bedrock* (model IDs, native Messages body, `anthropic_version: bedrock-2023-05-31`).

---

## Self-check
1. Why does `Converse` make model-swapping easy, and when must you fall back to `InvokeModel`?
2. What's the native request body shape for calling Claude via `InvokeModel` (the two required-ish fields)?
3. You get an error telling you to use an inference profile for a model. What ID form fixes it and why?
4. Your app throttles under load. Give three ways to raise effective throughput.
5. Which model type underpins Knowledge Bases, and what does it produce?
