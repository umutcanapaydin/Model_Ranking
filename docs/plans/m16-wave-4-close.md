---
record_type: wave
id: m16-wave-4-close
status: draft
process_version: v6.0
date: 2026-09-23
---
# Wave-Close Checklist — M16 Wave 4, the updater keeps every list current

**The nightly refresh now fetches every board itself, a changed board layout is recorded instead of
passing as a quiet night, and a model on the boards and in the price feeds reaches the lists without a
code edit.** The Epoch bundle is fetched and unpacked as untrusted input (D-158); the 2026-09 layout is
read and layout drift reaches `/health`; Claude Fable 5.1 is its own model; names no curated rule
matches are registered under a derived id with a price and a score (D-157, the owner's "the list wins"
ruling); `/health` names what was derived and what nothing matched. The first artifact with derived
models is published deliberately by the owner: D-132 refuses the roster jump, by design.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m16-plan.md` §2 W4 "(risk: **HIGH**)"; the branch plan reached main with PR #6 and was removed in this fix round (DevFlow: a plan never stays on the default branch) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every phase red-first in its own commit, then green: `tests/unit/test_epoch_bundle_fetch.py` (P1 and its security fixes), `tests/unit/test_epoch_layout.py` (P2), `tests/unit/test_registry.py` (P3), `tests/unit/test_registry_derived.py` (P4 and BLOCKING-1), `tests/unit/test_registry_disclosure.py` (P5), `tests/unit/test_refresh_job_install.py` (MAJOR-1). Smoke on copies of the served artifact with live upstreams: all 19 sources arrived, none carried, no drift | ✅ |
| 3 | Review per tier: HIGH → Code + Tester + pulled-forward security | Three independent seats (`seat: independent`). `docs/reviews/m16-wave-4-security-p1.md`: BLOCKING (F1), fixed in `cd2f942`. `docs/reviews/m16-wave-4-review.md` (Code + Tester, whole wave): BLOCKING (the grammar merged products) + MAJOR (the running launchd wrapper never fetched), fixed in the fix round. `docs/reviews/m16-wave-4-rereview.md`: **PASS-WITH-MINORS**, no BLOCKING or MAJOR; its MINOR-1 (the residual's reach), MINOR-3 (two green mutants) and NIT-1/NIT-2 fixed red-first; its MINOR-2 is the owner step below | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass | `docs/reviews/m16-wave-4-security-p1.md` (seat: independent) on the untrusted archive: BLOCKING F1 (a crafted zip crashed the whole night) and F2-F6, all fixed red-first in `cd2f942`; the full review re-verified all six against 24 hostile archives, a corrupt `ZIP_ZSTANDARD` member included | ✅ |
| 5 | Tester fault-injection: break → RED → reverted | Author mutants per phase, each restored byte-identical by an md5-checked script, all RED after the surviving ones got tests: P1 names/links/budget/member-cap/scratch/owner-dir/fetch-failure/nightly-flag/non-zip and the resolve guard (survived first, got its test); P2 path/name column/board and bundle drift/report/record/health; P4 baseline and grammar; P5 derived/unmatched/record/health, the modality filter and the not-served rule (both survived first, got tests); the fix round's eight grammar mutants. Independent sets: `docs/reviews/m16-wave-4-review.md` (38 mutants; its five survivors now have killer tests) and `docs/reviews/m16-wave-4-rereview.md` (20; its two survivors, M4 and M15, now have killer tests) | ✅ |
| 6 | Every acceptance criterion touched has a citing test entering through the LIVE entrypoint | REQ-ING-010 (D-158): `tests/unit/test_epoch_bundle_fetch.py` runs the real `refresh()` with the real `build.main` and a fetcher; REQ-CAN-001 as superseded by D-157: `tests/unit/test_registry_derived.py` drives `reconcile`, and `tests/unit/test_registry_disclosure.py` the real cycle | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | The bundle is untrusted input (D-158 clause 2): each refusal has its negative test in `tests/unit/test_epoch_bundle_fetch.py` (path escapes, links, planted links, bombs, member count, non-zip, unreadable codecs, deadline, redirects); INV-23 is kept by `refresh._served_without`'s read-only copy | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None. Twice this wave a tool touched a file it should not have and it was repaired without `git checkout`: an edit script duplicated a block of `src/app/workflows/registry.py` (the duplicate was cut by line), and a review seat's differently shaped scratch script, run with this lead's arguments, wrote seven two-byte files named after mutation strings (removed). The owner's untracked HTML file, moved by a mistyped command, was put back at once, same size and date | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | Where a model id can come from, enumerated in `src/app/workflows/registry.py`: a curated `ModelRule`, or `derive_identity` through `reconcile`'s `_Pending.ready` (price AND score, never a curated id), each with tests | ✅ |
| 9b | Scope & draft PR | PRs #5 and #6 (merged), then the fix round's draft PR. Planned vs delivered: P0-P5 delivered. Deferred with a record: the floors on fresh data (six D-148 floors move; W-128), the data-licence risk (W-129, owner: keep and record), the full review's NIT-1 (drift lines repeat the source name) and NIT-3 (bundle-gated tests pin the 2026-08-15 bundle), the thirteen same-spelling ids a curated rule should split (the measurement record), and the CI step that ages `data/epoch-source.yaml` (a workflow change, proposed to the owner in PR #6) | ✅ |
| 9a | Economy | `git diff --shortstat 120705a HEAD` without `make check-fast` (PR #7, its own change): 28 files, +2910/−132, of which code is +594/−39 in `src/` and `scripts/refresh_job.sh`; the rest is tests, four review records and two research records. VARIANCE noted: five phases, a security pass and two review rounds in one wave | ✅ |
| 9 | Skipped/waived ledger + run summary | `gates run: make check-fast · make check (pytest, Swift 268, conformance, client-decls, check-records, wave-check-all) · gates SKIPPED: none · outcome: the fix round's draft PR; the owner merges, reinstalls or retires the launchd wrapper (`scripts/install_refresh_wrapper.sh` or `scripts/retire_refresh.sh`; the installed copy still passes the retired bundle), THEN publishes the first derived artifact by hand` | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-09-23 · Wave commit range: `120705a..HEAD` (PRs #5, #6 and the fix round)

