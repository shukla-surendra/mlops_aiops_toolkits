# VPC — Security: Security Groups, NACLs, Flow Logs, IAM & threat models

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Epistemics:** **[Documented]** / **[Inferred]** as elsewhere.
> **Prereq:** [architecture.md](architecture.md), [networking.md](networking.md), [internals.md](internals.md).

Spec section 6. Network security in a VPC is **defense in depth**: identity (IAM) decides who can *change* the network; Security Groups + NACLs decide what packets *flow*; encryption + endpoint policies decide what data can *leave*; Flow Logs + GuardDuty give you *visibility*.

---

## 1. Security Groups (SGs) — the stateful, per-ENI firewall

[Documented]
- **Attached to ENIs** (M1/internals). Enforced in the Nitro data plane, co-located with each workload → scales linearly, no central bottleneck.
- **Stateful:** if you allow an inbound flow, the return traffic is automatically allowed (and vice versa). A per-ENI **connection-tracking table** remembers established flows. You almost never need matching egress rules for replies.
- **Allow-only:** SG rules can only *permit*. There is **no deny rule**. "Blocking" something = not having an allow that matches. Evaluation is the logical OR of all rules across all SGs on the ENI — if *any* rule allows it, it's allowed.
- **Rules reference:** a CIDR, another **Security Group ID** (the idiom — "allow from the app SG"), a **prefix list**, or IPv6. Referencing SGs auto-tracks membership as instances scale (see the Terraform `referenced_security_group_id` example).
- **Default SG:** every VPC has one; its default rules allow all traffic *from members of the same SG* and all egress. Many orgs delete those defaults and never use the default SG.
- **Default egress:** a new custom SG allows **all egress** until you change it; ingress is empty (deny-by-absence).

### Connection tracking nuance [Documented]
Tracked flows consume entries in the conntrack table; there are per-ENI limits (large but finite). AWS has an **untracked-connection optimization**: if a flow is allowed by a rule that is effectively "all traffic" in *both* directions (e.g. `0.0.0.0/0`), it may be handled *without* a tracking entry — which both saves state and means such flows aren't torn down when rules change. Practical impact: very high-connection workloads can hit tracking limits (`conntrack` exhaustion) → symptoms like dropped new connections; mitigations include tuning, more/bigger instances, or NLB.

---

## 2. Network ACLs (NACLs) — the stateless, subnet-level filter

[Documented]
- **Attached to subnets** (every subnet has exactly one NACL; the default allows all in/out).
- **Stateless:** return traffic is **not** automatically allowed. You must add explicit rules for **ephemeral ports** (typically 1024–65535) in the reverse direction. This is the #1 NACL footgun.
- **Ordered, numbered rules** evaluated low→high; first match wins; supports **explicit DENY** (unlike SGs). There's a final `*` implicit deny.
- Applies to *all* traffic crossing the subnet boundary, regardless of instance/ENI.

### SG vs NACL

| | Security Group | NACL |
|---|---|---|
| Attaches to | ENI | Subnet |
| State | **Stateful** (returns auto-allowed) | **Stateless** (must allow ephemerals) |
| Rules | Allow only | Allow **and** Deny |
| Evaluation | All rules OR'd (any allow → allow) | Numbered, first match wins |
| Reference by SG ID | Yes | No (CIDR only) |
| Typical use | Primary control — per-workload least privilege | Coarse subnet guardrail / explicit IP denylist |

**Design guidance:** make **SGs your primary tool** (expressive, stateful, SG-referencing). Use **NACLs sparingly** — as a blunt subnet-wide guardrail (e.g., deny a known-bad CIDR, or hard-isolate a sensitive subnet). Trying to do fine-grained policy in NACLs leads to ephemeral-port pain and rule sprawl.

---

## 3. VPC Flow Logs — your packet-level visibility (metadata)

[Documented]
- Capture **metadata about IP flows** (not payloads): src/dst IP+port, protocol, packets, bytes, start/end, **action (ACCEPT/REJECT)**, and (v3+) fields like `flow-direction`, `pkt-srcaddr`/`pkt-dstaddr` (crucial behind NAT/endpoints), `tcp-flags`, `az-id`, `subnet-id`, `instance-id`, `vpc-id`.
- **Scope:** enable at **VPC**, **subnet**, or **ENI** level. VPC-level = everything in it.
- **Destinations:** CloudWatch Logs, S3, or Kinesis Data Firehose. Query with CloudWatch Logs Insights or Athena (S3).
- **Custom format:** pick only the fields you need (cost + signal).

### What Flow Logs do NOT show [Documented]
- No packet payloads (use **Traffic Mirroring** for that).
- Some traffic is **not logged**: to/from the Amazon DNS server (base+2), Windows license activation, `169.254.169.254` (IMDS) and `169.254.169.253`, DHCP, and traffic to the VPC router reserved IPs. Knowing these blind spots prevents "why isn't my DNS/metadata traffic in the logs" confusion.
- `REJECT` shows SG/NACL denies for *tracked* directions — asymmetric NACL setups can log confusingly.

