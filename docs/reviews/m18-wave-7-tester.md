---
record_type: review
id: m18-wave-7-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Wave 7 Tester Review (m18)

**Reviewer:** Tester subagent (fresh eyes). This seat wrote none of the wave's code, tests or records.
It is not the wave's Code-Reviewer.
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** `e023296..b8432fe` (33 files, +1151 / -65). W7's own commits are `976f559`,
`593718c`, `f8ca4d9`, `7b2b668`, `a9f3c87` (the code review) and `b8432fe` (its fix round).
`58e8bf4` merges W6 and holds no W7 code. `e023296` is the closed M18-W6 head.
**Risk tier:** HIGH (`docs/plans/m18-wave-7-plan.md:14`). #104 touches `scripts/engine_service.sh`,
a security glob. By D-172 no security seat runs on the wave.
**Code-Reviewer verdict:** MINOR, M1 to M7 (`docs/reviews/m18-wave-7-review.md`). Not BLOCKING, so
this seat runs. `b8432fe` is the fix round; this seat is the first to test it.
**Model routing (HIGH, advisory):**
- Author family: Claude (every commit carries `GP-Agent: claude-code/local-lane`).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second model family is available to this seat.
- Fresh context: I started from the base profile, then read the wave plan, the milestone plan's W7
  amendment, the issues (#102 to #124, and #128 to #130), the code review and the diff. I have no
  memory of any authoring or reviewing session.

**Base-pinned policy:** `.claude/agents/Tester.md` has the same sha256 at `e023296` and in the
worktree. `git diff --stat e023296 b8432fe -- .claude .agents permission-matrix.md .github` is
empty. No commit in the range carries `Co-Authored-By` or "Generated with".

## Verdict
MINOR

**Nothing blocks.** Every acceptance check in the wave plan has a citing test that passes, or a
record where the check is a record (P0, #120). The suite is green. No test was weakened, skipped or
deleted in the range. The changed assertions follow the new Claude spellings; the held-out gate
was rewritten stricter (case-folded); one egress pin became two exact ones; the reload was removed.

**Fault injection: 54 of 79 faults killed (68.4%).** All restored byte-identically. The 25 that
stayed green are T1. I wrote a test for each one. Each new test passes on `b8432fe` and fails on its
fault. With them, 79 of 79 die. The tests are uncommitted in this worktree and in
`docs/reviews/m18-wave-7-tester.patch`.

**Four MINORs (T1 to T4), one K.9 (K1), two risks (R1, R2).** T1 is closed once the author applies
the patch. T2 is the one to fix before the wave closes: on the installed service, the launcher's
hint still prints a command that exits 2, the very symptom #104 reported.

## Acceptance-criterion coverage

W7 has no REQ-ID. Its checks are the wave plan's phase table (`docs/plans/m18-wave-7-plan.md:41-44`).
The tests cite their issue ids in docstrings.

- **P0: this plan, and the milestone plan's W7 amendment.** → `docs/plans/m18-wave-7-plan.md`;
  `docs/plans/m18-plan.md:230-233`. — RECORD, MET.
- **P1, #102: a repeat is decided by model id (two models sharing a display); red first.** →
  `tests/unit/test_recommend.py:638` (the value pick), `:664` (the budget pick), `:679` (the leader
  repeated has no trade-off). Red reproduced by faults 102-1 and 102-2 (the old rule, per pick).
  — GREEN. One mix of the two flags was unpinned (T1); now `:692`.
- **P1, #103: the run reports carry one account of unknown efforts; red first.** →
  `tests/unit/test_build.py:549`. Red by 103-1 (the line removed). — GREEN.
- **P1, #104: the launcher's message names a command that runs (its `--help` exits 0); red first.** →
  `tests/unit/test_engine_service.py:561`. Red by 104-1 (the old `build --fetch-epoch`). — GREEN by the
  plan's words. The `--db` value was unpinned (T1); now `:586`. On the service's own path the printed
  command still fails (T2).
- **P1, #112: no served display is its raw id where a product name is known; Claude names have one
  word order; each held by a test over the served artifact's names; red first.** →
  `tests/unit/test_display_names.py:50`, `:64`, `:69`, `:77`, `:87` (the artifact test). Red by 112-1
  (the old order) and 112-9 (the table not read). — GREEN. The turn's edges were unpinned (T1); now
  `:108`. The artifact test's inputs: R1.
- **P2, #114: the two test files pass in either order.** → `tests/unit/test_api_config.py:731` (no
  `reload` call). I ran the failing order by hand: 32 passed. — GREEN. A reload under another name
  passed the gate and broke the order (T1); now `:750` runs the two files in that order, as #114
  asked.
- **P2, #122: a planted real request fails the Python suite.** → `tests/unit/test_no_network.py:15`,
  `:25`, `:37`. Red by 122-1 (the guard off). — GREEN. Four doors, the install time and the step-out
  were unpinned (T1); now `:57`, `:64`, `:78`. `sendmsg` is still open (T3).
- **P2, #123: the launcher refuses an artifact past a serving bound, as a script.** →
  `tests/unit/test_engine_service.py:399` (two bounds). Red by 123-1, 123-2 and 123-3. — GREEN.
- **P2, #105: every PRD `file:line` lands on a test declaration, and the stale ones are corrected.**
  → `tests/unit/test_prd_citations.py:102`, `:108`. Red by 105-8 and 105-9 (a pointer moved). —
  GREEN. Four holes in the gate (T1), closed in the patch at `:123`, `:138`, `:147` and in
  `problems()`. Pointers into workflows and records stay outside the gate (K1).
- **P2, #119: a held-out question in a tuning `.json` set fails the gate.** →
  `tests/unit/test_ios_client_contract.py:165` (the gate), `:220` (its planted cases). — GREEN.
  The gate's wiring to the sets, and three of its folds, were unpinned (T1); now `:1304`, `:1316`.
- **P2, #118: greetings are labelled `NOT_A_SEARCH` in both off-topic sets, each change listed.** →
  `scripts/router_probe/offtopic_questions.json:33`, `offtopic_heldout_questions.json:7`, `:16`;
  listed in `f8ca4d9`'s message. — RECORD, MET. No test read the labels or the probe's skip (the
  review's M7). Now `test_ios_client_contract.py:1328`.
- **P3, #121: a register save to a non-file URL fails a test.** →
  `ios/EngineTests/FrontDoorTests.swift:765`; pins at `tests/unit/test_router_hints.py:525-526`,
  `:676`. Red by 121-1 (`url.isFileURL` removed: `swift test` fails). — GREEN.
- **P3, #124: Epoch's citation reads "Capabilities & benchmarking".** →
  `tests/unit/test_recommend.py:655` (the payload), `:136` (the README carries the payload's string).
  Red by 124-1 and 124-2. — GREEN.
- **P3, #120: D-174 names the served artifact as the seat's copy.** → `docs/decisions.md:3614-3619`.
  This seat was set up that way. — RECORD, MET.

## Red→green on reported symptoms

No issue has a separate red commit. So I put each symptom back in place and watched its test fail,
then restored the file and watched it pass:
- **#102**, a pick that shares the leader's name taken for the leader: 102-1, 102-2. Fail
  `test_recommend.py:638`, `:664`.
- **#103**, two accounts: 103-1. Fails `test_build.py:549`.
- **#104**, the printed command does not run: 104-1. Fails `test_engine_service.py:561`.
- **#112**, raw ids and two Claude orders: 112-1, 112-9, 112-10, 112-11. Fail
  `test_display_names.py:50`, `:64`, `:69`, `:87`.
- **#114**, the reload: 114-1 (the reload put back). Fails `test_api_config.py:731`. Under another
  name (114-2b) it passed the suite, and the failing order gave 5 failures again: T1.
- **#122**, a real request: 122-1. Fails `test_no_network.py:15`, `:37`.
- **#123**, the bound refusal: 123-1. Fails both cases of `test_engine_service.py:399`.
- **#105**, a moved pointer: 105-8, 105-9. Fail `test_prd_citations.py:102`.
- **#119**, a gate that reads no `.json` set (119-4, the state before the fix): it passed the suite.
  The new self-test calls the helper only. T1; now red on `test_ios_client_contract.py:165`.
- **#121**, a save that tries a remote write: 121-1. `swift test` fails
  `testASaveToAnythingButAFileTriesNoWrite`.
- **#124**, the old title: 124-1, 124-2. Fail `test_recommend.py:655`, `:136`.

## Suite result

- **`make check-fast` at `b8432fe`, with this seat's tests and this record:** PASS in 59.7 s, rc 0.
  Six legs, each PASS: `lint`; `typecheck`; `records` (`check-records`, which read this record too,
  `check-records-selftest`, `install-check`, `harvest-context-check`, `shell-dialect`,
  `wave-check-all`, `conformance`); `test` (1761 passed, 25 skipped; coverage 91.80%;
  `coverage-floor` PASS, 45 modules); `swift-test` (parallel: 451 tests, exactly the manifest);
  `client-decls` (19 files in 4 configurations). Evidence: `check-fast PASS in 59.7s`.
- **The suite at `b8432fe`, before this seat's tests:** 1749 passed, 25 skipped, rc 0, in 40 s.
- **With this seat's tests:** 1761 passed, 25 skipped, rc 0. The order test starts one child pytest
  of the two files (about 1.5 s, no coverage, no workers).
- **Coverage on touched code** (from the run at `b8432fe`): `board_tables.py` 100%, `registry.py`
  98.8%, `recommend.py` 95.5%, `build.py` 95.3%; total 91.8%. Every line the wave added in `src` is
  covered (`registry.py:511-590`, `recommend.py:526-610`, `build.py:781`). No drop.
- **Not run:** any installer by hand, launchctl, Docker, the simulator, `make lock` (network).

## Mocks / contract tests

- **No new external integration.** The wave adds no client. The network guard is a test-side
  fixture, not a mock.
- **The live contract tests** (`tests/integration`, `RUN_CONTRACT_TESTS=1`) were not run: they need
  the network. Their step-out from the guard is now pinned without the network (`test_no_network.py:78`).

## Fault injection

**Method.** Each fault replaced one exact string in place (a count of 1 was asserted first). Its
targeted tests ran; if they stayed green, the whole suite ran (`pytest -n auto`); a `FrontDoor.swift`
fault also ran `swift test`. Then the file was written back from its bytes, and its sha256 compared.
`git diff --quiet` was clean after each round. Every run was bytecode-free
(`PYTHONDONTWRITEBYTECODE=1`, `__pycache__` cleared before each run). Every Python run was wrapped in
`sandbox-exec` with outbound IP and the mDNSResponder socket denied, and loaded a harness plugin that
stands in for the network before `conftest.py` installs its guard. So a fault that opened a door saw
a fake answer, and no packet or lookup left the machine. Any run past its limit would have been
ended by SIGKILL to its group; none needed it.

**Kill rate: 54 of 79 (68.4%).** With this seat's tests: 79 of 79.

| issue | what was broken | faults | killed | stayed green (T1) |
|---|---|---|---|---|
| #102 | the identity rule, both picks; each of the four trade-off fields | 9 | 8 | 102-5 the budget flag read from the value pick |
| #103 | the discount: removed, discounting nothing, before the reconcile | 3 | 3 | — |
| #104 | the hint: old module, wrong `--db`, no such module, a prose-only flag | 4 | 3 | 104-2 `--db advisor.db` (M6 put back) |
| #112 | Claude order (rules, turn, edges, suffixes, Haiku); the table; the artifact test | 14 | 9 | 112-4 and 112-5 the edge at Claude 4 moved either way; 112-6, 112-7 the rest of the name dropped; 112-8 Haiku left out |
| #114 | the reload: put back; under an alias | 2 | 1 | 114-2b `from importlib import reload as again` |
| #122 | the guard; each of 8 doors; IPv6; "local" too wide; install time; the step-out (3) | 15 | 7 | 122-2 `connect`; 122-3 `connect_ex`; 122-7 `gethostbyname_ex`; 122-10 IPv6 `connect`; 122-12 installed per test; 122-13 lifted for every test; 122-14 lifted without the variable; 122-15 never put back |
| #123 | the refusal: disabled, exits 0, the bounds dropped | 3 | 3 | — |
| #105 | the gate's checks (7); the PRD's data (4) | 11 | 7 | 105-6 an ambiguous name; 105-7 only the first of `a, :b`; 105-10 `Makefile:108` put back; 105-11 the `:106` after a parenthetical moved |
| #119 | the folds (3); the sets read; short whole; `{q}` sets; long inside | 7 | 2 | 119-2, 119-3 a fold dropped; 119-4 no set read; 119-5 a short question whole; 119-6 `{q, ...}` sets |
| #121 | the writer (4); the R3 pin (5 spellings) | 9 | 9 | — |
| #124 | the payload's title; the README's | 2 | 2 | — |
| **total** | | **79** | **54** | **25** |

**Left out of the count, with the reason.**
1. **Equivalent:** 114-3b, `sys.modules.pop("app.adapter.main")` and import again. A new module object
   leaves `test_api_config.py`'s names consistent: the failing order passed (32 passed).
2. **Invalid:** 114-2 and 114-3, the first plants. They added lines, so the PRD gate failed on the
   shifted pointers, not on the fault. Each was redone line-neutral as 114-2b and 114-3b.
3. **Discarded run:** my first run with the patch read a stale `.pyc` of fault 112-14 (same size,
   restored within the same second). I threw that run away and redid every round bytecode-free.

**Checks of this seat's own #118 test:** 118-1 (a greeting labelled a search again) and 118-2
(`probe.swift` scores `NOT_A_SEARCH` again). Both fail `test_ios_client_contract.py:1328`. Before
the patch no test read either file.

## The code review's findings, re-checked

Each against the code at `b8432fe`:
- **M1 (the network guard).** Installed in `pytest_configure`; `gethostbyname(_ex)`,
  `gethostbyaddr`, `getnameinfo` and `sendto` refused; the step-out is per test, under
  `tests/integration`; INV-6 is partial again and G-5 names child processes. — FIXED in the code.
  Eight faults in it stayed green (T1, now pinned). `sendmsg`, which M1 named, is still open (T3).
- **M2 (the PRD gate).** Every line is read; a Makefile pointer must land on a target's line;
  `Makefile:108` is now `:115`. — FIXED in part. Any target passes, so `:108` (`format:`) put back
  passed. The rewording of REQ-RANK-001's Status line put `:106` outside the match. Both closed in the
  patch (T1).
- **M3 (#102's other half).** The budget pick and the leader each have a test; both review faults
  die. — FIXED. One mixed fault stayed green (T1, now pinned).
- **M4 (#112 over the served names).** `claude_word_order` is applied where a derived name is chosen;
  an artifact test names every served model. — FIXED. The turn's edges were unpinned (T1). The
  artifact test's inputs differ from the build's (T4, R1).
- **M5 (the reload gate).** Any call named `reload` is refused, read from the syntax tree. — FIXED
  for that spelling. An alias passed and broke the order again (T1); the patch adds the order test
  #114 asked for.
- **M6 (the hint's database).** The hint prints `--db $DB`. — FIXED for a path without spaces. The
  installed service's path has one (T2).
- **M7 (the probe's reader).** `probe.swift` skips `NOT_A_SEARCH` rows and says how many. — FIXED.
  Pinned now (`test_ios_client_contract.py:1328`).
- **K4 (case).** Both halves fold case. — FIXED. Neither fold was pinned on its own (T1).
- **K5 (REQ-REF-009).** The row cites `test_nightly_refresh.py:639` and `:653`. — FIXED.
- **R3 (the writer seam).** `test_router_hints.py:676` refuses a `write:` argument in any app call
  to `GapRegisterStore(`. I tried five spellings: the call, the call with a built URL,
  `GapRegisterStore.init(`, `.init(` with a built URL and a `typealias`. All five fail a test (the
  pin, or the egress gate, which refuses `.init(` and `typealias` in client files). — FIXED.
- **K1 to K3** are filed as #128, #129 and #130. — FILED.

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **T1** `tests/unit/test_recommend.py`, `test_engine_service.py`, `test_display_names.py`, `test_api_config.py`, `test_no_network.py`, `test_prd_citations.py`, `test_ios_client_contract.py`. **Twenty-five faults stayed green. Each now has a test, in the patch.**
  1. **#102 (102-5).** No test had a value pick that is the leader beside a budget pick that is
     not. So the budget line could read the value pick's flag.
  2. **#104 (104-2).** The test reads the hint's flags, not their values. M6's `--db advisor.db`
     put back passed.
  3. **#112 (112-4 to 112-8).** The Claude 4 edge could move either way; the date or mode after the
     version could be dropped; Haiku could be left out of the turn.
  4. **#114 (114-2b).** `from importlib import reload as again` passed the gate, and the failing
     order gave "5 failed, 27 passed" again.
  5. **#122 (8 faults).** The planted requests stop at `getaddrinfo`, so the `connect` and
     `connect_ex` doors were never reached; `gethostbyname_ex` and IPv6 were never tried. The
     guard could be installed per test (imports and wider fixtures open again). The step-out could
     lift every test in a contract run, lift `tests/integration` with no variable, or stay lifted.
  6. **#105 (4 faults).** An ambiguous name could take its first path; only the first of `a, :b`
     could be checked; `Makefile:108` (`format:`) put back passed, since any target passed; the
     `:106` in `test_rank.py:92 (which asserts the blend), :106` was outside the gate's match, and
     moving it passed.
  7. **#119 (5 faults).** Each fold could be dropped on its own; the real gate could read no `.json`
     set; a short question whole in a set, and the `{q, ...}` sets, were never tried.

  **The fix:** apply `docs/reviews/m18-wave-7-tester.patch` (12 tests, two rules added to the PRD
  gate, one line in the held-out gate; the table under "Tests added"). Each test passes on `b8432fe` and fails on its fault.

- **T2** `scripts/engine_service.sh:49`; `scripts/install_engine_service.sh:24-25`, `:72`. **On the installed service, the hint prints a command that exits 2: #104's symptom, on the one path that matters.** The service sets `MODEL_RANKING_DB="$DEPLOY/data/advisor.db"`, and `$DEPLOY` is under `~/Library/Application Support/`. The hint prints `--db $DB` with no quotes. Copied into a shell, the path splits at the space. I ran the launcher with a missing database under a folder named `Application Support`: the printed line split into `--db .../probe tree/Application` and two stray words. `refresh.main` on that argv exits 2: "unrecognized arguments: Support/model-ranking/engine/data/advisor.db". **The fix:** print the path quoted (`--db '$DB'` inside the echo's double quotes). Then put the patch's test (`test_engine_service.py:586`) under such a folder: `missing = tmp_path / "Application Support" / "data" / "advisor.db"`. It fails today.

- **T3** `tests/conftest.py:65-105`; `docs/security-invariants.md:172`. **`socket.sendmsg` passes the guard, and G-5 says the in-process half holds.** M1 named `sendto` and `sendmsg`. The fix patched `sendto` only. I installed the guard in a script and sent a datagram to 192.0.2.1: `sendto` was refused by the guard; `sendmsg` passed it and was stopped only by this seat's sandbox. **The fix:** guard `sendmsg` when it is given an address (its fourth argument), and add it to `test_the_connect_doors_refuse_a_numeric_address`; or name it in G-5.

- **T4** `tests/unit/test_display_names.py:87-104`. **The artifact test names models from other inputs than the build.** The build passes each score's parsed model name (`registry.py:685`). The test passes `scores.raw_name` and every `pricing.alias`. For 20 of the 200 derived models that are not in the table, the test's name differs from the served one (for example `gemma-4-26B-A4B-it` against `gemma-4-26b-a4b-it`). Its two checks still hold today: no served raw id is left outside the table and OpenAI's six, and the table faults die. But its docstring says "named the way this code would name it on the next build". **The fix:** say "an approximation" in the docstring, or read the names the way the build does.

## K.9 candidates spotted outside this wave's scope

- **K1** `tests/unit/test_prd_citations.py:19`. **The PRD gate reads code and Makefile pointers only.** Thirteen pointers go into workflows and records (`docs/prd.md:226`, `:257`, `:401`, `:462`, `:538`, `:540`, `:541`), for example `.github/workflows/ci.yml:54` and `docs/plans/m14-wave-1-close.md:46`. I read each: all land on their text today, and nothing checks them. Enhancement: check that such a pointer lands inside its file, as the gate's docstring says for "any other file".

## Risks queued to next M

- **R1** `tests/unit/test_display_names.py:87`. **The artifact test reads an artifact built before W7.** It recomputes names from the rows, so it sees the table and the turn, not what a refresh will serve. A refresh that serves another spelling than the test computes is not seen (T4's 20 models). What would show it: after the next refresh, `select id, display from models` differing from the test's names for a model outside the table.
- **R2** `tests/conftest.py:36-48`. **The review's R2 stands: the guard trusts loopback.** A proxy on 127.0.0.1 carries a request off the machine. No proxy variable is set in this seat. What would show it: a runner with `HTTPS_PROXY` set to a local proxy and an `httpx` client that honours it.

## Tests added/extended this review

Uncommitted in this worktree, and in `docs/reviews/m18-wave-7-tester.patch` (sha256
`3e1a971b9d6baac33f40990a683606dc7fec8f50e3430719858e56cf6dfcc3c7`, 7 files, +235 / -1;
`git apply -R --check` clean against the tree). Each passes on `b8432fe` and fails on its fault:

| test | proves | fails on |
|---|---|---|
| `tests/unit/test_recommend.py:692` `test_the_value_pick_can_be_the_leader_while_the_budget_pick_is_not` | #102: each pick is compared with the leader on its own | 102-5 |
| `tests/unit/test_engine_service.py:586` `test_the_launchers_hint_builds_the_artifact_it_looked_for` | #104, M6: the printed `--db` is the path the launcher looked for | 104-2 |
| `tests/unit/test_display_names.py:108` `test_claude_4_is_the_edge_and_the_rest_of_a_name_stays` | #112: the edge at Claude 4, Haiku, the rest of the name | 112-4 to 112-8 |
| `tests/unit/test_api_config.py:750` `test_the_empty_answer_tests_then_this_file_pass_in_that_order` | #114: the failing order, run as #114 asked | 114-2b |
| `tests/unit/test_no_network.py:57` `test_the_guard_is_in_place_before_any_test_module_is_imported` | #122, M1: installed at configuration | 122-12 |
| `tests/unit/test_no_network.py:64` `test_the_connect_doors_refuse_a_numeric_address` | #122: `connect`, `connect_ex`, IPv6, `gethostbyname_ex`, each with a call that sends nothing | 122-2, 122-3, 122-7, 122-10 |
| `tests/unit/test_no_network.py:78` `test_only_a_live_contract_test_steps_out_of_the_guard` | #122: the variable and the folder, and the guard put back | 122-13, 122-14, 122-15 |
| `tests/unit/test_prd_citations.py:123` `test_a_pointer_past_a_parenthetical_is_read_too`, with the bare-pointer pass in `problems()` | #105: `:106` read, `at :693` a body pointer | 105-11 (through `:102`, the real PRD) |
| `tests/unit/test_prd_citations.py:138` `test_every_pointer_of_a_list_is_read_and_a_name_must_be_one_file` | #105: the list and the one-path rule | 105-6, 105-7 |
| `tests/unit/test_prd_citations.py:147` `test_a_makefile_pointer_lands_on_the_target_its_sentence_names`, with the named-target rule in `problems()` | #105, M2: the target the sentence names | 105-10 (through `:102`, the real PRD) |
| `tests/unit/test_ios_client_contract.py:1304` `_every_tuning_set_read`, called by the gate at `:196` (one line, in place) | #119: the gate reads the sets, of both shapes | 119-4, 119-6 |
| `tests/unit/test_ios_client_contract.py:1316` `test_the_held_out_gate_folds_case_on_every_side_and_reads_every_shape` | #119, K4: each fold; a short question whole; a `{q}` set | 119-2, 119-3, 119-5, 119-6 |
| `tests/unit/test_ios_client_contract.py:1328` `test_greetings_in_the_off_topic_sets_are_not_searches_and_the_probe_skips_them` | #118, M7: the labels and the probe's skip | 118-1, 118-2 |

The edits to existing files append at the end, except two: the gate line at
`test_ios_client_contract.py:196` (same line count) and `problems()` in `test_prd_citations.py`,
which no PRD pointer cites. So no PRD pointer moves. The new network tests try each door with a call
that sends nothing even if the door were open: a UDP `connect` only sets the peer, and a numeric
name needs no resolver. The held-out tests use made-up questions and print only file names.

## How I worked

- My worktree only, detached at `b8432fe`, with its own `.venv` (`make install`, from the locks) and
  its own copy of the served `advisor.db`. Logs and the fault runner are in its gitignored `notes/`.
- No live held-out question was printed. The live sets were read only as counts. The two off-topic
  sets I read are on the gate's retired list.
- Every process I started has exited. The children of the tests end by `subprocess.run`'s timeout
  (SIGKILL) at worst; the fault runner kills a run's whole group with SIGKILL past its limit. None
  needed it. No probe used `os.abort()` or a crash path.
- The worktree holds only this record, the patch and the patch's test edits as changes.
