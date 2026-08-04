# VPC — Internals: ENIs, the Mapping Service, Hyperplane, Nitro & the algorithms

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Epistemics:** **[Documented]** = AWS docs / re:Invent / patents / whitepapers · **[Inferred]** = reconstruction from behavior + standard distributed-systems designs. AWS does not open-source the VPC data plane; treat Inferred parts as "how a senior engineer would build this," useful for reasoning, not gospel.
> **Prereq:** [architecture.md](architecture.md) (overlay/substrate, control vs data plane) and [networking.md](networking.md) (routing, gateways).

This is the "how AWS built it" file — spec sections 3 and 17. If M1 gave you the *model* and M2 the *routing*, this gives you the *machinery*.

---

## 1. The ENI (Elastic Network Interface) — the real atom

Everyone says "the instance has an IP." Wrong altitude. **The ENI has the IP; the instance has ENIs.** The ENI is the first-class, movable networking object; instances, Lambdas, RDS, NAT GWs, interface endpoints, ECS tasks — all get their network identity by having an ENI.

An ENI holds [Documented]:
- One **primary private IPv4** + optional **secondary private IPs** (all within the subnet CIDR).
- Optional IPv6 addresses.
- One **MAC address** (stable for the life of the ENI).
- **Security Group** memberships (SGs attach to ENIs, *not* to instances or subnets — an instance with 2 ENIs can be in different SGs per interface).
- A **source/destination check** flag (must be *disabled* to let an instance act as a router/NAT/firewall appliance — because anti-spoofing would otherwise drop transit traffic).
- An **attachment** to exactly one instance (or service) at a time, in exactly one subnet/AZ.

### Why "movable" matters
Because the ENI is detachable, its **IP + MAC + SGs move as a unit**. Classic use: a "floating" secondary ENI you detach from a failed instance and attach to a standby — the IP follows, no DNS change. This is the primitive behind many HA patterns and behind how AWS services keep stable IPs while the compute behind them is replaced.

### IP density & ENI limits [Documented]
- Max ENIs per instance and IPs per ENI are **instance-type dependent** (bigger instances → more ENIs, more IPs). This sets your **pod density** on EKS: with the default VPC CNI, each pod gets a real VPC IP from a secondary IP on an ENI, so `max_pods ≈ (ENIs × (IPs_per_ENI − 1))`. Running out of IPs is a real EKS scaling wall → mitigations: prefix delegation (assign /28 prefixes per ENI), custom networking, or IPv6.
- **Trunk/branch ENIs** power ECS `awsvpc` mode and EKS security-groups-for-pods: a "trunk" ENI multiplexes many "branch" ENIs so each task/pod gets its own ENI + SGs without exhausting instance ENI slots. [Documented]

### How the ENI appears inside the guest [Documented]
On Nitro instances the ENI is surfaced as an **ENA (Elastic Network Adapter)** — a PCIe device with its own driver. The guest sees a normal NIC (`eth0`, `ens5`). The ENA driver talks to the **Nitro card**, which is where the overlay encap/decap, SG enforcement, and anti-spoofing actually run (M1 §3c). So: guest NIC → ENA → Nitro card → substrate. The guest never sees the overlay headers.

---

## 2. The Mapping Service — a giant distributed directory

Recall the crux from M1: something must translate **virtual IP → physical host** for every destination. That's the Mapping Service. Going deeper [Documented that it exists + is the core; internal structure Inferred]:

### What it stores
Key → value roughly: `(vpc_id, virtual_ip) → (physical_host_ip, encap_context, owner, security_metadata)`. It's the authoritative source of *where everything is* and *who owns it*.

