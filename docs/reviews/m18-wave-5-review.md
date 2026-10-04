---
record_type: review
id: m18-wave-5-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# M18-W5 Code Review, round 2: the gates and records backlog

**Reviewer:** a second Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, tests or
records, and I am not the round-1 seat.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `77d3b2f..a140265`. W5's own change is `git diff 4d07e50 a140265`: 49 files,
+2056 / -163. `4d07e50` is the head of `origin/wave/m18-w4`, and the two merges (`10d9e50`,
`9cc26a2`) bring it in whole, so that diff is W5's commits and nothing of W4's. Round 1 read
`77d3b2f..f21f658`; this round adds `be2434f` (round 1's verdict), `e08bb20` (PRD citations after
the second merge), `3c584a5` (red) and `a140265` (fix).
**Risk tier:** HIGH (`docs/plans/m18-wave-5-plan.md:11-13`; `m18-plan.md:106` says MED). The diff
touches `src/app/adapter/main.py` (a docstring) and the D-126 gates. D-172: no security seat on the
wave; this seat checked the gates' fail direction instead.
**Model routing (HIGH, advisory):** author-family: claude-opus / reviewer-family: claude-opus (fallback: no second family available to this seat)
**Fresh context:** this seat started with none of the authoring context and none of round 1's. I
read the base-ref policy, then both plans and the ADRs, then W5's code diff, and only then round 1's
verdict and the red and fix commits' messages. The one-line commit subjects were visible in
`git log` from the start.

**Summary.** Round 1's one BLOCKING finding is fixed. A `URL` decoded outside `EngineClient.swift`
is now refused by the compiler gate in every spelling I tried, and the gate's self-test pins the
`decodeIfPresent` form. Every round-1 MINOR is fixed or narrowed. Each code fix is held by a test I
turned red with a mutant; M6's record fixes are checked by `check_records.py` and by reading them.
Nothing blocks.

Five new MINORs remain, all in controls this wave owns:
1. **M7.** The text gate, the only D-126 check CI runs, still passes a decoded URL spelled
   `Foundation.URL?` or reached through `type(of:)`.
2. **M8.** The new `_code` scanner erases live code after a raw string or an interpolation that
   holds `/*`.
3. **M9.** `missing_closes` still excuses any heading that contains the word "dropped", and counts
   only the headings it can parse.
4. **M10.** The input-parsing HIGH rule reads "HIGH" anywhere in row 1, and the template's own row 1
   says "LOW/MED/HIGH; auto-HIGH".
5. **M11.** The Swift tripwire still has two ways around it: a background session, and a base
   reached through a `typealias`.

**Policy.** `.claude/agents/Code-Reviewer.md` and `.agents/rules/practices.md` were read from
`77d3b2f`. At that ref the matrix is `permission-matrix.md` at the repository root;
`docs/permission-matrix.md` does not exist there. `git diff --stat 77d3b2f a140265 -- .claude .agents
permission-matrix.md .github Dockerfile fly.toml epb.html or.md` is empty. `docs/decisions.md` only
gains lines (0 removed in `4d07e50..a140265`).

**How I worked.** Everything ran in this seat's detached worktree at `a140265`, with its own
`.venv` and `advisor.db`.
1. **Gate at `a140265`.**
   1. pytest `-n auto` with `MODEL_RANKING_REQUIRE_ARTIFACT=1`: **1619 passed, 25 skipped**, rc 0.
   2. ruff: all checks passed. mypy (strict, `src`): no issues in 42 files.
   3. `module_coverage_floor.py`: PASS, 42 modules. `check_records.py`: PASS, no findings.
   4. `make wave-check-all`: **PASS**, 48 v5.0-or-later records validated and 20 pre-migration
      records out of scope. It wrote only the git-ignored `.gp/installed`.
   5. `client_decl_gate.py`: self-test first, then PASS, 15 files in 4 configurations.
   6. `swift test`: **367 tests, 0 failures**. `swift test --parallel` judged by
      `swift_xunit_gate.py`: PASS, 367. `--list-tests` equals `ios/EngineTests/test-manifest.txt`
      (367 lines).
2. **Red first, re-run.** Each red commit's Python tests ran on a `git archive` of that commit, then
   of its fix, in the scratchpad, with this worktree's venv and `PYTHONPATH=<tree>/src`. Where a
   pair touched no test file, the whole suite ran.

   | red → fix | red | fix |
   |---|---|---|
   | `5a3b1be` → `6efede4` | 2 failed, 3 passed | 5 passed |
   | `93de739` → `90ead9d` | 2 failed, 1 passed | 3 passed |
   | `90ead9d` → `1d2a455` (whole suite) | 1 failed, 1588 passed | 1589 passed |
   | `678a830` → `6894083` | 1 failed, 9 passed | 10 passed |
   | `ca8b785` → `f21f658` | 6 failed, 124 passed | 130 passed |
   | `3c584a5` → `a140265` | 6 failed, 64 passed | 70 passed |

   The six red at `3c584a5` are B1 ×2, M2, M3 ×2 and M4. M1's and M5's tests were added green by
   design ("held from now on"); the mutants below show they can fail.
