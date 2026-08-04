# VPC — Module 1: Why it exists, the mental model, and the internal architecture

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md) for the full plan.
> **Epistemics:** claims tagged **[Documented]** (docs / re:Invent / patents / whitepapers) or **[Inferred]** (reconstruction from observed behavior + standard designs). Hold Inferred parts more loosely.

**Module scope:** spec sections 1–3 + 17. Covers *why VPC exists*, the *core mental model*, and the *internal architecture* (control/data plane, Mapping Service, Nitro data plane, Blackfoot edge, distributed stateful Security Groups).

---

## 1. Why does this service exist?

### The problem in one sentence
You cannot let thousands of mutually-distrusting tenants share one physical network without giving each of them the *illusion* of a private, isolated, fully-controlled network — at wire speed, with no performance tax, and with no ability to see or attack each other.

### History: EC2-Classic (2006–2022)
When EC2 launched in 2006 there was no VPC. There was **EC2-Classic**: one gigantic, flat, shared network. Every instance AWS-wide launched into a single shared address space.

```
EC2-Classic (2006):  one flat shared L3 network for ALL customers
┌───────────────────────────────────────────────────────────┐
│  your-instance      random-other-customer      AWS-service │
│  10.x.x.x           10.x.x.x                    10.x.x.x    │
│  (private IPs assigned by AWS from one shared pool)         │
└───────────────────────────────────────────────────────────┘
```

What EC2-Classic did **not** give you:
- No choice of IP range (AWS handed you an IP from its shared pool).
- No customer-controlled subnets, no private-only instances, no routing control.
- No real network boundary — isolation was enforced **only** by Security Groups. One network, a firewall in front of every NIC.
- Public IPs changed on every stop/start — no stable network identity.
- No clean way to extend a corporate datacenter into it (no "your network" to VPN into).

### How companies solved this before AWS
Pre-cloud, "your network" was **physical**: routers, switches, hardware firewalls (Cisco ASA, Juniper), VLANs (802.1Q) for segmentation, routing protocols (OSPF/BGP). Isolation was physical + VLAN-based. VPC didn't invent *subnet / route table / firewall / gateway* — it **virtualized** them.

**Analogy (yours):** this is the same leap as bare-metal → containers. VLANs → software overlay networks; hardware firewalls → distributed packet filters. Kubernetes CNI plugins (Calico, Flannel-VXLAN, Cilium) do the *same category of thing* VPC does, at smaller scale.

### Why EC2-Classic was insufficient
1. **Security posture** — enterprises refused to put databases on a network shared with the whole internet-facing world, guarded only by a per-NIC firewall. They wanted private subnets with *no route to the internet at all*.
2. **Addressing control** — can't merge cloud with on-prem `10.0.0.0/8` if AWS owns the addresses. Hybrid networking impossible.
3. **No topology control** — no "public tier / private tier / traffic flows one way." Segmentation is the base of every serious architecture.
4. **Multi-tenancy at scale** — one flat network doesn't safely scale to millions of customers.

### Why AWS built VPC
VPC (2009) gives every customer a **software-defined virtual network** that *behaves* like a private datacenter network — own CIDR, subnets, route tables, gateways, firewalls — while physically it's an **encapsulated overlay on AWS's shared physical network**. EC2-Classic was fully retired in 2022. Today **everything is VPC**; there is no "outside a VPC" for your compute.

### What if VPC didn't exist?
- No private subnets → every database one bad SG rule from the internet.
- No hybrid cloud (no VPN/Direct Connect into "your" network).
- No segmentation → no PCI/HIPAA tiered architectures.
- No PrivateLink/endpoints → all AWS-service traffic over the public internet.
- Isolation resting entirely on host firewalls, no defense-in-depth.

Net: **the cloud could not have gone enterprise.** VPC is the feature that made AWS acceptable to banks.

---

## 2. The core mental model — this is the whole game

> **A VPC is not a network. It is a distributed lookup table plus a packet-rewriting engine that fakes a network.**

