# Zookeeper / ClickHouse Keeper

**Category:** distributed coordination service

## What it is

**Apache ZooKeeper** is a general-purpose distributed coordination service — it exists to
solve the problems that come up whenever multiple nodes in a cluster need to agree on
something: who's the leader, what's the current state, who owns which shard. Originated at
Yahoo. It uses **ZAB (ZooKeeper Atomic Broadcast)**, its own consensus protocol, to keep a
small shared tree of data consistent and available across a cluster of ZooKeeper nodes
(verified via Wikipedia; not independently confirmed from zookeeper.apache.org's own
docs). Historically used by many distributed systems for this role, including Kafka
(pre-KRaft) and Hadoop, and — relevant here — [ClickHouse](../clickhouse/README.md).

**ClickHouse Keeper** is ClickHouse's own C++ reimplementation of the same job: it
implements the ZooKeeper wire protocol/API, so anything that speaks to ZooKeeper can speak
to it unchanged, but internally it uses the **RAFT** consensus protocol instead of ZAB, and
ships built into ClickHouse itself rather than as a separate JVM-based service.

## Why a ClickHouse cluster needs one of these at all

A [ClickHouse](../clickhouse/README.md) cluster using `ReplicatedMergeTree` tables has
multiple replicas that can each accept writes. Something outside any single replica needs
to track "what data exists, in what order, and which replicas have it" so that replicas
converge on the same state instead of diverging. That's the coordination role — ZooKeeper
or ClickHouse Keeper is the source of truth for replication metadata, not for the actual
row data itself (which stays in ClickHouse).

## ZooKeeper vs. ClickHouse Keeper — which to run

ClickHouse's own documentation now recommends **ClickHouse Keeper** over standalone
ZooKeeper for new deployments — verified from ClickHouse's docs. The practical reasons:

- **One less system to operate** — no separate JVM-based ZooKeeper cluster to deploy,
  monitor, and upgrade independently of ClickHouse itself.
- **Same protocol compatibility** — because Keeper implements ZooKeeper's own wire
  protocol, migration between the two is a config change, not a data-format change.
- **Different consensus algorithm underneath** — RAFT (Keeper) vs. ZAB (ZooKeeper); this is
  an implementation detail for most users, not something application code interacts with
  directly.

**Gotcha, verified from ClickHouse's docs:** ZooKeeper nodes and ClickHouse Keeper nodes
**cannot be mixed within a single cluster** — the interserver protocols are not
compatible with each other, so a cluster runs either all-ZooKeeper or all-Keeper, never
both at once.

## Related

- [ClickHouse](../clickhouse/README.md) — the database whose replication this
  coordinates.
- [SigNoz](../signoz/README.md) — the observability platform whose backend
  ([ClickHouse](../clickhouse/README.md)) this piece supports.
