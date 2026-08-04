---
name: tech-log
description: Passively logs tools and technologies as they come up in conversation — anywhere in this monorepo (cloud-practice, k8n_explorer, agentsexplore, engineering_notebook, mlops_aiops, or elsewhere) — into mlops_aiops/docs/tools/<tool-slug>/README.md, indexed from mlops_aiops/docs/tools-and-technologies.md. One shared glossary for the whole repo, regardless of which subtree prompted the discussion. Trigger proactively — no need to wait for the user to ask — whenever a specific named tool, platform, framework, library, or technology (e.g. "Kubeflow", "MLflow", "Prometheus", "Terraform", "Kafka") is introduced or discussed with any substantive explanation (what it is, what it does, how it compares, how it's used, code examples). Do not trigger on passing mentions with no discussion, or on generic terms ("a database", "the pipeline") with no named product. Also invoke directly when the user asks to see, update, or review the tools log / tech glossary / a specific tool's docs.
---

# Tech Log

Keeps a per-tool documentation folder under `mlops_aiops/docs/tools/` for
every tool/technology discussed in chat, with
`mlops_aiops/docs/tools-and-technologies.md` acting as a lightweight index
into them — so the conversation doubles as real documentation without the
user having to ask each time. This is the **one shared tech glossary for
the whole monorepo** — it doesn't matter whether the discussion started
while looking at `cloud-practice/`, `k8n_explorer/`, `agentsexplore/`,
`engineering_notebook/`, or `mlops_aiops/` itself; everything lands in the
same place under `mlops_aiops/docs/`.

## Structure

```
mlops_aiops/docs/
  tools-and-technologies.md          <- index only: one line per tool + link
  tools/
    <tool-slug>/
      README.md                      <- full write-up for this tool
      examples/                      <- extracted code samples, if any
        <descriptive-name>.py
```

- `<tool-slug>` is the tool name lowercased, spaces/parens replaced with
  hyphens (e.g. "Evidently (Evidently AI)" -> `evidently`, "Databricks
  Lakehouse Monitoring" -> `databricks-lakehouse-monitoring`). Pick the
  simplest recognizable slug, not the full display name.
- Every tool gets a folder + README, even if short at first — it grows over
  time as more comes up in later conversations.
- Substantial code examples (more than ~10 lines, or anything meant to be
  reused/copied) go in `examples/<name>.py` (or `.sql`, `.yaml`, whatever
  fits) inside that tool's folder, referenced from the README rather than
  pasted inline. Short illustrative snippets can stay inline in the README.

## No dated changelog — update docs in place

Docs here are **living documentation, not a log.** Never add a "Change
log" section or dated bullets ("2026-08-04: added X"). When new information
comes up about a tool that already has a doc, rewrite/merge it directly
into the relevant section — the doc should always read like it was written
fresh today, with no history of how it accumulated. If something discussed
earlier turns out to be wrong or outdated, correct it in place rather than
appending a correction below it.

## When to run this

After any exchange where a specific named tool or technology was explained,
compared, or used in an example in enough depth to be worth remembering —
not on every passing mention. One folder per distinct tool, updated over
time as more comes up.

## Steps

1. **Read** `mlops_aiops/docs/tools-and-technologies.md` (create it with
   the index skeleton below if missing) and check whether the tool already
   has an entry (case-insensitive match on tool name).
2. **If it's a new tool**:
   - Create `mlops_aiops/docs/tools/<tool-slug>/README.md` using the
     README template below.
   - Add one line to the Index in
     `mlops_aiops/docs/tools-and-technologies.md` linking to
     `tools/<tool-slug>/README.md`, keeping the index alphabetically
     sorted.
3. **If the tool already has a folder**, read its `README.md` and merge
   the new information directly into the right existing section (e.g. add
   a row to an alternatives table, extend "What it's used for" with a new
   use case, correct something that changed) — or add a new section if it
   genuinely doesn't fit an existing one (e.g. a first usage example, a
   newly-discussed relationship to another tool). Don't create a duplicate
   folder or a second README for the same tool, and don't leave a trail of
   "also discussed on [date]" — just update the doc as if it always said
   this.
4. Extract any non-trivial code the user was shown into `examples/` as a
   real file, and link to it from the README rather than duplicating the
   code inline.
5. Write **full, readable documentation** in the README — not compressed
   bullet notes. It should read like real docs a teammate could open cold:
   what the tool is, what it's for, how it compares to alternatives, how to
   actually use it (with real commands/code), and what's specific to this
   repo's context (e.g. "on Databricks...", "on EKS..."). Only include what
   was actually discussed or asked about — don't pad with generic
   marketing copy nobody asked for.
6. Do not narrate this to the user unless they ask — just keep the docs
   current in the background. A brief one-line mention ("logged X") is fine
   but not required for every small addition.

## `mlops_aiops/docs/tools-and-technologies.md` skeleton (if missing)

```markdown
# Tools & Technologies Log

Lightweight index of tools and technologies discussed in chat, across this
whole monorepo. Each tool has its own folder under
`mlops_aiops/docs/tools/<tool-slug>/README.md` with the full write-up
(purpose, alternatives, usage examples, code samples). This file just
points to them. Maintained automatically by the `tech-log` skill (see
`.claude/skills/tech-log/SKILL.md`).

## Index

<!-- INDEX_START -->
_(no entries yet)_
<!-- INDEX_END -->
```

## Index line format

```markdown
- [<Tool Name>](tools/<tool-slug>/README.md) — <category>
```

## Per-tool `README.md` template

```markdown
# <Tool Name>

**Category:** <e.g. orchestration, observability, model serving, IaC, messaging>

## What it is

<1-3 sentence plain description.>

## What it's used for

<bulleted list of concrete use cases, specific to what was actually discussed>

## Alternatives

<table or list of comparable tools and how they differ, if discussed>

## Usage

<how it's actually used, in whatever repo context it came up in — commands,
 code, config. Link to examples/ for anything long.>
```

No date stamps, no changelog section — every edit updates the doc as if it
were written fresh.