3. **Mutants: 29 in-place edits.** Each file was restored from a byte copy, and each restore was
   checked with `git hash-object` against `HEAD:<path>` and `git diff --quiet` (all OK).
   1. **20 broke a round-1 fix or a W5 guard, and a test or gate went red.** They are listed per id
      in the table below, plus the register's load guard (**M7**(3)).
   2. **5 survived, and they are new findings:**
      1. `Foundation.URL?` decoded in `ContentView.swift` (**M7**);
      2. a URL decoded through `type(of:)` (**M7**);
      3. `GapRegisterStore.save` without its `isFileURL` guard (**M7**);
      4. a raw string holding `/*` above a live `copy.refinements = extra` in `Router.swift` (**M8**);
      5. an interpolation holding `/*` in the same place (**M8**).

      Both Router mutants build (`swift build` rc 0).
   3. **4 were probes:**
      1. the failure view's address line under `#if false` passes every pin and the compiler gate
         (**K3**);
      2. a test class deriving through `typealias PlainCase = XCTestCase` passes the Python check
         and runs (**M11**);
      3. `XCTest.XCTestCase` as a base does not compile, so that spelling is no bypass;
      4. a URL decoded through `type(of:)` and handed to a second `EngineClient(baseURL:)` is
         refused by `test_nothing_typed_by_the_reader_reaches_the_engine` and by the compiler gate.
         Without the second client it passes the text gate (**M7**).
4. **Probes on scratch trees**, never on the repository's records:
   1. `missing_closes` on five shapes, and the real M18 plan as if M18 had closed today (**M9**);
   2. `wave_check.py` on a copy of the M18-W1 close with the template's row-1 wording (**M10**);
   3. both comment strippers, base and W5, on three erasure shapes (**M8**);
   4. `advisor.db` read-only: `scores.score` is `REAL NOT NULL`; all 13,994 rows are finite reals.