### The `pkt-srcaddr` trick
Behind a NAT GW or load balancer, the `srcaddr` is the translated address but `pkt-srcaddr` is the **original** — essential for tracing "who actually initiated this" across NAT/endpoints.

---

## 4. IAM & policy controls for the network (who can change/what can leave)

Network security isn't just packets — it's also *who can modify the network* and *where data can go*:

- **IAM for VPC actions** [Documented]: `ec2:AuthorizeSecurityGroupIngress`, `ec2:CreateRoute`, `ec2:ModifyVpcEndpoint`, etc. Gate these tightly — the ability to add `0.0.0.0/0` to a SG or a route to an IGW is effectively "open the perimeter." Use **resource-level permissions** and **condition keys** (`ec2:Vpc`, `ec2:Region`).
- **VPC Endpoint policies** [Documented]: an IAM resource policy *on the endpoint* restricting which principals/actions/resources can be reached through it. This is a **data-exfiltration control**: e.g., an S3 gateway-endpoint policy that only allows access to *your* buckets stops a compromised instance from `aws s3 cp` to an attacker's bucket.
- **`aws:SourceVpc` / `aws:SourceVpce` condition keys** [Documented]: put on **bucket/resource policies** to require that access arrives *through your endpoint/VPC* — pairs with endpoint policies to build an exfil-resistant perimeter.
- **SCPs (Organizations)** [Documented]: guardrails like "no one can create an IGW" or "no public S3" across all accounts — the account-level backstop above IAM.

---

## 5. Encryption in transit

- **[Documented] Substrate-level encryption:** traffic between many Nitro instance types within a Region is automatically encrypted at the physical layer, and all inter-AZ/inter-Region traffic on the AWS backbone is encrypted. So intra-VPC traffic often already has a layer of encryption independent of your app.
- **You still terminate TLS** for application-layer confidentiality/integrity and to satisfy compliance (mTLS between services, TLS on ALB/NLB, ACM-managed certs). Don't rely solely on substrate encryption for regulated data — it's not something you can attest/configure per-flow.
- **VPN/Direct Connect:** IPsec (VPN) encrypts on-prem↔AWS; Direct Connect is private but **not encrypted by default** → run a VPN over it or use MACsec for encryption.

---

## 6. Threat models (think like an attacker, then defend)

| Threat | Mechanism | Defense |
|---|---|---|
| **SSRF → credential theft** | App fetches attacker URL → hits `169.254.169.254` IMDS → steals role creds | **IMDSv2** (session-token, hop-limit=1), block egress to metadata via app, least-priv roles |
| **Data exfiltration to S3** | Compromised instance `aws s3 cp` to attacker bucket | **S3 gateway-endpoint policy** + `aws:SourceVpc` on buckets + egress restrictions |
| **DNS exfiltration** | Encode data in DNS queries to attacker domain | **Route 53 Resolver DNS Firewall** (block/allow domains), query logging |
| **Lateral movement** | Flat network + wide SGs let a popped host reach the DB | **Tiered subnets + SG-referencing least privilege**; data tier reachable only from app SG |
| **Public exposure** | `0.0.0.0/0` on SSH/RDP/DB ports | No public DB subnets; **SSM Session Manager** instead of bastions/22; Config rules to detect |
| **Peering over-trust** | Peered VPC becomes a trusted blast-radius extension | Minimal routes, SGs still enforce; segment with TGW route tables |
| **Malicious/compromised traffic** | Inbound exploits, C2 beaconing | **AWS Network Firewall** (stateful IPS/domain filtering), **GuardDuty** (VPC flow/DNS anomaly detection) |

### The AWS-managed security services worth knowing [Documented]
- **GuardDuty** — analyzes VPC Flow Logs + DNS logs + CloudTrail for threats (crypto-mining, recon, exfil, IMDS abuse) with no agents.
- **AWS Network Firewall** — managed stateful firewall/IPS in your VPC (Suricata rules, domain filtering) for centralized inspection.
- **Route 53 Resolver DNS Firewall** — domain allow/deny at the resolver.
- **Traffic Mirroring** — copy packets from an ENI to an appliance for deep inspection/forensics.
- **Network Access Analyzer / Reachability Analyzer** — prove/verify what *can* reach what (see [troubleshooting.md](troubleshooting.md)).

---

## 7. Sources
- AWS docs: *Security groups*, *Network ACLs*, *VPC Flow Logs* (records + fields), *Endpoint policies*, *benchmark* condition keys, *Nitro encryption*.
- Whitepaper: *AWS Security Best Practices*, *Nitro Security Design*.
- Blog: *"Establishing a data perimeter on AWS"* (SourceVpc/SourceVpce patterns).

---

## Self-check
1. A teammate wants to "block port 3389 from one bad IP" using a Security Group. Explain why that's impossible with an SG and what you'd use instead.
2. You added an inbound NACL rule allowing TCP 443 but connections still hang. What did you forget, and why does the SG equivalent not need it?
3. Design the two controls (one endpoint-side, one bucket-side) that together stop a compromised instance from copying data to an *external* S3 bucket.
4. What traffic will never appear in VPC Flow Logs, and why does that matter when debugging DNS?
5. Explain IMDSv2's defense against SSRF in terms of what an attacker's forged request can't do.
