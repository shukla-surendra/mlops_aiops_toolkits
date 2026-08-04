# mlops_aiops_toolkits

A personal monorepo — this project's own MLOps/AIOps tooling work, plus
several previously separate practice repos merged in with full commit
history (via `git subtree`, not submodules — each folder below is native
history in this repo now, not a reference to an external one).

## Top-level folders

| Folder | What's in it |
|---|---|
| **`mlops_aiops/`** | This repo's own content: `docs/` (tool write-ups — Evidently, MLflow, Feast, Prometheus/Grafana/Loki, ELK/EFK, CloudWatch, observability on EKS) and `projects/` (runnable, uv-managed demo notebooks for the tools documented in `docs/`). Also holds `.claude/` — the Claude Code skill (`tech-log`) that keeps `docs/` updated as tools get discussed. |
| **`cloud-practice/`** | AWS/cloud practice notes and Terraform — VPC, EBS/EFS, SageMaker, Bedrock, SQS, and a full Terraform reference. |
| **`k8n_explorer/`** | Kubernetes practice — pod/node affinity, service types, Jobs/CronJobs, Helm charts, a Kubeflow pipeline sample, a KServe inference example, and a Grafana/Loki log-viewer demo. Has its own MkDocs site. |
| **`genai_lab/`** | Agentic AI / LLM tooling practice — MCP (from scratch and official SDKs), FastMCP auth patterns, LangGraph + Ollama, vector DBs (FAISS, Qdrant, pgvector), RAG, and Bedrock AgentCore. Has its own MkDocs site. |
| **`engineering_notebook/`** | Interview prep — DSA, system design (foundations + practice), low-level design, security engineering, behavioral. Has its own MkDocs site. |

## Why the split

`cloud-practice`, `k8n_explorer`, `genai_lab`, and `engineering_notebook`
were each their own repo, each already self-contained with its own
Makefile/MkDocs config — merging them in with `git subtree` preserved that
structure and their full commit history rather than flattening everything
into one undifferentiated tree. `mlops_aiops/` is where this repo's own
work happens going forward.
