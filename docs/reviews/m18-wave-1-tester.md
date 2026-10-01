---
record_type: review
id: m18-wave-1-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-01
---
# Wave 1 Tester Review (m18)

**Reviewer:** Tester subagent (fresh eyes). This seat wrote none of the wave's code, tests or records.
It is not one of the wave's three Code-Reviewers.
**Independent:** yes
**Date:** 2026-10-01
**Commit range:** `e82011b..8cfdd98`: 16 commits, 26 files. `e82011b` is the merge-base with
`origin/main`. The range holds the three Code-Reviewer verdicts (`e05ae15`, `78aa6d1`, `8e6232a`), D-172
(`cc78cb7`), and three red-then-fix pairs (`b718f70`→`8e54068`, `a7f4b3b`→`a04fdd5`,
`456eac2`→`8cfdd98`). **The last pair came after the third review, so no Code-Reviewer has read it.**
This seat is the first to see `456eac2` and `8cfdd98`.
**Risk tier:** HIGH (`docs/plans/m18-plan.md:39`, `:137`; `docs/plans/m18-wave-1-plan.md:11`)
**Code-Reviewer verdict:** PASS-WITH-MINORS (`docs/reviews/m18-wave-1-review.md`, round 3, `8e6232a`),
so this seat runs. D-172 removes the per-wave security pass; the fault injection below is still owed.
**Model routing (HIGH, advisory):**
- Author family: Claude (the commits carry `GP-Agent: claude-code/local-lane`; five do not, which the
  third review already raised as its M14).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second model family is available to this seat.
- Fresh context: this seat started from the role file, `practices.md` and `permission-matrix.md` §11,
  all read from `e82011b`. It then read the plans, D-171 and D-172, REQ-DEV-001, the owner's page, the
  three verdicts and the diff. It has no memory of any authoring or reviewing session.
**Base-pinned policy:** `git diff --stat e82011b..8cfdd98 -- .claude .agents permission-matrix.md
.github epb.html or.md` is empty. `docs/permission-matrix.md` does not exist at the base; the matrix is
`permission-matrix.md` at the repository root. `AGENTS.md` changes only under D-172.

## Verdict
BLOCKING

**Two things block. Both are test gaps, not defects: the code at `8cfdd98` does the right thing in
each case. The fix for each is a test, and both tests are written below and proven in a scratch copy.**

- **T1. The claim "a reinstall keeps the mode it finds" is not proven on the path a reinstall takes.**
  - This is a REQ-DEV-001 clause. Its citing test, `test_engine_service.py:398`, runs the installer
    with `--print-wrapper`.
  - The redeploy after every merge (D-170) runs the installer with no argument. Since `8cfdd98`,
    those are two separate branches of one condition (`install_engine_service.sh:50`).
  - Mutant I15 drops the no-argument branch. The owner's next redeploy would then put the phone's
    engine back on loopback without a word: the first review's M2, back again. **I15 passes the whole
    unit suite.**
- **T2. Coverage dropped on a touched module.** `src/app/adapter/main.py` falls from **97.06 % to
  96.54 %**. `permission-matrix.md` §11 classes that as BLOCKING.
  - Two new branches of the Host check never run: the bracketed IPv6 Host at `main.py:564`, and a
    connection with no local address at `:574`.
  - Mutants H13 and H14 change each branch and pass the whole unit suite.

**Everything else holds.**
- `make check-fast` passes (rc 0), and so does `make wave-check-all`.
- Every red commit's new tests fail on that commit and pass on its fix.
- A real engine on 127.0.0.1 behaves as D-171 says, with no list, with the service's list and with
  the LAN list.
- **68 mutants: 58 killed, 1 equivalent, 9 survived.** Of the 9 survivors:
  - three are the two blockers (I15; H13 and H14);
  - six are the MINORs T3 to T7.
- **The third Code-Reviewer's 29 mutants were replayed: 28 killed, 1 equivalent.** That includes
  M11's survivor, which is now killed.

**What this verdict needs to turn PASS:** add the two tests in "Tests added/extended this review"
(T1, T2) and rerun the gate. The same section has the four MINOR tests; three are a few lines each.

## Acceptance-criterion coverage (REQUIRED)

Every test named here is GREEN at `8cfdd98`. Mutant ids are defined under "Fault injection".

REQ-DEV-001 (`docs/prd.md:551`) and D-171, clause by clause. "Entry" says whether the test goes in
through the live entry point, a stand-in for it, or a source pin.

