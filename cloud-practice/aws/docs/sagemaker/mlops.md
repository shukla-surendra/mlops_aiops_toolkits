# SageMaker — MLOps: Pipelines, Registry, Feature Store, Monitoring

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md), [training.md](training.md), [inference.md](inference.md).

Spec sections 8, 11. MLOps = making ML **reproducible, automated, governed, and monitored** — the difference between a notebook demo and a production system.

---

## 1. Pipelines — CI/CD for ML [Documented]
- **SageMaker Pipelines** is a managed **DAG orchestrator** for ML steps: processing → training → evaluation → conditional register/deploy. Defined in the Python SDK; each step is a SageMaker job.
- **Why:** reproducibility (the whole flow is code + versioned), automation (retrain on new data/code), and a caching model (skip unchanged steps).
- **Conditional steps** gate deployment on evaluation metrics ("register the model only if AUC > 0.8").
- Alternatives/complements: **Step Functions**, **Airflow (MWAA)**, **Kubeflow on EKS** — Pipelines is the native, SageMaker-integrated option.

## 2. Model Registry — versioned model catalog [Documented]
- A **catalog of model versions** grouped into **model package groups**, each with metadata, metrics, lineage, and an **approval status** (PendingManualApproval → Approved/Rejected).
- Deployment pipelines watch for **Approved** models → promote to staging/prod. This is the governance gate between training and release.

## 3. Experiments & lineage [Documented]
- **Experiments** track runs: parameters, metrics, artifacts — so you can compare and reproduce.
- **ML Lineage Tracking** auto-records the graph: which dataset + code + hyperparameters produced which model, deployed to which endpoint. Essential for audit/debug ("what data trained the model serving this bad prediction?").

## 4. Feature Store [Documented]
- Managed store for ML **features** with two faces: **online** (low-latency lookups for real-time inference) and **offline** (S3, for training + batch). Solves **train/serve skew** (same feature definitions/values in both) and enables feature reuse across teams.
- Feature groups, ingestion, point-in-time correct queries for training sets.

## 5. Monitoring in production [Documented]
- **Model Monitor** — scheduled jobs that compare live endpoint traffic against a **baseline** to detect **data quality** drift, **model quality** drift (needs ground truth), **bias drift**, and **feature attribution** drift. Emits CloudWatch metrics + alarms → trigger retraining.
- **Clarify** — bias detection (pre/post training) + **explainability** (SHAP feature attributions), also usable online.
- **Data capture** — endpoints log inputs/outputs to S3 for monitoring + debugging.
- Plus standard **CloudWatch** endpoint metrics (invocations, latency, errors, instance utilization).

## 6. Projects & governance
- **SageMaker Projects** — MLOps templates wiring CodePipeline/CodeBuild + Pipelines + Registry into a repeatable CI/CD setup (build repo, deploy repo, approval flow).
- **Model Cards** — document a model's intended use, metrics, risks (governance/compliance artifact).
- **Role Manager / execution roles** — scoped permissions per persona (see [security.md](security.md)).

## 7. A mature MLOps loop (put it together)
```
data → Processing → Training (Experiments track it) → Evaluation
       → (Condition: metric OK?) → Model Registry (PendingApproval)
       → human/auto approve → Deploy pipeline → Endpoint (data capture on)
       → Model Monitor detects drift → alarm → trigger retrain pipeline ↺
Feature Store feeds both training (offline) and the endpoint (online).
```

---

## Sources
- AWS docs: *SageMaker Pipelines*, *Model Registry*, *Experiments*, *ML Lineage*, *Feature Store*, *Model Monitor*, *Clarify*, *Projects*, *Model Cards*.

---

## Self-check
1. What does a Pipeline give you that running jobs by hand from a notebook does not?
2. How does the Model Registry's approval status gate production deployment?
3. What is train/serve skew and how does Feature Store prevent it?
4. Model Monitor flags data-quality drift on an endpoint — walk the automated loop from detection to a retrained model.
5. A prediction is wrong in production; which two features help you trace *what data + code produced that model*?
