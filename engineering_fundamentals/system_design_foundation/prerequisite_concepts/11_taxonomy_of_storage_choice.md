# Prerequisite Concepts, Part 11: Taxonomy of Storage — Choosing by First Principles, Not Fashion

[Part 6](06_mechanical_sympathy_and_physics_of_latency.md) established the physics
underneath every storage medium (HDD seek/rotation, SSD write amplification, bit rot).
[Part 10](10_physics_of_persistence.md) established the two dominant storage-engine shapes
(B-tree vs. LSM-tree) and the RUM conjecture governing their trade-offs. [Part 2](02_data_and_consistency.md)
established how data spreads across machines (sharding, replication, GFS, consistency
models). This part doesn't introduce new mechanism — it names the failure mode that makes
all of that prior work useless in practice, and gives the checklist that fixes it: **how a
database actually gets chosen, versus how it should.**

## The Failure Mode: Choosing by Fashion, Not Engineering

At junior level, database selection is very often **not** a first-principles decision at
all — it's one of a small number of unexamined defaults:

- **"It's what I know."** The team (or the individual engineer) has used Postgres, or
  MongoDB, or MySQL before, so that's what gets reached for again — regardless of whether
  this workload's shape resembles the one that choice actually fit last time.
- **"It's what's popular."** A technology is trending, is what a bootcamp curriculum taught,
  or is what a well-known company's engineering blog described — so it must be a safe
  choice, without checking whether that company's scale, access pattern, or consistency
  requirements have anything in common with the workload actually being built.
- **"It's what the last company used."** A genuinely reasonable choice for a *different*
  workload, at a *different* scale, gets carried forward as an assumption rather than
  re-derived.

