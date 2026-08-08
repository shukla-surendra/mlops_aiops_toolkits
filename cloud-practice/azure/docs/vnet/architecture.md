# VNet — Module 1: Why it exists, the mental model, and the internal architecture

> Part of the Azure track. See [PROGRESS.md](../../../PROGRESS.md) for the full plan.
> **Epistemics:** claims tagged **[Documented]** (Microsoft docs / Microsoft Research papers
> / Ignite talks) or **[Inferred]** (reconstruction from observed behavior + standard SDN
> designs). Hold Inferred parts more loosely. Verified directly against
> learn.microsoft.com and Microsoft Research publications where cited, not assumed from
> memory or older tutorials.
>
> **Read this after `aws/docs/vpc/architecture.md`** — this module is written *as a contrast*
> to that one, not from zero. Where the mental model is identical, it's stated briefly;
> where Azure genuinely diverges, that gets the depth.

**Module scope:** spec sections 1–3 + 17. Covers *why VNet exists*, the *core mental
model*, and the *internal architecture* (control/data plane, Virtual Filtering Platform,
SmartNIC hardware offload, NSG dual-attachment) — the same shape as VPC's M1.

---

## 1. Why does this service exist?

### The problem in one sentence

Same problem VPC solves: you cannot let thousands of mutually-distrusting tenants share one
physical datacenter network without giving each of them the illusion of a private, isolated,
fully-controlled network, at line rate, with no cross-tenant visibility.

### History: Azure Service Manager / "Classic" (2010–2014→2024 retirement)

Azure's first deployment model — now called **Classic** or **ASM (Azure Service Manager)**
— predates the Azure Resource Manager (ARM) model everything below describes.
[Documented]: Classic had **Cloud Services** and **Affinity Groups** rather than a
Resource-Group-first, VNet-first model; networking and access control were far less
granular than what ARM introduced. Microsoft **retired Classic VM/networking resources in
2023–2024**, functionally the same "one clean cutover" moment EC2-Classic's 2022 retirement
was for AWS. If a tutorial mentions Affinity Groups or Cloud Services (classic), it's
describing a fully retired model.

### How companies solved this before Azure

Same pre-cloud baseline as the AWS doc: physical routers/switches/firewalls, VLANs
(802.1Q) for segmentation. Azure didn't invent subnet/route table/firewall/gateway either —
it virtualized them, on Microsoft's own software-defined networking research stack rather
than AWS's.

### Why Classic/ASM was insufficient

Structurally the same four reasons EC2-Classic was insufficient (security posture,
addressing control, no topology control, no multi-tenant isolation at scale) — the ARM +
VNet model exists for the same underlying reason VPC does, not a Microsoft-specific problem.

### Why Microsoft built VNet the way it did

[Documented] VNet gives every customer a software-defined virtual network — own CIDR,
subnets, route tables (**Effective Routes**, System + User Defined Routes), gateways,
firewalls (NSGs) — physically implemented as an **encapsulated overlay on Azure's shared
physical network**, run through Microsoft's **Host SDN** layer. Conceptually identical goal
to VPC; genuinely different implementation lineage — Azure's approach traces to Microsoft
Research's own SDN work (VL2, 2009) rather than converging independently on the same shape
AWS did.

### What if VNet didn't exist?

Same consequences as the VPC doc's list: no private subnets, no hybrid networking
(ExpressRoute/VPN Gateway), no segmentation for regulated workloads, no Private Link, no
defense-in-depth beyond host firewalls. Net: the cloud could not have gone enterprise here
either — this is the shared reason every major cloud built one of these early.

---

## 2. The core mental model — identical shape to VPC, different machinery underneath

> **A VNet is not a network. It is a distributed policy engine plus a packet-rewriting
> pipeline that fakes a network** — same two-networks idea as VPC (overlay vs. substrate),
> implemented by different Microsoft-built components.

There are still always **two networks**:

- **The substrate** — the real physical network of the Azure datacenter (internal-only IPs,
  real switches, real hosts). Carries every actual byte.
- **The overlay (your VNet)** — a virtual network that exists as metadata + packet rewrite
  rules. Your `10.0.0.0/16`, subnets, private IPs — a fiction maintained by Azure's SDN
  stack, not "real" to the physical fabric.

```
   THE OVERLAY  (the fiction your VM believes in)
   ┌──────────────────────────────────────────────────────┐
   │   VM A                      VM B                       │
   │   10.0.1.5   ─── send ──►   10.0.1.9                   │
   └──────────────────────────────────────────────────────┘
                         │
   ═══ VFP boundary (per host, in the Hyper-V vswitch) ═══
                         ▼
   THE SUBSTRATE  (the real physical network)
   ┌──────────────────────────────────────────────────────┐
   │  Host H1 [phys 10.50.4.7] ══► Host H2 [phys 10.50.9.3] │
   │    outer header: src 10.50.4.7  dst 10.50.9.3          │
   │    inner packet: src 10.0.1.5   dst 10.0.1.9           │
   └──────────────────────────────────────────────────────┘
```

