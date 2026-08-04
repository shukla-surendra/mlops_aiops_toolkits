# 5. Internals & Tool Comparison

> How Terraform works under the hood, how it talks to AWS, Terraform vs CloudFormation vs CDK, use cases, case studies, and a consolidated interview Q&A bank.

Related: [Fundamentals](01-fundamentals.md) · [State & backends](02-state-and-backends.md)

---

## How Terraform works internally

Terraform is not just a template runner. Internally each run:

1. Reads the root module and child modules
2. Parses variables, locals, data sources, resources, outputs
3. Resolves provider requirements and versions
4. Downloads or reuses provider plugins during `terraform init`
5. Reads current state from the backend
6. Builds a dependency graph
7. Asks providers to refresh/read real infrastructure
8. Compares desired config with current state
9. Produces an execution plan
10. Executes the graph in dependency order
11. Updates state after successful operations

```text
HCL Configuration → Terraform Core → Provider Plugin (AWS) → AWS APIs → Real AWS Resources
```

## How Terraform communicates with AWS

Terraform Core does **not** call AWS APIs directly. It talks to the **AWS provider plugin** (over RPC). The provider:

- Authenticates to AWS
- Calls AWS APIs (via the AWS SDK)
- Translates resource blocks into API operations
- Reads current attributes back from AWS
- Returns results to Core, which updates state

```text
resource "aws_s3_bucket" "logs"
        │
Terraform Core
        │
AWS Provider Plugin
        │
AWS SDK / AWS APIs
        │
Amazon S3
```

This separation is why Terraform supports many providers, not just AWS.

### Core vs provider plugin

| Terraform Core | Provider plugin |
|----------------|-----------------|
| Read configuration, evaluate expressions | Understand a specific platform (e.g. AWS) |
| Build the dependency graph | Authenticate to that platform |
| Manage state | Map resources/data sources to API calls |
| Create the plan, decide ordering | Handle create/read/update/delete |
| Coordinate plugins over RPC | — |

### Execution model

Terraform builds a resource graph from references (attributes, module outputs, data sources, explicit `depends_on`). Independent resources can run in **parallel**; dependent ones run in order — one reason Terraform scales better than naive scripting.

```text
VPC → Subnets → Security Group → ECS Service
```

---

## Terraform vs CloudFormation vs CDK

### Terraform
- HCL, provider plugins, works across many clouds and SaaS platforms
- Keeps its own state; produces a plan before apply
- Strong ecosystem for multi-cloud and shared modules

### AWS CloudFormation
- AWS-native IaC service; YAML/JSON templates
- Manages infrastructure as CloudFormation **stacks**; AWS handles orchestration and rollback
- No separate state backend to manage; best aligned with AWS-native governance

