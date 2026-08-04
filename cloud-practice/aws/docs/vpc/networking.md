# VPC — Module 2: Deep packet flow, routing, and the core components

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Epistemics:** **[Documented]** = AWS docs / re:Invent / whitepapers · **[Inferred]** = reconstruction from behavior + standard designs.
> **Prereq:** [architecture.md](architecture.md) (the two-networks / overlay model). Everything below is the *overlay's* routing logic sitting on top of the substrate + Mapping Service from M1.

**Scope:** spec section 4. The building blocks (CIDR, subnets, route tables, ENIs, gateways) and then the *packet flow* for every important path: intra-VPC, subnet→internet (IGW), private→internet (NAT), VPC→AWS-service (endpoints), VPC↔VPC (peering / Transit Gateway), plus DNS.

---

## 1. The building blocks (precise definitions)

| Component | What it *actually* is | Mental anchor |
|---|---|---|
| **VPC** | A regional overlay network + a CIDR block (e.g. `10.0.0.0/16`). Spans all AZs in the region. | A virtual routing domain / a virtual datacenter LAN |
| **Subnet** | A slice of the VPC CIDR (e.g. `10.0.1.0/24`) **pinned to exactly one AZ**. A subnet is a *routing + placement boundary*, not a broadcast domain. | A VLAN pinned to one datacenter |
| **Route table** | An ordered-by-longest-prefix set of routes. Associated with subnets. Decides next-hop for a destination. | Linux `ip route` table, per-subnet |
| **ENI (Elastic Network Interface)** | The virtual NIC. Holds private IP(s), MAC, SG memberships. *This* is what attaches to an instance/Lambda/endpoint. | A veth / a NIC you can detach and move |
| **IGW (Internet Gateway)** | A horizontally-scaled, redundant target that does 1:1 NAT (private↔public IP) at the VPC edge. Not a device you size. | The building's border router doing SNAT/DNAT |
| **NAT Gateway** | A managed many:1 SNAT device in a subnet, for private instances to *egress* to the internet. | A Linux `MASQUERADE` box, managed + HA per-AZ |
| **VPC Endpoint** | A private door to AWS services without traversing the internet. Two kinds: **Gateway** (S3/DynamoDB, via route table) and **Interface** (an ENrelay via PrivateLink). | A private service mesh sidecar to AWS APIs |

### CIDR & the 5 reserved IPs [Documented]
In every subnet, AWS reserves **5 addresses**. For `10.0.1.0/24`:
- `.0` — network address
- `.1` — the **VPC router** (implicit; the default gateway for every instance)
- `.2` — the **DNS server** (the "Amazon-provided DNS" / Route 53 Resolver, at base+2)
- `.3` — reserved for future use
- `.255` — broadcast (VPC doesn't support broadcast, but it's reserved)

So a `/24` gives 251 usable IPs, not 256. This matters for capacity math (a `/28`, the minimum, gives just 11 usable). The `.1` router being *implicit* is important: there is **no real gateway device** — it's the overlay's distributed routing logic. When your instance ARPs for `10.0.1.1`, the Nitro data plane answers.

---

## 2. The single most important routing rule

> Every subnet has **exactly one** route table. Every route table **always** contains the `local` route for the VPC CIDR, and it **cannot be removed or overridden**.

```
Destination        Target       Notes
10.0.0.0/16        local        ← implicit, immutable: all intra-VPC traffic
0.0.0.0/0          igw-xxxx     ← you add this → "public subnet"
```

**"Public subnet" is not a property of the subnet.** It's a subnet whose route table has a default route to an IGW. There is no checkbox that makes a subnet public — it's *entirely* defined by routing. Internalize this; 80% of "why can't my instance reach the internet" bugs are a missing/wrong route.

**Longest-prefix-match wins** (same as any router): a `/32` route beats a `/24` beats `/16` beats `/0`. This is how you surgically steer specific destinations (e.g., send `10.1.2.3/32` to a firewall appliance while everything else goes to the NAT GW).

---

## 3. Packet flow, path by path

### 3a. Intra-VPC, instance → instance (recap from M1)
`10.0.1.5 → 10.0.2.9`. Route table: matches `local` (10.0.0.0/16). Nitro on the source host: anti-spoof → SG egress → **Mapping Service lookup** (virtual→physical host) → encapsulate → substrate → dest host decapsulates → SG ingress → deliver. Cross-subnet within a VPC needs **no gateway** — the `local` route + overlay handle it, even across AZs. NACLs are evaluated at subnet boundaries (M3).

### 3b. Public subnet → internet (via IGW)

```
Instance (10.0.1.5, has public/EIP 52.x.x.x)     Route table (public subnet):
  │  dst 8.8.8.8                                   10.0.0.0/16 → local
  ▼                                                0.0.0.0/0   → igw-xxxx
[overlay router] longest-prefix → 0.0.0.0/0 → IGW
  ▼
[IGW / Blackfoot edge]  1:1 SNAT:  src 10.0.1.5 → 52.x.x.x     (stateless, deterministic)
  ▼
Internet → 8.8.8.8
  ◄── reply to 52.x.x.x → IGW reverse-NAT → 10.0.1.5 → instance
```

