# SQS — First Principles & Internal Architecture

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> *Convention:* claims tagged **[Documented]** (AWS docs / re:Invent / patents / papers) or **[Inferred]** (reconstruction from behavior). Hold Inferred loosely.

## 1. Why SQS exists

**[Documented]** SQS launched in **2004** — AWS's first-ever public service, a year before EC2 or S3. The problem it solved predates "cloud": in a distributed system, if Service A calls Service B directly (synchronously), A is now coupled to B's uptime, latency, and capacity. If B is slow or down, A either blocks or fails.

Before message queues were commoditized, teams either:
- built their own queueing layer on top of a database (a table with a `status` column, polled — fragile, doesn't scale, lock contention), or
- ran self-managed message brokers (early RabbitMQ/ActiveMQ/MSMQ) — meaning *you* own patching, HA, and failover for the broker itself.

SQS's pitch: a **fully managed, serverless, pull-based queue** — no server to provision, no broker to patch, scales from zero to massive throughput without touching a dial.

## 2. The mental model

Think of SQS as a **shared inbox tray between two teams that never talk to each other directly.** Team A (producer) drops letters in the tray and walks away — doesn't care who picks them up or when. Team B (consumer) checks the tray whenever it's ready, grabs a letter, and only throws it away once the job described in the letter is actually done. If Team B disappears mid-task, the letter reappears in the tray for someone else to grab.

Core value: **temporal decoupling** (producer and consumer don't need to be online at the same time) and **load leveling** (a burst of 10,000 requests doesn't crash your database — it just sits in the tray until workers catch up).

## 3. Core technology & internal architecture

**[Documented]** SQS stores each message **redundantly across multiple servers within a region**, spread across its underlying storage/compute fleet, so no single server or disk failure loses your message. There is no dedicated broker node you provision — the "queue" is a logical namespace, not a physical machine.

**[Inferred]** AWS has never published a Physalia-style deep internals paper for SQS the way it has for EBS/DynamoDB. What's understood from behavior + re:Invent talks: SQS was built as a **highly available, horizontally distributed key-value-ish store** underneath — every message is essentially a blob with metadata (receipt handle, visibility deadline, retry count) replicated across multiple storage nodes, with the queue's "position" tracked in a way that favors **availability over strict ordering** for the Standard queue type. This is a direct application of the **CAP theorem** trade-off: SQS Standard chooses **AP** (available + partition-tolerant, weak/eventual consistency on ordering and count), while SQS FIFO gives up some of that availability/throughput headroom to buy **ordering + exactly-once processing** per message group.

**Why this matters practically:** `ApproximateNumberOfMessagesVisible` has "Approximate" in its name for a reason — the count is an **eventually consistent estimate** across the distributed backend, not a live transaction count. Don't build logic that depends on it being exact.

## 4. Message lifecycle

1. **Send** — producer calls `SendMessage`. Message becomes durable and visible.
2. **Receive** — consumer calls `ReceiveMessage`. The message isn't deleted — it becomes **invisible** to other consumers for the duration of the **Visibility Timeout** (default 30s). This is the mechanism that gives at-least-once delivery: if the consumer crashes before finishing, the message reappears automatically.
3. **Process** — consumer does the actual work.
4. **Delete** — consumer calls `DeleteMessage` using the **receipt handle** (a one-time token from that specific receive, not the message ID) once processing succeeded.

If the consumer never deletes it (crash, timeout too short, bug): the message becomes visible again after the timeout expires → gets redelivered → **consumers must be idempotent**. SQS Standard guarantees *at-least-once* delivery, not *exactly-once* — duplicate processing is normal, not an edge case.

**Long polling vs short polling:** short polling (`WaitTimeSeconds=0`) returns immediately even if the queue is empty — wasteful, and can miss messages spread across the backend (returns from a random subset of servers). **Long polling** (`WaitTimeSeconds` up to 20s) waits for a message to arrive before responding — fewer empty responses, lower cost, more complete results. **Always use long polling in production.**

## 5. Standard vs FIFO — the fundamental trade-off

| | Standard | FIFO |
|---|---|---|
| Ordering | Best-effort, **not guaranteed** | Strict, per **Message Group ID** |
| Delivery | At-least-once (duplicates possible) | Exactly-once processing (dedup window: 5 min) |
| Throughput | Effectively unlimited, scales horizontally | Up to 3,000 msg/sec per API call with batching (High Throughput mode), or 300/sec without |
| Use when | Order doesn't matter, max scale needed (logging, metrics, generic task queue) | Order matters within a key (per-customer event sequence, financial transactions) |

**Default to Standard** unless you have a specific ordering/dedup requirement — FIFO's throughput ceiling and added complexity (message group IDs, dedup IDs) aren't free.

## 6. Limits every architect hits eventually

- **Message size:** 256 KB max. For larger payloads, use the **Extended Client Library** — send the actual payload to S3, put a pointer message in SQS. Don't chunk large payloads manually.
- **Retention:** 1 minute to 14 days (default 4 days). After that, unprocessed messages are gone — silently. This is why DLQ + monitoring matters (see [monitoring-alarms.md](monitoring-alarms.md)).
- **Visibility timeout ceiling:** 12 hours max. If a job legitimately takes longer, periodically call `ChangeMessageVisibility` to extend it, or rethink the job granularity.
- **In-flight message limits:** Standard queues cap at ~120,000 in-flight (received-but-not-deleted) messages; FIFO caps at 20,000. Hitting this means consumers aren't keeping up or aren't deleting properly.

## 7. Core architecture patterns

- **Decoupling / buffering:** web tier accepts a request instantly, drops a message, returns 200 — actual work happens async via a worker fleet. Protects downstream systems (DB, third-party API) from traffic spikes.
- **Fan-out:** SNS → multiple SQS queues (each subscriber gets its own copy) — the standard pub/sub pattern, since SQS itself is strictly point-to-point/competing-consumers, not broadcast.
- **Work queue / competing consumers:** many worker instances all poll the same queue; SQS's invisibility mechanism ensures each message goes to exactly one worker at a time — natural horizontal scaling, just add more workers.
- **Dead Letter Queue (DLQ):** after `maxReceiveCount` failed attempts, the message is automatically moved to a DLQ instead of retrying forever — isolates "poison pill" messages so they don't block the rest of the queue. See [monitoring-alarms.md §7](monitoring-alarms.md).
- **Delay queues:** hold a message invisible for up to 15 minutes before it's even eligible for the first receive — used for scheduled/deferred work.
- **Event-driven compute:** Lambda's **event source mapping** polls SQS internally (long-polling on your behalf) and invokes your function with a batch — most serverless SQS consumers are built this way today, no polling code needed.
- **Autoscaling workers:** Application Auto Scaling can scale an EC2/ECS worker fleet using `ApproximateNumberOfMessagesVisible` as the custom scaling metric — ties directly to the alarms doc.

## 8. Security basics

- **IAM policies** control who can `SendMessage`/`ReceiveMessage`/`DeleteMessage` — least privilege per action, not just per queue.
- **Queue policies** (resource-based) allow cross-account access (e.g., another account's S3 bucket notifications writing into your queue).
- **Encryption:** SSE-SQS (AWS-owned key, free) or SSE-KMS (your CMK, auditable via CloudTrail, costs per API call) — encrypts message body at rest.
- **VPC endpoints:** traffic to SQS can stay off the public internet via an interface VPC endpoint (PrivateLink) — relevant in a private subnet with no NAT.

## 9. How this fits the bigger picture

| If you need... | Reach for... |
|---|---|
| Simple point-to-point task queue, at-least-once, huge scale | **SQS Standard** |
| Strict per-key ordering + no duplicate processing | **SQS FIFO** |
| One event → many independent subscribers | **SNS fan-out to SQS** |
| Replayable ordered stream, multiple consumers reading independently, retention-based (not delete-on-read) | **Kinesis Data Streams** |
| Complex event routing/filtering across many AWS services and SaaS | **EventBridge** |

The single most common architect mistake: reaching for Kinesis or a custom Kafka setup when a plain SQS queue would've done the job with a fraction of the operational overhead — SQS is almost always the right *default* for "decouple these two things," upgrading only when a concrete requirement (ordering, replay, fan-out) demands it.

## 10. What SQS is similar to (technology comparison)

| Technology | How it maps to SQS | Key difference |
|---|---|---|
| **RabbitMQ** | Closest self-hosted analog — a broker holding messages for consumers to pull, with ack/nack semantics similar to visibility timeout + delete. | You run/patch/scale the broker yourself; RabbitMQ supports richer routing (exchanges/topics) SQS doesn't natively do. |
| **Apache Kafka** | Both handle high-throughput async messaging. | Kafka is a **log** (messages persist, multiple consumers replay independently by tracking their own offset); SQS **deletes** a message once consumed — no replay. Kafka needs cluster ops (brokers, partitions, ZooKeeper/KRaft); SQS is serverless. |
| **Redis Lists / Streams** | `LPUSH`/`BRPOP` as a queue, or Redis Streams with consumer groups (`XREADGROUP`/`XCLAIM` ~ visibility timeout). | Redis durability depends on your persistence config; you own HA/failover. |
| **A database table used as a queue** (`status = 'pending'`, polled) | Exactly the pattern SQS was built to replace. | Polling a DB for pending rows causes lock contention and doesn't scale; SQS externalizes this into a managed distributed store. |
| **Kubernetes Job queue / work-queue pattern** | Same "competing consumers" idea — pods pull work items and mark them done. | K8s has no native durable message store; SQS/Kafka/Redis usually sit *behind* the pods for exactly this reason. |
| **Azure Service Bus** | Direct managed-cloud equivalent — queues with dead-lettering, sessions (~FIFO groups). | Different pricing/API, same conceptual slot. |
| **GCP Pub/Sub** | Direct managed-cloud equivalent, architecturally closer to pub/sub-first (like SNS+SQS combined) — fan-out is native, no separate "SNS" needed. | Push or pull delivery both native; ordering keys ~ FIFO message groups. |

**One-line summary:** if your stack has RabbitMQ or a DB-polling queue, SQS is the "don't operate this yourself" version of that. Kafka is *not* a drop-in replacement — its replay/log model is a different guarantee SQS deliberately doesn't offer.

## 11. Open-source alternatives to SQS itself (not just "a queue in general")

These specifically try to replicate **SQS's own API/semantics** (Standard + FIFO), as opposed to being a different kind of queue you'd migrate to:

- **[Documented] ElasticMQ** — an open-source server that implements the actual SQS REST API (including FIFO queue behavior, message groups, dedup IDs). Existing SQS SDK code points at it by just changing the endpoint URL. Mostly used for local dev/CI, but some teams run it self-hosted in production when they need SQS semantics without AWS. You still own uptime, scaling, and durability config yourself — the "no ops" value prop of real SQS is gone.
- **[Documented] LocalStack** — emulates SQS (and dozens of other AWS services) for local development/testing. Same caveat: dev/test tool, not a production message broker.
- **[Documented] goaws** — a smaller Go-based fake SQS/SNS server, similar niche to ElasticMQ (lighter weight, less complete FIFO support).
- **[Inferred] Apache Pulsar** — not an SQS clone, but the closest **architectural parallel** for the Standard-vs-FIFO split: Pulsar's **Shared subscription** (any available consumer takes the next message, at-least-once) mirrors SQS Standard's competing-consumers model, while its **Key_Shared subscription** (strict ordering per key, routed to one consumer per key) mirrors FIFO's per-Message-Group-ID ordering. If you want a self-hosted system with a *native* concept of "unordered scalable" and "ordered per key" living side by side, Pulsar is the production-grade candidate — but it's a different API entirely, not a drop-in.
- **RabbitMQ (quorum queues) / NATS JetStream** — can approximate SQS's durability and redelivery guarantees with configuration (quorum queues for replication, JetStream work-queue consumers for competing-consumer semantics), but neither has a first-class FIFO-per-key concept as clean as Pulsar's Key_Shared or SQS FIFO's message groups.

**Bottom line:** if you need API-compatibility (so existing SQS client code just works), **ElasticMQ** is the answer, with the understanding that you've traded "managed service" for "one more stateful system to operate." If you need the *conceptual* pairing of Standard+FIFO in a self-hosted system built for that from scratch, **Apache Pulsar** is the closest fit, at the cost of adopting a different API/operational model entirely.

---

## Not yet covered (candidates for future modules)
- Deep networking / packet flow specifics for SQS API calls.
- Cost model deep-dive (request pricing, batching economics, data transfer).
- Production case studies (real company architectures using SQS at scale).
- Debugging/troubleshooting guide (stuck consumers, poison messages, throughput ceilings).
- Interview Q&A (junior→principal).
