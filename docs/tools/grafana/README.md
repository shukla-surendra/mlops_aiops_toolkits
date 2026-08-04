# Grafana

**Category:** observability / monitoring (Kubernetes/EKS)
**First documented:** 2026-08-04

## What it is

Visualization/dashboarding layer only — it stores no data itself. You
point it at data sources and build dashboards/alerts on top of whatever
they return.

## What it's used for on EKS

Queries [Prometheus](../prometheus/README.md) for metrics and
[Loki](../loki/README.md) for logs (and often Tempo for traces), giving one
UI across metrics + logs for an EKS cluster instead of separate tools per
signal type.

## Deployment

Comes bundled in the **`kube-prometheus-stack`** Helm chart alongside
Prometheus, Alertmanager, node-exporter, and kube-state-metrics — so a
single Helm install typically gets you Grafana pre-wired to Prometheus.
Loki is usually added as a second data source afterward.

## Alternatives / managed options

- **Amazon Managed Grafana (AMG)** — AWS-managed Grafana; can point at
  Amazon Managed Service for Prometheus (AMP) and/or CloudWatch, so you're
  not operating the Grafana server yourself.
- **CloudWatch dashboards / Container Insights** — AWS-native alternative
  if you want to avoid running a separate visualization layer entirely, at
  the cost of flexibility/portability compared to Grafana.

## Related

Part of the metrics/logs/visualization trio commonly run together on EKS
— see [Prometheus](../prometheus/README.md) for the "LGTM stack" naming
context (Loki, Grafana, Tempo, Mimir/Prometheus).

## Change log

- 2026-08-04: Initial documentation — what it is, role as pure
  visualization layer, kube-prometheus-stack bundling, AMG/CloudWatch
  alternatives.
