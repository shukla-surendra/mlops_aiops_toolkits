# EBS — Interview preparation

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> Spec section 15. Answers = what an interviewer wants to hear. Say them out loud.

---

## Junior
**Q. EBS vs instance store?** EBS = network-attached, durable, survives the instance, detach/snapshot/resize. Instance store = local physical disk, ephemeral (lost on stop/terminate), fastest, no snapshots. Use EBS for anything you keep.

**Q. Volume types, one line each?** gp3 = default SSD (provision IOPS/throughput independent of size); io2/Block Express = high-IOPS/sub-ms DBs, 99.999%; st1 = throughput HDD (logs/big-data); sc1 = cold HDD.

**Q. What's a snapshot?** Incremental, block-level backup to S3 (multi-AZ durable); first is full, rest copy only changed blocks.

## Senior
**Q. Why is EBS single-AZ?** Replicas live in one AZ; AWS trades cross-AZ durability for low, consistent write latency (cross-AZ sync would add ms/write). You get cross-AZ/Region durability via snapshots (S3) or app replication.

**Q. Explain the "network disk" model and one consequence.** Blocks live on a remote storage fleet; Nitro presents them as NVMe. Consequence: every I/O is a network round trip → latency > instance store, and the volume outlives the instance.

**Q. gp3 vs gp2?** gp2 ties IOPS to size (3/GB) + burst bucket → cliffs. gp3 decouples IOPS/throughput from size, is cheaper, and has flat (no-burst) performance. Migrate gp2→gp3.

**Q. Multi-Attach — what does it and doesn't it give you?** Shared *block* access to one io2 volume from up to 16 instances in one AZ. NOT a shared filesystem — needs a cluster-aware FS or you corrupt data. For shared files across AZs, use EFS.

**Q. Encryption?** AES-256 on the Nitro card (line-rate), envelope encryption (per-volume DEK wrapped by a KMS key), covers at-rest + in-transit + snapshots + derived volumes. Delete the KMS key → data gone.

## Principal / architecture
**Q. Design the control plane that tracks which servers hold each volume's replicas.** This is Physalia: millions of tiny Paxos-replicated databases (one per small volume group), colocated near the data they describe to shrink blast radius, so a partition takes out a few cells, not the Region. Contrast with one big DB (single blast radius). Reference the 2011 re-mirroring-storm outage as motivation.

**Q. How would you build durable block storage for a fleet?** In-AZ synchronous replication (ack after replicas durable), re-mirror on failure with **rate limiting** (avoid thundering-herd storms), a consensus-based placement/leadership control plane with contained blast radius, offload the data path to hardware (Nitro), and back up to a separate multi-AZ store (S3 snapshots) for the AZ-failure case.

**Q. EBS vs EFS vs S3 vs instance store — pick for a workload.** Block single-attach durable = EBS; shared POSIX multi-AZ = EFS; object/HTTP/11-nines = S3; ultra-low-latency ephemeral scratch = instance store.

## Scenario
**Q. "Our DB volume is slow."** Check instance EBS ceiling vs volume, burst balance (gp2), provisioned vs consumed (io2), queue length/parallelism, I/O size, and whether it's freshly restored (lazy-load). Fix the actual bottleneck; often it's the instance size or gp2 burst.

**Q. "Make this single-AZ EBS DB survive a Region outage."** DLM snapshots → cross-Region copy → pre-baked AMIs + IaC for rebuild → optionally app-level cross-Region replica for low RPO. State RPO/RTO per tier.

**Q. "Cut our EBS bill."** gp2→gp3, right-size provisioned IOPS, delete orphaned volumes/snapshots, check forgotten FSR, thin-provision via Elastic Volumes, archive cold snapshots.

## Incident
**Q. "A whole AZ's volumes went unavailable and recovery made it worse."** Classic re-mirroring storm (2011): correlated failure + unbounded automatic recovery = thundering herd exhausting capacity. Mitigation lessons: rate-limit recovery, contain control-plane blast radius (Physalia), and don't treat a volume as Region-durable.

**Q. "Encrypted volumes across the fleet suddenly can't attach."** Suspect the shared KMS key: disabled, scheduled for deletion, or a key-policy/grant change removed `Decrypt`. Check CloudTrail for `DisableKey`/`ScheduleKeyDeletion`/policy edits.

---

## Rapid-fire
- Volume = network storage impersonating a local NVMe disk (via Nitro).
- Single-AZ replicas; snapshots (S3) = your multi-AZ/Region durability.
- gp3 default; io2 Block Express for DBs; st1 throughput; sc1 cold.
- IOPS × I/O size ≈ throughput; need queue depth to hit high IOPS.
- Perf = min(volume provisioned, instance EBS ceiling).
- Multi-Attach = shared block, not shared FS. EFS for shared files.
- Encryption = Nitro AES-256, envelope via KMS; key deletion = data loss.
- Physalia = tiny-Paxos control plane; 2011 outage = re-mirroring storm.

---

## Self-check
Answer any 3 Principal/scenario/incident questions out loud in <90s each without reading. Stalls → the doc to revisit.