### AWS CDK
- Define infrastructure in general-purpose languages (TypeScript, Python, Java, C#, Go)
- Uses constructs/abstractions, **synthesizes to CloudFormation**, deploys through CloudFormation
- Best when app developers want familiar languages and higher-level constructs

> **Important:** CDK is *not* an alternative deployment engine to CloudFormation. CDK **generates** CloudFormation; CloudFormation performs the deployment.

### Where each is stronger

| | Stronger at | Trade-offs |
|--|-------------|-----------|
| **Terraform** | Multi-cloud, one workflow across AWS/Azure/GCP/K8s/SaaS, readable HCL, strong module model, clear plan step | You operate a state backend |
| **CloudFormation** | Native AWS lifecycle integration, no state backend to manage, AWS-only governance | AWS only; large templates get unwieldy |
| **CDK** | Familiar languages, loops/abstractions/composition, less boilerplate | More software complexity in infra; still AWS-only via CloudFormation |

### Which to choose

- **Multi-cloud / AWS + SaaS / platform standardization** → Terraform
- **AWS-only, staying fully AWS-native, no separate state strategy** → CloudFormation
- **AWS-only, developers want infra in code with reusable constructs** → CDK

Rules of thumb: *most enterprise platform teams* → Terraform; *AWS-only developer productivity* → CDK; *AWS-native managed stack orchestration* → CloudFormation.

---

## Use cases

**Terraform:** shared networking, multi-account AWS foundations, Kubernetes + cloud resources, cross-cloud DR, managing SaaS (Datadog, GitHub, Cloudflare, Snowflake), standardized reusable modules.

**CloudFormation:** AWS-only infrastructure as stacks, orgs standardized on AWS-native controls, service integrations that assume CloudFormation stacks.

**CDK:** application teams creating AWS resources alongside app code, reusable internal AWS constructs, developer-centric teams comfortable in TS/Python/Java/C#/Go.

---

## Case studies

| Scenario | Good fit | Why |
|----------|----------|-----|
| Startup, AWS-only, mostly developers, speed over shared standards | **CDK** | Familiar languages, constructs reduce boilerplate, app + infra in one codebase |
| Mid-size, shared platform team, 20+ apps, multiple environments | **Terraform** | Clear module ownership, root-module/state isolation, easier shared standards |
| Enterprise, AWS-only, strict governance & stack operations | **CloudFormation or Terraform** | CFN fits AWS-native operating models; Terraform wins if many teams need a stronger plan workflow + module ecosystem |
| Multi-cloud platform (AWS + Azure/GCP), shared policy/naming | **Terraform** | One tool, one language, many providers; consistent state and module patterns |

**Tool-selection best practices:** optimize for operating model not hype; pick one primary IaC standard per platform area; avoid mixing tools for the same workload without a clear reason; standardize review, tests, and pipelines regardless of tool.

---

## Terraform best practices for AWS

- Use remote state with locking; isolate state by deployable unit + environment
- Pin Terraform and provider versions
- Use reusable modules for shared patterns; keep root modules small
- Save reviewed plans for production changes
- Validate variables; mark sensitive variables and outputs
- Prefer IAM roles over long-lived access keys
- Tag everything consistently
- Avoid ad hoc `terraform state` surgery; prefer declarative `import` blocks
- Run `terraform fmt`, `validate`, and `test` in CI/CD

---

## Interview Q&A

### Conceptual
1. **Difference between Terraform Core and a provider plugin?** Core reads config, builds the graph, manages state, and plans; the provider authenticates to a platform and maps resources to API calls. They communicate over RPC.
2. **Why does Terraform need state?** To map configuration to real infrastructure and calculate changes without rediscovering everything each run.
3. **How does Terraform know creation order?** It builds a dependency graph from references and `depends_on`, then executes in order (independent resources in parallel).
4. **Root module vs child module?** The root module is where you run Terraform; child modules are reusable building blocks it calls.
5. **Why shouldn't unrelated systems share one state?** It increases blast radius, slows plans, causes lock contention, and blocks independent team deployments.

### AWS-specific
1. **How does Terraform communicate with AWS?** Core talks to the AWS provider plugin over RPC; the provider calls AWS APIs via the SDK and returns results to Core, which updates state.
2. **Role of the AWS provider?** Authenticate, translate resource blocks to API calls, handle CRUD, read current attributes.
3. **Why is remote state important on AWS?** Shared, versioned, encrypted, and lockable state enables safe team collaboration.
4. **Why `use_lockfile = true` in the S3 backend?** It provides native S3 state locking (replacing deprecated DynamoDB locking) to prevent concurrent-apply corruption.
5. **When choose CloudFormation or CDK over Terraform?** AWS-only + AWS-native governance → CloudFormation; AWS-only + developers wanting infra in a programming language → CDK.

### Comparison
1. **CDK vs CloudFormation?** CDK is a framework to define infra in general-purpose languages; it synthesizes CloudFormation, which does the deployment.
2. **Terraform vs CloudFormation?** Terraform is multi-cloud with its own state and plan workflow; CloudFormation is AWS-native with managed stacks and no separate state.
3. **Why Terraform in multi-cloud orgs?** One tool/language/workflow across many providers with reusable modules.
4. **Why might app teams prefer CDK?** Familiar languages, loops, abstractions, and higher-level constructs.
5. **Is CDK a replacement for CloudFormation?** No — CDK generates CloudFormation; CloudFormation deploys.

### Scenario-based
1. *80 AWS accounts wanting common networking standards* → Terraform with versioned shared modules and per-account/per-env isolated state.
2. *AWS-only startup, all engineers write TypeScript* → CDK, for developer ergonomics and shared codebase.
3. *Bank wanting strict AWS-native, stack-based governance* → CloudFormation is a strong fit.
4. *Team already uses Terraform for AWS + Datadog + GitHub — add CDK for one app?* → Prefer staying consistent unless there's a clear, compelling reason.

---

## Final mental model

```text
Application Repository   →  what should exist
Root Module             →  assembles reusable modules
Reusable Modules        →  how common infrastructure is built
Terraform Plan          →  preview of changes
Remote State            →  what already exists
Provider                →  talks to cloud APIs
AWS Infrastructure      →  the real thing
```

If you're learning for interviews: understand the internals at a high level, explain provider plugins and state clearly, know CDK deploys through CloudFormation, never answer "which is best" with a blanket statement, and tie recommendations to team structure, cloud scope, and governance. If you're building a real platform: standardize on the fewest IaC tools possible, favor clarity over clever abstractions, and design around ownership, state isolation, and repeatable delivery.