Internalize this and everything else falls out: why SGs scale infinitely, why you can't sniff a neighbor, why public IPs don't appear on your NIC, why cross-AZ costs latency + money.

There are always **two networks**:

- **The substrate** — the *real* physical IP network of the datacenter. Real switches, hosts, IPs (AWS-internal ranges you never see). Carries every actual byte.
- **The overlay (your VPC)** — a *virtual* network that exists only as metadata + packet headers. Your `172.31.0.0/16`, subnets, instance IPs — not "real" to physical switches. A fiction maintained by encapsulation.

```
   THE OVERLAY  (the fiction your instance believes in)
   ┌──────────────────────────────────────────────────────┐
   │   Instance A                Instance B                │
   │   172.31.1.5   ─── send ──►  172.31.1.9               │
   └──────────────────────────────────────────────────────┘
                         │
   ═══ encapsulation boundary (the Nitro card, per host) ═══
                         ▼
   THE SUBSTRATE  (the real physical network)
   ┌──────────────────────────────────────────────────────┐
   │  Host H1 [phys 10.1.4.7]  ═══►  Host H2 [phys 10.2.9.3]│
   │    outer header: src 10.1.4.7  dst 10.2.9.3           │
   │    inner packet: src 172.31.1.5 dst 172.31.1.9        │
   └──────────────────────────────────────────────────────┘
```

**This is precisely VXLAN/Geneve overlay networking** (you know it from Kubernetes). Flannel-VXLAN: pod `10.244.1.3` on Node A → pod `10.244.2.7` on Node B; packet wrapped in an outer header to Node B's real IP, sent over the physical LAN, unwrapped. **VPC is that, hardened for millions of tenants across AZs.** [Documented — overlay/encapsulation model is described in re:Invent talks; exact wire format proprietary → Inferred Geneve/VXLAN-like.]

The mapping `virtual IP → physical host IP` is the crux. Something must know `172.31.1.9` currently lives on physical host `10.2.9.3`. That's the **Mapping Service**.

---

## 3. Internal architecture

### 3a. Control plane vs data plane (distributed-systems lens)
Like every well-built distributed system (and exactly like K8s `etcd + API server` vs `kubelet + CNI datapath`):

- **Control plane** — slow, authoritative, strongly managed. Creates VPCs/subnets/routes, computes and distributes mappings. Low request rate. **Its failure does not stop packets already flowing.**
- **Data plane** — the fast path. Per-packet encap, lookup, filter, forward at line rate (100 Gbps+ on Nitro). **Zero dependency** on the control plane at packet time.

This split is *why VPC is reliable*: an AWS API/control-plane outage doesn't stop existing instances from talking, because mappings + rules are already pushed to hosts. Stating this in an interview reads as senior.

### 3b. The Mapping Service — the heart  [Documented concept · internal impl Inferred]
Authoritative distributed store of `virtual → physical` location data (+ routing/ownership/security metadata):
- Partitioned + replicated across the region (a huge distributed KV store).
- Every host **caches** the mappings it needs. First packet to a new dest may miss → query Mapping Service → cache. Then pure local lookups.
- Instance launch/stop/migrate → control plane **updates/invalidates** mappings, pushes to relevant hosts. Eventually-consistent-with-invalidation — same pattern as a CDN or CPU cache-coherence.
- Enforces **ownership**: records who owns which virtual IP → tenant A can't claim tenant B's address.

### 3c. The data plane on each host — and Nitro
When Instance A sends a packet, this pipeline runs **on the source host's Nitro card** (offloaded hardware, not the hypervisor CPU):

```
Instance A emits frame → 172.31.1.9
        │
        ▼  [on H1's Nitro card]
 (1) Anti-spoof check      : is src really A's IP/MAC? if not → DROP
 (2) Security Group egress : stateful eval of A's SG rules
 (3) Mapping lookup        : 172.31.1.9 → phys host 10.2.9.3 (cache; miss→Mapping Svc)
 (4) Encapsulate           : outer[src 10.1.4.7 → dst 10.2.9.3] + inner packet
 (5) Emit onto substrate
        │
        ▼  substrate delivers to H2
 (6) Decapsulate           : strip outer header  [on H2's Nitro card]
 (7) Security Group ingress: stateful eval of B's SG rules
 (8) Deliver inner packet to Instance B
```