The AWS doc's Mapping Service has a direct Azure counterpart in spirit — something has to
know `10.0.1.9` currently lives on physical host `10.50.9.3`, and enforce who's allowed to
claim that virtual IP. In Azure that "something" is built into the **Virtual Filtering
Platform (VFP)** described below, not a separately-named lookup service in Microsoft's
public materials — worth noting as a real naming/architecture difference, not just
terminology.

---

## 3. Internal architecture

### 3a. Control plane vs. data plane — same distributed-systems split as VPC

- **Control plane** — Azure Resource Manager (ARM) processes VNet/subnet/NSG/route-table
  create/update calls, computes policy, pushes it down to hosts. Low request rate,
  strongly consistent for the resource model itself.
- **Data plane** — per-packet encapsulation, policy lookup, and enforcement, running on
  every host at line rate, with **zero dependency on ARM at packet time** — identical
  reliability argument to VPC: an ARM/control-plane outage doesn't stop already-provisioned
  VMs from talking to each other, because policy is already pushed to the host.

### 3b. VFP — the Virtual Filtering Platform, Azure's real equivalent of "the Mapping Service + SG enforcement" combined

[Documented — Microsoft Research, NSDI 2017: **"VFP: A Virtual Switch Platform for Host
SDN"** (Firestone et al.)]. VFP is a **programmable virtual switch** that runs in the host
(originally in the Hyper-V host's software vswitch, now largely hardware-offloaded — see
3c). Rather than a single "Mapping Service" as a named separate component, VFP itself
implements a layered pipeline of **MatchAction Tables (MATs)** — ordered rule tables that
each host's vswitch evaluates per packet, covering:

- VNet encapsulation/decapsulation (the overlay↔substrate translation)
- Network Security Group enforcement (see 3d)
- Load balancing / NAT (Azure Load Balancer's actual enforcement point is here, at the
  source/destination host, not a central appliance — same "distributed, not centralized"
  design principle as AWS SGs)
- Metering/billing counters, ACLs, and (in Microsoft's own description) the same
  functionality a physical Top-of-Rack switch + hardware load balancer + firewall appliance
  would otherwise provide, implemented in software (then hardware) at every host instead.

This is architecturally the same idea as "encapsulate + enforce co-located with every
workload, so nothing bottlenecks centrally" that makes AWS SGs scale linearly — VFP is
Microsoft's version of that same principle, just packaged as one programmable pipeline
component rather than split into separately-branded pieces.

### 3c. SmartNIC hardware offload — Azure's Nitro-equivalent moment

[Documented — Microsoft Research, SIGCOMM 2015: **"Azure Accelerated Networking: SmartNICs
in the Public Cloud"** (Firestone et al.)]. Running VFP's full MAT pipeline in host software
(on the hypervisor CPU) costs CPU cycles and adds latency per packet — the exact same
"Dom0 software tax" problem pre-Nitro AWS had. Microsoft's fix: an **FPGA-based SmartNIC**
(part of Microsoft's Project Catapult FPGA program) that runs VFP's packet-processing
pipeline **in reconfigurable hardware on the NIC**, offloading the data path off the main
CPU entirely — marketed today as **Accelerated Networking**.

Practical consequence, stated the same way the VPC doc states Nitro's: **VFP's policy
pipeline physically runs on the SmartNIC**, not the hypervisor CPU, on VM sizes with
Accelerated Networking enabled — this is *why* those VM sizes get lower latency and higher
throughput at near-bare-metal levels, and it's the direct Azure analogue to "why a Nitro
instance gets 100+ Gbps at near-bare-metal": both are hardware-offloaded SDN data planes,
built via different hardware strategies (AWS: purpose-built Nitro ASIC/SoC; Azure:
reconfigurable FPGA), converging on the same architectural answer to the same problem.

### 3d. Network Security Groups — dual-attachment, the real divergence from AWS

[Documented, and this is the single most practically important contrast with VPC]: an NSG
can be attached at **either** the subnet level **or** the individual NIC level — sometimes
both on the same VM at once, in which case **both must independently allow traffic** for it
to pass (evaluated as effectively an AND, not an override). AWS splits this into two
*separate* constructs — stateless subnet-level NACLs and stateful per-ENI Security Groups —
where Azure gives you one construct (NSG, always stateful) usable at either or both scope
levels.

- **This is a genuinely different mental model, not just a naming swap.** An AWS engineer's
  instinct — "SGs are per-instance, NACLs are per-subnet, don't conflate them" — doesn't
  transfer cleanly, because Azure's NSG is the *same rule engine* at both scopes, and a
  common Azure misconfiguration is expecting a subnet-level NSG to be "just like a NACL"
  (i.e. assuming it's stateless) when it's stateful at both levels.
- Enforcement point is the same VFP pipeline on the host described in 3b/3c — still
  distributed, still co-located with the workload, still no centralized firewall appliance
  bottleneck. The architectural scaling story is identical to AWS SGs; the *rule model* is
  what differs.

### 3e. The edge/border — NAT Gateway, Load Balancer outbound rules, and Azure Firewall

Azure's edge-translation story is more fragmented across products than AWS's IGW, on
purpose — different products for different needs rather than one implicit gateway:

- **Public IP → private IP translation** happens the same way conceptually as AWS's IGW
  1:1 NAT: the VM's OS only ever sees its private IP; a Public IP resource is a top-level
  Azure resource associated with a NIC or Load Balancer frontend, translated at the
  network edge — never configured inside the guest OS.
- Outbound-only internet access for private resources goes through **NAT Gateway** (a
  managed, scalable SNAT resource — closer to AWS's NAT Gateway than to the IGW) or through
  a Load Balancer's outbound rules (Azure's older default SNAT path, now considered legacy
  in favor of NAT Gateway for anything beyond trivial scale).
- **Azure Firewall** is a separate, explicitly-provisioned managed appliance for
  centralized outbound/east-west policy — unlike NSGs (distributed, free, always-on),
  Azure Firewall is a discrete, billed resource you choose to add, closer in spirit to a
  traditional perimeter firewall than to VFP's distributed model.

### 3f. Where the AZ boundary lives — the sharpest contrast with VPC, worth burning in

[Verified against Microsoft's own docs, and already flagged in
`aws-to-azure-transition-guide.md`]: **a VNet is regional, same as a VPC** — but **a subnet
is NOT pinned to a single Availability Zone the way an AWS subnet is pinned to one AZ.** An
Azure subnet spans the whole region; individual *resources* (VMs, in particular) declare
which AZ they land in independently, as a property of the resource, not a property of the
subnet they sit in.

> This inverts a piece of muscle memory an AWS engineer carries automatically: "one subnet
> per AZ, three subnets for three AZs" is the *default* AWS mental model (baked into every
> AWS VPC Terraform module you've likely written) and **does not apply in Azure at all** —
> a single Azure subnet can, and routinely does, contain VMs spread across every AZ in the
> region simultaneously. Designing an Azure VNet with "one subnet per AZ" out of AWS habit
> isn't just unnecessary, it actively fights how Azure resource placement is meant to work.

Cross-AZ traffic still rides the physical substrate between datacenters and is still
billed and still has real (if small) latency — the physics is identical to AWS; only the
*addressing/subnet* abstraction around it differs.

---

## Distributed-systems concepts in play (preview of section-17 depth)

- **Control/data plane separation** — reliability via decoupling, identical principle to
  VPC.
- **Programmable match-action pipeline (VFP's MATs)** — the Azure-specific shape of "policy
  evaluated per packet," conceptually close to how a P4/OpenFlow pipeline or an eBPF/XDP
  chain evaluates ordered rules.
- **Hardware SDN offload (SmartNIC/FPGA)** — the same "move the data plane off the general
  CPU" idea as Nitro, solved with reconfigurable hardware instead of a fixed-function ASIC —
  a genuinely different hardware strategy worth being able to name in an interview.
- **Distributed, co-located stateful firewalling** — NSGs enforced at the host via VFP, same
  "scales linearly with the fleet, no central bottleneck" property as AWS SGs.
- **Resource-scoped policy vs. subnet-scoped topology** — the AZ-non-pinning of subnets is a
  genuinely different *resource placement model*, not just a naming difference from NACLs.

---

## Sources

- Firestone et al., Microsoft Research — **"VFP: A Virtual Switch Platform for Host SDN,"**
  NSDI 2017. Canonical source for the VFP/MAT pipeline described in 3b.
- Firestone et al., Microsoft — **"Azure Accelerated Networking: SmartNICs in the Public
  Cloud,"** SIGCOMM 2015. Canonical source for the FPGA/SmartNIC offload in 3c.
- Microsoft Learn — *"What is Azure Virtual Network?"*, *"Network security groups"*,
  *"Add a network security group to a subnet or network interface"* (the dual-attachment
  behavior in 3d), *"What is Azure NAT Gateway?"*.
- Microsoft Learn — Azure Resource Manager (ARM) vs. classic deployment model retirement
  notices (the 2023–2024 Classic/ASM retirement referenced in §1).
- Best study method: keep `aws/docs/vpc/architecture.md` open side by side and mark every
  place this doc says "same as VPC" vs. "genuinely different" — the second category is what
  an interviewer will actually probe if AWS-to-Azure comparison comes up.

---

## Gate

Answer the questions in
[`quizzes/vnet/module-1-gate.md`](../../quizzes/vnet/module-1-gate.md) before advancing to
**M2 — deep packet flow, effective routes, peering, Private Link**.
