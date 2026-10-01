---
record_type: review
id: m18-wave-1-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-01
---
# Wave 1 Tester Review (m18), second seat

**Reviewer:** Tester subagent (fresh eyes). This is the second Tester seat on this wave. It wrote none
of the wave's code, tests or records. It is not one of the wave's three Code-Reviewers, and it is not
the first Tester, whose BLOCKING verdict (`90109a7`) this file replaces. Nothing below is taken from
that verdict without being run again here.
**Independent:** yes
**Date:** 2026-10-01
**Commit range:** `e82011b..ed8b7e7`: 18 commits, 27 files. `e82011b` is the merge-base with
`origin/main`. The range holds the three Code-Reviewer verdicts (`e05ae15`, `78aa6d1`, `8e6232a`),
D-172 (`cc78cb7`), five red-then-fix pairs, the first Tester's verdict (`90109a7`) and the author's
answer to it (`ed8b7e7`). `ed8b7e7` changes tests and `docs/prd.md` only: no product code moved
after `8cfdd98`.
**Risk tier:** HIGH (`docs/plans/m18-plan.md:39`, `:137`; `docs/plans/m18-wave-1-plan.md:11`)
**Code-Reviewer verdict:** PASS-WITH-MINORS (`docs/reviews/m18-wave-1-review.md`, round 3, `8e6232a`).
D-172 removes the per-wave security pass; the fault injection below is still owed, and was run.
**Model routing (HIGH, advisory):**
- Author family: Claude (the commits carry `GP-Agent: claude-code/local-lane`).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second model family is available to this seat.
- Fresh context: this seat started from `.claude/agents/Tester.md`, `.agents/rules/practices.md` and
  `permission-matrix.md` §11, all read from `e82011b` with `git show`. (`docs/permission-matrix.md`
  does not exist at the base; the matrix is `permission-matrix.md` at the root.) It then read the
  plans, D-171 with notes 1-10, D-172, REQ-DEV-001, the owner's page, the three review rounds, the
  first Tester's verdict and the diff. It has no memory of any authoring or reviewing session.
**Base-pinned policy:** `git diff --stat e82011b..ed8b7e7 -- .claude .agents permission-matrix.md
.github epb.html or.md` is empty. `AGENTS.md` changes only under D-172.

## Verdict
PASS-WITH-MINORS

**Nothing blocks.** Every clause of REQ-DEV-001 that code can prove has a citing test that passes,
every red commit sampled fails where it should, coverage on the touched module went up, and both
gates pass. The first Tester's two blockers are closed, and each of its eight surviving faults is
now killed by one of the tests `ed8b7e7` added.

**Five MINORs, each a fault that stayed green.** Four come with a test, proven in a scratch copy;
the fifth belongs to #69.
- **T8.** The Host check is proven only on `/v1/categories`. A check scoped to `/v1` passes the whole
  suite, which would leave `/health` and every other path open to any Host.
- **T9.** `--no-lan`, the only control while the network is open (D-171 note 7), is tested only through
  `--print-wrapper`. The install the owner runs to close it is never run, and its closing line
  "home network: off" is asserted nowhere.
- **T10.** The app shows the address under the engine's refusal by matching the code `unknown_host`.
  That code is two literals, one in Python and one in Swift, and no test ties them together.
- **T11.** `engineURL`'s empty-host guard never runs. `http://:8080` parses with an empty host, not a
  missing one, and no test value reaches the guard.
