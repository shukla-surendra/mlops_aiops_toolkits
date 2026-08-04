# VPC — Module 2 Gate

**Status:** 🟡 OPEN
**Covers:** [`../../docs/vpc/networking.md`](../../docs/vpc/networking.md) + the Terraform in [`../../terraform/vpc/`](../../terraform/vpc/)
**Rule:** Clear this before M3 (Security Groups vs NACLs internals, ENI, Flow Logs).

---

## Conceptual

**Q1.** There is no checkbox that makes a subnet "public." Define precisely what makes a subnet public vs private, and give the *three* conditions that must ALL be true for an instance to be reachable from the internet.

_Answer:_


**Q2.** A private instance reaches `8.8.8.8` through a NAT Gateway. Explain why the packet takes **two** NAT hops (NAT GW *then* IGW), and what address the packet has after each hop. How does return traffic find its way back?

_Answer:_


## Scenario

**Q3.** Your app in private subnets pushes 40 TB/month to S3 and the NAT Gateway bill is huge. What single, near-zero-cost change fixes this, why does it work (in terms of route tables), and what's the one AWS-service limitation of that endpoint type?

_Answer:_


**Q4.** Org has VPC-A ↔ VPC-B peered and VPC-B ↔ VPC-C peered. A team says "so A can reach C through B." Are they right? Explain the property involved and what you'd deploy instead for a 20-VPC org.

_Answer:_


## Terraform / predict-the-behavior

**Q5.** In `main.tf`, the data-tier route tables intentionally have no `0.0.0.0/0` route. A developer adds a NAT route to the data RT "to install OS packages." What tier boundary did they just break, and what's the safer way to let the data tier fetch packages/backups?

_Answer:_


**Q6.** Flip `single_nat_gateway` from `true` to `false` with 3 AZs. Predict exactly which resources change count and by how much (NAT GWs, EIPs, `app_default` routes), and what real-world failure this protects against.

_Answer:_


---

### Grading (mentor fills in)
- Q1: · Q2: · Q3: · Q4: · Q5: · Q6:
- **Verdict:** ⬜ Pass → open M3 · ⬜ Needs patch
