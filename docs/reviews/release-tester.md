---
record_type: review
id: release-tester
status: draft
seat: independent
process_version: v7.2
date: 2026-10-25
---
# Release Tester Review

This verdict is the light-mode Tester for release v0.2.0, dispatched by run v020 (`docs/plans/run-v020.md`) before the
release. It replaces the v0.1.0 verdict (PASS, reviewed head `0bdf2eb`, written at `471dd79`), which stays in git
history. That verdict carried M1-M3 of the `9d3cf0e` verdict; all three are closed in this range: M1 by #418 (the cut
is retired, expires and excuses by name), M2 by #417 (`tests/unit/test_arena_respelling.py:68` pins id and effort),
M3 by `1b926e7` (the docstring cites D-220 clause 3).

**Reviewer:** Tester subagent (`.claude/agents/Tester.md`, `AGENTS.md` and `.agents/rules/practices.md` read from
`main`). I had fresh eyes and wrote none of the range's code or tests. The only tests I wrote are the three commits
listed under "Tests added this review", on my own branch, after the range.
**Independent:** yes
**Date:** 2026-10-25
**Commit range:** `0bdf2eb2fa3f92439b29e6b58a71948b9722e15d..b4dd4f1a0da43b6371a44105b404e568021f7c7f`, the head of
`integration/run-v020` (draft PR #432): #418, #427, #411, #412, #417, #426, #419, #403, #404, #413, #429, #410, #401,
#408, #396, #447 and #450, plus the owner's #424 CI change (`15e5c9e`, `697f758`). 86 files, 83 commits. Rulings:
D-221, D-222, D-223, D-224.
**Reviewed head:** e87f9a943548fee88dea9f8f759a55e2a02815a9 (this review's last test commit; `b4dd4f1` plus three
test-only commits)
**Risk tier:** HIGH. The range moves the deploy gate's exemption (#410), the refresh cycle's child build and its kill
(#426), the accepted-cuts guard (#418, #429), the client-decls gate (#396), and retires INV-27..29 with the Mac
scripts (#427, D-224).
**Seat:** my own worktree `$TMPDIR/wt-tester-v020` on `review/release-tester-v020`, cut from `b4dd4f1`, with its own
`.venv` (`make install`) and a copy of the main clone's `advisor.db`. A second detached worktree
(`$TMPDIR/wt-tester-v020-rg`) ran the red-to-green pairs and the base coverage at `0bdf2eb`, with this seat's venv.
No launchd service, owner data directory, Fly or network call was touched; nothing was pushed.
**Cross-model routing:** author family Claude / reviewer family Claude; no second family was available in this seat.
Fresh context: this seat read the diff, the issues with their comments, the ADRs and the tests, not the implementers'
sessions.
**Mutation kill-rate (advisory):** no mutation runner is wired for this stack (no mutmut or equivalent in the
Makefile). The hand fault injection below stands in: 37 faults, 30 killed on the range's own tests, 7 survived; all 37
killed after this review's tests.

## Verdict
MINOR -- 0 BLOCKING open, 2 MINOR. Three BLOCKING findings were found and each is closed by a test this review added
(B1-B3 below): two deploy surfaces D-223 clause 5 named had no test and their removal stayed green; five accepted-cut
schema checks had been silently bypassed by their own negative tests; `refresh.py` coverage fell on a touched module.
Every acceptance criterion now has a passing citing test, every reported symptom was reproduced red on its pre-fix
commit and is green after it (12 of 12 pairs re-run here), and no test was weakened, skipped or deleted to go green.

## Acceptance-criterion coverage
**#418 (D-221): a cut excuses by name, expires, names a logged ADR, is routed to security; epoch_chess retired**
- cl. 1 retired -> `tests/unit/test_accepted_cuts.py:85` asserts `load_accepted_cuts() == {}` and the file ends
  `cuts: []` -- GREEN.
- cl. 2 by name -> `:281` (a cut naming a model's KEPT spelling excuses none of 6 lost of 18: the board is refused)
  and `:288` (naming the lost spellings excuses them) -- GREEN; F1 (by model again) killed by `:281`.
- cl. 3 expiry -> `:259` (no `until`, expired, not a date, unknown ADR each raise), `:265` (expiring today applies),
  `:206` (a malformed file fails the night through `refresh()` and leaves the live artifact) -- GREEN.
- cl. 4 routing + ADR -> `:305` (`review-need` says `security` in light and `code-reviewer+security` in heavy for a
  change to the file), `:293` (`EXCEPTION_FILES` equals the path the refresh reads, derived), `:344` (unreadable log
  fails closed) -- GREEN.
- Security review M3 -> `:316` (a name with an empty spelling key fails closed) -- GREEN.
- Schema checks D-220 cl. 3 kept -> `:376` (added here, B2) -- GREEN.

**#429 (D-223 cl. 2-4): 30-day cap, strict ADR check, R2 edges**
- `tests/unit/test_accepted_cuts.py:332` -- 31 days out, year 9999, ADR only in a code block, a superseded ADR, an
  ADR naming another board: each raises -- GREEN; F2-F5 killed here.
- `:337` -- exactly 30 days out and a four-digit `D-1000` parse; `:344` the unreadable log -- GREEN.
- cl. 4 (no per-change route for the cut code) is a ruling, not a behaviour: INV-54's rows and this review cover it.

**#427 (D-222, D-223 cl. 10, D-224): the Mac engine's code retired**
- installer/launcher gone, nothing starts an engine -> `tests/unit/test_engine_service.py:34` (`ios/app.sh` runs no
  uvicorn, launchctl or `engine_service`), `:89`, `:103` (every command a script tells the operator exists) -- GREEN.
- the remover stays until run (D-224 cl. 3) -> `:23` -- GREEN.
- the deploy reads no Mac artifact -> `tests/unit/test_deploy_hosted.py:355` (unset `MODEL_RANKING_SERVED` refuses,
  a copy in the retired folder is not shipped, no `fly` call) -- GREEN.
- app's debug default and local-network prompt -> `tests/unit/test_engine_address.py:157`,
  `tests/unit/test_testflight_ready.py:84`, `tests/unit/test_ui_test_script.py:78` -- GREEN.
- hosted invariants kept (D-224 cl. 2) -> `tests/unit/test_engine_host.py:59` (a bind beyond loopback with no Host
  list is a startup problem) and INV-25/26's cited tests -- GREEN.
- "a hosted night publishes on its own" is the owner's step (D-222 cl. 2); the merge waits on it (D-223 cl. 10).
  Not provable in this seat, and not claimed.

**#411: a bad JSON from a source fails that source, never the night**
- `tests/unit/test_client_json_errors.py:60` (AST scan: every client `json.loads` on fetched bytes sits in a `try`
  catching `ValueError` and `RecursionError`; `:54` fails closed on an empty scan) and `:65` (100k-deep and
  4,400-digit Datacurve files fail Datacurve while SimpleBench after it stores 106 rows, through `_ingest_sources`)
  -- GREEN; F25 killed.

**#412** -> `tests/unit/test_simplebench.py:167` (200k newlines, no closing bracket: `SourceError` in under 1 s; 50.9 s
on the pre-fix commit) -- GREEN.
**#417** -> `tests/unit/test_arena_respelling.py:78` (20k-space names under 0.25 s; 0.03 s measured here) and `:68`
(id and effort pinned) -- GREEN.
**#419** -> `tests/unit/test_arena_respelling.py:115` (`GPT-4o (image)`, `(Image)`, `(audio)` refused) and `:124` (a
bracketed date stays the text model) -- GREEN; F26 killed.

**#426 (D-223 cl. 1): the build in a child the cycle kills; each source's time in the night's record**
- `tests/unit/test_refresh_build_child.py:27` (a child past its limit is killed, returns 124 within 10 s), `:35`
  (its own exit code otherwise), `:39` (a killed build fails the night; reason and record name `aider`;
  `source_seconds == {"litellm": 3.0, "aider": None}`), `:56` (every night records seconds), `:70` (through
  `_ingest_sources`: a failing source still writes its finish), `:94` (`main` hands `refresh` `build_in_child`)
  -- GREEN; F15-F18 killed. `:115`, `:131`, `:139` added here (B3).
- The three CLI tests that moved their patch to `build_in_child`
  (`tests/unit/test_refresh.py:561,588,612-618`): `main` passes `builder=build_in_child` by global lookup
  (`src/app/workflows/refresh.py:1748`), so the patch replaces exactly what production calls. With the production
  line reverted to the in-process build (F15), `test_refresh.py::test_the_cli_exit_codes_distinguish_published_
  unchanged_and_failed` and `:94` go red. Not weakened: same assertions, same exit codes.

**#403** -> `tests/unit/test_media_price_collision.py:29`, `:38` (a media board model with a text price is named in the
build's drift; an unpriced one is not) -- GREEN; F21 killed. Measured here on the main clone's artifact:
`media_price_collisions` returns `[]`, so the risk is latent.
**#404** -> `tests/unit/test_osworld.py:362` (non-ASCII board within twice its text), `:375` (1.6M references under
5 s) -- GREEN; F22 killed.
**#413** -> `tests/unit/test_record_schema_sync.py:44`, `:48` (planted drift found; empty constants fail) -- GREEN;
F24 (a status planted in the schema) killed.
**#410 (D-223 cl. 5)** -> `tests/unit/test_deploy_gate_pin.py:77` (forged tag + marker), `:89` (moved tag), `:98` (pin
edited on the branch), `:139`/`:150` (replace refs on the pin and on the base), `:166` (product file), `:124` (an
upgrade the owner merged owes no delta), `:185` (added here, B1: all three deploy surfaces) -- GREEN; F9-F14 killed.
`conformance/test-deploy-shipped.py` keeps its six cases, the missing-tag case now a missing-pin case -- PASS in
`make check`.
**#401 (D-223 cl. 6)** -> `docs/refusals.md` R-4 names the four spellings with the reason; held by
`tests/unit/test_nightly_hosted.py:273` (a stale gate deploys nothing and fails the night) and `:418` (both jobs run
only on main; the token is `fly-production`'s) -- GREEN. No code change.
**#408 (D-223 cl. 7)** -> `tests/unit/test_arena_slices.py:470` (a 96 MiB decode is still stopped at baseline +
40 MiB) and `:487` (an ordinary file reads under it) -- GREEN; F23 (ceiling not enforced) killed.
**#396 (D-223 cl. 8)** -> `tests/unit/test_client_decl_gate.py:1597` (12 rebuilt shapes refused), `:1623` (3 casts back
from an existential refused), `:1640` (the six admitted shapes, the counting loop's `if` among them, stay admitted)
-- GREEN; F19 (and each of `split`, `partition`, `removeAll` dropped alone) and F20 killed. `make client-decls` PASS.
**#447** -> `tests/unit/test_prd_status.py:61` (`D-222` and `D-1000` name a successor) -- GREEN.
**#450** -> `python -m app.workflows.plans --check-staleness data/plans.yaml` and the rosters' check, the CI
`plan-staleness` job's commands: both exit 0 here; 10 of 10 rows `last_verified: 2026-10-25`.

## Red to green on reported symptoms
Each red commit's own tests, run at the red commit and at its fix, in the second worktree:

| Issue | Red commit | Red | Fix | Green |
|---|---|---|---|---|
| #418 | `1b926e7` | 11 failed | `eaeee31` | 40 passed |
| #411 | `1225d48` | 3 failed | `dc75791` | 4 passed |
| #412 | `72fab74` | 1 failed (50.9 s) | `134e368` | 1 passed (0.1 s) |
| #417 | `39afe71` | 2 failed | `37f4742` | 119 passed |
| #426 | `2c32248` | 6 failed | `4d7fec8` | 91 passed |
| #419 | `24ce3a0` | 3 failed | `4076b6c` | 123 passed |
| #403 | `5884728` | 3 failed | `229e1aa` | 3 passed |
| #429 | `6a1a1d0` | 6 failed | `780f52b` | 49 passed |
| #410 | `ae02816` | 3 failed | `c912a80` | 6 passed |
| #410 B1 | `6233e49` | 1 failed | `831f072` | 9 passed |
| #396 | `d4ef69e` | 15 failed | `09572d9` | 21 passed |
| #447 | `9a14be1` | 1 failed | `2bd8dc1` | 4 passed |

#404, #413 and #408 are tests-only (no symptom in code); their tests were proven by fault injection (F22, F24, F23).

## Suite result
- `make test` at `b4dd4f1`: 4668 passed, 37 skipped, exit 0 (95.9 s, offline sandbox, artifact required);
  coverage-floor PASS; skip budget 96 of 96.
- At this review's head (`make check`): 4683 passed, 37 skipped; total coverage 93.00%.
- Coverage on touched code, `0bdf2eb` -> `b4dd4f1` -> this head: `workflows/refresh.py` 96.1% -> 94.9% -> 96.5%;
  `workflows/build.py` 95.3% -> 95.5%; `workflows/registry.py` 99.5% = 99.5%; `clients/datacurve.py` 98.7%,
  `livebench.py` 94.7%, `osworld.py` 95.0%, `simplebench.py` 100%, `terminalbench.py` 90.3%, `arena_slices.py` 98.5%,
  each unchanged. Total 92.89% -> 92.82% -> 93.0%.

## Fault-injection table
Each fault: one exact string replaced, the named tests run, the file's original bytes written back in place (never a
git checkout), md5 compared with the pre-injection hash and `git diff --quiet` on the file. Steps 2-5 ran as one
sequence per fault (`$TMPDIR/fi/fi.py`).

