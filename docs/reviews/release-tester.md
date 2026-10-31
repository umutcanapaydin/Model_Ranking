---
record_type: review
id: release-tester
status: draft
seat: independent
process_version: v7.2
date: 2026-10-31
---
# Release Tester Review

This verdict is the light-mode Tester for release v0.2.0, dispatched by run v020 (`docs/plans/run-v020.md`) before the
release. It replaces the v0.1.0 verdict (PASS, reviewed head `0bdf2eb`, written at `471dd79`), which stays in git
history. That verdict carried M1-M3 of the `9d3cf0e` verdict; all three are closed in this range: M1 by #418 (the cut
is retired, expires and excuses by name), M2 by #417 (`tests/unit/test_arena_respelling.py:68` pins id and effort),
M3 by `1b926e7` (the docstring cites D-220 clause 3).

**Reviewer:** Tester subagent (`.claude/agents/Tester.md`, `AGENTS.md` and `.agents/rules/practices.md` read from
`main`). I had fresh eyes and wrote none of the range's code or tests. The only tests I wrote are the commits
listed under "Tests added this review", each on a review branch of my own, after the range it reviewed.
**Independent:** yes
**Date:** 2026-10-31 (the delta round 2026-10-31b, `ed18de5..243d115`, and before it the delta round of run 1030 and
the fixes before it; the night-1028 delta round was 2026-10-29,
the night-1027 and the launchd-guard and build-6 delta rounds were
2026-10-27, the nightly, hotfix-1026 and B5 rounds 2026-10-26, the full round 2026-10-25)
**Commit range:** this round `ed18de5bef8ad54d501b8a268db9900073ab903f..243d115` (`integration/fixes-1031`: #517,
#522, #518, #535; D-232, D-233); the round before it `3cddbddaa777f327b1a2bf0bb2ff7a35b9e196e9..290557c39d6e672877cf6399b9d21eab2403ffbf`
(#496, #494, #488, #493, #500, #484, #510, #506, #511, #509, #503, #501, #505, the guard patch #497/#498; D-230,
D-231); the full round `0bdf2eb2fa3f92439b29e6b58a71948b9722e15d..b4dd4f1a0da43b6371a44105b404e568021f7c7f`, the head of
`integration/run-v020` (draft PR #432): #418, #427, #411, #412, #417, #426, #419, #403, #404, #413, #429, #410, #401,
#408, #396, #447 and #450, plus the owner's #424 CI change (`15e5c9e`, `697f758`). 86 files, 83 commits. Rulings:
D-221, D-222, D-223, D-224.
**Reviewed head:** 6e6f5beb81fc12d29d51540fc132be230d8d880b (the delta round 2026-10-31b, `ed18de5..243d115`, the
head of `integration/fixes-1031`, plus this round's three tests committed at `6e6f5be` on `review/release-delta-1031b`;
the 2026-10-31 delta round's head was `ed18de5`; the night-1028 re-check's head was `3cddbdd`, the night-1028 delta round's `e00c516`,
the night-1027 delta round's `07a7fc6`, the 2026-10-27 delta
round's `50c4764`, the B5 re-verify round's `9ef6448`, the hotfix-1026 delta round's `20008c6`,
the nightly delta round's `0222150`, the full round's `e87f9a9`)
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
PASS -- 0 BLOCKING open, 0 MINOR open in this file. The delta round 2026-10-31b (below, `ed18de5..243d115`: #517,
#522, #518, #535; D-232, D-233) found every acceptance criterion proven by a citing test through the real entry point
(`scripts/deploy_gate.py` run as a program on a git fixture; `make client-decls` for #535), each red on the code
before its fix where the issue fixes code; `make check-fast` is green at `6e6f5be` (pytest 4919 passed, 37 skipped;
client-decls PASS in 4 configurations). 26 faults: 22 killed by the range's own tests or gate; the 4 that stayed
green (F7: `all(found)` weakened to `any` in `devflow_pins`; F9: `pushd` dropped; F14: `--chdir` dropped; F20: `/`
added to the runner's look-behind) are closed by this round's tests at `6e6f5be`. M10, M11 and M12 of the round before are filed
as #525, #526 and #527 and are tracked there, not here.

The 2026-10-31 delta round, as it read when it closed: MINOR -- 0 BLOCKING open, 3 MINOR open (M10, M11, M12, all new). The 2026-10-31 delta round (below,
`3cddbdd..290557c`) found every acceptance criterion of the thirteen issues closed in the range, and of the owner's
guard patch, proven by a citing test, each red on its reproduce commit where the issue fixes code; `make check` is
green at `290557c`, and `make ui-test` against an artifact built today is green (23 of 23 with the engine up, 2 of 2
with it down) once the simulator is booted. 49 faults: 43 killed by the range's own tests; two that stayed green
(F12b, #510's check in the one verified reader; F19, `--work-tree` on the untracked listing) are closed by this
round's two tests, which the run's session applies; the other four are equivalent or harmless. M10: #503's fix in
`scripts/ui_test.sh` fails quietly when the simulator was shut down before the run. M11: `GIT_WORK_TREE` in the
environment makes `make deploy-check` judge another tree and PASS (handed to the Security-Reviewer, Escalate-NOW
class; the guard's `--judge` is not fooled and `fly deploy` stays the owner's). M12: #484's button runs in no UI
test. None blocks tonight's deploy as far as the tests go.

The night-1028 re-check, as it read when it closed: MINOR -- 0 BLOCKING open, 0 MINOR open. M8 and M9, the night-1028 round's two, are fixed at `0f1837f` and re-checked
(below, "Night-1028 re-check"); M9's UI test is the owner's run on the simulator before the build 7 upload. As the
night-1028 round read when it closed: MINOR -- 0 BLOCKING open, 2 MINOR open (M8 and M9, both new); M1, M2, M3
(#456), M4 (#457), M6 (#466) and M7 (#477) are closed in this range. The night-1028 delta round (below, `07a7fc6..e00c516`) found every acceptance criterion of
the run's eleven issues proven by a citing test, each red on its pre-fix commit where the issue fixes code; eight
faults in the new code stayed green (F83, F84, F99, F109, F110, F114, F123, F124), and this round's tests close all
eight. M8: the #463 ratio's 0.5 s floor sits within about 2x of the #417 regression's own time. M9: #481's screen
wiring ran in no test here, and the existing UI test reads the caption's label, which the guide's button changes.
Neither blocks the deploy or the build 7 upload.

The night-1027 delta round, as it read when it closed: MINOR -- 0 BLOCKING open, 6 MINOR open (M1, M2, M3 #456, M4
#457, M6 #466, and M7, new). The night-1027 delta round
(below, `50c4764..ac7bba9`) found D-227 and D-228 each proven by a citing test that is red before its fix; six faults
in D-228's new code stayed green, and `07a7fc6` closes all six. M7: the committed re-spelling expires on 2026-11-10,
after which every hosted night fails, by design, and so do at least 92 unit tests that read the committed file
against today's date; nothing tracks retiring it. Not a deploy blocker.

The 2026-10-27 delta round, as it read when it closed: MINOR -- 0 BLOCKING open, 5 MINOR open (M1, M2, M3 #456,
M4 #457, M6 #466), none new. The 2026-10-27 delta round
(below, `9ef6448..f32cdbf`) found the guard's launchd retirement, its re-pin and build 6 to be what they say; it closed
one test gap of its own (a case #470 deleted with the launchd rules) in `50c4764`.

The B5 re-verify round, as it read when it closed: MINOR -- 0 BLOCKING open. B5 is closed by `133d638` (D-226) and re-verified below: its test is red at `6cf0e51` and
green at `133d638`. 5 MINOR open: M1, M2 (full round), M3 (#456), M4 (#457), M6 (#466). M5 is answered by D-226
clause 3.

The hotfix-1026 delta round, as it read when it closed: BLOCKING -- 1 BLOCKING open (B5: a D-225 republish skipped
the re-read that stops a publish over an artifact replaced mid-cycle), 6 MINOR (M1-M6).

The rounds before this one, as they read when they closed: MINOR -- 0 BLOCKING open, 4 MINOR (M1, M2 from the full
round; M3, M4 from the delta round of 2026-10-26, below). The delta `e87f9a9..b762ffe` found one fault that stayed green, a non-executable `scripts/nightly_hosted.sh`
(B4); it is closed by `0222150`. The full round found three BLOCKING findings, and each is closed by a test this review added
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
- **B5** (hotfix-1026 delta round) `src/app/workflows/refresh.py:1663` -- a D-225 republish skipped W-047's re-read.
  Reproduced by `tests/unit/test_release_restamp.py:150` (`6cf0e51`, red), fixed by `133d638` (D-226: the re-read
  `_replaced_underneath`, `:1285`, runs on `same`, `:1668`); re-verified in "B5 re-verify round" below.
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
- **B4** (delta round) `scripts/nightly_hosted.sh` -- its exec bit was held by no test (F43). Closed by
  `tests/unit/test_nightly_hosted.py:497` (`0222150`).

## MINOR (the author fixes each in this wave or files it as an issue)
- **M10**, **M11**, **M12**: from the 2026-10-31 delta round, set out under "Delta MINOR" of that round below; each
  open, to be fixed or filed as an issue (M11 through the Security-Reviewer first).
- **M8**, **M9**: from the night-1028 delta round, set out under "Night-1028 delta MINOR" below; both fixed at
  `0f1837f` and re-checked. M1-M4, M6 and M7 are closed there, by #452, #463, #456, #457, #466 and #477.
- **M7**: from the night-1027 delta round, set out under "Night-1027 delta MINOR" below.
- **M5**, **M6**: from the hotfix-1026 delta round, set out under "Delta MINOR (hotfix-1026)" below. M5 is answered
  by D-226 clause 3; M6 is filed as #466. M3 and M4 are filed as #456 and #457.
- **M3**, **M4**: from the delta round of 2026-10-26, set out under "Delta MINOR" below.
- **M1** `src/app/clients/terminalbench.py:52-54` -- the widened catch in `TerminalBench4Client.fetch_raw` is held
  only by the AST shape scan (`tests/unit/test_client_json_errors.py:60`); no test drives a deep or 4,300-digit
  listing through it. Coverage unchanged from the base (90.3%).
- **M2** `tests/unit/test_arena_respelling.py:78`, `tests/unit/test_simplebench.py:167`,
  `tests/unit/test_osworld.py:375` -- three new wall-clock bounds, the shape #408 retired for memory. Margins are wide
  here (0.03 s against 0.25 s; 0.1 s against 1 s), but the bracket test's red margin is only about 4x (1.0 s pre-fix on
  this Mac): a much faster runner could pass the quadratic form. A step counter would not depend on the machine.

## Tests added this review
- 2026-10-31 round, as files for the run's session to apply (not committed by this seat), under
  `tester-1031/` in this session's scratchpad, mirroring their repository paths:
  `tests/unit/test_deploy_gate_505_tester.py:20` (#505, the #505 review's M2 by the environment: a new code file is
  a change to the guard's `--judge` whatever `GIT_WORK_TREE` names; red under F19b) and
  `tests/unit/test_deploy_gate_510_tester.py:20` (#510, #511: the one verified reader refuses a commit that does not
  hash, on its own; red under F12d). Once they are committed, the commit that carries them is the head this verdict
  covers: the session sets `**Reviewed head:**` to it, since the gate counts tests as code.
- Night-1028 round, as working-tree changes on `e00c516` for the run's session to commit (the seat has no
  `advisor.db`, so its commit hook cannot pass): `tests/unit/test_refresh_build_child.py:182` (#453 M2: `_Limits`,
  the alarm `main` sets, is the clock `build_in_child` reads, and a closed cycle leaves none; red under F83, F84),
  `tests/unit/test_accepted_respellings.py:278` (#478: a new model with a name no pair lists does not move; red under
  F99), `:352` (#477: without the fixture both loaders default to the committed file; red under F109, F110),
  `tests/unit/test_deploy_gate_444.py:66` (#444 M3: a dispatched workflow whose file name is not lower-case is on the
  surface; red under F114), `ios/EngineTests/FrontDoorTests.swift:923` with its manifest line (#481: no sentence of a
  Turkish guide is an English one; red under F123, F124).
- `tests/unit/test_accepted_respellings.py:268,276` (`07a7fc6`, night-1027 round) -- D-228 clause 2: one shape per
  condition of `_respelled_ids` (old model kept, new name onto a kept model, old name kept, new name already
  served, the night after the publish) leaves `respelled`'s result equal to the candidate; a re-spelled model with
  two rows beside an unlinked row reads as the board it was. Red under F60-F63, F73 and F74.
- `tests/unit/test_release_restamp.py:173` (`9ef6448`, B5 re-verify round) -- D-226 clause 1: a republish past a
  serving bound publishes and counts no refusal, and a night whose content moved is still refused at the bound. Red
  under F57.
- `tests/unit/test_release_restamp.py:93,112,126` (`20008c6`, hotfix-1026 round) -- D-225: the republish's reason and
  record (red under F48), an unreadable record taken over by the release (red under F45), and #460 end to end: the
  hosted deploy refuses the older release's data, then accepts it after the release's quiet night, and the startup
  catch-up (#258) sees no other release's data (red under F49).
- `tests/unit/test_release_restamp.py:150` (hotfix-1026 round, the declared red commit after this verdict) -- B5: a D-225
  republish must not overwrite an artifact replaced mid-cycle. RED at `6411610`; green under F47.
- `tests/unit/test_deploy_gate_pin.py:185` (`b70fc0b`) -- D-223 cl. 5, #410: each of `scripts/deploy_hosted_engine.sh`,
  `scripts/nightly_hosted.sh`, `scripts/ci/nightly-hosted.yml` is code to the gate even byte-identical to the pinned
  commit. Red under F11, F12, F13.
- `tests/unit/test_accepted_cuts.py:376` (`b1aa0da`) -- D-220 cl. 3, D-221, INV-54: nine cuts valid but for one field,
  each refused by its own check. Red under F27-F31.
- `tests/unit/test_refresh_build_child.py:115,131,139` (`e87f9a9`) -- #426: the progress reader keeps only whole
  events, an unreadable progress file names no source, a stream with no descriptor is not handed to the child. Red
  under F32-F34.
- `tests/unit/test_nightly_hosted.py:497` (`0222150`) -- #455, D-217 clause 7: every tracked file the nightly workflow
  starts as a command is executable on disk and `100755` in git's index. Red under F43, and red at `761f9c6`.

## make check
`make check` in this seat's worktree at `e87f9a9`, run serially as the merge gate, before this verdict was written:
exit 0. session-check, lint (ruff clean), typecheck (mypy: no issues in 54 files), pytest (4683 passed, 37 skipped,
offline sandbox, artifact required; coverage 93.00%), coverage-floor (54 modules), check-records and its selftest,
install-check, wave-check-all (68 records), conformance (33, `test-deploy-shipped` among them), swift-test (727, and
SlowTierTests 7 of 7) and client-decls (22 files, 4 configurations) all PASS. Each of the three test commits also
passed the commit-msg hook's `make check-fast`.

## Delta round 2026-10-26 (e87f9a9..0222150)

**Range:** `e87f9a943548fee88dea9f8f759a55e2a02815a9..b762ffec9b33c2b1be96fe15b286af788ea4b3fd`, plus this round's
test commit `0222150`. The code it changes is three files, which the owner merged in #454 and #455. The rest of the
range is records already reviewed: this verdict, `release-security.md`, `docs/releases/v0.2.0.md`, `run-v020.md`,
`owner-actions.md`, `process-log.md`, `security-invariants.md`.
**Seat:** my own worktree `$TMPDIR/wt-tester-nightly` on `review/release-tester-nightly`, cut from `b762ffe`. Its own
`.venv` was built by `make install` from the hash-checked locks, because the commit-msg hook's `check-fast` needs a
venv this tree owns (`scripts/venv_owner.py`). It used a read-only copy of the main clone's `advisor.db`. A detached
worktree at `761f9c6` ran the red half of the red-to-green pair and was removed clean. Nothing was pushed. No
launchd, owner data directory, Fly or GitHub call was made.
**Fresh eyes:** I wrote none of `e6647b9`, `d2b77de` or `023522a`. My only code in the range is the test in
`0222150`.

### Per change
- **`.github/workflows/nightly-hosted.yml` (new, D-217 clause 7)**: `cmp` against `scripts/ci/nightly-hosted.yml` shows
  the two are byte-identical. They are held equal by `tests/unit/test_nightly_hosted.py:476`. **F40**: a one-byte
  drift (the first `n` of `nightly` changed to `N`) turned it RED (1 failed). It was reverted in place, and md5
  `d97dbc02dda501914795589da4d7447c` matched before and after. The proposal's shape, which is now the installed
  file's shape, stays held by the workflow tests at `:404-473`. **F41**: deleting the installed file stayed GREEN
  (43 passed, and conformance PASS); the file was moved back, md5 unchanged. See M3.
- **`conformance/test-ci-yaml.py:88-92` (the fallback parser skips keys nested deeper than a step's own keys)**:
  **F42**: removing the 5 lines turned `test-ci-yaml` RED (exit 1, "the stdlib fallback parser disagrees with PyYAML
  on job `refresh`" and "... `deploy`", `:375`), and `conformance/run-all.py` turned RED with it (1 failing). That is
  the conformance job CI runs (`.github/workflows/ci.yml:175`). The lines were put back by exact string replacement,
  md5 `d162f14f74e2d613bf0bc6f339994441` before and after. The commit before the fix, `e6647b9`, carries these
  same bytes, so this is also the fix's red-to-green pair. The test holding the fix is the PyYAML-agreement check
  run over the installed `nightly-hosted.yml`. Nothing in the file's own samples holds it. See M4.
- **`scripts/nightly_hosted.sh` mode 644 -> 755 (#455)**: **F43**: `chmod 644` stayed GREEN on
  `tests/unit/test_nightly_hosted.py` and `test_deploy_gate_pin.py` (54 passed), and conformance stayed PASS. Every
  test starts the script with `/bin/bash <script>` (`:44-45`), which never reads the mode. The workflow starts it as
  a command (`.github/workflows/nightly-hosted.yml:86,97,144`). That is the failure #455 fixed: "so the nightly run can
  start it" (`023522a`). This is **B4**, closed by `tests/unit/test_nightly_hosted.py:497` (`0222150`). The test
  derives from the workflow's `run:` lines every tracked file started as a command. It asserts each one is
  executable on disk and tracked `100755` in git's index, which is what a runner's checkout reads. It fails if
  `nightly_hosted.sh` is not in the derived set. With the new test, `chmod 644` turned RED ("not executable on
  disk"), and so did `git update-index --chmod=-x` ("tracked with mode 100644"). Both were reverted, and the index
  is again `100755 c9c964d`. **Red to green:** the test is RED at `761f9c6`, the merge before the fix, where the
  index holds `100644`, and GREEN at `b762ffe`. `scripts/deploy_hosted_engine.sh`, which `nightly_hosted.sh`
  `exec`s directly (`:49,90`), was already held: the scratch-repository tests copy it with its mode and run it.

### Delta BLOCKING
None open. **B4** (above) was found and closed in this round by `tests/unit/test_nightly_hosted.py:497`.

### Delta MINOR
- **M3** `tests/unit/test_nightly_hosted.py:478` -- `if INSTALLED.exists()` made the equality test vacuous while the
  workflow was a proposal. Now that the owner has installed it, deleting `.github/workflows/nightly-hosted.yml`
  stays green (F41). That turns the nightly refresh and deploy off without a red test. Since the night is now the
  only route to the hosted engine (D-217, D-222), the test could require the installed file.
- **M4** `conformance/test-ci-yaml.py:88-92`, `:251` -- the parser fix is held only because the current installed
  `nightly-hosted.yml` happens to nest `name:` under `with:`. The self-proof samples (`MUST_FIRE`/`MUST_PASS`) have no
  such step. If that workflow is removed or reworded, reverting the fix stays green. The check also runs only where
  PyYAML is present, so the machine without PyYAML that the fallback serves is never shown the fix. A step-parse
  sample with a nested `with: name:` would hold it. That is a change to a control (`/writing-a-control`), so it is
  the author's to make, not this seat's.

### Delta test integrity
`git diff e87f9a9..b762ffe -- tests/` is empty. No test was weakened, skipped or deleted in the range.

### Delta suite result
- `make test` in this seat at `0222150`: 4684 passed, 37 skipped, offline sandbox, artifact required. Coverage was
  93.00%, the same as the full round. coverage-floor PASS (54 modules), and the skip budget was 96 of 96.
- `0222150` passed the commit-msg hook's `make check-fast`. `ruff check` on the changed test is clean.
- **Mutation kill-rate (advisory):** no runner is wired. Hand faults F40-F43: 2 killed on the range's own tests
  (F40, F42) and 2 survived (F41, F43). F43 is killed after `0222150`. F41 still survives (M3).

## Delta round 2026-10-26 hotfix (0222150..20008c6)

**Range:** `0222150b195f2eba06fe33707c1124fcbd8ad70b..6411610`, the head of `integration/hotfix-1026` (local, not
pushed), plus this round's two test commits: `20008c6`, and B5's declared red test in the commit after this verdict. Three branches, merged into the lane by merge
commits: `fix/issue-460-unchanged-restamp` (#460, D-225; `src/app/workflows/refresh.py`, red test `7c542db`),
`fix/issue-459-version` (#459; `pyproject.toml` and `APP_VERSION` 0.1.0 -> 0.2.0, red test `27bb96f`) and
`enhancement/issue-461-retire-remover` (#461; `scripts/remove_engine_service.sh` and its one test deleted, docs, a
`.path-refs-allow` row, owner-actions rows). The rest of the range is records already reviewed (`cd00af7`, the v0.2.0
release merge).
**Risk tier:** HIGH. #460 adds a publish path to the refresh cycle and lifts its refusals on that path; the deploy
gate's data-builder check reads what that path writes.
**Seat:** my own worktree `$TMPDIR/wt-tester-1026` on `review/tester-hotfix-1026`, cut from `6411610`. The fault
runs used the main clone's `.venv` interpreter with `PYTHONPATH` on this worktree's `src` and
`PYTHONDONTWRITEBYTECODE=1`; the commit-msg hook's `check-fast` needs a venv this tree owns, so `make install` built
one here before the first commit. A read-only copy of the main clone's `advisor.db`. Two detached worktrees at
`7c542db` and `27bb96f` ran the red halves and were removed clean. Nothing was pushed; no launchd, owner data
directory, Fly or GitHub call was made.
**Fresh eyes:** I wrote none of `e6c5497`..`1ab57a0`. My only code in the range is the two test commits.

### Acceptance-criterion coverage (hotfix-1026)
- **#460 / D-225 clause 1** (a release's unchanged cycle over another builder's artifact publishes, and the record
  names this release) -> `tests/unit/test_release_restamp.py:35` (asserts `EXIT_PUBLISHED`, equal fingerprints,
  `served_built_by == release-bbbbbbb`, and the served file is the new build: `observed_at == LATER`) -- GREEN.
  "Or none": `:76` (`{}`) and `:112` (`not json`, empty; added here) -- GREEN.
- **D-225 clause 2** (the refusals are skipped on `same`) -> no test needs it: F47 (computing the refusal on `same`)
  stays green on every test of the range and of this round. What the skip lifts on `same` is B5.
- **D-225 clause 3** (no release stamp, or the same release, stays unchanged) -> `:51` (same release) and `:60`
  (`None`, `dev-abc1234`, `unknown`) -- GREEN; red under F44 and F46.
- **D-225 clause 4 / the goal** (the deploy accepts the data a release's quiet night republished) ->
  `tests/unit/test_release_restamp.py:126` (added here): a scratch repository whose served record names
  `release-1234567` is refused by `scripts/deploy_hosted_engine.sh --dry-run`; a refresh with
  `APP_BUILD=release-<HEAD short>` (as `scripts/nightly_hosted.sh:55` stamps it) and identical content publishes;
  the deploy then passes, its stamp ends `-from-<HEAD short>`, and `nightly.built_by_another` is False -- GREEN.
- **#459** (`/health` == `APP_VERSION` == the package version; the package is never older than the newest
  `docs/releases/v*.md`) -> `tests/unit/test_app_version.py:39`, `:44` -- GREEN.
- **#461** (nothing runs or tests the remover; INV-73's test stays) -> `git grep remove_engine_service` leaves only
  the Bash guard that refuses running it (`.claude/hooks/bash_guard.py:424`, its tests at
  `tests/unit/test_bash_guard_bounds.py:546`), the ADR and record history, and the `.path-refs-allow` row. INV-73
  still cites `tests/unit/test_engine_service.py:57`, which exists and passes; renaming it turned
  `tests/unit/test_security_invariants.py::test_the_list_holds_together` RED (F54).

### Red to green (hotfix-1026)
- **#460**: at `7c542db` (the red commit, before the fix) `test_release_restamp.py` is 2 failed, 4 passed
  (`:35`, `:76`); at `6411610` all pass.
- **#459**: at `27bb96f` `test_app_version.py:44` fails ("pyproject.toml says 0.1.0, but docs/releases/ records
  v0.2.0"); at `6411610` both pass. `:39` passes on both sides, as it should: the two copies agreed at 0.1.0.
- **B5** (this round): `test_release_restamp.py:150` is RED at `6411610` ("a concurrent publish was overwritten:
  unchanged content, republished as this release's own build (D-225)"); it turns green under F47.

### Fault-injection table (hotfix-1026)
Each fault was one exact string replacement made by a script that wrote it, ran the tests, put the original bytes
back at the same offset and compared md5 before and after; every row's md5 matched
(`refresh.py` `f130ab1b8f18619a837b1398abccd83d`, `main.py` `0d15ef484eae8762365760feab2280c1`, `pyproject.toml`
`2e91ddedb97363e2e5d53c9ee02118f9`, `test_engine_service.py` `76797a9d4441523706128452d7ac4c9a`). The set: the
eleven refresh, nightly, stamp and deploy test files (334 tests) for F44-F49, `test_app_version.py` for F50-F53.

| ID | Fault | Range's tests | After this round |
|---|---|---|---|
| F44 | `_another_release_built` without the `startswith("release-")` check | RED (7 failed: `:60` x3, `test_refresh.py` x3, `test_refresh_carry.py` x1) | RED |
| F45 | an unreadable record returns False | GREEN (334 passed) | RED (`:112` x2, `:150`) |
| F46 | an equal `served_built_by` republishes anyway (churn) | RED (`:51`) | RED |
| F47 | the refusal is computed on `same` (clause 2 removed) | GREEN (334 passed) | GREEN, and it turns B5's `:150` green: the remedy, not a hole |
| F48 | the republish's reason reads "the served content changed" | GREEN (334 passed) | RED (`:93`) |
| F49 | `_another_release_built` never consulted (#460 reverted) | RED (`:35`, `:76`) | RED (6 failed, `:126` among them) |
| F50 | `APP_VERSION` alone 0.2.1 | RED (`test_app_version.py:39`) | RED |
| F51 | `pyproject.toml` alone 0.2.1 | RED (`:39`) | RED |
| F51b | `APP_VERSION` alone 0.1.9 | RED (`:39`) | RED |
| F52 | a `docs/releases/v9.9.9.md` record added (removed after) | RED (`:44`) | RED |
| F53 | `docs/releases/` emptied (both records moved out and back, md5 `62dca946...`, `cbb4c0d3...` unchanged) | RED (`:44`, "no release record ... names a version") | RED |
| F54 | INV-73's cited test renamed | RED (`test_security_invariants.py`) | RED |

**Mutation kill-rate (advisory):** no runner is wired for this stack. Hand faults F44-F54 (12): 9 killed on the
range's own tests, 3 survived (F45, F47, F48). After this round F45 and F48 are killed; F47 survives by design and is
the remedy for B5.

### Interactions checked (hotfix-1026)
- **`consecutive_refusals`**: a republish is `EXIT_PUBLISHED`, so the count goes to 0 as on any served cycle
  (`refresh.py:1053-1056`); `:93` seeds 2 and asserts 0.
- **`sources_last_ok`**: `served` covers both published and unchanged (`refresh.py:1074-1077`), so the republish
  moves the same arrivals an unchanged night did. No change in behaviour.
- **Carried and expired sources on `same`**: `same` compares the candidate with the live digest
  (`refresh.py:1641`). The build drops an expired source's rows, so `same` with a non-empty `expired` happens only
  when those rows changed nothing served. Then `_served_without` (`:1345`) equals the live artifact in what it
  serves, and `degradations`/`upward_anomalies` (`:1268-1278`) have nothing to report: skipping them on `same` lets
  through no removal a user sees. What it drops are unserved rows, which an unchanged night kept. The record's
  `carried`/`expired` (`:1083-1092`) are written the same on both outcomes. Not a finding.
- **The two refusals that are not about change**: `_reason_to_refuse` also holds the serving-bound check on the
  candidate (`:1264-1266`, D-173 clause 4) and the re-read of the live artifact before a publish (`:1286-1294`).
  D-225 clause 2's reason ("they guard what a user would see change") holds for neither. The bound check on an
  identical-serving candidate repeats what the live file already is, so skipping it is not worse than the unchanged
  night it replaces. Skipping the re-read is B5.
- **#258 startup catch-up** (`src/app/adapter/nightly.py:163`): before D-225 a release engine with the in-process
  nightly caught up at every startup and never converged on quiet data, because an unchanged cycle kept the old
  builder's name. After a republish `built_by_another` is False (`:126`). The switch is refused in production, so
  this is not reached on Fly.

### Delta BLOCKING (hotfix-1026)
- **B5** `src/app/workflows/refresh.py:1663` (`refusal = None if same else _reason_to_refuse(...)`) -- a D-225
  republish skips the re-read before `candidate.replace(target)` (`:1690`). That re-read is W-047's guard: the lock
  stops two refreshes, never a hand-run `build.py`. An independent review once demonstrated a 95.0 build published
  mid-cycle and overwritten (`tests/unit/test_refresh.py:1300`). Before D-225 an unchanged cycle never published, so
  it never needed the re-read. Now a release's quiet night publishes over any artifact that replaced the live one
  while it built, and the record names this release as its builder. The new publish path has no test for it; F47
  shows that nothing in the range needs clause 2's skip. **Reproduced:**
  `tests/unit/test_release_restamp.py:150` (the declared red commit after this verdict) is RED at `6411610`: the 95.0
  artifact is lost and the outcome is `published`. **Exposure:** low in today's topology. The hosted night runs
  alone on a CI runner (`scripts/nightly_hosted.sh`), the Mac runs no engine, and a cycle without a `release-*`
  stamp never republishes. But it is a load-bearing guard removed on a HIGH path (REQ-REF-001: never leaves the
  live artifact worse than it found it), so it blocks. **Remedy (the author's, through `/fix-issue`; D-225 clause 2
  is amended by a new ADR or a superseding one):** on `same`, keep the re-read. The smallest form computes the
  re-read on both paths and skips only the change guards. F47, which computes the whole refusal on `same`, also
  turns `:150` green with all 334 tests green, but it would also refuse a quiet night past a bound and count it as
  a refusal.

### Delta MINOR (hotfix-1026)
- **M5** `docs/prd.md:446` -- REQ-REF-002 still reads "An unchanged upstream produces no publish and says so". D-225
  now publishes a release's first unchanged night (its record says `published`, with the D-225 reason). D-225
  amends #198's record rule but not this criterion. Changing what a criterion means is the owner's call, so the
  author should raise it with the owner or amend the statement under an ADR.
- **M6** `src/app/workflows/refresh.py:1049-1051` (outside the range, from before it) -- `write_status` reads the
  previous record and calls `.get` on it without checking it is an object. A record that is valid JSON but not an
  object (`[]`) crashes every cycle with `AttributeError`, and the crash leaves the record unrewritten, so the
  cycle never recovers. Found when `[]` was tried as an unreadable record for D-225: `_another_release_built`'s
  `not isinstance(previous, dict)` branch (`:1017`) leads only into this crash. The author files it.

### Delta test integrity (hotfix-1026)
`git diff 0222150..6411610 -- tests/ conformance/`: two files added (`test_app_version.py`, `test_release_restamp.py`)
and one test deleted, `test_engine_service.py::test_the_remover_takes_off_the_service_the_retired_installer_put_on`,
with the script it read (#461, D-224 clause 3). No invariant cites it (`git grep` is empty). No `skip` or `xfail` was
added, and no assertion was weakened.

### Delta suite result (hotfix-1026)
- At `6411610`: 4691 passed, 37 skipped, offline sandbox, artifact required, coverage 93.00%; `refresh.py` 96.47%
  (`:1015-1016`, the unreadable-record branch, uncovered), `main.py` 98%.
- With B5's red test in the tree: 4695 passed, 1 failed (B5's red test `:150`, as declared), 37 skipped; coverage 93.02%;
  `refresh.py` 96.68% (`:1015-1016` now covered), against 96.47% at `6411610` and 96.5% at the previous rounds'
  head, so the touched module's coverage is above its prior level.
- `20008c6` passed the commit-msg hook's `make check-fast` (lint, typecheck, test, swift-test, client-decls,
  records). B5's red test goes in a declared red commit (`test: ..., red`), whose gate is `check-red`: lint,
  typecheck, `pytest-collect` and records, no test run. A docs commit after it cannot pass `check-docs`, which runs
  the tests, so this verdict is committed first and names `20008c6`.

## B5 re-verify round 2026-10-26 (20008c6..9ef6448)

**Range:** `db17f9b..133d638` on `integration/hotfix-1026` (local): `72eef28` (D-226, amending D-225 clause 2),
`6cf0e51` (this review's red test for B5, recommitted unchanged by the coordinator after the ADR, because a docs
commit cannot pass with a red test in the tree), `133d638` (the fix). Plus this round's test commit `9ef6448`.
**Seat:** the same worktree `$TMPDIR/wt-tester-1026`; `review/tester-hotfix-1026` was moved to `133d638` (its own
`e64b901` is the same test as `6cf0e51`, so nothing was lost) and `9ef6448` is on top, so the branch fast-forwards
onto the integration branch. A detached worktree at `6cf0e51` ran the red half and was removed clean. Nothing was
pushed; no launchd, owner data directory, Fly or GitHub call was made.
**Fresh eyes:** I wrote none of `72eef28` or `133d638`. `6cf0e51`'s test and `9ef6448` are mine.

### The fix
`133d638` moves the re-read out of `_reason_to_refuse` into `_replaced_underneath(target, live)`
(`src/app/workflows/refresh.py:1285`); `_reason_to_refuse` ends by calling it (`:1282`), and `_cycle` calls it alone
on `same` (`:1668`). So a republish skips only the refusals that compare content, as D-226 clauses 1 and 2 say.

### Red to green
`tests/unit/test_release_restamp.py::test_a_republish_never_overwrites_an_artifact_replaced_mid_cycle` (`:150`):
at `6cf0e51` 1 failed, 10 passed; at `133d638` 11 passed.

### Fault injection
Same method as above (exact replacement, original bytes put back at the same offset, md5
`9bcbcce246010ec90dcacc1644f378d8` before and after each). Set: the eleven refresh, nightly, stamp and deploy test files
(339 tests at `133d638`).

| ID | Fault | At `133d638` | After `9ef6448` |
|---|---|---|---|
| F55 | the re-read dropped on `same` (`None if same ...`) | RED (`:150`) | RED |
| F56 | `_replaced_underneath` never refuses | RED (`:150`, `test_refresh.py:1300`) | RED |
| F57 | the full `_reason_to_refuse` on `same` (D-226 clause 1 reverted) | GREEN (339 passed) | RED (`:173`) |

F57 stayed green: nothing held D-226 clause 1, the decision that a quiet night past a serving bound is not counted
as a refusal. `tests/unit/test_release_restamp.py:173` (`9ef6448`) now holds it. It sets
`MODEL_RANKING_MAX_RANKED_ROWS=1`, asserts the republish publishes with `consecutive_refusals == 0`, and asserts a
night whose content moved is refused "past a bound", so the bound is shown to bite. It is a test gap with the code
correct, so it is closed here rather than raised as a finding.

### MINOR status
- **M5** answered by D-226 clause 3 (`docs/decisions.md`, the D-226 entry): REQ-REF-002 still governs what a user
  sees, and the owner asked on 2026-10-26 for a restamp on unchanged nights. D-226 is `proposed`. The criterion's
  wording at `docs/prd.md:446` is unchanged, which the ADR accepts.
- **M6** filed as #466; **M3**, **M4** as #456, #457. **M1**, **M2** unchanged.

### Suite result
- At `9ef6448`: 4697 passed, 37 skipped, offline sandbox, artifact required; coverage 93.02%; `refresh.py` 96.69%
  (96.68% at the previous round's head), so the touched module's coverage did not fall.
- `9ef6448` passed the commit-msg hook's `make check-fast`. `ruff check` on the changed test is clean.
- **Mutation kill-rate (advisory):** F55-F57: 2 killed on the fix's tests, 1 survived (F57), killed after `9ef6448`.

## Delta round 2026-10-27 (9ef6448..f32cdbf)

**Range:** `9ef64482ae331c65491ef2675289b22caa5db0da..f32cdbffdfc8ef2de4081a4e75350378d149ab09`, main's tip and the tip
of `release/v0.2.0`, plus this round's test commit `50c4764`. Code: `.claude/hooks/bash_guard.py`,
`tests/unit/test_bash_guard_bounds.py` (#470, `b9b7c1b`, the owner's patch, D-224, #284), `.claude/settings.json`
(the re-pin), `ios/ModelRanking.xcodeproj/project.pbxproj` (#469, `b72de72`, build 6). The rest is records and
`build/`.
**Risk tier:** HIGH for the guard (a safety control loses rules); LOW for the build number.
**Seat:** my own worktree `$TMPDIR/release-tester-1027` on `review/release-tester-1027`, cut from `f32cdbf`, with its
own `.venv` (`make install`; `app` resolves to this tree's `src`) and a read-only copy of the main clone's
`advisor.db`. The fault ran in memory (a pytest plugin in the scratchpad recompiled `_judge_shell`), so the guard file
was never written: md5 `8adfc7f1ce14533472a70f69855030de` before and after. Nothing was pushed; no launchd, Fly or
GitHub call was made.
**Fresh eyes:** I wrote none of `b72de72`, `b9b7c1b` or the re-pin. My only code in the range is `50c4764`.

### Per change
- **The retirement removes only launchd rules.** `git diff 9ef6448..f32cdbf -- .claude/hooks/bash_guard.py` takes out
  the two docstring bullets (#284), `LAUNCHD`, `LAUNCHD_REMOVE`, `LAUNCHD_READ_ONLY`, `LAUNCHD_SCRIPT`, the two names
  from `GUARDED` (`bash_guard.py:414`) and the one branch in `judge_words` (was `:1763-1766`); the `DEPLOY` branch
  above it (`:1745`) is untouched. No removed name is left in the guard, `conformance/`, `permission-matrix.md` or
  `INSTALL.md` (`grep -n -i -e 284 -e launchd -e engine_service`: nothing). Neither script is in `scripts/`; the only
  code-tree mentions left are `.path-refs-allow:153` (a written reason), `scripts/README.md:47` (prose) and
  `tests/unit/test_testflight_ready.py:91`, an absence assertion. The rule's retirement is recorded in
  `docs/watchlist.md:53` with its trigger (a launchd service again), as D-224 clause 1 asks.
- **The guard still refuses what it must.** `tests/unit/test_bash_guard_bounds.py`: 684 passed at `f32cdbf`, 686 at
  `50c4764`. `conformance/test-bash-guard.py`: PASS, 591 tool calls fed as Claude Code feeds them, 0 wrong verdicts,
  exit 0. The deploy script's rule keeps its refusals (`:125-139`) and its case rule (`:754-760`).
- **The pin matches the guard.** `python3 .claude/hooks/guard_pin.py --check` (read-only): `guard-pin PASS ... sha256
  36cf17e8484a`, exit 0; `shasum -a 256 .claude/hooks/bash_guard.py` is `36cf17e8...0961`, and it is the only hash
  in `.claude/settings.json`, twice (the Write/Edit hook `:79`, the Bash hook `:90`). The diff changes only those two
  hashes and their 12-character echoes.
- **Build 6 is only the build number.** The pbxproj diff is four lines, `CURRENT_PROJECT_VERSION = 5;` to `6;`, one per
  build configuration; all four now read `6`, `MARKETING_VERSION` stays `0.2.0`. No test reads the build number; the
  owner's TestFlight upload is what refuses a reused one.

### Test integrity
`git diff 9ef6448..f32cdbf -- tests/ conformance/` is one file, `test_bash_guard_bounds.py`, +3/-36. The deleted
cases are the two launchd tests (20 refused, 7 allowed), the mixed-case launchd names in the case test (whose
deploy-script cases stay, one added), and `bash scripts/remove_engine_service.sh --help` in the P1 test
(`:739`). Each goes with the rule it tested, by D-224 and the owner's patch, so none is deleted to force green. One
was collateral: the P1 case was the only one where a shell runs a guarded SCRIPT FILE, not a `-c` string, with
`--help` after it. **F58**: `_judge_shell`'s P1 check turned from `all` to `any` (`bash_guard.py:2752`), in memory:
RED on the six `-c` cases left, so P1 is still held, but the script-file shape had no case. `50c4764` adds
`bash scripts/deploy_hosted_engine.sh --help` and `sh scripts/deploy_hosted_engine.sh --version`
(`tests/unit/test_bash_guard_bounds.py:735-737`): GREEN on the guard, RED under F58 (8 failed, the two new among
them). A test gap with the code correct, so it is closed here rather than raised as a finding.

### Delta BLOCKING
None.

### Delta MINOR
None new. M1, M2, M3 (#456), M4 (#457) and M6 (#466) are unchanged by this range.

### Delta suite result
- `make test` in this seat at `50c4764`: 4670 passed, 37 skipped, offline sandbox, artifact required; coverage
  93.02%, as at `9ef6448`; coverage-floor PASS (54 modules), skip budget 96 of 96. 4697 at `9ef6448`, less the 29
  launchd cases #470 removed, plus the two `50c4764` adds.
- `50c4764` passed the commit-msg hook's `make check-fast` (lint, typecheck, records with conformance, swift-test,
  client-decls, test). `ruff check` on the changed test is clean.
- **Mutation kill-rate (advisory):** no runner is wired. F58: killed on the range's own tests (the `-c` cases); the
  script-file shape it exposed is held after `50c4764`.

## Night-1027 delta round 2026-10-27 (50c4764..ac7bba9)

**Range:** `50c4764bd94ffaa21201eaffaa6892f65c07e811..ac7bba9`, the head of `integration/night-1027`, plus this
round's test commit `07a7fc6`. Three PRs merged into the lane: #474 (`fix/issue-467-republish-bound`, D-227: red
`397c1c9`, ADR `975b186`, fix `6c40bcc`), #473 (`chore/guard-version-tags`: `docs/owner-actions.md` and the process
log only; the guard patch under `build/` is not in git and is out of scope) and #476 (`fix/issue-475-t2i-respelling`,
D-228: red `2401eaa`, ADR `838d8b0`, fix `534bc09`). Code: `src/app/workflows/refresh.py`,
`data/accepted-cuts.yaml`; tests: `tests/unit/test_accepted_respellings.py` (new), `test_release_restamp.py`,
`test_accepted_cuts.py`.
**Risk tier:** HIGH. Both fixes move the refresh's publish guards (the serving bounds on a republish; the board and
novelty guards under an accepted re-spelling) on the night the hosted engine deploys.
**Seat:** my own worktree `$TMPDIR/tmp.ZohPZL5Yky/rt` on `review/release-tester-1027b`, cut from `ac7bba9`, with its
own `.venv` (`make install`; `app` resolves to this tree's `src`) and a copy of the main clone's `advisor.db`. A
second detached worktree (`.../rg`) ran the red-to-green pairs with this seat's venv and `PYTHONPATH` on its own
`src`. No launchd service, owner data directory, Fly or GitHub write was touched; nothing was pushed.
**Fresh eyes:** I wrote none of the range. My only code is `07a7fc6`.
**Cross-model routing:** author family Claude / reviewer family Claude; no second family was available in this seat.

### Acceptance-criterion coverage
D-227 (#467):
- Clause 1 (a republish runs `egress_problems` with the running code's bounds, `refresh.py:1408`, called at `:1790`)
  and clause 2 (past a bound: nothing published, `EXIT_UNCHANGED`, the bound named, no refusal counted) ->
  `tests/unit/test_release_restamp.py:173`. It sets `MODEL_RANKING_MAX_RANKED_ROWS=1` under a new release and asserts
  `EXIT_UNCHANGED`, "past a bound" in the reason, the served bytes unchanged, `served_built_by` still the old release
  and `consecutive_refusals == 0`; a night whose content moved is still refused at the bound. GREEN. Red under F67.
- Clause 3 (the other content refusals stay skipped; the re-read stays) -> `test_release_restamp.py:150` (the re-read,
  B5) and `:93,112,126` (the republish publishes on unchanged content). GREEN. F77 (below) is equivalent since D-227.

D-228 (#475):
- Clause 1, the schema -> `tests/unit/test_accepted_respellings.py:148` (17 shapes: no or past or too-far `until:`,
  an unknown ADR, an unknown board, blank names, a self-map, two onto one, a chain, pairs not a map or empty, an extra
  key, a board twice, `respellings` a map, an unknown top key, no `cuts`), `:153` (the ADR must name the board),
  `:116` (a surface and a declared board both parse), `:122` (the cuts parser reads the shared file), `:202` (a
  malformed list fails the night through `refresh()`). GREEN. Red under F65, F71, F72, F75, F76.
- Clause 2, a pair judged as the row it was only when it is a re-spelling, on its board alone, a surface's ranked
  models too -> `:56` (the control: 4 of 12 re-derived, all three guards fire), `:64` (accepted: no reason), `:69`
  (one board's pairs excuse nothing on the other), `:74` (an unlisted re-derivation still counts), `:87`, `:95` (two
  old models arriving as one excuse neither), and, after `07a7fc6`, `:268` (each shape that is not a re-spelling
  leaves the candidate unchanged) and `:276` (every row reads as the row it was). GREEN. Red under F59-F64, F69, F73,
  F74.
- Clause 3, the published candidate and its digest unchanged; the record names each pair -> `:52` (every judged
  summary keeps the candidate's digest), `:276`, and `:191-198` through `refresh()`: published, `renamed` holds
  "Probe 00 -> PROBE.00 on board ... and 1 more", `largest_board_change` is None. GREEN. Red under F66, F68, F70.
- Clause 4, the first entry -> `:208` parses the committed file. That it names exactly #475's 27 pairs is data, not
  behaviour; I checked it by hand instead: all 27 old names are on the served side's recorded board
  (`tests/fixtures/arena_media/text_to_image.json`, LMArena's 2026-10-07 snapshot, 82 rows), none of the 27 new
  names is, and `registry.derive_identity(..., media=True)` derives a different id for each of the 27 pairs. The new
  side (LMArena's 2026-10-26 names) needs the network and was not checked here.

### Red to green
- #467: `test_release_restamp.py:173` RED at `397c1c9` ("unchanged content, republished as this release's own build
  (D-225)", `:185`), 12 of 12 GREEN at `6c40bcc`.
- #475: `test_accepted_respellings.py` 30 of 30 RED at `2401eaa`, 30 of 30 GREEN at `534bc09`. At the red commit the
  tests fail on the missing `respelled` and loader, not on the guard; the symptom itself (three guards refusing a
  re-derived board) is held by the control `:56`, GREEN at the fix.

### Fault injection
Each fault an exact replacement in `refresh.py`, the original bytes put back at the same offset, md5
`2fe61a43115002ff6f55342c37f18b62` before and after each. Set: the eighteen refresh, cut, re-spelling, restamp and
board test files (561 tests at `ac7bba9`, 567 at `07a7fc6`).

One revert went wrong and was repaired before any other step: F75's replacement text also matched the cuts parser's
`known =` line, so the first harness's `replace(new, old, 1)` put the original back on the wrong line. md5 read
`168d1aa2...`; `git diff` showed the two `known =` lines swapped; I swapped them back in place, by offset, and md5
read `2fe61a43...` again with a clean `git status`. The harness then reverted by offset, and F75-F78 were re-run.

| ID | Fault | At `ac7bba9` | After `07a7fc6` |
|---|---|---|---|
| F59 | `_respelled_ids`' one-to-one rule dropped | RED (`:95`) | RED |
| F60 | `now[new] not in before` dropped | GREEN | RED (`:268[onto-a-kept-model]`) |
| F61 | `was[old] not in after` dropped | GREEN | RED (`:268[the-old-model-stayed]`) |
| F62 | `old not in now` dropped | GREEN | RED (`:268[the-old-name-stayed]`) |
| F63 | `new not in was` dropped | GREEN | RED (`:268[the-new-name-was-served]`) |
| F64 | every pair applied to every board, not the board named | RED (`:69`) | RED |
| F65 | `_check_terms` skipped for a re-spelling (`until:`, ADR, reason) | RED (`:148` x4, `:153`, `:202`) | RED |
| F66 | `respelled` changes the digest | RED (`:64,69,74`) | RED |
| F67 | `_why_unchanged`'s `egress_problems` removed | RED (`test_release_restamp.py:173`) | RED |
| F68 | `respelled` not applied in `_cycle` (the loader still read) | RED (`:191`) | RED |
| F69 | a surface's ranked models not moved | RED (`:64,69,191`) | RED |
| F70 | the spellings not moved | RED (`:191`) | RED |
| F71 | a board named twice accepted | RED (`:148[a-board-twice]`) | RED |
| F72 | the two-onto-one and chain checks dropped | RED (`:148` x2) | RED |
| F73 | `_moved_rows` drops the unlinked rows | GREEN | RED (`:276`) |
| F74 | `_moved_rows` collapses a model's copies | GREEN | RED (`:276`) |
| F75 | surfaces dropped from a re-spelling's known boards | RED (92 tests) | RED |
| F76 | the `respellings` list never read | RED (18 tests) | RED |
| F77 | the full `_reason_to_refuse` on `same` (D-226 clause 1 reverted) | GREEN | GREEN (equivalent) |
| F78 | the cuts parser stops calling `_check_terms` (the refactor) | RED (14 tests) | RED |

F60-F63, F73 and F74 stayed green: each condition D-228 clause 2 names was held only through a guard's verdict, and
"onto a kept model" only through the one-to-one rule beside it. The code is correct; the tests had gaps, so `07a7fc6`
closes them rather than raising findings. F77 is equivalent since D-227: the bound check that killed it as F57 now
runs in `_why_unchanged` before the refusal, and on `same` the digest covers every count, row and price the
remaining content refusals compare.

### Test integrity
`git diff 50c4764..ac7bba9 -- tests/` deletes no test. `test_release_restamp.py:173` is flipped from D-226 clause 1's
"publishes, no refusal" to D-227's "unchanged, no refusal", as D-227 clause 2 rules, and keeps its moved-night bound
assertion. `test_accepted_cuts.py:177` adds one line: the cut fixture also points the re-spelling loader at its file.

### Night-1027 delta BLOCKING
None.

### Night-1027 delta MINOR
- **M7** `data/accepted-cuts.yaml:21` (`until: 2026-11-10`), read by `src/app/workflows/refresh.py:1784` through
  `load_accepted_respellings()`'s default path -- from 2026-11-11 the committed entry fails `_check_terms`
  (`refresh.py:356-359`; `parse_accepted_respellings(raw, today=2026-11-11)` raises "text_to_image's cut has no
  `until:` date, or it is past"). For the hosted night that is D-228's design: the refresh fails until the entry goes.
  But nothing tracks retiring it after the first published night (no owner-actions row, watchlist entry or issue),
  and the suite reads the same committed file against today's date: F75, which raises the same `AcceptedCutError`,
  turned 92 tests red in the refresh set alone (`test_floor_served.py`, `test_refresh*.py` and the rest, every test
  that reaches `refresh()` with the default loader path). So on 2026-11-11 `make test` and CI go red on every branch,
  whatever it changes. Remedy: an issue or owner-actions row to remove the entry once a hosted night has published
  the new names (D-228 clause 4 says it is inert from then), and point the suite's default loader paths at a fixture
  (a conftest fixture, as `_cuts_on_disk` does) so no test depends on the committed file's dates except
  `test_the_committed_file_parses`. Fix before 2026-11-10; not a deploy blocker.
- M1, M2, M3 (#456), M4 (#457) and M6 (#466) are unchanged by this range.

### Night-1027 delta suite result
- `make test` in this seat at `ac7bba9`: 4700 passed, 37 skipped, offline sandbox, artifact required; coverage
  93.10%; `refresh.py` 97% (96.69% at `9ef6448`), so the touched module's coverage did not fall. coverage-floor PASS
  (54 modules), skip budget 96 of 96.
- `07a7fc6` passed the commit-msg hook's `make check-fast` (lint, typecheck, records with conformance, swift-test,
  client-decls, test: 4706 passed, 37 skipped, coverage 93.10%). `ruff check` on the changed test is clean.
- **Mutation kill-rate (advisory):** no runner is wired. F59-F78: 13 of 20 killed on the range's own tests, 6
  survived and 1 equivalent; 19 of 20 killed after `07a7fc6`, the equivalent F77 left.

## Night-1028 delta round 2026-10-29 (07a7fc6..e00c516)

**Range:** `07a7fc6e51df76f9eb8fd238a26f9d3fd0bc2a39..e00c516df11f75791cfab5ba27035650604c3e12`, the tip of
`integration/run-night-1028` (draft PR #483; record `docs/plans/run-night-1028.md`, rulings D-229). 25 code files,
+827/-100. Nine draft PRs stacked: #485 (#481: red `68f75b5`, fix `7a7508f`), #490 (#477, #478, #479: red `2911dda`,
fix `a78eb15`, its security round's MINORs `a56cf3d`), #487 (#466: red `7db7758`, fix `3486f82`), #489 (#453: red
`0eb5e12`, fix `59d12b7`), #486 (#463: `dcc3b24`, `38d9eab`, test only), #491 (#456, #457: `6df974d`, test only),
#492 (#452: `6e1512e`, test only), #495 (#444: red `6e7bdb9`, fix `fba96ba`), and build 7 (`4280613`).
**Risk tier:** HIGH. The range moves the deploy gate's exemption (#444), the refresh's build child and its clocks
(#453), and the policy file's parser and the re-spelling guard (#477-#479).
**Seat:** my own worktree `$TMPDIR/wt-tester-1028` on `review/release-tester-1028`, at `e00c516`, with its own
`.venv` (`make install`; `app` resolves to this tree's `src`) and no `advisor.db`, so nothing here is committed: this
verdict and the tests below are working-tree changes for the run's session to commit. A second detached worktree
(`$TMPDIR/wt-tester-1028-rg`, removed after) ran the red-to-green pairs with this seat's venv and `PYTHONPATH` on its
own `src`. Targeted test files only (the machine's load average was 27-90). No launchd service, owner data
directory, simulator, Fly or GitHub write was touched; nothing was pushed.
**Fresh eyes:** I wrote none of the range. My only code is the tests listed under "Tests added this review".
**Cross-model routing:** author family Claude / reviewer family Claude; no second family was available in this seat.
Fresh context: the diff, the issues with their comments, D-229 and the tests, not the implementers' sessions.

### Acceptance-criterion coverage
- **#481** (D-229 clause 1), the issue's done-when as triaged: each degraded state has its own guide in both
  languages, no empty and no shared sentence, `.available` none -> `ios/EngineTests/FrontDoorTests.swift:893`
  (no guide when available), `:898` (every degraded state: a title, steps, none blank, the "still answers" line;
  titles differ across states and languages; step lists differ as wholes), `:923` (added here: no Turkish sentence is
  an English one), `:936` (`.turnedOff` names "Apple Intelligence & Siri" / "Apple Intelligence ve Siri" and is a
  Settings remedy), `:946` (`.notEligible` is not), `:952` (the caption has a guide exactly when not available),
  `:959` (both button labels). GREEN (7 of 7). The Settings button is not drawn: D-126's client-decls control refuses
  the URL, the run's assumption, filed as #484; "on the device" is the owner's check. The screen wiring is M9.
- **#477** (1) the D-228 entry retired -> `tests/unit/test_accepted_respellings.py:337` (the committed file holds no
  re-spelling) and `test_accepted_cuts.py:85`; (2) the suite reads no committed policy -> `:343` (the loaders' defaults
  are the fixture's and read nothing) and, added here, `:352` (without the fixture both default to the committed file).
  GREEN. F108 is the probe of the symptom itself: an expired `until: 2026-10-01` entry put back in the committed file
  turns only the two tests that name it red (`:208`, `:337`); 271 refresh, restamp, carry, floor and cut tests stay
  green, where the night-1027 round saw 92 go red. That the hosted nights of 2026-10-27 and 2026-10-28 published the
  new names is a claim about served data, not checked offline here.
- **#478** a pair names rows, not models -> `:263` (an old model's second name the pairs do not list), `:270` (a
  listed sibling pair that is not itself a re-spelling), `:278` (added here: the new model's name no pair lists),
  `:310` (the control: both names listed, the model reads as it was). GREEN. Red under F97-F100.
- **#479** repeated keys and merge keys refused, `board:` that is not a name -> `:328` (a second `cuts`, a second
  `pairs` key; both parsers), `:361` (a merge key), `:371` (40,000 keys walked under 2 s), `:387` (a list or mapping
  as `board:`, cut and re-spelling). GREEN. Red under F89-F95.
- **#466** a non-object record reads as none -> `tests/unit/test_refresh_carry.py:529` (`[]`, `"x"`, `3`, `null`: the
  cycle's record is written). GREEN. Red under F79.
- **#453** M1 `-P` -> `tests/unit/test_refresh_build_child.py:154`; M2 bounded by the cycle -> `:171` (a stood-in
  deadline) and, added here, `:182` (the alarm `_Limits` sets is the deadline the child reads, and a closed cycle
  leaves none); M2 the fetch budget -> `:211` (handed down as `--fetch-seconds`) and `:233` (the build's
  `cycle_ends()` is set from it); R2 -> `:256` (`nan`, `inf` read as no time). GREEN. R1 (`NSAllowsLocalNetworking`)
  is not in this range's diff and has no test; the issue names it as a recommendation.
- **#463** linear whatever the load -> `tests/unit/test_arena_respelling.py:79`, a ratio between 5k and 20k spaces
  with a 0.5 s floor. GREEN here at load averages 27-90; the #417 regression still goes red (F101, F102). See M8.
- **#452** M1 -> `tests/unit/test_terminalbench_4.py:209` (deep nesting, a 5,000-digit integer, garbage: each a
  `SourceError`, never a `RecursionError`); M2 -> `tests/unit/test_simplebench.py:167` and
  `tests/unit/test_osworld.py:375`, ratios with floors of 1.0 s and 3.0 s. GREEN. Red under F103-F105; OSWorld's fault
  proof is the known timeout, not re-run.
- **#456** a missing installed workflow fails -> `tests/unit/test_nightly_hosted.py:483,489`. GREEN. F119, the
  installed path pointed at a missing file without touching `.github/` (agents never write there): RED, "is missing:
  the hosted engine's nightly refresh and deploy are off"; the pre-#456 body under the same fault: GREEN, the
  reported F41.
- **#457** a self-proof sample with a nested `name:` -> `conformance/test-ci-yaml.py:262,298`, run by the fallback
  parser itself whether PyYAML is installed or not. PASS. F118 (the fix at `:88` reverted): FAIL, "read the steps of a
  sample with `name:` nested under `with:` as ['hosted-state', 'after']".
- **#444** M2 symlink -> `tests/unit/test_deploy_gate_444.py:30`; M3 derived surface -> `:69` (a declared script, a
  dispatched workflow, a workflow running a deploy, and, added here, a dispatched workflow not in lower case) with its
  control `:80`; R2 forged blob -> `:88`; M1 the pin routed to security -> `:105` (light mode) and `:115` (derived from
  the gate's own constant). GREEN. Red under F111-F114, F116, F117. Known and filed, not re-raised: the commit and tree
  checks of `verified_blob` and `deploy_surface`'s fail-closed branch are untested (#494 M2-M3); a forged loose tree
  at the reviewed head (#493). A probe here confirmed #494 M1's mixed-case case: a declared `scripts/Ship_It.sh`
  shipped by an upgrade passes the gate (`declared()` lower-cases it); not live, the brief's four commands are lower
  case.
- **Build 7** (D-229 clause 2) -> `ios/ModelRanking.xcodeproj/project.pbxproj:239,260,280,296`, all four
  configurations `CURRENT_PROJECT_VERSION = 7`, `MARKETING_VERSION` unchanged. A record, no test.

### Red to green
- #481: `OnDeviceGuideTests` 6 tests with 14 failures at `68f75b5`; 6 of 6 GREEN at `7a7508f`.
- #477-#479: `test_accepted_respellings.py` + `test_accepted_cuts.py` 5 RED at `2911dda` (the unlisted name, both
  repeated-key shapes, the committed entry, the committed-policy default); 100 of 100 GREEN at `a78eb15`.
  `a56cf3d`'s tests on `a78eb15`'s code: 5 RED (the sibling pair, the merge key, the quadratic walk, both
  non-name boards); 47 of 47 GREEN at `a56cf3d`.
- #466: 4 of 4 RED at `7db7758`, GREEN at `3486f82`.
- #453: 5 RED at `0eb5e12` (`-P`, the deadline, the budget handed down, the build's side, finite times); 14 of 14
  GREEN at `59d12b7`.
- #444: 7 RED at `6e7bdb9`, 1 GREEN (the control); 8 of 8 GREEN at `fba96ba`.
- #463, #452, #456, #457 change tests only; each symptom is a fault that stayed green or a flaky bound, so their proof
  is the fault table (F101-F105, F118, F119).

### Fault injection
Each fault an exact single-occurrence replacement, run, the original bytes written back, md5 compared and
`git status` clean after each: `refresh.py` `5d6e5531360a014ae12f9ca7b41f568b`, `yaml_guard.py` `0b4b9eba...`,
`build.py` `3a1b05aa...`, `registry.py` `fca8e67c...`, `simplebench.py` `d0289da8...`, `terminalbench.py`
`12cf0448...`, `tests/conftest.py` `4db614f0...`, `data/accepted-cuts.yaml` `9df42ef5...`, `scripts/deploy_gate.py`
`fadc4291...`, `scripts/review_need.py` `9a54dbb5...`, `conformance/test-ci-yaml.py` `d7161657...`,
`FrontDoor.swift` `aec0978b...`. Every restore matched. F119 changes no file.

| ID | Fault | On the range's tests | After this round |
|---|---|---|---|
| F79 | `write_status` keeps a non-object record | RED (`test_refresh_carry.py:529` x4) | RED |
| F80 | the build child without `-P` | RED (`:154`) | RED |
| F81 | the cycle's deadline not applied to the child | RED (`:171`) | RED |
| F82 | the two-minute margin dropped | RED (`:171`) | RED |
| F83 | `_Limits` never sets the deadline | GREEN (all of `tests/unit`, 4677) | RED (`:182`) |
| F84 | `_Limits.close` leaves the deadline set | GREEN | RED (`:182`) |
| F85 | `--fetch-seconds` not passed | RED (`:211`) | RED |
| F86 | `max(0.0, ...)` dropped | GREEN | GREEN (equivalent: a spent budget refuses every fetch either way) |
| F87 | the build ignores `--fetch-seconds` | RED (`:233`) | RED |
| F88 | non-finite progress times read | RED (`:256`) | RED |
| F89 | `unique_keys=True` dropped from the policy reader | RED (`:328` x2, `:361`) | RED |
| F90 | the merge-key refusal dropped | RED (`:361`) | RED |
| F91 | a key counted twice allowed | RED (`:328` x2) | RED |
| F92 | the walk skips sequences | RED (`:328`, `:361`) | RED |
| F93 | the walk skips a mapping's values | RED (`:328`, `:361`) | RED |
| F94 | a cut's `board:` type check dropped | RED (`:387` x2) | RED |
| F95 | a re-spelling's `board:` type check dropped | RED (`:387` x2) | RED |
| F96 | the walk's seen-node check dropped | GREEN | GREEN (equivalent: revisits are bounded by the expansion limit) |
| F97 | old model's names need not all be listed | RED (`:263`) | RED |
| F98 | sibling pairs need not be re-spellings | RED (`:270`) | RED |
| F99 | the new model's names need not be exactly the listed ones | GREEN | RED (`:278`) |
| F100 | all three #478 conditions dropped | RED (`:263`, `:270`) | RED |
| F101 | #417 `_TEXT_BRACKET` lookbehind dropped | RED (`test_arena_respelling.py:79`, 1.03 s at 20k) | RED |
| F102 | #417 `_PAREN_EFFORT` lookbehind dropped | RED (`:79` x2, 1.54 s) | RED |
| F103 | #412 simplebench `\n\s*\];` restored | RED (`test_simplebench.py:167`, 86 s) | RED |
| F104 | terminalbench catches `ValueError` only | RED (`test_terminalbench_4.py:209`, nested) | RED |
| F105 | terminalbench catches `RecursionError` only | RED (`:209`, digits, garbage) | RED |
| F106 | the conftest fixture not autouse | RED (`:343`) | RED |
| F107 | the D-228 entry put back | RED (`:337`) | RED |
| F108 | the entry put back, expired (`until: 2026-10-01`) | RED (`:208`, `:337` only; 271 others green) | RED |
| F109 | `load_accepted_cuts`' default points elsewhere | GREEN | RED (`:352`) |
| F110 | `load_accepted_respellings`' default points elsewhere | GREEN | RED (`:352`) |
| F111 | the symlink refusal dropped | RED (`test_deploy_gate_444.py:30`) | RED |
| F112 | `rel in surface` dropped | RED (`:69` x3) | RED |
| F113 | declared scripts left off the surface | RED (`:69`, script) | RED |
| F114 | the on-disk workflow names left off the surface | GREEN | RED (`:69`, not in lower case) |
| F115 | the lower-cased workflow names left off the surface | GREEN | GREEN (equivalent: the on-disk names cover every file that exists) |
| F116 | `_object` does not hash the bytes | RED (`:88`) | RED |
| F117 | the pin left out of `EXCEPTION_FILES` | RED (`:105`, `:115`) | RED |
| F118 | #457's fallback-parser fix reverted | FAIL (`conformance/test-ci-yaml.py:298`) | FAIL |
| F119 | the installed nightly workflow missing (simulated) | RED (`test_nightly_hosted.py:483`) | RED |
| F120 | `hasGuide` always true | RED (`FrontDoorTests.swift:952`) | RED |
| F121 | `.turnedOff` not a Settings remedy | RED (`:936`) | RED |
| F122 | `.notEligible` sent to Settings | RED (`:946`) | RED |
| F123 | the Turkish "still answers" line in English | GREEN | RED (`:923`) |
| F124 | one Turkish `.turnedOff` step in English | GREEN | RED (`:923`) |

F83, F84, F99, F109, F110, F114, F123 and F124 stayed green; the code is correct in each, the tests had the gap, and
this round's tests close all eight rather than raising findings. F109/F110 is a gap #477's fixture opened: before it,
`test_accepted_cuts.py:88` called the loader with its default; now no test saw the default the hosted night reads.

### Test integrity
`git diff 07a7fc6..e00c516 -- tests ios/EngineTests conformance` deletes no test and adds no skip.
`test_accepted_cuts.py:88` now names the committed file (the fixture would otherwise answer); `:302` turns `==` into
`in` because `EXCEPTION_FILES` gained the pin, which `test_deploy_gate_444.py:115` holds; adding an entry there only
routes more to security. The three timing tests trade a wall-clock bound for a ratio with a floor (M8 on the arena
one). `test_nightly_hosted.py:483` drops its `if INSTALLED.exists()` guard, as #456 asks.

### Night-1028 delta BLOCKING
None.

### Night-1028 delta MINOR
- **M8** `tests/unit/test_arena_respelling.py:101` -- the #463 ratio `large < max(8 * small, 0.5)` floors at 0.5 s,
  and the regression it guards takes 1.03 s at 20k spaces here (F101, at a load average of 90; F102 1.54 s). A runner
  about twice as fast as this Mac passes the quadratic form through the floor, the narrow red margin M2 named. The
  simplebench and osworld floors leave 12x and 5x. Remedy: time 10k and 40k spaces, so the quadratic form takes about
  four times as long while the linear one stays far under the floor.
- **M9** `ios/ModelRanking/ContentView.swift:598-614,695-703,784-813` -- #481's screen wiring (the caption is a
  button exactly when `hasGuide`, the help line opens the guide, the sheet lists the steps) ran in no test here: the
  Engine tests hold `OnDeviceState`, and the UI tests are outside `check`. The existing
  `ios/UITests/ScreenPathTests.swift:199` `testTheQuestionSaysWhoReadsIt` matches `caption.label` exactly against the
  five caption sentences, and in every state but `.available` the caption is now a button whose label also holds an
  `info.circle` image. Not run here (the simulator is shared with another session). Remedy: run that UI test before
  the build 7 upload and, if the label changed, give the image `.accessibilityHidden(true)` or match the label's
  prefix; a UI test that taps the caption and finds the first step would hold the sheet.
- Closed in this range: M1 by `test_terminalbench_4.py:209` (#452), M2 by the three ratio tests (#452, #463; M8
  is what remains), M3 by `test_nightly_hosted.py:483,489` (#456), M4 by `conformance/test-ci-yaml.py:262` (#457), M6
  by `test_refresh_carry.py:529` (#466), M7 by `a78eb15` and the conftest fixture (#477).

### Night-1028 delta suite result
- Targeted, in this seat at `e00c516`: the twelve test files the range touches, 418 passed; with this round's tests,
  the changed files and their neighbours 316 passed, the Swift manifest and client-contract tests 84 passed, the three
  timing tests 4 passed serially; `conformance/test-ci-yaml.py` PASS; `swift test --filter OnDeviceGuideTests` 7 of 7,
  and `swift test --list-tests` matches `ios/EngineTests/test-manifest.txt`. `ruff check` on the three changed test
  files is clean. One full `tests/unit` run went with F83 in place: 4677 passed, 59 skipped. `make test` and
  `make check` were not run in this seat (the machine's load; no `advisor.db`): the commit hook's `make check-fast` is
  the run's session's.
- Coverage on touched code: every changed statement of `refresh.py` (23) and `build.py` (6) runs in the targeted
  set; of `yaml_guard.py`'s 21, all but `:164` (the seen-node `continue`, F96, equivalent). `scripts/deploy_gate.py`
  runs in a subprocess, which coverage does not see; its faults above stand in.
- **Mutation kill-rate (advisory):** no runner is wired. F79-F124: 35 of 46 killed on the range's own tests, 8
  survived and 3 equivalent; 43 of 46 killed after this round's tests, the equivalent F86, F96 and F115 left.

### Night-1028 re-check 2026-10-29 (e00c516..3cddbdd)
`git diff e00c516 3cddbdd -- ios tests src` is this round's tests, byte-identical to what this seat wrote, and the two
fixes below; the rest is this verdict and `docs/plans/run-night-1028.md`. Seat: a fresh worktree
`$TMPDIR/wt-tester-1028b`, detached at `3cddbdd`, with its own `.venv`; nothing committed, nothing pushed.
- **M8, fixed:** `tests/unit/test_arena_respelling.py:98` now times 10k and 40k spaces against the same
  `max(8 * small, 0.5)`. GREEN at `3cddbdd` (load average about 2). F101 (`_TEXT_BRACKET`'s lookbehind dropped): RED,
  "10k spaces: 0.2544 s, 40k: 3.9675 s"; F102 (`_PAREN_EFFORT`'s): RED on both shapes, 6.12 s and 6.21 s at 40k.
  The regression now runs about 8x past the floor, where it ran 2x; `registry.py` restored, md5
  `fca8e67c83941ae93928d07429017011` before and after, `git status` clean.
- **M9, fixed as far as this seat can run it:** `ios/ModelRanking/ContentView.swift:610` gives the caption's button
  `.accessibilityLabel(Text(UIText.onDeviceCaption(onDevice, language)))`, so its label is the caption's sentence
  again, the one `ios/UITests/ScreenPathTests.swift:199` matches, and not the sentence plus the `info.circle` image.
  `make client-decls`, which type-checks every file under `ios/ModelRanking` against the iOS SDK: PASS, 4
  configurations. The UI test was not run here (the simulators are booted by another session); running it before the
  build 7 upload stays the owner's.
- This round's tests at `3cddbdd`: the three Python files and the arena test, 196 passed; `swift test --filter
  OnDeviceGuideTests` 7 of 7.

## Delta round 2026-10-31 (3cddbdd..290557c)

**Range:** `3cddbddaa777f327b1a2bf0bb2ff7a35b9e196e9..290557c39d6e672877cf6399b9d21eab2403ffbf`, `main` after #514
(`integration/run-1030`), #513, #512 (`integration/fixes-1030`), #502, #499, #498 and #497. 30 code files, 49 files in
all, 67 commits. Issues closed in the range: #496, #494, #488, #493, #500, #484, #510, #506, #511, #509, #503, #501,
#505, and the owner's guard patch (#497 docs, #498 `f5b9395`). Rulings: D-230, D-231.
**Risk tier:** HIGH. Twelve of the range's issues change or test the deploy gate (`scripts/deploy_gate.py`,
`scripts/brief_fields.py`), two the client's egress controls (#484, D-230) and its transport exception (#488), one
the Bash guard (#498), one the refresh's status-record readers (#496).
**Seat:** my own worktree `tester-wt`, detached at `290557c`, with its own `.venv` (`make install`, editable to this
tree's `src`) and a copy of the main clone's `advisor.db`; `make check` and `make ui-test` ran there. A second
detached worktree `tester-rg` ran the red commits; a third, `tester-fi`, the fault injection, each with this seat's
venv and the tree's own `src` (`pythonpath`). All three under this session's scratchpad, removed after. A fresh
artifact for `make ui-test` was built into the scratchpad (`app.workflows.refresh --fetch-epoch`: 19 surfaces
answering, scores 14,666 rows). No launchd service, owner data directory, Fly or GitHub write was touched; the only
simulator used was `iPhone 17`, shut down when this round started; nothing was committed or pushed.
**Fresh eyes:** I wrote none of the range. My only code is the two test files under "Tests added this review", left
uncommitted for the run's session to apply.
**Cross-model routing:** author family Claude / reviewer family Claude; no second family was available in this seat.
Fresh context: the diff, the issues with their comments, D-230, D-231 and the tests, not the implementers' sessions.

### Acceptance-criterion coverage

- **#496** (one reader of the status record; a record nested past the recursion limit reads as none, for all four
  readers) -> `tests/unit/test_refresh_carry.py:547` drives `_read_last_ok`, `_another_release_built`,
  `nightly.read_record` and `write_status` over a 200,000-deep `.refresh.json`. RED at `2bba8cf`, GREEN at `290557c`;
  red under F1 (RecursionError dropped from `status_record.read_status`) and F49 (`nightly.read_record` reading the
  file itself). `src/app/workflows/status_record.py` 100% covered. Behaviour note: `read_record` now returns None for
  a record of `{}` where it returned `{}`; `built_by_another` then answers False instead of True, but the only caller
  that reads it (`src/app/adapter/nightly.py:374`) ORs it with `needs_catch_up`, which is True for both, so the
  catch-up is unchanged.
- **#494** M1 (every spelling of a declared command: `./x`, `bash ./x`, mixed case, absolute, a workflow by its stem
  and by its `name:`) -> `tests/unit/test_deploy_gate_494.py:37` (six cases); M1's fail-closed declarations (none,
  `make <target>`) -> `:48`; the control -> `:58`; M2 (a forged pinned tree) -> `:72`; M3 (an unreadable base
  workflow) -> `:117`; R2 (a link at the pin) -> `:132`; R1 (git cannot list) -> `:156`. RED at `ec5d662`: 9 of 12
  (the three green there are the control and the two test gaps M2 and M3, which tested code already in place). Red
  under F2-F5, F25, F30, F31, F36.
- **#493** (the reviewed head's commit and every tree under it hashed) -> `tests/unit/test_deploy_gate_493.py:26`
  (a forged subtree), `:78` (a forged reviewed commit, the review's B1), `:100` (two levels down), `:110` (a
  zero-padded `040000` tree), `:126` (fail closed with no index listing or no git). RED at `6846467`. Red under F6,
  F7, F10, F12, F14, F37.
- **#500** (the gate refuses an index entry flagged assume-unchanged or skip-worktree) ->
  `tests/unit/test_deploy_gate_493.py:49` end to end (RED at `6846467`) and `:143`, which is what holds the refusal
  itself: since #505 the comparison reads content, so the end-to-end case stays green without `_flagged` (F8), and
  only `:143` (`changed_since` returns None with the flag set) goes red. `closure_check` reads the same
  `changed_since` (`scripts/closure_check.py:86`).
- **#506** (a code file renamed into a record path is both its sides) -> `tests/unit/test_deploy_gate_506.py:18`
  (committed, uncommitted, intent-to-add) and `:35` (a rename-detection setting). RED at `aab6906`, 3 of 3. Since
  #505 the old side is a tree entry missing on disk (`_differs`), red under F15.
- **#509** (every base blob the gate trusts read through a verified path; one test per probe) ->
  `tests/unit/test_deploy_gate_509.py:31` (probe 1, the pin), `:43` (probe 2, the brief), `:55` (a forged base
  workflow), `:84` (a forged workflows tree), `:98` (a link beside the workflows). RED at `025e407`, 3 of 3. Red under
  F11, F13, F32, F36.
- **#510** (a forged pinned commit does not exempt a changed tool) -> `tests/unit/test_deploy_gate_494.py:96`. GREEN
  at `290557c`, but see "Fault injection" F12b: #510's mutant was in `_object`, which #511 removed; the analogue in
  the one verified reader (`scripts/brief_fields.py`, `batch_read`'s hash comparison for a commit) stays green there,
  because `_commit` peels the pinned commit and git refuses the forged object first. The test is red only with both
  gone (F12c). This review's `tests/unit/test_deploy_gate_510_tester.py:20` holds the reader's check alone (red under
  F12d).
- **#511** (one verified reader for `_unhashed`, `verified_blob` and #509's reads) ->
  `tests/unit/test_deploy_gate_511.py:25`, `:38` (both route through the shared reader and parser), `:45` (the
  control). RED at `d59244d`, 2 of 3 (the control green). `grep -n 'def _object\|20-byte' scripts/deploy_gate.py`:
  no second reader left.
- **#501** (a declared command is read only through the programs the gate knows; every listed spelling refuses, a
  control still exempts) -> `tests/unit/test_deploy_gate_501.py:41` (cd-then-relative, `$PWD`, `python -m`, a
  directory, `just`, `bash -c`, and the review's semicolon, assignment-first, workflow-id and known-program-expansion
  cases), `:50` (a dispatched workflow that runs `make` or `just`), `:63` (the controls: `fly deploy`, a script,
  `bash` with a script, `gh workflow run`). RED at `bde8f45`, 7 of 11 (the four controls green). Red under F23-F25,
  F27-F29. D-231 clause 1's named enumeration: `KNOWN_PROGRAMS = {"fly", "flyctl"}` (`scripts/deploy_gate.py:437`).
- **#505** (content, not git's state: fsmonitor, a stat-clean entry, an attributes filter, `info/exclude`,
  `core.excludesFile`, a self-ignoring `.gitignore`) -> `tests/unit/test_deploy_gate_505.py:25`, `:37`, `:51`, `:60`,
  `:68`, `:77`, one per bypass; the committed `.gitignore` still counts `:84`; the review's M1 to M3 and R1 to R3 at
  `:101`, `:110`, `:127`, `:150`, `:160`, `:173`, `:185`, `:195`, `:204`. RED at `5ce756f`, 6 of 7 (the control
  green). Red under F16, F18, F21, F22, F33, F34, F38. F19 (`--work-tree` dropped from the untracked listing)
  stayed green; this review's `tests/unit/test_deploy_gate_505_tester.py:20` closes it (below).
- **#484** (D-230: the guide shows "Open Settings" where the remedy is in Settings, through one door pinned by both
  client gates) -> `tests/unit/test_settings_door_484.py:27` (the sheet's button sits under `guide.opensSettings`, a
  source-text test), `:37`, `:46`, `:66` (the compiled gate grants the door only while its bytes hash to the pin),
  `:54` (the text gate's one exact expression), `:83` (each declaration seen on the shipping client);
  `ios/EngineTests/FrontDoorTests.swift:936` (which states open Settings, both languages). RED at `78c0ef0`, 4 of 4.
  Red under F40-F45. `make client-decls` PASS in `make check` (23 client files, 4 configurations). No run taps the
  button: M12.
- **#488** (Done when: the Release `.app`'s Info.plist has no `NSAllowsLocalNetworking`, the Debug one has it, and a
  Debug simulator build still reaches a local engine) -> `tests/unit/test_testflight_ready.py:166` (Info.plist
  preprocessed per configuration as Xcode does), `:183` (no local file can give Release the key). RED at `66a49f5`,
  2 of 3 (Debug-True green there, as it should be). Red under F46-F48. Beyond the test, the built bundles, read with
  `plutil -p`: a Release build for the simulator (`xcodebuild -configuration Release`, this seat's derived data) has
  `NSAppTransportSecurity => {}` and `EngineURL => https://model-ranking.fly.dev`; the Debug build `make ui-test`
  made has `NSAllowsLocalNetworking => true` and reached the engine on `127.0.0.1:8090` (19 of 19 ScreenPathTests).
- **#503** (`make ui-test` green on main) -> `make ui-test` against a fresh artifact, run 3 below: engine up 23 of 23,
  engine down 2 of 2, `ios/UITests/FailureScreenTests.swift:21,40` green. Run 1 on the same tree was red in the
  engine-down pass, both FailureScreenTests, #503's exact symptom: M10.
- **The guard patch** (#498, `f5b9395`: `v*` tags and replace refs are the owner's; reading tags and making other
  tags stay allowed) -> `tests/unit/test_bash_guard_bounds.py:1063` (27 refusals), `:1078` (23 allowed). The patch's
  test file run against the guard of `f5b9395~1`: 27 failed (every refusal), 23 passed (every allowed case). The
  pin: `.claude/settings.json` names sha256 `9d1faaf6bf7f`, the hash this session's own guard checks on every Bash
  call. #497 is a docs row (`docs/owner-actions.md`) with nothing to test.

### Red to green
Each "reproduce" commit, its new test file run against its own tree (the code before the fix), with this seat's
venv: `2bba8cf` 1 failed; `ec5d662` 9 failed, 3 passed; `66a49f5` 2 failed, 1 passed; `6846467` 3 failed, 1
passed; `78c0ef0` 4 failed; `aab6906` 3 failed; `d59244d` 2 failed, 1 passed; `025e407` 3 failed; `bde8f45` 7
failed, 4 passed; `5ce756f` 6 failed, 1 passed. Every green case at a red commit is a control or a test of code
already in place (named per issue above). All green at `290557c` (`make check`). #510 is test-only (its red is F12c);
#503 is red in run 1 and green in runs 2 and 3 below.

### Fault injection
Each fault injected in `tester-fi` at `290557c`, the deploy gate's eleven test files run (`-n 6 -x`), then the exact
string replaced back and the file's md5 compared with its pre-injection hash (`f34f0281ae13` for `deploy_gate.py`,
`f816b0a7e85f` for `brief_fields.py`; every revert matched, `git status` clean after). One revert by my harness's
first version replaced the wrong occurrence (F2: the injected text occurred earlier in the file); I repaired it by
exact replacement, the md5 matched the committed blob, and the harness then reverted by position.

| # | Fault | Result |
|---|---|---|
| F1 | `read_status` without RecursionError | RED `test_refresh_carry.py:547` |
| F2 | `_named_files` without `normpath` | RED `test_deploy_gate_494.py:58` |
| F3 | an empty declaration not failing closed | RED `:48[no-deploy-command]` |
| F4 | `_files` not lower-casing | RED `test_deploy_gate_444.py` (workflow not in lower case) |
| F5 | `_blob` accepting any mode | RED `test_deploy_gate_494.py:132` |
| F6 | `compare_problem` ignoring `_unhashed` | RED `test_deploy_gate_493.py:26` |
| F7 | `_unhashed` not walking below the root | RED `:26` |
| F8 | `_flagged` returning none | RED `:143` only (see #500) |
| F10 | `_subtrees` by spelling `40000` | RED `:110` |
| F11 | `devflow_pin` by `git show` | RED `test_deploy_gate_509.py:31` |
| F12 | `batch_read` skipping a commit's hash | RED `test_deploy_gate_493.py:78` |
| F12b | the same, #510's test alone | GREEN `test_deploy_gate_494.py:96` -- closed by this review's test |
| F12c | F12 and `_commit` without the peel | RED `:96` |
| F12d | F12 against this review's test | RED `test_deploy_gate_510_tester.py:20` |
| F13 | `batch_read` skipping a blob's hash | RED `test_deploy_gate_444.py` (forged pinned blob) |
| F14 | `batch_read` skipping a tree's hash | RED `test_deploy_gate_493.py:26` |
| F15 | `_differs`: a missing file is no change | RED `test_deploy_gate_444.py` (symlink) |
| F16 | `_differs` ignoring the executable bit | RED `test_deploy_gate_505.py:127` |
| F17 | `_differs`: a 120000 entry not required to be a link | GREEN, equivalent: `os.readlink` on a regular file raises, which `_differs` reads as a change |
| F18 | `_new_files` without the index's extra entries | RED (three cases) |
| F19 | `--work-tree` dropped from the untracked listing | GREEN -- closed by this review's test (F19b RED) |
| F19c | `--work-tree` dropped from the cached listing | GREEN, equivalent: staged paths are kept only when they exist under `root` |
| F20 | `_PLAIN_GIT` without `core.fsmonitor=false` and `core.untrackedCache=false` | GREEN, equivalent on git 2.54 (measured: with a quiet fsmonitor and the untracked cache on, `git status` hides a new file, `git ls-files --others` lists it) |
| F21 | a folder's glob characters not escaped | RED `test_deploy_gate_505.py:204` |
| F22 | a nested `.gitignore` not scoped to its folder | RED `:110` |
| F23 | a compound command read as one | RED `test_deploy_gate_501.py:41[semicolon]` |
| F24 | an assignment before the program | RED `:41[assignment-first]` |
| F25 | an unknown program read as known | RED `test_deploy_gate_494.py:48[make-target]` |
| F26 | `bash -<option>` not refused by its dash | GREEN, equivalent unless a tracked file is named like an option: the option names no file, which refuses |
| F27 | a path-like word naming no file | RED `test_deploy_gate_501.py:41[known-program-expansion]` |
| F28 | a dispatch by id | RED `:41[workflow-id]` |
| F29 | a dispatched workflow running `make` | RED `:50[make]` |
| F30 | an incomplete workflow read not failing closed | RED `test_deploy_gate_494.py:117` |
| F31 | a failed base workflow file ignored | RED `:117` |
| F32 | an unreadable base workflows folder ignored | RED `test_deploy_gate_509.py:84` |
| F33 | `changed_since` ignoring `compare_problem` | RED `test_deploy_gate_493.py:143` |
| F34 | `_redirected` never set | RED `test_deploy_gate_505.py:160` |
| F35 | a non-directory entry on the way not refused | GREEN; `batch_read`'s kind check refuses every such entry but a zero-padded `040000` directory, which then reads its own hashed content: stricter than needed, no safety effect |
| F36 | the brief at the base by `git show` | RED `test_deploy_gate_494.py:72` and the #509 brief probe |
| F37 | a commit naming no tree passed | RED `test_deploy_gate_493.py:78` |
| F38 | a link entry compared as a file | RED `test_deploy_gate_505.py:173` |
| F40 | the door's pin not checked | RED `test_settings_door_484.py:46` |
| F41 | the door's grant not tied to the pin | RED `:66` |
| F42 | the door's declarations not required to be seen | RED `:83` |
| F43 | a changed door not reported | RED `:66` |
| F44 | the button outside `opensSettings` | RED `:27` |
| F45 | a second address in the door | RED `:37` |
| F46 | Info.plist's exception unconditional | RED `test_testflight_ready.py:166[Release-False]` |
| F47 | Release defining `ENGINE_LOCAL_NETWORKING` | RED `:166[Release-False]` |
| F48 | Debug not defining it | RED `:166[Debug-True]` |
| F49 | `nightly.read_record` reading the file itself | RED `test_refresh_carry.py:547` |

**Mutation kill-rate (advisory):** no mutation runner is wired for this stack. Hand faults: 49 run (F9 was a
mistyped target and is not counted), 43 killed by the range's own tests, 6 green: F12b and F19 are closed by this
review's two tests; F17, F19c, F20 and F26 are equivalent as measured above; F35 is a strictness with no safety
effect. 45 of 49 killed after this review's tests.

### Interactions checked
- **The content comparison on a real tree.** With both verdicts' `**Reviewed head:**` set to `290557c` in
  `tester-wt` (after `make check` and three `make ui-test` builds, so `.venv`, `build/`, `advisor.db`, `.gp/`,
  `coverage.json` and the caches are all there), `scripts/deploy_gate.py --check` printed "no code changed since"
  for both and PASS, in about 4 s; the two files were restored byte for byte (md5) after. No ignored file reads as a
  change.
- **The pin fixture's change** (`tests/unit/test_deploy_gate_pin.py:59`, `conformance/test-deploy-shipped.py`): the
  fixture now declares `fly deploy`. With #494's fail-closed empty declaration, a fixture with none would make every
  refusal test pass vacuously (the #494 review's B1); declaring one makes them able to fail again. A strengthening.
- **`test_deploy_gate_dispatch.py`'s injected failure** moved from `subprocess.run` (`git show`) to
  `brief_fields.batch_read`, the reader #509 put in its place; the same case (a base workflow unreadable, so every
  dispatch is a deploy) is asserted.

### Test integrity
`git diff --diff-filter=D --name-only 3cddbdd..290557c`: nothing deleted. The four modified test files only add a
declaration to a fixture (above), add a table name to a list the client-decls test empties, and re-point one
injected failure; no assertion is removed or weakened. No security-invariant test was modified or deleted.

### Delta BLOCKING
None.

### Delta MINOR
- **M10** `scripts/ui_test.sh:93-95,99,105` -- #503's fix holds only while the simulator is already booted. Run 1 used
  `UI_TEST_DEVICE="iPhone 17"`, shut down at the start: xcodebuild boots it for the online pass and shuts it after,
  so `forget_answers`'s `xcrun simctl uninstall` fails ("Unable to lookup in current state: Shutdown", in
  `xcodebuild.log`), `|| true` hides it, the app keeps its answer, and both FailureScreenTests fail ("the failure
  screen never appeared", `FailureScreenTests.swift:23`; `:42`), engine down exit 65: #503's symptom. With the
  device booted first, run 2 (`UI_TEST_ONLY=FailureScreenTests`) and run 3 (all) are green. On the owner's Mac the
  default `iPhone 17 Pro` is usually booted, which is why #519's run passed. Remedy: boot the device before the
  uninstall (`xcrun simctl boot "$DEVICE" 2>/dev/null || true`, or `simctl bootstatus "$DEVICE" -b`), and fail the
  run when the uninstall fails for any reason but "not installed". Not a deploy blocker: the harness only.
- **M11** `scripts/deploy_gate.py:940-947` (`toplevel`), `:593-602` (`_redirected`) -- the #505 review's M2 by the
  environment. With `GIT_WORK_TREE` naming a clean checkout of the reviewed head, `deploy_gate.py --check` (what `make
  deploy-check` runs) and the argv form (`deploy_gate.py "fly deploy"`) both judge that checkout: a product change to
  `src/app.py` in the tree being deployed printed "no code changed since" and PASS, exit 0 (probed on the `_installed`
  fixture). `toplevel` honours the variable, and `_redirected` reads only `core.worktree`. The Bash guard's `--judge`
  path is not fooled (it judges the folder it runs in; this review's test), and the guard allows
  `GIT_WORK_TREE=... make deploy-check` (probed through `judge_call`). `fly deploy` stays the owner's (D-185), so no
  agent deploy passes through this; what can be forged is the PASS of `make deploy-check` that `/going-live` and the
  owner read. A gate result that stays green with no test, so the Escalate-NOW class: handed to the
  Security-Reviewer. Remedy: run the gate's git calls with the `GIT_*` environment removed, or refuse while any of
  `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES` or
  `GIT_CONFIG_*` is set; with one test per variable. Tonight's deploy is the owner's, by hand, from the owner's own
  shell, where none is set.
- **M12** `ios/ModelRanking/ContentView.swift:800-805` -- #484's button is proven by a source-text test
  (`tests/unit/test_settings_door_484.py:27`, red under F44) and the door by the two pins; no run taps it. A UI test
  cannot reach the guide on this Mac: the simulator's caption is "Apple Intelligence enhanced" (no guide). The draft
  UI test I wrote (`IntelligenceGuideTests`, kept outside the proposed tests because it skips here) compiled and
  skipped in run 3. Remedy: a launch argument that scripts `OnDeviceState` for UI tests, as `-UITestRouting` scripts
  the model tier, then that test; until then the button on a device is the owner's check before the TestFlight build.

### Delta suite result
- **`make check`** in `tester-wt` at `290557c`, serial, the merge gate: exit 0. session-check; lint (ruff: all checks
  passed); typecheck (mypy: no issues in 55 source files); pytest 4872 passed, 37 skipped (the contract and Epoch
  skips the budget names), offline sandbox, artifact required, 450 s; coverage 93% (refresh.py 97%, nightly.py 99%,
  status_record.py 100%); coverage-floor PASS (55 modules); `coverage_floor --derive`: CI will skip 96 of 4909, the
  budget 96; check-records and its self-test PASS; install-check; shell-dialect (12 scripts); wave-check-all (68
  records); conformance PASS (33); swift-test PASS (734, each in the manifest; SlowTierTests 7 of 7); client-decls
  PASS (23 client files, 4 configurations).
- **`make ui-test`** (D-175; not in check) against the fresh artifact, `UI_TEST_DEVICE="iPhone 17"`, engine on
  `127.0.0.1:8090`:
  - run 1 (the device shut down at start): engine up exit 0 (19 ScreenPathTests and 4 ScrollStepTests, 23 of 23,
    including #503's three: `testCodingGetsTwoFamilyLists...`, `testCodingShowsBothAnswers...`,
    `testFindAModelAnswersTheQuestionAsRouted`); engine down exit 65, both FailureScreenTests red (M10).
  - run 2 (the device booted, `UI_TEST_ONLY=FailureScreenTests`): exit 0, 2 of 2.
  - run 3 (the device booted, every class, with the draft guide test added for that run only and removed after):
    engine up 24 executed, 0 failures, the draft skipped; engine down 2 of 2; exit 0.
- **This review's tests**, each in `tester-fi` at `290557c`: `test_deploy_gate_505_tester.py` 1 passed,
  `test_deploy_gate_510_tester.py` 1 passed, ruff clean; each red under its fault (F19b, F12d).

## Delta round 2026-10-31b (ed18de5..243d115)

**Range:** `ed18de5bef8ad54d501b8a268db9900073ab903f..243d115`, the head of `integration/fixes-1031` (#532, #537,
#540, #538, #539): #517 (the policy, the workflows and the DevFlow pin at the merge-base AND the default branch's tip;
D-232 clause 1, D-233), #522 (a dispatched deploy workflow's text puts what it names on the deploy surface; D-232
clause 2), #518 (tests only, the verified reader's fail-closed paths), #535 (`Date.<=` on the standings sink's
Foundation list). Code: `scripts/deploy_gate.py`, `scripts/brief_fields.py`, `scripts/client_decl_gate.py`; tests:
three new files. Acceptance criteria read from `gh issue view 517/522/518/535` and `docs/decisions.md:6365`
(D-232), `:6392` (D-233).
**Risk tier:** HIGH. Every code change is to the deploy gate or a privacy gate (D-180).
**Seat:** my own worktree on `review/release-delta-1031b` at `243d115`, its own `.venv` (`make install`) and its own
copy of `advisor.db`, under this session's scratchpad. Red runs were done in the same tree by writing the pre-range
files with `git show ed18de5:<path> >` and writing HEAD's back; every fault was reverted by exact string replacement
and md5-checked against its pre-injection hash (`9c6737f89b08` `deploy_gate.py`, `bb009a5cd391` `brief_fields.py`,
`88e92f954bf2` `client_decl_gate.py`; every revert matched, `git status` clean after each). No launchd service, owner
data directory, Fly or GitHub write was touched; nothing was pushed.
**Fresh eyes:** I wrote none of the range. My only code is the three test files at `6e6f5be`.
**Cross-model routing:** author family Claude / reviewer family Claude; no second family was available in this seat.
Fresh context: the diff, the four issues, D-232, D-233 and the tests, not the implementers' sessions.

### Acceptance-criterion coverage

- **#517 / D-232 clause 1: `Deploy commands:` read at the merge-base and the tip, the union guarded** ->
  `tests/unit/test_deploy_gate_517.py:42` runs `deploy_gate.py "fly deploy"` on a branch cut before the declaration,
  its own brief without it: exit 2. RED at `ed18de5`'s code, GREEN at `243d115`; red under F1 (`protected_bases`
  returns the merge-base only, `scripts/brief_fields.py:339`) and F2 (`declared` reads the first base only,
  `scripts/deploy_gate.py:692`).
- **#517 / D-232 clause 1: `Working mode:` read at both, each mode's Tester owed** -> `test_deploy_gate_517.py:55`
  (the tip says heavy, the merge-base and the tree light: `--check` refuses and names heavy). RED pre-fix; red under
  F1, F3 (`scripts/deploy_gate.py:660` reads the first base's mode only).
- **#517 / D-232 clause 1: the base workflows read at both** -> `test_deploy_gate_517.py:89` (a deploy workflow only
  the tip holds: `gh workflow run release` exit 2). RED pre-fix; red under F4 (`scripts/deploy_gate.py:907`, the first
  base only).
- **D-233: a tooling file is DevFlow's only when both pins hold its bytes** -> `test_deploy_gate_517.py:67` (a branch
  cut before an upgrade restoring the older pin's bytes, carrying the newer verdicts: refused, names
  `scripts/tool.py`). RED pre-fix; red under F5 (`devflow_pins` reads the first base, `scripts/deploy_gate.py:412`)
  and F6 (`all` to `any`, `:437`).
- **D-233: "a base with no pin, or a pin that does not read, exempts nothing"** -> no test held it: F7 (`all(found)`
  to `any(found)`, `scripts/deploy_gate.py:412`) stayed green on all 284 deploy-gate tests. Closed by
  `tests/unit/test_deploy_gate_517_tester.py:33` (the tip's pin removed, garbled, emptied after the branch was cut;
  the control first passes with both pins) and `:45` (the merge-base's pin garbled, the tip pinning the upgrade): each
  red under F7, GREEN at `6e6f5be`.
- **#522 / D-232 clause 2: every file the workflow's text names is on the surface; a recipe runner anywhere, a change
  of directory, or a local `uses: ./` exempts nothing** -> `tests/unit/test_deploy_gate_522.py:58`, 19 spellings
  through `deploy_gate.py --check` (the issue's eight, the #522 review's B1 five and M1/R4 six). 14 RED at
  `ed18de5`'s code; the 5 path/case runner spellings were refused before #522 and are held as regressions, as the
  test says. Red under F8 (`named |=` dropped, `scripts/deploy_gate.py:581`), F10 (`cd` dropped), F11 (`uses: ./`),
  F12 (`working-directory:`), F13 (`env -C`), F15 (`re.IGNORECASE`), F17 (`$X` expansions kept), F18 (no leading-`/`
  strip), F19 (the whole `_UNREAD_IN_WORKFLOW` search dropped, `:536`). Three parts no test held: F9 (`pushd`
  dropped), F14 (`--chdir` dropped), F20 (`/` added to the runner's look-behind at `:524`, which hides `bash -c
  '/usr/bin/make ship'`). Closed by `tests/unit/test_deploy_gate_522_tester.py:30` (`pushd`, `env --chdir`, `env
  --chdir=`, `bash -c '/usr/bin/make ship'`, `sh -c "./make ship"`): each red under its fault, GREEN at `6e6f5be`.
- **#522: the issue's setup-line decision (checkout, `pip install` must not empty the surface)** ->
  `test_deploy_gate_522.py:67` (a workflow of setup steps and the declared deploy script leaves a plain tooling file
  DevFlow's: exit 0) and `:78` (`env FOO=1 bash -c` is no `env -C`); red under F16 (the `(?-i:` guard dropped).
- **#518: one test per surviving mutant, or a sentence why it is equivalent** -> SHA-256 ids (#511 R1, #509 N14):
  `tests/unit/test_deploy_gate_518.py:31`, red under F21 (sha1 always, `scripts/brief_fields.py:145`), F22 (the
  commit's `tree` regex narrowed to 40, `:180`) and F25 (the walk's id size fixed at 20 bytes); `40000` on the way
  (#511 R2, #509 N7): `:54`, red under F23 (the type bits instead of the spelling at `:207`); a nested tree error
  (#509 N12): `:69`, red under F24 (`continue` for `raise` at `:305`); N13b: the equivalence sentence is
  `docs/process-log.md:1668`. Tests only, so no red commit: each test passes on `ed18de5`'s code, as it should.
- **#535: a reviewed edit adds `Foundation.Date.<=` to `SINK_FOUNDATION_ALLOWED` with its reason** ->
  `scripts/client_decl_gate.py:1391-1393` (the entry and its reason). Proven through the real gate: `make
  client-decls` PASS at `243d115` (23 client files, 4 configurations, 83 s); with the entry removed (F26) it fails in
  all four with the issue's exact message ("`Foundation.Date.<=` is not on the list ..."), then PASS again after the
  in-place restore. CI does not run client-decls, so `tests/unit/test_client_decl_gate_535_tester.py:41` holds the
  allowance in the unit suite (red under F26), `:48` holds that `<`, `>`, `>=` and `==` stay refused in the same sink,
  and `:54` that the engine client's sink did not gain it. The gate reported `<=` only, so the narrow edit matches
  the issue's "if the same resolution now applies" clause.

### Red to green
The range's own tests run against `ed18de5`'s `scripts/deploy_gate.py` and `scripts/brief_fields.py`: 18 failed, 12
passed. Failed: all four of `test_deploy_gate_517.py`, 14 of the 19 spellings of `test_deploy_gate_522.py:58`. The
twelve green: the five runner spellings refused before #522, the two #522 controls, the five #518 tests (tests only).
All 30 GREEN at `243d115`. #535: `make client-decls` red with the entry removed (F26), green with it.

### Fault injection
Each fault injected in this tree, the deploy-gate tests run (`tests/unit` and `conformance`, `-k "deploy_gate or
brief_fields or deploy_shipped"`, `-n 8 -x`), reverted by exact string replacement, md5 compared.

| # | fault | result |
|---|---|---|
| F1 | `protected_bases` returns the merge-base only | RED `test_deploy_gate_517.py:42`, `:55` |
| F2 | `declared` reads the first base only | RED `:42` |
| F3 | the verdicts read the first base's mode only | RED `:55` |
| F4 | `_workflow_texts` reads the first base only | RED `:89`, `test_deploy_gate_494.py` |
| F5 | `devflow_pins` reads the first base only | RED `:67` |
| F6 | `shipped_unchanged` `all` to `any` | RED `:67` |
| F7 | `devflow_pins` `all(found)` to `any(found)` | GREEN; RED `test_deploy_gate_517_tester.py:33`, `:45` |
| F8 | the workflow's named files not added to the surface | RED `test_deploy_gate_522.py:58[a-script]` |
| F9 | `pushd` dropped | GREEN; RED `test_deploy_gate_522_tester.py:30[pushd-then-relative]` |
| F10 | `cd` dropped | RED `:58[cd-then-relative]` |
| F11 | `uses: ./` dropped | RED `:58[local-uses]` |
| F12 | `working-directory:` dropped | RED `:58[working-directory]` |
| F13 | the `env -C` alternative dropped | RED `:58[env-C]` |
| F14 | `--chdir` dropped | GREEN; RED `test_deploy_gate_522_tester.py:30[env-chdir]`, `[env-chdir-equals]` |
| F15 | `re.IGNORECASE` dropped | RED `:58[expansion]` |
| F16 | `(?-i:` dropped (a lower-case `-c` read as `-C`) | RED `:78` |
| F17 | expansions not taken out | RED `:58[workspace-variable]` |
| F18 | no leading-`/` strip | RED `:58[workspace-variable]` |
| F19 | `_UNREAD_IN_WORKFLOW` not searched | RED `:58[quoted]`, `[local-uses]`, `[env-C]` |
| F20 | `/` in the runner's look-behind | GREEN; RED `test_deploy_gate_522_tester.py:30[make-by-path-in-bash-c]` |
| F21 | sha1 for every id | RED `test_deploy_gate_518.py:31` |
| F22 | the commit's `tree` regex at 40 hex | RED `:31` |
| F23 | a directory on the way by its type bits | RED `:54` |
| F24 | a nested tree error skipped in `verified_files` | RED `:69` |
| F25 | the reader's id size fixed at 20 bytes | RED `:31` |
| F26 | `Date.<=` removed from the standings sink's list | RED `make client-decls` (4 of 4); RED `test_client_decl_gate_535_tester.py:41` |

**Mutation kill-rate (advisory):** no mutation runner is wired for this stack. Hand faults: 26, 22 killed by the
range's own tests or gate, 4 green (F7, F9, F14, F20); 26 of 26 killed after this round's tests.

### Test integrity
`git diff --name-status ed18de5..243d115 -- tests conformance`: three files added, none modified or deleted. No
assertion weakened, no test skipped; no security-invariant test touched. The range's tests cite their issue and ADR
in the module docstring (`#517:`, `#522:`, `#518:`) rather than a `# covers` comment, as the deploy-gate tests have
since #410; this round's tests carry `# covers`.

### Observations (no finding)
- `scripts/deploy_gate.py:353` (`_unhashed`, #493) has its own `{40,64}` tree regex that no SHA-256 test reaches.
  Pre-existing, not on #518's list, and it fails closed (a SHA-256 repository would refuse, not pass).
- The stale-entry rule (`tests/unit/test_client_decl_gate.py:1113`) means a toolchain that binds `<=` to the standard
  library again makes `Date.<=` an unseen entry and client-decls red; #536 (print the toolchain it read) is the
  existing issue for tracing that.
- The Security-Reviewer's open items on this range are filed: #541 (four more `env`/`PATH` spellings), #534 (a stale
  `origin/HEAD`), #533 (the guard lets the change move the default branch's refs).

### Delta BLOCKING
None.

### Delta MINOR
None. The four faults that stayed green are closed by this round's tests (`6e6f5be`).

### Delta suite result
- `make check-fast` in this tree with the three tests: PASS in 221.8 s -- lint, typecheck, records (session-check,
  check-records, its self-test, install-check, harvest-context-check, shell-dialect, wave-check-all, conformance),
  swift-test, client-decls (4 configurations), test (pytest 4919 passed, 37 skipped; coverage 93.16%). The commit's
  own commit-msg hook ran it again: PASS in 202.2 s.
- `ruff check` on the three new files: all checks passed.

### Tests added this round
- `tests/unit/test_deploy_gate_517_tester.py:33`, `:45` -- D-233's "a base with no pin, or a pin that does not read,
  exempts nothing" (F7).
- `tests/unit/test_deploy_gate_522_tester.py:30` -- D-232 clause 2's `pushd`, `env --chdir`, and a runner by path or
  `./` inside a `-c` string (F9, F14, F20).
- `tests/unit/test_client_decl_gate_535_tester.py:41`, `:48`, `:54` -- #535's allowance, its narrowness, and its sink
  (F26), in the suite CI runs.
