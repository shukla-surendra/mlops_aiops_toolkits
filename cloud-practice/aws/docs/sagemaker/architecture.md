# SageMaker — Module 1: Why it exists, the mental model, and the internal architecture

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Epistemics:** **[Documented]** = AWS docs / re:Invent · **[Inferred]** = reconstruction from behavior + standard designs.

**Scope:** spec sections 1–3. Why SageMaker exists, the mental model, and the internal architecture (control/data plane, component map, how a training job and an endpoint physically run, the container contract).

---

## 1. Why does SageMaker exist?

### The problem in one sentence
Turning a model from a notebook into a **trained, deployed, monitored, reproducible production system** requires enormous *undifferentiated* infrastructure work — GPU clusters, data pipelines, distributed training, model serving at scale, autoscaling, monitoring, lineage — none of which is "the model."

### History: how ML was done before
- **On-prem:** buy a GPU box/cluster, run Jupyter on it, train by hand, serve with a hand-rolled Flask app behind a load balancer. No reproducibility, no lineage, ops nightmare.
- **Early cloud:** raw **EC2 GPU instances** — you still provision, install CUDA/drivers, babysit training, build your own serving/scaling. Frameworks (TensorFlow, PyTorch, XGBoost) solved *modeling* but left *infrastructure and lifecycle* to you.
- The result: 80–90% of the effort was plumbing, and every team rebuilt the same MLOps wheel.

### Why AWS built SageMaker (2017)
A **managed platform for the whole ML lifecycle** — prepare data, build, train, tune, deploy, monitor, govern — so teams ship models instead of managing GPU fleets. It's the "RDS moment" for ML: the heavy lifting becomes a managed service you drive by API.

### What if it didn't exist?
You'd do **DIY MLOps on EC2/EKS** — Kubeflow/Ray/Argo, custom training orchestration, DIY HPO, a serving stack, Prometheus/Grafana, and a home-grown model registry. Many teams still do (and it's valid), but they're re-implementing what SageMaker provides as managed primitives.

---

## 2. The core mental model

> **SageMaker is not one product — it's a suite of managed capabilities stitched together by a control plane, organized around the ML lifecycle. The core primitive is: "hand SageMaker a container + a pointer to data in S3 + an instance spec, and it runs ephemeral managed compute (a job) or a persistent managed fleet (an endpoint) for you."**

Two ideas unlock everything:
- **Everything is a job or an endpoint.** *Jobs* (training, processing, tuning, batch transform) are **ephemeral** — SageMaker spins up a cluster in an **AWS-managed account**, runs your container, writes results to S3, tears it down, **bills per second**. *Endpoints* are **persistent** managed serving fleets. You never patch a box.
- **The contract is a container + S3 + IAM role.** Your algorithm is a Docker image (in ECR); your data lives in S3; a **SageMaker execution role** grants access. SageMaker orchestrates the rest.

This is the same "virtualize the resource, run it as a managed service, drive it by API" philosophy as the storage/networking services — applied to ML compute + lifecycle.

```
   You provide                    SageMaker runs (managed account/infra)
   ┌────────────────────┐         ┌───────────────────────────────────────┐
   │ container (ECR)     │  ──►    │ Training job: provision GPUs → pull    │
   │ data (S3)           │         │  image → stream S3 data → run → write  │
   │ instance type/count │         │  model artifact to S3 → tear down      │
   │ execution role (IAM)│         │ Endpoint: persistent fleet + LB +      │
   └────────────────────┘         │  autoscaling serving /invocations      │
                                   └───────────────────────────────────────┘
```

---

## 3. The component map (what's actually in "SageMaker")

| Stage | Component | What it is |
|---|---|---|
| **Build** | **Studio** | Web IDE (notebooks, debugging, everything). The modern front door. |
| | Notebook instances | Older managed Jupyter on an EC2 instance. |
| | **JumpStart** | Model/solution hub — pre-trained models & FMs you deploy/fine-tune in a click. |
| | Autopilot | AutoML — give it a table, it builds candidate models. |
| **Prepare** | **Processing jobs** | Ephemeral containers for data prep / feature engineering / evaluation. |
| | Data Wrangler | Visual data prep. |
| | **Feature Store** | Managed store for ML features (online low-latency + offline S3). |
| | Ground Truth | Managed data labeling. |
| **Train** | **Training jobs** | Ephemeral managed clusters that run your training container. |
| | **HPO / Tuning jobs** | Managed hyperparameter search (Bayesian/random). |
| | Experiments | Track runs, params, metrics. |
| **Deploy** | **Endpoints** (real-time/serverless/async) | Persistent managed serving. |
| | Batch Transform | Offline batch inference job. |
| **Operate** | **Model Registry** | Versioned model catalog + approval workflow. |
| | **Pipelines** | DAG orchestration (CI/CD for ML). |
| | **Model Monitor** | Data/model quality + drift detection on endpoints. |
| | Clarify | Bias detection + explainability (SHAP). |

