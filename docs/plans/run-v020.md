# Run — v020

<!-- Copy to `docs/plans/run-<name>.md` (`<name>`: lowercase letters, digits, hyphens) when `/plan-run` opens a run, and keep it current: it is
     the ONE record of an unattended run. `make run-check` reads it, `make closes` grades every
     run file in the tree, and `/start-session` reads it first to resume the run after a new
     session or a compaction. Every table cell is read by `scripts/run_check.py`; keep the column
     order and the vocabularies below. Lines starting with `Mode:`, `Started:`, `Ended:`,
     `Integration branch:`, `Plan PR:` and `Rulings:` keep their wording. -->

Mode: light
Started: 2026-10-24
Ended: 2026-10-25 — all milestones closed
Integration branch: `integration/run-v020` · PR: #432
Plan PR: #431
Rulings: D-223, D-224

<!-- `Ended:` is `open` while the run runs. When it ends: `<YYYY-MM-DD> — <why>`, where why is one
     of `all milestones closed`, `owner stopped`, `stopped at <class>, nothing independent left`.
     `Rulings:` lists the ADRs the owner's answers to the run's decisions message became
     (`/log-decision`, each with its `Owner ruling:` line); `none` when every question took its
     default. -->

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | queue | 8c30c9f | issues | closed |

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| issue-418 | fix/issue-418-accepted-cuts | #430 | none | stacked |
| issue-427 | enhancement/issue-427-retire-mac-code | #448 | none | stacked |
| issue-411 | fix/issue-411-json-errors | #433 | none | stacked |
| issue-412 | fix/issue-412-simplebench-regex | #434 | none | stacked |
| issue-417 | fix/issue-417-bracket-regex | #435 | none | stacked |
| issue-426 | fix/issue-426-refresh-alarm | #436 | none | stacked |
| issue-419 | fix/issue-419-image-modality | #437 | none | stacked |
| issue-403 | fix/issue-403-media-price | #438 | none | stacked |
| issue-404 | fix/issue-404-osworld-tests | #439 | none | stacked |
| issue-413 | fix/issue-413-schema-sync | #440 | none | stacked |
| issue-429 | fix/issue-429-cut-edges | #441 | none | stacked |
| issue-410 | fix/issue-410-gate-exemption | #445 | none | stacked |
| issue-401 | fix/issue-401-dispatch-spellings | #442 | none | stacked |
| issue-408 | fix/issue-408-ceiling-flake | #443 | none | stacked |
| issue-396 | fix/issue-396-g2-rebuilds | #446 | none | stacked |
| issue-447 | fix/issue-447-prd-adr-ids | #449 | none | stacked |
| issue-450 | fix/issue-450-plans-reverified | #451 | none | stacked |

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|
| 2026-10-24 | issue-427 | security-test | Retiring the Mac launcher and installer (D-223 cl. 10) deletes `tests/unit/test_engine_service.py`, the tests INV-27, INV-28 and INV-29 cite: retire those three invariants with the scripts? | issue-411 and the rest of the queue; answered 2026-10-25: retire them (D-224) |

## For the owner

Run v020 is done: 17 issues stacked on `integration/run-v020` (#432), and release v0.2.0's verdicts are on it.
The release Tester's verdict is MINOR, with three BLOCKING closed with its own tests. The release security
verdict is MINOR. `make deploy-check` is PASS. The one stop (#427, the retired invariants) was answered by D-224.

The order:
1. **The hosted night first**, from the 2026-10-21 owner-actions rows: `fly-production` and its token, the
   nightly workflow, then one night run by hand. #432 retires the Mac's engine code, so the data must already
   come from the hosted night.
2. **Merge the plan PR #431**, which accepts D-223.
3. **Merge #432 as a merge commit, never a squash.** It carries #430, #428, #433-#446, #448, #449 and #451, in
   the wave table's order. The merge marks each stacked draft merged and closes its issue. It also accepts
   D-221, D-222 and D-224.
4. **Deploy v0.2.0 and tag it.** Each is an owner-actions row.
5. **Take the Mac's service off** (`scripts/remove_engine_service.sh`), then the guard rows: tags and replace
   refs, and the retired installer rule.

Queued for the next release, deliberately not shipped on their own (GPF-009): #444, #452 and #453.
