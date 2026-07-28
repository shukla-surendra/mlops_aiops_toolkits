---
name: personal-style
description: Observes two related but distinct things about this user in this project — (1) learning style: what explanation formats actually help them understand (analogies vs formal definitions, code vs abstract theory, question patterns) and (2) communication style: how they phrase and structure their own messages (sentence structure, punctuation habits, bundling multiple asks, typo tolerance, how they open requests and corrections). Logs dated observations for both and maintains two human-readable profiles. Trigger proactively — no need to wait for the user to ask — right after any exchange with a clear signal for either: an understanding breakthrough/friction moment, or a notably structured/phrased message (a correction, a bundled multi-part ask, a stated preference about how they like to communicate). Also invoke directly when the user asks to see, update, or review their learning style, communication style, or "how I work" generally.
---

# Personal style observer

Purpose: help the user build self-awareness of how they learn *and* how they communicate in
this project, and calibrate future explanations and my own message-parsing to match. This is
diagnostic, not a report card — every observation is tentative and the synthesis should be
revised as new evidence comes in, never treated as a fixed trait.

Two separate files, two separate kinds of signal — don't conflate them:

- `memory/user_learning_style_profile.md` — what explanation *formats* work: how they best
  understand something once given it.
- `memory/user_communication_style_profile.md` — how *they* write: phrasing, sentence structure,
  punctuation, how requests and corrections are typically shaped.

## Learning-style signals (→ `user_learning_style_profile.md`)

- **Breakthrough** — "got it," "that makes sense," "cleared [it] up" after a specific
  explanation. Note *what* about that explanation worked: analogy to a known tool? real code
  instead of hypothetical? a step-by-step trace of actual command behavior? a comparison table?
- **Friction** — "I don't understand," "still confused," a request to re-explain. Note what
  style was used right before the friction hit.
- **Question pattern** — open-ended vs narrow/binary vs comparison-seeking. A run of narrow,
  pointed follow-ups usually means they're testing a specific hypothesis and want a direct,
  mechanical answer, not a restated definition.
- **Stated preference about explanations** — "compare it to X first," "give me the use case
  before the mechanics," "less theory, more example."

## Communication-style signals (→ `user_communication_style_profile.md`)

- **Sentence/message structure** — run-on vs punctuated, single-ask vs bundled multi-ask
  messages, mid-message self-correction ("say is it — say it has to..."), how long messages
  typically run.
- **Phrasing habits** — recurring openers ("can you..."), how corrections are framed ("no i
  meant...", "not just X, I need Y as well"), where they place reasoning/motivation for a
  request (often trailing, after the actual ask).
- **Mechanical habits** — punctuation choices (e.g. space before `?`), capitalization patterns,
  typo frequency/tolerance. Log these to inform how literally to parse messages — never to flag
  typos back to the user or imply correctness judgment.
- **Thought process markers** — do they specify everything upfront, or state a terse version and
  correct iteratively once they see the result? Do they reach for their own analogies/comparisons
  unprompted when confused, rather than waiting for one to be offered?

## How to log

Append one dated bullet to the "Observation log" section of the relevant file. Keep it concrete
and tied to the actual message — quote or closely paraphrase the user's own words for
communication-style entries (their phrasing *is* the data), and describe the exchange for
learning-style entries. Don't editorialize beyond what was actually observed, and never frame a
communication-style observation as a correctness or quality judgment (e.g. typos, grammar) —
it's purely descriptive, for better parsing/calibration on my end.

## How to keep the synthesis current

After adding a new observation to either file, re-read that file's whole log and, if the pattern
has sharpened or shifted, rewrite its "Current synthesis" section at the top. Keep it short —
bullets, not paragraphs — phrase every point as an observed tendency ("tends to," "usually
opens with"), never as a fixed claim. With only a handful of observations, say so explicitly.

## When the user asks to see their profile(s)

Read the relevant file(s) — both, if they ask broadly ("how do I communicate/learn"). Summarize
inline for a quick answer, or render as a Markdown/HTML Artifact (via the Artifact tool) if they
want something to actually review and revisit. Never fabricate more confidence or more data
points than the logs actually contain.
