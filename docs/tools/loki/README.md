# Loki

**Category:** observability / monitoring (Kubernetes/EKS)
**First documented:** 2026-08-04

## What it is

Log aggregation system — described as "[Prometheus](../prometheus/README.md)
but for logs." It only indexes **labels** (e.g. namespace, pod, container)
rather than full-text content, which keeps storage/indexing costs much
lower than full-text log systems (e.g. ELK/OpenSearch). Queried with
**LogQL**.

## What it's used for on EKS

Loki itself only stores and serves logs — it doesn't collect them. On EKS
you need a **shipping agent** running as a DaemonSet on every node to tail
container logs and push them to Loki:

- **Promtail** — Loki's original/traditional shipping agent.
- **Grafana Alloy** — Promtail's successor, the currently recommended agent.
- **Fluent Bit** — a more general-purpose log shipper, also commonly used
  to ship to Loki.

## Deployment

Usually installed via the `loki-stack` Helm chart, or `loki` + a shipping
agent (`promtail`/`alloy`) as separate charts. Wired into the same
[Grafana](../grafana/README.md) instance that's already querying
[Prometheus](../prometheus/README.md) (e.g. from `kube-prometheus-stack`),
as a second data source — giving one UI for both metrics and logs.

## Related

Part of the metrics/logs/visualization trio commonly run together on EKS:
Prometheus (metrics), Loki (logs), Grafana (visualization) — see
[Prometheus](../prometheus/README.md) for the "LGTM stack" naming context.
For a direct comparison against the alternative logging architecture
(Elasticsearch/ELK/EFK) and a full integration-flow diagram, see
[`docs/observability-on-eks.md`](../../observability-on-eks.md).

## Change log

- 2026-08-04: Initial documentation — what it is, label-only indexing vs.
  full-text, required shipping agents (Promtail/Alloy/Fluent Bit),
  deployment pattern alongside kube-prometheus-stack.
- 2026-08-04: Linked the consolidated `observability-on-eks.md` overview
  and its Loki-vs-ELK/EFK comparison table.