### How it's built (Inferred, standard design)
- A **partitioned, replicated key-value store** — think a DynamoDB-class system: data sharded across many nodes by key (**consistent hashing** so adding capacity doesn't reshuffle everything), each shard replicated for durability, writes acknowledged by a **quorum** of replicas.
- **Regional, multi-AZ**: replicas across AZs so an AZ loss doesn't lose the directory.
- **Reads dominate massively** (every cache-miss packet is a read; writes only on launch/stop/migrate/config-change). So the design optimizes for read scale: heavy caching + replicas.

### Consistency model [Inferred]
- Authoritative store is kept strongly consistent enough that ownership is never ambiguous (you can't have two tenants think they own the same virtual IP).
- But **hosts cache mappings**, and cache propagation is **eventually consistent with invalidation** — when a mapping changes (instance moved), the control plane pushes updates/invalidations. There's a brief window where a stale cache could point at the old host; the system handles this with versioning/validation so a misdelivered packet is dropped rather than mis-delivered. This is the same shape as CPU cache coherence or a CDN purge.

### Where CAP lands
For the *data plane* (forwarding packets), AWS chose **availability + partition tolerance**: hosts keep forwarding using cached mappings even if the Mapping Service is briefly unreachable — an existing flow must not die because a directory node blipped. Freshness (consistency) is traded for liveness, with correctness preserved by ownership validation. This is why "control plane down ≠ data plane down" (M1 §3a).

---

## 3. Hyperplane — the internal fabric behind NAT GW, NLB, PrivateLink, EFS

**AWS Hyperplane** is a massive internal **distributed, stateful, flow-aware** network function platform. [Documented that Hyperplane underpins NAT Gateway, Network Load Balancer, PrivateLink, and EFS mount targets.]

Why it's a big deal architecturally:
- It provides **stateful connection handling** (NAT translations, LB flow affinity) **decoupled from any single instance**, running as a shared fleet. That's how a NAT Gateway can do millions of flows and ~100 Gbps with **no instance for you to manage or scale** — the state lives in Hyperplane, sharded across many nodes, replicated so a node failure doesn't drop your flows.
- **Flow state is replicated** [Inferred: N-way replication / consistent-hash-by-flow], so the fabric survives node loss without breaking established TCP connections — a property a single NAT instance can never give you.
- Because it's shared and horizontally scaled, these services feel "serverless": you get an endpoint, not a box.

Mental anchor: Hyperplane is to *stateful L3/L4 network functions* what S3 is to *storage* — a giant multi-tenant distributed system you consume through a small API surface.

---

## 4. Nitro — where the VPC data plane physically executes

Full Nitro treatment belongs to the EC2 service; here's the networking-relevant core [Documented]:

- **Nitro cards** are dedicated hardware (a SoC on the PCIe bus) that offload networking (ENA/overlay), storage (EBS/NVMe), and management away from the main CPU. The **Nitro hypervisor** is a thin KVM-based component that does little more than CPU/memory partitioning; there is **no fat Dom0** touching your packets (unlike the old Xen design).
- **The VPC data plane runs on the Nitro card:** encapsulation/decapsulation, Security Group evaluation, anti-spoofing, and rate limiting all execute in that offload hardware at line rate. This is why SGs and the overlay impose ~no CPU tax on your workload.
- **Nitro Security Chip / root of trust:** hardware-verified boot; the card enforces that the host can't inspect guest memory or traffic outside policy. This hardware isolation is a pillar of AWS's multi-tenant threat model (see [security.md](security.md)).
- **[Documented] Some Nitro instance types encrypt inter-instance VPC traffic at the physical layer automatically** (within-Region), and all traffic crossing the physical network between AZs/regions on the AWS backbone is encrypted. So "is my intra-VPC traffic encrypted?" is often *yes at the substrate level*, independent of your app's TLS.

---

## 5. Hybrid & route propagation internals

For VPN/Direct Connect/TGW, routing stops being static tables and becomes **dynamic** [Documented]:
- **BGP** is the lingua franca. A **Virtual Private Gateway (VGW)** or **Transit Gateway** peers via BGP with your on-prem routers (over IPsec VPN or Direct Connect). Routes learned via BGP can be **propagated** into VPC/TGW route tables automatically (route propagation), instead of you hand-writing them.
- **Longest-prefix-match** still decides; propagated routes and static routes coexist, with static preferred on ties [Documented].
- **TGW route tables** implement segmentation: each attachment is associated with one TGW route table and can propagate its routes into others selectively — this is how you build "prod can't talk to dev" at the routing layer, not just SGs.

---

## 6. Distributed-systems concepts, mapped onto VPC (spec §17)

| Concept | Where it shows up in VPC |
|---|---|
| **Control vs data plane** | Mapping Service/APIs (control) vs Nitro forwarding (data). Reliability comes from decoupling. |
| **CAP / AP with correctness** | Data plane favors availability; ownership validation preserves correctness under stale caches. |
| **Consistent hashing** | [Inferred] partitioning the Mapping Service + Hyperplane flow tables so scaling doesn't reshuffle. |
| **Quorum / replication** | [Inferred] Mapping Service durability; Hyperplane flow-state replication. |
| **Eventual consistency + invalidation** | Host mapping caches updated/invalidated by control plane (CDN/cache-coherence pattern). |
| **Distributed stateful firewall** | Security Groups: per-ENI conntrack co-located with each workload (scales linearly). |
| **Capability / ownership model** | Anti-spoofing: authoritative address ownership prevents impersonation. |
| **Overlay / tunneling** | Encapsulation (VXLAN/Geneve-family) of virtual packets over the substrate. |
| **Leader election / consensus** | [Inferred] within control-plane services managing config + replica coordination. |
| **BGP / distributed routing** | Hybrid route propagation via VGW/TGW. |
| **Hardware root of trust / virtualization** | Nitro card + security chip enforcing isolation. |

---

## 7. Sources
- re:Invent: *"A Day in the Life of a Billion Packets"*; *AWS Hyperplane / PrivateLink* deep dives; *Nitro* architecture sessions.
- Whitepaper: *"The Security Design of the AWS Nitro System."*
- AWS docs: *Elastic network interfaces*; *AWS Nitro System*; *Transit Gateway route tables*; *Route propagation*.
- Amazon VPC CNI (`amazon-vpc-cni-k8s`) on GitHub — the clearest real-world example of ENI/secondary-IP mechanics (open source).

---

## Self-check (study, don't skip)
1. "The instance has the IP" is the wrong altitude. Restate it correctly and explain one HA pattern that this enables.
2. Why can the Mapping Service be briefly unreachable without existing connections dropping? Which CAP tradeoff is being made, and what preserves correctness?
3. What single property of Hyperplane lets a NAT Gateway survive a node failure without breaking your established TCP connection — and why can a self-managed NAT *instance* never offer it?
4. On an EKS node using the default VPC CNI, you hit a hard ceiling on pods well below CPU/memory limits. What's the mechanism, and name two fixes.
5. Which parts of the VPC data plane run on the Nitro card, and why does that mean Security Groups cost you ~no throughput?
