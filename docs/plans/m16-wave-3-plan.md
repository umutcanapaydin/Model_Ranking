---
record_type: plan
id: m16-wave-3-plan
status: draft
process_version: v6.0
date: 2026-09-23
---
# M16-W3 plan — numbers that follow one rule

**Working plan for the `enhancement/m16-w3-one-rule` pull request.** DevFlow's `/work-enhancement`:
this document lives on the branch and is deleted before the owner merges; what survives is the
code, the ADRs, the wave-close record and the PR. Milestone plan: `docs/plans/m16-plan.md` §2 W3.

## Goal

Two data debts M15 closed with, paid on one rule each: a source outage stops blanking the surfaces
that source feeds (D-144 as ruled, W-116), and every surface's floor follows D-148's ROWS rule.

## Scope

**In.** Per-source carry-forward with a ~30-day age limit; what the refresh does when a carried
source expires; how a carried surface says so; a `scripts/survey_boards.py` mode that derives every
floor under D-148 reproducibly (review M-2) plus the missing `parse_rate_board` keep-best test (W4
review MINOR-5); the before/after table and the owner's per-surface ruling (plan §0.3); the ruled
floors in `categories.py`; which rule each tie margin follows (D-148 clause 2).

**Out.** Anchors (D-146: they do not move). New surfaces. The router (W4). W-124/W-125/W-126
(closure).

## What the code does today (measured, 2026-09-23)

- `build._ingest_sources` deletes a failed OPTIONAL source's rows (`reset_source`) and reports it; a
  failed REQUIRED source (`swebench`, `aider`, `litellm`, `openrouter`) raises and the whole build
  fails. Epoch bundles and boards behave like optional sources.
- The refresh then compares candidate with live; a surface left with no evidence is refused under
  D-128, so the OLD artifact keeps serving and every other source's fresh data is thrown away
  (measured 2026-09-20: an Arena timeout discarded fresh LiteLLM, OpenRouter and SWE-bench data).
- Served staleness (`coverage.source_health`, `stale_notice`) is computed from each board's own
  `run_date`, not from when this project fetched it. A carried row keeps its `observed_at`, which
  is the fetch time, so its carry age is derivable from the data itself.

## Decisions — ruled by the owner 2026-09-23, before any code

1. **Which sources carry forward.** The ruling says "a source". Today only the Arena boards and the
   Epoch bundle are optional; the four required sources fail the build. **Ruled: every source carries
   forward** — the rule is about data age, not about which source is important, and
   a required source failing is exactly the outage that today freezes the whole artifact.
2. **How a carried surface says so.** D-151 put no refresh state in the app. Options: (a) nothing
   on `/v1`; the refresh record and `/health` name carried sources and their age; (b) a new
   `/v1/categories` field (for example the date the carried evidence was fetched), under its own
   ADR, shown on the detail screen. **Ruled: (a)** — the existing board-date staleness line
   already tells a reader when the evidence was RUN, which is what they judge by; a fetch date is
   operations information, and D-151 keeps operations out of the app.
3. *(Not a question, recorded so it is visible.)* When a carried source passes ~30 days its surface
   drops, as ruled. D-128 would refuse that candidate as "worse" and freeze everything else, so the
   refresh must accept a surface blinded by an EXPIRED carry, and its record must say why.
4. *(Later, from the table.)* Each surface whose Budget Pick or Best Value changes under the
   re-derived floor is ruled one by one (plan §0.3).

## Phases — one reviewable slice each, gates green after every one

- [x] **P1 — carry-forward in the build.** `build` takes the live artifact; a source that fails keeps
  its last good `scores`/`pricing` rows from it when they are at most 30 days old, and reports them
  as carried; older ones are dropped and reported as expired. *Acceptance:* tests (red first) for a
  failed optional source carried, a failed required source carried instead of failing the build,
  an expired carry dropped, a fresh fetch replacing carried rows, and no carry when
  there is no live artifact.
- [ ] **P2 — the refresh with carried and expired sources.** The refresh hands the live artifact to
  the build; D-128 accepts a surface blinded by an expired carry and still refuses any other
  blinding; the refresh record names carried and expired sources with their age. *Acceptance:*
  the 2026-09-20 incident replayed as a test — Arena fails, the other sources' fresh data is
  published, Arena's rows are carried.
- [ ] **P3 — disclosure** as ruled in decision 2: the refresh record and `/health` name each carried
  source and its age; `/v1` and the app do not change. ADR D-156 records decisions 1-3.
- [ ] **P4 — the survey mode.** `scripts/survey_boards.py --floors` prints every surface's floor under
  D-148 (board rows, top third) beside today's; `parse_rate_board` keep-best tested. *Acceptance:*
  reproduces the W1 review's numbers for the M8 surfaces.
- [ ] **P5 — the table and the ruling.** Before/after per surface: floor, and whether Budget Pick or
  Best Value changes at each budget. Put to the owner; nothing changes until ruled.
- [ ] **P6 — the ruled floors.** `categories.py` floors and header comment; `agentic-coding` states its
  effort population; each tie margin names the rule it follows (D-148 clause 2).
- [ ] **Close** — `/repo-review` on the branch, independent review (MED: one combined seat),
  the wave-close record (m16-wave-3-close), `/pre-merge`. This plan file is deleted before the merge.

## Risks

- Carrying a REQUIRED source means a month-old price can serve beside fresh scores. The age limit
  bounds it; decision 1 is where that is accepted or not.
- A surface blinded by expiry is a user-visible change: that list disappears until its source
  returns. It is the ruled behaviour; the refresh record says so.
