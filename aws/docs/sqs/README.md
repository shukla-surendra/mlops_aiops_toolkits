# Amazon SQS — Documentation set

Deep-dive on Simple Queue Service, from first principles to production. Read in order.

## Study order

1. **[architecture.md](architecture.md)** — *Why SQS exists · the "shared inbox tray" mental model · internal architecture* (redundant multi-server storage, CAP trade-off Standard vs FIFO), message lifecycle, delivery semantics, limits, core patterns, security basics, and a decision table vs SNS/Kinesis/EventBridge. **Start here.**
2. **[monitoring-alarms.md](monitoring-alarms.md)** — every CloudWatch metric SQS publishes, every CloudWatch alarm parameter explained in plain English, DLQ alarm patterns, and CLI/Terraform alarm examples.

## Not yet written
- `security.md`, `best-practices.md`, `troubleshooting.md`, `interview.md` — see architecture.md's "Not yet covered" section.
- Terraform module, boto3 scripts, hands-on labs.

---
*Convention:* claims tagged **[Documented]** (AWS docs / re:Invent / patents / papers) or **[Inferred]** (reconstruction from behavior). Hold Inferred loosely.
