# EFS — Security: mount targets, encryption, IAM, Access Points

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md); [VPC security](../vpc/security.md) (SGs gate NFS).

Spec section 6. EFS security = **network (who can reach 2049) + encryption (at rest + in transit) + identity (IAM + POSIX + Access Points)**.

---

## 1. Network — the mount target Security Group [Documented]

- A client can only mount if it can reach the AZ's **mount target ENI on TCP 2049 (NFS)**. That's gated by the **Security Group on the mount target**.
- **Best practice:** give the mount target an SG that allows **2049 only from the client instances' SG** (SG-referencing, like the VPC docs), not a CIDR, and never `0.0.0.0/0`. An open 2049 is a data-exposure hole.
- Subnet **NACLs** must also allow 2049 + ephemeral ports (stateless — see [VPC security](../vpc/security.md)).

## 2. Encryption [Documented]

- **At rest:** enabled at filesystem creation, using **KMS** (AES-256). Transparent; can't be added to an existing unencrypted filesystem (recreate + copy). Turn it on always.
- **In transit (TLS):** mount with **`amazon-efs-utils`** and the **`-o tls`** option — it runs a local stunnel that wraps NFS in TLS to the mount target. Not on by default with a plain `nfs4` mount, so **use efs-utils and `tls`** for sensitive data.
- **Enforce TLS** via the filesystem policy (below): deny any mount that isn't using `aws:SecureTransport`.

## 3. Identity — POSIX, IAM & Access Points

- **POSIX permissions** work as normal (uid/gid/mode). But by default any client that can reach 2049 mounts the **root** of the filesystem and enforces its *own* uids — weak isolation in multi-tenant/container settings.
- **EFS Access Points** [Documented] fix this: an Access Point is an application-specific entry that **enforces a POSIX user/group and a root directory** for anything mounting through it. So container A mounts through AP-A and is *pinned* to `/app-a` as uid 1001, container B to `/app-b` — clean multi-tenant isolation on one filesystem. This is the standard pattern for **EKS/ECS** persistent volumes.
- **IAM authorization** [Documented]: mount with `-o iam` (efs-utils) so the client authenticates with its **IAM role**, and control access with a **filesystem resource policy** (e.g., "only these roles may mount," "require TLS," "read-only for role X"). Combines with Access Points for identity + path + permission control.

### Example filesystem policy intent
- Deny all non-TLS mounts (`aws:SecureTransport = false` → Deny).
- Allow `elasticfilesystem:ClientMount`/`ClientWrite` only to specific role ARNs.
- Optionally require access via a specific Access Point.

## 4. Threat models

| Threat | Mechanism | Defense |
|---|---|---|
| **Open NFS port** | SG allows 2049 from too-wide a range → anyone in the VPC mounts your data | SG 2049 from client SG only; never `0.0.0.0/0` |
| **Plaintext NFS** | Data + file handles in the clear on the wire | Mount `-o tls` (efs-utils); enforce via policy |
| **Unencrypted at rest** | Filesystem created without KMS | Encrypt at creation; org guardrail to require it |
| **Weak multi-tenant isolation** | Every client mounts root with its own uids | **Access Points** (enforced uid + root dir) + IAM policy |
| **Over-broad mount rights** | Any role can mount read/write | Filesystem policy scoped to specific roles + read-only where possible |
| **Data exfil to another account** | (EFS isn't shared cross-account like snapshots, but VPC peering/TGW could expose 2049) | Keep mount-target SGs tight; segment networks |

---

## Sources
- AWS docs: *EFS encryption (rest + transit)*, *EFS Access Points*, *IAM authorization for NFS clients*, *Filesystem policies*, *Controlling network access to mount targets*.

---

## Self-check
1. What single Security Group rule design safely controls who can mount an EFS filesystem, and what must you avoid?
2. Two ways EFS data can be exposed if you "just mount it" — one network, one crypto. How do you close each?
3. You run 50 containers on one EFS filesystem and need each pinned to its own directory + uid. Which feature, and how does it enforce isolation?
4. Write (in words) the filesystem policy that guarantees no one can mount without TLS.
5. Why is `-o tls` not automatic, and which package enables it?
