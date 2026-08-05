# Cloud Migration Strategy & Execution Plan: 200 AWS Services → Azure

**Prepared as**: a Principal Engineer's migration strategy talk/plan. Companion to
[`aws-to-azure-transition-guide.md`](aws-to-azure-transition-guide.md) (service mapping,
mental model) and [`aws/docs/vpc/cross-cloud-comparison.md`](aws/docs/vpc/cross-cloud-comparison.md)
(networking specifics this plan's hybrid-connectivity phase depends on) — read those first
if the AWS↔Azure vocabulary below isn't already familiar.

## What kind of document this actually is

"Whatever we call this document" — in real enterprise practice, what follows corresponds
to three distinct deliverables that AWS's and Azure's own migration methodologies name
separately, bundled here into one talk: a **Migration Readiness Assessment** (do we
understand what we have and is it safe to move), a **Business Case** (why, and at what
cost), and a **Migration Wave Plan** (the actual sequencing and timeline). Producing all
three together, as one document, is itself a Principal-level call — most teams produce them
separately across different phases, but a single narrative is what a talk needs.

## Assumptions and scope (explicit, since the ask specifically wants them stated)

Stating these up front because **the entire plan below changes** if any of them don't
hold — this is not boilerplate, it's the actual input to every downstream decision:

- **Direction**: 200 services currently running on AWS, target is Azure. (Confirmed with
  the requester — the prompt read "AWS to AWS," treated as a typo for AWS→Azure given the
  immediately preceding work in this repo.)
- **"200 services" means 200 independently-deployable application/service units** — not
  200 AWS *resources* (which would be a vastly larger, differently-shaped number). Each
  service is assumed to have its own deployment lifecycle, its own team or team-fraction
  of ownership, and non-trivial dependencies on other services in the portfolio.
- **No greenfield assumption** — these are live, in-production services with real traffic,
  not a lab exercise. Migration must not be visible to end users as downtime beyond
  planned, communicated maintenance windows.
- **Business is continuing to operate and ship features throughout** — this is not a
  "freeze everything, migrate, then resume" scenario. Teams keep shipping to AWS during
  early waves; this has real implications for drift between assessed state and actual
  state by the time a service's wave arrives (addressed in Risk Management).
- **No single "how many services per month" throughput benchmark exists from AWS/Azure's
  own docs** — any timeline math below is an explicit, labeled **model** built from stated
  assumptions about wave team capacity, not a vendor-published rate. Treat the numbers as
  illustrative and re-derive them from your own team's actual capacity before committing to
  a real date.
- **Budget and executive sponsorship are assumed to exist** — this plan doesn't make the
  business case for *why* migrate (cost, capability, contract, or regulatory reasons are
  all real, valid drivers, but are assumed already decided before this plan starts).
- **A hybrid period is assumed unavoidable** — with 200 services and real dependency
  chains, some services will run on AWS while their dependencies have already moved to
  Azure (or vice versa) for a meaningful stretch of the timeline. Any plan that assumes a
  clean instant cutover for 200 interdependent services is not a credible plan.

## Methodology grounding — this isn't invented, it's assembled from named frameworks

Verified directly against source material, not asserted from memory:

- **The "Rs" categorization concept traces to Gartner, 2011** — analyst Richard Watson's
  *"Migrating Applications to the Cloud: Rehost, Refactor, Revise, Rebuild, or Replace?"*
  originated the idea of classifying each application into one of a small set of migration
  strategies rather than treating "migrate" as one undifferentiated action. This is the
  single most important mental shift for a 200-service portfolio: **not every service gets
  migrated the same way**, and deciding *how* each one moves is a distinct step from
  deciding *when*.
- **AWS's current model extends this to 7 Rs** (its own docs state this explicitly builds
  on Gartner's 2011 framework): **Rehost** (lift-and-shift, no changes), **Replatform**
  (lift-and-reshape, some optimization — e.g. RDS instead of self-managed DB), **Relocate**
  (hypervisor-level move, e.g. VMware-based), **Repurchase** (drop-and-shop — replace with
  a SaaS/managed equivalent), **Refactor/Re-architect** (redesign for cloud-native),
  **Retain** (no business case to move it now), **Retire** (decommission — the highest-ROI
  category nobody budgets time for).
- **AWS's Migration Acceleration Program (MAP)** structures large migrations in three
  phases — **Assess** (readiness assessment against AWS CAF's six perspectives: business,
  people, governance, platform, security, operations; produces the business case/TCO),
  **Mobilize** (build the landing zone, run a pilot wave, build team skills — AWS's own
  guide describes this as roughly 8 workstreams over 8 two-week sprints), **Migrate &
  Modernize** (execute at scale — the "migration factory" pattern, reusing patterns/tooling
  validated in Mobilize).
- **Azure's Cloud Adoption Framework (CAF)** uses a parallel structure — **Strategy → Plan
  → Ready → Adopt** as the sequential foundation (Adopt is where actual
  migrate/modernize/build work happens), with **Govern, Secure, Manage** running in
  parallel as ongoing operational methodologies, not one-time phases. Azure's CAF has a
  dedicated, named page for **"migration wave planning"** — confirming "wave" is standard
  vocabulary on both platforms, not something invented for this document.

This plan below maps onto: **AWS MAP's Assess phase** (Part 1), **Mobilize phase** (Part
2), **Migrate & Modernize phase** (Parts 3-4) — using Azure as the destination, since AWS's
methodology for *assessing and sequencing* a migration is destination-agnostic even when
the target cloud is Azure.

