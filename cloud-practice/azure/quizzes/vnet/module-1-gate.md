# VNet — Module 1 Gate

**Status:** 🟡 OPEN (awaiting learner answers)
**Covers:** [`../../docs/vnet/architecture.md`](../../docs/vnet/architecture.md)
**Rule:** Do not advance to M2 until these are answered and graded. Rough wording is fine —
this checks the mental model and the AWS-contrast points specifically, not phrasing.

---

## Conceptual

**Q1.** VPC's Nitro card and Azure's SmartNIC solve the same underlying problem. State the
problem in one sentence, then name the one genuine hardware-strategy difference between how
AWS and Azure each solved it.

_Answer:_


**Q2.** Azure doesn't have a separately-named "Mapping Service" the way the VPC doc
describes for AWS. What Azure component actually does that job, and why is it described as
one pipeline rather than a separately-branded lookup service?

_Answer:_


## Scenario

**Q3.** You're migrating a 3-tier AWS VPC design (one subnet per AZ × 3 AZs, for the web
tier) to Azure and you recreate the same "one subnet per AZ" layout out of habit. Explain
specifically why this doesn't map the way it seems to, and what Azure's subnet/AZ model
actually expects instead.

_Answer:_


**Q4.** A colleague attaches an NSG to a subnet, allowing inbound port 443, and separately
attaches a *different* NSG to a NIC inside that subnet, which does **not** have a rule
allowing port 443 inbound. Will traffic on port 443 reach the VM? Explain using the
dual-attachment model, and contrast with how an AWS engineer might have expected this to
behave based on NACL + Security Group semantics.

_Answer:_


## Predict-the-behavior

**Q5.** Azure's control plane (ARM) has a regional degradation — you can't create or modify
NSGs or VNets. Predict what happens to packets already flowing between existing VMs, and
explain why, using the control-plane/data-plane split from §3a.

_Answer:_


---

### Grading (mentor fills in)
- Q1:
- Q2:
- Q3:
- Q4:
- Q5:
- **Verdict:** ⬜ Pass → open M2 · ⬜ Needs patch
