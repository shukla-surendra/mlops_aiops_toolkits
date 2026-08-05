# VPC — Cross-Cloud: How GCP and Azure Diverge From the AWS Model

> Companion to [architecture.md](architecture.md) and [networking.md](networking.md).
> Read those first — this doc assumes the AWS overlay/substrate mental model and asks,
> concept by concept, whether it transfers to GCP and Azure, or where it genuinely breaks.
> **Epistemics:** claims tagged **[Documented]** are verified directly against each
> vendor's own current docs, not inferred. For the broader (non-networking) AWS↔Azure
> picture — Resource Groups, Entra ID, the resource hierarchy, full service mapping — see
> [aws-to-azure-transition-guide.md](../../../aws-to-azure-transition-guide.md). For how
> this networking model factors into an actual large-scale migration's hybrid-connectivity
> bridge, see [aws-to-azure-migration-strategy.md](../../../aws-to-azure-migration-strategy.md).

**Why this matters**: the single biggest mistake moving between clouds is assuming "VPC"
(AWS), "VPC network" (GCP), and "VNet" (Azure) are the same concept with different names.
Two of the three genuinely are close analogues of each other; one of them — GCP — is built
on a materially different scope model, and getting that wrong leads to real architecture
mistakes, not just vocabulary confusion.

---

## 1. Scope: regional vs. global — the biggest divergence

| | AWS VPC | GCP VPC network | Azure VNet |
|---|---|---|---|
| **VPC/VNet scope** | One region | **Global** | One region |
| **Subnet scope** | One AZ (pinned) | One region (spans all zones in it) | One region (spans all AZs in it) |

**[Documented] GCP's VPC is global, full stop.** Google's own docs: *"VPC networks,
including their associated routes and firewall rules, are global resources and are not
associated with any particular region or zone."* A single GCP VPC network can contain
subnets in every region on Earth simultaneously — there is no AWS equivalent of "one VPC
per region." If you're moving an AWS multi-region architecture (separate VPCs per region,
stitched with peering or Transit Gateway) onto GCP, the direct analogue often *isn't*
"one VPC network per region" — it can genuinely be **one VPC network, with regional
subnets, spanning everywhere you operate.**

**[Documented] GCP subnets are regional, not zonal.** *"Subnets are regional resources"* —
a subnet spans every zone within its region; a VM in any zone of that region draws IPs
from the same regional subnet. **The entire AWS concept of "this subnet lives in exactly
one AZ" doesn't exist in GCP's model.** Zone placement for a GCP resource is a property of
the resource, not the subnet it's in.

**[Documented] GCP's "auto mode" vs. "custom mode" VPC networks** — a GCP-specific choice
with no AWS equivalent. Auto mode automatically creates one subnet per region (using
predefined `10.128.0.0/9` ranges) and keeps creating one in every *new* region GCP adds,
without you doing anything. Custom mode creates zero subnets automatically — you define
every one, and Google's own docs recommend custom mode for production specifically because
auto mode's automatic-expansion behavior is a poor fit for deliberate address planning.

**[Documented] Azure VNet is regional, like AWS.** *"Region-scoped: A VNet exists in a
single Azure region. All resources in that VNet must be in the same region."* To span
multiple regions you peer separate VNets, the same shape as AWS cross-region peering/TGW.

**[Documented] But Azure subnets are not AZ-pinned, unlike AWS.** This is the nuance most
likely to trip up someone who just internalized the AWS model: *"A VNet does span
availability zones within that region,"* and — critically — a single Azure subnet's
resources can be spread across multiple AZs; AZ selection in Azure is a **per-resource**
choice, not a per-subnet one. Two VMs in the *same* Azure subnet can sit in different AZs.
In AWS, that's structurally impossible — the subnet itself determines the AZ.

**The practical consequence**: an AWS engineer designing "one subnet per AZ per tier" (the
canonical 3-tier pattern in `networking.md` §5) is applying an AWS-specific constraint that
doesn't exist on Azure (where AZ and subnet are independent) or GCP (where AZ isn't even a
subnet-level concept at all — it's zone, and subnets don't pin to one).

