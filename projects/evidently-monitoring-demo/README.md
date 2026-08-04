# Evidently monitoring demo

Runnable Jupyter notebook demonstrating drift + classification-performance
monitoring with Evidently and XGBoost, logged to MLflow. Standalone version
of the pattern documented in
[`docs/tools/evidently/README.md`](../../docs/tools/evidently/README.md)
(the 4-hour Databricks batch example) — uses synthetic data and local
pandas/MLflow instead of Delta tables and Databricks Workflows, so it runs
anywhere without a cluster.

This has been executed end-to-end (see "Known environment quirks" below
for the two real issues that came up and how they're handled).

## Setup (uv)

Managed with [uv](https://docs.astral.sh/uv/) — dependencies are declared
in `pyproject.toml`, pinned in `uv.lock`.

```bash
cd projects/evidently-monitoring-demo
uv sync
```

This creates `.venv/` and installs everything (pandas, scikit-learn,
xgboost, evidently, mlflow, jupyter) at the versions in `uv.lock`. No
separate `pip install` step needed.

## Run it

Interactively, in Jupyter:

```bash
NLTK_DISABLE_IMPORT_SECURITY=1 uv run jupyter notebook evidently_xgboost_monitoring.ipynb
```

Headlessly, to just execute it end-to-end and bake in the outputs (useful
for CI-style "does it still run" checks):

```bash
NLTK_DISABLE_IMPORT_SECURITY=1 uv run jupyter nbconvert --to notebook --execute --inplace evidently_xgboost_monitoring.ipynb
```

Then browse the MLflow run (the logged Evidently HTML report + drift
metric):

```bash
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
```

## Known environment quirks (already handled, documented for context)

- **`NLTK_DISABLE_IMPORT_SECURITY=1` is required.** NLTK 3.10+ ships a
  legitimate security hardening feature (`nltk/inisec.py`, CWE-427
  mitigation) that blocks NLTK's own internal imports whenever the current
  working directory is on `sys.path` — which Jupyter/uv add by default.
  Evidently pulls in NLTK transitively (for text/LLM descriptors we don't
  even use here), so this false-positive fires on plain `import evidently`.
  The env var above is NLTK's own documented escape hatch for this exact
  situation — nothing malicious involved, verified by reading
  `nltk/inisec.py` directly.
- **Evidently's classic API moved under `evidently.legacy`.** Current
  Evidently (0.7.x) ships a new core API; the familiar
  `Report`/`ColumnMapping`/`metric_preset` interface used in this notebook
  and most existing tutorials still exists, just under
  `evidently.legacy.*` (e.g. `from evidently.legacy.report import Report`).
- **MLflow's plain filesystem store (`./mlruns`) is in maintenance mode.**
  Current MLflow refuses to use it by default and recommends a database
  backend even for local use — this notebook uses
  `sqlite:///mlflow.db` instead.

## Related docs

- [Evidently](../../docs/tools/evidently/README.md) — full write-up,
  alternatives, server requirements, MLflow relationship.
- [MLflow](../../docs/tools/mlflow/README.md) — tracking backbone used here.
- [Databricks example](../../docs/tools/evidently/examples/databricks_xgboost_batch_monitoring.py) —
  the production version this notebook is a standalone stand-in for.