Key facts:
- **[Documented] The IGW does the public-IP NAT.** The instance OS only ever has `10.0.1.5`. The IGW performs a **1:1 stateless** translation between the private IP and its associated public/Elastic IP. (Contrast NAT GW, which is *stateful many:1*.)
- **Three conditions for an instance to be internet-reachable:** (1) a public IP or EIP, (2) subnet route `0.0.0.0/0 → igw`, (3) SG + NACL allow. Miss any one → no connectivity. This triple is the canonical debugging checklist.
- The IGW is **not a bottleneck you manage** — it's horizontally scaled and free; you pay only for data transfer.

### 3c. Private subnet → internet (via NAT Gateway)

Private instances have **no public IP** and their subnet route sends `0.0.0.0/0` to a **NAT Gateway** that lives in a *public* subnet.

```
Private instance 10.0.11.5           Private RT:  0.0.0.0/0 → nat-xxxx
  │  dst 8.8.8.8                                  10.0.0.0/16 → local
  ▼ (local? no → nat)
NAT Gateway (in public subnet 10.0.1.0/24, has EIP 52.x.x.x)
   stateful SNAT: src 10.0.11.5:44321 → 52.x.x.x:52000   (records in conntrack table)
  ▼
Public RT: 0.0.0.0/0 → igw  →  IGW 1:1 NAT (NATGW private→its EIP) → internet
  ◄── replies come back to the EIP, NAT GW reverses both translations
```

Why two hops (NAT GW *then* IGW)? Because the NAT GW itself sits in a public subnet and reaches the internet through the IGW like any other host. The NAT GW's job is **egress-only** address hiding for the private tier; inbound-initiated connections to private instances are impossible through it.

Critical design + cost points:
- **[Documented] NAT Gateway is per-AZ.** For HA you deploy **one NAT GW per AZ** and point each AZ's private route table at *its own* AZ's NAT GW. A single NAT GW is a single-AZ failure domain — if that AZ dies, all private egress dies.
- **The #1 hidden AWS cost.** NAT GW charges hourly **plus per-GB processed**. Cross-AZ traffic through a NAT GW in another AZ is billed *twice* (data processing + cross-AZ transfer). Chatty private→S3 traffic through a NAT GW is a classic six-figure bill — fix with a **Gateway Endpoint** (§3d).
- **NAT instance** (the old DIY way): a plain EC2 with `iptables MASQUERADE` and source/dest-check disabled. Cheaper at tiny scale, but you own HA, patching, and it's a throughput bottleneck. NAT GW replaced it for nearly all cases.

### 3d. VPC → AWS service (VPC Endpoints)

Without an endpoint, an instance talking to S3/DynamoDB/etc. goes out via IGW/NAT over the *public* AWS network (still encrypted, but leaves your VPC and costs NAT $). Endpoints keep it on the AWS private network.

**Gateway Endpoint** (S3, DynamoDB only) — [Documented]
- Implemented purely as a **route table entry** with a *prefix list* target (e.g. `pl-xxxx` → `vpce-xxxx`).
- Zero ENIs, **no hourly cost**, no data cost. It just makes the route table send S3-bound traffic to the endpoint instead of the NAT GW.
- The instance still uses the public S3 DNS name; the route diverts the traffic privately.

```
Private RT with a Gateway Endpoint for S3:
  10.0.0.0/16          local
  0.0.0.0/0            nat-xxxx
  pl-63a5400a (S3)     vpce-xxxx     ← S3 traffic bypasses NAT entirely (free)
```

**Interface Endpoint** (most other services: SNS, SQS, KMS, EC2 API, Kinesis, private APIs…) — [Documented], built on **PrivateLink**
- Creates an **ENI with a private IP in your subnet**. AWS gives you a private DNS name that resolves to that ENI.
- Traffic to the service goes to the local ENI → across PrivateLink → a **Network Load Balancer fronting the service** in AWS's account. [NLB/Hyperplane fronting is Documented for PrivateLink.]
- Costs **per-hour per-AZ + per-GB**. Still usually cheaper and more secure than NAT-ing to public endpoints, and it works from fully private (no-internet) VPCs.

**PrivateLink** is the same machinery you use to expose *your own* service to another VPC/account privately: you put an NLB in front, create an endpoint service, and consumers create interface endpoints. No peering, no route overlap concerns, unidirectional. Internally it rides **AWS Hyperplane** — a massive distributed, stateful NAT/load-balancing fabric that also powers NAT GW and NLB. [Documented that Hyperplane underpins these.]

### 3e. VPC ↔ VPC

