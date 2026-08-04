# VPC — Troubleshooting & debugging

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** all prior VPC docs. This is spec section 14 — the systematic diagnosis of "it can't connect."

The golden rule: **connectivity is a chain, and every link must pass.** Debug the chain in order rather than guessing. Most VPC incidents are one of a dozen well-known breaks.

---

## 1. The universal connectivity checklist (memorize this order)

For "A can't reach B," verify each link:

1. **Does the destination even exist / listen?** (process up, listening on the port, health check green)
2. **Route:** does A's subnet route table have a route to B's destination (`local`, IGW, NAT, peering, TGW, endpoint prefix list)? Longest-prefix-match — is a more specific route stealing it?
3. **Return route:** does B's subnet have a route *back* to A? (asymmetric routing is a silent killer, esp. with appliances/peering)
4. **Security Group (stateful):** does B's SG *allow inbound* from A (CIDR or A's SG)? Does A's SG *allow egress* to B (usually yes by default)?
5. **NACL (stateless):** does B's subnet NACL allow inbound on the port AND **outbound on ephemeral ports** for the reply? Same for A in reverse.
6. **Public reachability triple** (if via internet): public IP/EIP + route to IGW + SG/NACL allow — all three.
7. **DNS:** is A even resolving B to the right IP? (`enableDnsSupport`/`Hostnames`, private hosted zone association, endpoint private DNS)
8. **Address translation:** NAT/endpoint doing what you think? Check `pkt-srcaddr` in Flow Logs.

Work top-down; the first failing link is your bug.

---

## 2. Tools, in order of leverage

- **VPC Reachability Analyzer** [Documented] — give it source + destination; it does a **static analysis** across routes, SGs, NACLs, peering, endpoints and tells you *reachable or not, and which component blocks it*. Start here for "can A reach B" — it often answers in seconds without touching the instances.
- **Network Access Analyzer** — find *unintended* paths ("what can reach the internet / the data tier?").
- **VPC Flow Logs** — did the packet arrive? ACCEPT or REJECT, and at which ENI? Use `pkt-srcaddr`/`pkt-dstaddr` to see through NAT. Query with CloudWatch Logs Insights (below).
- **From inside the instance** (via **SSM Session Manager**, no SSH needed): `ip route`, `ip addr`, `ss -tlnp` (is it listening?), `curl -v`, `dig`/`nslookup`, `traceroute`/`mtr`, `tcpdump -ni any port X`, `nc -vz host port`.
- **`curl http://169.254.169.254/latest/meta-data/`** (IMDSv2: get a token first) — confirm identity/role/network from the instance's own view.

### CloudWatch Logs Insights — Flow Log queries
```
# Top REJECTs hitting an ENI (find blocked flows)
fields @timestamp, srcAddr, dstAddr, dstPort, action
| filter action = "REJECT"
| sort @timestamp desc | limit 50

# Who is talking to 10.0.20.5 (a DB) and is it accepted?
fields srcAddr, dstAddr, dstPort, action, bytes
| filter dstAddr = "10.0.20.5"
| stats sum(bytes) as total by srcAddr, action
```

---

## 3. Common failures → diagnosis → fix

| Symptom | Likely cause(s) | Fix |
|---|---|---|
| Instance can't reach internet | Missing public IP; no `0.0.0.0/0`→IGW (public) or →NAT (private); NAT in dead AZ; SG egress; NACL ephemeral | Check the public triple / NAT route + AZ; verify NACL out+in ephemerals |
| Can't SSH/RDP in | SG missing inbound 22/3389 from your IP; NACL ephemeral outbound; instance in private subnet; no route to IGW; wrong key | Prefer **SSM** (removes 90% of this class); else check SG+NACL+route+public IP |
| Reaches by IP, not by name | `enableDnsSupport/Hostnames` off; private hosted zone not associated to VPC; resolver issue; endpoint `private_dns_enabled` off | Flip both VPC DNS attrs; associate PHZ; enable endpoint private DNS |
| VPC peering silent fail | Routes missing on **one** side; overlapping CIDR; expecting **transitivity** (A→C via B); SG referencing across peering not supported cross-Region | Add routes both sides; no overlap; use TGW; use CIDRs not SG refs across peer |
| Interface endpoint not used | `private_dns_enabled` off (app still hits public DNS→NAT); SG on the endpoint ENI blocks 443; wrong subnet/AZ | Enable private DNS; open 443 on endpoint SG from clients |
| Gateway endpoint (S3) not used | Route-table association missing; endpoint policy too strict; wrong Region service name | Associate to the subnet's RT; loosen/scope policy |
| Intermittent egress drops at scale | **NAT GW SNAT port exhaustion** (~55k per unique dest) → `ErrorPortAllocation` metric | Spread destinations, more NAT GWs, or many distinct dst IPs; cache/reuse connections |
| New connections dropped, CPU fine | **Conntrack exhaustion** (`conntrack_allowance_exceeded`) or bandwidth allowance (`bw_*_allowance_exceeded`) | Bigger instance, fewer tracked flows, NLB, untracked-flow patterns |
| Large transfers hang, small OK | **MTU / PMTUD**: jumbo (9001) inside VPC but path drops; ICMP "frag needed" blocked by SG/NACL | Allow ICMP type 3 code 4; set MTU 1500 for internet paths |
| Appliance (firewall/NAT instance) drops transit | **source/dest check still enabled** on its ENI | Disable source/dest check |
| Hybrid route not working | BGP not propagating; static vs propagated precedence; overlapping on-prem CIDR | Enable route propagation; check TGW/VGW route tables |

---

## 4. IAM / API-side debugging

- "AccessDenied creating route/SG rule" → check the IAM policy for `ec2:CreateRoute`, `ec2:AuthorizeSecurityGroupIngress`, and any **condition keys** (`ec2:Vpc`, region) or **SCPs** blocking it. CloudTrail shows the exact denied call + which policy.
- "My change didn't take effect" → confirm you edited the **route table associated with that subnet** (a subnet uses the main RT if not explicitly associated — a very common trap).

---

## 5. A worked example (the muscle memory)

*"App in private subnet can't reach RDS in data subnet."*
1. Reachability Analyzer: source = app ENI, dest = RDS ENI:5432 → says "blocked by security group."
2. Confirm: RDS SG inbound must allow 5432 **from the app SG** (not a CIDR that doesn't match). It was allowing from the *public* subnet CIDR, but the app moved subnets. Fix: reference the app SG.
3. Validate: from the app box via SSM, `nc -vz rds-endpoint 5432` → connects. `dig rds-endpoint` returns the private IP (confirms DNS + PHZ). Done.

---

## Sources
- AWS docs: *Reachability Analyzer*, *Network Access Analyzer*, *Flow Logs records*, *NAT gateway troubleshooting* (`ErrorPortAllocation`), *Nitro network performance* (allowance metrics), *Systems Manager Session Manager*.

---

## Self-check
1. Give the connectivity chain in order. Which link is the "silent killer" when using firewall appliances, and why?
2. An instance reaches `1.1.1.1` by IP but `curl https://example.com` fails. Where do you look first?
3. NAT egress works for hours then throws intermittent failures under load; CPU is idle. Which metric confirms the cause and what are two fixes?
4. Why does editing a route table sometimes have "no effect," and what's the subnet-association gotcha?
5. Reachability Analyzer says "reachable" but the app still times out. What classes of problem does that tool *not* cover?