## Part 1 — Assess: portfolio categorization and dependency mapping

**Before any timeline exists, every one of the 200 services needs two things done to it:**

1. **A 7-Rs categorization.** Not a guess — driven by a scored assessment per service
   across: business criticality, technical debt/architecture fitness for lift-and-shift,
   compliance/data-residency constraints, licensing (some AWS-native services like
   DynamoDB or Lambda have no 1:1 Azure equivalent — see the mapping table in
   [`aws-to-azure-transition-guide.md`](aws-to-azure-transition-guide.md) — a service built
   tightly around DynamoDB's specific consistency model may need Refactor, not Rehost, even
   if the team's instinct is "just lift and shift"), and remaining useful life (a service
   scheduled for retirement in 18 months is a **Retain** or **Retire** candidate, not a
   migration candidate at all — this single check alone typically removes 10-20% of a
   real 200-service portfolio from the migration scope entirely, and is the highest-ROI
   step nobody does first).
2. **Dependency mapping.** Using AWS Application Discovery Service (agentless or
   agent-based) feeding a dependency graph, cross-referenced against Azure Migrate's
   discovery on the target side once a pilot lands. The graph answers one question that
   determines the entire wave sequence: **for each service, what does it call, and what
   calls it?** Services with no dependents ("leaf" services) and few dependencies are
   naturally early-wave candidates; shared/foundational services with many dependents
   (auth, a shared message bus, a core data platform) are the ones whose *migration
   strategy* choice ripples into every dependent service's plan — get these categorized
   and sequenced first even if they migrate in a later wave, because every dependent
   service's plan is contingent on knowing what happens to them.

**Output of Part 1**: a scored table of all 200 services — R-category, criticality,
dependency fan-in/fan-out, estimated complexity — that Part 2 and 3 consume directly. This
*is* the Migration Readiness Assessment deliverable named above.

## Part 2 — Mobilize: landing zone, pilot wave, and the hybrid-connectivity bridge

**Before wave 1 touches a production service**, three things need to exist:

- **The Azure landing zone** — the target-state Resource Group/Subscription/Management
  Group hierarchy (per the resource-hierarchy section of
  [`aws-to-azure-transition-guide.md`](aws-to-azure-transition-guide.md)), Entra ID
  tenant/RBAC structure, and baseline governance (policy, tagging, cost management) — built
  *before* any real service moves, not evolved ad hoc as services land.
- **Hybrid connectivity between AWS and Azure**, for however long the migration takes.
  With 200 interdependent services, some fraction will always be split across both clouds
  mid-migration — a service on Azure calling a not-yet-migrated dependency still on AWS
  needs a real, secure, low-latency path between them. This is a VPC↔VNet-adjacent problem:
  either a **site-to-site VPN** (AWS VPN Gateway ↔ Azure VPN Gateway) for lower initial
  cost and setup time, or **AWS Direct Connect + Azure ExpressRoute** meeting at a shared
  colocation/exchange point for higher bandwidth and lower latency at higher cost — the
  same "start simple, graduate once volume justifies it" logic already established
  elsewhere in this repo for other infra decisions. **This bridge is often the single most
  underestimated piece of a multi-cloud migration** — teams plan the service moves and
  treat cross-cloud connectivity as an afterthought, then discover the temporary VPN link
  is now a permanent bottleneck 8 months in.
