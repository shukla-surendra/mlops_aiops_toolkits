# VPC — Module 1 Gate

**Status:** 🟡 OPEN (awaiting learner answers)
**Covers:** [`../../docs/vpc/architecture.md`](../../docs/vpc/architecture.md)
**Rule:** Do not advance to M2 until these are answered and graded. Rough wording is fine — this checks the mental model, not phrasing.

> Write your answers under each question (or answer in chat). The mentor grades, patches gaps, then opens M2.

---

## Conceptual

**Q1.** Using the two-networks (overlay/substrate) model, explain *why* an instance can never sniff its neighbor's traffic even in promiscuous mode. Name the specific mechanism.

_Answer:_


**Q2.** The AWS control plane suffers a regional degradation — you can't launch new instances or modify Security Groups. Your *existing* instances keep serving traffic normally. Explain why, in terms of control plane vs data plane.

_Answer:_


## Scenario

**Q3.** A colleague says: "I'll just assign the public IP directly inside the guest OS with `ip addr add`, that's the same as an Elastic IP." Why is this wrong, what actually carries the public IP, and where does the translation happen?

_Answer:_


## Predict-the-behavior

**Q4.** Security Groups are stateful and enforced per-ENI at the host. Given that, predict: does adding 500 more instances to a Security Group degrade that SG's packet-filtering throughput? Why or why not? Contrast with a traditional centralized hardware firewall.

_Answer:_


---

### Grading (mentor fills in)
- Q1:
- Q2:
- Q3:
- Q4:
- **Verdict:** ⬜ Pass → open M2 · ⬜ Needs patch
