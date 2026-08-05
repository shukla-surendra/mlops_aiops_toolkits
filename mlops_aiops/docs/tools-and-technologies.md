# Tools & Technologies Log

Lightweight index of tools and technologies discussed in chat for this
project. Each tool has its own folder under `docs/tools/<tool-slug>/README.md`
with the full write-up (purpose, alternatives, usage examples, code samples).
This file just points to them. Maintained automatically by the `tech-log`
skill (see `../../.claude/skills/tech-log/SKILL.md`, at the repo root).

## Index

<!-- INDEX_START -->
- [Databricks Lakehouse Monitoring](tools/databricks-lakehouse-monitoring/README.md) — ML monitoring / observability (Databricks-native)
- [ELK / EFK Stack (Elasticsearch, Logstash/Fluentd, Kibana)](observability-on-eks.md#logs-the-fork-in-the-road--loki-vs-elkefk) — observability / monitoring (logs)
- [Evidently (Evidently AI)](tools/evidently/README.md) — ML monitoring / observability
- [Feast](tools/feast/README.md) — feature store
- [Grafana](tools/grafana/README.md) — observability / monitoring (Kubernetes/EKS)
- [Loki](tools/loki/README.md) — observability / monitoring (Kubernetes/EKS)
- [MLflow](tools/mlflow/README.md) — experiment tracking / model registry / model lifecycle
- [ML & GenAI Lifecycle and Governance](ml-genai-lifecycle-and-governance.md) — cross-cutting: lifecycle stages, data/model governance, SR 11-7, EU AI Act, GDPR Art. 22
- [MLOps, AIOps, LLMOps (definitions & origins)](mlops-aiops-llmops.md) — cross-cutting: what each discipline is, who defines it, where they overlap
- [Observability on EKS (overview)](observability-on-eks.md) — cross-cutting: Prometheus, Grafana, Loki, ELK/EFK, tracing, alerting, alternatives
- [OpenTelemetry / Tempo / Jaeger](observability-on-eks.md#traces-the-pillar-people-forget) — observability / monitoring (tracing)
- [Prometheus](tools/prometheus/README.md) — observability / monitoring (Kubernetes/EKS)
- [vLLM](tools/vllm/README.md) — LLM inference / serving
<!-- INDEX_END -->
