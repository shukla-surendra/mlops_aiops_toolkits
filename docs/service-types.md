# Service types: `ClusterIP`, `NodePort`, `LoadBalancer`, headless, `ExternalName`

Hands-on companion: [`services-demo/`](../services-demo). One shared Deployment, five
Services in front of it, one per type below.

A `Service` is a stable address plus a rule for picking which Pod actually answers. `type`
controls **who can reach that address from where** — it doesn't change how Pods are
selected (`spec.selector`) or which port forwards to which (`port` / `targetPort`), which
are the same across every type.

## `ClusterIP` — the default

A stable virtual IP, internal to the cluster, that load-balances across every Pod matching
the selector. Every other Service type is built on top of this one — `NodePort` and
`LoadBalancer` both still get a ClusterIP, they just add another way to reach it.

Reachable only from inside the cluster (other Pods, or `kubectl port-forward`/`exec`). Not
reachable from your laptop's browser without a tunnel of some kind — see
[`accessing-pods-and-services.md`](./accessing-pods-and-services.md).

## `NodePort`

Everything `ClusterIP` does, plus: opens the same port (default range `30000-32767`) on
**every node's** IP, cluster-wide. Reach it at `<any-node-ip>:<nodePort>`, whether or not a
Pod is actually running on that particular node — `kube-proxy` routes the request to a
node that has one.

Because the port is claimed on every node, an explicit `nodePort` value must be unique
across the whole cluster — see the collision demo in
[`multiple-services-same-port.md`](./multiple-services-same-port.md). Leaving `nodePort`
unset lets Kubernetes auto-assign a free one and sidesteps that entirely.

Good for local/dev access (this is what `minikube service` uses under the hood). Not how
production HTTP(S) traffic gets in — no hostnames, no TLS, and it exposes raw node IPs as
the access point.

## `LoadBalancer`

Everything `NodePort` does, plus: asks the platform to provision a real external load
balancer with its own public IP or DNS name and point it at the NodePort it just opened.

- **Cloud (EKS/GKE/AKS):** this is a real API call to the provider — an ELB/NLB on AWS, for
  example — and `EXTERNAL-IP` fills in with something a browser anywhere can hit.
- **Local (minikube):** there's no cloud to call, so `EXTERNAL-IP` sits at `<pending>`
  forever unless `minikube tunnel` is running to simulate one.

One `LoadBalancer` Service is one external load balancer. Fine for exposing a single app;
exposing many this way means many load balancers, which is exactly the problem `Ingress`
solves by multiplexing many Services behind one.

## Headless Service (`clusterIP: None`)

Turns off the virtual-IP-and-load-balancing behavior entirely. DNS for a headless Service
resolves directly to the set of matching Pod IPs — one `A` record per Pod — instead of one
stable ClusterIP in front of them.

This matters most alongside a `StatefulSet`: each replica gets a distinct, stable DNS name
(`<pod>.<service>.<namespace>.svc.cluster.local`) instead of being anonymous behind a
load-balanced IP. It also works on a plain `Deployment` (as in the demo) — you just get
Pod-level DNS instead of Service-level DNS, with no load-balancing in between; the client
decides which resolved IP to use.

## `ExternalName`

The odd one out: no selector, no endpoints, no Pods, no proxying. It's a pure DNS alias —
resolving the Service's name returns a `CNAME` to whatever `spec.externalName` says instead
of a Pod IP.

Used to give an in-cluster, `.svc.cluster.local`-shaped name to something that lives
**outside** the cluster — a managed database, a legacy host, a third-party API — so
application code always addresses it the same way regardless of where the real thing is.
Because it's DNS-only, it doesn't get a ClusterIP, doesn't show up in `endpoints`, and
carries none of the health-checking or load-balancing the other types have.

## Usage — everyday `kubectl` commands

The five manifests in [`services-demo/`](../services-demo) are the declarative (YAML)
way to create a Service. Day to day you'll also touch Services imperatively — creating one
quickly, inspecting why it isn't working, or changing its `type` in place.

### Create

```bash
# Quick, imperative — good for throwaway testing:
kubectl expose deployment web-backend --port=80 --target-port=80 --type=ClusterIP

# Declarative — good for anything you want to keep/review/re-apply:
kubectl apply -f 01-clusterip.yaml
```

`kubectl expose` reads the Deployment's Pod template to build the selector for you — it's
the fastest way to get a Service in front of something that already exists, but it doesn't
leave a YAML file behind, so it's easy to forget what you created and why.

### Inspect

```bash
kubectl get svc                        # type, ClusterIP, EXTERNAL-IP, ports
kubectl get svc -o wide                # + selector, shown as SELECTOR column
kubectl describe svc web-clusterip     # selector, endpoints, events — the first stop when debugging
kubectl get endpoints web-clusterip    # the actual Pod IP:port pairs currently behind the Service
```

`kubectl describe svc` is usually the fastest way to answer "why isn't this working" — it
shows the selector it's using and the endpoints it resolved to in one place. If
`Endpoints: <none>`, the Service's `selector` doesn't match any Pod's labels (or the
matching Pods aren't `Ready` — a Service only includes Pods that pass their readiness
probe, see [`probes-and-health-checks.md`](./probes-and-health-checks.md)). That's the
single most common Service bug, and it never shows up as an error on the Service itself —
`kubectl get svc` looks completely healthy either way.

### Change a Service in place

```bash
# Bump ClusterIP -> NodePort without deleting/recreating:
kubectl patch svc web-clusterip -p '{"spec": {"type": "NodePort"}}'

# Open an editor against the live object:
kubectl edit svc web-clusterip
```

`selector` and `type` can both be changed live — Kubernetes doesn't need to recreate the
Service object, it just starts routing differently on the next request. `ClusterIP` itself
(the virtual IP address, not the type) is immutable once assigned, though — changing that
does require delete/recreate.

### Session affinity

By default each request is load-balanced independently — consecutive requests from the
same client can land on different Pods. To pin a client to one Pod for the life of its
session instead:

```yaml
spec:
  sessionAffinity: ClientIP
```

### Delete

```bash
kubectl delete svc web-clusterip
# or, for anything applied from a file:
kubectl delete -f 01-clusterip.yaml
```

## Summary

| Type | Own ClusterIP? | Reachable from outside the cluster | Load-balanced |
|---|---|---|---|
| `ClusterIP` (default) | Yes | No | Yes, across matching Pods |
| `NodePort` | Yes | Yes — any node IP, high port | Yes |
| `LoadBalancer` | Yes | Yes — provisioned external IP/DNS (or `<pending>` locally) | Yes |
| Headless (`clusterIP: None`) | No | No | No — DNS returns every Pod IP directly |
| `ExternalName` | No | N/A — DNS alias to something already external | No — no Pods involved |

See [`services-demo/`](../services-demo) to apply all five and compare them against a live
cluster.
