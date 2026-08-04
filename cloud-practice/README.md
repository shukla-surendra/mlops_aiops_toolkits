# AWS Mastery — Architecture & Internals

A long-running (multi-month) deep study of AWS at **architecture / internals depth** — the knowledge senior AWS Solutions Architects, platform engineers, and SREs actually carry. **Not** certification-oriented.

**Method:** one service at a time, taught as progressive **gated modules**. You don't advance until you pass a knowledge check. Every internal claim is tagged **[Documented]** vs **[Inferred]**. Everything is related back to Linux, Kubernetes, networking, and distributed systems.

## 👉 Start / resume here

Open **[PROGRESS.md](PROGRESS.md)** — the master tracker. It always says exactly where we are and what's next. Read it first in any session.

Two tracks: **`aws/`** (active) and **`gcp/`** (planned, taught by contrast later).

## Current focus

**AWS · Service #1: VPC / Networking**
- Module 1 (why VPC exists, the two-networks mental model, internal architecture): **[aws/docs/vpc/architecture.md](aws/docs/vpc/architecture.md)**
- Module 1 gate (answer to advance): **[aws/quizzes/vpc/module-1-gate.md](aws/quizzes/vpc/module-1-gate.md)**

## Docs site

All Markdown renders to a self-contained, themed HTML site — persistent left-nav sidebar (grouped, filterable, `/` to focus), breadcrumbs, prev/next pager, reading-progress bar, on-page TOC with scroll-spy, code copy-buttons, auto-styled `[Documented]`/`[Inferred]` badges, and a no-flash light/dark theme:

```bash
pip install -r requirements.txt
make docs     # render to docs_html/ and serve at http://localhost:8000
make check    # validate all relative Markdown links, then build (CI-friendly)
```

## Layout

See the repo structure section in [PROGRESS.md](PROGRESS.md#5-repo-structure-filled-incrementally). Folders are created as each service/module is covered.

## How a session works

1. Read `PROGRESS.md` → Current Position.
2. If a gate is OPEN, write your answers into the gate file (or in chat).
3. Mentor grades, patches gaps, writes the next module to `aws/docs/<service>/`, opens the next gate, and updates `PROGRESS.md`.
