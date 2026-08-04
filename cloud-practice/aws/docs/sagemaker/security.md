# SageMaker — Security

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md); [VPC security](../vpc/security.md), [IAM concepts].

Spec section 6. SageMaker security = **execution roles (what jobs/endpoints can do) + VPC/network isolation (where they run) + KMS (data at rest) + tenant isolation**.

---

## 1. Execution roles — the core of SageMaker IAM [Documented]
- Every job/endpoint/notebook runs with a **SageMaker execution role** (an IAM role SageMaker assumes). It defines what the *compute* can touch: which **S3** buckets (data + model), **ECR** (pull image), **KMS** keys, **CloudWatch**, etc.
- **Two identities to reason about:** (a) the **user/role that calls the SageMaker API** (can they `CreateTrainingJob`, `CreateEndpoint`?), and (b) the **execution role** the job then runs as. Least-privilege both.
- **Common mistake:** giving the execution role `AmazonS3FullAccess` / `AdministratorAccess`. Scope it to the specific buckets/keys. A training container runs arbitrary code — treat its role as attacker-reachable.

## 2. Network posture [Documented]
- **Default:** jobs/endpoints run in a **SageMaker-managed account** with internet access, reaching S3 over AWS's network.
- **VPC mode:** attach **ENIs into your VPC** (subnets + security groups) so compute can reach **private** resources (RDS, internal APIs) and so traffic is governed by your SGs/NACLs.
- **Network isolation:** run containers with **no inbound/outbound network at all** (no internet) — the container can't call out; data comes only via the mounted channels. Combine VPC mode + isolation + **VPC endpoints** (S3 gateway, `sagemaker.api`/`sagemaker.runtime` interface endpoints) for a fully private, exfiltration-resistant setup — the regulated-data pattern (ties to your [VPC endpoints](../vpc/networking.md) study).
- **Studio** can also run in VPC-only mode (no public internet).

## 3. Encryption [Documented]
- **At rest:** KMS for the ML storage volumes on jobs/endpoints, model artifacts in S3, notebook storage, and Feature Store. Use customer-managed keys for control/audit.
- **In transit:** TLS to the endpoints and between distributed-training nodes (**inter-container traffic encryption** option for multi-node jobs handling sensitive data — adds overhead).
- **Data in S3:** encrypt buckets; the execution role needs `kms:Decrypt` on the key (a disabled key = job fails to read data — same failure mode as EBS/EFS).

## 4. Data protection & tenancy
- **VPC endpoint policies + `aws:SourceVpc`** on data buckets → a compromised training container can't exfiltrate to arbitrary S3 (data-perimeter pattern).
- **Multi-tenant:** separate execution roles + buckets + KMS keys per team/tenant; consider separate accounts for strong isolation. Network isolation prevents a job from phoning home.
- **Studio user isolation:** per-user execution roles / spaces; don't share one powerful role across a team.

## 5. Threat models

| Threat | Mechanism | Defense |
|---|---|---|
| **Over-privileged execution role** | Container code exfiltrates via broad S3/network access | Scope role to specific buckets/keys; VPC + network isolation |
| **Malicious/poisoned container or model** | Supply-chain: bad image or model artifact runs your code | Trusted ECR images, scan, sign; least-priv role limits blast radius |
| **Data exfiltration** | Training job uploads data to attacker S3/endpoint | Network isolation, VPC endpoints + `aws:SourceVpc`, egress controls |
| **Public endpoint exposure** | Endpoint/API reachable too broadly | IAM auth on `InvokeEndpoint`; keep in VPC; no public exposure |
| **Notebook as a foothold** | Long-lived notebook with a powerful role + internet | Idle shutdown, scoped roles, VPC-only Studio |
| **Secrets in code/notebooks** | Hardcoded keys | Secrets Manager, roles not keys |

---

## Sources
- AWS docs: *SageMaker Roles*, *Give SageMaker access to resources in your VPC*, *Network isolation*, *Protect data with encryption*, *Infrastructure security in SageMaker*, *Connect to SageMaker through a VPC endpoint*.

---

## Self-check
1. Name the two distinct IAM identities in a SageMaker training job and why you least-privilege both.
2. What does "network isolation" actually prevent, and how do you still get data into such a job?
3. Design the fully-private setup for training on regulated data (VPC mode + which endpoints + which isolation).
4. An encrypted-S3 dataset makes a training job fail to start. What KMS-side cause do you check?
5. Which two controls stop a compromised training container from exfiltrating your data to an external bucket?
