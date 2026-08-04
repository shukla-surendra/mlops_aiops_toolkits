# MLflow

**Category:** experiment tracking / model registry / model lifecycle
**First documented:** 2026-08-04

## What it is

Open-source platform for managing the ML lifecycle. Four main pieces:

- **Tracking** — logs params, metrics, and artifacts for each experiment
  "run," queryable/comparable later.
- **Model Registry** — versions models, tracks stage transitions (e.g.
  staging → production), and provides lineage back to the run that
  produced each version.
- **Model packaging** — the `MLmodel` format, a standard way to package a
  model with its dependencies so it can be loaded/served consistently
  regardless of the framework (XGBoost, sklearn, PyTorch, etc.).
- **Model serving** — can serve a registered model directly as a REST
  endpoint.

On Databricks, MLflow is built in as a **managed service** — tracking and
the model registry work out of the box against Unity Catalog, with no
separate server to stand up.

## Relationship with Evidently

MLflow and [Evidently](../evidently/README.md) are complementary, not
competing:

- MLflow is the **tracking backbone** — it stores whatever gets logged to
  it, but doesn't compute drift/quality/performance statistics itself.
- Evidently is the **analysis library** that computes those statistics and
  produces a report; it has no tracking system of its own.
- In practice: Evidently reports (HTML/JSON) get logged into MLflow runs as
  **artifacts**, and Evidently's computed numbers (e.g.
  `dataset_drift_detected`) get logged as MLflow **metrics** — see the
  worked Databricks XGBoost batch-monitoring example in the Evidently docs,
  which does exactly this inside an `mlflow.start_run()` block.
- Minor overlap: MLflow's own `mlflow.evaluate()` has built-in evaluators
  (classification/regression metrics, some SHAP explainability) that cover
  a sliver of point-in-time model evaluation also covered by Evidently's
  `ClassificationPreset`/`RegressionPreset` — but MLflow has no drift
  detection (reference-vs-current distribution comparison) of its own.

## Change log

- 2026-08-04: Initial documentation — what it is, four main components,
  Databricks-managed integration, and relationship with Evidently.
