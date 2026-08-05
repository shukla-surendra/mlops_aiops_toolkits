---
name: engineering-fundamentals
description: Two modes for engineering_fundamentals/ interview-prep content (DSA, ML/LLM + distributed system design, LLD). Mode 1 ("articulate it") adds/refreshes the "Articulate It: Interview Framing & Vocabulary" closing section on a tutorial/problem/concept-primer doc, and covers authoring a new first-principles concept-primer doc from scratch — use when a doc under system_design/, system_design_practice/, or dsa_prep/ is created or substantially rewritten, or when asked to "add articulate it" / explain something "from first principles" for this repo. Mode 2 ("mock interview") runs a live mock system design interview at senior/staff/principal bar, or a rapid-fire fundamentals quiz, using this repo's tutorials as question bank and hidden answer key — use for "quiz me", "mock interview me", "practice a design question", "grill me on fundamentals". Do not use Mode 2 for passively explaining a design — that's just reading the tutorial.
---

# Engineering Fundamentals

Two independent modes over the same content tree. Pick based on what's
being asked — first-principles doc authoring, or a live interview
simulation.

## Shared context

- `system_design/` (incl. `prerequisite_concepts/`) — ML/LLM system
  design tutorials, deep-dives, `12_tricky_scenarios/` incidents.
- `system_design_practice/` — general distributed-systems case studies,
  incl. `00_staff_level_signal/tutorial.md` (the senior/staff/principal
  rubric Mode 2's debrief uses).
- `dsa_prep/` — LeetCode-style `problem.md` / `PATTERN.md` files.
- One MkDocs site per tree (`docs_dir: .`) — always plain relative links
  between top-level folders, never a hardcoded `127.0.0.1:PORT` URL.
- Pure index files (`README.md`, `TOP_LIST.md`) never get an Articulate It
  section — no explanatory content there to reframe.

---

## Mode 1 — Articulate It (doc authoring)

Every substantive doc ends with a closing section helping the reader (a)
explain the same content multiple ways depending on how an interview is
going, and (b) pick up precise shorthand + fluent vocabulary. Heading text
must match **exactly** (greppable across ~150 files):

```markdown
## Articulate It: Interview Framing & Vocabulary

### Three Ways to Explain This

- **[framing label] (the default for ...):** "[first-person spoken quote]"
- **[framing label] (good for ...):** "[quote]"
- **[framing label] (good for ...):** "[quote]"

### Vocabulary Builder

- **term** (n./v./adj.) — definition. *"Example sentence."*
- **"a reusable spoken phrase…"** — why/when to use it.
```

**Three content modes, pick by which tree the doc is in:**

- **A. `system_design/` + `system_design_practice/`** — three genuinely
  distinct angles (trade-off-first, narrative/incident-first, business-
  impact-first, numbers-first, systems-first, or risk-first — whichever
  three fit *that* doc). Vocabulary: ~4-6 items, split technical shorthand
  + expressive phrases. Length proportional to the doc (~25-45 lines for a
  full tutorial).
- **B. `dsa_prep/`** — coding-interview framings: brute-force-first (name
  naive + complexity before optimizing), invariant/correctness (what
  property does the loop maintain), pattern-recognition (name the broader
  technique, reference the sibling `PATTERN.md`). `problem.md`: ~3
  framings + ~4 vocab items (~40-50 lines total). `PATTERN.md`: richer,
  ~4-5 vocab items, framings about the pattern itself (~70-80 lines).
- **C. `system_design/prerequisite_concepts/`** ("Part N" docs) — covers
  the **whole doc's authoring pattern**, not just the closing section,
  since this tree teaches foundational concepts everything else assumes.
  This is also the general **first-principles explanation pattern** to
  reuse for *any* new from-scratch explanation in this repo, not only
  this tree:
  - 1-2 sentences of framing: what this covers, what it assumes, link to
    the previous part.
  - Body organized one concept per `##` section, always **problem →
    mechanism → why it matters practically** — never define a term and
    stop; answer "why does this exist" before "what is it." Prefer a
    concrete worked example with real/illustrative numbers over an
    abstract definition.
  - Cross-reference relentlessly, both within the primer and out to
    tutorials/scenarios elsewhere that assume the concept.
  - State numeric claims (hardware specs, pricing, bandwidth) as
    **illustrative and approximate**, explicitly — the relationship, not
    the specific number, is the point.
  - Ends with `## Quick Self-Check` (not "Practice Questions" — this tree
    teaches concepts, not case studies), then `## Articulate It`, then the
    nav footer.
  - **Wire it in fully**: update adjacent parts' nav-footer Prev/Next
    links, add to `mkdocs-system-design.yml`'s `nav:`, update
    `system_design/README.md`'s part list, cross-link from any doc
    elsewhere with a real-world tie-in. Run
    `mkdocs build -f mkdocs-system-design.yml --strict -d /tmp/<dir>`
    afterward and grep the built HTML's `id="..."` for anchor links
    rather than hand-guessing a slug (mkdocs lowercases, spaces→single
    dash, strips `/` and `&` without adding a second dash).

For Mode C's own closing section, follow Mode A's structure — same
audience/voice, just explaining a concept instead of a system.

**Procedure:**

1. Read the target file in full — never draft from memory of a similar
   file.
2. Draft the section to a scratch file outside the repo.
3. Insert with the bundled script (nav footers use non-breaking spaces
   around `|`, which breaks naive string-matching):
   ```bash
   python3 .claude/skills/engineering-fundamentals/scripts/insert_section.py <scratch.md> <target.md>
   ```
   Add `--replace` if refreshing an existing section.
4. Verify: `grep -c "## Articulate It: Interview Framing & Vocabulary" <file>` prints `1` for every processed file.
5. For a large batch, split across parallel background agents — each gets
   this skill's content inlined into its prompt (a fresh agent can't
   invoke skills on its own), an explicit file list, and the verify step.