- **T12.** A second shape of T4 (#69): wrapping the address line in a condition that is never true for
  the four failures it serves passes the source pin.

**What was run.**
- `make check-fast`: rc 0. `make wave-check-all`: rc 0.
- The red-first order was spot-checked on three pairs of five, with Swift on one.
- A real engine on 127.0.0.1 was probed with raw Host headers.
- **63 faults were injected: 54 killed, 2 equivalent, 7 survived.** Of the 7, C5 is the first Tester's
  T4, already on #69. The other six are T8 to T12.

## Acceptance-criterion coverage (REQUIRED)

Every test named here is GREEN at `ed8b7e7`. The fault ids are defined under "Fault injection".

REQ-DEV-001 (`docs/prd.md:551`) and D-171, clause by clause. "Entry" says how the test reaches the
behaviour:
- live: through the real entry point;
- executed: the function itself, called directly;
- a stand-in for the entry point;
- a source pin.

| clause | citing test (file:line) | entry | faults it kills | status |
|---|---|---|---|---|
| The engine binds loopback unless the installer is told otherwise | `test_engine_service.py:350` (default wrapper), `:356` (`--lan`), `:365` (one `--host`, from the variable), `:178` | the real installer, `--print-wrapper`; the launcher's exec line as a source pin | I8, I11, I7, I9, L2, L3, L4 | GREEN |
| `make run` binds loopback (note 1) | `test_engine_service.py:435` | source pin on the Makefile | X1 | GREEN |
| A bind beyond loopback with no list refuses to start (clause 2) | `test_engine_host.py:58`; `test_engine_service.py:374` (the real launcher, run to its refusal) | live: the launcher, its preflight and `validate_startup_config` | V1, V2, V3, L1, L5 (V4: see N8) | GREEN |
| A reinstall keeps the mode it finds, and says so (note 2) | `test_engine_service.py:454` (a plain install over a LAN wrapper, written and announced); `:399` (kept, closed, loopback stays loopback) | live: the full install, against the module's `_install` stubs and a scratch HOME | I15, I13, I14, I1, I2 | GREEN |
| `--no-lan` closes it (note 2, note 7) | `test_engine_service.py:399` | **a stand-in: `--no-lan --print-wrapper`**. A real `--no-lan` install is never run. | none singly (I3 is equivalent) | GREEN, but I16 and I17 survive: **T9** |
| Only writing the wrapper reads it (third review M12) | `test_engine_service.py:421` (`--print-plist`), `:472` (`--deploy-only`) | the real installer, scratch HOME | I5 | GREEN |
| The written wrapper is the owner's alone (#86) | `test_engine_service.py:388` | live: a full install against the stubs | I6 | GREEN |
| With no Host list, a request arriving on a network address is refused (note 1) | `test_engine_host.py:72`, `:53`, `:106` | the real ASGI app through `TestClient` (its `scope["server"]` is synthetic); `_arrived_off_loopback` executed | H1, H9, H10, H14, H15 | GREEN (a real non-loopback socket: N10) |
| An exposed engine refuses a Host not on its list (clause 1) | `test_engine_host.py:45`, `:38`, `:81`, `:90`, `:96` | the real ASGI app with its middleware | H3, H4, H5, H13, H13b | GREEN, **on `/v1/categories` only**: H16 survives, **T8** |
| The app's engine address is set per build, loopback when unset (clause 4) | `EngineClientTests.swift:552`, `:594`; `test_engine_address.py:21`, `:30`, `:39`, `:48`, `:61` | `engineURL` executed; the build chain (`ENGINE_URL` → plist → `Bundle.main`) held by source pins | S1, S2, S3, S15, S14, P1, X5, X6, X7 | GREEN; the empty-host guard never runs: S2b survives, **T11** |
| …and shown under a failure to reach it (notes 8, 10) | `EngineClientTests.swift:559`, `:569`, `:578`, `:587`, `:290`; `LanguageTests.swift:443`; `test_engine_address.py:73` (view pin) | `addressNote` executed; the view held by a source pin (no test runs `ContentView`) | S4–S10, S8b, S13, C4, C10 | GREEN; C5 (T4, #69) and C9 (**T12**) survive; the `unknown_host` link is untied: U1, **T10** |
| `ios/app.sh`'s simulator build is always loopback (note 5) | `test_engine_service.py:443` | source pin on the build line | X2 | GREEN |
| The redirect guard compares hosts without case (second review K3) | `EngineClientTests.swift:53`, `:61`; `test_ios_client_contract.py:504` | `SameHostOnly` executed through its delegate method | S11, S12 | GREEN |
| Nothing new leaves the phone (D-126; D-160 as amended) | `test_router_hints.py:229`, `:302`; `client-decls` | the client's sources, and the compiler's resolved declarations | not mutated (the wave adds no request) | GREEN |
| The app runs on the owner's iPhone | the owner's own run (`docs/owner-iphone.md`) | none possible in this seat | n/a | PARTIAL, as the PRD row says |

Every test file above cites REQ-DEV-001: in its module docstring (`test_engine_host.py:1`,
`test_engine_address.py:1`), its section header (`test_engine_service.py:347`), or a comment on the
class or test (`EngineClientTests.swift:54`, `:291`, `:550`, `:579`; `LanguageTests.swift:440`). The
PRD row's 28 evidence line numbers each point at the test they name (checked one by one at
`ed8b7e7`).

**The live engine, run by this seat.**
- uvicorn 0.54.0 ran from the worktree on 127.0.0.1 only, on ports 8161, 8162 and 8163. A copy of
  `advisor.db` was served, with the nightly switch unset.
- Each server was stopped with SIGTERM, and a connect afterwards found no listener.
- The requests were raw HTTP/1.1, so the Host header was exactly what was sent (scratch
  `t2work/logs/probe.json`).

| Host header sent | no list | `127.0.0.1,localhost` | LAN list (four names) |
|---|---|---|---|
| `127.0.0.1:<port>`, `localhost:<port>`, `127.0.0.1` | 200 | 200 | 200 |
| `evil.example`, `127.0.0.1.evil.example:<port>` | 200 | 400 `unknown_host` | 400 |
| `UMUT-MACBOOK-PRO-2.LOCAL:8080`, `192.168.0.26:8080` | 200 | 400 | 200 |
| `[::1]:8080` | 200 | 400 | 400 |
| empty, or no Host header | 200 | 400 | 400 |
| `/health`, Host `127.0.0.1` / Host `evil.example` | 200 / 200 | 200 / 400 | 200 / 400 |

- Every response, refusals included, carried `X-Content-Type-Options: nosniff`.
- A fourth start used the strict lane: `APP_ENV=production`, `MODEL_RANKING_BIND=0.0.0.0` and no list.
  It never listened, exited 1, and its log names `MODEL_RANKING_ALLOWED_HOSTS`. The import-time
  check fails closed.
- uvicorn fills `scope["server"]` from `getsockname()` (`uvicorn/protocols/utils.py:30-44`), so the
  no-list rule reads the address the connection arrived on.

## Red→green on reported symptoms

The first Tester verified all five pairs. This seat sampled three of them.
- Each commit was extracted with `git archive` into a scratch tree, with the venv linked and
  `PYTHONPATH` pointed at that tree's `src`, so the launcher's own Python imported that commit's code.
- HOME was a scratch folder.
- A `sitecustomize` guard refused any `python -m uvicorn` not on 127.0.0.1 above port 8100.
- "Added" means the `def test_` lines the red commit adds.

| pair | added tests: red / fix | notes |
|---|---|---|
| `41be53a` → `eccd5b1` | 7 of 9 FAIL / all 9 PASS | The two that pass on red are correct guards: the positive control `test_a_host_on_the_list_is_served`, and `test_the_installed_wrapper_is_the_owners_alone`, whose `chmod 700` predates the wave. **At this red commit the launcher test asked for an engine on 127.0.0.1:8080; the guard refused it** (exit 3), so the test failed without starting anything. |
| `b718f70` → `8e54068` | 5 of 8 FAIL / all 8 PASS | The network-arrival rule (B1), the reinstall keep (M2), `make run`, `app.sh` and the bundle id all fail on red. The plist key pin and the M5 case and empty-Host guards pass on red, as guards should. |
| `456eac2` → `8cfdd98` | 1 of 1 FAIL / PASS (Python); Swift `testAFailureWhoseCauseIsTheAddressShowsIt`: 2 assertion failures on red (`unknown_host`, `insecureTransport`), 0 on the fix | Every Swift failure is an XCTest assertion, not a compile error. |

**Weakened or deleted tests.** I read every line the range removes under `tests/` and
`ios/EngineTests/`.
- `_deploy` gains a scratch HOME. `"starting on :"` becomes the stricter `"starting on"`.
- The launcher and `SameHostOnly` pins follow their code.
- `_install` gains `**extra`.
- The view pin's `_code` call now also strips `/* */`. That is stricter, and it closes the first
  Tester's T3.
- Two comments are reworded to cite REQ-DEV-001.
- No test was skipped, weakened or deleted. The Swift manifest gains 9 names and loses none.

## Suite result
- **`make check-fast` at `ed8b7e7`: PASS, rc 0, in 54 s.** It was run with this seat's guards in
  front: `launchctl`, `xcrun simctl`, `curl` and `lsof` refused, and `git` refused to reach any
  network remote. No guard fired.
  - lint, typecheck and records: PASS.
  - test: **1563 passed, 23 skipped**. Total coverage 91.57 %.
  - swift-test: **363 tests, exactly the manifest**.
  - client-decls: PASS, 15 files in 4 configurations.
- **`make wave-check-all`: PASS, rc 0.** 47 records validated.
- **Python coverage on touched code** (permission-matrix §11).
  - Method: `pytest tests/unit -n auto --cov=src/app --cov-branch`, with
    `MODEL_RANKING_REQUIRE_ARTIFACT=1` and a scratch HOME, on `git archive` copies of `e82011b` and
    `ed8b7e7`, each with the same `advisor.db` (sha256 `5c6977a9c67c…`).
  - **`src/app/adapter/main.py`: 97.06 % → 97.27 %, up.**
    - Base: 402 statements, 12 missing; 108 branches, 3 missing.
    - Head: 433 statements, 12 missing; 116 branches, 3 missing.
    - Every line the wave added (`main.py:545-578`, `:646-653`, `:750-762`) runs. The misses are the
      same twelve pre-wave lines, moved by the insertions.
  - No other module under `src/app` dropped. It is the only touched Python module under `src/`.
- **Swift coverage** was not measured. §11 reads Python modules. Every new Swift function
  (`engineURL`, `addressNote`, `UIText.engineAddress`) is executed by a named test above.

## Mocks / contract tests
- **launchd, curl, lsof and plutil.** One stub set, `_STUBS` (`test_engine_service.py:237-255`),
  reached through one helper, `_install` (`:258`).
  - `ed8b7e7`'s new install test reuses `_install` through its new `**extra`.
  - This seat's proposed T9 test extends the same helper with `*flags`.
  - No parallel stub exists.
- **The engine over HTTP, as the app sees it.** `StubProtocol` (`EngineClientTests.swift`) is the
  one Swift stub.
  - The wave adds one error code, `unknown_host`, and the app now branches on it
    (`EngineClient.swift:151`). That is a first.
  - No contract test ties the app's literal to the engine's: **T10**.
- **macOS `scutil` and `ipconfig`.** Tests pass `ENGINE_LAN_NAME` and `ENGINE_LAN_IP` instead.
- No new external integration.

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **T8** `src/app/adapter/main.py:750-762`; `tests/unit/test_engine_host.py:38-106`. **The Host check is
  proven on one path.**
   1. Every Host test asks `/v1/categories`.
   2. H16 makes the refusal apply only when the path starts with `/v1`. Under it, `/health` and any
      other path serve every Host, and the no-list network rule no longer covers them. H16 passes the
      whole suite (1563 passed).
   3. The code is right today: the live probe refuses `/health` with Host `evil.example`. But D-171
      clause 1 says "a request", and exempting `/health` for monitoring is the regression this would
      let through in silence.
   4. **Why only MINOR:** the data (`/v1`) is proven on both rules. `/health` serves public build and
      freshness facts.
   5. **The fix:** one parametrized test, below (`test_every_path_is_behind_the_host_check`). It
      kills H16.
- **T9** `scripts/install_engine_service.sh:46-55`, `:196-197`; `tests/unit/test_engine_service.py:399`;
  `docs/owner-iphone.md:57`. **`--no-lan` is never run as the install the owner runs, and "home
  network: off" is asserted nowhere.**
   1. D-171 note 7 makes `--no-lan` the one control while the network is open, and the owner's page
      says to run `scripts/install_engine_service.sh --no-lan`. That is a full install.
   2. The citing test, `:399`, runs `--no-lan --print-wrapper`. `_install` cannot pass a flag.
   3. The fault I16 removes the closing "home network: off, loopback only" line, the "says so" of a
      closed or loopback reinstall. It passes the whole suite.
   4. The fault I17 makes the close apply only when a mode argument is given, by two coordinated
      edits. A real `--no-lan` install then keeps `0.0.0.0` and prints "kept". It passes the whole
      suite.
   5. **Why this is not T1 again (BLOCKING there):**
      1. T1 was an existing branch that depended on the mode, which `--print-wrapper` never took.
      2. The close decision (`:51`, `:55`) does not depend on the mode at all, so `:399` runs every
         line of it.
      3. The write itself is proven by `:454` (the LAN case) and `:388` (the loopback case).
      4. I17 has to add a mode dependence to survive. Every single-edit fault on this path is killed
         or equivalent (I3, N7).
   6. **The fix:** one test, below (`test_no_lan_closes_the_home_network_on_the_install_the_owner_runs`),
      plus `*flags` on `_install`. It kills I16 and I17.
- **T10** `ios/ModelRanking/Engine/EngineClient.swift:151`; `src/app/adapter/main.py:759`;
  `tests/unit/test_engine_host.py:49`, `:77`; `ios/EngineTests/EngineClientTests.swift:573`, `:582`.
  **The code the app matches is not tied to the code the engine sends.**
   1. The failure screen shows the address under the engine's own refusal (D-171 note 10) because
      Swift compares `code == "unknown_host"`.
   2. The engine's tests hold their literal, and the Swift tests hold theirs. Nothing reads one
      against the other.
   3. The fault U1 renames the engine's code to `host_not_allowed`, and the engine's own two
      assertions follow. It passes all 1563 Python tests and all 363 Swift tests. The renamed-host
      case D-171 note 10 describes would then show no address.
   4. This is the first time the app branches on an engine error code.
   5. **The fix:** one test, below (`test_the_app_matches_the_code_the_engine_sends_for_an_unknown_host`).
      It reads the code from the live ASGI app and pins the Swift comparison to it. It kills U1.
- **T11** `ios/ModelRanking/Engine/EngineClient.swift:172`; `ios/EngineTests/EngineClientTests.swift:594-600`.
  **The empty-host guard never runs.**
   1. Measured with `swift` on this Mac:
      1. `URL(string: "http://")`, `"http:///v1"` and `"http:"` have a nil host;
      2. `"http://:8080"`, `"http://@:8080"` and `"https://:443/x"` have an empty one.
   2. The fallback test's only http value is `"http://"`, so `!host.isEmpty` is never reached. The
      fault S2b drops it and passes `swift test` (363) and the Python suite.
   3. Under S2b, an override that lost its name (`ENGINE_URL = http:/$()/:8080`) is used as-is instead
      of falling back. The plan (`m18-wave-1-plan.md`, "Design") promises the fallback for "an
      http(s) URL with a host".
   4. **The fix:** add `"http://:8080"` to the list at `:596`, below. It kills S2b.
- **T12** `ios/ModelRanking/ContentView.swift:671-674`; `tests/unit/test_engine_address.py:73-85`. **A
  second shape of T4: the pin cannot see a surrounding condition.**
   1. The fault C9 wraps the address block in `if error.recovery == nil { … }`.
   2. The four failures that carry an address (`unreachable`, `timedOut`, `offline`,
      `insecureTransport`) all have a recovery line (`EngineClient.swift:68-87`), so the address would
      never show for them.
   3. It typechecks (`make client-decls`: PASS under the mutant), and it passes the pin and the whole
      suite.
   4. Same cause as T4 (C5, `.hidden()`, still surviving): no test runs `ContentView`.
   5. **The fix:** fold it into #69 beside T4. A view test that renders `failure(_:)` kills both. I
      wrote no pin for it, for the first Tester's reason: each pin names one more shape to guess.

## Notes (no change required by this verdict)

- **N6. Equivalent: H17.** Dropping the refusal's own `X-Content-Type-Options` line changes nothing.
  - `_no_sniff` is registered after `_known_host` (`main.py:765`), so Starlette makes it the outer
    middleware, and it sets the header on every response, the refusal included.
  - Measured: `test_engine_host.py:50` still sees the header under H17, and the live probe shows it on
    every refusal. The line is redundant, not wrong.
- **N7. Equivalent: I3** (the first Tester's N1), confirmed again. `install_engine_service.sh:55`
  closes the mode whatever `:51` decides.
- **N8. V4 is killed, but only by accident.** V4 reads an unset `MODEL_RANKING_BIND` as `0.0.0.0`.
  - Four older tests catch it because they assert the whole startup-problem tuple
    (`test_api_config.py`, `test_board_standings.py`, `test_stage40_minors.py`). None cites D-171.
  - Under V4, `ios/app.sh`'s by-hand launcher would refuse to start.
  - A direct test is offered below (`test_an_unset_bind_is_loopback`). It is optional.
- **N9. C5 still survives, as T4 said.** The caller reports T4 is on #69. This seat did not read
  GitHub.
- **N10. The first Tester's N3 and N4 still stand.**
  - The no-list refusal is shown through a real socket only for loopback. A non-loopback socket needs
    a LAN bind, which this seat may not make. uvicorn's `getsockname` path was read again
    (`uvicorn/protocols/utils.py:30-44`), and the loopback probe repeated.
  - No Xcode build was run. The plist chain is held by pins (X5, X6, X7, P1, S14), and by the plan's
    spike and the owner's first run.
- **N11. For the milestone's closure security seat (D-172), not a test gap.**
  - With no list, loopback serves every Host. The probe's first column shows it.
  - So `make run` and `ios/app.sh`'s launcher are not shielded from a page that rebinds a name to
    127.0.0.1. Only the service, which always sets a list, is.
  - D-171 clause 1 says exactly this ("unset … every Host is served"). It is recorded here so the
    closure seat reads it on purpose.

## K.9 candidates spotted outside this wave's scope
- **K6** The first Tester's K1 (`tests/unit/test_router_hints.py:31-34`: `_code` keeps `/* */`) is
  unchanged. `test_engine_address.py:81` now works around it locally.

## Fault injection (HIGH: mandatory)

**Harness:** scratch `t2work/mut.py`. For each fault it:
1. checks every file it touches against `HEAD` (`git hash-object` = `git rev-parse HEAD:<file>`);
2. records each file's sha256 and saves its bytes;
3. makes exact edits, each of which must match a stated number of times (once, unless noted);
4. runs the named tests (Python), or the Python pins plus `swift test --filter` on the four affected
   classes (Swift). If nothing fails, it runs the whole of `tests/` with `-n auto`, plus the whole of
   `swift test` for Swift faults, and `make client-decls` for view faults, to show they typecheck;
5. writes the original bytes back **in place**, never with `git checkout` or `restore`;
6. asserts that sha256 equals the pre-edit hash, that `git hash-object` equals HEAD's blob, and that
   `git diff --quiet` holds.

All 63 rows of the log (`t2work/logs/mutants.jsonl`) say `restored: true`. Every Swift kill is an
XCTest assertion, never a compile error. Afterwards, all 671 tracked files match the pre-run sha256
baseline, `git status --porcelain` is empty, and `git diff --quiet` holds.

**Restore hashes** (sha256 prefix, pre = post, and the HEAD blob that `git hash-object` matched):

| file | faults | sha256 (pre = post) | HEAD blob |
|---|---|---|---|
| `src/app/adapter/main.py` | 17 | `8de4876503d4` | `35171db171` |
| `scripts/engine_service.sh` | 5 | `cc17145abc38` | `522a1b539a` |
| `scripts/install_engine_service.sh` | 14 | `1e95ef214a6b` | `7541de9c4d` |
| `ios/ModelRanking/Engine/EngineClient.swift` | 16 | `8db356862dc9` | `e5f3c54157` |
| `ios/ModelRanking/Engine/Language.swift` | 1 | `837d756a40ee` | `84d144583a` |
| `ios/ModelRanking/ContentView.swift` | 4 | `c2f4a3ff1d11` | `705a1170a5` |
| `ios/Config/Info.plist` | 2 | `d7ead6196aaa` | `3e7b7b968f` |
| `ios/Config/Engine.xcconfig` | 2 | `ac803fa1b130` | `81ee48b12e` |
| `ios/app.sh` | 1 | `87fbebb2c27b` | `a78263dc44` |
| `Makefile` | 1 | `8678e690d706` | `4d9d0b876c` |
| `tests/unit/test_engine_host.py` (U1 only) | 1 | `7eca801a563e` | `18cd5c8148` |

**The faults.**
- "t1:" marks a replay of a fault the first Tester named. It was rebuilt from that verdict's
  description and edited here, not taken from its harness.
- "t2" marks a fault new to this seat.
- **The first Tester's eight survivors (I15, H13, H14, C4, S8, I13, I14, I5) are all KILLED now**, each
  by a test `ed8b7e7` added. C5 is its T4, which is not a test this wave owes.

| id | origin | the fault | result | killed by |
|---|---|---|---|---|
| H1 | t1:H1 | no-list arrival rule off | KILLED | `test_engine_host.py:72` |
| H3 | t1:H3 | list check off | KILLED | `:45` (4 Hosts) |
| H4 | t1:H4 | prefix match instead of exact | KILLED | `:45` |
| H5 | t1:H5 | port not stripped | KILLED | `:38` |
| H9 | t1:H9 | the peer's address in place of the local one | KILLED | `:72` |
| H10 | t1:H10 | `is_private` in place of `is_loopback` | KILLED | `:72`, `:106` |
| H13 | t1:H13 | bracketed IPv6 Host kept whole | KILLED | `:96` |
| H13b | t2 | an unclosed bracket stripped and served | KILLED | `:96` |
| H14 | t1:H14 | no local address counted as a network | KILLED | `:106` |
| H15 | t2 | a name as the local address counted as a network | KILLED | `:53`, `:106` |
| **H16** | t2 | **the Host check applies only to `/v1` paths** | **SURVIVED** (1563 passed) | **T8** |
| H17 | t2 | the refusal's own nosniff line dropped | SURVIVED, equivalent | **N6** |
| V1 | t1:V1 | the startup bind check off | KILLED | `:58`; `test_engine_service.py:374` (guard refused the exec) |
| V2 | t1:V2 | `and` → `or` in the startup check | KILLED | `test_engine_host.py:58` |
| V3 | t1:V3 | `0.0.0.0` counted as loopback | KILLED | `:58` |
| V4 | t2 | an unset bind read as `0.0.0.0` | KILLED, by unrelated tests only | `test_api_config.py`, `test_board_standings.py`, `test_stage40_minors.py` (**N8**) |
| L1 | t1:L1 | the preflight's result ignored | KILLED | `test_engine_service.py:374` (guard refused the exec) |
| L2 | t1:L2 | a second `--host 0.0.0.0` | KILLED | `:365` |
| L3 | t1:L3 | the exec's default bind `0.0.0.0` | KILLED | `:178`, `:365` |
| L4 | t2 | the exec ignores the bind (`--host 127.0.0.1`) | KILLED | `:178`, `:365` |
| L5 | t2 | the preflight runs without the bind variable | KILLED | `:374` (guard refused the exec) |
| I15 | t1:I15 | the install forgets the mode | KILLED | `:454` |
| I13 | t1:I13 | the "kept" line removed | KILLED | `:454` |
| I14 | t1:I14 | the closing "home network: on" line removed | KILLED | `:454` |
| I5 | t1:I5 | `--deploy-only` reads the live wrapper | KILLED | `:472` |
| I1 | t1:I1 | the keep check off | KILLED | `:399`, `:454` |
| I2 | t1:I2 | any wrapper opens the network | KILLED | `:399` |
| I3 | t1:I3 | `NO_LAN = no` dropped from the keep check | SURVIVED, equivalent | **N7** |
| **I16** | t2 | **the closing "home network: off" line removed** | **SURVIVED** (1563 passed) | **T9** |
| **I17** | t2 | **`--no-lan` closes only when a mode is given (two edits)** | **SURVIVED** (1563 passed) | **T9** |
| I6 | t1:I6 | wrapper `chmod 755` | KILLED | `:388` |
| I7 | t1:I7 | the `.local` name not lower-cased | KILLED | `:356` |
| I8 | t1:I8 | the default bind `0.0.0.0` | KILLED | `:350`, `:399` |
| I9 | t1:I9 | the LAN address left off the list | KILLED | `:356`, `:454` |
| I11 | t1:I11 | no Host list by default | KILLED | `:350`, `:356`, `:454` |
| S1 | t1:S1 | any URL scheme accepted | KILLED | `EngineClientTests.swift:594` |
| S2 | t1:S2 | the host check dropped | KILLED | `:594` |
| **S2b** | t2 | **only the empty-host check dropped** | **SURVIVED** (363 Swift, 1563 Python) | **T11** |
| S3 | t1:S3 | always loopback | KILLED | `:552` |
| S15 | t2 | https refused | KILLED | `:552` |
| S14 | t1:P2 | `localDefault` reads nothing | KILLED | `test_engine_address.py:48` |
| S8 | t1:S8 | `addressNote` always English | KILLED | `EngineClientTests.swift:578` |
| S8b | t2 | English only for the `unknown_host` refusal | KILLED | `:578` |
| S4 | t1:S4 | `unknown_host` shows no address | KILLED | `:569`, `:578` |
| S5 | t1:S5 | every refusal shows the address | KILLED | `:587` |
| S6 | t1:S6 | only `.unreachable` shows it | KILLED | `:559`, `:569`, `:578` |
| S7 | t1:S7 | `insecureTransport` shows no address | KILLED | `:569`, `:578` |
| S9 | t1:S9 | the host only, not the URL | KILLED | `:559`, `:569`, `:578` |
| S10 | t1:S10 | the Turkish line in English | KILLED | `LanguageTests.swift:443`; `EngineClientTests.swift:578` |
| S11 | t1:S11 | redirect compared with case | KILLED | `EngineClientTests.swift:53`; `test_ios_client_contract.py:504` |
| S12 | t2 | redirect host compared by prefix | KILLED | `EngineClientTests.swift:61`; `test_ios_client_contract.py:504` |
| S13 | t1:S13 | the unreachable detail drops the address | KILLED | `EngineClientTests.swift:290` |
| C4 | t1:C4 | the view block `/* */`-commented | KILLED | `test_engine_address.py:73` |
| C5 | t1:C5 | `.hidden()` on the line | SURVIVED (typechecks) | the first Tester's T4, #69 (**N9**) |
| **C9** | t2 | **the line shown only when there is no recovery line** | **SURVIVED** (typechecks) | **T12** |
| C10 | t2 | the view shows loopback's address, not the client's | KILLED | `:73` |
| P1 | t1:P1 | plist key `EngineUrl` | KILLED | `:30`, `:48` |
| X7 | t1:X7 | `NSAllowsArbitraryLoads` added | KILLED | `:30` |
| X5 | t1:X5 | the optional include dropped | KILLED | `:21` |
| X6 | t1:X6 | the default `ENGINE_URL` is the owner's Mac | KILLED | `:21` |
| X2 | t1:X2 | `app.sh` drops `ENGINE_URL` | KILLED | `test_engine_service.py:443` |
| X1 | t1:X1 | `make run` binds `0.0.0.0` | KILLED | `:435` |
| **U1** | t2 | **the engine renames `unknown_host`, and its own tests follow** | **SURVIVED** (1563 Python, 363 Swift) | **T10** |

**Kill rate (advisory, HIGH): 54 of 61 non-equivalent faults, 88.5 %.** No mutation runner is wired
for this stack, so this hand-built set stands in for one.

## Tests added/extended this review

**None in the repository.** This seat may change only this file. Each test below was written into a
scratch copy of `ed8b7e7` (scratch `t2work/trees/prop`; the whole diff is
`t2work/proposed-tests.diff`).
- Each is GREEN there, and the copy's whole suite passes: 1569 passed, 23 skipped.
- Each was run against its fault in that copy, and each goes red (`t2work/logs/propcheck.txt`).
- The installer test uses the module's `_install` stubs and a scratch HOME.

**T8** (kills H16). In `tests/unit/test_engine_host.py`:
```python
@pytest.mark.parametrize("path", ["/health", "/v1/categories", "/no-such-route"])
def test_every_path_is_behind_the_host_check(db: Path, monkeypatch: pytest.MonkeyPatch, path: str) -> None:
    """W1 second Tester T8 (REQ-DEV-001, D-171 clause 1): the check runs before any route."""
    monkeypatch.setenv(HOSTS, LIST)
    refused = TestClient(adapter.app, base_url="http://evil.example").get(path)
    assert refused.status_code == 400 and refused.json()["error"]["code"] == "unknown_host", path
    monkeypatch.delenv(HOSTS)
    arrived = TestClient(adapter.app, base_url="http://192.168.0.26:8080").get(path)
    assert arrived.status_code == 400 and arrived.json()["error"]["code"] == "unknown_host", path
```

**T9** (kills I16 and I17). In `tests/unit/test_engine_service.py`, `_install` gains `*flags`. Its
signature becomes `(tmp_path, repo, health, *flags, **extra)`, and it runs
`["/bin/bash", str(INSTALLER), *flags]`. Then:
```python
def test_no_lan_closes_the_home_network_on_the_install_the_owner_runs(tmp_path: Path) -> None:
    """W1 second Tester T9 (REQ-DEV-001, D-171 note 7): `--no-lan` is the one control while the network
    is open, and the owner runs it as an install. launchctl, curl and plutil are stubs; HOME is scratch."""
    repo = _scratch_repo(tmp_path)
    wrapper = tmp_path / "home" / "Library" / "Application Support" / "model-ranking" / "engine_service.sh"
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text('export MODEL_RANKING_BIND="0.0.0.0"\n', encoding="utf-8")
    done = _install(tmp_path, repo, f'{{"status":"ok","build":"release-{_sha(repo)}"}}', "--no-lan",
                    ENGINE_LAN_NAME="probe-mac", ENGINE_LAN_IP="192.168.9.9")
    assert done.returncode == 0, done.stdout + done.stderr
    written = wrapper.read_text(encoding="utf-8")
    assert 'export MODEL_RANKING_BIND="127.0.0.1"' in written, written
    assert 'export MODEL_RANKING_ALLOWED_HOSTS="127.0.0.1,localhost"' in written, written
    assert "home network: kept" not in done.stderr, done.stderr
    assert "home network: off" in done.stdout, done.stdout
```

**T10** (kills U1). In `tests/unit/test_engine_host.py`:
```python
def test_the_app_matches_the_code_the_engine_sends_for_an_unknown_host(db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """W1 second Tester T10 (REQ-DEV-001, D-171 note 10): the app shows the address under this refusal
    by matching its code in Swift; the code is read from the engine, not typed twice."""
    monkeypatch.setenv(HOSTS, LIST)
    code = TestClient(adapter.app, base_url="http://evil.example").get("/v1/categories").json()["error"]["code"]
    client = (Path(__file__).resolve().parents[2] / "ios" / "ModelRanking" / "Engine" / "EngineClient.swift").read_text(
        encoding="utf-8")
    assert f'code == "{code}"' in client, code
```

**T11** (kills S2b). In `ios/EngineTests/EngineClientTests.swift:596`, add `"http://:8080"` to the
fallback list. It names no new test, so the manifest is unchanged.

**N8** (optional; kills V4 directly). In `tests/unit/test_engine_host.py`:
```python
def test_an_unset_bind_is_loopback(db: Path) -> None:
    assert not any(HOSTS in problem for problem in adapter.validate_startup_config("test"))
```

**T12:** no test here; it goes to #69 with T4.

## Safety (this seat's rules)

- **Neither installer script was executed by this seat.** `scripts/install_engine_service.sh` and
  `scripts/remove_engine_service.sh` ran only inside `tests/unit/test_engine_service.py`, in the
  gate, the red replays, the fault runs and the scratch copy.
  - The pytest runs had a scratch HOME, except the gate.
  - Every full install went through `_install`, with its own `launchctl`, `curl`, `plutil` and
    `lsof` stubs first on PATH.
  - Before the fault runs I confirmed that no installer fault touches the `--print-*` early exits, so
    `_installer(...)` (HOME `/Users/probe`) still printed and exited.
  - Behind that, this seat's own PATH refused `launchctl`, `curl` and `lsof`, and refused any `git`
    fetch or push to a network remote.
- **No `launchctl`, `xcodebuild` or `simctl` ran, and nothing ran on the simulator.**
  - `xcrun` was filtered: `simctl`, `xcodebuild` and `devicectl` are refused. It was used only by
    `client-decls`, for `--show-sdk-path` and `swiftc -typecheck`.
  - `swift test` and one `swift` script ran on macOS only.
  - **"BLOCKED in this review seat" appeared exactly once, caused on purpose:** one `launchctl print`
    to prove the provided guard refuses (exit 97).
  - This seat's own guard refused one `git fetch` and one `xcrun simctl list`, both sent on purpose
    to test it. It refused nothing else.
- **Nothing bound beyond loopback, and nothing bound 8080.**
  - The probe engines bound 127.0.0.1:8161-8164 and were stopped with SIGTERM. A connect afterwards
    found no listener.
  - A `sitecustomize` guard refused every `python -m uvicorn` not on 127.0.0.1 above port 8100, with
    `os._exit(3)`, never `abort`. It fired twice on purpose, to test it (0.0.0.0:8150 and
    127.0.0.1:8080). Otherwise it fired four times, each before any engine code ran:
    - `41be53a`'s red launcher test, asking for 127.0.0.1:8080;
    - V1, L1 and L5, each asking for 192.0.2.1:8080.
  - No test reached the network.
- **Changes.** No commit, no push, no GitHub. The only tracked change in the worktree is this file.
  Every fault was reverted in place and checked byte-identical (table above). Scratch work lives
  outside the worktree, under the session's scratchpad folder `t2work/`.
