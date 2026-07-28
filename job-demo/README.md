# job-demo

Hands-on companion to the Job section of [`docs/workload-types.md`](../docs/workload-types.md).
Three manifests, each isolating one behavior of `Job` that's easy to describe but more
convincing to watch happen: run-to-completion, retry-on-failure, and parallel work-splitting.

See [`cronjob-demo/`](../cronjob-demo) for running a Job like these on a schedule.

Assumes a running `minikube` cluster (`minikube status`).

## Why does `Job` exist?

Every other workload type in this repo (`Deployment`, `StatefulSet`, `DaemonSet`) is built
around the assumption that a Pod exiting is a *problem* — the controller's whole job is to
notice and bring up a replacement, forever. That assumption is wrong for a piece of work that
has a natural end: a migration finishes, a report finishes, a video finishes encoding. Point a
Deployment at that container and it becomes a bug — the Pod exits `0`, the Deployment sees
"container not running" and restarts it, and now your one-time migration re-runs in an infinite
crash loop.

`Job` inverts the assumption: it exists specifically to run a Pod (or several) **to completion,
exactly the number of times you asked for, and then stop** — while still giving you the
reliability piece (retry on failure, up to a limit) that a bare, uncontrolled `kubectl run` Pod
doesn't give you at all. It's the missing middle between "one Pod, no supervision" and "a
controller that never lets the Pod stay stopped."

## What use case does it solve?

Anything that's a discrete unit of work rather than an always-on service:

- **Database migrations / schema changes** — this repo's own
  [`full-stack-app/templates/migration-job.yaml`](../full-stack-app/templates/migration-job.yaml)
  runs the schema/seed migration once per install or upgrade, ahead of the backend Pods rolling
  out.
- **Batch/data processing** — transform a fixed input (a file, a table, a queue's current
  backlog) and stop; `02-job-parallel.yaml` here is that shape, with `parallelism` controlling
  how many workers chew through it at once.
- **One-off backfills or admin tasks** — reindexing, a data-format upgrade, a bulk cleanup —
  work you want run reliably (with retries) but only when triggered, not continuously.
- **CI/CD and build steps run inside the cluster** — compiling, testing, or publishing an
  artifact as a cluster-native step rather than an external CI runner.

The common thread: the work has a defined finish line and a defined *number* of times it should
run (once, or `completions` times) — never "keep this running."

## Do we need to schedule it?

Not necessarily — that's the deciding line between `Job` and `CronJob`:

- **No recurrence needed → plain `Job`** (what's in this directory). You create it once —
  by hand, from a CI/CD pipeline step, as a Helm install/upgrade hook (see the migration Job
  above), or in response to some other event — it runs to completion, and it's done. There's no
  schedule because there's nothing to repeat.
- **The same work needs to happen on a timer → `CronJob`** (see
  [`cronjob-demo/`](../cronjob-demo)). A CronJob doesn't replace a Job's mechanics — it *is* a
  Job template, and at every tick it creates a new, ordinary `Job` that behaves exactly like the
  ones in this directory (same `backoffLimit` retries, same completion tracking). The only thing
  a CronJob adds on top is "and do that again every `schedule`."

Rule of thumb: reach for `CronJob` only once you can name the recurring cadence up front (nightly
backup, hourly report). If the trigger is instead "after a deploy," "when a user clicks a
button," or "whenever this pipeline stage runs" — that's a plain `Job`, created on demand by
whatever's driving that event, not a schedule.

## Part 1 — a basic Job (`00-job-basic.yaml`)

```bash
kubectl apply -f 00-job-basic.yaml
kubectl get pods -l job-name=pi-calc -w
```

Watch the Pod go `Pending` → `Running` → `Completed`. Unlike a Deployment's Pods, a Job's Pod
finishing successfully is the goal, not a crash to recover from — it stays in `Completed`, it
isn't restarted:

```bash
kubectl get job pi-calc
kubectl logs job/pi-calc
```

`kubectl get job` shows `COMPLETIONS 1/1` once done. The logs are the first couple thousand
digits of pi — proof the container actually ran to completion rather than just exiting `0`
immediately.

## Part 2 — retries via `backoffLimit` (`01-job-retry.yaml`)

```bash
kubectl apply -f 01-job-retry.yaml
kubectl get pods -l job-name=flaky-job -w
```

This container always `exit 1`s. With `restartPolicy: Never`, a failed Pod isn't restarted in
place — the **Job controller** notices the failure and creates a brand-new Pod instead. Watch
three Pods appear (the original attempt plus two retries, matching `backoffLimit: 2`), each
with a fresh name:

```bash
kubectl get pods -l job-name=flaky-job
kubectl describe job flaky-job
```

`describe` ends with `Status: Failed` and an event log showing each `SuccessfulCreate` — one per
attempt. Once `backoffLimit` attempts are all exhausted, the Job stops retrying and reports
failed rather than looping forever.

## Part 3 — splitting work with `completions`/`parallelism` (`02-job-parallel.yaml`)

```bash
kubectl apply -f 02-job-parallel.yaml
kubectl get pods -l job-name=parallel-work -w
```

`completions: 6, parallelism: 3` means: run this Pod six times total, up to three at once. Expect
three Pods `Running` immediately, and — as each finishes its 5s sleep — a new one starts to
replace it, until six have completed:

```bash
kubectl get job parallel-work
kubectl logs -l job-name=parallel-work --prefix
```

Each log line shows a different Pod hostname picking up "one unit of work" — this is the pattern
for batch/fan-out jobs (e.g. processing a queue or a fixed list of files) where you want bounded
concurrency instead of either fully serial or fully unbounded.

## Cleanup

```bash
kubectl delete -f 02-job-parallel.yaml
kubectl delete -f 01-job-retry.yaml
kubectl delete -f 00-job-basic.yaml
```

## Command & flag glossary

| Command / flag | Means |
|---|---|
| `kubectl apply -f <file>` | Create (or update) whatever's described in that YAML file. |
| `kubectl get pods -l job-name=<name> -w` | List Pods labeled with the Job that owns them (Kubernetes auto-labels every Job's Pods with `job-name=<job>`) and `-w`atch for changes live instead of a one-time snapshot. |
| `kubectl get job <name>` | Shows a Job's `COMPLETIONS` (e.g. `1/1`, `6/6`) and `DURATION` — the summary view; `describe` below gives the blow-by-blow. |
| `kubectl describe job <name>` | Full detail including the event log — every Pod the Job controller created and why (`SuccessfulCreate`, `BackoffLimitExceeded`, etc). |
| `kubectl logs -l job-name=<name> --prefix` | Logs from every Pod matching the label at once, each line prefixed with which Pod it came from — needed here since a parallel Job has several Pods, not one. |
| `kubectl delete -f <file>` | The inverse of `apply` — remove exactly what that file describes. |

## Reference

| File | Demonstrates |
|---|---|
| `00-job-basic.yaml` | A Job runs its Pod once to completion and stops — no restart on success. |
| `01-job-retry.yaml` | `backoffLimit` — a failed Pod isn't restarted in place; the Job controller creates a new one, up to the limit. |
| `02-job-parallel.yaml` | `completions`/`parallelism` — bounded concurrent fan-out across many Pod runs. |
