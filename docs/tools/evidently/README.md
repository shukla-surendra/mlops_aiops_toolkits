# Evidently (Evidently AI)

**Category:** ML monitoring / observability
**First documented:** 2026-08-04

## What it is

Open-source Python library for evaluating, testing, and monitoring ML models
and data in production. Lightweight — works standalone without dedicated
infra, and plugs into whatever pipeline/scheduler you already have (Airflow,
cron, Databricks Workflows, plain CI).

## What it's used for

- **Data drift detection** — compares a reference dataset (e.g. training
  data) against current production data to flag distribution shifts in
  features or target.
- **Model performance monitoring** — tracks metrics (accuracy, regression
  error, classification metrics) over time once ground truth is available.
- **Data quality checks** — missing values, schema changes, out-of-range
  values.
- **Reports & test suites** — generates HTML/JSON reports, or pass/fail test
  suites you can run in CI or on a schedule.
- **Dashboards** — a newer Evidently Cloud layer adds live dashboards on top
  of the core library, but the core library itself is just Python + reports.

Note: an Evidently `Report` is a **single point-in-time comparison** of a
reference vs. a current dataset — it does not accumulate history across runs
on its own. For a trend view over time, you append each run's metrics to
your own storage (see the Databricks example below).

## Does it need a server?

No, not for the core library. `Report.run()` / `TestSuite.run()` execute
in-process on pandas DataFrames and produce a plain HTML/JSON artifact — you
save or log that yourself (a file, MLflow, S3, a Delta table, whatever).
That's exactly why it drops into a Databricks job or a plain cron script
with zero extra infrastructure.

Two **optional** server components exist if you want more than one-off
reports:

- **`evidently ui`** — open-source, self-hostable local web server. Point it
  at a "workspace" directory of saved reports and it gives a browsable
  dashboard with history across runs. Run via `pip install evidently` then
  `evidently ui` — no external dependency, you host it yourself.
- **Evidently Cloud** — their managed SaaS platform: hosted dashboards, team
  accounts, alerting. No self-hosting, but it's an external service/account.

For the Databricks batch-monitoring example documented below, **no server
is used or needed** — logging to MLflow plus the `ml_monitoring.drift_history`
Delta table already solves the trend-over-time problem without adopting
either of these.

## Drift detection concepts, vs. a custom implementation

If you've built (or are considering building) a custom drift-detection
setup — e.g. capture a benchmark at training time, sample inference
results, compare against actual outcomes once ground truth arrives — see
[`drift-detection-concepts.md`](drift-detection-concepts.md) for a direct
comparison against how Evidently structures the same problem, including
where a custom outcome-based approach and Evidently's label-free
covariate/prediction drift diverge, and a concrete mapping from custom
pipeline stages onto Evidently's API.

## Relationship with MLflow

They're complementary, not overlapping.

- **MLflow** is the tracking/registry/serving backbone — experiment
  tracking (params, metrics, artifacts per run), a model registry for
  versioning, model packaging (MLmodel format), and model serving. It's a
  system of record for "what ran, when, with what results," not an
  analysis library.
- **Evidently** is an analysis library that computes drift/quality/
  performance statistics and produces a report. It has no tracking system,
  registry, or serving of its own.

**Integration**: Evidently has a native MLflow hook — log a `Report`'s
HTML/JSON as an MLflow artifact, and push its computed numbers (e.g.
`dataset_drift_detected`, per-feature drift scores) as MLflow metrics,
inside a normal `mlflow.start_run()` block. This is exactly what the
Databricks XGBoost example above does: Evidently computes, MLflow stores.
On Databricks this is frictionless since MLflow tracking is already
built in — the Evidently report becomes just another artifact next to your
training runs, no separate storage system needed.

**Partial overlap**: MLflow's own `mlflow.evaluate()` has built-in
evaluators (classification/regression metrics, some SHAP-based
explainability) that cover a sliver of what Evidently's
`ClassificationPreset`/`RegressionPreset` do for point-in-time model
evaluation. But MLflow has **no drift detection** (no reference-vs-current
distribution comparison) and no data-quality test suites — that stays
Evidently-only territory.

**Bottom line**: MLflow tracks/versions/serves; Evidently generates the
drift/monitoring content that gets tracked. See
[MLflow](../mlflow/README.md) for the other side of this relationship.