Burn these in:

- **[Documented] Anti-spoofing is enforced in the data plane.** The source host verifies every packet's source against what the Mapping Service says the instance owns. *This is why you physically cannot spoof source IPs or ARP-poison neighbors in EC2* — a whole class of L2 LAN attacks is structurally impossible. It's also why promiscuous mode gets you nothing: you only receive packets encapsulated *to your host, for your instance*.

- **[Documented] Security Groups are a distributed, stateful firewall enforced at every ENI**, not a central appliance. Rules are pushed to the host holding the instance. No single "firewall box" to bottleneck — enforcement scales linearly with the fleet because it's co-located with every workload. That's the architectural reason SGs have no throughput penalty and effectively unlimited aggregate capacity. Stateful = a connection-tracking table per ENI, so return traffic is auto-allowed (like Linux `conntrack` / `iptables -m state`).

- **[Documented] Nitro offload.** On modern instances, steps 1–8 run on the **Nitro card** — dedicated hardware (SoC on the PCIe bus) doing encapsulation, SG enforcement, EBS, and ENA networking. The main CPU/hypervisor never touch the data path. Pre-Nitro (Xen era, ~2013) this ran in software in the privileged **Dom0**, costing CPU + latency. Nitro is *why* a VM gets 100+ Gbps at near-bare-metal. (Full Nitro deep-dive lands in the EC2 service; here just anchor: **VPC's data plane physically lives on the Nitro card.**)

### 3d. Blackfoot — the edge/border  [Documented name · mechanics partly Inferred]
The overlay is self-contained, but packets must leave it — internet, other AWS services, other VPCs. **Blackfoot** is AWS's name for the edge devices that translate between the VPC overlay and the outside world: decapsulate, translate addresses, hand off. Key consequence:

> **Your instance's public IP is never on your instance.** The OS only sees the private IP. The Internet Gateway (realized by these edge devices) does a **1:1 stateless NAT** between the private IP and the public/Elastic IP as packets cross the VPC boundary.

That one fact resolves many confusions: why `ip addr` never shows the public IP; why an instance in a private subnet with a public IP still can't reach the internet (no route to IGW); why Elastic IPs are "attached" logically, not configured in the guest OS.

### 3e. Where the AZ boundary lives
An AZ = one or more physical datacenters with independent power/cooling/network. A VPC spans all AZs in a region; a **subnet lives in exactly one AZ**. Cross-AZ traffic rides the substrate between datacenters (single-digit ms, and it's **billed**). The overlay hides physical topology, but **substrate distance is real** → cross-AZ latency + data-transfer cost. The fiction is perfect for *correctness*; physics still bills you.

---

## Distributed-systems concepts in play (preview of section-17 depth)
- **Control/data plane separation** — reliability via decoupling.
- **Eventually-consistent distributed cache with invalidation** — Mapping Service + host caches.
- **Overlay networking / tunneling** — encapsulation (VXLAN/Geneve family).
- **Distributed stateful firewalling** — connection tracking co-located with workloads, scaling horizontally.
- **Capability/ownership model** — anti-spoofing via authoritative address ownership.

---

## Sources
- re:Invent — **"A Day in the Life of a Billion Packets"** (Eric Brandwine) — canonical on the Mapping Service + encapsulation. *Watch before M2.*
- re:Invent — **"Another Day, Another Billion Packets"** and later Nitro networking deep-dives.
- **AWS Nitro System** overview + *"The Security Design of the AWS Nitro System"* whitepaper.
- AWS docs — *"How Amazon VPC works"*, *"VPC networking components"*.
- Best analogy: your own **Kubernetes CNI / VXLAN** knowledge — map each concept across deliberately.

---

## Gate
Answer the 4 questions in [`quizzes/vpc/module-1-gate.md`](../../quizzes/vpc/module-1-gate.md) before advancing to **M2 — deep packet flow**.