- **A pilot wave** — 3-5 real, low-risk (Retain-adjacent-but-not-quite, low-criticality,
  few dependents) services migrated first, specifically to validate the landing zone,
  tooling, and process before committing to the full wave plan. The pilot's job is finding
  what's wrong with the plan while the blast radius is small — treat pilot findings as
  mandatory input to revising Part 3's wave plan, not just a confidence exercise.

## Part 3 — Migrate & Modernize: wave planning methodology

**Waves are sequenced by three factors together, not any one alone:**

1. **Dependency order** — a service generally shouldn't move before its hard dependencies
   have either already moved, or the hybrid bridge from Part 2 makes the split
   configuration workable for the duration.
2. **Risk gradient** — confidence should build wave over wave. Early waves: low
   criticality, low complexity, Rehost-category services. Middle waves: increasing
   criticality and complexity as the team's tooling/process is proven. Late waves: the
   highest-criticality, Refactor-category, and most deeply-depended-upon services, moved
   last specifically *because* the team has the most practiced process and the most
   organizational trust by then.
3. **Team/business capacity** — how many services a wave team can actually carry
   concurrently without degrading quality, which is a real capacity constraint distinct
   from the technical sequencing above.

**A "migration factory"** — AWS MAP's own term for the Migrate & Modernize phase's
operating model — is the practical mechanism for executing at 200-service scale: a
standardized, repeatable process (runbook, tooling, rollback plan, communication template)
applied per-service by a rotating set of wave teams, rather than each service's migration
being independently reinvented. The factory pattern is what makes 200 services tractable at
all — without it, 200 migrations is 200 different one-off projects.

## Part 4 — Worked wave plan (explicitly modeled, not benchmarked)

Applying the above to a representative 200-service portfolio, with **stated, re-derivable
assumptions** rather than an unverifiable industry rate:

**Assumed portfolio split** (a realistic shape for a mature AWS estate, not a universal
constant — re-derive from your own Part 1 assessment):

| R-category | Assumed % of portfolio | Count (of 200) |
|---|---|---|
| Retire | 10% | 20 |
| Retain | 10% | 20 |
| Rehost | 40% | 80 |
| Replatform | 25% | 50 |
| Refactor/Re-architect | 12% | 24 |
| Repurchase | 3% | 6 |

**160 services actually migrate** (200 minus Retire and Retain).

**Assumed wave-team capacity** (the explicitly modeled part — state your own team's real
number here instead): a wave team can carry **~4 Rehost-category services concurrently
per 2-week sprint** to completion (discover → move → validate → cutover), **~2
Replatform-category services** per sprint (more validation/optimization work), and
**Refactor-category services are tracked individually**, each with its own multi-sprint
timeline outside the factory cadence since they're effectively small re-architecture
projects, not migrations.

| Phase | Duration (modeled) | What happens |
|---|---|---|
| Assess (Part 1) | 6-8 weeks | Portfolio categorization + dependency mapping for all 200 services |
| Mobilize (Part 2) | 8-10 weeks | Landing zone, hybrid connectivity, pilot wave (3-5 services) |
| Migrate & Modernize — Rehost/Replatform waves | ~20-26 weeks | 130 services (80 Rehost + 50 Replatform) via the factory pattern, 3-4 wave teams running in parallel, each wave ~2 weeks |
| Migrate & Modernize — Refactor track | Runs in parallel with the above, extends ~4-8 weeks beyond it | 24 Refactor-category services, tracked as individual projects, typically the long pole |
| Repurchase | Runs opportunistically alongside other waves | 6 services replaced with Azure-native/SaaS equivalents, often the fastest category once a vendor decision is made |
| **Total, Assess through last wave** | **~40-50 weeks (roughly 9-12 months)** | For this specific modeled assumption set — a genuinely different team capacity number changes this materially, re-derive don't reuse |

## Risk Management

- **Portfolio drift**: the Part 1 assessment goes stale as teams keep shipping features
  during a 9-12 month migration. Mitigation: re-validate each service's categorization
  immediately before its wave starts, not just once at the start of the whole program.
- **The hybrid-connectivity bridge becomes a permanent bottleneck**: flagged in Part 2 —
  mitigate by explicitly sizing it for late-wave load, not early-wave load, and revisiting
  the VPN-vs-ExpressRoute/Direct-Connect decision at the program's midpoint.
- **A shared/foundational service's migration strategy changes everyone downstream**: if
  the auth service or core data platform's R-category or timeline shifts, every dependent
  service's wave assignment needs re-evaluation — this is why Part 1 explicitly calls out
  assessing high-fan-in services first even if they migrate later.