| # | Behaviour broken | Result | md5 after revert |
|---|---|---|---|
| F1 | #418 `_excused` by model again | killed `test_accepted_cuts.py:281` | adc1d57e identical |
| F2 | #429 no 30-day cap | killed `:332[year-9999]` | identical |
| F3 | #429 superseded ADR accepted | killed `:332[superseded]` | identical |
| F4 | #429 code-block header read | killed `:332[in-a-code-block]` | identical |
| F5 | #429 ADR need not name the board | killed `:332[names-another-board]` | identical |
| F6 | #418 an expired cut applies | killed `:337` | identical |
| F7 | #418 empty spelling key admitted | killed `:316` | identical |
| F8 | #418 cuts file not routed to security | killed `:305` | c8f0f875 identical |
| F9 | #410 pin read from the branch | killed `test_deploy_gate_pin.py:150` | cfaecf8b identical |
| F10 | #410 replace refs honoured | killed `:150` | identical |
| F11 | #410 `deploy_hosted_engine.sh` off the safety surface | killed `:109` | identical |
| F12 | #410 `nightly_hosted.sh` off the safety surface | **SURVIVED** -> killed by `:185` (B1) | identical |
| F13 | #410 `scripts/ci/` off the safety surface | **SURVIVED** -> killed by `:185` (B1) | identical |
| F14 | #410 compare with a tag, not the pin | killed `:124` | identical |
| F15 | #426 nightly entry builds in process | killed `test_refresh.py` CLI exit-codes, `test_refresh_build_child.py:94` | adc1d57e identical |
| F16 | #426 child never killed | killed `:27` | identical |
| F17 | #426 killed night names no source | killed `:39` | identical |
| F18 | #426 progress `done` only on success | killed `:70` | c8a9c0d2 identical |
| F19 | #396 `split`/`partition`/`removeAll` dropped (together, then each alone) | killed `test_client_decl_gate.py:1597` x4 | efd474c3 identical (see note) |
| F20 | #396 cast-back not recorded | killed `:1623` | efd474c3 identical |
| F21 | #403 collisions not reported | killed `test_media_price_collision.py:38` | identical |
| F22 | #404 `ensure_ascii` reverted | killed `test_osworld.py:362` | 413e2431 identical |
| F23 | #408 reader ceiling not enforced | killed `test_arena_slices.py:470` | 5af5bdfd identical |
| F24 | #413 a status planted in the schema | killed `test_record_schema_sync.py:44` | 3cef04c2 identical |
| F25 | #411 Datacurve catch narrowed | killed `test_client_json_errors.py:65` | 2c2a9196 identical |
| F26 | #419 a parenthesis no modality boundary | killed `test_arena_respelling.py:115` | fca8e67c identical |
| F27 | undeclared board accepted | **SURVIVED** -> killed by `test_accepted_cuts.py:376` (B2) | adc1d57e identical |
| F28 | blank reason accepted | **SURVIVED** -> killed by `:376` (B2) | identical |
| F29 | a board named twice accepted | **SURVIVED** -> killed by `:376` (B2) | identical |
| F30 | ADR id shape unchecked | **SURVIVED** -> killed by `:376` (B2) | identical |
| F31 | empty or non-string rows accepted | **SURVIVED** -> killed by `:376` (B2) | identical |
| F32 | #426 a `done` with no `start` counted | killed `test_refresh_build_child.py:115` (B3) | identical |
| F33 | #426 an unreadable progress file raises | killed `:131` (B3) | identical |
| F34 | #426 every stream handed to the child | killed `:139` (B3) | identical |