**Don't**: invent a different heading; add this section to index files;
reuse worked-example wording verbatim in a real file; hand-guess a mode-C
anchor without verifying against a strict build.

---

## Mode 2 — Mock interview

A **live simulation**, not a Q&A. Realism is the entire value — explaining
the answer or narrating your own reasoning mid-interview destroys the
exercise. Stay in character until the debrief (Concept-Check Mode is the
one exception — see below).

**Setup** — ask or infer: (1) **mode**: green-field
(`system_design*/*/tutorial.md`), incident/debugging
(`system_design/12_tricky_scenarios/*.md`), concept-check (rapid quiz), or
a custom question; (2) **which question**; (3) **bar** — senior (working,
reasoned design), staff/default (scope, time horizon, ambiguity-handling,
*proactive* trade-off framing), or principal (+ organizational influence,
build-vs-buy as strategy, multi-year sequencing — never let this quietly
collapse back to staff); (4) **time pressure** — gently timeboxed by
default (~5 min clarify, ~10 high-level, ~20 deep-dive, ~10 trade-offs).

Load the matching file now, in full, as the hidden rubric — never reveal
or hint at it live. For `12_tricky_scenarios`, the "Likely Root Causes" /
"Diagnostic Path" / "The Fix" sections are private grading notes.

**Concept-Check Mode** (skip the interview flow below): rapid-fire
fundamentals from `prerequisite_concepts/0N_*.md` — read the doc, ask one
question at a time (from its Quick Self-Check or a natural variant),
**give feedback immediately after each answer** (deliberate exception to
the no-feedback-mid-interview rule), escalate difficulty as they breeze
through (definitional → application → judgment), end whenever they say
stop.

**Interview flow** (green-field / incident modes):

1. **Present the prompt**, one or two sentences like a real interviewer,
   then go quiet — respond to clarifying questions only, never volunteer
   numbers unprompted, give brief realistic acknowledgments, nudge lightly
   if stuck (and note internally that a nudge was needed), never confirm
   correctness mid-interview.
2. **High-level design** — Socratic pushback on anything hand-waved.
3. **Deep-dive** — steer into the tutorial's own core deep-dive component
   unless they self-select somewhere interesting (note this — staff
   candidates often self-select). Draw follow-ups from the answer key's
   "Staff Follow-Ups" / "Failure Modes to Raise Proactively."
4. **Trade-offs** (weight heaviest) — ask explicitly if not raised
   unprompted; note whether you had to ask (this is most of the
   senior-vs-staff signal).
5. **Debrief** — break character explicitly. Scorecard against the
   staff-vs-senior axes (scope, time horizon, ambiguity, trade-offs) from
   `system_design_practice/00_staff_level_signal/tutorial.md`; if bar is
   Principal, extend with the three extra axes (influence, build-vs-buy,
   technical strategy) from that same doc's later sections; cite specific
   moments vs. the reference answer; a plain verdict pinned to the
   requested bar; point them at the doc's own Articulate It section for
   vocabulary they were missing.

**Ending early**: "end it" / "show me the answer" at any point → drop
character immediately, show/summarize the reference doc, no penalty.

**Rules**: never reveal the answer key was read; never grade mid-interview
except Concept-Check Mode; rigorous, not adversarial, tone; Principal bar
must get all three extra scorecard rows, not a label slapped on staff's;
redoing a question after a debrief is a normal fluency-building rep.
