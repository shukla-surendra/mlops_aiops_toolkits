# VPC — Interview preparation

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> Spec section 15. Questions grouped by level, each with the *answer an interviewer wants*. Practice saying these out loud — the goal is to sound like you've operated this, not memorized it.

---

## Junior / foundational

**Q. Public vs private subnet?**
A. Not a property of the subnet — it's routing. A subnet is "public" iff its route table has `0.0.0.0/0 → IGW`. Private = default route to a NAT GW (egress only) or no default route at all.

**Q. Security Group vs NACL?**
A. SG = stateful, per-ENI, allow-only, can reference other SGs — your primary tool. NACL = stateless, per-subnet, ordered allow+deny, must open ephemeral ports for returns — a coarse guardrail. Lead with SGs.

**Q. What are the 3 conditions for an instance to be internet-reachable?**
A. Public IP/EIP, a route to an IGW, and SG+NACL allowing the traffic. Miss any one → no connectivity.

**Q. Why 5 reserved IPs per subnet?**
A. Network, VPC router (base+1), Amazon DNS (base+2), a reserved (+3), broadcast (last). So a /24 = 251 usable.

## Senior

**Q. Walk a packet from one instance to another in the same VPC.**
A. Overlay/substrate model: source Nitro card does anti-spoof → SG egress → Mapping Service lookup (virtual→physical host) → encapsulate (outer = physical host IPs) → substrate → dest Nitro decapsulates → SG ingress → deliver. No gateway needed for `local`; works across AZs (substrate carries it, and it's billed cross-AZ).

**Q. How does VPC isolate millions of tenants on shared hardware?**
A. It's a software-defined overlay: virtual packets encapsulated over the physical substrate; a Mapping Service holds authoritative virtual→physical + ownership; the Nitro data plane enforces anti-spoofing so you can't impersonate or sniff neighbors. Isolation is by encapsulation + ownership + hardware root of trust, not physical separation.

**Q. Why don't Security Groups have a throughput cost or a central bottleneck?**
A. They're a distributed stateful firewall enforced per-ENI on each host's Nitro card — enforcement scales linearly with the fleet because it's co-located with every workload.

**Q. Gateway vs Interface endpoint?**
A. Gateway (S3, DynamoDB) = a route-table prefix-list entry, no ENI, free. Interface (everything else) = an ENI in your subnet via PrivateLink (NLB/Hyperplane fronting the service), costs per-AZ-hour + per-GB. Both keep traffic off the public internet.

## Principal / architecture

**Q. Design a multi-AZ, multi-account production network for a regulated workload.**
A. Per-app VPCs (blast radius) on non-overlapping CIDRs (IPAM-planned); central Transit Gateway hub with segmented route tables (prod≠dev); centralized egress VPC with NAT + AWS Network Firewall; 3-tier subnets (public LB / private app / sealed data with no `0.0.0.0/0`); endpoints for AWS services + endpoint policies + `aws:SourceVpc` for a data perimeter; Flow Logs + GuardDuty + DNS Firewall; Direct Connect + VPN for on-prem; SCP guardrails (no IGW in workload accounts); everything IaC + PR-reviewed.

**Q. Peering vs Transit Gateway — when and why?**
A. Peering: 1:1, non-transitive, cheapest data transfer, fine for a few VPCs. TGW: hub-and-spoke, transitive, segmentable, scales past the O(N²) peering mesh, supports VPN/DX attachment — at a per-attachment + per-GB cost. Cross the line around ~a handful of VPCs or when you need transitivity/hybrid/segmentation.

**Q. Is intra-VPC traffic encrypted?**
A. Often yes at the substrate: many Nitro instance types encrypt inter-instance traffic within a Region, and inter-AZ/Region backbone traffic is encrypted. But you still terminate TLS for app-layer guarantees/compliance — substrate encryption isn't per-flow configurable/attestable.

## Scenario

**Q. "We peered VPC-A↔B and B↔C; A still can't reach C. Why?"**
A. Peering is non-transitive and needs routes on both sides of each connection; B doesn't relay A↔C. Add a direct A↔C peering, or move to a TGW hub.

**Q. "Our NAT Gateway bill exploded."**
A. Chatty egress through NAT — usually bulk S3/ECR traffic. Add an S3/DynamoDB **gateway endpoint** (free) and interface endpoints for other services; check for a NAT GW in the wrong AZ (double charge); consider IPv6 + egress-only IGW. Confirm with CUR `NatGateway-Bytes`.

**Q. "Design private access to a partner's API without exposing either network."**
A. PrivateLink: partner puts an NLB behind an endpoint service; we create an interface endpoint. Unidirectional, no CIDR overlap concerns, no peering — the partner never routes into our VPC.

## Production incident

**Q. "At 3am, new connections start failing intermittently on healthy, low-CPU instances behind a NAT GW. Diagnose."**
A. Two prime suspects: **NAT SNAT port exhaustion** (`ErrorPortAllocation` — too many flows to the same dst IP:port; fix with more distinct destinations/NAT GWs or connection reuse) and **conntrack/bandwidth allowance** on the instance (`conntrack_allowance_exceeded` / `bw_*_allowance_exceeded` — fix with bigger instances, NLB, fewer tracked flows). Confirm via CloudWatch metrics + Flow Logs, not guesswork.

**Q. "A subnet's route change 'didn't take.'"**
A. Likely edited the wrong route table — the subnet was using the VPC's **main** route table, not the one you changed (no explicit association). Associate the subnet to the intended RT.

**Q. "Security review found an instance can reach the internet that shouldn't."**
A. Run **Network Access Analyzer** to enumerate internet-reachable paths; likely a stray `0.0.0.0/0→NAT/IGW` route or a wide SG. Remediate route/SG; add a Config rule + EventBridge auto-alert to prevent recurrence.

---

## Rapid-fire (know cold)
- ENI holds the IP/MAC/SGs and is movable; the instance just attaches ENIs.
- SGs stateful (allow-only), NACLs stateless (allow+deny, ephemeral ports).
- `local` route is immutable; longest-prefix-match wins.
- Public IP lives on the IGW (1:1 NAT), never in the guest OS.
- NAT GW is per-AZ, egress-only, hourly + per-GB — the top hidden cost.
- Mapping Service = virtual→physical directory; Hyperplane = stateful NAT/LB fabric (NAT GW, NLB, PrivateLink, EFS).
- Peering non-transitive; TGW transitive + segmentable.
- Reachability Analyzer proves a path; Flow Logs show if packets arrived (metadata only).

---

## Self-check
Pick any 3 "Principal/scenario/incident" questions above and answer them out loud in under 90 seconds each, without reading. If you stall, that's the doc section to re-read.