| clause | citing test | entry | mutants killed by it | status |
|---|---|---|---|---|
| The engine binds loopback unless the installer is told otherwise | `test_engine_service.py:349` (default wrapper), `:355` (`--lan`), `:364` (one `--host`, read from the variable), `:178` | the real installer, `--print-wrapper`; the launcher's exec line as text | I8, I10, I11, I12, I7, I9, L2, L3 | GREEN |
| `make run` binds loopback (D-171 note 1) | `test_engine_service.py:434` | source pin on the Makefile | X1 | GREEN |
| A bind beyond loopback with no list refuses to start (clause 2) | `test_engine_host.py:58` (the startup check); `test_engine_service.py:373` (the real launcher, run to its refusal) | live: the launcher, its preflight and `validate_startup_config` | V1, V2, V3, L1 | GREEN |
| **A reinstall keeps the mode it finds** (note 2) | `test_engine_service.py:398` (kept, closed with `--no-lan`, loopback stays loopback) | **a stand-in: `--print-wrapper`**. A plain install over a LAN wrapper is never run. | I1, I2, I3c | **GREEN, but I15 survives: T1** |
| …and says so (note 2) | none | none | none | **I13, I14 survive: T6** |
| Only writing the wrapper reads it (third review M12) | `test_engine_service.py:420` | the real installer, `--print-plist` only | I4 | GREEN; I5 (`--deploy-only`) survives: **T7** |
| The written wrapper is the owner's alone (#86) | `test_engine_service.py:387` | live: a full install against stubs | I6 | GREEN |
| With no Host list, a request arriving on a network address is refused (note 1) | `test_engine_host.py:72`, `:53` | the real ASGI app through `TestClient`. The local address there is `TestClient`'s synthetic `scope["server"]`. | H1, H2, H9, H10 | GREEN; a connection with no address (`main.py:574`) is never run: **T2** |
| An exposed engine refuses a Host not on its list (clause 1) | `test_engine_host.py:45`, `:38`, `:81`, `:90` | the real ASGI app with its middleware | H3, H4, H5, H6, H7, H8, H11, H12 | GREEN; a bracketed IPv6 Host (`main.py:564`) is never run: **T2** |
| The app's engine address is set per build, loopback when unset (clause 4) | `test_engine_address.py:21`, `:30`, `:39`, `:48`, `:61`; `EngineClientTests.swift:552`, `:585` | `engineURL` is executed. The build chain (`ENGINE_URL` → plist → `Bundle.main`) is held by source pins. | X4–X11, P1, P2, S1, S2, S3 | GREEN (the build itself: **N4**) |
| …and shown under a failure to reach it (notes 8, 10) | `EngineClientTests.swift:559`, `:569`, `:578`, `:290`; `LanguageTests.swift:443`; `test_engine_address.py:73` (view pin) | `addressNote` is executed. The view is held only by a source pin, since no test runs `ContentView`. | S4, S5, S6, S7, S9, S10, S13, C1, C2, C3 | GREEN; C4 and C5 survive (**T3**, **T4**); S8 survives (**T5**) |
| `ios/app.sh`'s simulator build is always loopback (note 5) | `test_engine_service.py:442` | source pin on the build line | X2, X3 | GREEN |
| The redirect guard compares hosts without case (second review K3) | `EngineClientTests.swift:53`; `test_ios_client_contract.py:504` | executed (`SameHostOnly` through a stub session) | S11, S12, P3 | GREEN |
| Nothing new leaves the phone (D-126, D-160 as amended) | `test_router_hints.py:229`, `:302`; `client-decls` | the client's sources, raw, and the compiler's resolved declarations | not mutated (the wave adds no request) | GREEN |
| The app runs on the owner's iPhone | the owner's own run (`docs/owner-iphone.md`) | none possible in this seat | n/a | PARTIAL, as the PRD row says |

**The live engine, run by this seat.** uvicorn 0.54.0 ran from a scratch copy of `8cfdd98` on
127.0.0.1 only, on ports 8141, 8142 and 8143, with the nightly switch unset. Each server was stopped
with SIGTERM, and no listener was left. The requests were raw HTTP/1.1, so the Host header was exactly
what was sent (`tester-w18/logs/probe.json`).

| Host header sent | no list | `127.0.0.1,localhost` | LAN list (four names) |
|---|---|---|---|
| `127.0.0.1:<port>`, `localhost:<port>` | 200 | 200 | 200 |
| `evil.example`, `127.0.0.1.evil.example:<port>` | 200 | 400 `unknown_host` | 400 |
| `UMUT-MACBOOK-PRO-2.LOCAL:8080` | 200 | 400 | 200 |
| empty, or no Host header at all | 200 | 400 | 400 |
| `/health`, Host `127.0.0.1` | 200 | 200 | 200 |

uvicorn fills `scope["server"]` from `getsockname()` of the accepted socket
(`uvicorn/protocols/utils.py:30-44`, `http/h11_impl.py:99`, `httptools_impl.py:108`). So the no-list
rule reads the address a connection arrived on, as D-171 note 1 says. This seat cannot show the
refusal through a real non-loopback socket without binding a LAN address, which it may not do (**N3**).

## Red→green on reported symptoms

Each red commit and its fix were extracted with `git archive` into scratch trees. Every run used a
scratch HOME and the uvicorn guard (see "Safety").

