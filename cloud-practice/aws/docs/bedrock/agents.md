# Bedrock — Agents, Flows & Prompt Management

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md), [knowledge-bases.md](knowledge-bases.md).

Spec section 3. An **agent** turns an FM from "answer a question" into "accomplish a task" — it plans, calls tools/APIs, retrieves knowledge, and loops until done. Bedrock Agents is the managed orchestration layer for that loop.

---

## 1. The mental model
Give the model **tools** and a **goal**; it decides which tool to call, reads the result, and iterates. The loop (reason → act → observe → repeat) is the agent. Bedrock runs that loop for you and calls your code/APIs when the model requests them.

```
goal ─► [model plans] ─► call action group (Lambda/API) ─► observe result
   ▲                                                          │
   └──────────────── loop until goal met ◄────────────────────┘
          (also: query Knowledge Bases, apply Guardrails, use memory)
```

## 2. Bedrock Agents — the pieces [Documented]
- **Foundation model** — the reasoning engine (e.g. `anthropic.claude-opus-4-8`).
- **Instructions** — a system prompt defining the agent's role/behavior.
- **Action groups** — the agent's **tools**: each maps to a **Lambda function** (or a return-control-to-caller contract) with an **OpenAPI / function schema** describing the operations + parameters. The model fills the parameters; Bedrock invokes the Lambda; the result feeds back.
- **Knowledge Bases** — attach one or more so the agent can retrieve grounded facts.
- **Guardrails** — attach for safety on every turn.
- **Memory** — optional session memory so multi-turn tasks retain context.
- **Orchestration** — Bedrock runs the plan/act/observe loop; you can inspect the **trace** (the model's reasoning + tool calls) for debugging.

Invoke with `InvokeAgent` (`bedrock-agent-runtime`), streaming the agent's steps + final answer.

## 3. Return of control vs Lambda
- **Lambda action groups** — Bedrock calls your Lambda directly (fully managed loop).
- **Return control** — Bedrock hands the tool call back to *your* application to execute (when the tool needs your runtime, credentials, or human approval), then you send the result back. The analog of client-side tools.

## 4. Flows — visual orchestration [Documented]
**Bedrock Flows** let you wire a directed graph of steps — prompts, models, Knowledge Bases, Lambdas, conditions, iterators — into a deployable workflow without hand-coding the glue. Good for deterministic multi-step GenAI pipelines (classify → retrieve → summarize → route) where you want structure over open-ended agency.

## 5. Prompt Management [Documented]
A **versioned catalog** of prompts (with variables, model + inference config, and versions/aliases) so prompts are managed artifacts — testable, comparable, and referenced by ID from apps/Flows/Agents — instead of strings scattered in code. The GenAI analog of a model registry for prompts.

## 6. Agents vs Flows vs plain Converse-with-tools
- **Plain `Converse` + `toolConfig`** — you own the tool loop in code; maximum control, minimal managed machinery (mirrors the "manual loop / tool runner" choice on the Anthropic API).
- **Bedrock Agents** — managed open-ended agentic loop (planning + tools + KB + memory + trace) with less code.
- **Flows** — deterministic, graph-structured pipelines when the steps are known in advance.

Choose by how open-ended the task is and how much orchestration you want AWS to own.

---

## Sources
- AWS docs: *Agents for Amazon Bedrock*, *Action groups*, *Return control*, *Agent memory*, *Bedrock Flows*, *Prompt Management*.

---

## Self-check
1. Describe the agent loop in four words, and what an "action group" is.
2. When would you use "return control" instead of a Lambda action group?
3. Flows vs Agents — which fits a fixed classify→retrieve→summarize pipeline, and why?
4. What does the agent **trace** give you, and why does it matter operationally?
5. When is plain `Converse` + `toolConfig` the right call over Bedrock Agents?
