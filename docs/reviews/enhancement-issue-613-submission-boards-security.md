---
record_type: review
id: enhancement-issue-613-submission-boards-security
status: draft
seat: independent
process_version: v7.3.1
date: 2026-11-16
---
# Security Review — enhancement #613, submission boards (branch `enhancement/issue-613-submission-boards`, PR #617)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`)
**Independent:** yes. I wrote none of this change's code, tests, ADR or lock edit.
**Seat and method:** a fresh seat (D-174). I worked in its own `git worktree` on `review/issue-613-security` at
`bd551d5`, with its own venv (`make install`), and did not touch the main checkout. I read the whole range. I ran 20
source mutants of `src/app/workflows/refresh.py` and 12 probe tests, all in a scratch copy outside the worktree. I
re-ran the real `refresh()` on a copy of the 2026-11-12 served state, with the guards instrumented. I also checked the
lock's hashes against PyPI's JSON API.
**Date:** 2026-11-16
**Release range:** `bb00c1b..bd551d5`
**Reviewed head:** bd551d559888cd407aea5d72ddf5d5e45e21034e
**Risk tier:** MEDIUM. The brief declares no HIGH paths. The change relaxes a data-integrity guard (W-049, D-132,
D-159). It touches no auth, PII, payment or migration path, so §11's senior-review trigger does not fire.

## Verdict
BLOCKING

## Findings

### BLOCKING
- **B1** `src/app/workflows/refresh.py:648-652` against `:589` and `:596`: the cap counts fewer rows than `added`
  removes, so a computed set of names can excuse more than one row per name and more than half the board. This breaks
  D-253 clause 2's two conditions: one row a name (M26), and at most `MAX_SUBMISSION_GAIN` of the board. OWASP A04
  (insecure design: a control's accounting differs from its enforcement).

  **How.** `arrivals` counts one unlinked row per new key (`row.copy == 0`). It returns the linked raw names and the
  unlinked keys as one set. `added` then builds `keys = Counter(spelling_key(n) for n in names ...)` over every name,
  including the linked raw names. So a linked raw name `Fresh 0` and the unlinked key `fresh0` both count toward key
  `fresh0`. Two unlinked rows are excused, plus the linked row, and the cap counted two of the three.

  **Is it reachable?** Yes. Reconcile links per `(raw_name, effort)` (`registry.py`, `reconcile`). One submitted model
  can therefore be linked at one effort and unlinked at another, under the same raw name. That is exactly this
  collision. It needs no crafted input, only a new model with an effort whose derived id has no price.

  **Evidence.** Probes in a scratch copy, on the `coding` fixture with 12 served rows:
  - P2: 1 new linked model `Fresh 0` and 4 unlinked `fresh 0` rows. 5 new rows; the cap counted 2; `added` excused 3.
  - P2c: 6 new linked models, plus 2 unlinked twin rows for each. The board grows 12 to 30, with 18 new rows (60%).
    `arrivals` admits it, because its count is 12 of 30, at most half. `added` excuses all 18, so the night has
    **no reasons and publishes**.
  - P2d, the control: the same 18 rows, with unlinked keys no linked name shares. Refused: "6 of 18 rows ... over the
    25% limit".

  At the worst case, the board grows fourfold in a night with no ruling: L = S new linked names and 2S twin rows give
  3S excused of 4S. D-253 holds that "a board that more than doubles is judged as before".

  **Tests.** No test has an unlinked arrival. These mutants all stay green: M9 (unlinked keys dropped from the
  condition), M9b (unlinked keys not admitted), M10 (every unlinked copy counted), and M2b (every linked row of a new
  model counted).

  **Remedy.** Make the cap measure what `added` actually removes. For example, compute
  `excused = len(now - added(candidate, live, {name: names | new_keys}).board[name])` and cap that. Alternatively, stop
  a linked raw name from contributing a key in `added`. Add red tests for P2 (one name excuses one row) and P2c (a
  collision flood over the cap is judged as before).

  **Not a regression?** The `Counter` over linked names dates from D-251's listed path, where the owner read every
  name. D-253 makes it reachable with no human in the loop.

### MINOR
- **M1** `src/app/workflows/refresh.py:183-184`, `:1495`: `admitted` is documented as "what the night published
  without a ruling". It is filled, and written to the record, on a refused night as well (`:2051` runs before every
  guard). It also lists names, not rows: in P2 it says 2 names while 3 rows were excused.

  **Failure scenario.** On a refused night, the operator reads names as published that were not. Under B1, the record
  understates what was set aside.

  **Remedy.** Either write it only on a published night, or rename it in the record to "set aside". Also record the
  excused row count beside the names.

- **M2** `tests/unit/test_submission_boards.py` (whole file): the unlinked-key half of clause 2 has no test (see B1's
  surviving mutants). Without one, the shape behind B1 is invisible to the suite. Fixed together with B1.

### PASS
- Clause 1 is pinned: dropping `served <= now` (`:640`) turns `test_a_lost_served_row_turns_the_computed_arrivals_off`
  red.
- The cap boundary is pinned: `<=` to `<` turns `test_arrivals_up_to_half_the_board_publish` red, and so do a 0.55 or
  1.0 cap and removing the cap.
- M26 holds on the linked path: `added` excusing every row of a leaving model turns
  `test_a_flood_under_one_new_name_excuses_one_row` red.
