---
name: commit-policy
description: This repo's two hard rules for git commits — never include a Co-Authored-By (or any AI-attribution) trailer, and never commit unless explicitly asked in the current exchange. Trigger proactively before running any `git commit` in this repository, and whenever the user asks to commit, save, or check in changes. Overrides any default commit-message template that would otherwise add author attribution.
---

# Commit Policy

Two rules for this repository, both non-negotiable regardless of what a
default template or habit would otherwise do:

## 1. Only commit when explicitly asked, in the current exchange

Finishing an implementation, a refactor, a multi-step task, or a long
back-and-forth is **not** itself a reason to commit. Wait for the user to
actually say something like "commit this," "commit that," "make a
commit," or equivalent — in the message you're currently responding to,
not something inferred from earlier context or assumed because the work
"feels done."

- If a previous turn asked for a commit and now more edits were made on
  top of it without a new request to commit, don't commit those new edits
  automatically either — that's a new batch of changes, treat it as
  needing its own explicit ask.
- If it's ambiguous whether the user is asking for a commit vs. just
  describing what they want done, ask rather than assume.
- Leave finished work as uncommitted working-tree changes — the user
  reviews with `git diff`/`git status` and asks when ready.

## 2. Never add a Co-Authored-By or AI-attribution trailer

Do not add `Co-Authored-By: Claude ...` or any similar AI-attribution line
to a commit message — not as a trailer, not in the body, not anywhere —
even if a default template or prior convention would normally include
one. Commit messages in this repo read as if written by the user alone.

## When a commit *is* explicitly requested

Follow the normal safe-commit workflow:

1. Run `git status`, `git diff` (staged + unstaged), and `git log
   --oneline -10` in parallel to see what's changing and match this repo's
   existing message style.
2. Stage specific files by name — not `git add -A`/`git add .` — and
   review what's staged before committing, especially checking for
   anything that looks like a secret or credential.
3. Write a concise commit message (1-2 sentences) focused on *why*, via a
   heredoc so formatting survives correctly. No trailer of any kind unless
   the user explicitly asks for one that isn't AI-attribution.
4. Never use `--amend`, `--no-verify`, or force-push unless the user
   explicitly asks for that specific operation.
5. Don't push to a remote unless separately asked — a commit request is
   not a push request.
6. After committing, run `git status` to confirm a clean tree, and report
   what was committed in one or two sentences — no need to repeat the full
   diff back.