**Why this is a fashion decision, not an engineering one**: none of these reasons reference
the actual workload at all — not its access pattern, its size, its latency requirements, its
consistency needs, its write shape, or what failures it has to survive. **Every database
embodies a trade-off** — this is not a rhetorical claim, it's the literal content of the
last three parts: B-tree vs. LSM-tree is [the RUM conjecture](10_physics_of_persistence.md#naming-the-trade-off-precisely-write-read-and-space-amplification)
made concrete (no structure minimizes read, write, *and* space cost simultaneously), CAP
theorem forces a consistency-vs-availability choice under partition, and every replication
strategy trades latency against durability against cost. **"Which database is best" is not
a coherent question** until a workload is specified — the coherent question is always
**"which axis am I choosing to optimize, and what am I consciously willing to pay on the
others."**

## A Brief History: Why a Taxonomy Needs to Exist At All

Fashion-driven selection isn't just a junior-engineer habit — it's the reflex left over from
several decades where there genuinely was only one dominant model. **Picking a storage model
that fights a workload's natural shape is the data-model version of [Part 6's mechanical
sympathy](06_mechanical_sympathy_and_physics_of_latency.md#mechanical-sympathy-working-with-the-machine-not-against-it):
fighting the grain instead of working with it** — and the history below is the concrete
story of an entire industry doing exactly that at scale, until it stopped working.

### Codd, 1970: The Paper That Created "The One Model"

Edgar F. Codd, then at IBM, published *"A Relational Model of Data for Large Shared Data
Banks"* (Communications of the ACM, 1970). **The problem it solved**: the databases before
it — IBM's own IMS (hierarchical), the CODASYL network model — made querying mean
physically navigating explicit pointer paths baked into how the data happened to be stored;
the logical question you wanted to ask and the physical path you had to walk were the same
thing. **Codd's insight**: represent everything uniformly as **relations** — tables of
tuples — and query them with declarative predicate logic (state *what* you want, not *how*
to reach it), letting the database engine, not the programmer, figure out the access path.
Codd's own term for this was **data independence**: the first time the logical model was
decoupled from physical storage.

### Normalization and 3NF: Store Every Fact Exactly Once

Codd (and later, with Raymond Boyce) formalized **normal forms** — design rules eliminating
redundancy. **Third Normal Form (3NF)**: every non-key attribute depends on the key, the
whole key, and nothing but the key — no fact stored twice. This isn't an aesthetic
preference; duplicated facts create three concrete, named failure modes: an **update
anomaly** (a fact is duplicated across rows, one copy gets updated, the others don't, and the
data now silently disagrees with itself), an **insert anomaly** (a fact can't be recorded
until an unrelated row happens to exist to attach it to), and a **delete anomaly** (deleting
the one row holding a fact destroys the fact entirely, with no other copy to fall back on).
Normalization is **data integrity enforced by structure**: one source of truth per fact,
referenced by foreign key rather than copied.

### ACID, Fully Unpacked

[Part 2's ACID vs. BASE section](02_data_and_consistency.md#acid-vs-base) named the four
letters; here's each one's actual mechanism:

- **Atomicity** — all-or-nothing. Needs more than [Part 10's
  WAL](10_physics_of_persistence.md#the-write-ahead-log-making-durability-affordable) (which
  only replays *forward*) — an **undo** mechanism is required too, to cleanly roll back a
  transaction that aborts partway through, leaving no partial effect behind.
- **Consistency** — a transaction moves the database between states that satisfy its
  declared constraints (foreign keys, uniqueness, check constraints). **Worth flagging
  explicitly, because it's a genuinely common conflation**: this is a *completely different*
  "C" from CAP theorem's Consistency (linearizable reads across replicas). ACID's C is about
  the schema's own integrity rules never being violated — it's mostly a *consequence* of the
  other three ACID properties plus the declared constraints, not an independent mechanism of
  its own, and it has nothing to do with replica agreement.
- **Isolation** — concurrent transactions behave as if run one at a time, even while
  physically interleaved, at a chosen strength (Read Committed → Repeatable Read →
  Serializable, increasingly strict), enforced via locking (two-phase locking) or **MVCC**
  (multi-version concurrency control — Postgres's approach: keep multiple versions of a row
  so readers never block writers and vice versa).
- **Durability** — already fully covered: `fsync` + write-ahead log, [Part
  10](10_physics_of_persistence.md#fsync-the-physical-line-between-written-and-durable).

### The Join Tax

3NF's entire mechanism is decomposition — splitting one fact across many tables specifically
to guarantee it's stored once. The bill comes due at read time: reconstructing "one order,
with its customer, its line items, its product names" means **joining** several tables back
together — nested-loop, hash, or merge join, real CPU and I/O, multiplying with every
additional table involved. Distributed, it gets far worse: a join across shards living on
different machines means shipping data across the network mid-query — [Part 6/9's
distance-cost
argument](06_mechanical_sympathy_and_physics_of_latency.md#distance-of-data-one-physical-idea-two-different-scales)
applied to query execution itself, not just storage access. This is the exact trade
normalization makes, stated plainly: **integrity now, reconstruction cost later** — a
RUM-conjecture-shaped trade wearing a different name.

### Impedance Mismatch

The friction between how an application naturally models data — objects, nested structures,
inheritance, references — and the relational model's flat, tabular, set-based shape, which
has no native concept of either. Bridging the gap requires an **ORM** (Hibernate,
SQLAlchemy, ActiveRecord), itself a leaky abstraction (the **N+1 query problem** — silently
issuing one query per row instead of one query total — is the classic symptom). This
mismatch, not just scale, is one of the direct historical arguments *for* document
databases: a JSON-shaped document matches an application object's actual shape far more
closely than a normalized relational schema does, with no translation layer required at all.

### ~2005: Google and Amazon Hit the Wall — NoSQL Begins With Key-Value Stores

By the mid-2000s, Google and Amazon were operating at a scale where the relational model's
join-heavy, strongly-consistent, vertically-scaled default became the actual bottleneck, not
a convenience. Two papers mark the moment:

- **Google's Bigtable** (OSDI 2006) — a distributed, structured store built because
  relational engines of the era simply couldn't be sharded to the scale Google's crawl and
  index data required.
- **Amazon's Dynamo** (SOSP 2007) — built explicitly because a shopping cart has to always
  accept a write, even mid-partition; that requirement meant deliberately trading ACID's
  strong consistency for availability — a conscious CAP-theorem choice, not a compromise
  forced by ignorance. Dynamo is also the actual origin of [quorum reads/writes and
  consistent hashing](02_data_and_consistency.md#quorum-based-replication-n-w-r), both
  already documented elsewhere in this repo.

The first practical systems that followed — Riak, Voldemort, and later Cassandra
(explicitly merging Dynamo's distribution model with Bigtable's data model) — were
**key-value stores**: the simplest possible access pattern, chosen first precisely because
it discards both joins and rigid schema, the two things the relational model could no longer
deliver at that scale without becoming the bottleneck itself. **This is the whole doc's
thesis, playing out historically before it became a checklist**: forcing a join-heavy,
strongly-consistent, normalized model onto a workload that fundamentally needed massive
horizontal scale and always-on availability was fighting that workload's grain — exactly
like forcing random I/O onto a spinning disk — and the industry's answer wasn't "a better
relational database," it was naming that a *different* model fit that *different* shape,
which is the taxonomy this whole part exists to formalize.

## The Six Axes: What "First Principles" Actually Means Here

Six questions, asked *before* naming a technology, not after. Each one maps directly onto
mechanism already established in this repo — this part's job is turning that mechanism into
a decision procedure.

### 1. Access Pattern — How Is the Data Actually Queried?

The single most workload-defining question, and the one fashion-driven selection skips most
often. [Part 2's indexing section](02_data_and_consistency.md#indexing-why-databases-dont-scan-everything)
and [Part 10's B-tree/LSM-tree read paths](10_physics_of_persistence.md#b-trees-fully-unpacked-optimizing-for-reads-by-paying-on-writes)
already did the mechanical work here — this axis is about naming *which* pattern the actual
workload has:

| Pattern | What it means | Structure that fits |
|---|---|---|
| **Point lookup** (`GET key`) | Exact-match retrieval by a known key, no ordering needed | Hash index / pure key-value store — O(1), can't range-query, [Part 2](02_data_and_consistency.md#indexing-why-databases-dont-scan-everything) already names this trade-off |
| **Range scan** (`WHERE created_at BETWEEN X AND Y`) | Retrieval of a contiguous, ordered slice | B-tree or sorted LSM-tree — requires the data to be *kept* in sorted order, which a hash index structurally cannot provide |
| **Multi-predicate / relational** (joins, arbitrary `WHERE` clauses across columns) | Queries that weren't known in advance, spanning multiple entities | Relational (B-tree-backed) with a real query planner — the workload a bootcamp's "just use Postgres" default actually fits, when it fits at all |
| **Analytical scan / aggregation** (`SUM`, `GROUP BY` across millions of rows, few columns) | Reading most of a huge table, but only a handful of its columns | Columnar/OLAP (Parquet, ClickHouse, Snowflake) — [Part 10's scope note](10_physics_of_persistence.md#scope-note--a-third-camp-this-doc-doesnt-cover) already flags this as a third camp, neither B-tree nor LSM-tree |
| **Graph traversal** (multi-hop relationship queries) | "Friends of friends," recommendation paths, fraud rings | Graph database (Neo4j) — adjacency is the primary structure, not a foreign key join reconstructed per query |

**The question to actually ask**: *do I fetch by exact key, by range, by an arbitrary
predicate I can't predict in advance, by scanning most of the table for an aggregate, or by
walking relationships?* Naming this correctly eliminates most of the field before any other
axis is even considered.

### 2. Data Size — Does It Fit on One Machine, and Where in the Storage Hierarchy?

This is [Part 2's capacity problem](02_data_and_consistency.md#why-one-machine-stops-being-enough--two-different-problems)
stated as a question rather than a mechanism: past a certain volume, no single machine holds
or serves it all, and **sharding** becomes necessary — with all the added complexity of
cross-shard queries and rebalancing that a single-node system never has to solve. Just as
important, and more often skipped: **which storage tier does the working set actually need
to live in?** [Part 6's storage-economics
section](06_mechanical_sympathy_and_physics_of_latency.md#the-economics-of-machine-cost-is-physics)
already gave the numbers — RAM runs roughly ~100x pricier per GB than SSD, SSD roughly ~10x
pricier than cold/archival storage — so this axis is really asking: *is my hot working set
small enough to justify RAM's premium (Redis, Memcached), does it need SSD's random-access
speed at a moderate premium, or is most of this data touched rarely enough that cold/archive
tiers are the economically correct answer regardless of how "slow" that sounds in isolation?*

### 3. Latency Budget — What SLA Does Each Request Actually Need?

Every other axis is downstream of this one, because the latency budget determines which
tier of [Part 6's physical hierarchy](06_mechanical_sympathy_and_physics_of_latency.md#hardware-reality-the-abstraction-hides-the-physics-not-the-cost)
is even affordable:

- **Sub-millisecond, real-time** (ad bidding, a feature-flag check, a session lookup on
  every request) — the budget doesn't have room for a disk seek at all, let alone a network
  hop to a remote replica; this forces an in-memory store, and forces **synchronous**
  cross-replica consistency off the table entirely if any replica is more than a few
  milliseconds away ([Part 2's sync/async
  argument](02_data_and_consistency.md#sync-vs-async-replication-the-same-fsync-trade-off-at-cluster-scale)).
- **Tens of milliseconds, interactive** (a page load, an API response) — affords SSD-backed
  reads and same-region synchronous replication, but not a cross-continent round trip
  ([Part 9](09_dns_bgp_and_the_edge.md)'s geography numbers) inside the request path.
- **Seconds to minutes, batch/analytical** (a nightly aggregation, a dashboard refresh) — can
  afford columnar/cold-tier storage and cross-region or even cross-cloud data movement, since
  nothing in the request path is waiting synchronously on it.

**The question to actually ask**: *what's the p99 target for this specific access pattern,
and which physical tier from Part 6 can actually deliver that number* — not "what feels
fast enough," a number with an actual SLA behind it.

### 4. Consistency Model — What Does "Correct" Mean for This Data?

[Part 2's consistency spectrum](02_data_and_consistency.md#the-consistency-spectrum-its-not-just-strong-vs-eventual)
and [ACID vs. BASE](02_data_and_consistency.md#acid-vs-base) already name the options; this
axis is choosing among them deliberately rather than by default. A financial ledger cannot
tolerate a partially-applied transfer — it needs **strong consistency** and **ACID**, full
stop, and the throughput/scalability cost that comes with it is simply the price of
correctness. A social media like-counter can be wrong for a few seconds with zero
user-visible harm — **eventual consistency** and **BASE** aren't a compromise there, they're
the objectively correct choice, since paying for strong consistency would be pure waste.
**The question to actually ask**: *if two replicas of this data briefly disagree, what is
the actual, concrete cost — and is that cost closer to "a customer loses money" or "a UI
counter is off by one for a second"?*

### 5. Write Amplification — What Does This Workload Do to the Storage Engine's Write Path?

This axis is [Part 10's B-tree-vs-LSM-tree trade-off](10_physics_of_persistence.md#naming-the-trade-off-precisely-write-read-and-space-amplification)
applied as a filter, plus [Part 6's SSD write-amplification
tax](06_mechanical_sympathy_and_physics_of_latency.md#write-amplification-precisely-the-waf-formula)
stacked on top of it when the underlying medium is flash. A B-tree pays a random-access
write cost on every update (page rewrite, possible cascading splits) — fine for a
read-heavy, low-update workload, expensive for high-volume writes over an effectively random
keyspace. An LSM-tree defers that cost to background compaction, trading it for read
amplification instead. **Critically, these two amplification sources compound, not
substitute**: a B-tree engine's small random page rewrites, running on an SSD, are exactly
the access pattern that maximizes the SSD's *own* write amplification (scattered small
writes hit many different erase blocks instead of filling one sequentially) — so a
write-heavy, random-key workload on a B-tree-over-SSD stack pays both taxes at once. **The
question to actually ask**: *what's my read/write ratio, is the keyspace being written
effectively random or naturally clustered/sequential, and have I checked which storage
engine that shape actually favors — or picked one before asking?*

### 6. Failure Modes — What, Specifically, Has to Survive?

The axis most often skipped entirely, because "the database handles durability" is treated
as a single, monolithic guarantee rather than several genuinely different ones, each solved
by a different mechanism already covered in this repo:

| Failure class | What it means | Mechanism that actually protects against it |
|---|---|---|
| **Process/machine crash before a write is flushed** | The write was acknowledged but the in-memory structure holding it never made it to the main table | `fsync` + write-ahead log — [Part 10](10_physics_of_persistence.md#the-write-ahead-log-making-durability-affordable) |
| **Single disk/machine failure** | An entire physical copy of the data is gone | Replication — [Part 2](02_data_and_consistency.md#replication-distributed-truth-gfs-and-what-11-nines-actually-means) |
| **Silent bit-level corruption** | Data already durably written quietly goes wrong, with no crash and no error reported | Checksums (+ scrubbing, self-healing) — [Part 6](06_mechanical_sympathy_and_physics_of_latency.md#the-invisible-enemy-bit-rot-silent-data-corruption-and-checksums) |
| **Rack/datacenter failure** | An entire facility becomes unreachable | Multi-rack/multi-AZ replication (GFS's rack-spread, Azure ZRS) — [Part 2](02_data_and_consistency.md#gfs-2003-the-reference-architecture) |
| **Entire region failure** | A geographic region (natural disaster, major outage) goes down | Cross-region replication (Azure GRS, S3 cross-region replication) — [Part 2](02_data_and_consistency.md#cloud-analogs-s3-and-azure-grs) |
| **Human error** (bad migration, accidental `DROP TABLE`, bad deploy) | The data is technically "durable" and perfectly replicated — the *mistake* replicated too | Point-in-time recovery / backups — a genuinely separate mechanism from all of the above, since replication faithfully propagates a human mistake exactly as fast as it propagates a legitimate write |

**The question to actually ask**: *which of these six failure classes am I actually
defending against with this choice, and which am I implicitly assuming "the database
handles" without having verified it does?* Notice that no single mechanism covers every row
— a system can have a flawless WAL and full cross-region replication and *still* lose data
to an unbacked-up bad migration, because replication and backup are answering different
questions.

## The Anti-Pattern, Named Explicitly: Fashion-Driven Selection

Three concrete junior-level patterns, each traceable to skipping one specific axis above:

- **"I'll use MongoDB because it's what I know"** — for a workload that turns out to be
  highly relational, needing multi-table joins and cross-entity transactions. This skips
  **axis 1 (access pattern)**: the schema's actual shape was never checked against what the
  chosen engine is structurally good at.
- **"I'll use Postgres because it's the default"** — for a write-heavy, effectively-random-key
  time-series ingestion workload (device telemetry, event streams). This skips **axis 5
  (write amplification)**: it's [Part 10's worked
  example](10_physics_of_persistence.md#worked-example-the-same-workload-two-engines)
  almost exactly, the textbook case where a B-tree pays a random-write tax an LSM-tree
  simply doesn't.
- **"Everyone at [well-known company] uses this, so it must be safe"** — without checking
  whether that company's *scale*, *consistency needs*, or *failure tolerance* have anything
  in common with the system actually being built. A pattern that's correct at planet-scale,
  eventually-consistent, BASE-style throughput can be actively wrong for a small system that
  actually needed ACID correctness more than it needed that scale.

**The fix in one sentence**: run the six axes as an explicit checklist *before* naming a
technology — the technology choice should be the *last* step, a consequence of the six
answers, never the first.

## Worked Decision Framework: Four Scenarios Through the Six Axes

| Scenario | Access pattern | Data size | Latency budget | Consistency | Write shape | Dominant failure mode | Fits |
|---|---|---|---|---|---|---|---|
| **User session store** | Point lookup by session ID | Small, fits in RAM cluster-wide | Sub-millisecond | Eventual is fine — a stale session read is rarely consequential | Frequent overwrite, small values | Process/node crash (sessions are often acceptably ephemeral) | Redis / Memcached — in-memory, hash-indexed |
| **Financial ledger** | Point lookup + range scan (statement queries) + multi-row transactions | Moderate, single-region | Tens of ms, interactive | Strong — ACID, no partial transfers, ever | Moderate volume, not the bottleneck | All six failure classes matter, especially human error (backups non-negotiable) | Postgres / MySQL — B-tree, ACID, mature backup tooling |
| **IoT telemetry ingestion** | Append-heavy writes, range scan by timestamp | Very large, sharded | Writes: tens of ms; reads: batch-tolerant | Eventual — a delayed sensor reading is not the failure mode to design around | Extremely high volume, near-random device-ID keys | Disk/rack failure at scale (replication factor matters more than any single mechanism) | Cassandra / a wide-column LSM-tree store — [Part 10's textbook LSM case](10_physics_of_persistence.md#worked-example-the-same-workload-two-engines) |
| **Product catalog search / analytics dashboard** | Multi-predicate filtering + aggregation across millions of rows, few columns | Large, read-heavy | Seconds, batch-tolerant | Eventual, refreshed periodically | Write-rarely, bulk-loaded | Region failure (analytics is rarely the record-of-truth copy) | Columnar/OLAP (ClickHouse, Snowflake, Parquet-on-object-storage) — [Part 10's third camp](10_physics_of_persistence.md#scope-note--a-third-camp-this-doc-doesnt-cover) |

**Reading the table correctly**: the "Fits" column is never the starting point — it's what
*falls out* once the other six columns are answered honestly for the actual workload. Two
systems that look superficially similar ("we store records and query them") can land in
completely different rows once latency budget and write shape are actually specified.

## Designing and Operating From First Principles

1. Have I named my access pattern precisely (point lookup, range scan, multi-predicate,
   analytical scan, graph traversal) — or am I assuming "a database" handles all of them
   equally well?
2. Do I know whether my data fits comfortably on one machine, and which storage tier (RAM,
   SSD, cold/archive) my actual working set belongs in — or am I defaulting to whatever tier
   my chosen engine happens to use?
3. Have I stated an actual p99 latency number for this workload, and checked which physical
   tier from Part 6 can deliver it — or am I reasoning from a vague sense of "fast enough"?
4. Have I named, concretely, what happens if two replicas briefly disagree — and is that
   cost closer to "someone loses money" or "a counter is off by one" — before picking a
   consistency model?
5. Do I know my read/write ratio and whether my write keyspace is random or
   naturally-ordered — and have I checked whether that shape favors a B-tree or an LSM-tree,
   or picked an engine before asking?
6. Have I named which of the six failure classes (crash, disk, silent corruption, rack,
   region, human error) I'm actually defending against with this choice — and which ones
   I'm implicitly assuming are covered without verifying?
7. If my reason for choosing this technology is "it's what I know" or "it's popular" or
   "it's what my last company used," have I gone back and checked it against the six axes
   anyway — or let familiarity substitute for that check?
8. Am I confident the technology choice came *after* the six answers, not before them?

## Key Takeaways

- **Fashion-driven database selection** — "it's what I know," "it's popular," "it's what my
  last company used" — is a pattern that never references the actual workload at all, which
  is exactly what makes it fashion rather than engineering.
- **Every database embodies a trade-off**: this isn't a slogan, it's the literal content of
  the RUM conjecture, CAP theorem, and every sync-vs-async replication decision already
  covered in this repo — "best database" is incoherent without a specified workload.
- The six axes — **access pattern, data size, latency budget, consistency model, write
  amplification, failure modes** — are the checklist that turns "which database" from a
  fashion question into an engineering one, and each maps directly onto mechanism already
  established in Parts 2, 6, and 10.
- **Access pattern** (point lookup vs. range scan vs. multi-predicate vs. analytical scan
  vs. graph traversal) eliminates most of the field before any other axis is considered.
- **Data size and latency budget together** determine which physical storage tier (RAM,
  SSD, cold/archive) is even affordable, per Part 6's storage economics.
- **Consistency model** should be chosen by naming the concrete cost of two replicas briefly
  disagreeing — not defaulted to "strong" out of caution or "eventual" out of trend-chasing.
- **Write amplification** from the storage engine (B-tree vs. LSM-tree) and from the medium
  (SSD's own WAF) *compound*, not substitute — a write-heavy, random-key workload on a
  B-tree-over-SSD stack pays both taxes simultaneously.
- **Failure modes are six genuinely different classes**, each requiring its own named
  mechanism (WAL/fsync, replication, checksums, multi-rack/AZ spread, cross-region
  replication, backups) — no single guarantee covers all six, and human error specifically
  is not solved by replication at all, since replication faithfully propagates mistakes too.
- The technology name should always be the **last** step of the decision, a consequence of
  the six answers — never the first.

## Quick Self-Check

- Why is "which database is best" not a coherent question on its own — what has to be
  specified before it becomes answerable?
- A team picks MongoDB "because it's what we know," and the workload turns out to need
  multi-table joins and cross-entity transactions. Which of the six axes did that decision
  skip, and what would asking it first have surfaced?
- Why do a B-tree's write amplification and an SSD's own write amplification compound
  rather than substitute for a write-heavy, random-key workload — trace the mechanism from
  both Part 6 and Part 10.
- Name a concrete workload where strong consistency is clearly correct, and one where it's
  clearly wasteful — what's the actual test that separates the two cases?
- Why doesn't cross-region replication protect against a human accidentally dropping a
  table — what failure class does it protect against instead, and what mechanism actually
  covers the human-error case?
- For the "IoT telemetry ingestion" scenario in the worked table, name which specific axis
  answer is the one that rules out a B-tree engine most decisively.

## Articulate It: Interview Framing & Vocabulary

### Three Ways to Explain This

- **Six-axes framing (the default for any "which database would you use" question):** "I
  wouldn't name a technology first — I'd walk the access pattern, data size, latency
  budget, consistency needs, write shape, and failure modes this workload actually has, and
  let the technology fall out of those answers. Naming a database before that is picking by
  fashion, not engineering, and it's a pattern I actively try to avoid."
- **Compounding-cost framing (good for a storage-engine-choice deep-dive):** "Write
  amplification isn't one number — a B-tree's random page rewrites and an SSD's own erase-
  block garbage collection are two separate amplification sources that compound on a
  write-heavy, random-key workload. I'd check both before assuming 'the database handles
  it.'"
- **Failure-class framing (good for a durability/DR question):** "I'd separate 'durable'
  into the specific failure classes it needs to survive — process crash, disk failure,
  silent corruption, rack failure, region failure, human error — because each one has a
  genuinely different mechanism behind it, and a system can be airtight on five of them and
  still lose data on the sixth if nobody named it explicitly."

### Vocabulary Builder

**Technical shorthand — use these instead of over-explaining the concept every time:**

- **fashion-driven selection** (n. phrase) — choosing a technology by familiarity or
  popularity rather than by the workload's actual requirements; the anti-pattern this whole
  doc is named against.
- **the six axes** (n. phrase) — access pattern, data size, latency budget, consistency
  model, write amplification, failure modes; the first-principles checklist that should
  precede any storage technology choice.
- **access pattern** (n. phrase) — the shape of how data is actually queried (point lookup,
  range scan, multi-predicate, analytical scan, graph traversal); the single most
  workload-defining axis.
- **compounding amplification** (n. phrase) — when a storage engine's own write
  amplification (e.g., a B-tree's page rewrites) stacks on top of the underlying medium's
  amplification (e.g., an SSD's WAF), rather than one substituting for the other.
- **failure class** (n. phrase) — one of the six genuinely distinct ways data can be lost or
  corrupted (crash, disk, silent corruption, rack, region, human error), each requiring its
  own named defense rather than one being assumed to cover all.

**Expressive phrases — for stating a trade-off fluently instead of listing pros/cons:**

- **"…the technology name should be the last step, not the first"** — a compact way to
  argue for axis-first reasoning over familiarity-first reasoning in any storage-choice
  discussion.
- **"…every database embodies a trade-off"** — a reusable line for pushing back on "just
  tell me the best database," redirecting toward "best for which workload."
- **"…replication propagates mistakes exactly as faithfully as it propagates legitimate
  writes"** — a precise way to explain why backups and replication solve different
  problems, not overlapping ones.

---

**Previous:** [Part 10: The Physics of Persistence (B-Trees vs. LSM-Trees)](10_physics_of_persistence.md)  |  **Next:** [0. The Interview Framework](../00_interview_framework/00_interview_framework.md)
