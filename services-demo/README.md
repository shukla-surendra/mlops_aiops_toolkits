# services-demo

Hands-on companion to [`docs/service-types.md`](../docs/service-types.md). One shared
Deployment, five Services in front of it — apply them one at a time and see exactly how
each `type` changes reachability. Every Pod serves its own hostname on `/`, so `curl`ing a
Service repeatedly shows the load-balancing (or lack of it) directly in the response body.

Assumes a running `minikube` cluster (`minikube status`).

## Setup

```bash
kubectl apply -f 00-deployment.yaml
kubectl get pods -l app=web-backend -o wide
```

Three `web-backend` Pods, each running `nginx:alpine` with its hostname baked into
`index.html`.

## Part 1 — `ClusterIP` (the default)

```bash
kubectl apply -f 01-clusterip.yaml
kubectl get svc web-clusterip
```

Only reachable from inside the cluster. Prove the load-balancing from a throwaway Pod:

```bash
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- \
  sh -c "for i in 1 2 3 4 5 6; do curl -s http://web-clusterip; done"
```

Expect a mix of hostnames across the six requests — one ClusterIP, traffic spread across
all three Pods behind it.

## Part 2 — `NodePort`

```bash
kubectl apply -f 02-nodeport.yaml
kubectl get svc web-nodeport
# PORT(S)  80:3XXXX/TCP  <- the auto-assigned high port
```

Everything `ClusterIP` gives you, plus the same port opened on **every node's** IP:

```bash
minikube service web-nodeport --url
curl "$(minikube service web-nodeport --url)"
```

Run the `curl` a few times — same load-balancing as Part 1, just reachable from outside
the cluster now via a node IP instead of only from inside.

## Part 3 — `LoadBalancer`

```bash
kubectl apply -f 03-loadbalancer.yaml
kubectl get svc web-loadbalancer
# EXTERNAL-IP stays <pending> - no cloud provider to hand out a real one
```

minikube can simulate a cloud load balancer with a tunnel (needs a separate terminal,
keeps running):

```bash
minikube tunnel
```

With the tunnel active, `EXTERNAL-IP` fills in and the Service is reachable directly:

```bash
kubectl get svc web-loadbalancer
curl http://<EXTERNAL-IP>
```

On a real cloud cluster (EKS/GKE/AKS) this same manifest provisions an actual external
load balancer with a public IP/DNS name — no `minikube tunnel` involved, that step only
exists because a laptop isn't a cloud provider.

## Part 4 — Headless Service (`clusterIP: None`)

```bash
kubectl apply -f 04-headless.yaml
```

Compare DNS resolution for the headless Service against the ClusterIP one from Part 1,
from inside the cluster:

```bash
kubectl run dns-test --image=busybox:1.36 --rm -it --restart=Never -- \
  sh -c "nslookup web-clusterip; echo ---; nslookup web-headless"
```

`web-clusterip` resolves to one virtual IP. `web-headless` resolves to **three** IPs — one
per Pod, no load-balancing IP in between. This is the mechanism StatefulSets rely on to
give each replica a stable, individually-addressable DNS name.

## Part 5 — `ExternalName`

```bash
kubectl apply -f 05-externalname.yaml
```

No selector, no endpoints, nothing proxied — just a DNS alias:

```bash
kubectl run dns-test --image=busybox:1.36 --rm -it --restart=Never -- \
  nslookup web-external.default.svc.cluster.local
```

Resolves as a CNAME to `example.com` instead of a Pod IP. This is how you give an
in-cluster name to something that lives outside the cluster (a managed database, a
legacy host) so app code always talks to a `.svc.cluster.local` name, whether the real
thing is in-cluster or not.

## Cleanup

```bash
kubectl delete -f 05-externalname.yaml
kubectl delete -f 04-headless.yaml
kubectl delete -f 03-loadbalancer.yaml
kubectl delete -f 02-nodeport.yaml
kubectl delete -f 01-clusterip.yaml
kubectl delete -f 00-deployment.yaml

# if you started one in Part 3:
# Ctrl-C the `minikube tunnel` terminal
```

## Reference

| File | Service `type` | Reachable from | Load-balanced |
|---|---|---|---|
| `01-clusterip.yaml` | `ClusterIP` (default) | Inside cluster only | Yes |
| `02-nodeport.yaml` | `NodePort` | Inside cluster + any node IP | Yes |
| `03-loadbalancer.yaml` | `LoadBalancer` | Inside cluster + external LB IP (cloud, or `minikube tunnel`) | Yes |
| `04-headless.yaml` | `ClusterIP: None` | Inside cluster only, resolves to Pod IPs directly | No — client picks |
| `05-externalname.yaml` | `ExternalName` | DNS alias only, no Pods involved | N/A |