- **Cutover risk concentrated in high-criticality late waves**: by design, the riskiest
  services move last with the most-practiced process — but that also means the latest
  waves have the least schedule slack left if something goes wrong. Build explicit buffer
  into the last 2-3 waves specifically, not evenly across the whole timeline.
- **Team fatigue / migration-factory burnout**: 9-12 months of sustained migration work on
  top of regular feature work is a real organizational risk, not just a technical one —
  worth naming explicitly in a Principal-level plan, since it's the kind of risk that gets
  omitted from purely technical planning documents.

## Cutover and rollback strategy, by R-category

| Category | Cutover approach | Rollback approach |
|---|---|---|
| Rehost | Blue-green: stand up on Azure, validate, switch traffic (DNS/traffic manager), keep AWS instance warm for a defined rollback window | Switch traffic back; AWS instance was never torn down during the window |
| Replatform | Similar blue-green, but data-layer migration (e.g., to a managed Azure DB) needs its own validated data-sync/cutover plan, often the actual complexity driver, not the compute move | Depends on whether the data-layer change is reversible within the rollback window — decide and document this *before* cutover, not during an incident |
| Refactor | Feature-flagged, incremental rollout (the same canary/shadow pattern already documented in [`engineering_fundamentals`](../engineering_fundamentals/system_design_foundation/04_model_serving_deployment/tutorial.md) for model rollouts applies directly here) | Flag flip back to the old implementation, since old and new run in parallel during rollout by design |
| Repurchase | Data migration to the new SaaS/managed product, then a defined traffic cutover — rollback plan is specific to whether the old product/data can still ingest writes during a rollback window | Depends entirely on the specific replacement — no general pattern, must be planned per case |

## Governance during migration

- **Dual-cloud cost visibility** — both AWS and Azure billing need to feed one combined
  view for the duration; without it, the org loses the ability to reason about total spend
  during the overlap period, which for a 9-12 month program is not a short window.
- **Security posture parity** — Azure RBAC/Entra ID policies need to match (or
  deliberately improve on) AWS IAM's existing posture before a service's data moves, not
  after — verified in Part 2's landing-zone build, re-checked per wave.
- **Single source of truth for "where does service X actually run right now"** — with
  services genuinely split across both clouds mid-migration, an out-of-date runbook or
  on-call doc pointing at the wrong cloud is a real, common incident-response failure mode
  during exactly this kind of program.

## Success metrics / exit criteria

- Per-wave: zero unplanned downtime beyond the communicated cutover window, rollback
  capability validated (not just planned) before cutover, cost within the modeled range for
  that service's R-category.
- Program-level: portfolio fully migrated or explicitly Retained/Retired (not "still on
  AWS with no plan"), hybrid-connectivity bridge decommissioned once the last dependency
  crossing it has moved, and — the metric most programs skip — **a documented count of how
  many services' actual R-category differed from their Part 1 assessment**, since that gap
  is the single best input to making the *next* large migration's Assess phase more
  accurate.

## Staff & Principal Altitude

A **senior** answer picks a migration tool, estimates a timeline from gut feel, and moves
services roughly in the order teams volunteer.

A **staff** answer additionally: categorizes every service by R-strategy before
sequencing anything; builds the dependency graph explicitly rather than assuming it's
known; sequences waves by risk gradient, not convenience.

A **principal** answer additionally: (1) treats the hybrid-connectivity bridge as a
first-class, explicitly-sized piece of infrastructure with its own lifecycle, not an
afterthought; (2) names portfolio drift and organizational fatigue as real risks alongside
technical ones, since a 9-12 month program's biggest failure modes are often organizational,
not technical; (3) builds the "does actual R-category match Part 1's prediction" metric
into the program specifically so the *next* migration this org runs is better-informed than
this one — treating the migration itself as a source of organizational learning, not just a
one-time project to close out.

## Related docs in this repo

- [`aws-to-azure-transition-guide.md`](aws-to-azure-transition-guide.md) — the service
  mapping and mental-model doc this plan's R-categorization step depends on.
- [`aws/docs/vpc/cross-cloud-comparison.md`](aws/docs/vpc/cross-cloud-comparison.md) — the
  networking depth behind Part 2's hybrid-connectivity bridge decision.
- [`04_model_serving_deployment` tutorial](../engineering_fundamentals/system_design_foundation/04_model_serving_deployment/tutorial.md)
  — the canary/shadow rollout pattern this plan's Refactor-category cutover strategy reuses.
