# EBS — Security: encryption, KMS, IAM & threat models

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md), [snapshots-durability.md](snapshots-durability.md).

Spec section 6. EBS security is mostly **encryption (KMS) + who can create/attach/share volumes and snapshots**. The scary failure modes are *snapshot leakage* and *KMS key loss*.

---

## 1. Encryption at rest — how it actually works [Documented]

- EBS encryption uses **AES-256 (XTS)**, done **transparently on the Nitro card** at line rate → ~no CPU cost, no app changes.
- **Envelope encryption:** each volume gets a unique **data key (DEK)**; that DEK is itself encrypted by a **KMS key (CMK/KMS key)**. The Nitro card gets the decrypted DEK (via KMS, gated by IAM) to encrypt/decrypt I/O. The DEK never leaves the encryption boundary in plaintext at rest.
- **Encrypts:** data at rest on the volume, data **in transit between instance and volume**, all **snapshots** of the volume, and volumes created from those snapshots. Encryption is **inherited** down the snapshot→volume chain.
- **Encryption by default**: an account/Region setting so every new volume is encrypted with a default (or chosen) KMS key — set this org-wide. Once on, you can't create unencrypted volumes there.
- **You cannot un-encrypt** a volume in place; to change encryption/key you snapshot → copy with the new key → create a new volume.

## 2. KMS interactions & the sharp edges

- **Attaching an encrypted volume requires KMS permission** to use the key. If the KMS key is **disabled or its grant/permission is removed, the volume can't be attached/read** — an IAM/KMS misconfig looks like a storage outage. [Documented]
- **Deleting the KMS key = the data is gone.** No key, no DEK, no plaintext — unrecoverable. Treat KMS key lifecycle as data lifecycle; use key policies + `PendingDeletion` windows + CloudTrail alarms on `ScheduleKeyDeletion`.
- **Sharing encrypted snapshots:** you **cannot share a snapshot encrypted with the AWS-managed default key.** You must encrypt with a **customer-managed KMS key** and **share that key's grant** with the target account. Cross-account copy re-encrypts with the destination's key.

## 3. IAM & resource controls

- Gate volume/snapshot verbs: `ec2:CreateVolume`, `AttachVolume`, `CreateSnapshot`, `ModifySnapshotAttribute` (this one makes a snapshot **public/shared** — guard it hard), `ec2:CopySnapshot`, plus `kms:CreateGrant`/`Decrypt` on the key.
- Use **tag-based conditions** (`aws:ResourceTag`, `ec2:CreateAction`) and **enforce encryption** via IAM/SCP (`Deny CreateVolume` when `ec2:Encrypted=false`).
- **Block public sharing of snapshots** at the account level; audit for any snapshot with `createVolumePermission = all`.

## 4. Threat models

| Threat | Mechanism | Defense |
|---|---|---|
| **Snapshot exfiltration** | Attacker/insider shares a snapshot to their account or makes it public → recreates your DB | Deny `ModifySnapshotAttribute` broadly; block public sharing; encrypt with CMK (can't share without key grant); CloudTrail alarm |
| **Unencrypted data at rest** | Volume/snapshot never encrypted → raw data if storage/backups leak | **Encryption by default** + SCP denying unencrypted CreateVolume |
| **KMS key deletion / lockout** | Key deleted or permission pulled → data unrecoverable / outage | Key policy hygiene, deletion-window alarms, avoid single-person key control |
| **Orphaned volumes/snapshots** | Old detached volumes hold sensitive data + cost money | Lifecycle cleanup, tagging, Recycle Bin for recovery |
| **Cross-account copy leakage** | Sharing a CMK grant too broadly | Scope grants to specific accounts/actions; audit grants |
| **Boot-volume tampering (AMI)** | Malicious AMI/snapshot as a supply-chain vector | Use trusted/owned AMIs; verify; scan |

---

## Sources
- AWS docs: *Amazon EBS encryption*, *Encryption by default*, *Sharing encrypted snapshots*, *KMS envelope encryption*, *Block public access for snapshots*.
- Whitepaper: *AWS KMS Cryptographic Details*.

---

## Self-check
1. Walk envelope encryption for an EBS volume: what's the DEK, what's the KMS key, where does the plaintext DEK live and who uses it?
2. A volume suddenly can't attach and I/O fails, but nothing changed on the instance. What KMS-side causes would you check first?
3. Why can't you share a snapshot encrypted with the default AWS-managed key, and what's the correct way to share encrypted data cross-account?
4. Which single IAM action, if left ungoverned, most directly enables snapshot data exfiltration — and how do you contain it?
5. Your compliance team wants "no unencrypted EBS anywhere." Name the two controls (one account setting, one org guardrail) that enforce it.
