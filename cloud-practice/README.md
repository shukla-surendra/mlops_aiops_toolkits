# AWS Mastery — Architecture & Internals

A long-running (multi-month) deep study of AWS at **architecture / internals depth** — the knowledge senior AWS Solutions Architects, platform engineers, and SREs actually carry. **Not** certification-oriented.

**Method:** one service at a time, taught as progressive **gated modules**. You don't advance until you pass a knowledge check. Every internal claim is tagged **[Documented]** vs **[Inferred]**. Everything is related back to Linux, Kubernetes, networking, and distributed systems.

## 👉 Start / resume here

Open **[PROGRESS.md](PROGRESS.md)** — the master tracker. It always says exactly where we are and what's next. Read it first in any session.

Three tracks: **`aws/`** (active), **`azure/`** (active, taught by contrast with AWS), and
**`gcp/`** (planned, starts after AWS+Azure, taught by contrast later). Need a fast
service-mapping reference instead of the full gated Azure curriculum? See
**[aws-to-azure-transition-guide.md](aws-to-azure-transition-guide.md)** — a standalone
doc, not part of the gated curriculum. Planning an actual large-scale migration? See
**[aws-to-azure-migration-strategy.md](aws-to-azure-migration-strategy.md)** — a
Principal-Engineer-level migration plan (Gartner's 5 Rs → AWS's 7 Rs → wave planning →
worked timeline) for a 200-service AWS→Azure migration.

## Current focus

**AWS · EBS (#2) + EFS (#3)** — docs complete, awaiting learner Q&A. VPC (#1) paused, docs complete: **[aws/docs/vpc/architecture.md](aws/docs/vpc/architecture.md)**.

**Azure · Service #1: VNet** — M1 delivered, gate open: **[azure/docs/vnet/architecture.md](azure/docs/vnet/architecture.md)** / **[azure/quizzes/vnet/module-1-gate.md](azure/quizzes/vnet/module-1-gate.md)**. See [azure/README.md](azure/README.md) for the planned service order.

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
