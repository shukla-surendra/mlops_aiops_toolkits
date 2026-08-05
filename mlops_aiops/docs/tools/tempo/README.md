# Tempo

**Category:** observability / monitoring (tracing)

## What it is

Grafana Labs' distributed tracing backend — stores and queries traces received from an
[OpenTelemetry](../opentelemetry/README.md) Collector (or Jaeger/Zipkin protocols
directly). Pairs naturally with [Grafana](../grafana/README.md) — same team, same UI as
[Prometheus](../prometheus/README.md) (metrics) and [Loki](../loki/README.md) (logs),
which is exactly what "the LGTM stack" (Loki, Grafana, Tempo, Mimir/Prometheus) refers to.

## What it's used for on EKS

Receives spans from an OTel Collector running as a Deployment or sidecar, stores them, and
serves trace-lookup queries from Grafana — typically "jump from a slow request in a
dashboard straight to its full trace" as the actual workflow this enables.

**Durability**: like Loki, Tempo is designed around **S3/object storage** as its trace
block store from the start — not an afterthought, the same design philosophy Loki uses for
logs.

## Alternatives

- **Jaeger** — older, CNCF-graduated, still widely used, has its own dedicated UI rather
  than living inside Grafana; see [Jaeger](../jaeger/README.md).
- **Vendor-hosted tracing** (Datadog APM, New Relic distributed tracing) — no self-hosted
  backend to run at all, at commercial SaaS cost.

## Related

- [OpenTelemetry](../opentelemetry/README.md) — the instrumentation/collection layer
  feeding Tempo.
- [Grafana](../grafana/README.md), [Prometheus](../prometheus/README.md),
  [Loki](../loki/README.md) — the rest of the "LGTM stack."
- [`observability-on-eks.md`](../../observability-on-eks.md) — full integration-flow
  diagram.
