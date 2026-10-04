---
record_type: review
id: m18-wave-5-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# M18-W5 Code Review: the gates and records backlog

**Reviewer:** Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `77d3b2f..f21f658`: 13 commits plus the merge `10d9e50`, 47 files, +1304 / -160.
`77d3b2f` is the head of `wave/m18-w4`, which this wave is stacked on. `10d9e50` brought W4 in.
`git diff 5623f4b 1d2a455` and `git diff 77d3b2f 10d9e50` carry the same lines (md5 of the sorted
`+`/`-` lines is equal), so the merge adds no change of its own. Only W5's commits are reviewed.
**Risk tier:** HIGH (`docs/plans/m18-wave-5-plan.md:12`). `m18-plan.md:106` says MED. The diff
touches `src/app/adapter/main.py` (a docstring), which is a §3 security glob, and the D-126 gates. The
wave plan predicted `EngineClient.swift` (#58); the diff touched `FrontDoor.swift` instead.
**Model routing (HIGH, advisory):** author-family: claude-opus / reviewer-family: claude-opus (fallback: no second family available)
**Fresh context:** this seat started with none of the authoring context. I read the plans and the
issues first, then the code and the tests. The one-line commit subjects were visible in `git log`
from the start. I read the full commit messages only after the code, when I matched the red commits
to their fixes.

**Summary.** One finding blocks. #58's gate half is not closed. A `URL` decoded from the reader's
text in `ContentView.swift` passes **both** D-126 gates at `f21f658`. I measured it with an in-place
mutant, a `Decodable` struct with an `Optional<URL>` field decoded from a string:
1. the text gates: 44 passed;
2. `client_decl_gate.py`: PASS in all four configurations.

The compiler gate's new rule matches only `decode(`. `decodeIfPresent(` is what Swift synthesises for
every optional property, and the compiler prints `T -> URL` for it. The text gate has no rule for a
decoded URL at all. The fix is a regex and two fixture lines (**B1**).

The rest holds up:
1. The register is file-only, and the standings store already was.
2. The offline tripwire works on every path the suite uses today.
3. Every red commit fails on its own tree and passes on its fix, including `90ead9d`'s accidental
   red, which `1d2a455` fixes.
4. The records are accurate in the sample I traced.

Six findings are MINOR:
1. **M1.** The Swift tripwire has four ways around it.
2. **M2.** #98's stripper misses nested comments. It also now erases live code from the negative
   pins' view.
3. **M3.** `missing_closes` passes vacuously on a plan whose waves it cannot parse.
4. **M4.** The input-parsing HIGH rule fails open on three inputs.
5. **M5.** #92's T1 watcher skips `/v1/recommendations`, and N1 misses a split line.
6. **M6.** Records: P4's move to W6 is unrecorded in the milestone plan, two citations are wrong, and
   the #52 rule has no ADR.

**Policy.** The profile (`.claude/agents/Code-Reviewer.md`) and `.agents/rules/practices.md` were
read from `77d3b2f`. At that ref the matrix is `permission-matrix.md` at the repository root, and
`docs/permission-matrix.md` does not exist. `git diff --stat 77d3b2f f21f658 -- .claude .agents
permission-matrix.md .github Dockerfile fly.toml epb.html or.md` is empty. `docs/decisions.md` only
gains lines (+4, -0).

**How I worked.**
1. **Gate**, at `f21f658` with the worktree's own `.venv`. `make` was not used, so that `install`
   writes nothing.
   1. pytest `-n auto` with `MODEL_RANKING_REQUIRE_ARTIFACT=1`: **1609 passed, 25 skipped**. The
      Mac's 25 matches `docs/skip-budget.txt:28`; the budget is 76, because CI also skips the
      compiled fixture.
   2. ruff, mypy (strict), the module coverage floor, `check_records.py` and `wave_check_all.py`:
      PASS.
   3. `client_decl_gate.py`, self-test first: PASS, 15 files in 4 configurations.
   4. `swift test`: 366 tests, 0 failures. `swift test --parallel`: xUnit 366 tests, 0 failures.
      `--list-tests` equals `ios/EngineTests/test-manifest.txt`.
2. **Red first.** I ran each red commit's tests on a `git archive` of its tree in the scratchpad,
   not in a git worktree, with this worktree's venv and `PYTHONPATH=<tree>/src`. Swift was run with
   `swift test --filter` in the archive.
   1. `5a3b1be`: 2 Python failed, and Swift's `testEverySessionConfigurationAsksTheTripwireFirst`
      failed. Fix `6efede4`: 5 passed.
   2. `93de739`: 2 of 3 gate tests failed, and the register's Swift test failed: the tripwire
      recorded `https://example.invalid/gap-register.json`, so nothing left the machine.
   3. `90ead9d`: the gate tests and the Swift test pass, but `test_the_gap_register_stays_on_the_device`
      fails, as `1d2a455`'s message says. `1d2a455`: 12 passed.
   4. `678a830`: 1 failed. Fix `6894083`: 16 passed.
   5. `ca8b785`: 6 failed (N2, N3, #82 ×3, #83), and 25 passed (T1–T4, N1, N3's IntegrityError
      half), as its message states. Fix `f21f658`: 31 passed.
3. **Probes**, none of which bound a socket. Every request went to `127.0.0.1:8199`, with nothing
   listening, or to the tripwire.
   1. The tripwire, in a scratch SwiftPM package holding a copy of `OfflineTestCase.swift`
      (`cr5-swiftprobe`): eight cases.
   2. The declaration gate's `dump_ast`, `references` and `problems` on scratch fixtures
      (`cr5-declprobe`): eleven cases.
   3. `missing_closes` and `wave_check.py` on scratch trees (`cr5-ctl`, `cr5-ctl83`).
4. **Mutants: 11 in-place edits**, each restored from a byte copy. After each I checked
   `git hash-object` and `git diff --quiet`.
   1. **2 were killed:**
      1. `URL.decoded` dropped from `NETWORK`;
      2. a schema-migrating opener on `/v1/recommendations`, which died only incidentally (**M5**).
   2. **6 survived the gate they target:**
      1. a URL decoded in `ContentView.swift`, in two spellings (**B1**);
      2. a nested comment (**M2**);
      3. a class `setUp` override (**M1**);
      4. an aliased writable open on `/v1/recommendations` (**M5**);
      5. a split `simctl … booted` line (**M5**).
   3. **3 were attempts toward B1's spellings** that the text gate refused for an unrelated pattern:
      a URL literal, `.init(`, and `typealias`. The last also did not type-check.
5. **One probe trapped.** `URLSession(configuration: URLSessionConfiguration())` stopped the scratch
   package's `xctest` process with signal 5. It was a command-line process in the scratchpad, not
   the project's suite. I did not run it again, to avoid crash dialogs on the owner's Mac (**R1**).
6. **Read only:** GitHub issues #33, #51, #58, #59, #82, #83, #92 and #98.
7. **Not done, by this seat's rules:**
   1. no run of `install_engine_service.sh` or `remove_engine_service.sh`, except inside
      `tests/unit/test_engine_service.py` (stubs, scratch HOME);
   2. no `launchctl`, `xcodebuild`, `simctl`, nothing on the simulator, nothing in `~/Library`;
   3. no server; no commit, push or GitHub write.
8. **Tree.** Clean apart from this file.

## Verdict
BLOCKING

**One BLOCKING, six MINOR.** **B1** must be fixed before the wave closes; a new Code-Reviewer then
reads the new range. I recommend fixing M1 to M5 in the same round. Each is a few lines, and M2 is a
regression this wave introduced into a control.
- **B1.** A URL decoded from text outside `EngineClient.swift` passes both D-126 gates. The
  compiler rule misses `decodeIfPresent`, and the text gate has no decoded-URL rule.
- **M1.** The Swift tripwire has four ways around it:
  1. a class `setUp` override;
  2. a stub that declines a request;
  3. a background configuration;
  4. Swift Testing.
- **M2.** #98's `_code` misses Swift's nested block comments, and a `/*` inside a `//` comment now
  hides live code from the negative pins.
- **M3.** `missing_closes` passes vacuously on a closed milestone whose wave headings it cannot parse.
- **M4.** The HIGH rule passes three inputs:
  1. an undated close;
  2. a footprint whose `Mutant set author:` line comes before `Touched:`;
  3. `src/app/clients` without its slash.
- **M5.** The T1 watcher does not run `/v1/recommendations`, and N1's check misses a `simctl` call
  split over two lines.
- **M6.** Records:
  1. P4's move to W6 is not in `m18-plan.md`;
  2. two PRD citations are wrong;
  3. the #52 rule has no ADR.

**K.9:** K1 (other ways to make a URL from text pass the compiler gate), K2 (REQ-ING-010's
duplicate rows).
**Risks:** R1 (a deprecated configuration initialiser trapped `xctest`), R2 (a process-wide audit
hook in every pytest worker), R3 (N2 narrows D-156 without saying so in D-156).

## Findings

### BLOCKING (must fix before this wave closes)

- **B1** `scripts/client_decl_gate.py:213-216`, `:264-265`; `scripts/client_decl_fixtures/ContentView.swift:9-12`; `tests/unit/test_router_hints.py:382`. **A URL decoded from the reader's text outside `EngineClient.swift` passes both D-126 gates.**

  #58's "Expected" reads: "the gates refuse a `URL` made by decoding outside `EngineClient.swift`".
  The milestone's W5 criterion is "Every gate gap filed is closed with a gate shown red"
  (`m18-plan.md:34`). The wave closed the register half; the gate half is open.

  **The mutant, in place in `ios/ModelRanking/ContentView.swift`, then restored byte-identical:**
  ```swift
  struct CrBox: Decodable { let u: Optional<URL> }
  func crProbeDecodes(_ blob: String) -> Optional<URL> {
      (try? JSONDecoder().decode(CrBox.self, from: Data(blob.utf8)))?.u
  }
  ```
  1. `test_router_hints.py`, `test_ios_client_contract.py`, `test_engine_address.py`: **44 passed.**
  2. `client_decl_gate.py`: **`client-decls PASS: 15 client file(s) in 4 configuration(s)`.**

  **Why the compiler gate misses it.** `DECODES_URL` requires `\.decode\(` in the declaration path.
  Swift synthesises `KeyedDecodingContainer.decodeIfPresent(_:forKey:)` for every optional property,
  and the dump prints its substitution as clearly as `decode`'s. From the probe's AST:
  `decl="Swift.(file).KeyedDecodingContainer.decodeIfPresent(_:forKey:) [with (substitution_map
  generic_signature=<K, T where K : CodingKey, T : Decodable> K -> OptBox.CodingKeys T -> URL)]"`.

  Eleven compiled probe files (`cr5-declprobe/fx2`) show where the rule stops:
  1. **Refused.** `JSONDecoder.decode([URL].self)`, `decode(URL.self)`,
     `PropertyListDecoder.decode([String: URL].self)`, and a synthesised `Decodable` with a
     non-optional `URL` field. So the comment's "a container's `decode(URL.self, forKey:)` inside a
     synthesised `Decodable`" holds.
  2. **Passed.** A hand-written `decodeIfPresent(URL.self, forKey:)`, and a synthesised `Decodable`
     with a `URL?` field.

  **Why the text gate misses it.** `test_router_hints.py:382` refuses `URL(`, `URL.` and
  `: [URL` / `: URL`, the last with the note "a URL-typed value, which a decoder can fill from
  anywhere". It does not refuse `Optional<URL>`, `[URL].self` or `-> [URL]`. A second mutant,
  `JSONDecoder().decode([URL].self, from: blob.data(using: .utf8) ?? [])` in `ContentView.swift`,
  also passed the text gates (44 passed). The compiler gate refuses that one. The text gate is the
  only D-126 check CI runs, because CI has no Xcode and skips the compiled fixture.

  **What it reaches today.** Both file stores now refuse a non-file address (`FrontDoor.swift:308`,
  `:318`; `StandingsStore.swift:54`, `:67`), so the path #58 named through the register is closed at
  the sink. A decoded URL outside `EngineClient.swift` is still the network's first step, by this
  gate's own rule (`client_decl_gate.py:98-100`). The obvious next consumer is
  `EngineClient(baseURL:)`, which the gate scopes by file, not by data (its docstring, B19). I did not
  build that chain.

  **Why BLOCKING.**
  1. #58's acceptance, "the gates refuse a URL made by decoding", is unmet on the form Swift
     generates for every optional URL property. This is "REQ-ID unmet (acceptance criteria not
     green)" in permission matrix §11, with this wave's own criterion standing in for the REQ.
  2. It is D-126, the boundary this project treats as absolute. The compiler gate exists because six
     rounds of word lists each missed a form (`client_decl_gate.py:3-6`). This is that history again,
     on the rule this wave added.

  **The fix.**
  1. `DECODES_URL`: `\.decode(?:IfPresent)?\(`, or any `\.decode\w*\(`.
  2. Add a `struct … { let u: Optional<URL> }` decoded in the fixture's `ContentView.swift`, so the
     self-test pins the synthesised `decodeIfPresent` form, and its canned twin in
     `test_client_decl_gate.py`.
  3. Then either give the text gate a decoded-URL pattern (`[<\[,]\s*URL\b` would catch
     `Optional<URL>`, `[URL]` and `[String: URL]`), or state in `client_decl_gate.py`'s docstring
     and the close record that the text gate does not see decoding and CI therefore does not either.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `ios/EngineTests/OfflineTestCase.swift:53-57`, `:86-98`; `tests/unit/test_swift_tests_offline.py:22`, `:34`. **The Swift tripwire has four ways around it, and its tearDown cannot tell when it was never installed.**

  The header claims "How it catches every way a test could fetch". Probes in a scratch package with a
  copy of the base, every request to `127.0.0.1:8199`, nothing listening:
  1. **A class `setUp` that skips `super`.** The install happens only in the base's
     `override class func setUp()`. A subclass `override class func setUp() {}` running first in its
     process skips it. That happens under `swift test --filter`, and in a parallel worker. Probe P5:
     the request reached the real stack (`-1004`, cannot connect) and the test **passed**. The base's
     tearDown checks `notInstalled == nil`, which stays nil when the install never ran. The source
     check reads only instance hooks (`test_swift_tests_offline.py:34`). The same override added to
     `StandingsStoreTests.swift` passed both Python checks (5 passed).
  2. **A stub that declines.** A stub session replaces `protocolClasses`, as all three in
     `EngineClientTests.swift` do. A request the stub does not `canInit` falls through to the real
     stack, and nothing is recorded (probe P4: `-1004`, attempts `[]`). Today `StubProtocol.canInit`
     returns `true` (`EngineClientTests.swift:208`), so nothing escapes now.
  3. **A background configuration.** `URLSessionConfiguration.background(withIdentifier:)` is not
     exchanged: its first protocol class is `_NSURLAppSSOProtocol` (probe P2).
  4. **Swift Testing.** An `import Testing` / `@Test` function derives from nothing, and none of the
     checks reads it. The tripwire is installed only by an XCTest class's `setUp`. The target has 0
     such tests today.

  What holds: `URLSession.shared` (P3), `Data(contentsOf:)` (P6), a copied `.default` (P7) and an
  undrained request failing the test (P9) are all caught. The exchange is confined to the test
  process, and the app does not compile `ios/EngineTests/` (`project.pbxproj` syncs only
  `ModelRanking`). Both the serial and the parallel run are covered for every class in the target
  today.

  **The fix.**
  1. Also install from the base's instance `setUp()`, which the Python check already forces
     subclasses to call through.
  2. In tearDown, assert that `URLSessionConfiguration.default.protocolClasses?.first` is the
     tripwire.
  3. Have the Python check refuse an `override class func setUp` that does not call `super`, and
     `import Testing` in `EngineTests`.
  4. Either require every `URLProtocol` subclass in the target to `canInit` everything, or append
     the tripwire after a stub's classes.

