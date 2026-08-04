# VPC — Best practices, production architectures, cost & monitoring

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md), [networking.md](networking.md), [security.md](security.md).

Spec sections 8, 9, 10, 11. This is the "what do real teams actually do" file — design decisions, anti-patterns, the cost traps, and how to watch it in production.

---

## 1. CIDR & IP planning (the decision you can't easily undo)

- **Plan the whole org's address space first.** Overlapping CIDRs are the thing that later blocks peering/TGW/hybrid. Carve non-overlapping ranges per environment/region/account *before* you build. Use **AWS IPAM** to allocate and prevent overlap at scale. [Documented]
- **Size generously but not absurdly.** A `/16` per VPC is common; leave room for more subnets/AZs. Remember the **5 reserved IPs per subnet** and that you can't resize a subnet — only add new ones (or a **secondary CIDR** to the VPC). [Documented]
- **Reserve space for growth**: extra AZs, extra tiers, future EKS pod density (each pod eats a VPC IP with the default CNI — size app subnets accordingly, or use IPv6/prefix delegation).
- **IPv6**: dual-stack removes NAT for egress (IPv6 uses an **egress-only IGW**, which is free vs NAT GW) — a real cost/scale lever. [Documented]

## 2. Subnet & AZ strategy

- **≥2 AZs always; 3 for prod / quorum systems.** A subnet is single-AZ; spread every tier across AZs so an AZ loss is survivable.
- **Tier by trust**: public (LB/NAT only) → app (no public IPs) → data (no `0.0.0.0/0` route at all). Keep data tiers sealed; give them AWS access via endpoints, not NAT.
- **Right-size subnets per tier**: big app subnets (pod density), smaller public subnets (just LBs/NAT).

## 3. Multi-account / landing-zone networking (how big orgs really run)

- **Per-account/per-app VPCs** (blast-radius isolation) connected via a **central Transit Gateway** hub, rather than a peering mesh. [Documented]
- **Centralized egress**: a shared "egress VPC" with NAT + AWS Network Firewall that spoke VPCs route through — one place to inspect/filter/pay-for-NAT instead of N. Tradeoff: cross-AZ/TGW data charges vs. consolidated control + fewer NAT GWs.
- **Centralized ingress/inspection**: shared inspection VPC for east-west and north-south filtering.
- **Shared VPC (RAM)**: alternatively, share subnets from one account into many via Resource Access Manager — fewer VPCs, central network team owns plumbing.
- **DNS**: central Route 53 Resolver rules + endpoints shared org-wide for hybrid resolution.

## 4. Production architectures by shape (defend the decisions)

| Org type | Pattern & why |
|---|---|
| **High-scale streaming (Netflix-like)** | Many accounts, TGW hub, heavy CloudFront/edge, multi-AZ everything, chaos-tested AZ failover; regional isolation for blast radius. |
| **Ride-share / real-time (Uber-like)** | Low-latency multi-AZ, private service mesh, PrivateLink for internal APIs, tight SG segmentation between microservices. |
| **Bank / regulated** | 3-tier hard segmentation, no internet on data tier, centralized inspection (Network Firewall), full Flow Logs + GuardDuty, Direct Connect to on-prem, encryption everywhere, SCP guardrails (no IGW in workload accounts). |
| **Healthcare (HIPAA)** | PrivateLink/endpoints so PHI never touches the internet, dedicated tenancy where required, strict endpoint policies + `aws:SourceVpc`, audit via Flow Logs/CloudTrail. |
| **E-commerce** | Public ALB → private app (auto-scaled) → private RDS multi-AZ; gateway endpoint for S3 assets; WAF on ALB; NAT per-AZ. |
| **Data platform (Databricks-like)** | Customer-VPC injection, PrivateLink to control plane, endpoints to S3/Kinesis, no public egress from compute, SG-scoped access to metastore. |

## 5. Best-practice checklist

- Private-by-default subnets; public only for LB/NAT.
- **Least-privilege SGs, referenced by SG ID**, never `0.0.0.0/0` on admin ports.
- **No bastions on port 22** — use **SSM Session Manager** (no inbound, IAM-audited, logged).
- **Endpoints for AWS services** (S3/DynamoDB gateway = free; interface for the rest) to cut NAT + keep traffic private.
- **VPC Flow Logs on** (at least at VPC scope) → S3/Athena for cheap retention.
- **DNS Firewall + GuardDuty** enabled.
- **Tag everything** (cost allocation + incident blast-radius).
- **One NAT GW per AZ** in prod; IPv6/egress-only IGW where possible.
- **IaC everything** (Terraform/CDK); no click-ops network changes; PR review on SG/route changes.
- **SCP guardrails** for the dangerous verbs (create IGW, open SGs, disable Flow Logs).

