# GCP Track

Planned. The GCP deep-dive starts after the AWS **and Azure** tracks establish the core mental models (networking, IAM, storage, compute), so we can teach GCP largely by **contrast** — VPC vs GCP VPC (global!), IAM vs GCP IAM (resource hierarchy), S3 vs GCS, EC2 vs GCE, etc. Azure was inserted ahead of GCP in the sequence on 2026-08-08 because Microsoft (Phase 1) is more time-urgent than Google (Phase 3) per `private_profile`'s dated plan — see `PROGRESS.md`'s Changelog for the full reasoning.

Structure will mirror `aws/`:

```
gcp/
├── docs/<service>/{architecture,internals,networking,security,best-practices,troubleshooting,interview}.md
├── quizzes/<service>/
├── terraform/  cdk/  labs/  ...
```

See [../PROGRESS.md](../PROGRESS.md) for the master plan and current position.