- **M2** `tests/unit/test_router_hints.py:31-37`; `tests/unit/test_engine_address.py:80`. **#98's stripper misses Swift's nested block comments, and it now hides live code from the negative pins.**

  1. **Nested comments: the #98 class itself.** Swift block comments nest. The mutant
     `/* /* the address line, off for now */` above the failure view's `if let address =
     error.addressNote(client.baseURL, language) { Text(address)… }` and `*/` below it:
     1. it type-checks with 0 errors (`swiftc -typecheck`, simulator SDK), so the line is gone from
        the build;
     2. `test_the_failure_screen_shows_the_address_the_app_asked` still **passes**.

     The non-greedy `/\*.*?\*/` stops at the inner `*/` and leaves the code visible. This is the W1
     Tester's mutant C4 with one more `/*`.
  2. **A regression in the other direction.** The new `re.sub` runs before the `//` cut. A `/*`
     inside a line comment now opens a "comment" that the regex closes at a later `*/`, and erases
     the live code between them. Checked on `_code` directly:
     `// see /* the old note` / `outcome.refinements = picked` / `// */ end` → the negative pin
     `\.refinements\s*(=|\.append|\+=)` (`test_router_hints.py:168`) **does not see the assignment**.
     The old stripper, which cut each line at `//`, did. The three Router pins at `:130`, `:155` and
     `:175` all assert absences through `_code`.

  **The fix:** one left-to-right scanner that tracks depth for `/*` … `*/`, honours `//` to the end
  of the line, and skips string literals. Pin it with both shapes above.