- The median recompute (`:604-608`) takes the same population as `serving_summary`'s median (ranked rows), minus only
  `gone`.
  - A served price change beside arrivals still trips the guard (`:156` test). Removing the recompute, or keeping the
    arrivals in it, turns the tests red.
  - P6: served prices down 20% beside cheap arrivals publishes, as designed (under the 25% limit).
  - `kept` being empty gives 0.0, and the median guard skips. That case is unreachable on a priced surface: the served
    models, once unpriced, leave the ranking, and the loss guards refuse (P3, P3b). Mutant M8 is equivalent.
- No leak to a board outside the set. `arrivals` reads only the `surfaces` it is given (mutant M15 red).
  `_cycle` passes `submission_surfaces()` (M14 red). The declared-board branch of `added` (`:582`) gets no computed
  key, because today no declared board's source equals a surface name (checked: 19 surfaces, 47 declared boards,
  disjoint). See R3.
- `submission_surfaces` fails closed. An empty set or an unranked source raises (M11 and M12 red). Through `refresh()`
  with `SUBMISSION_BOARDS = {}`, the night raises and the live artifact is untouched (P7).
- Real data: re-run on a copy of the 2026-11-12 state, `computer-use` went from 33 served to 46 rows, with 13 new and
  13 excused, 0 still new, and 13 names. One of them is an unlinked key, `openaiinklingsmall1102rc17`, with no linked
  twin. The median was $3.00 judged ($2.575 as a candidate). The night published 19 surfaces with
  `admitted_count` 13, matching the author's evidence. B1's collision is not in today's data.
- Lock (#616): only `opentelemetry-api` changes (6 name lines, 12 hash lines across 3 locks). The hashes match PyPI:
  the wheel is `2cbd7373…a34` and the sdist `d7b0008e…6b4`, both uploaded 2026-10-29. Its `requires_dist` is unchanged
  (`typing-extensions>=4.5.0`). `scripts/lock_dependencies.py --check`: "4 lock(s) current".
- The retirement of `data/accepted-cuts.yaml`'s D-251 entry leaves `additions: []`, and it parses past its old expiry
  (`test_accepted_additions.py`). No secrets or high-entropy strings appear in the diff. No destructive operations.

## Gates passed
- [x] Secret scan green (`make secrets`, gitleaks, no leaks: the dispatcher's line at `bd551d5`)
- [x] `make deps` (pip-audit) green (dispatcher's line)
- [x] `make slopsquat` green (20 declared, 0 suspect; no new import in the range)
- [x] Default-deny preserved for new external surfaces (no new route or endpoint)
- [x] Permission-matrix not violated (no `.github/`, `.claude/` or `.githooks/` touch; no destructive operation)
- [x] Prompt-injection hygiene: no LLM input is added. Submission content reaches only the parser and guards.
- [ ] Auth/PII checks: not applicable (no such path)
- [ ] SAST: `bandit` is not installed in the venv. Not run. The diff adds no I/O, exec, subprocess or deserialization.

## Acceptance criteria evidence
The plan is `docs/plans/enhancement-submission-boards.md`. The criteria are the plan's own bullets; it gives no
REQ-IDs.
- A named set with a reason, which fails closed: `refresh.py:237-248`, `:613-624`; tests at
  `tests/unit/test_submission_boards.py:163`, `:169`.
- Arrivals computed, one row a name, capped at half: `refresh.py:626-653`; tests at `:84`, `:88`, `:93`, `:99`,
  `:106`. **Not met for unlinked keys (B1).**
- A board outside the set is judged as before: test at `:113`, `:194`.
- `admitted` recorded: `refresh.py:2053-2054`, `:1495`; test at `:176`. See M1.
- The median leaves out set-aside arrivals: `refresh.py:604-608`; tests at `:139`, `:145`, `:149`, `:156`.
- D-251's entry retired: `data/accepted-cuts.yaml:28-31`; test at `tests/unit/test_accepted_additions.py:189`.

## Risks queued
- **R1** `refresh.py:248` (`MAX_SUBMISSION_GAIN`): growth compounds, up to double per night, every night, with the
  publisher's merge as the only human review. The arrivals' scores are unguarded by design (D-253 rationale), so a
  fabricated submission the publisher merges tops `computer-use` with no ruling. This is the owner's ruling. D-253's
  "Revisit when" covers it; it is not a defect.
- **R2** `refresh.py:256-268`: a served row is "kept" by its identity (model and copy, or key and copy), not by its
  content. P4 replaced every served score with 0.1 beside 5 arrivals, and the night published. This is pre-existing:
  the board guards never read scores ("news, not damage"), and a refused batch no longer brings a human's look at it.
- **R3** `refresh.py:582-584`: `added` applies one key to a surface's own board and to a declared board of the same
  name. Surface names and declared sources are disjoint today, but nothing asserts it. A future declared board named
  like a submission surface would receive computed arrivals. A one-line assertion in `submission_surfaces` would
  close it.
- **R4** `refresh.py:645-650`: one new model under many distinct raw names excuses one row per name. In P5, 12
  spellings of one model on a 12-row board were all excused, and the night published. This is per D-253's design. A
  parser change that mints a raw name per submission would ride on it, bounded by the cap once B1 is fixed.