5. **Read only:** GitHub issues #107, #108, #60 and #85.
6. **Not done, by this seat's rules:**
   1. no run of `install_engine_service.sh` or `remove_engine_service.sh`, except inside
      `tests/unit/test_engine_service.py` (stubs, scratch HOME);
   2. no `launchctl`, `xcodebuild`, `simctl`, simulator or `~/Library`;
   3. no Swift probe that builds a bare `URLSessionConfiguration()` (#108), and no trap of any kind;
   4. no socket bound. The one request that left the tripwire went to `127.0.0.1:9`, inside the
      M1 mutant;
   5. no commit, push or GitHub write.
7. **Tree:** clean apart from this file.

## Verdict
PASS-WITH-MINORS

**No BLOCKING, five MINOR (M7–M11), one K.9 (K3), one risk (R4).** Round 1's B1 is fixed and held
on both D-126 gates for the forms #58 named. I recommend fixing M7, M8 and M10 in this wave. Each is
a few lines, and each is a control this wave added or claimed to close.
1. M7: the text gate still passes a decoded URL spelled `Foundation.URL?` or reached through
   `type(of:)`, and the register's save guard is held by nothing.
2. M8: the `_code` scanner erases live code after a raw string or interpolation holding `/*`. The
   base stripper saw both shapes.
3. M9: `missing_closes` excuses any heading containing "dropped", and silently skips a heading it
   cannot parse when another one parses.
4. M10: the #83 rule passes a MED close that keeps the template's row-1 wording.
5. M11: the tripwire's header still says "every way", while a background session and a
   `typealias`-derived class each go around it.

## Round 1's findings, re-checked

Each round-1 id, whether it is fixed, the test that holds it, and the mutant I used to show that
test can fail:

| id | status | held by | my mutant → result |
|---|---|---|---|
| B1 | **Fixed.** `DECODES_URL` takes `decode(?:IfPresent)?` (`client_decl_gate.py:216`); the fixture decodes a `URL?` (`client_decl_fixtures/Detail.swift:9-15`), and `FIXTURE_REFUSALS` expects it (`:220-223`); the text gate refuses `URL` as a type argument (`test_router_hints.py:417`) | `test_client_decl_gate.py:70` (canned), `:57` (compiled self-test); `test_router_hints.py:557` | (1) regex back to `decode\(` → 2 failed, and `client_decl_gate.py` prints `self-test … Detail.swift: URL.decoded was not refused`, rc 1. (2) pattern removed → `:557` failed. (3) round 1's own mutant (`struct CrBox: Decodable { let u: Optional<URL> }` in `ContentView.swift`) → text gate 1 failed, compiler gate FAIL in each configuration. Residue: **M7** |
| M1 | **Fixed for (1), (2), (4); (3) open.** (1) the base also installs per test (`OfflineTestCase.swift:108-111`), tearDown fails a test in a process where it never installed (`:116-117`), and the Python check sees a class hook that skips super (`test_swift_tests_offline.py:27-34`). (2) the `protocolClasses` setter is exchanged and appends the tripwire last (`OfflineTestCase.swift:60`, `:89-96`). (4) `import Testing` is refused (`test_swift_tests_offline.py:53`). (3) a background configuration: no change | `OfflineTestCase.swift:132` (`testARequestAStubDeclinesIsCaughtToo`); `test_swift_tests_offline.py:37`, `:44`, `:53` | (1) setter exchange removed → `testARequestAStubDeclinesIsCaughtToo` failed: `("[]") is not equal to ("["http://127.0.0.1:9/declined"]")`. (2) `override class func setUp() {}` in `RefinementsTests` → `:44` failed; Swift still 7/7 green, because the per-test install covers it. (3) the same plus the base's instance `setUp` removed → 7 of 7 failed: "the tripwire was never installed in this process (#59)". (4) `import Testing` → `:53` failed. Residue: **M11** |
| M2 | **Fixed for nested comments, `/*` inside `//`, and plain strings** (`test_router_hints.py:31-68`) | `test_router_hints.py:565`; `test_engine_address.py:80` | (1) the regex stripper put back → `:565` failed. (2) round 1's nested comment around the failure view's address line → `test_the_failure_screen_shows_the_address_the_app_asked` failed. (3) `// see /* the old note` above a live `copy.refinements = extra` → the Router refinements pin failed. Residue: **M8** |
| M3 | **Half fixed.** A closed milestone whose plan yields no wave heading is a finding (`wave_check_all.py:90-92`), and `## Wave N` and `### M19-WN` are read (`:63`). The "dropped" substring is unchanged (`:94`) | `test_wave_check_m18_rules.py:102`, `:113` | (1) the fail-closed branch removed → `:102` failed. (2) the heading regex narrowed back → `:113` failed. Residue: **M9** |
| M4 | **Fixed, all three.** An undated close is graded, the footprint is read up to the next field in any order, and `src/app/clients\b` is matched (`wave_check.py:360-367`) | `test_wave_check_m18_rules.py:125` | each of the three reverted alone → `:125` failed each time. New fail-open beside it: **M10** |
| M5 | **Fixed.** T1 drives `/v1/recommendations` (`test_readonly_uri.py:200`); N1 joins `\`-continued lines (`test_engine_service.py:527`) | `test_readonly_uri.py:177`; `test_engine_service.py:522` | (1) `__import__("sqlite3").connect(str(path))` at `main.py:1471` → T1 failed: "opened the served artifact writable". (2) the same at `refresh.py:986` → T1 failed. (3) the same at `build.py:309` → `test_carry_forward.py:315` failed. (4) `xcrun simctl \` / `uninstall booted "$BUNDLE"` added to `ios/app.sh` → N1 failed |
| M6 | **Fixed.** (1) `m18-plan.md:204-206` records #60/#85's move to W6. Like W4's amendment (`:200-202`), it leaves §2 and the §7 inventory as they were. (2) REQ-API-007 cites `test_readonly_uri.py:137`, the test's `def`; REQ-API-009 cites `coverage-by-req.md:39`, row 6. (3) D-174 (`decisions.md:3469`), cited from `AGENTS.md` §4 (`:77`) | records; `check_records.py` PASS | — (records) |
| K1 | **Filed** #107, open, M18 milestone | — | not re-probed |
| K2 | **Fixed.** REQ-ING-010's duplicate table row is gone; one section remains (`prd.md:326`) | `check_records.py` PASS | — |
| R1 | **Filed** #108, open | — | not probed (this seat's rule 3). The fix round widened its surface: **R4** |
| R2 | Unchanged: `sys.addaudithook` at import (`test_readonly_uri.py:174`). Still a queued risk; I saw no interference in 1619 tests under `-n auto` | — | — |
| R3 | **Fixed in the records.** The D-156 note (`decisions.md:2607`) and REQ-REF-009 (`prd.md:580`) say a non-finite score is not carried | `test_carry_forward.py:369` | none needed. The artifact holds 0 NULL and 0 non-finite scores (`score REAL NOT NULL`), so N2 changes nothing served today |

## Findings

### BLOCKING (must fix before this wave closes)
- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M7** `tests/unit/test_router_hints.py:413-417`, `:557-562`; `ios/ModelRanking/Engine/FrontDoor.swift:318`; `ios/EngineTests/FrontDoorTests.swift:749-760`. **#58's text-gate half covers the type-argument spellings and nothing past them, and the register's save guard is held by no test.**

  B1's fix gave the text gate `[<\[,(]\s*URL\b`. Its test says "a URL decoded from text needs `URL`
  as a type argument". Two mutants in `ContentView.swift`, each decoding a URL from the reader's
  text, show that claim is false:
  1. `struct CrBox: Decodable { let u: Foundation.URL? }`, decoded, returned as `Foundation.URL?`:
     text gates **46 passed**. A module-qualified `URL` meets neither `:\s*\[?\s*URL\b` nor the new
     pattern.
  2. `func crProbeInfers(_ blob: String) -> URL? { try? JSONDecoder().decode(type(of:
     EngineClient.localDefault), from: Data(blob.utf8)) }`: text gates **46 passed**. `-> URL` is
     not a pattern, and `type(of:)` names no type.

  The compiler gate fails on both, rc 1 (`ContentView.swift: Foundation.URL.decoded is the
  network`). So the defence holds where Xcode is, which is `make check` on the owner's Mac. CI runs
  only the text gate, and there the decode is invisible. Round 1 offered this choice: a pattern, or a
  stated limit. The fix took the pattern and states no limit.

  Two more points on the same issue:
  3. **The register's save guard is held by nothing.** I removed `url.isFileURL` from
     `GapRegisterStore.save` (`FrontDoor.swift:318`). `GapRegisterHardeningTests` passed (7 of 7),
     and so did the text gates. `Data.write(to:)` never goes through URL loading, so the tripwire
     cannot see it. The test's comment says "Neither a load nor a save may touch an address that is
     not a file; the offline tripwire would record either" (`FrontDoorTests.swift:751-753`); for the
     save it would not. The load guard is held: removed, the test fails with the tripwire recording
     `https://example.invalid/gap-register.json`. The new test was also inserted under the doc
     comment of the test after it: `/// And a save into a fresh folder round-trips, folder created
     on the way.` (`:749`) now documents `testTheRegisterIsOnlyEverAFileOnThisDevice`.
  4. **What the new pattern refuses that the app needs.** Nothing in the app today: no client file
     matches it. But it has no `EngineClient.swift` entry in `EGRESS_PERMITTED`. So the compiler
     gate's own fixture, which says `EngineClient.swift` may decode `[URL]`
     (`client_decl_fixtures/EngineClient.swift:8-10`), would fail the text gate as real code. The
     two D-126 gates now disagree about the one door. That is stricter, not looser, but whoever
     first needs a decoded URL in `EngineClient.swift` will meet a refusal that the compiler gate's
     fixture says is wrong.

  **The fix:**
  1. Add `\.\s*URL\b` (any qualified `URL`) and `->\s*\(?\s*URL\b` to `EGRESS`, with
     `EngineClient.swift` entries where the door needs them.
  2. Write in `client_decl_gate.py`'s docstring and the close record that the text gate cannot see
     a type it never names (`type(of:)`), so CI's D-126 check does not see decoding in general.
  3. Pin the save guard where it can be observed, or drop "or a save" from the test's comment, and
     move the stray doc comment back to its test.

- **M8** `tests/unit/test_router_hints.py:31-68`. **The `_code` scanner still erases live code: a raw string or a string interpolation holding `/*` opens a "comment" that Swift never sees.**

  The docstring says "comment markers inside a string literal are text". That holds for `"…"` and
  `"""…"""`, and fails for two other literal forms. Each mutant below was appended to `Router.swift`
  above a live `copy.refinements = extra`, and each builds (`swift build` rc 0):
  1. `let note = #"a"/*"#`. The scanner ends the string at the inner `"`, so `/*` opens a comment.
     Swift reads one raw string whose content is `a"/*`.
  2. `let note = "\(tags["/*"] ?? "")"`. The scanner ends the string at the quote inside the
     interpolation, so `/*` again opens a comment.

  Nothing after the mutant closes the "comment", so `_code` returns nothing from there to the end of
  the file. Placed higher in a file, it would erase up to the next `*/` anywhere, including one in a
  `//` line. `test_only_the_model_output_boundary_builds_an_outcome_with_refinements` **passes (12
  passed)**. That pin holds D-168 clause 4, and its own docstring says it is the only holder where
  the embedding assets do not load.

  Base vs. W5, on `_code` directly:

  | shape | base `77d3b2f` sees the assignment | `a140265` sees it |
  |---|---|---|
  | `let s = "//"; copy.refinements = extra` | no | yes |
  | raw string with `/*`, then the assignment | yes | **no** |
  | interpolation with `/*`, then the assignment | yes | **no** |

  So the wave traded one bypass for two, and the two new ones erase to the end of the file, not only
  to the end of a line.

  **The fix:**
  1. Scan `#…"…"#` raw strings by their `#` count.
  2. Track `\(`…`)` depth, with nested strings, inside a string.
  3. **Fail closed.** If the scan ends inside a block comment, raise. Swift cannot compile an
     unclosed `/*`, so ending inside one means the scanner misread the file.

  Pin all three with the two shapes above.

- **M9** `scripts/wave_check_all.py:89-95`. **`missing_closes` still excuses any heading containing "dropped", and counts only the headings it can parse.**

  Round 1's M3 asked for two things. This round did the first (a plan with no parseable heading is a
  finding) and not the second. Probes on scratch trees, each a closed M19:
  1. `### W1 — one` (closed) and `### W2 — the dropped-frames fix` (not closed) → **0 missing**. The
     excuse is the substring `"dropped" in rest.lower()` (`:94`).
  2. `### W1 — one` (closed) and `### Wave two — the second` (not closed) → **0 missing**. One
     heading parses, so the new no-wave check does not fire, and the second wave is never counted.
  3. `### **W1** — one` and `### **W2** — two`, nothing closed → fails closed, as designed.
  4. `### W1: one` (closed) and `### W2: two` → W2 missing, as designed.

  What holds:
  1. On the real M18 plan, as if M18 had closed today, it lists W2–W6 correctly.
  2. Nothing before M18 is graded (`EXPECTED_CLOSES_FROM = 18`, GPF-001).
  3. `make wave-check-all` passes on the repository: no closure report from M18 on exists yet.

  **The fix:**
  1. Match "dropped" as a marked token, for example `\(dropped\b` or `— dropped`.
  2. Count a heading that names a wave in any spelling (`W\d|Wave\b`). One that does not parse is a
     finding, even when its neighbours parse.

- **M10** `scripts/wave_check.py:364-366`; `docs/wave-checklist.template.md:33`. **The #83 rule passes a MED close that keeps the template's row-1 wording, because that wording contains "HIGH".**

  The rule takes row 1 whole and asks for `\bHIGH\b` anywhere in it. The template's row 1 reads "Risk
  tier recorded for this wave in the plan (LOW/MED/HIGH; auto-HIGH if the diff touches
  authz/secrets/crypto/input-parsing/egress)". Probe: the M18-W1 close, built the way the test's
  `_record` builds it (dated 2026-10-04, tier MED, `Touched: src/app/clients/epoch.py`):
  1. with the close's own row-1 wording: **rc 1**, the rule fires;
  2. with the template's row-1 wording: **rc 0**, the rule is silent.

  The M15–M18 closes happened to shorten that cell, which is why nothing fails today. Evidence that
  says "MED; the HIGH globs were not touched" would pass the same way, by the same regex. It fails open, beside the three
  inputs round 1's M4 closed. GPF-001 holds: no close is dated on or after 2026-10-04, and none
  in scope is undated, so nothing existing is graded.

  **The fix:** read the tier from the evidence cell's `risk: **X**` token, the shape every close and
  the test already use, and refuse a row-1 evidence cell that has none.

- **M11** `ios/EngineTests/OfflineTestCase.swift:8-17`; `tests/unit/test_swift_tests_offline.py:18-24`. **The tripwire still has two ways around it, and its header still says it catches "every way a test could fetch".**

  1. **A background configuration** (round 1's M1(3)). Nothing changed. Background sessions run
     out of process and ignore custom protocol classes, so no exchange can catch them. Only a source
     check can: refuse `background(withIdentifier` in `ios/EngineTests/` and the Engine sources.
     Today 0 uses.
  2. **A base reached through a `typealias`.** I added `typealias PlainCase = XCTestCase` and made
     `RefinementsTests` derive from `PlainCase`:
     1. `test_swift_tests_offline.py`: **4 passed**;
     2. `swift test --filter RefinementsTests`: 7 passed, with none of the base's tearDown checks.

     The check matches `: XCTestCase` as spelled. The same `typealias` in a client file is refused
     by the text gate; in the test target nothing refuses it.

  **The fix:**
  1. Refuse `background(withIdentifier` and `typealias … = XCTestCase` in the Python check.
  2. Better, if it proves workable: check from the Swift side, once per process, that every test
     class in the bundle inherits `OfflineTestCase`, for example by walking `XCTestSuite.default`.
     I did not build this.
  3. Narrow the header to what it catches.

  **The setter exchange itself is sound**, and I checked the three things the brief asked about:
  1. **No test relies on the old list.** Every stub session in the suite sets
     `protocolClasses = [StubProtocol.self]` (`EngineClientTests.swift:238`, `:421`, `:474`), and
     `StubProtocol.canInit` is `true` (`:208`). So the list becomes `[StubProtocol, Tripwire]`, and
     the stub answers first. All 367 tests pass serially and in parallel.
  2. **A stub can lose its request only one way:** a test that appends its stub after
     `.ephemeral`'s list, which already starts with the tripwire. No test does, and the same
     ordering was true before this round.
  3. **The exchange cannot recurse.** The class getters set a list that already contains the
     tripwire, so the exchanged setter appends nothing. If any exchange fails, `notInstalled` fails
     every test rather than trapping.

### PASS (what looks good)

- **B1 is closed on the authority gate, and the gate tests itself first.**
  1. `make client-decls` runs `self_test()` before the app (`client_decl_gate.py:351-358`), and the
     fixture now refuses `URLSession`, `FileManager` and two decoded-URL shapes.
  2. Reverting the rule fails both the canned test and the compiled self-test.
  3. Round 1's exact mutant is refused by both gates.
  4. The skip budget's +1 (`docs/skip-budget.txt`, 75 → 76) is the compiled fixture CI cannot run,
     and the Mac's 25 skips match.
- **Every round-1 fix was red first**, six for six at `3c584a5`. No fix weakened an assertion to
  pass. `a140265` edits two test files:
  1. `test_router_hints.py`, for gate code that lives there (the scanner and the `EGRESS` pattern);
  2. one assertion in `test_wave_check_m18_rules.py:94`, which drops the slash from
     `"src/app/clients/"` to match the widened message. The assertion is no weaker for it.
- **The fail-closed changes respect GPF-001.**
  1. `missing_closes` grades only milestones from M18 that have a closure report. None exists, so
     today it grades nothing.
  2. The HIGH rule grades closes dated from 2026-10-04, or undated. No in-scope close is either, and
     `wave_check.py:325-331` already holds an undated close to today's version.
  3. `make wave-check-all` is PASS on the tree.
- **N2 and N3 are narrow and correct.**
  1. `_as_stored` reuses `_calendar_date` and refuses a non-finite or non-numeric score.
  2. The artifact holds 13,994 finite `REAL NOT NULL` scores and only NULL or 10-character
     `run_date`s, so nothing served changes.
  3. N3's `isinstance` guard turns `isfinite(None)`'s `TypeError` into a `SourceError`, which a
     caller treats as a failed source (`test_stored_scores_are_bounded.py:94`).
- **T1 now drives the product's route** and the refresh's expiry-night read. The one artifact
  reader it does not drive, `Carry.restore`, has its own read-only test
  (`test_carry_forward.py:315`), which killed my mutant there.
- **The records hold where I traced them.**
  1. All 108 `file:line` citations the new PRD rows add resolve. 106 land on a test or definition
     line. The other two are deliberate source citations: the contract test's `pytestmark` skip
     (`test_arena_openrouter_contract.py:15`) and `ContentView.swift:64`'s `budget = "unlimited"`.
  2. In `docs/architecture.md` I checked 32 MiB and five redirects (`protocols.py:49`, `:55`), 120
     characters (`main.py:897`), 40 (`main.py:738`), 64 (`registry.py:501`), 4 MiB (`maxStandingsBytes`)
     and the 60 s release wait (`install_engine_service.sh:190`). All match.
  3. D-154 and D-157 gain a dated status line each, with bodies untouched. D-174 follows D-173's
     status form ("decided by the agent on the owner's standing instruction").
- **Discipline.**
  1. All 17 non-merge W5 commits carry `GP-Task: M18-W5`. None carries `Co-Authored-By` or
     "Generated with".
  2. `AGENTS.md` is 127 lines.
  3. No new `noqa`. One new `# type: ignore[union-attr]` sits in a test (`test_wave_check_m18_rules.py`);
     `make typecheck` reads `src` only, so it is inert, not wrong.
  4. Nothing outside P1–P3 changed. P4 (#60, #85) is moved by amendment, not half-done.

## Producers of hardened invariant(s)

Producers, from the code, with the citing test per producer, and the gaps:

| producer | invariant | citing test | gap |
|---|---|---|---|
| `JSONDecoder`/`PropertyListDecoder.decode(…URL…)` outside `EngineClient.swift` | a decoded URL is the network (#58, D-126) | compiler: `test_client_decl_gate.py:47`, `:57`; text: `test_router_hints.py:557` | text gate: `Foundation.URL`, `type(of:)`, `-> URL` (**M7**) |
| `KeyedDecodingContainer.decodeIfPresent(…URL…)`, synthesised for `URL?` | the same | `test_client_decl_gate.py:70`, `:57` (fixture `Detail.swift:9-15`) | none on the compiler gate |
| `URL(_:strategy:)`, `NSDataDetector`, a generic decode wrapper | a URL made from text is the network | text gate catches `URL(` only | #107 (K1) |
| `GapRegisterStore.load` (`FrontDoor.swift:308`) | the register is only a file (#58) | `FrontDoorTests.swift:750` | none |
| `GapRegisterStore.save` (`FrontDoor.swift:318`) | the same | none observable | **M7**(3) |
| `URLSession.shared`, `Data(contentsOf:)` | no Swift test reaches the network (#59) | `OfflineTestCase.swift:142` | none |
| `.default`/`.ephemeral` sessions (`OfflineTestCase.swift:77-87`) | the same | `OfflineTestCase.swift:124`, `:142` | none |
| stub sessions (`EngineClientTests.swift:238`, `:421`, `:474`), via the setter (`OfflineTestCase.swift:89-96`) | the same | `OfflineTestCase.swift:132` | none |
| the install itself (`OfflineTestCase.swift:101-111`) | every test runs guarded | tearDown `:116-117`; `test_swift_tests_offline.py:44` | a `typealias` base (**M11**) |
| `.background(…)` sessions | the same | none | **M11** |
| `main.py:370`, `:1255`, `:1415`, `:1471`; `refresh.py:551`, `:986` | readers are read-only at run time (INV-23, T1) | `test_readonly_uri.py:177` | none |
| `Carry.restore` (`build.py:309`) | the same | `test_carry_forward.py:315` | none |
| `_store_scores` (`ingest.py:133-137`) | a missing score is a SourceError (N3) | `test_stored_scores_are_bounded.py:94`, `:101` | none |
| `Carry.restore` via `_as_stored` (`build.py:316-321`, `:371-389`) | carried rows meet the store's rules (N2) | `test_carry_forward.py:369` | none |
| `ios/app.sh` simctl calls | every call names its device (N1) | `test_engine_service.py:522` | none |
| `_code` (`test_router_hints.py:31-68`) | a pin never reads a comment (#98) | `test_router_hints.py:548`, `:565` | raw strings, interpolation (**M8**); `#if false` (K3) |
| `missing_closes` (`wave_check_all.py:74-103`) | a planned wave has a close (#82) | `test_wave_check_m18_rules.py:48`, `:54`, `:62`, `:102`, `:113` | "dropped" substring; partial parse (**M9**) |
| `wave_check.py:360-367` | input parsing is HIGH (#83) | `test_wave_check_m18_rules.py:91`, `:97`, `:125` | the template's row-1 wording (**M10**) |

## Acceptance criteria evidence

W5 adds no REQ-ID. Its criterion is "Every gate gap filed is closed with a gate shown red, and the
records drift is fixed" (`m18-plan.md:34`). Here it is per issue, against
`m18-wave-5-plan.md:22-28`:
- **#68** → `docs/prd.md` REQ-APP-002/003/005 → `test_refinements.py:60`, `AnswerPlanTests.swift:45`,
  `:143`, `CombineTests.swift:47`, `CombinePropertyTests.swift:79`. Records; met.
- **#33** → the M2 and M7 rows, REQ-API-010/011, `decisions.md:2367`, `:2636`. Met, including
  round 1's two citations.
- **#80** → `docs/architecture.md`, `AGENTS.md` §1. Met; spot-checked above.
- **#52, #84** → `AGENTS.md:77`, D-174 (`decisions.md:3469`). Met.
- **#59** → `OfflineTestCase.swift:22-121` → `OfflineTestCase.swift:124`, `:132`, `:142`;
  `test_swift_tests_offline.py:18`, `:37`, `:44`, `:53`. Red `5a3b1be` and `3c584a5`, fixes
  `6efede4` and `a140265`. Met; **M11**.
- **#51** → `client_decl_gate.py:333-358`, `scripts/client_decl_fixtures/` →
  `test_client_decl_gate.py:33`, `:57`. Met.
- **#58** → `FrontDoor.swift:308` → `FrontDoorTests.swift:750`; `client_decl_gate.py:216` →
  `test_client_decl_gate.py:47`, `:70`, `:57`; `test_router_hints.py:417` → `:557`. Met on the
  compiler gate; the text gate and the save guard are **M7**.
- **#98** → `test_router_hints.py:31-68` → `:548`, `:565`; `test_engine_address.py:80`. Met for
  comments; **M8**.
- **#92** → T1 `test_readonly_uri.py:177`; T2 `:158`; T3 `test_board_standings.py:648`; T4
  `test_calibrate_board.py:112`; N1 `test_engine_service.py:522`; N2 `test_carry_forward.py:369`; N3
  `test_stored_scores_are_bounded.py:94`, `:101`. Red `ca8b785`, fix `f21f658`. Met.
- **#82** → `wave_check_all.py:74-103` → `test_wave_check_m18_rules.py:48`, `:54`, `:62`, `:102`,
  `:113`. Met; **M9**.
- **#83** → `wave_check.py:273-274`, `:360-367` → `test_wave_check_m18_rules.py:91`, `:97`, `:125`.
  Met; **M10**.
- **#60, #85** → not in W5. They moved to W6 by amendment (`m18-plan.md:204-206`). Both are open with
  no milestone set on GitHub.

## Every file in the diff

`git diff --stat 4d07e50 a140265`, 49 files. I read every file's diff in full, except
`docs/architecture.md` and `docs/prd.md`, which I checked as described under PASS:
1. **Records (8).**
   1. `AGENTS.md`: §1 restated (#80); §4's seat rule (#52, D-174).
   2. `docs/architecture.md`: rewritten for the product after M18-W4 (#80).
   3. `docs/decisions.md`: D-154 and D-157 status lines (#33); the D-156 note (#92 N2); D-174.
   4. `docs/plans/m18-plan.md`: the W5 amendment.
   5. `docs/plans/m18-wave-5-plan.md`: new.
   6. `docs/prd.md`: #68, #33 and REQ-REF-009.
   7. `docs/reviews/m18-wave-5-review.md`: this file.
   8. `docs/skip-budget.txt`: 75 → 76.
2. **The phone (17).**
   1. `OfflineTestCase.swift`: new, the tripwire.
   2. Fourteen test files move each class onto `OfflineTestCase`, with no other change, except two:
      1. `FrontDoorTests.swift` adds the register test;
      2. `StandingsStoreTests.swift` calls super in both hooks.

      The fourteen are `AnswerPlan`, `CombineProperty`, `Combine`, `Detail`, `EngineClient`,
      `FrontDoor`, `Language`, `OwnerSessionDefect`, `RefinementBoundary`, `Refinements`,
      `RouterBoundary`, `Scores`, `StandingsStore` and `Uncertainty`.
   3. `EngineClientTests.swift` also restates one doc comment on the retired budget picker.
   4. `test-manifest.txt`: +4 tests.
   5. `FrontDoor.swift`: the register is file-only.
3. **Gates (7).**
   1. `client_decl_gate.py`: `URL.decoded`, `self_test`, the fixture folder.
   2. Four fixtures in `scripts/client_decl_fixtures/`.
   3. `wave_check.py`: #83.
   4. `wave_check_all.py`: #82.
4. **Engine (3).**
   1. `main.py`: a docstring id, REQ-API-011.
   2. `build.py`: N2.
   3. `ingest.py`: N3.
5. **Tests (14).** `test_board_standings` (T3), `test_budgets_endpoint` (the REQ-API-011 rename),
   `test_calibrate_board` (T4), `test_carry_forward` (N2), `test_client_decl_gate` (#51, #58),
   `test_engine_address` (`_code` alone), `test_engine_service` (N1), `test_readonly_uri` (T1, T2),
   `test_recommend_assistant` (#33's stale 1400), `test_router_hints` (`_code`, `EGRESS`, #58),
   `test_stored_scores_are_bounded` (N3), `test_swift_test_manifest` (the base class in its
   pattern), `test_swift_tests_offline` (#59) and `test_wave_check_m18_rules` (#82, #83).

## K.8 contract drift check

`git grep -n` at `a140265`, for the plan's three symbols (`m18-wave-5-plan.md:41-47`) and the ones
this wave added:
```
scripts/client_decl_gate.py:110:NETWORK_FILE = "EngineClient.swift"
scripts/client_decl_gate.py:216:DECODES_URL = re.compile(r'decl="[^"]*\.decode(?:IfPresent)?\([^"]*\[with \(substitution_map[^"]*->[^"]*\bURL\b')
scripts/client_decl_gate.py:333:def self_test() -> list[str] | None:
scripts/wave_check.py:274:INPUT_PARSING_HIGH_FROM = "2026-10-04"
scripts/wave_check_all.py:48:PATTERN = "docs/plans/m*-wave-*-close.md"
scripts/wave_check_all.py:60:EXPECTED_CLOSES_FROM = 18
scripts/wave_check_all.py:63:WAVE_HEADING = re.compile(r"^#{2,4}\s*(?:M\d+-)?W(?:ave\s*)?(\d+)\b(.*)$", re.M)
scripts/wave_check_all.py:66:def _excused_waves(ledger: pathlib.Path) -> set[str]:
scripts/wave_check_all.py:74:def missing_closes(root: pathlib.Path) -> list[str]:
tests/unit/test_router_hints.py:31:def _code(swift: str) -> str:
tests/unit/test_engine_address.py:15:from .test_router_hints import _code
ios/EngineTests/OfflineTestCase.swift:60:        exchange("setProtocolClasses:", "offlineSetProtocolClasses:", classMethod: false)
ios/EngineTests/OfflineTestCase.swift:90:    @objc func offlineSetProtocolClasses(_ classes: [AnyClass]?) {
ios/EngineTests/OfflineTestCase.swift:100:class OfflineTestCase: XCTestCase {
src/app/workflows/build.py:60:from app.workflows.ingest import RunContext, SourceReport, _calendar_date, _store_scores
src/app/workflows/build.py:371:def _as_stored(
```
1. `NETWORK_FILE`, `PATTERN` and `_code`'s signature are unchanged. `_code` now strips more, and its
   only consumers are the three Router pins (`test_router_hints.py:162`, `:187`, `:207`) and
   `test_engine_address.py:80`.
2. `dump_ast` gains an optional `folder` that defaults to `CLIENT`, so existing callers are
   unchanged.
3. `/v1` is unchanged: the only `main.py` edit is a docstring.

**Verdict: OK.** No symbol drifted. M7–M11 are behaviour findings.

## K.9 candidates spotted outside this wave's scope

- **K3** `tests/unit/test_router_hints.py:31-68`; `tests/unit/test_engine_address.py:73-88`. **A pin is satisfied by code the compiler never builds: code under `#if false`, or text inside a string literal.** `_code` removes comments only, which is all #98 asked. Probe: the failure view's `if let address = error.addressNote(client.baseURL, language) { Text(address)… }` wrapped in `#if false` / `#endif`. Results: `test_the_failure_screen_shows_the_address_the_app_asked` and every other text gate pass (46 passed); `client_decl_gate.py` passes too. The compiler's own count shows the line left the build: 1925 → 1923 declarations per configuration. The scanner also keeps string literals in its output, so a positive pin can be met by a string quoting the code. Bug, same class as #98: drop `#if false`/`#if never` blocks and string contents from `_code`'s output, or hold the address line from `swift test` once the view is testable.

## Risks queued to next M

- **R4** `ios/EngineTests/OfflineTestCase.swift:60`, `:89-96`. **The setter exchange widens #108's surface.** Since `a140265`, every `protocolClasses` assignment in the test process runs the swizzled setter. That includes any assignment Foundation makes on a configuration it builds itself. #108 (a bare `URLSessionConfiguration()` trapped `xctest` with signal 5, cause unmeasured) was filed before this exchange existed, and it is still open. I did not probe it, by this seat's rules. The suite is green and nothing in the target builds a bare configuration. What would show it is real: #108's own measurement, first without the exchange and then with it, made somewhere a trap cannot raise a dialog on the owner's Mac. If the trap appears only with the exchange, a future test or Engine change that builds a configuration that way would crash the suite rather than fail one test.

*Filled by: Code-Reviewer seat, round 2 (independent) · Date: 2026-10-04 · Commit range: `77d3b2f..a140265`*