## 6. Anti-patterns (and the fix)

| Anti-pattern | Why it bites | Fix |
|---|---|---|
| One giant flat VPC, no tiers | Lateral movement, no blast-radius control | Tiered subnets + SG segmentation |
| Single AZ | AZ outage = full outage | ≥2 AZs per tier |
| Overlapping CIDRs | Can't peer/TGW/hybrid later | Plan with IPAM up front |
| Public database subnet | One SG slip = internet-exposed DB | Data tier, no `0.0.0.0/0` route |
| Wide-open SGs (`0.0.0.0/0` SSH/DB) | Trivial exposure | Least privilege + SSM |
| NAT per instance / NAT instance at scale | Cost + throughput + HA pain | Managed NAT GW per AZ; endpoints |
| Peering mesh at 20+ VPCs | O(N²) sprawl, non-transitive confusion | Transit Gateway hub |
| Hardcoded IPs in SGs/app config | Breaks on scale/replace | SG references, DNS, service discovery |
| Chatty S3 through NAT | Huge NAT data-processing bill | S3 **gateway endpoint** (free) |

## 7. Cost optimization (where the money actually goes)

VPC itself is free; the **data movement** is what bills. The big ones [Documented]:

1. **NAT Gateway** — hourly **+ per-GB processed**. The classic surprise. Kill it with: **gateway endpoints** for S3/DynamoDB, **interface endpoints** for other services, IPv6 + egress-only IGW, and *not* routing bulk traffic through NAT. Consolidating to one NAT GW saves hourly but adds cross-AZ data charges — model both.
2. **Cross-AZ data transfer** — every byte between AZs is billed *each way*. Keep chatty tiers AZ-local where correctness allows; beware NAT GW in a different AZ (double charge).
3. **Data transfer out to internet** — tiered pricing; use CloudFront to offload + cheapen egress.
4. **Interface endpoints** — per-AZ-hour + per-GB. Usually still cheaper/safer than NAT, but each endpoint × each AZ adds up — consolidate.
5. **Transit Gateway** — per-attachment-hour + per-GB. Centralization has a data-processing cost; weigh vs. peering (peering data transfer is cheaper but doesn't scale operationally).
6. **VPC Flow Logs** — ingestion/storage cost; send to S3 (cheaper than CloudWatch) and select only needed fields.

**Monitor cost:** Cost Explorer + the **Cost and Usage Report (CUR)** filtered by `usageType` (look for `NatGateway-Bytes`, `DataTransfer-Regional-Bytes`) and cost-allocation tags. Set budgets/alarms on data-transfer spend.

## 8. Monitoring & operations (spec §11)

- **CloudWatch metrics**: NAT GW (`BytesOutToDestination`, `ErrorPortAllocation`, `ActiveConnectionCount`), TGW, interface endpoints, per-ENI network metrics (`bw_in/out_allowance_exceeded`, `conntrack_allowance_exceeded` on Nitro) — these tell you when you're hitting instance network/conntrack limits.
- **VPC Flow Logs** → CloudWatch Logs Insights / Athena for traffic analysis, top talkers, REJECT hunting.
- **Reachability Analyzer** — static proof that A can/can't reach B (route + SG + NACL + endpoint aware). **Network Access Analyzer** — find unintended paths (e.g., anything that can reach the internet).
- **AWS Config** — rules like `vpc-flow-logs-enabled`, `restricted-ssh`, `vpc-default-security-group-closed`; drift detection on network resources.
- **CloudTrail** — every network API call (who opened that SG?); pipe to alerts on sensitive verbs.
- **EventBridge** — react to network changes (e.g., alert/auto-remediate when a `0.0.0.0/0` ingress rule is added).
- **GuardDuty** — anomaly detection over flow/DNS/CloudTrail.

---

## Sources
- Whitepapers: *Building a Scalable and Secure Multi-VPC AWS Network Infrastructure*; *AWS Well-Architected — Reliability & Security Pillars*.
- AWS docs: *VPC pricing*, *Data transfer pricing*, *AWS IPAM*, *Centralized egress*, *Config managed rules*.
- Blog: *"Establishing a data perimeter"*, *"Reduce NAT gateway costs with VPC endpoints"*.

---

## Self-check
1. Your monthly bill shows a large `NatGateway-Bytes` line. Walk through the top 3 things you'd check/change, in order of impact.
2. Why does consolidating from per-AZ NAT to a single NAT GW sometimes *increase* cost? Which line item appears?
3. When would you choose a Transit Gateway hub over VPC peering, and what's the cost you accept for that?
4. Give three controls that keep a data tier both unreachable from the internet *and* able to back up to S3.
5. Which CloudWatch metric warns you that an instance is about to drop new connections due to network-state limits?
