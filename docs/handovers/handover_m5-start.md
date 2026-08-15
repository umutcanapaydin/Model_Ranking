AGENT-TO-AGENT HANDOVER -- start of M5
Project: model_ranking
Boundary: M4 CLOSED + SIGNED (2026-08-15) -> M5 PLANNED, UNSIGNED
Written by: Claude (Cowork lead agent, D-106), 2026-08-15, at the owner's request
Supersedes for CURRENT STATE: docs/HANDOVER-model-ranking.md (2026-08-11 snapshot, kept for history)

=======================================================================
0. READ THIS FIRST -- WHERE THINGS STAND
=======================================================================
The repository is GREEN and IDLE. There is no half-finished work, no failing
gate, and no question waiting on the agent side. Everything described here is
committed -- this file included -- in the commit that ships this handover.

Exactly ONE thing blocks all forward motion:

    docs/plans/m5-plan.md is DRAFT / UNSIGNED.

Ask the owner to sign it. Do not dispatch W1 before he does. Milestone plans
are signed by the owner -- that is a standing constant in this project, not a
formality (AGENTS.md section 3, mode A0.5).

Everything else on the "open" list is either the owner's action or M5 scope.

=======================================================================
1. THE PROJECT IN SIX LINES
=======================================================================
It answers one question honestly: "which AI subscription should I buy?"
- Curated plan table (data/plans.yaml, 10 plans) + provider model rosters
  (data/rosters.yaml) link a PLAN to the MODELS its provider explicitly names.
- Free-and-legal benchmark + pricing sources score those models.
- A deterministic, rule-based engine (no LLM anywhere in the data or scoring
  path, D-104) returns three labeled answers per task and budget.
- The product's value is the honesty of the links, not the ranking math.
- Engine behind a future iOS advisor app. HTTP API is M6. Fly.io is the owner's
  recorded deploy preference (m4-plan.md) but has NO valid ADR -- that line
  cites an ID colliding with the ratified D-110, and PRD OQ-3 still reads "not
  chosen yet". Close it properly in M6 with a real ID.

=======================================================================
2. THE DOCTRINE YOU MUST NOT BREAK (each was paid for)
=======================================================================
- A score is a (model, harness) pair. Never average across scales or mix
  benchmarks within a category (D-105). M5 makes it a (model, harness, EFFORT)
  triple -- see the plan.
- Never invent a price or a score. Unmatched names are DROPPED and COUNTED,
  never guessed (M1 rule 4). A plan whose page names nothing rankable is
  disclosed as unscored, never silently ranked.
- Fail loud, fail closed, per source. A health check fails toward DISCLOSURE.
- Only documented endpoints. Artificial Analysis is BANNED (D-101).
- Honesty is a feature, and it is implemented: close_call, stale_notice, the
  "UYARI ..." branch when the quality floor is unmet, and D-110's equivalence
  note. If a change makes the answer look better by saying less, it is wrong.
- FP-M2-2 (paid for TWICE): a fixture that encodes a remote VALUE is an
  untested assumption wearing a test's clothing. Probe the live source before
  the wave closes, or leave the criterion visibly OPEN.
- M4-W4 (paid for once, expensively): a fix written to close a review finding
  is NEW CODE and inherits the review obligation. Fault-inject the FIX. Give
  the fix delta its own fresh-eyes pass. "It was written to close a BLOCKING
  finding" is not evidence that it works -- in M4 that exact assumption hid
  four more defects, one of them undefended in both engines.

=======================================================================
3. HOW WORK RUNS HERE (mode A0.5 + D-106)
=======================================================================
- The owner sets scope, signs milestone plans, and runs his own tests at the
  milestone gate. He does not code. Speak Turkish to him, plainly. Send every
  command WITH its path/cd -- he works across several terminals.
- Waves close AGENT-side: fresh-eyes review (never your own code), fault
  injection with in-place md5-verified reverts (NEVER git checkout on
  uncommitted work), a filled wave-close checklist, green gates, one commit.
- Do NOT stop between waves. Meet the owner at milestone closure.
- INTERRUPT HIM IMMEDIATELY, never wait for the boundary, on: a suspected
  secret, any security finding, or a scope change that invalidates the plan.
  M4 exercised this: the agent restated a SIGNED criterion and stopped the
  milestone until the owner ruled. That was correct. Do the same.
- Agent commits carry the D-106 + V4C-64 trailers (GP-Agent / GP-Task).
- Every committed file is ENGLISH (V4C-79). Turkish PRODUCT strings are
  deliberate and live in .language-allow, each with a written reason.