You don't use all of it. A minimal path = Studio → Training job → Model → Endpoint. The rest is MLOps maturity.

---

## 4. Internal architecture

### 4a. Control plane vs data plane [Documented behavior]
- **Control plane** — the SageMaker APIs (`CreateTrainingJob`, `CreateEndpoint`, …), orchestration, scheduling, lifecycle. It provisions and tears down the compute on your behalf.
- **Data plane** — the actual **training clusters** and **inference fleets** running your containers, plus the data path to S3/EFS/FSx. This is where your GPUs burn and your `/invocations` get served.

### 4b. How a training job physically runs [Documented]
1. You call `CreateTrainingJob` with: image (ECR), input channels (S3 paths), instance type/count, hyperparameters, output S3 path, execution role.
2. SageMaker **provisions the requested instances in an AWS-managed account**, sets up an ephemeral cluster (multi-node gets a private network + env vars describing peers).
3. It **pulls your container** from ECR and **stages input data**: **File mode** (download all to local EBS/NVMe first), **Pipe mode** (stream from S3), or **FastFile mode** (lazy stream, POSIX-like). See [training.md](training.md).
4. Runs the container's entrypoint with data under `/opt/ml/input/`, writes the model to `/opt/ml/model/`, which SageMaker **uploads to S3** on success.
5. **Tears the cluster down.** You pay for the seconds it ran. Spot instances + checkpointing to S3 make this cheap.

### 4c. How an endpoint physically runs [Documented]
1. `CreateModel` (image + model artifact in S3 + role) → `CreateEndpointConfig` (instance type, count, variants, autoscaling) → `CreateEndpoint`.
2. SageMaker stands up a **persistent fleet** behind a **managed load balancer**; each instance runs your serving container, which must answer **`GET /ping`** (health) and **`POST /invocations`** (inference).
3. **Autoscaling** adjusts instance count on metrics (e.g., `InvocationsPerInstance`). **Production variants** enable A/B, canary, and blue-green/shadow deploys.
4. You pay for the **running instances** (real-time) — the classic "idle endpoint burning money" cost trap (→ serverless/async for spiky/infrequent traffic; see [inference.md](inference.md)).

### 4d. The container contract [Documented]
- Standard directory layout: `/opt/ml/input/` (data + config), `/opt/ml/model/` (artifacts), `/opt/ml/output/` (failure reason), `/opt/ml/code/` (your script in script mode).
- **Script mode** — use an AWS-provided framework container (PyTorch/TF/XGBoost/HuggingFace) and just supply your `train.py`. **BYOC (bring your own container)** — you build the full Docker image for custom needs. Most people use script mode.

### 4e. Networking & data [Documented]
- **By default** jobs/endpoints run in a **SageMaker-managed account** with internet access, reaching S3 over AWS's network.
- **VPC mode** attaches **ENIs into your VPC** so training/inference can reach private resources (RDS, internal services) and, with **network isolation**, run with **no internet** — critical for regulated data (see [security.md](security.md)).
- **Data sources:** **S3** (primary), **EFS/FSx for Lustre** for large/shared datasets (FSx-Lustre is the HPC choice for big training sets — ties back to your storage study).

---

## Sources
- AWS docs: *How Amazon SageMaker works*, *Use Docker containers to build models*, *Training storage paths*, *Deploy models for inference*.
- re:Invent: *SageMaker deep dives* (AIM track).

---

## Self-check
1. State the core primitive of SageMaker in one sentence (what you provide vs what it runs).
2. Contrast a *job* and an *endpoint* in terms of lifecycle and billing — and name the classic cost trap.
3. Walk the lifecycle of a training job from `CreateTrainingJob` to model-in-S3, naming where the container and data come from.
4. What two HTTP routes must a serving container implement, and what does each do?
5. When do you need VPC mode + network isolation, and what does it change about how the job reaches data?