## Alternatives

| Tool | Angle |
|---|---|
| **WhyLabs / whylogs** | Lightweight data logging + drift, strong on streaming/low-overhead profiling |
| **Arize AI** | Full observability platform, LLM + traditional ML, strong tracing/embeddings drift |
| **Fiddler AI** | Enterprise model monitoring + explainability |
| **Arthur AI** | Enterprise monitoring, bias/fairness focus |
| **NannyML** | Estimates performance *without* ground truth (drift-based performance estimation) |
| **Deepchecks** | Closest open-source peer — validation suites for data/model |
| **Alibi Detect** (Seldon) | Drift/outlier detection library, more research-oriented |
| **Great Expectations** | Data quality/validation focus, often paired with Evidently rather than competing |
| **SageMaker Model Monitor / Azure ML Data Drift** | Cloud-native, built into the platform if already on AWS/Azure |
| **[Databricks Lakehouse Monitoring](../databricks-lakehouse-monitoring/README.md)** | Databricks-native equivalent — see comparison there |

For a self-hosted, framework-agnostic setup, Evidently and Deepchecks are the
closest open-source peers; for a managed platform, Arize/Fiddler/WhyLabs are
the usual next step up.

## Running it on Databricks

Evidently is just a Python library, so it runs unmodified on Databricks:

- `%pip install evidently` on a cluster/notebook.
- It expects **pandas** DataFrames — convert Spark/Delta data with
  `.toPandas()` (fine for reference/profiling-sized samples, not for huge
  tables).
- Log the HTML report as an **MLflow artifact** (Evidently has a native
  MLflow integration), and/or write the computed metrics to a Delta table
  for a Databricks SQL / AI-BI dashboard.
- Current Evidently versions (0.7.x) moved the classic `Report`/
  `ColumnMapping`/`metric_preset` API under `evidently.legacy.*` — e.g.
  `from evidently.legacy.report import Report`, not `from evidently.report
  import Report`. Same behavior, new import path; already updated in
  [`examples/databricks_xgboost_batch_monitoring.py`](examples/databricks_xgboost_batch_monitoring.py).

### Worked example: XGBoost batch classifier, scored every 4 hours

Setup: an XGBoost classification model scores a batch on a 4-hour schedule
via a Databricks Workflow. Each scoring run writes features + predictions
(and later, true labels once they land) to a Delta table
`ml_monitoring.batch_predictions`.

A monitoring task runs immediately after the scoring task in the same
Workflow. Full code: [`examples/databricks_xgboost_batch_monitoring.py`](examples/databricks_xgboost_batch_monitoring.py).

A standalone, runnable version of this same pattern (synthetic data, local
pandas/MLflow, no Databricks/Spark required) lives in
[`projects/evidently-monitoring-demo/`](../../../projects/evidently-monitoring-demo/) as a Jupyter notebook.

Key points:

