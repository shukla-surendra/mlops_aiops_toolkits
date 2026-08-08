# Entra ID + Azure RBAC — Module 1 Gate

**Status:** 🟡 OPEN (awaiting learner answers)
**Covers:** [`../../docs/entra-id/architecture.md`](../../docs/entra-id/architecture.md)
**Rule:** Do not advance to M2 until these are answered and graded. Rough wording is fine —
this checks the mental model and the AWS-contrast points specifically, not phrasing.

---

## Conceptual

**Q1.** Explain, in your own words, why Entra ID and Azure RBAC are two separate systems
rather than one bundled identity+authorization service the way AWS IAM is. What real
capability does that separation buy Azure that a bundled model wouldn't?

_Answer:_


**Q2.** A role assignment grants `Contributor` (full management-plane `Actions`, no
`DataActions`) on a Storage Account. Can the assignee read the actual bytes of a blob inside
that account? Why or why not, and what would need to be added if not?

_Answer:_


## Scenario

**Q3.** Your team publishes a multi-tenant SaaS app registered in your Entra ID tenant. A
customer in a different tenant installs it. Explain what object gets created in the
customer's tenant, why it's a separate object rather than a reference to your original App
Registration, and why AWS IAM has no clean equivalent to point to here.

_Answer:_


**Q4.** You need a VM to read secrets from Key Vault with no credentials stored anywhere,
and you want the credential to be automatically destroyed if the VM is deleted. Which kind
of Managed Identity do you use, and why would a user-assigned identity be the wrong choice
for this specific requirement?

_Answer:_


## Predict-the-behavior

**Q5.** A user has valid credentials and a Contributor role assignment that should let them
manage a VM, but they're signing in from an unmanaged personal device flagged as
non-compliant. Predict whether the operation succeeds, and explain which layer (Entra ID or
Azure RBAC) is responsible for blocking it, and why that layering makes it possible to
enforce this consistently across Azure *and* Microsoft 365 with one policy.

_Answer:_


---

### Grading (mentor fills in)
- Q1:
- Q2:
- Q3:
- Q4:
- Q5:
- **Verdict:** ⬜ Pass → open M2 · ⬜ Needs patch
