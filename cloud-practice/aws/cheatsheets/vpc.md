# VPC Cheatsheet

One-page recall. Full detail in [`../docs/vpc/`](../docs/vpc/README.md).

## Mental model
- **Two networks:** overlay (your VPC, fake) rides the substrate (physical, real) via **encapsulation**. Mapping Service = virtual→physical directory. Data plane on **Nitro card**.
- **VPC = distributed lookup + packet rewriter that fakes a network.**

## Reserved IPs (per subnet)
`.0` network · `.1` router · `.2` DNS (base+2) · `.3` reserved · `.last` broadcast → **/24 = 251 usable**, /28 (min) = 11.

## Routing
- Every subnet → exactly 1 route table; `local` (VPC CIDR) is **immutable**.
- **Longest-prefix-match wins.**
- "Public subnet" = route table has `0.0.0.0/0 → IGW`. Nothing else.

## Gateways / egress
| Need | Use |
|---|---|
| Public in+out | IGW (1:1 NAT, free, public IP lives here not in OS) |
| Private egress only | NAT GW (per-AZ, hourly + per-GB, **#1 hidden cost**) |
| S3 / DynamoDB privately | **Gateway endpoint** (route entry, FREE) |
| Other AWS svc privately | **Interface endpoint** (ENI/PrivateLink, per-AZ-hr + per-GB) |
| VPC↔VPC (few) | Peering (non-transitive, no CIDR overlap) |
| VPC↔VPC (many)/hybrid | Transit Gateway (transitive, segmentable) |
| IPv6 egress | Egress-only IGW (free) |

## Internet-reachable triple
public IP/EIP **+** route to IGW **+** SG/NACL allow. (all three)

## SG vs NACL
| | SG | NACL |
|---|---|---|
| On | ENI | Subnet |
| State | Stateful | Stateless (open ephemerals!) |
| Rules | Allow only | Allow + Deny, numbered |
| Ref SG | Yes | No |
Lead with **SGs** (least privilege, reference by SG ID). NACLs = blunt guardrail.

## DNS
- Resolver at **base+2** / `169.254.169.253`. IMDS = `169.254.169.254`.
- Need **both** `enableDnsSupport` + `enableDnsHostnames` for PHZ / endpoint private DNS.

## Cost traps
NAT GW bytes · cross-AZ transfer (each way) · internet egress · interface endpoints × AZ · TGW per-GB · Flow Logs. Fix: endpoints, AZ-locality, IPv6, CloudFront. Watch `NatGateway-Bytes` in CUR.

## Debugging chain (in order)
listen? → route → return route → SG → NACL(ephemeral) → public triple → DNS → NAT/`pkt-srcaddr`.
Tools: **Reachability Analyzer** (proves path) · **Flow Logs** (did it arrive, ACCEPT/REJECT) · **SSM** (`ss -tlnp`, `dig`, `nc -vz`, `tcpdump`).
Gotchas: subnet uses **main RT** if unassociated · disable **source/dest check** on appliances · NAT SNAT `ErrorPortAllocation` · `conntrack_allowance_exceeded`.

## CLI quickies
```bash
aws ec2 describe-vpcs --query 'Vpcs[].{Id:VpcId,Cidr:CidrBlock}'
aws ec2 describe-route-tables --filters Name=vpc-id,Values=vpc-xxx
aws ec2 describe-security-groups --group-ids sg-xxx
aws ec2 describe-network-interfaces --filters Name=vpc-id,Values=vpc-xxx
# Prove reachability
aws ec2 create-network-insights-path --source i-src --destination i-dst \
  --protocol tcp --destination-port 5432
```

## Terraform primitives
`aws_vpc` · `aws_subnet` · `aws_internet_gateway` · `aws_eip`+`aws_nat_gateway` · `aws_route_table`(+`aws_route`,`aws_route_table_association`) · `aws_vpc_endpoint` · `aws_security_group`+`aws_vpc_security_group_{ingress,egress}_rule`. Example: [`../terraform/vpc/`](../terraform/vpc/README.md).

## Internals name-drops
Mapping Service (directory) · Hyperplane (stateful NAT/LB fabric: NAT GW, NLB, PrivateLink, EFS) · Blackfoot (edge/border NAT) · Nitro card (data plane) · ENA (guest NIC) · BGP (hybrid route propagation).