=======================================================================
4. WHAT M4 ADDED (so you can read the code in the right order)
=======================================================================
src/app/workflows/
  registry.py   - the rule table. THE PRODUCT'S IP. Self-defending: property
                  tests prove variant-before-parent order and that no rule
                  swallows a sibling. Adding a rule must stay cheap and tested.
  rosters.py    - M4-W2. Provider model lists as a SECOND documented source
                  with its own provenance and its own clock. Plan-page links
                  win ties over roster links; the recommendation text says
                  WHICH source named the model.
  coverage.py   - M4-W3. plan_coverage() and source_health(): how many plans
                  can be ranked per category and why the rest cannot, plus how
                  old each source's newest evidence is. Read-only by MECHANISM
                  (mode=ro), not by convention. Runs in CI weekly.
  subscribe.py  - the subscription recommender. M4-W4 added D-110 equivalence:
                  when several plans in budget rank on the same model at the
                  same score, say so, name the cheapest with its price, quote
                  the monthly spread, and state which members rest on a roster.
  recommend.py  - D-109 rounding: one decimal, at the OUTPUT boundary only.
                  shown_gap()/lead_phrase() keep prose from contradicting the
                  JSON fields next to it.

=======================================================================
5. THE NUMBER THAT DEFINES M5
=======================================================================
Coding plan coverage: 1 of 10. Assistant: 6 of 10.

Not because linking is broken -- M4 fixed that -- but because SWE-bench has
published nothing since 2026-02-26 and Aider since 2025-10-03. Every ChatGPT
and Claude plan is unrankable for coding today.

The owner has already fetched the unblocker (Epoch AI bundle, CC-BY, on his
disk at ~/Desktop/terminal_output/model_ranking/epoch_data/). Its real shapes
were read and measured -- the numbers are in m5-plan.md section 0. Two traps
are written into the plan and must not be walked into:
  (a) Gemini 3.1 Pro scores 0.756 on Epoch's SWE-bench and 0.118 on DeepSWE.
      Both rows are PREVIEW builds, so "one is a preview" explains nothing --
      the distinguishing token is `customtools` on the SWE-bench row. Test that
      variable. Publishing either number without the explanation, or silently
      picking one, is a milestone failure (REQ-REC-012).
  (b) Epoch reports the same model at FIVE effort levels -- max/xhigh/high/
      medium/low -- and the spread is large (opus-5: 0.736 at max, 0.581 at
      low). Collapsing efforts and taking MAX would advertise performance the
      buyer's plan may not offer. Effort becomes stored data (REQ-CAN-005).

=======================================================================
6. ENVIRONMENT FOOTGUNS (all observed, none theoretical)
=======================================================================
- This container CANNOT push (proxy 403). Ship commits as git bundles; the
  owner pulls and pushes. Writing the bundle straight into his repo folder via
  the device bridge works and saves him a download.
- epoch.ai, huggingface.co and openrouter.ai are proxy-403 from here. The live
  halves run in CI or on his machine.
- Arena's live client is flaky even on his machine: the filter endpoint 500s,
  the client falls back to full pagination and rate-limits itself (W-007,
  M5-W4). His arena_overall_*.json files are the working fallback.
- Stale __pycache__ has burned this project once: a same-length constant edit
  inside one second made the runtime report the OLD value while disk showed the
  new one. When a number "won't change", delete every __pycache__ first.
- He runs Python 3.14 locally (seen in his own `make check` output); this
  container is 3.13; every CI workflow pins 3.12. Nothing in the repo tests
  3.11 despite `requires-python = ">=3.11"` -- do not claim it is covered.
- pytest must be called as .venv/bin/pytest on his machine.

=======================================================================
7. IMMEDIATE TODO FOR THE NEXT AGENT
=======================================================================
1. Read note.txt, this file, then docs/plans/m5-plan.md.
2. Get the M5 plan signed. Answer any question he has about it FIRST -- the
   two locked decisions in its header were his, so re-read them before
   discussing.
3. On signature: dispatch W1 (Epoch source + Gemini contradiction
   investigation + coverage measurement per candidate board). W1 ends with a
   ratified record and ONE mid-milestone owner touchpoint: he signs which
   board becomes the coding category's primary benchmark.
4. Remind him once, early, about the two owner-side items that have now
   survived two closes: the W-001 gitleaks allowlist stanza, and triggering
   the first CI runs of the coverage and roster-staleness legs.

=======================================================================
8. VERIFICATION AT THE MOMENT OF HANDOVER
=======================================================================
make check -> 7 targets green: lint (ruff ONLY -- black is installed but never
  invoked by the gate), typecheck (mypy, 23 source files), test (193 passed +
  5 network-gated), check-records, check-records-selftest, install-check,
  pin-check.
make bootstrap-check -> PASS (0 fail / 2 warn).
git: HEAD = the handover commit, which follows the M5 plan draft commit. This
  container cannot push; the owner pulls the bundle and pushes.
Live pipeline: rebuilt and re-run by the OWNER on his own machine 2026-08-15,
  output matching closure-report-m4.md figure for figure.
