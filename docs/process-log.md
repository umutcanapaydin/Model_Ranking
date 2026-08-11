# Process Log

> Append-only. One entry per session (typically per work-day or per slice). 3-10 lines each. Never edit historical entries; correct via a new entry.
>
> Each entry ends with a `Lesson:` tag — slide titles for training decks and seed candidates for `.agents/rules/playbook-seeds.md`.
>
> Seed G.1: open this file BEFORE the work starts.

---

## S1 — Project bootstrap (TEMPLATE — replace with real entry)

**Date:** YYYY-MM-DD
**Agent:** <Claude / Codex / human>

What we did:
- Cloned pipeline v2.0 template into this project.
- Filled in AGENTS.md PROJECT section (name, customer, stack, REQ-ID scheme).
- Adapted `permission-matrix.md` for project context.
- Created `.claude/settings.json` from `docs/claude-harness-config.md` (Cowork-blocked file).
- Created `.mcp.json` from `mcp.json.template`.
- Ran `make check` — green on day 1.
- Wrote first REQ-IDs in `docs/prd.md`.

What surprised us:
- <e.g., "PostToolUse hook caught a stray edit while we were typing — instant feedback.">

What we'd do differently:
- <e.g., "Should have read tool-suitability.md before sizing M1.">

Lesson: <one-line generalizable principle, or "none today">

---

## S2 — <next session>

<continue here>

## 2026-08-10 — M1 W1: schema + LiteLLM ingestion (Claude, Cowork)
Stage 0 closed (bootstrap-check PASS on owner machine, 0 fail/2 warn). Owner signed m1-plan §13;
W1 implemented: schema.py (provenance columns, CHECK>0, UNIQUE widened pre-freeze), RawSource
Protocol + fake, LiteLLM client/parser (bool/negative guards), ingest run-context. 19 unit tests
+ 1 env-gated contract test (live PASS, 500+ aliases); ruff/mypy-strict clean. Fresh-eyes combined
review: PASS, 9 MINOR — all applied or ledgered. Fault-injection ×2: RED confirmed, md5 reverts.
Owner checkpoint commit OWED (repo not yet opened).
Lesson: the starter's own src/__init__.py breaks `make typecheck` (mypy src) — a Stage-0 gate gap;
candidate seed for the template upstream.

## 2026-08-10 (2) — M1 W2-W3-W4: full data layer + recommendation engine (Claude, Cowork)
Owner ratified A0.5 flow (no stops between waves) + M1-M5 roadmap written to deliverables-plan.
W2: SWE-bench Verified + Aider ingestion (review PASS, 5 MINOR applied). W3: canonical registry +
median prices + ranking + export — review FAIL (2 BLOCKING: mypy-on-tests; real-alias false
matches gpt-5-pro→gpt-5 class) → 5 new canonical models, 12 tightened lookaheads, deterministic
tie-break; re-verified green. W4: 3-answer engine + CLI — review CHANGES REQUIRED (false why on
floor-unmet fallback; exit-code collision) → fixed + tested. First LIVE run caught Aider dup-model
UNIQUE abort (fixture blind spot) → keep-best dedupe + regression. Final: 71 tests + 3 gated,
live e2e green (2154 prices, 173+68 scores, 42 canonical models; picks: Opus/MiniMax/DeepSeek).
Fault-injection ×6 across waves, all RED + md5 reverts. All owner checkpoint commits OWED.
Lesson: fixtures model imagined data; the first live run belongs INSIDE the wave, not after it —
candidate seed + closure-report item.

## 2026-08-11 — M1 Stage 4 closure (Claude, Cowork)
Security review (closure, BLOCKING gate): PASS, 0 BLOCKING; 2 MINOR closed (unused deps → planned;
.gitignore += *.db) + CLI connect moved into try. Quality Gate: 13/13 criteria ✅ with citing tests
(V3C-02), coverage 88%, criteria diffs NONE. Capture: EXPERIENCE.md M1 entry, closure-report-m1.md
generated, 2 seed candidates queued for owner. Owner opened GitHub repo (Model_Ranking); all
checkpoint commits collapse into owner's initial commit. Milestone closes at owner sign-off.
Lesson: closure telemetry (fix-rate/churn) needs git history from day one — starting M2, checkpoint
commits land per wave, so M2 will have real trust telemetry.
