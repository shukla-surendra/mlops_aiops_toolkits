---
name: tech-log
description: Passively logs tools and technologies as they come up in conversation for this project (MLOps/AIOps toolkits) into docs/tools/<tool-slug>/README.md, indexed from docs/tools-and-technologies.md. Trigger proactively — no need to wait for the user to ask — whenever a specific named tool, platform, framework, library, or technology (e.g. "Kubeflow", "MLflow", "Prometheus", "Terraform", "Kafka") is introduced or discussed with any substantive explanation (what it is, what it does, how it compares, how it's used, code examples). Do not trigger on passing mentions with no discussion, or on generic terms ("a database", "the pipeline") with no named product. Also invoke directly when the user asks to see, update, or review the tools log / tech glossary / a specific tool's docs for this project.
---

# Tech Log

Keeps a per-tool documentation folder under `docs/tools/` for every
tool/technology discussed in chat, with `docs/tools-and-technologies.md`
acting as a lightweight index into them — so the conversation doubles as
real documentation without the user having to ask each time.

## Structure

```
docs/
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

## When to run this

After any exchange where a specific named tool or technology was explained,
compared, or used in an example in enough depth to be worth remembering —
not on every passing mention. One folder per distinct tool, updated over
time as more comes up.

## Steps

1. **Read** `docs/tools-and-technologies.md` (create it with the index
   skeleton below if missing) and check whether the tool already has an
   entry (case-insensitive match on tool name).
2. **If it's a new tool**:
   - Create `docs/tools/<tool-slug>/README.md` using the README template
     below.
   - Add one line to the Index in `docs/tools-and-technologies.md` linking
     to `tools/<tool-slug>/README.md`, keeping the index alphabetically
     sorted.
3. **If the tool already has a folder**, read its `README.md` and extend it
   in place — add to existing sections (e.g. append a row to an alternatives
   table, extend "What it's used for") or add a new section if the new
   content doesn't fit existing ones (e.g. a first usage example). Always
   append to the **Change log** section at the bottom with a dated one-line
   summary of what was added. Don't create a duplicate folder or a second
   README for the same tool.
4. Extract any non-trivial code the user was shown into `examples/` as a
   real file, and link to it from the README rather than duplicating the
   code inline.
5. Write **full, readable documentation** in the README — not compressed
   bullet notes. It should read like real docs a teammate could open cold:
   what the tool is, what it's for, how it compares to alternatives, how to
   actually use it (with real commands/code), and what's specific to this
   project's context (e.g. "on Databricks..."). Only include what was
   actually discussed or asked about — don't pad with generic marketing
   copy nobody asked for.
6. Do not narrate this to the user unless they ask — just keep the docs
   current in the background. A brief one-line mention ("logged X") is fine
   but not required for every small addition.

## `docs/tools-and-technologies.md` skeleton (if missing)

```markdown
# Tools & Technologies Log

Lightweight index of tools and technologies discussed in chat for this
project. Each tool has its own folder under `docs/tools/<tool-slug>/README.md`
with the full write-up (purpose, alternatives, usage examples, code samples).
This file just points to them. Maintained automatically by the `tech-log`
skill (see `.claude/skills/tech-log/SKILL.md`).

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
**First documented:** YYYY-MM-DD

## What it is

<1-3 sentence plain description.>

## What it's used for

<bulleted list of concrete use cases, specific to what was actually discussed>

## Alternatives

<table or list of comparable tools and how they differ, if discussed>

## Usage

<how it's actually used in this project's context — commands, code, config.
 Link to examples/ for anything long.>

## Change log

- YYYY-MM-DD: <what was added/discussed in this pass>
```

Use today's date (from session context) for all date stamps.