- **M3** `scripts/wave_check_all.py:61`, `:85-86`. **`missing_closes` passes vacuously on a plan whose wave headings it cannot parse.**

  Probe: a closed M19 with no close records at all.
  1. `### W1 — one`: 2 missing, as designed.
  2. `## Wave 1 — one`: **0 missing.**
  3. `### M19-W1 — one`: **0 missing.**

  AGENTS.md §3.5: "the comparing gate **fails CLOSED** (an empty or errored derived set is a
  FAILURE, never a vacuous pass)", and #82 asks for "fail closed on a missing one
  (`/writing-a-control`)". Also, any heading that contains the substring "dropped" is excused.

  What holds:
  1. On the real M18 plan, as if M18 closed today, it lists W2–W6 correctly.
  2. Nothing before M18 is graded (`EXPECTED_CLOSES_FROM = 18`, GPF-001).
  3. `wave_check_all.py` passes on the tree.

  **The fix:** a closed milestone whose plan yields no wave heading is itself a finding, and
  "dropped" is matched as a marked token, for example `(dropped`.

- **M4** `scripts/wave_check.py:274`, `:355-364`. **The input-parsing HIGH rule fails open on three inputs.**

  I ran `wave_check.py` on the M18-W1 close with tier MED, `Touched: src/app/clients/epoch.py` and
  date 2026-10-04: rc 1, the rule fires. Each variant below returns **rc 0**:
  1. **No `date:` line.** The rule needs `dated is not None`. An undated v6.6 close otherwise passes
     `wave_check.py`, and an undated record has no claim to be grandfathered.
  2. **`Mutant set author:` above `Touched:`.** `Touched:(.*?)^\s*Mutant set author:` then finds
     nothing.
  3. **`Touched: src/app/clients (epoch.py)`.** The rule looks for the substring with the slash.

  GPF-001 holds: every existing close is dated before 2026-10-04 and is not graded.

  **The fix:**
  1. Grade an undated close, so the rule reads `dated is None or … >= INPUT_PARSING_HIGH_FROM`.
  2. Read the `Touched:` field on its own, up to the next `Field:` line.
  3. Match `src/app/clients\b`.

