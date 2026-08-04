# Terraform: 3-tier VPC

Builds the canonical multi-AZ, 3-tier VPC from [`../../docs/vpc/networking.md §5`](../../docs/vpc/networking.md): public / app / data tiers across N AZs, with IGW, NAT Gateway(s), tiered Security Groups, and a free S3 Gateway Endpoint.

> ⚠️ **This creates billable resources.** NAT Gateways and Elastic IPs cost money even when idle (~$32/mo per NAT GW + data). Run `terraform destroy` when done. For pure config learning, `terraform plan` alone costs nothing.

## What it creates

```
VPC 10.0.0.0/16
├── public/<az>   (10.0.0.0/24 …)   RT → IGW           [NAT GW + EIP live here]
├── app/<az>      (10.0.10.0/24 …)  RT → NAT GW + S3 endpoint
└── data/<az>     (10.0.20.0/24 …)  RT → local only (sealed from internet)
SGs: alb (80/443 from internet) → app (8080 from alb) → data (5432 from app)
```

## Files

| File | Purpose |
|---|---|
| `versions.tf` | Terraform + AWS provider pins, provider + default tags |
| `variables.tf` | All knobs (region, AZs, CIDR, single-vs-per-AZ NAT, endpoint toggle) |
| `main.tf` | VPC, IGW, subnets, NAT GWs, route tables + associations |
| `endpoints.tf` | S3 Gateway Endpoint (free NAT-bypass for S3) |
| `security_groups.tf` | Tiered SGs chained by reference (ALB→app→data) |
| `outputs.tf` | IDs + NAT egress IPs for downstream use |
| `terraform.tfvars.example` | Copy → `terraform.tfvars` and edit |

## Usage

```bash
cd aws/terraform/vpc
cp terraform.tfvars.example terraform.tfvars   # edit as needed

terraform init
terraform validate
terraform plan          # inspect — costs nothing
terraform apply         # creates real resources ($$)

terraform output        # see IDs, NAT egress IPs
terraform destroy       # ALWAYS clean up
```

Requires AWS credentials (`aws configure`, `AWS_PROFILE`, or an assumed role) and permission to manage VPC resources.

## Things to try (turns this into a lab)

1. `plan` with `single_nat_gateway = true` vs `false` — diff the NAT GW / EIP / route counts. This is the HA-vs-cost tradeoff made concrete.
2. Set `enable_s3_gateway_endpoint = false` and diff — see the endpoint + its route-table associations vanish.
3. Drop `azs` to 2 entries — watch every `count`-driven resource fan back in.
4. Trace one app subnet's route table in the plan: confirm `0.0.0.0/0 → nat`, `local`, and the S3 prefix-list route all appear.

## Deliberately out of scope (later modules)

- No EC2/ALB/RDS yet — this is the *network substrate* only.
- Interface Endpoints, NACLs, VPC Flow Logs → M3 (`security.md`).
- Remote state backend (S3 + DynamoDB lock) → M5. This example uses local state.
