# AWS → Azure: A Translation Guide for AWS Engineers

A practical bridge doc, not a full gated curriculum module (see [PROGRESS.md](PROGRESS.md)
for that — the `gcp/` track is planned to be taught "by contrast" the same way this doc
teaches Azure). If you already carry the AWS mental model from `aws/docs/`, this is the
fastest way to redirect that knowledge rather than starting from zero.

**Epistemics**: every non-obvious claim below is verified directly against Microsoft's
current docs (learn.microsoft.com), not assumed from memory or older tutorials — Azure
renames things more aggressively than AWS does, and a few of the differences below are
exactly the kind of thing that trips up someone transferring AWS knowledge unmodified.

## The core mental-model shift, first principles

**AWS's philosophy: granular services, assemble your own, Account as the hard isolation
boundary.** An AWS Account is simultaneously a billing boundary, a resource-isolation
boundary, and (by default) an IAM boundary — nothing crosses it without explicit
cross-account policy. Beyond that, AWS gives you almost no *native* organizing construct
within an account — grouping related resources is done with tags, or with a CloudFormation
stack's deployment boundary, both of which are conventions you adopt, not something AWS
enforces.

**Azure's philosophy: fewer, broader-scoped, more integrated services, and identity is the
foundation everything else sits on top of.** Two things AWS engineers consistently
underestimate on first contact:

1. **Resource Groups are mandatory, not a convention.** [Verified, Microsoft's own
   definition]: *"A resource group is a container that you use to manage related resources
   for an Azure solution... All resources in your resource group should share the same
   lifecycle."* Every Azure resource belongs to exactly one Resource Group **from the
   moment you create it** — there's no equivalent "just tag it later" escape hatch the way
   AWS lets you defer organizational decisions indefinitely. This is a Day-1 decision AWS
   never forces on you.
2. **Identity is unavoidable and central, not optional.** Every Azure subscription trusts
   exactly one identity tenant (**Microsoft Entra ID** — see the rename note below), and
   every resource operation authenticates through it. AWS IAM can run standalone with no
   directory service at all; Azure's model doesn't offer that option.

## The resource hierarchy — genuinely different shape from AWS's

| AWS | Azure | Notes |
|---|---|---|
| (implicit — the AWS account structure itself) | **Tenant** (a Microsoft Entra ID directory) | The root of the whole hierarchy — [verified] the root Management Group's ID literally equals the Entra tenant ID; everything folds up to it |
| Organization → Organizational Unit | **Management Group** | Groups subscriptions for policy/RBAC inheritance, same intent as AWS OUs |
| **Account** | **Subscription** | The closer of the two to AWS's billing+isolation boundary, but see below — it's not a perfect match |
| *(no native equivalent — tags/stacks only)* | **Resource Group** | [Verified] a genuinely Azure-specific construct with no AWS analogue — a mandatory, lifecycle-scoped container *within* a subscription |
| Resource | Resource | Same concept |