## Wave footprint — RECORD ONLY

```
Touched:        src/app/clients/{epoch_bundle,epoch_board,protocols}.py · src/app/workflows/{refresh,build,
                registry,sources}.py · src/app/adapter/nightly.py · scripts/refresh_job.sh · .gitignore
                tests/unit/test_{epoch_bundle_fetch,epoch_layout,registry,registry_derived,
                registry_disclosure,nightly_refresh,refresh_job_install,plans_ingest}.py
                docs/{decisions,prd,warnings.ledger}.md · docs/research/{source-expansion-2026-09-23,
                m16-w4-derived-registry-2026-09-23}.md
Mutant set author: the lead agent (supporting evidence only) and the independent seats
                (docs/reviews/m16-wave-4-security-p1.md, m16-wave-4-review.md, m16-wave-4-rereview.md)
Observed RED:   registry.py `if routed:` -> `if True:` with any -vN stripped failed six
                test_different_products_never_derive_one_id cases: DeepSeek V2/V3/V5, Claude 1/2/2.1 and
                Mistral 7B v0.1/v0.2/v3 each merged under one id again
Owner instruction: "if it is on a list, the list wins; but when we cannot give anything, [...] we
                will present the list we derived from the data" (2026-09-23, translated from Turkish)
                -- delivered as D-157; and "if it does not work with the updater, the updater is our
                priority" -- delivered as D-158 and P2.
K.8 contracts:  /v1 unchanged. /health gains refresh_drift, refresh_derived, refresh_unmatched
                (additive). The refresh record gains drift, derived, unmatched. refresh gains
                --fetch-epoch.
Closure rounds: (filled at the M16 closure)
Hand-kept lists: the grammar's decoration lists (_REGION_PREFIXES, _VENDOR_FAMILIES,
                _COLON_DECORATION, _AT_DECORATION) and the vendor maps are named, each with its reason,
                in registry.py; check-fast's legs are derived from `check:` (PR #7).
```
