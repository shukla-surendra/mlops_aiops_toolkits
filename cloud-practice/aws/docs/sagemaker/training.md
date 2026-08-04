# SageMaker — Training & processing

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md) (jobs are ephemeral managed clusters).

Spec sections 3, 5, 7 for the training path. The mental frame: **a training job is a disposable GPU cluster that reads S3, runs your container, and writes a model to S3.** Everything here is about feeding it data efficiently, scaling it, and not overpaying.

---

## 1. Job types
- **Training job** — runs your training container; outputs a model artifact to S3.
- **Processing job** — same ephemeral-cluster idea for **data prep / feature engineering / model evaluation / batch scoring** (scikit-learn, Spark, or BYOC). Keeps prep reproducible and off your notebook.
- **Hyperparameter tuning (HPO) job** — launches many training jobs to search hyperparameters (Bayesian or random), optimizing a target metric.
- **Batch Transform** — offline inference (covered in [inference.md](inference.md)).

## 2. Getting data in — the input modes [Documented]
This is where training performance is won or lost:
- **File mode (default)** — SageMaker **downloads the whole dataset** to the instance's local EBS/NVMe before training starts. Simple; slow start for big data; needs enough local disk.
- **Pipe mode** — **streams** data from S3 directly into the training process (no full download). Faster start, less disk, good for large sequential datasets. Your framework must read the stream.
- **FastFile mode** — **lazy, POSIX-like streaming**: files appear as a local filesystem but blocks are fetched on demand. Best of both for many workloads; the modern default for large S3 datasets.
- **EFS / FSx for Lustre** — mount a shared filesystem for very large or repeatedly-used datasets. **FSx for Lustre (S3-linked)** is the HPC choice: massive parallel throughput, backed by S3 (ties to your [EFS/FSx](../efs/README.md) study). Removes the per-job download cost when you train repeatedly on the same big corpus.

**Rule:** small data → File; big/streaming → FastFile or Pipe; huge + reused → FSx for Lustre.

## 3. Distributed training [Documented]
For models/data too big for one GPU/instance:
- **Data parallelism** — replicate the model across GPUs, split the batch; gradients all-reduced. SageMaker's **Distributed Data Parallel (SMDDP)** optimizes all-reduce for AWS networking; or use PyTorch DDP/`torchrun`.
- **Model parallelism** — split the *model* across GPUs when it doesn't fit (SageMaker **Model Parallel** library, tensor/pipeline parallelism) — needed for large models/LLMs.
- SageMaker sets up the **multi-node cluster + networking + env vars** (`WORLD_SIZE`, rank, master addr); your script uses them. Choose instances with fast interconnect (e.g., **EFA** — Elastic Fabric Adapter — for low-latency GPU-to-GPU across nodes).

## 4. Managed Spot training — the big cost lever [Documented]
- Run training on **Spot instances** (up to ~90% cheaper) with **`use_spot_instances=True`** + a **checkpoint S3 path**. If Spot reclaims the instance, SageMaker resumes from the last checkpoint.
- Trade: possible interruptions → longer wall-clock. Almost always worth it for long training; make your script **checkpoint regularly** to S3.
- **Warm Pools** keep provisioned clusters alive between jobs to cut the minutes of cold-start when iterating (you pay for the kept-warm time).

## 5. Hyperparameter tuning (HPO) [Documented]
- A tuning job runs N training jobs exploring the search space, maximizing/minimizing an **objective metric** it scrapes from your logs.
- **Strategies:** Bayesian (smart, default), Random, Grid, Hyperband (early-stops bad trials — cheaper). Set `max_jobs` + `max_parallel_jobs` (parallelism vs Bayesian learning tradeoff).
- Define **hyperparameter ranges** + the **metric regex**. Warm-start from a prior tuning job to save cost.

## 6. Script mode vs BYOC [Documented]
- **Script mode** — use an AWS **framework container** (PyTorch/TF/XGBoost/HuggingFace/scikit-learn) and pass your `train.py` (+ `requirements.txt`). 90% of cases. The container calls your script with the standard `/opt/ml` paths.
- **BYOC** — build your own Docker image (custom deps, exotic frameworks). More control, more maintenance. Follow the container contract (`/opt/ml/...`, exit codes, `/opt/ml/output/failure`).
- **Extend a framework container** — middle ground: start from AWS's image, add layers.

## 7. Instance selection (train)
- **GPU** families for deep learning (`ml.g5`, `ml.p4d/p5` for large-scale) — match to model size + interconnect needs (EFA for multi-node).
- **CPU** (`ml.c5/m5`) for classic ML (XGBoost, sklearn).
- Right-size: more/bigger GPUs finish faster but cost more per hour — optimize **total cost = $/hr × hours**, and Spot slashes the $/hr.

---

## Sources
- AWS docs: *Access training data (File/Pipe/FastFile)*, *Distributed training*, *Managed Spot Training & checkpoints*, *Automatic Model Tuning*, *Use your own training algorithms*.
- Libraries: `sagemaker` Python SDK; SMDDP / SMP; FSx for Lustre + S3.

---

## Self-check
1. You train repeatedly on the same 5 TB dataset; per-job File-mode download dominates wall-clock. What two data options fix this and how?
2. Explain data vs model parallelism and when you're forced into the latter.
3. How does Managed Spot training stay correct across interruptions, and what must your script do?
4. In an HPO job, what determines "which trial won," and which strategy early-stops bad trials to save money?
5. When is BYOC justified over script mode, and what contract must the image honor?
