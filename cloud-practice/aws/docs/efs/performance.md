# EFS — Performance & modes

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md).

Spec section 7. EFS performance has **two independent knobs**: a **performance mode** (latency vs parallelism) and a **throughput mode** (how MB/s is provisioned). Plus the ever-present reality: it's a network filesystem, so **per-op latency and small-file/metadata workloads are the weak spot**.

---

## 1. Performance modes [Documented]

- **General Purpose (default, recommended):** lowest per-operation latency; supports a very high but bounded rate of operations/sec. Right for ~all workloads (web content, containers, CMS, home dirs, dev).
- **Max I/O (legacy):** higher aggregate parallel throughput/ops at the cost of **higher per-op latency**. Historically for massively parallel workloads (thousands of clients). **AWS now steers you to General Purpose + Elastic throughput** instead; Max I/O is rarely the right pick on modern EFS.

Watch the **`PercentIOLimit`** CloudWatch metric on General Purpose — near 100% means you're hitting the ops/sec ceiling (rare; consider redesign before Max I/O).

## 2. Throughput modes [Documented]

- **Elastic (recommended default):** throughput **scales automatically** up and down with demand; you **pay per GB transferred**. No planning, no burst cliffs. Best for spiky/unpredictable workloads — which is most of them.
- **Bursting:** throughput **scales with filesystem size** (baseline ∝ GB stored) and uses a **burst-credit** bucket to exceed baseline for a while. A **small** filesystem has **low baseline throughput** — the classic "my new empty EFS is slow" surprise. Watch **`BurstCreditBalance`**; near 0 = throttled to baseline.
- **Provisioned:** you **set a fixed MB/s** independent of size and pay for it — for when you need guaranteed high throughput on a small dataset.

Rule of thumb: **use Elastic** unless you have a steady, predictable, large workload where Bursting/Provisioned is cheaper.

## 3. The latency reality (and how to work with it)

- EFS is a **network filesystem**: expect **single-digit-millisecond** latency per operation (higher than EBS's sub-ms/low-ms). Sequential large-file throughput is excellent; **tiny-file and metadata-heavy** workloads (millions of small files, `find`/`ls -R`, git checkouts, `node_modules`) are where the per-op latency compounds. [Documented characteristic]
- **Mitigations:**
  - **Parallelism** — EFS throughput is aggregate; drive many concurrent files/clients rather than one serial stream (`cp` is slow; `rsync`/GNU `parallel`/many workers are fast).
  - **Larger I/O sizes** — bigger reads/writes amortize per-op cost.
  - **Right mount options** — `amazon-efs-utils` defaults are tuned; avoid tiny `rsize`/`wsize`.
  - **Cache locally** where possible for read-mostly hot sets.
  - **Don't use EFS for a transactional DB** — that's EBS io2. Use EFS for shared *files*, not shared *database pages*.

## 4. Storage classes and their performance/cost tradeoff [Documented]

- **Standard** — multi-AZ, hot data.
- **Standard-IA (Infrequent Access)** — much cheaper storage, but a **per-GB retrieval charge** and slightly higher first-byte latency; **Lifecycle Management** moves files here after N days idle.
- **Archive** — cheapest, for rarely-accessed data, higher retrieval latency/cost.
- **One Zone** variants — single-AZ versions of the above at lower storage price.

**Intelligent-Tiering / Lifecycle Management** automatically moves files between Standard and IA/Archive based on access — big savings for datasets with a cold tail, with the caveat that a sudden scan of cold data incurs retrieval charges/latency. See [best-practices.md](best-practices.md).

---

## Sources
- AWS docs: *Amazon EFS performance*, *Throughput modes*, *Performance modes*, *EFS CloudWatch metrics*, *EFS storage classes & lifecycle management*.

---

## Self-check
1. A brand-new, nearly-empty EFS (Bursting mode) is slow. Explain why and name the metric + the mode change that fixes it.
2. You have spiky, unpredictable throughput needs. Which throughput mode, and why?
3. A CI job doing a git checkout of a repo with 200k tiny files is painfully slow on EFS. Why, and what two mitigations help most?
4. When would you deliberately choose Provisioned over Elastic throughput?
5. Your storage bill is high but most files are untouched for months. What feature addresses this and what's its one gotcha?