Tally: 37 faults (F1-F34, F19 run as four). 30 killed by the range's tests; 7 survived (F12, F13, F27-F31); all 7
killed by this review's tests. F32-F34 prove B3's tests red.

Note on F19: the harness's first revert replaced the wrong occurrence of `reduce|` in `scripts/client_decl_gate.py`.
The byte check caught it (md5 differed, `git diff` not clean); the file was repaired by two exact string edits to
HEAD's md5 `efd474c341aee456e41510ea960085d0` (`git diff --quiet` clean), the harness changed to write the
pre-injection bytes back, and F19 and F20 were re-run. The F20 result above is from that re-run.

## Test integrity
- **Deleted with the Mac scripts (#427, `eefbe5f`):** `tests/unit/test_engine_service.py` went from 37 tests to 8.
  Six are kept by name, and two were rewritten rather than dropped: the app-script test (now `:34`, starts no engine)
  and the remover test (now `:23`). A static map of the other 29 bodies shows each ran or read
  `scripts/engine_service.sh` (`_launch`, `LAUNCHER`) or `scripts/install_engine_service.sh` (`_install`, `_deploy`,
  `_installer`, `INSTALLER`), both deleted. The two preflight tests ran `validate_startup_config`
  through the launcher; the function itself stays held by `tests/unit/test_engine_host.py:59`,
  `tests/unit/test_board_standings.py:346-350` and `tests/unit/test_api_config.py`. Also dropped: the
  hand-kept-epoch-bundle pin on `ios/app.sh` (`test_nightly_refresh.py`; the script now starts no engine, `:34`) and
  `test_the_served_path_is_the_one_the_installer_serves` (read the deleted installer). INV-27..29 are retired by D-224
  with watchlist rows; the security-invariants trial rows 3-5 that killed them go with them. No deleted test held
  surviving code.
- **The three CLI tests in `tests/unit/test_refresh.py` (#426):** see #426 above; the patch target is the one
  production calls, F15 shows it.
- **The two `UnlinkedRow` identity assertions (v0.1.0 range):** still present, unchanged in this range
  (`tests/unit/test_refresh_boards.py:90`, `tests/unit/test_uncovered_boards.py:82`).
- **Changed, not weakened:** `test_arena_respelling.py:68` is stronger (id and effort pinned);
  `test_engine_address.py:157` and `test_testflight_ready.py:84` assert the retired prompt and `--lan` are absent;
  `test_dependency_locks.py` moved its three install sites from the deleted installer to `scripts/ci/nightly-hosted.yml`;
  `test_arena_slices.py:470,487` move the ceiling to baseline + 40 MiB and F23 shows the ceiling still stops a file;
  `conformance/test-deploy-shipped.py` keeps its six cases. No `skip` or `xfail` was added in the range.
- **Weakened by construction (B2):** D-221 added a required key, so the pre-existing negative cases at
  `test_accepted_cuts.py:92-125` stopped reaching the checks they were written for. Found by F27-F31, closed at `:376`.

## Mocks / contract tests
- No new external integration. #411 and #426 drive `app.clients.fakes.FakeRawSource`, the canonical fake, through
  `build._ingest_sources`. The contract tests (`tests/integration/`) are unchanged and skip without
  `RUN_CONTRACT_TESTS`, as the CI contract job runs them.

## BLOCKING
None open. Found and closed in this review, each by a test on this branch:
- **B1** `scripts/deploy_gate.py:213-215` -- D-223 clause 5 put `scripts/nightly_hosted.sh` and `scripts/ci/` on the
  safety surface, but only `deploy_hosted_engine.sh` was planted in a test; removing either stayed green (F12, F13).
  Closed by `tests/unit/test_deploy_gate_pin.py:185`, which names the three surfaces itself (`b70fc0b`).
- **B2** `tests/unit/test_accepted_cuts.py:92-125` -- since `until:` became required (D-221), the undeclared-board,
  named-twice, ADR-shape, reason and rows checks of `src/app/workflows/refresh.py:320-347` ran in no test; removing
  each stayed green (F27-F31). Closed by `tests/unit/test_accepted_cuts.py:376`, valid cuts but for one field, the
  refusal's message pinned (`b1aa0da`).
- **B3** `src/app/workflows/refresh.py` -- coverage fell 96.1% -> 94.9% (permission-matrix section 11): the progress
  reader's torn-line and unreadable-file branches and `_has_fileno`'s refusal (`:1463-1484`) and the B2 branches.
  Closed by `tests/unit/test_refresh_build_child.py:115,131,139` (`e87f9a9`); 96.5% now.

## MINOR (the author fixes each in this wave or files it as an issue)
- **M1** `src/app/clients/terminalbench.py:52-54` -- the widened catch in `TerminalBench4Client.fetch_raw` is held
  only by the AST shape scan (`tests/unit/test_client_json_errors.py:60`); no test drives a deep or 4,300-digit
  listing through it. Coverage unchanged from the base (90.3%).
- **M2** `tests/unit/test_arena_respelling.py:78`, `tests/unit/test_simplebench.py:167`,
  `tests/unit/test_osworld.py:375` -- three new wall-clock bounds, the shape #408 retired for memory. Margins are wide
  here (0.03 s against 0.25 s; 0.1 s against 1 s), but the bracket test's red margin is only about 4x (1.0 s pre-fix on
  this Mac): a much faster runner could pass the quadratic form. A step counter would not depend on the machine.

## Tests added this review
- `tests/unit/test_deploy_gate_pin.py:185` (`b70fc0b`) -- D-223 cl. 5, #410: each of `scripts/deploy_hosted_engine.sh`,
  `scripts/nightly_hosted.sh`, `scripts/ci/nightly-hosted.yml` is code to the gate even byte-identical to the pinned
  commit. Red under F11, F12, F13.
- `tests/unit/test_accepted_cuts.py:376` (`b1aa0da`) -- D-220 cl. 3, D-221, INV-54: nine cuts valid but for one field,
  each refused by its own check. Red under F27-F31.
- `tests/unit/test_refresh_build_child.py:115,131,139` (`e87f9a9`) -- #426: the progress reader keeps only whole
  events, an unreadable progress file names no source, a stream with no descriptor is not handed to the child. Red
  under F32-F34.

## make check
`make check` in this seat's worktree at `e87f9a9`, run serially as the merge gate, before this verdict was written:
exit 0. session-check, lint (ruff clean), typecheck (mypy: no issues in 54 files), pytest (4683 passed, 37 skipped,
offline sandbox, artifact required; coverage 93.00%), coverage-floor (54 modules), check-records and its selftest,
install-check, wave-check-all (68 records), conformance (33, `test-deploy-shipped` among them), swift-test (727, and
SlowTierTests 7 of 7) and client-decls (22 files, 4 configurations) all PASS. Each of the three test commits also
passed the commit-msg hook's `make check-fast`.