| pair | red commit: the new tests that FAIL | fix: all PASS |
|---|---|---|
| `41be53a` → `eccd5b1` | The Host refusal (`test_engine_host.py`, four foreign Hosts) and the startup check. In `test_engine_service.py`: the default wrapper, the `--lan` opt-in (usage error, exit 2), one `--host` from the variable, and the preflight. **At this red commit the launcher test tried to start a real engine on 127.0.0.1:8080, the owner's port; the guard refused it.** | yes |
| `e94cd7c` → `fee46fd` | The three `test_engine_address.py` tests (the files are missing). The Swift `EngineAddressTests` are red by compilation: `EngineClient` has no member `engineURL`. | yes (Swift: 14 tests, 0 failures) |
| `b718f70` → `8e54068` | B1: a network arrival is served (200, expected 400). M2: the reinstall keep, and `app.sh`'s loopback pin. B1: `make run` binds loopback. M3: the bundle id. Swift `testAnUnreachableEngineNamesTheAddressItTried` fails by assertion. | yes |
| `a7f4b3b` → `a04fdd5` | B2: the view pin. In Swift, 6 assertion failures: `addressNote` is stubbed to nil (3 cases), `engineAddress` to `""` (2), and the case-free redirect (1). | yes |
| `456eac2` → `8cfdd98` | M12: `--print-plist` printed "home network: kept". M10: `testAFailureWhoseCauseIsTheAddressShowsIt` fails twice (`unknown_host`, `insecureTransport`). | yes |