- **Reference** = training-time snapshot (features + true label + the
  model's own prediction on that data), stored as a Delta table.
- **Current** = just the latest 4-hour batch, filtered by `scoring_ts`.
- Uses `Report(metrics=[DataDriftPreset(), ClassificationPreset()])` with a
  `ColumnMapping` describing target/prediction/feature columns.
- **Labels lag reality**: `actual_label` usually isn't available yet at
  scoring time. Run `DataDriftPreset()` immediately (features/predictions
  only); run `ClassificationPreset()` in a separate, later-scheduled job once
  ground truth has caught up for that batch.
- Report HTML + a `dataset_drift_detected` metric are logged to **MLflow**.
- Because the report itself has no memory of past runs, append one row per
  run to a separate Delta table (`ml_monitoring.drift_history`) to get a
  trend line, and visualize it in a Databricks SQL/AI-BI dashboard.
- **Alerting**: after logging the metric, fail the Databricks task (or hit a
  Slack webhook) if `drift_detected` is true — Databricks Jobs surfaces that
  as a failed run/alert.

## Difference vs. plain Python + pandas (no Databricks)

The Evidently code itself is **identical** either way — `Report`,
`ColumnMapping`, and the metric presets only ever operate on pandas
DataFrames; nothing about them is Databricks-specific. What changes is the
scaffolding *around* it:

| Concern | Databricks | Plain Python + pandas |
|---|---|---|
| Data source | `spark.table(...).toPandas()` from Delta | `pd.read_csv`/`read_parquet`, or a direct DB query |
| Scheduling | Databricks Workflows (native, chained to the scoring job) | Cron / Airflow / Prefect, set up yourself |
| Compute | Managed cluster, autoscaling | Whatever machine/container runs the script |
| Artifact tracking | Built-in managed MLflow | Self-hosted MLflow server, or just write files to disk/S3 |
| Auto-logging predictions | Model Serving can auto-log to an inference table | You write the scoring output to a file/DB yourself |
| Trend history / dashboard | Delta table + Databricks SQL/AI-BI dashboard | Append to CSV/Postgres + build your own dashboard (Streamlit, Grafana, etc.) |
| Governance | Unity Catalog access control on the tables | Whatever access control your storage layer has |

Databricks doesn't change *what* Evidently computes — it just supplies the
scheduling, storage, and artifact-tracking scaffolding that you'd otherwise
have to build by hand in a plain Python setup.

## Change log

- 2026-08-04: Initial documentation — what it is, purpose, alternatives.
- 2026-08-04: Databricks compatibility notes; comparison against Databricks
  Lakehouse Monitoring.
- 2026-08-04: Worked example for a 4-hour scheduled XGBoost batch classifier
  on Databricks; pandas-only comparison table.
- 2026-08-04: Documented server requirements — core library is server-free;
  `evidently ui` (self-hosted) and Evidently Cloud (SaaS) are optional
  add-ons for persistent dashboards, neither needed for the Databricks
  example already documented here.
- 2026-08-04: Documented relationship with MLflow — complementary roles
  (MLflow tracks/versions/serves, Evidently computes drift/quality/
  performance content), the native MLflow logging integration already used
  in the Databricks example, and the minor overlap via `mlflow.evaluate()`.
- 2026-08-04: Added a standalone runnable Jupyter notebook at
  `projects/evidently-monitoring-demo/` — same drift+classification
  monitoring pattern as the Databricks example, using synthetic data and
  local pandas/MLflow so it runs without Databricks/Spark.
- 2026-08-04: Set up `projects/evidently-monitoring-demo/` with uv
  (`pyproject.toml` + `uv.lock`, `uv sync`) and actually executed the
  notebook end-to-end to verify it runs — replaced `requirements.txt`/pip
  with uv as the project's env manager. Executing it surfaced three real
  environment issues, now fixed and documented in the project's README:
  - NLTK 3.10+ ships a genuine security hardening feature
    (`nltk/inisec.py`, a CWE-427 mitigation — verified by reading the file,
    not a supply-chain compromise) that blocks NLTK's own internal imports
    whenever the current working directory is on `sys.path`, which
    Jupyter/uv add by default. Evidently pulls in NLTK transitively even
    though this demo uses no text/LLM descriptors, so plain `import
    evidently` false-positives. Fix: set `NLTK_DISABLE_IMPORT_SECURITY=1`
    (NLTK's own documented escape hatch) when running anything that
    imports evidently under Jupyter/uv.
  - Confirmed installed version is evidently 0.7.21, where the classic API
    lives under `evidently.legacy.*` (see the import-path note added above
    in "Running it on Databricks").
  - MLflow's plain filesystem store (`./mlruns`) is now in maintenance mode
    and current MLflow refuses to use it by default — the demo uses
    `sqlite:///mlflow.db` instead, MLflow's own recommended local backend.
  - Teaching note baked into the notebook: with only 1 of 8 synthetic
    features drifted (12.5%), `dataset_drift` stayed `False` even though
    that one feature was correctly flagged as drifted individually —
    Evidently's dataset-level flag only flips `True` once the *share* of
    drifted columns crosses a default >50% threshold. Correct, expected
    behavior, not a bug — illustrates why per-feature drift still matters
    when the dataset-level flag stays green.
- 2026-08-04: Added `drift-detection-concepts.md` — a direct comparison
  between a custom outcome-based (ground-truth-dependent) drift
  implementation and Evidently's split between label-free
  covariate/prediction drift and label-dependent performance drift, with a
  mapping table and a concrete step-by-step adoption walkthrough.