---

## 2. Internet Gateway / NAT Gateway equivalents

| | AWS | GCP | Azure |
|---|---|---|---|
| Public internet ingress/egress | Internet Gateway (1:1 NAT, free, horizontally scaled) | Implicit default route + external IP on the instance (no separate "gateway" resource to attach) | Public IP resource attached to a NIC, or a Load Balancer/NAT Gateway resource |
| Private-subnet egress-only internet | NAT Gateway (managed, per-AZ, hourly + per-GB) | **Cloud NAT** (managed, regional, per-VM-instance-hour + per-GB, conceptually the same many:1 SNAT idea) | **Azure NAT Gateway** (managed, zonal or zone-redundant, similar per-hour + per-GB model) |

The *concept* — a managed appliance doing many-to-one SNAT so private resources get
outbound-only internet access — transfers cleanly across all three clouds; only the
resource name and exact scoping (regional vs. zonal) differ. This is the one area where
the AWS mental model ports over almost unchanged.

---

## 3. VPC Endpoints / PrivateLink equivalents

| | AWS | GCP | Azure |
|---|---|---|---|
| Private access to the provider's own services | Gateway Endpoint (S3/DynamoDB, free) + Interface Endpoint (PrivateLink, most others, paid) | **Private Google Access** (for GCP APIs, no extra resource needed if enabled on the subnet) + **Private Service Connect** (PrivateLink equivalent, paid) | **Private Endpoint** (Azure Private Link, paid, ENI-equivalent-in-your-subnet model, closely mirrors AWS Interface Endpoints) |

Azure's Private Endpoint model is architecturally the closest of the three to AWS's
Interface Endpoint/PrivateLink — same "gets a private IP in your subnet, resolves via
private DNS" shape. GCP's Private Service Connect is the rough equivalent for
GCP-service/partner traffic; Private Google Access (a subnet-level flag, not a discrete
resource) covers the free "reach Google APIs privately" case with no billed endpoint
resource at all, unlike either AWS or Azure's model.

---

## 4. Peering — the one principle that transfers cleanly everywhere

**[Documented] Non-transitivity holds on all three clouds, verified independently on
each.**

- **AWS**: *"VPC peering is non-transitive: A–B and B–C does not give A–C."*
- **GCP**: *"VPC Network Peering does not provide transitive routing... If net-a and net-b
  are peered, and net-a and net-c are peered, VPC Network Peering does not provide
  connectivity between net-b and net-c."*
- **Azure**: *"Peering isn't transitive; each peering is a direct link."*

Whatever mental model you've built around AWS peering's non-transitivity — and the
Transit-Gateway-style hub-and-spoke fix for the O(N²) mesh problem it causes at scale —
transfers directly to GCP (which has its own hub-and-spoke pattern via Network Connectivity
Center) and Azure (via Virtual WAN / a hub VNet with an NVA). This is the safest concept to
assume transfers without re-verification; scope (§1) is the one that isn't.

---

## Sources

- Google Cloud docs: *VPC networks overview*, *Subnets*, *VPC Network Peering*.
- Microsoft Learn: *Azure virtual networks and subnets* (design guide), *What are Azure
  Availability Zones?*, *Virtual Network peering overview*.
- AWS docs already cited in [architecture.md](architecture.md) and
  [networking.md](networking.md).

---

## Self-check

1. Why can't you replicate AWS's "one subnet per AZ" pattern literally on GCP — what's
   the actual structural reason, not just "it's different"?
2. An Azure VNet has one subnet with VMs in three different AZs. Explain why this is
   normal in Azure but impossible in AWS, in terms of what a subnet actually *is* in each
   cloud.
3. You're advising a team moving a 3-region AWS architecture (3 VPCs, Transit-Gateway-
   connected) to GCP. Would you default to 3 VPC networks or 1? What does that choice
   actually hinge on?