- **Tests that pass on their red commit, correctly.** These are guards for a hole a reviewer found by
  mutant, not repros of a defect:
  - round 1's M4 (the plist key) and M5 (Host case, empty Host);
  - round 2's M7 (`starting on`);
  - round 3's M11 (the view pin);
  - the positive controls and `test_the_installed_wrapper_is_the_owners_alone` (#86's `chmod`).
  - Each is shown to bite by its mutant in the fault table: P1, P2, H6, H7, H8, C3 and I6.
- **Weakened or deleted tests.** I read every line the range removes under `tests` and
  `ios/EngineTests`.
  - `_deploy` gains a scratch HOME.
  - `"starting on :"` becomes `"starting on"`. That is stricter: the old text no longer appeared once
    the echo named the bind.
  - The `--host 127.0.0.1` needle follows the launcher.
  - The `SameHostOnly` pin follows the lower-casing.
  - `.insecureTransport` leaves the "no address" list, as M10 ruled.
  - The plist test's filter moved with the bundle id.
  - **One change is a weakening, by accident (T3).** `456eac2` deleted `test_engine_address.py`'s own
    `_code`, which also removed `/* */` comments, and imported `test_router_hints._code`, which does not.
  - No test was skipped or deleted. The Swift manifest gains 8 names and loses none.

## Suite result
- **`make check-fast` at `8cfdd98`: PASS, rc 0, in 52.5 s** (`tester-w18/logs/check-fast.log`). Run
  with `PYTHONDONTWRITEBYTECODE=1`, the uvicorn guard on, and an `xcrun` filter in front.
  - lint, typecheck and records: PASS.
  - test: **1559 passed, 23 skipped**. Total coverage 91.51 %. coverage-floor passes: 41 modules,
    floor 60 %.
  - swift-test: **362 tests, exactly the manifest**.
  - client-decls: PASS, 15 files in 4 configurations.
- **`make wave-check-all`: PASS, rc 0.** 47 records validated. No M18 wave-close record exists yet.
- **Python coverage on touched code** (permission-matrix §11).
  - Method: `pytest tests/unit -n auto --cov=src/app --cov-branch`, with
    `MODEL_RANKING_REQUIRE_ARTIFACT=1`, on `git archive` copies of `e82011b` and `8cfdd98`, each with
    the same `advisor.db`.
  - **`src/app/adapter/main.py`: 97.06 % → 96.54 %. That is a drop: T2.**
    - Base: 402 statements, 12 missing; 108 branches, 3 missing.
    - Head: 433 statements, 14 missing; 116 branches, 5 missing.
    - The new misses are `:564` and `:574`, and the branches `563→564` and `573→574`.
  - With this seat's two proposed host tests in a scratch copy, it is **97.27 %**, above the base.
  - No other module under `src/app` dropped. The total stays 92 %.
- **Swift coverage** was not measured. §11 reads Python modules.

## Mocks / contract tests
- **The engine over HTTP, as the app sees it.** The wave adds one error code, `unknown_host`, in the
  existing error shape, and no route changes.
  - `test_ios_payload_contract.py` and `test_ios_client_contract.py` pass.
  - The one Swift stub, `StubProtocol` (`EngineClientTests.swift`), is reused. No parallel stub was
    added.
- **launchd, curl, lsof and plutil.**
  - The installer tests use the one stub set, `_STUBS` (`test_engine_service.py:237-255`).
  - The proposed T1 test reuses it through a helper that only adds environment.
  - The real `launchctl` stays the owner's to run (D-170).
- **macOS `scutil` and `ipconfig`.** Tests pass `ENGINE_LAN_NAME` and `ENGINE_LAN_IP` instead.
  - Since `8cfdd98`, no deploy or plist test reaches them: `_deploy` has a scratch HOME (`:103-106`).
  - That half of the guard is unheld (**T7**).
- No new external integration, so no new contract test is owed.

## BLOCKING

- **T1** `scripts/install_engine_service.sh:50`; `tests/unit/test_engine_service.py:398`; `docs/prd.md:551`.
  **The reinstall that keeps the mode is tested only through `--print-wrapper`.**
  1. **What the code does.** Since `8cfdd98` (third review M12), the keep check runs when
     `MODE` is empty **or** `--print-wrapper`:
     `if { [ -z "$MODE" ] || [ "$MODE" = "--print-wrapper" ]; }`.
     - The empty branch is the install. D-170 reruns it after every merge, and the owner's page
       relies on it (`docs/owner-iphone.md:57-58`).
     - The `--print-wrapper` branch only prints.
  2. **What the test does.** `:398` runs only `--print-wrapper`. The full-install tests (`:282`,
     `:290`, `:302`, `:387`) never start from a LAN wrapper.
  3. **The mutant, I15.** Drop `[ -z "$MODE" ] ||` from the condition. The installer then rewrites
     the owner's wrapper to `127.0.0.1` on the next redeploy and restarts the engine with
     `kickstart -k`, so the phone silently stops reaching the engine. This is exactly the first
     review's M2. **It passes the whole unit suite** (1550 passed).
  4. **Why BLOCKING.** The profile counts a criterion whose test does not assert the claimed
     behaviour as unproven. The claimed behaviour is a reinstall, and the test asserts a print. The
     branch is new in a commit no Code-Reviewer read, on a HIGH wave.
  5. **The fix.** One test, below (`test_a_plain_reinstall_writes_the_mode_it_found_and_says_so`). It
     runs the real installer with no argument, against the existing stubs, over a LAN wrapper. It
     asserts that the WRITTEN wrapper keeps `0.0.0.0` and its LAN list.
     - In a scratch copy it is GREEN on `8cfdd98`.
     - It kills I15, and also I13 and I14 (T6).
- **T2** `src/app/adapter/main.py:563-564`, `:573-574`. **Coverage on `main.py` dropped from 97.06 % to
  96.54 %. Two branches of the Host check that this wave added never run.**
  1. **The bracketed IPv6 Host, `:564`.** `_host_name("[::1]:8080")` is never called with a bracket.
     - H13 keeps the brackets (`return host`) and survives.
     - Today that fails closed: the service's lists name no IPv6 address. But it is the only
       IPv6 parse the check has, and its docstring promises it.
  2. **A connection with no local address, `:574`.** uvicorn reports none, or a path, for a Unix
     socket. `_arrived_off_loopback(None)` is never called.
     - H14 makes it `True`, so the no-list engine would refuse such a request. It survives.
  3. **Why BLOCKING.** `permission-matrix.md` §11: "Coverage drop on touched module". The Tester
     profile §3 says the same. The M17-W5 seat applied the same bar ("No touched Python module loses
     coverage").
  4. **The fix.** Two tests, below:
     - `test_an_ipv6_host_is_compared_without_its_brackets_or_port`;
     - `test_without_a_list_a_connection_with_no_local_address_is_not_called_a_network_one`.
     - They kill H13 and H14, and bring `main.py` to **97.27 %**.

## MINOR (the author fixes each in this wave or files it as an issue)

- **T3** `tests/unit/test_engine_address.py:79-80`; `tests/unit/test_router_hints.py:31-34`. **The
  view pin is fooled by a block comment, a regression from `456eac2`.**
  - The pin now strips comments with `test_router_hints._code`, which removes `//` comments and keeps
    `/* … */`.
  - C4 wraps the whole address block in `/* … */`. The address is then never shown, and the pin and
    the whole unit suite pass. The ContentView source still typechecks.
  - The `_code` this file had until `a04fdd5` removed block comments, so the M11 fix lost that.
  - **The fix:** one line, below. It kills C4.
- **T4** `ios/ModelRanking/ContentView.swift:672-674`; `tests/unit/test_engine_address.py:73`. **A
  source pin cannot see that the line is drawn.**
  - C5 appends `.hidden()` to the `Text`, and it passes. So would `.opacity(0)`, or a zero frame.
  - The pin matches only what it can name, and no test runs `ContentView`. This is the residue of
    M11 that the third reviewer predicted: "a view test would be better; it belongs to #69".
  - **The fix:** fold it into #69, or file it. I wrote no pin for it, because every modifier pin is
    one more name to guess.
- **T5** `ios/ModelRanking/Engine/EngineClient.swift:138-156`; `ios/EngineTests/EngineClientTests.swift:559-583`.
  **`addressNote` ignores its language, and no test sees it.**
  - S8 passes `.english` in place of `language`. A Turkish reader then reads "Engine address:" under
    a Turkish failure title.
  - It passes all of `swift test` and the Python pins. Every `addressNote` test asks in `.english`.
    `LanguageTests.swift:443` tests `UIText.engineAddress` directly, never through `addressNote`.
  - **The fix:** one Swift test, below (`testTheAddressLineIsInTheReadersLanguage`), plus its manifest
    line. It kills S8.
- **T6** `scripts/install_engine_service.sh:53`, `:196-197`; `docs/decisions.md` D-171 note 2. **"…and
  says so" has no test.**
  - D-171 note 2 says a reinstall keeps the mode "and says so". The owner's page step 1 says the
    installer "prints `home network: on`". Neither line is asserted anywhere:
    - I13 removes the "home network: kept" line;
    - I14 removes the closing "home network: on / off" line.
  - Both pass the whole unit suite.
  - **The fix:** T1's test asserts both, and kills both.
- **T7** `scripts/install_engine_service.sh:50`; `tests/unit/test_engine_service.py:420`. **Half of M12
  is held.**
  - The third review named two modes that must not read the live wrapper: `--print-plist` and
    `--deploy-only`. `:420` tests `--print-plist` only.
  - I5 changes the condition to `!= --print-plist`, so `--deploy-only` reads the wrapper again. It
    passes the whole unit suite.
  - The harm is small, since the deploy itself ignores the mode. But it is the exact regression M12
    was about: a test path that depends on the owner's live service.
  - **The fix:** one test, below (`test_a_deploy_reads_no_live_wrapper`). It kills I5.

## Notes (no change required by this verdict)

- **N1. Equivalent mutant: I3**, the third reviewer's `M2-no-lan-ignored`. It drops `NO_LAN = no` from
  the keep check, and `install_engine_service.sh:55` closes the mode anyway. Dropping both (I3c) is
  killed by `:398`. Not a finding.
- **N2. Two evidence lines do not cite the id.** The PRD's REQ-DEV-001 evidence cites
  `EngineClientTests.swift:53` and `:290`. Both sit in classes whose comments name the review rounds
  (K3, M4), not REQ-DEV-001 or D-171 (seed E.2). The third review's M13(b) fixed the other two files.
  It is records drift, small enough to fold into the T1/T2 commit.
- **N3. The no-list rule is shown on a real socket only for loopback.**
  - `test_engine_host.py:72` uses `TestClient`'s synthetic `server`. Arrival on a LAN address through
    a real socket needs a LAN bind, which this seat may not make.
  - What stands in for it: uvicorn's own source (`getsockname`) and the loopback probe above.
  - Note 9 and #94 already record the forwarder case.
- **N4. No build was run.** `xcodebuild` is barred in this seat, and the simulator is paused.
  - The chain `ENGINE_URL` → `Info.plist` `$(ENGINE_URL)` → `Bundle.main` → `EngineClient()`
    (`ContentView.swift:72`) is held by source pins (X4–X11, P1, P2), plus `client-decls` typechecking
    the client.
  - The plan's spike (`m18-wave-1-plan.md:15-21`) and the owner's first run are its only end-to-end
    proof. REQ-DEV-001 is honestly PARTIAL.
- **N5. A regressed preflight does not reach the network.** With the preflight off (L1, V1), the
  launcher test execs uvicorn on 192.0.2.1:8080. The guard log shows these arguments. Real uvicorn
  would start the lifespan, then fail to bind. The nightly catch-up waits `STARTUP_GRACE_SECONDS = 60`
  (`nightly.py:68`) before any refresh, so the failed bind ends it first. Read, not run.

## K.9 candidates spotted outside this wave's scope

- **K1** `tests/unit/test_router_hints.py:31-34`. **`_code` keeps `/* */` comments.**
  - Any pin built on it that requires code to be PRESENT is satisfied by commented-out code. T3 is
    one instance.
  - Pins that require code to be ABSENT fail safe.
  - Worth one look at the other presence pins that use it, or one line in `_code` itself.

## Risks queued to next M

- **R1** `docs/owner-iphone.md:41-48`. Step 6 explains three screens. It does not explain the fourth
  one this wave now shows: "This engine does not answer to that host", with the address under it.
  "Keep in mind" covers the rename that causes it (lines 61-63), but a reader at step 6 will not find
  it there. This is a page line, not a test; it goes to the owner's next look at the page.

## Fault injection (HIGH: mandatory)

**Harness:** `tester-w18/mut.py`. For each mutant it:
1. checks the file against `HEAD` with `git hash-object`;
2. records the file's sha256;
3. makes exact byte edits, each of which must match once;
4. runs the named tests;
5. writes the original bytes back in place;
6. asserts the sha256 equals the pre-edit hash, `git hash-object` equals HEAD's blob, and
   `git diff --quiet` holds.

No `git checkout` or `git restore` was used. A survivor of its named tests was re-run against the
whole of `tests/unit` (Python mutants), or against the whole of `swift test` plus the three Python pin
files (Swift mutants). Every Swift kill is an XCTest assertion, never a compile error. The log is
`tester-w18/logs/mutants.jsonl`, one row per mutant, and **all 68 rows say `restored: true`**.

**Restore hashes** (sha256 prefix before = after, and the HEAD blob `git hash-object` matched):

| file | sha256 (pre = post) | HEAD blob |
|---|---|---|
| `src/app/adapter/main.py` | `8de4876503d4` | `35171db171` |
| `scripts/engine_service.sh` | `cc17145abc38` | `522a1b539a` |
| `scripts/install_engine_service.sh` | `1e95ef214a6b` | `7541de9c4d` |
| `Makefile` | `8678e690d706` | `4d9d0b876c` |
| `ios/app.sh` | `87fbebb2c27b` | `a78263dc44` |
| `ios/Config/Engine.xcconfig` | `ac803fa1b130` | `81ee48b12e` |
| `ios/Config/Info.plist` | `d7ead6196aaa` | `3e7b7b968f` |
| `ios/ModelRanking.xcodeproj/project.pbxproj` | `f26ba10d947e` | `9710da6cc2` |
| `.gitignore` | `4381e99bee55` | `41a99a4126` |
| `ios/ModelRanking/ContentView.swift` | `c2f4a3ff1d11` | `705a1170a5` |
| `ios/ModelRanking/Engine/EngineClient.swift` | `8db356862dc9` | `e5f3c54157` |
| `ios/ModelRanking/Engine/Language.swift` | `837d756a40ee` | `84d144583a` |

After the run, all 670 tracked files match the pre-run sha256 baseline (`sha-baseline.txt` =
`sha-after.txt`), and `git status --porcelain` is empty.

**The mutants.** "cr3:" marks a replay of the third Code-Reviewer's set, rebuilt from
`docs/reviews/m18-wave-1-review.md` and adapted where `8cfdd98` moved the code.

| id | origin | the fault | result | killed by |
|---|---|---|---|---|
| H1 | cr3:B1a-arrival-off | no-list arrival rule off | KILLED | `test_engine_host.py:72` |
| H2 | cr3:B1a-name-is-network | a name counts as a network address | KILLED | `:53` |
| H3 | tester | list check off | KILLED | `:45` (4 Hosts) |
| H4 | tester | prefix match instead of exact | KILLED | `:45` (`127.0.0.1.evil.example`, `…local.evil.example`) |
| H5 | tester | port not stripped | KILLED | `:38` |
| H6 | cr3:M5-header-case | header not lower-cased | KILLED | `:81` |
| H7 | cr3:M5-list-case | list not lower-cased | KILLED | `:81` |
| H8 | cr3:M5-empty-host-served | empty Host served | KILLED | `:90` |
| H9 | tester | the peer's address in place of the local one | KILLED | `:72` |
| H10 | tester | `is_private` in place of `is_loopback` | KILLED | `:72` |
| H11 | tester | the list checked only off loopback (rebinding on loopback) | KILLED | `:45`, `:90` |
| H12 | tester | the Host middleware unregistered | KILLED | `:45`, `:72`, `:90` |
| **H13** | tester | bracketed IPv6 Host kept whole (`main.py:564`) | **SURVIVED** | **T2** |
| **H14** | tester | no local address counted as a network (`main.py:574`) | **SURVIVED** | **T2** |
| V1 | cr3:B1-startup-check-off | the startup check off | KILLED | `:58`; `test_engine_service.py:373` (guard refused the exec) |
| V2 | tester | `and` → `or` in the startup check | KILLED | `:58` |
| V3 | tester | `0.0.0.0` counted as loopback | KILLED | `:58` |
| L1 | tester (cr3 did not run it) | the preflight's result ignored | KILLED | `test_engine_service.py:373` (guard refused the exec) |
| L2 | cr3:86-second-host | a second `--host 0.0.0.0` | KILLED | `:364` |
| L3 | tester | the launcher's default bind `0.0.0.0` | KILLED | `:178`, `:364` |
| I1 | cr3:M2-keep-mode-off | the keep check off | KILLED | `:398` |
| I2 | cr3:M7-any-wrapper-opens | any wrapper opens the network | KILLED | `:398` |
| I3 | cr3:M2-no-lan-ignored | `NO_LAN = no` dropped from the keep check | SURVIVED, equivalent | **N1** |
| I3c | tester | both `--no-lan` guards dropped | KILLED | `:398` |
| I4 | tester | every mode reads the wrapper (M12 undone) | KILLED | `:420` |
| **I5** | tester | `--deploy-only` reads the wrapper | **SURVIVED** | **T7** |
| I6 | cr3:86-wrapper-755 | wrapper `chmod 755` | KILLED | `:387` |
| I7 | cr3:M5-installer-name-case | the `.local` name not lower-cased | KILLED | `:355` |
| I8 | tester | the default bind `0.0.0.0` | KILLED | `:349`, `:398` |
| I9 | tester | the LAN address left off the list | KILLED | `:355` |
| I10 | tester | `--lan` keeps a loopback bind | KILLED | `:355`, `:398` |
| I11 | tester | no Host list by default | KILLED | `:349`, `:355` |
| I12 | tester | the wrapper drops the list export | KILLED | `:349`, `:355` |
| **I13** | tester | the "kept" line removed | **SURVIVED** | **T6** |
| **I14** | tester | the closing "home network" line removed | **SURVIVED** | **T6** |
| **I15** | tester | **the install forgets the mode (keep only for `--print-wrapper`)** | **SURVIVED** | **T1** |
| X1 | cr3:B1b-make-run-0000 | `make run` binds `0.0.0.0` | KILLED | `:434` |
| X2 | cr3:M2-appsh-url-dropped | `app.sh` drops `ENGINE_URL` | KILLED | `:442` |
| X3 | cr3:M2-appsh-bundle-dropped | `app.sh` drops the bundle id | KILLED | `:442` |
| X4 | cr3:M3-bundle-id-out-of-xcconfig | the bundle id commented out | KILLED | `test_engine_address.py:61` |
| X5 | cr3:M3-include-dropped | the `#include?` dropped | KILLED | `:21` |
| X6 | tester | the default `ENGINE_URL` is the owner's Mac | KILLED | `:21` |
| X7 | tester | `NSAllowsArbitraryLoads` added | KILLED | `:30` |
| X8 | tester | the local-network usage text dropped | KILLED | `:30` |
| X9 | tester | Release config loses `INFOPLIST_FILE` | KILLED | `:39` |
| X10 | tester | Release config loses the xcconfig | KILLED | `:39` |
| X11 | tester | the override not git-ignored | KILLED | `:21` |
| C1 | cr3:B2a-view-line-removed | the view's address block removed | KILLED | `:73` |
| C2 | cr3:B2a-view-line-commented | the block `//`-commented | KILLED | `:73` |
| C3 | cr3:B2a-view-computed-not-shown | `let _ = error.addressNote(…)` (M11) | KILLED | `:73` |
| **C4** | tester | the block `/* */`-commented | **SURVIVED** | **T3** |
| **C5** | tester | `.hidden()` on the line | **SURVIVED** | **T4** |
| P1 | cr3:M4-key-misspelt | plist key `EngineUrl` | KILLED | `:48` |
| P2 | cr3:M4-reads-nil | `localDefault` reads nil | KILLED | `:48` |
| P3 | cr3:K3-case-sensitive-again | redirect compare with case (pin) | KILLED | `test_ios_client_contract.py:504` |
| S1 | cr3:W4-any-scheme | any URL scheme accepted | KILLED | `EngineClientTests.swift:585` |
| S2 | tester | the host check dropped | KILLED | `:585` |
| S3 | tester | always loopback | KILLED | `:552` |
| S4 | tester | `unknown_host` shows no address | KILLED | `:569` |
| S5 | cr3:B2a-refused-shows-address (adapted) | every refusal shows the address | KILLED | `:578` |
| S6 | cr3:B2a-only-unreachable (adapted) | only `.unreachable` shows it | KILLED | `:559` |
| S7 | tester | `insecureTransport` shows no address (M10) | KILLED | `:569` |
| **S8** | tester | `addressNote` always English | **SURVIVED** (swift test + pins) | **T5** |
| S9 | tester | the host only, not the URL | KILLED | `:559`, `:569` |
| S10 | cr3:B2a-turkish-line | the Turkish line in English | KILLED | `LanguageTests.swift:443` |
| S11 | cr3:K3-case-sensitive | redirect compare with case | KILLED | `EngineClientTests.swift:53` |
| S12 | tester | every redirect followed | KILLED | `:39`, `:61`, `:67`, `:78` |
| S13 | cr3:M4-detail-without-address | the unreachable detail drops the address | KILLED | `:290` |

**Kill rate:** 58 of 67 non-equivalent mutants, **87 %**.
- **The third Code-Reviewer's set:** 29 replayed, 28 killed, 1 equivalent (I3). Its one real
  survivor, M11's C3, is now killed.
- **This seat's own mutants:** 39, of which 9 survive. Those are this verdict's T1 to T7.

## Tests added/extended this review

**None in the repository.** This seat may change only this file. Each test below was written into a
scratch copy of `8cfdd98` (`tester-w18/trees/prop`; the whole diff is `tester-w18/proposed-tests.diff`):
- each is GREEN there;
- each kills its survivors (`tester-w18/logs/propcheck.txt`);
- with them, `main.py` coverage is 97.27 %;
- the manifest test passes once the Swift name is added.

The two BLOCKING tests (T1, T2) are given in full.

**T1, T6.** In `tests/unit/test_engine_service.py`: a helper beside `_install` that adds environment,
then the test. Proven: kills I15, I13 and I14.
```python
def _install_with(tmp_path: Path, repo: Path, health: str, **extra: str) -> subprocess.CompletedProcess[str]:
    """`_install`, with this Mac's name and address given instead of asked (scutil, ipconfig)."""
    stubs, state, home = tmp_path / "stubs", tmp_path / "state", tmp_path / "home"
    for folder in (stubs, state, home):
        folder.mkdir(exist_ok=True)
    for name, body in _STUBS.items():
        (stubs / name).write_text(body, encoding="utf-8")
        (stubs / name).chmod(0o755)
    (repo / ".venv" / "bin").mkdir(parents=True, exist_ok=True)
    (repo / ".venv" / "bin" / "python").write_text("#!/bin/bash\n", encoding="utf-8")
    (repo / ".venv" / "bin" / "python").chmod(0o755)
    env = {**_CLEAN_GIT_ENV, "HOME": str(home), "MODEL_RANKING_REPO": str(repo),
           "PATH": f"{stubs}:{os.environ['PATH']}", "STUB_LOG": str(tmp_path / "calls.log"),
           "STUB_STATE": str(state), "ENGINE_DEPLOY_NO_VENV": "1", "ENGINE_INSTALL_WAIT_S": "1",
           "STUB_HEALTH": health, **extra}
    return subprocess.run(["/bin/bash", str(INSTALLER)], capture_output=True, text=True, timeout=120, env=env)


def test_a_plain_reinstall_writes_the_mode_it_found_and_says_so(tmp_path: Path) -> None:
    """REQ-DEV-001 / D-171 note 2: the redeploy after a merge is a plain install, not `--print-wrapper`.
    It must WRITE the home-network wrapper it found, and say so on both lines the owner reads."""
    repo = _scratch_repo(tmp_path)
    wrapper = tmp_path / "home" / "Library" / "Application Support" / "model-ranking" / "engine_service.sh"
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text('export MODEL_RANKING_BIND="0.0.0.0"\n', encoding="utf-8")
    done = _install_with(tmp_path, repo, f'{{"status":"ok","build":"release-{_sha(repo)}"}}',
                         ENGINE_LAN_NAME="probe-mac", ENGINE_LAN_IP="192.168.9.9")
    assert done.returncode == 0, done.stdout + done.stderr
    written = wrapper.read_text(encoding="utf-8")
    assert 'export MODEL_RANKING_BIND="0.0.0.0"' in written, written
    assert 'export MODEL_RANKING_ALLOWED_HOSTS="127.0.0.1,localhost,probe-mac.local,192.168.9.9"' in written
    assert "home network: kept" in done.stderr, done.stderr
    assert "home network: on" in done.stdout, done.stdout
```

**T2.** In `tests/unit/test_engine_host.py`. Proven: kills H13 and H14.
```python
def test_an_ipv6_host_is_compared_without_its_brackets_or_port(db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`_host_name`'s bracket branch (main.py:564) never ran: `[::1]:8080` is `::1` on the list."""
    monkeypatch.setenv(HOSTS, "127.0.0.1,::1")
    client = TestClient(adapter.app, base_url="http://127.0.0.1:8080")
    assert client.get("/v1/categories", headers={"host": "[::1]:8080"}).status_code == 200
    assert client.get("/v1/categories", headers={"host": "[::1]"}).status_code == 200
    assert client.get("/v1/categories", headers={"host": "[::2]:8080"}).status_code == 400
    assert client.get("/v1/categories", headers={"host": "[::1"}).status_code == 400


def test_without_a_list_a_connection_with_no_local_address_is_not_called_a_network_one() -> None:
    """`_arrived_off_loopback`'s first branch (main.py:574) never ran. uvicorn reports no address, or
    a path, for a Unix socket; neither is a network address."""
    assert adapter._arrived_off_loopback(None) is False
    assert adapter._arrived_off_loopback(("/tmp/engine.sock", None)) is False
    assert adapter._arrived_off_loopback(("192.168.0.26", 8080)) is True
    assert adapter._arrived_off_loopback(("::1", 8080)) is False
```

**The MINOR tests, each proven in the scratch copy.**
- **T3** (kills C4). In `test_engine_address.py:80`, strip block comments before `_code`:
  `_code(re.sub(r"/\*.*?\*/", "", view[start : view.index("// MARK:", start)], flags=re.S))`.
- **T5** (kills S8). Add `testTheAddressLineIsInTheReadersLanguage` to `EngineAddressTests`. It
  asserts `"Motor adresi: …"` from `addressNote(address, .turkish)` for `.unreachable`, `.timedOut`,
  `.offline`, `.insecureTransport` and the `unknown_host` refusal. Add its line to
  `test-manifest.txt`.
- **T7** (kills I5). Add `test_a_deploy_reads_no_live_wrapper`. It writes a LAN wrapper into the
  scratch HOME that `_deploy` uses, then asserts that no "home network" text is printed.

## Safety (this seat's rules)

- **Neither installer script was executed by this seat.** `scripts/install_engine_service.sh` and
  `scripts/remove_engine_service.sh` ran only inside `tests/unit/test_engine_service.py`, with a scratch
  HOME (`HOME` set to a scratch folder for every pytest run, the gate excepted) and the file's own
  stubs. Installer mutants were edited in place, run through that file, and restored byte-identical.
- **No `launchctl`, `xcodebuild` or `simctl` ran, and nothing ran on the simulator.**
  - `xcrun` ran only inside `make check-fast`'s `client-decls` leg, through a filter that passes
    only SDK-path queries and `swiftc`. The leg made two kinds of call:
    - `xcrun --sdk iphoneos|iphonesimulator --show-sdk-path`;
    - `xcrun swiftc -typecheck -dump-ast` against those SDKs.
    Both are compile-only.
  - To prove the filter refuses everything else, I sent it one `xcrun simctl list`. The filter
    stopped it ("BLOCKED in this review seat", exit 97), and the real `xcrun` never saw it. That is
    the only time the message appeared.
- **Nothing bound beyond loopback.**
  - The probe engines bound 127.0.0.1:8141-8143, were stopped with SIGTERM, and left no listener.
  - During the red runs and the mutants, `python -m uvicorn` was refused at start by a
    `sitecustomize` guard (`os._exit(3)`, never `abort`). It fired three times, each before any
    engine code ran:
    - `41be53a`'s red launcher, asking for 127.0.0.1:8080;
    - V1 and L1, asking for 192.0.2.1:8080.
- **Changes.** No commit, no push, no GitHub. The only tracked change is this file. The bytecode
  caches the run created were removed.
