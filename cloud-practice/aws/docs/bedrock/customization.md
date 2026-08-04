# Bedrock — Customization, evaluation & Provisioned Throughput

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md), [models-inference.md](models-inference.md).

Spec sections 3, 7. When prompting + RAG aren't enough, you can **customize** a model on your data, **evaluate** which model is best, and reserve **dedicated capacity**.

---

## 1. The customization ladder (cheapest → heaviest)
1. **Prompt engineering** — free, instant. Try first.
2. **RAG (Knowledge Bases)** — ground on your data without changing weights. Covers most "it doesn't know our stuff" needs. See [knowledge-bases.md](knowledge-bases.md).
3. **Fine-tuning** — train on labeled `{prompt, completion}` pairs to specialize tone/format/task. Produces a **private custom model**.
4. **Continued pre-training** — further-train on large *unlabeled* domain corpora to shift the base's domain knowledge/style.
5. **Distillation** — use a large "teacher" model to generate training data that fine-tunes a smaller, cheaper "student" for your task (near-teacher quality, lower cost/latency).

**Rule:** exhaust prompt + RAG before fine-tuning. Fine-tuning is for *behavior/format/skill*, RAG is for *knowledge*; they're complementary, not substitutes.

## 2. How customization works [Documented]
- You supply training (and validation) data in **S3** (format depends on the model).
- Bedrock runs a **training job** and produces a **custom model** that is **private to your account** — your data is not used to train the base model or shared with the provider.
- **A custom model must run on Provisioned Throughput** (below) to be invoked — you can't call a custom model on pure on-demand.
- Availability of fine-tuning/continued-pretraining depends on the model family (not every model supports every method) — check support before planning.

## 3. Model evaluation [Documented]
- **Bedrock Model Evaluation** compares models on *your* task — automatic metrics, **LLM-as-a-judge**, or **human** evaluation — so you pick by evidence, not vibes. Use it before committing to a model or after fine-tuning to prove a lift.

## 4. Provisioned Throughput [Documented]
- **On-demand** = pay per token, shared capacity, subject to throttling.
- **Provisioned Throughput** = reserve **model units** (a fixed throughput allotment) for a term (hourly, or 1/6-month commitments for discounts). Gives **guaranteed capacity + steadier latency**, and is **required to serve custom models**.
- **When:** predictable high-volume production, latency SLAs, or serving a custom model. Otherwise on-demand (+ cross-region inference profiles) is cheaper and simpler.
- **Cost caution:** provisioned capacity bills whether or not you use it — the Bedrock analog of an idle SageMaker endpoint. Right-size model units and commitment term.

## 5. Deciding
```
Need private knowledge?         → RAG (Knowledge Bases)
Need specific behavior/format?  → Fine-tune (then Provisioned Throughput to serve)
Cheaper/faster at a narrow task?→ Distill a smaller student
Predictable high volume / SLA?  → Provisioned Throughput
Which base model is best?       → Model Evaluation on your task
```

---

## Sources
- AWS docs: *Custom models*, *Fine-tuning & continued pre-training*, *Model distillation*, *Model evaluation*, *Provisioned Throughput*.

---

## Self-check
1. Order the customization ladder and state what each rung is *for* (knowledge vs behavior).
2. Why can't you serve a fine-tuned custom model on pure on-demand?
3. What is distillation and when does it pay off?
4. When is Provisioned Throughput worth it, and what's its cost trap?
5. How would you *prove* a fine-tuned model is actually better than the base for your task?
