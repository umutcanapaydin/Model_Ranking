# Run — v020

<!-- Copy to `docs/plans/run-<name>.md` (`<name>`: lowercase letters, digits, hyphens) when `/plan-run` opens a run, and keep it current: it is
     the ONE record of an unattended run. `make run-check` reads it, `make closes` grades every
     run file in the tree, and `/start-session` reads it first to resume the run after a new
     session or a compaction. Every table cell is read by `scripts/run_check.py`; keep the column
     order and the vocabularies below. Lines starting with `Mode:`, `Started:`, `Ended:`,
     `Integration branch:`, `Plan PR:` and `Rulings:` keep their wording. -->

Mode: light
Started: 2026-10-24
Ended: open
Integration branch: `integration/run-v020` · PR: #432
Plan PR: #431
Rulings: D-223

<!-- `Ended:` is `open` while the run runs. When it ends: `<YYYY-MM-DD> — <why>`, where why is one
     of `all milestones closed`, `owner stopped`, `stopped at <class>, nothing independent left`.
     `Rulings:` lists the ADRs the owner's answers to the run's decisions message became
     (`/log-decision`, each with its `Owner ruling:` line); `none` when every question took its
     default. -->

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | queue | 8c30c9f | issues | running |

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| issue-418 | fix/issue-418-accepted-cuts | #430 | none | stacked |
| issue-427 | enhancement/retire-mac-engine | #428 | none | stopped |
| issue-411 | fix/issue-411-json-errors | #433 | none | stacked |
| issue-412 | fix/issue-412-simplebench-regex | none | none | queued |
| issue-417 | fix/issue-417-bracket-regex | none | none | queued |
| issue-426 | fix/issue-426-refresh-alarm | none | none | queued |
| issue-419 | fix/issue-419-image-modality | none | none | queued |
| issue-403 | fix/issue-403-media-price | none | none | queued |
| issue-404 | fix/issue-404-osworld-tests | none | none | queued |
| issue-413 | fix/issue-413-schema-sync | none | none | queued |
| issue-429 | fix/issue-429-cut-edges | none | none | queued |
| issue-410 | fix/issue-410-gate-exemption | none | none | queued |
| issue-401 | fix/issue-401-dispatch-spellings | none | none | queued |
| issue-408 | fix/issue-408-ceiling-flake | none | none | queued |
| issue-396 | fix/issue-396-g2-rebuilds | none | none | queued |

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|
| 2026-10-24 | issue-427 | security-test | Retiring the Mac launcher and installer (D-223 cl. 10) deletes `tests/unit/test_engine_service.py`, the tests INV-27, INV-28 and INV-29 cite: retire those three invariants with the scripts? | issue-411 and the rest of the queue |

## For the owner

The owner's purpose for this run (2026-10-24, translated): finish everything open, and merge once,
when the release is ready. So the run ends with release v0.2.0's verdicts (one Tester, one
Security-Reviewer over everything since v0.1.0's heads, GPF-009) and its record on the integration
branch. The morning's order: the plan PR, then the integration PR (merge commit, never a squash),
then the deploy (`docs/owner-actions.md`). Outside the run, and in parallel, the owner's steps for
#427 (the Mac retired): `fly-production` and its token, the nightly workflow, one night by hand, then the Mac's
service off. **Merge the integration PR only after a hosted night has published** (D-223 clause 10:
#427's code retirement is in this run, so the Mac stops being the data's source when it merges).