- **M5** `tests/unit/test_readonly_uri.py:177-208`; `tests/unit/test_engine_service.py:522-529`. **#92's T1 watcher does not run the product's main route, and N1's check misses a split line.**

  1. **T1.** The runtime watcher drives `/v1/boards`, `/v1/categories`, the boot check,
     `fingerprint_of` and `_served_without`. That is exactly the list #92 gave. It does not drive
     `/v1/recommendations`, the route every question uses (`main.py:1471`), the refresh cycle's live
     read (`refresh.py:986`) or `Carry.restore` (`build.py:309`).
     1. **Mutant:** `conn = __import__("sqlite3").connect(str(path))` at `main.py:1471`, a writable
        handle under no name the AST gate reads.
     2. **Result:** 1 failed, 1608 passed. The one failure is `test_api_v1.py:549`, which
        monkeypatches `open_readonly` to provoke a 500 and so noticed that the route no longer
        calls it. No read-only guard fired.
     3. **Overclaim:** the test's name, `test_every_reader_opens_the_artifact_read_only_at_run_time`,
        says more than it runs.
  2. **N1.** The check keeps lines containing `"simctl "` and looks for `booted` on the same line.
     The mutant `xcrun simctl \` / `    uninstall booted "$BUNDLE"` added to `ios/app.sh` passed
     (33 passed in `test_engine_service.py`).

  **The fix:**
  1. Drive every route in `DECLARED_ROUTES`, including `task=coding` and one single surface, plus
     the two refresh reads, or rename the test to what it covers.
  2. Join `\`-continued lines before matching.

- **M6** `docs/plans/m18-plan.md:110-116`, `:185`, `:200-202`; `docs/plans/m18-wave-5-plan.md:28`, `:53`; `docs/prd.md:400`, `:402`; `AGENTS.md` §4. **Records.**

  1. **P4's move to W6 is not recorded where the plan says changes go.** `m18-plan.md` freezes its
     criteria and says "A later change is a plan amendment". W4 moved #74 and #56 that way
     (`:200-202`). Here:
     1. §2 W5 still lists #60 and #85 (`:112`, `:115`), and so does the inventory (`:185`);
     2. §2 W6 does not name them;
     3. the wave plan's P4 row still reads as planned (`:28`).

     Cutting P4 is within the wave plan's own valve, "P4 is the part to cut if it runs long" (`:53`),
     and the close record will say so. That makes the move honest, but recorded only in the close.
     **Nothing P4 needed slipped into P1–P3 half-done:**
     1. no change touches `test_ios_client_contract.py`'s arithmetic tripwires or a `/v1/boards`
        relay;
     2. the new REQ-APP-005 row names #60 as what is missing.

     Add an amendment line to `m18-plan.md` and move the two issues in the inventory.
  2. **Two PRD citations are wrong.**
     1. REQ-API-007 cites `test_readonly_uri.py:136`. That was right at `0a36775`; `ca8b785` then
        inserted `import sys`, and the test is now at `:137`.
     2. REQ-API-009 cites `docs/coverage-by-req.md:33`, a table separator; the row is at `:39`.

     The other 95 test and source citations I resolved hold (below).
  3. **The #52 rule has no ADR.** `AGENTS.md` §4 gains a process rule, one seat after another, each
     in its own worktree and venv, with no ADR. The profile lists "AGENTS.md … edited without ADR"
     as MINOR. D-172, its stated model, is an ADR. Either log one, or cite #52 as the rule's record
     on the line.

### PASS (what looks good)

- **The register is file-only, and the gate tests itself first.** `GapRegisterStore.load` and `save`
  refuse a non-file address (`FrontDoor.swift:308`, `:318`). The on-device store is built from
  `FileManager` file URLs, so production is unchanged. `main()` runs `self_test()` before any app
  check and returns 1 if it is broken (`client_decl_gate.py:351-358`).
  1. The self-test fails closed. An unparseable dump leaves all three expected refusals missing, and
     a fixture that does not type-check fails.
  2. With no Xcode it is skipped, and the gate reports `SKIPPED NO-ENVIRONMENT` as before.
  3. CI runs the two canned-output tests, and the skip budget moves 75 → 76 for the compiled one.
  4. The `\bURL\b` boundary does not match `URLRequest`. The canned string in
     `test_client_decl_gate.py:25-30` matches what Xcode 26 printed in my probe.
- **The tripwire is sound where the suite uses it.** The exchange swaps `+defaultSessionConfiguration`
  and `+ephemeralSessionConfiguration` once per process (`static let`). It fails every test, rather
  than crashing, if a selector is missing. All 52 test classes derive from the base;
  `StandingsStoreTests` now calls `super` in both hooks. Serial and parallel: 366 each.
- **#92's N2 and N3 are right and narrow.**
  1. N3: `isinstance(score, (int, float))` before `isfinite`. Every parser yields Python floats
     (`aider.py:100`, `arena.py:398`, `swebench.py:102`, …, and `to_pylist` in the parquet reader),
     so no valid score is newly refused.
  2. N2: `_as_stored` reuses `_calendar_date`. The two-line finite check now lives in two places
     (`ingest.py:135`, `build.py:382`); a shared helper would keep them from drifting. The served
     artifact has 0 non-finite scores and 0 malformed `run_date`s, so N2 changes nothing today.
- **The audit hook does not interfere under xdist.** It records only while `_WATCHING[0]` is set,
  only the `sqlite3.connect` event, and the test filters by its own `tmp_path`. 1609 passed under
  `-n auto`. Its cost and permanence are **R2**.
- **D-154 and D-157 follow append-only.** Each keeps its original `**Status:**` line and body, and
  gains one dated line. The cited merges exist:
  1. `829e02d` is PR #9 on 2026-09-23, `5f6ab30` is PR #6 and `eee2faf` is PR #8;
  2. `5fc3f02` is a direct push.

  `closure-report-m16.md:15`, `:40` and `:150` carry D-154 and "the owner signs by merging". D-170
  and D-166 amend them as stated. `check_records.py`: no findings.
- **The PRD rows are honest.** Every REQ id cited in `tests/` or `ios/EngineTests/` (112) has a row.
  #33's five items are each addressed:
  1. REQ-API-010 is now one requirement, and the other is renumbered REQ-API-011, with its two code
     docstrings updated;
  2. the M2 and M7 ids, REQ-IMG-001..003, REQ-SRC-010 and REQ-ANM-001 have rows;
  3. REQ-BGT-001 says no ADR records its retirement;
  4. the three stale MET rows are restated.

  REQ-APP-003 and REQ-APP-005 went MET → PARTIAL with the missing piece named.

  I resolved all 96 test and source `file:line`s the new rows cite. Each lands on a test definition,
  or once on the source line cited (`ContentView.swift:64`), whose name matches its row. The
  exception is M6(2)'s `test_readonly_uri.py:136`. The document citations I checked by hand hold,
  except `coverage-by-req.md:33`: `m10-wave-4-close.md:37`, `m14-wave-1-close.md:46` and
  `m7-plan.md:166-169`. A sample read in full:
  1. `test_arena_openrouter_contract.py:21` and `:30` hold the ≥100 and ≥20 floors;
  2. `FrontDoorTests.swift:347` asserts the image-generation decline;
  3. `.github/workflows/ci.yml:7-10`, `:54` and `contract-tests.yml:15-17`, `:110` read as cited.
- **`docs/architecture.md` matches the code where I checked it.**
  1. **Refresh:** the 23:00 window and two-hour span, 60 s grace, 4 h recent-skip, 30 min kill,
     64 KiB tail, `--fetch-epoch`/`--epoch-dir`, the group/other-writable check, the quarter
     thresholds and the "changed while building" refusal.
  2. **Phone:** the 8 s model tier, two refinements, the ephemeral 10 s session, the 4 MiB cap, the
     caches folder and `SameHostOnly`'s case-insensitive compare.
  3. **Trust boundaries:** 32 MiB, five redirects, 512 MiB and 8 MiB for the parquet child (declared
     in `arena_slices.py`), 2000 zip members, the 120-character harness cut at the API boundary
     (`main.py:897`), 40-character echo, `NSAllowsLocalNetworking`, the loopback rule with no Host
     list, the `127.0.0.1,localhost` list and the launchd label.
  4. **Startup:** five declared routes, and `validate_startup_config` at import (`main.py:653`).
- **Discipline.**
  1. Every gate change was red first (verified above), and no fix changed an assertion to pass.
  2. `90ead9d` was red, and `1d2a455` says so.
  3. No drive-by edits: each file maps to P1–P3. The `main.py` and `test_budgets_endpoint.py` edits
     are the REQ-API-011 rename, and `test_recommend_assistant.py`'s is #33's stale 1400.
  4. No new `noqa`, `type: ignore` or hard-coded path.
  5. All 13 commits carry `GP-Task: M18-W5` and no AI attribution.
  6. `AGENTS.md` is 127 lines.

## Producers of hardened invariant(s)

Producers of hardened invariant(s), from the code, with the citing test for each producer and the
gaps:

| producer | invariant | citing test | gap |
|---|---|---|---|
| `JSONDecoder`/`PropertyListDecoder.decode(…URL…)` outside `EngineClient.swift` | a decoded URL is the network (#58, D-126) | `test_client_decl_gate.py:47`, `:57` (fixture) | text gate: none (**B1**) |
| `KeyedDecodingContainer.decodeIfPresent(URL.self…)`, synthesised for `URL?` | the same | none | **B1** |
| `URL(_:strategy:)`, `NSTextCheckingResult.url`, a generic `decode(T.self)` wrapper | a URL made from text is the network | text gate catches `URL(` only | **K1** |
| `GapRegisterStore.load`/`save` (`FrontDoor.swift:308`, `:318`) | the register is only a file (#58) | `FrontDoorTests.swift:750` | none |
| `StandingsStore.load`/`save` (`StandingsStore.swift:54`, `:67`) | the standings are only a file | `StandingsStoreTests.swift:136` | none |
| `URLSession.shared`, `Data(contentsOf:)` | no Swift test reaches the network (#59) | `OfflineTestCase.swift:109` | none |
| `.default`/`.ephemeral` sessions (`OfflineTestCase.swift:53-57`) | the same | `OfflineTestCase.swift:101`, `:109` | the install can be skipped (**M1**(1)) |
| stub sessions (`EngineClientTests.swift:237`, `:420`, `:473`) | the same | `StubProtocol.canInit` is `true` (`:208`) | a declining stub (**M1**(2)) |
| `.background(…)` sessions; Swift Testing tests | the same | none | **M1**(3), (4) |
| `main.py:370`, `:1255`, `:1415`; `refresh.py:551`; `_served_without` | readers are read-only at run time (INV-23, T1) | `test_readonly_uri.py:177` | none |
| `main.py:1471` (`/v1/recommendations`); `refresh.py:986`; `build.py:309` | the same | AST gate only (`:137`) | an aliased opener survives (**M5**(1)) |
| `WRITABLE_OPENS` entries | each writer opens once (T2) | `test_readonly_uri.py:158` | none |
| `ARENA_METRIC`, `ARENA_SLICES`, `EPOCH_BOARDS` | every board metric has a direction (T3) | `test_board_standings.py:651` | none |
| `calibrate_board.py` `floor_shipped` | the label is the shipped rule (T4) | `test_calibrate_board.py:112` | none |
| `ios/app.sh` simctl calls | every call names its device (N1) | `test_engine_service.py:522` | a split line (**M5**(2)) |
| `ingest._store_scores` (`ingest.py:133-137`) | a missing score is a SourceError (N3) | `test_stored_scores_are_bounded.py:94`, `:101` | none |
| `Carry.restore` via `_as_stored` (`build.py:316-321`, `:371-389`) | carried rows meet the store's rules (N2) | `test_carry_forward.py:369` | not in D-156 (**R3**) |
| `main()` → `self_test()` (`client_decl_gate.py:351-358`) | the gate cannot pass the app while it has stopped refusing (#51) | `test_client_decl_gate.py:57` | none |
| `_code` (`test_router_hints.py:31-37`) | a pin never reads a comment (#98) | `test_router_hints.py:513` | nested comments; `/*` in `//` (**M2**) |
| `missing_closes` (`wave_check_all.py:64-92`) | a planned wave has a close (#82) | `test_wave_check_m18_rules.py:48`, `:54`, `:62` | unparsed headings (**M3**) |
| `wave_check.py:355-364` | input parsing is HIGH (#83) | `test_wave_check_m18_rules.py:91`, `:97` | three inputs (**M4**) |

## Acceptance criteria evidence

W5 adds no REQ-ID. Its criterion is "Every gate gap filed is closed with a gate shown red, and the
records drift is fixed" (`m18-plan.md:34`). Here it is per issue, against `m18-wave-5-plan.md:22-28`:
- **#68** → `docs/prd.md:418-421` (REQ-APP-002/003/005) → `test_refinements.py:60`,
  `AnswerPlanTests.swift:45`, `:143`, `CombineTests.swift:47`, `CombinePropertyTests.swift:79`.
  Records; met.
- **#33** → `docs/prd.md:210-228` (M2), `:393-402` (M7), `:422`, `:463`, `:471`, `:480`,
  `:538-542`; `docs/decisions.md:2367`, `:2634`. Records; met, except the two citations in
  **M6**(2).
- **#80** → `docs/architecture.md` (all eight sections) and `AGENTS.md` §1. Met; spot-checked
  against the code above.
- **#52, #84** → `AGENTS.md` §4. Met; no ADR (**M6**(3)).
- **#59** → `OfflineTestCase.swift:19-98` → `OfflineTestCase.swift:101`, `:109`;
  `test_swift_tests_offline.py:18`, `:27`. Red `5a3b1be`, fix `6efede4`. Met for the suite as it
  is; four bypasses (**M1**).
- **#51** → `client_decl_gate.py:333-358`, `scripts/client_decl_fixtures/` →
  `test_client_decl_gate.py:33`, `:57`. Red `93de739`, fix `90ead9d` and `1d2a455`. Met.
- **#58** → `FrontDoor.swift:308`, `:318` → `FrontDoorTests.swift:750`: **met**.
  `client_decl_gate.py:213-216`, `:264-265` → `test_client_decl_gate.py:47`: **not met**. A decoded
  `URL?` passes both gates (**B1**).
- **#98** → `test_router_hints.py:31-37` → `:513`. Red `678a830`, fix `6894083`. Met for flat
  comments; nested comments and the new erase (**M2**).
- **#92** → T1 `test_readonly_uri.py:177`; T2 `:158`; T3 `test_board_standings.py:651`; T4
  `test_calibrate_board.py:112`; N1 `test_engine_service.py:522`; N2 `test_carry_forward.py:369`;
  N3 `test_stored_scores_are_bounded.py:94`, `:101`. Red `ca8b785`, fix `f21f658`. Met as #92
  scoped it; T1 and N1 have gaps (**M5**).
- **#82** → `wave_check_all.py:64-92`, `:150-159` → `test_wave_check_m18_rules.py:48`, `:54`, `:62`.
  Met; vacuous on unparsed headings (**M3**).
- **#83** → `wave_check.py:274`, `:355-364` → `test_wave_check_m18_rules.py:91`, `:97`. Met; three
  fail-open inputs (**M4**).
- **#60, #85** → not done. Cut by the wave plan's valve (`m18-wave-5-plan.md:53`); the move is
  unrecorded in the milestone plan (**M6**(1)).

## K.8 contract drift check

`git grep -n` at `f21f658`, for the plan's symbols (`m18-wave-5-plan.md:41-47`) and the new ones:
```
scripts/client_decl_gate.py:110:NETWORK_FILE = "EngineClient.swift"
scripts/client_decl_gate.py:216:DECODES_URL = re.compile(r'decl="[^"]*\.decode\([^"]*\[with \(substitution_map[^"]*->[^"]*\bURL\b')
scripts/client_decl_gate.py:333:def self_test() -> list[str] | None:
scripts/wave_check_all.py:48:PATTERN = "docs/plans/m*-wave-*-close.md"
scripts/wave_check_all.py:60:EXPECTED_CLOSES_FROM = 18
scripts/wave_check_all.py:64:def missing_closes(root: pathlib.Path) -> list[str]:
scripts/wave_check.py:274:INPUT_PARSING_HIGH_FROM = "2026-10-04"
tests/unit/test_router_hints.py:31:def _code(swift: str) -> str:
tests/unit/test_engine_address.py:15:from .test_router_hints import _code
ios/EngineTests/OfflineTestCase.swift:86:class OfflineTestCase: XCTestCase {
src/app/workflows/build.py:60:from app.workflows.ingest import RunContext, SourceReport, _calendar_date, _store_scores
src/app/workflows/build.py:371:def _as_stored(
```
1. `NETWORK_FILE` and `PATTERN` keep their values; their line numbers moved.
2. `dump_ast` gains an optional `folder` that defaults to `CLIENT`, so existing callers are
   unchanged.
3. `_code` keeps its signature and widens what it strips; its two consumers are the three Router
   pins and `test_engine_address.py:80` (**M2**).
4. `/v1` is unchanged: the only `src/app/adapter/main.py` edit is a docstring.
5. `build.py` takes a second private name from `ingest`, beside `_store_scores`.

**Verdict: OK** for symbol drift. B1 is a behaviour finding, not a renamed contract.

## K.9 candidates spotted outside this wave's scope

- **K1** `scripts/client_decl_gate.py:101-109`. **Other ways to make a URL from text pass the compiler gate.** Compiled probes in a non-network file, each passed `problems()`: `try? URL(s, strategy: .url)` (iOS 16's parse strategy; `URL.init(_:strategy:` is not in `NETWORK`); `NSDataDetector(types: .link)` → `NSTextCheckingResult.url`; a generic `func load<T: Decodable>(_: T.Type, _: Data) -> T?` in one file, called as `load(URL.self, d)` from another (the substitution lands on `main.load`, which is not capability-checked: the file-scoped limit the docstring names). The text gate catches the first by its `URL(` spelling. Neither gate names `NSDataDetector`. Bug: one more line in `NETWORK` for the first two; the third is the #85 data-flow work.
- **K2** `docs/prd.md:326`, `:359`. **REQ-ING-010 still has two rows**, and the table row's own note, "Duplicate of line 299, which carries a different status", points at a line that has moved. #33 fixed the REQ-API-010 collision only. Docs.

## Risks queued to next M

- **R1** `ios/EngineTests/OfflineTestCase.swift:53-67`. **`URLSessionConfiguration()` trapped `xctest`.** In my scratch package, with the exchange installed, `URLSession(configuration: URLSessionConfiguration())` stopped the process with signal 5 before the probe printed anything. I did not run it again, so I do not know whether the exchange or Foundation's deprecated initialiser is the cause. If it is the exchange, a test or Engine change that builds a configuration that way would crash the suite (a crash report, possibly a dialog) rather than fail one test. What would show it: the same line in a scratch package with no `OfflineTestCase`. If it traps there too, the cause is Foundation, not the exchange.
- **R2** `tests/unit/test_readonly_uri.py:169-174`. **A process-wide, permanent audit hook in every pytest worker.** `sys.addaudithook` runs at import, so every xdist worker installs it at collection, whether or not it runs the test, and it cannot be removed. It is cheap and guarded, and I saw no interference. What would show it: a slowdown in event-heavy tests, or a second hook that vetoes `sys.addaudithook`. Installing it on first use inside the test would scope it.
- **R3** `src/app/workflows/build.py:316-321`. **N2 narrows D-156 without saying so in D-156 or REQ-REF-009.** A source whose live rows hold a non-finite score is now not carried. On a failed night, a required source then fails the build instead of serving its last rows. The artifact holds none today. What would show it: a failed night for a source whose live rows predate the M17 closure's finite check.

*Filled by: Code-Reviewer seat (independent) · Date: 2026-10-04 · Commit range: `77d3b2f..f21f658`*
