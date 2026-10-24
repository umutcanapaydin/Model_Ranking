---
record_type: review
id: fix-issue-418-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-24
---
# Security Review — fix-issue-418

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need-branch` on the range: `security`, a policy edit: `scripts/review_need.py`, `data/accepted-cuts.yaml`)
**Independent:** yes. I wrote none of D-221, the red tests or the fix.
**Date:** 2026-10-24
**Release range:** `3564a80..eaeee31` (`c9390f3` D-221, `1b926e7` red tests, `eaeee31` the fix; branch `fix/issue-418-accepted-cuts`)
**Reviewed head:** eaeee31aaf028de4df67e01ea9c07a234417f77b
**Risk tier:** MEDIUM. The change edits an exception to a product safety guard (the D-164 board-loss guard) and a review-routing control. The brief declares no HIGH paths (`docs/project-brief.md:110`), and nothing here touches auth, PII, payment or a migration, so no senior-review line is owed.

## Verdict
PASS WITH FINDINGS: BLOCKING 0 · MINOR 3 · NIT 0 · risks queued 2.

Every clause the owner ruled (D-221 clauses 1-4) is implemented and fails closed. Nothing lets a cut excuse more lost rows than it lists names. The three MINORs are ways a cut can be broader than D-221 intends: an expiry with no upper bound, an ADR check that only tests that a header exists, and a spelling key that can be empty. Each needs a cut file change to use, and that change is now routed to this seat.

## Method

- Policy read from the base ref: the profile, `AGENTS.md`, `docs/security-baseline.md` and `permission-matrix.md` at `main` (`3564a80`).
- Read the whole range diff, `#418` with its comments, and D-221.
- In my own worktree at `eaeee31`, probes of the parser and of `_excused`. The main clone's `.venv` was used read-only, with `PYTHONPATH` set to the worktree's `src`, and no `make install` was run.
- `review_need.py` probes in throwaway repositories (the tests' `Repo` helper): rename away, rename into, delete, mode change and modify.
- `pytest tests/unit/test_accepted_cuts.py tests/unit/test_review_need_base_policy.py tests/unit/test_refresh_board_ids.py`: 75 passed.

## Answers to the dispatcher's questions

- **A date that YAML reads as a datetime.** `until: 2099-01-01 00:00:00` and `2099-01-01T00:00:00Z` are refused, because `_cut_expiry` rejects a `datetime` (`src/app/workflows/refresh.py:338-345`). An int (`20991231`) and `null` are refused too. A quoted ISO string is read with `date.fromisoformat`, so `'20991231'` and `'2099-W01-1'` are accepted. Both are real dates, so that widens nothing. The real gap is the far future: see M1.
- **An ADR id matched as a substring.** This cannot happen. `decision` must fullmatch `D-\d{3}`, and the header regex anchors `^## D-NNN —` (`refresh.py:324-327`), so `D-22` and `D-1000` are refused. A header inside a fenced code block, a process ADR (`D-005`) or a superseded ADR is accepted: see M2.
- **The decisions file missing.** It fails closed. `_decision_log` raises `AcceptedCutError` (`refresh.py:348-352`). The cycle records a crash and does not publish (`refresh.py:1171-1190`), and `main` exits `EXIT_FAILED` (`refresh.py:1632-1637`). The log is read only when at least one cut exists.
  - The Mac release: `git archive` exports docs/ with no `export-ignore` (`scripts/install_engine_service.sh:13`).
  - The hosted image: it copies only `src` (`Dockerfile:15`) and runs no refresh. There, `ACCEPTED_CUTS_PATH` is absent, so `load_accepted_cuts` returns `{}` and nothing is excused.
- **A lost linked row whose name is in the cut under another model.** Probes:
  - The same raw name on two models, both rows lost: 2 excused.
  - The name re-linked from m1 to m2: m1's row is excused, though the name stays on the board.

  Both follow D-221 clause 2: "the raw name it arrived under". Both are bounded by live rows that carry a listed name.
- **Copies of one raw name.** `Spellings` is a frozenset, so N copies of a listed name on one model excuse 1. That under-excuses, which is the safe direction. Unlinked copies are excused up to the number of distinct listed names with that key.
- **Upstream control.** `lost` and `before` come from the live artifact, and the candidate can only shrink `after` (`refresh.py:366-376`). So no upstream can push the excused count past |live spellings ∩ cut|.
- **The route from every range.** `changed` comes from `git diff --name-only --no-renames -z` (`scripts/review_need.py:224`). With `--no-renames`, a rename lists both paths. Rename away, rename into, delete, mode change and modify all returned `review-need: security` in light mode. The policy-edit branch returns before the mode filters (`review_need.py:278-282`), so the route holds in either mode.
- **Case-variant paths.** A case-variant path is a different file, and the refresh never reads it. On a case-insensitive checkout or extract, the lowercase entry sorts last and wins.
- **Does it weaken anything it routed before?** No. `policy_edits` only appends `exceptions` (`review_need.py:194-195`); `edits`, `scripts` and `lines` are unchanged. The reason line's `edits[:4]` can hide the path behind `...`, but the route stays.

## Findings

### BLOCKING
- none

### MINOR
- **M1** `src/app/workflows/refresh.py:330-332` (with `_cut_expiry`, `:338-345`) — **`until:` has no upper bound.** A cut with `until: 9999-12-31` parses (probed), and it is the standing relaxation D-221 retires. Inside its window, rows that are re-published and dropped again are excused again: #418's M3.
  - Why MINOR: using it needs a cut file change, and that change is now routed to security.
  - Remedy: `_checked_cut` refuses an `until` more than a ruled number of days after `today` (the owner picks the cap; 90 days would fit D-221's "once"), with a cited test in INV-54. The cap needs an owner ruling, so this needs a **new issue**.
- **M2** `src/app/workflows/refresh.py:326` — **the ADR check only tests that a header exists.** Probes that passed:
  - `decision: D-005`, a process ADR unrelated to any cut;
  - `D-136`;
  - a `## D-999 —` header inside a fenced code block.

  Nothing ties the ADR to the board, or checks that it is still standing. D-221 clause 4's words are met ("an ADR that `docs/decisions.md` holds"), but the field does not show that the owner accepted this cut.
  - Remedy: skip fenced blocks; require the ADR's section to name the cut's board; refuse an ADR whose `**Status:**` is superseded or rejected.
  - This can ride a follow-up of this branch or M1's issue.
- **M3** `src/app/workflows/refresh.py:370-374` (with `spelling_key`, `:277-280`) — **a cut name with an empty spelling key excuses rows by another name.** A name with no `[a-z0-9+]`, such as `通义千问` *(a model name, kept as evidence)* or `---`, has key `""`. Probe: lost unlinked row `文心一言` *(a model name)*, cut `{通义千问}` → excused 1.
  - The count stays bounded by the number of such listed names, but the excused row's own name is not listed, which goes against D-221 clause 2.
  - Remedy: `_checked_cut` refuses a row name whose `spelling_key` is empty, with a test. This is small, so it can go in this branch.

### PASS
- **Clause 1:** the epoch_chess entry is retired (`data/accepted-cuts.yaml:12` `cuts: []`). Its provenance (`bf278b0`, the two release tags) is kept in the file's header comment.
- **Clause 2:** `_excused` counts, per model, only the lost spellings that the cut names: `before - after` (`refresh.py:374-375`). The #416 M2 probe now refuses (`tests/unit/test_accepted_cuts.py:277`).
- **Clause 3:**
  - An unparseable, missing or past `until` raises `AcceptedCutError`.
  - The error propagates as a crash, so nothing publishes and the exit is non-zero. It is never ignored and never applied.
  - `today` is the UTC date; tests inject it.
- **Clause 5 is derived, not typed twice.** `EXCEPTION_FILES` is held equal to `refresh.ACCEPTED_CUTS_PATH` by a test (`tests/unit/test_accepted_cuts.py:289`). It fails closed: a path outside the root raises in `relative_to`.
- **Schema checks:**
  - `_CUT_KEYS` needs exactly five keys.
  - A board named twice is still refused.
  - Cuts apply only to declared boards. A surface's own board takes no `excused` (`refresh.py:574-575`).
- **Gates:** no new third-party import (`contextlib` and `importlib.util` are stdlib). No secret or destructive operation in the diff (grep). No log line carries PII.

## Gates passed
- [x] Secret scan green (`make secrets` on `eaeee31`: `no leaks found`, per the dispatcher)
- [x] `make deps` (pip-audit) green (`No known vulnerabilities found`)
- [x] `make slopsquat` green (PASS; no new imports)
- [x] Default-deny preserved for new external surfaces (no new surface)
- [x] Permission-matrix not violated
- [x] Prompt-injection hygiene. Upstream raw names are data, compared and never followed. The cuts file is read with `safe_load_bounded` (SafeLoader).
- [ ] Auth/PII checks + human review trigger — n/a (no auth, PII, payment or migration path)
- [ ] SAST — `bandit` is not installed in the project venv. The diff was read by hand: no `eval`, no `subprocess` with a shell, no new file write.

## Acceptance criteria evidence
- D-221 cl. 1 → `data/accepted-cuts.yaml:12`; `tests/unit/test_accepted_cuts.py:85`
- D-221 cl. 2 → `src/app/workflows/refresh.py:366-376`, `:581-586`; `tests/unit/test_accepted_cuts.py:277`, `:284`
- D-221 cl. 3 → `src/app/workflows/refresh.py:330-332`, `:338-345`; `tests/unit/test_accepted_cuts.py:255`, `:261`
- D-221 cl. 4 (ADR) → `src/app/workflows/refresh.py:326-327`, `:348-352`; `tests/unit/test_accepted_cuts.py:255` (`unknown-adr`)
- D-221 cl. 4 (route) → `scripts/review_need.py:87-90`, `:194-195`; `tests/unit/test_accepted_cuts.py:289`, `:301`
- INV-54 amended → `docs/security-invariants.md:104` (three new cited tests; conformance PASS (33) on `eaeee31`)

## Risks queued
- **R1** `docs/project-brief.md:110` — **the code that applies the exception has no per-change security route.** `_excused`, `parse_accepted_cuts`, `_checked_cut` and the `cuts` argument of `degradations` sit in `src/app/workflows/refresh.py`, which has no per-change security route in light mode (HIGH paths: `none`). A later change could restore by-model excusal or drop the `until` check. Only INV-54's tests would guard it until the release review, because the file is routed but the code that applies it is not.
  - Remedy, for the owner: a HIGH glob or a line-scoped route for these functions, as `policy_lines` does for the Makefile.
  - Suggest a **new issue**.
- **R2** `src/app/workflows/refresh.py:348-352` — **two gaps with no test:**
  - The unreadable-decisions-log branch has no test. It fails closed by reading the code.
  - At `D-1000` the `D-\d{3}` shape refuses every cut. That fails closed, but it will need a widening then.

  Small enough for this branch, or for M2's follow-up.