**VPC Peering** [Documented]
- A 1:1 connection; the two VPCs' overlays are stitched so `local`-like routing works across them.
- You add routes on **both** sides pointing the *other* VPC's CIDR at the peering connection (`pcx-xxxx`).
- **CIDRs must not overlap.** Peering is **non-transitive**: A–B and B–C does *not* give A–C. This is deliberate (prevents accidental transit) and is why large orgs outgrow peering.
- Traffic stays on the AWS backbone (no internet), and there's **no bandwidth bottleneck device** — it's just overlay routing. Cross-AZ/region data charges apply.

```
VPC-A 10.0.0.0/16                 VPC-B 10.1.0.0/16
  RT: 10.1.0.0/16 → pcx-123         RT: 10.0.0.0/16 → pcx-123
        └────────── pcx-123 (peering) ──────────┘
  (A↔C needs its OWN peering — B does NOT relay)
```

**Transit Gateway (TGW)** [Documented] — the hub-and-spoke fix for peering's N² mesh
- A regional **cloud router**: attach many VPCs (and VPNs, Direct Connect) to one TGW; it routes between them via **TGW route tables**.
- Solves transitivity and the O(N²) peering explosion — N VPCs need N attachments, not N² peerings.
- Supports **segmentation** via multiple TGW route tables (e.g., prod attachments can't route to dev). Cross-region peering of TGWs enables global backbones.
- Costs per-attachment-hour + per-GB. It *is* a managed, scaled device (built on Hyperplane-class infra) — think of it as your org's core router in the cloud.

```
        ┌──────── Transit Gateway (regional router) ────────┐
        │   TGW route table(s) decide inter-attachment paths │
        └───┬───────────┬───────────┬───────────┬───────────┘
         VPC-A       VPC-B       VPC-C     VPN / Direct Connect
   Any-to-any (subject to TGW route tables) — transitive, segmentable
```

---

## 4. DNS inside a VPC [Documented]

- Two VPC attributes gate everything: **`enableDnsSupport`** (turns on the resolver at base+2) and **`enableDnsHostnames`** (gives instances public DNS names). Private hosted zones and endpoint private DNS **require both = true** — a very common gotcha.
- The **Route 53 Resolver** lives at **VPC base +2** (e.g., `10.0.0.0/16` → `10.0.0.2`) and also at the link-local `169.254.169.253`. It resolves public names, the VPC's internal names, private hosted zones, and endpoint private DNS.
- **Route 53 Resolver Endpoints** (inbound/outbound) bridge DNS with on-prem for hybrid: outbound forwards specific domains to your data-center DNS; inbound lets on-prem resolve your private zones.
- `169.254.169.254` is the **Instance Metadata Service** (IMDS) — *not* DNS, but the other famous link-local address. (IMDSv2 / SSRF hardening lives in the security module.)

---

## 5. Putting it together: the canonical 3-tier VPC

This is the shape the Terraform in [`../../terraform/vpc/`](../../terraform/vpc/) builds.

```
VPC 10.0.0.0/16  (2 AZs shown; extend to 3 for prod)
┌───────────────────────────── AZ-a ─────────────┬───────────── AZ-b ──────────────┐
│ Public   10.0.0.0/24   [NAT-GW-a, ALB node]     │ Public   10.0.1.0/24  [NAT-GW-b] │
│    RT: 0.0.0.0/0 → IGW                           │    RT: 0.0.0.0/0 → IGW           │
│ App(priv) 10.0.10.0/24 [app instances]          │ App(priv) 10.0.11.0/24           │
│    RT: 0.0.0.0/0 → NAT-GW-a ; S3 → gw-endpoint   │    RT: 0.0.0.0/0 → NAT-GW-b      │
│ Data(priv)10.0.20.0/24 [RDS]                     │ Data(priv)10.0.21.0/24 [RDS-standby]
│    RT: 10.0.0.0/16 local only (no egress)        │    RT: local only                │
└─────────────────────────────────────────────────┴──────────────────────────────────┘
                         │IGW│  ← internet          gw-endpoint → S3 (free, private)
```

Design rationale you should be able to defend:
- **3 tiers** = blast-radius + least-privilege segmentation (web/app/data).
- **NAT GW per-AZ** = no cross-AZ egress $ and no single-AZ egress outage.
- **Data tier has no `0.0.0.0/0` route at all** = it physically cannot reach or be reached from the internet.
- **Gateway Endpoint for S3** = keep backups/artifacts off the NAT bill.
- Spread every tier across **≥2 AZs** = survive an AZ loss.

---

## Sources
- AWS docs: *VPC route tables*, *NAT gateways*, *VPC endpoints*, *Transit Gateway*, *DNS attributes for your VPC*.
- re:Invent: *"AWS PrivateLink & Hyperplane"* deep dives; *Transit Gateway* sessions.
- Blog: "Building a scalable and secure multi-VPC AWS network infrastructure" (AWS whitepaper).

---

## Gate (M2)
See [`../../quizzes/vpc/module-2-gate.md`](../../quizzes/vpc/module-2-gate.md) — clear it before M3 (Security Groups vs NACLs internals, ENI, Flow Logs).