[Verified, Microsoft's own phrasing]: Azure documents this as *"four levels of management
scope: management groups, subscriptions, resource groups, and resources"* — Tenant is the
directory root rather than a formally named "scope level," but functionally sits above
Management Group in the hierarchy.

**The AWS Account vs. Azure Subscription mismatch, precisely**: an AWS Account is one flat
boundary doing three jobs at once (billing, isolation, IAM scope). Azure splits that into
two layers — Subscription (billing + a natural RBAC/policy scope) and Resource Group
(lifecycle grouping *within* that billing boundary) — so "how do I isolate this workload"
in Azure is a two-decision question (which subscription, which resource group), not one.

## Identity: IAM vs. Entra ID + Azure RBAC

- **Microsoft Entra ID** is the current name — [verified]: Azure Active Directory (Azure
  AD) was officially renamed, announced July 11, 2023, with the rollout largely complete
  by end of 2023. If a tutorial or a colleague says "Azure AD" or "AAD," they mean this —
  same service, old name. (Azure AD *B2C* was the one exception not renamed.)
- **Azure RBAC** grants Entra identities (users, groups, service principals, or managed
  identities) a role **at a specific scope** — Management Group, Subscription, Resource
  Group, or individual Resource — and that assignment **inherits downward** through the
  hierarchy. Structurally similar to how AWS IAM policies can be attached at different
  points, but the scope hierarchy itself (four fixed levels, always inheriting down) is
  more rigid and explicit than AWS's model.
- **AWS IAM Role (assumed via STS)** → **Azure Managed Identity** (system-assigned, tied to
  one resource's lifecycle, or user-assigned, reusable across resources) — same goal
  (avoid hardcoded credentials for a resource calling other Azure services), different
  implementation shape.

## Availability Set vs. Availability Zone — two different Azure concepts, don't conflate

[Verified, both are real and distinct]: **Availability Set** groups VMs across **fault
domains and update domains within a single datacenter** (99.95% SLA) — this predates
Azure's AZ support and is *not* the same thing as an AZ. **Availability Zone** is a
**physically separate datacenter within a region** with independent power/cooling/network
(99.99% SLA) — this is Azure's actual analogue to an AWS AZ. Seeing "Availability Set" in
an Azure doc and assuming it means the same thing as "Availability Zone" is a genuinely
common, easy mistake for someone coming from AWS, where only one such concept exists.

## Service-by-service mapping

### Compute

| AWS | Azure |
|---|---|
| EC2 | Virtual Machines |
| Auto Scaling Group | Virtual Machine Scale Sets (VMSS) |
| Lambda | Azure Functions |
| Elastic Beanstalk | App Service |

### Containers

| AWS | Azure |
|---|---|
| ECS | Azure Container Instances (ACI) / Azure Container Apps |
| EKS | Azure Kubernetes Service (AKS) |
| ECR | Azure Container Registry (ACR) |

### Storage

| AWS | Azure |
|---|---|
| S3 | Blob Storage |
| EBS | Managed Disks |
| EFS | Azure Files |

### Databases

| AWS | Azure | Notes |
|---|---|---|
| RDS | Azure SQL Database / Azure Database for PostgreSQL, MySQL | |
| DynamoDB | Azure Cosmos DB | **Not a clean 1:1** — see below |
| ElastiCache | Azure Cache for Redis | |

**Cosmos DB is not a direct DynamoDB clone** — [verified] it's explicitly multi-model,
exposing data through multiple APIs (NoSQL/document, MongoDB-compatible, Gremlin/graph,
Table). The **Table API** specifically is the closer DynamoDB-equivalent surface; the
default NoSQL API is a different document-model shape. **Worth knowing this is actively
shifting**: as of mid-2026, Microsoft's own Cosmos DB overview page has rebranded toward
"Unified AI Database," foregrounding vector-search/AI workloads, and there's now a
separate, related product — **Azure DocumentDB** (MongoDB-wire-compatible, PostgreSQL
engine underneath) — positioned alongside it. If you're working from an older tutorial,
re-check current positioning before committing to either for a real design.

### Networking

Covered in full depth already —
[VPC — Cross-Cloud: How GCP and Azure Diverge From the AWS Model](aws/docs/vpc/cross-cloud-comparison.md)
covers VNet vs. VPC scope, subnet/AZ relationship, NAT Gateway/endpoint equivalents, and
peering. Quick summary table for this doc's purposes:

| AWS | Azure |
|---|---|
| VPC | Virtual Network (VNet) — regional like AWS, but subnets aren't AZ-pinned (see the linked doc) |
| Internet Gateway | (implicit — no separate attach-a-gateway resource) |
| NAT Gateway | Azure NAT Gateway |
| VPC Endpoint (Interface) | Private Endpoint (Azure Private Link) |
| VPC Peering | VNet Peering (also non-transitive, verified) |
| Route 53 | Azure DNS + Traffic Manager |
| CloudFront | Azure CDN / Azure Front Door |
| ALB / NLB | Application Gateway / Azure Load Balancer |

### Messaging & eventing

| AWS | Azure |
|---|---|
| SQS | Azure Queue Storage / Service Bus Queues |
| SNS | Service Bus Topics / Event Grid |
| Kinesis | Event Hubs |

### Monitoring & observability

| AWS | Azure |
|---|---|
| CloudWatch | Azure Monitor |
| CloudTrail | Activity Log |
| X-Ray | Application Insights |

(See also this repo's own [`observability-terminology.md`](../mlops_aiops/docs/observability-terminology.md)
and [`observability-on-eks.md`](../mlops_aiops/docs/observability-on-eks.md) for how these
map onto the open-source stack, not just AWS↔Azure.)

### Secrets, IaC, and orchestration

| AWS | Azure | Notes |
|---|---|---|
| Secrets Manager / Parameter Store | Key Vault | |
| CloudFormation | ARM Templates | [Verified] ARM is more fundamental than CloudFormation's role — *"When you send a request through any of the Azure APIs, tools, or SDKs, Resource Manager receives the request... authenticates and authorizes"* it. Every Azure operation goes through ARM, not just declarative deployments. |
| CDK | Bicep | Bicep compiles down to ARM JSON, the same relationship CDK has to raw CloudFormation — a more ergonomic DSL over the same underlying engine |
| Step Functions | Logic Apps / Durable Functions | |

### Data & analytics

| AWS | Azure |
|---|---|
| Redshift | Synapse Analytics |
| EMR | HDInsight / Azure Databricks (first-party Microsoft integration, notably closer than AWS's relationship with Databricks) |

## What actually surprises AWS engineers most, in practice

1. **Resource Group is a Day-1 decision AWS never forces.** Deciding "which Resource
   Group" happens at resource-creation time, every time — there's no deferring it.
2. **Identity (Entra ID) isn't optional infrastructure you bolt on later** — it's the
   substrate every Azure subscription already trusts before you've created a single
   resource.
3. **Not every Azure region has Availability Zones.** Unlike AWS where essentially every
   region offers multiple AZs, some Azure regions are AZ-less — check the specific target
   region before assuming three-AZ redundancy is available, rather than assuming AWS's
   near-universal AZ availability carries over.
4. **Old tutorials say "Azure AD"** — same service, renamed to Microsoft Entra ID in 2023.
   Don't assume it's a different, deprecated product.
5. **Subnets aren't AZ-pinned in Azure** — a real behavioral difference from AWS's "one
   subnet, one AZ" rule, covered in full in the
   [cross-cloud VPC comparison](aws/docs/vpc/cross-cloud-comparison.md).

## Related docs in this repo

- [VPC — Cross-Cloud Comparison](aws/docs/vpc/cross-cloud-comparison.md) — the deep,
  verified networking-specific comparison this doc's Networking section summarizes.
- [AWS → Azure Migration Strategy & Execution Plan](aws-to-azure-migration-strategy.md) —
  the large-scale (200-service) migration methodology built on top of this service mapping.
- [PROGRESS.md](PROGRESS.md) — the master AWS-track curriculum this guide sits alongside.
- [`gcp/README.md`](gcp/README.md) — the (planned) GCP track, intended to be taught by the
  same contrast-with-AWS method this doc uses for Azure.
