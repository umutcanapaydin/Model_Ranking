---
record_type: review
id: backlog-hardening-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-14
---
# Independent review, round 2: the hardening wave (#276, #271, #272, #275, #274, D-198)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-14
**Commit range:** `01c0fc0..9e799b4` (17 commits; `origin/main` is `01c0fc0`). Round 1's fixes are
`b2ece4d` (red), `05ebda7` and `9e799b4`.
**Risk tier:** MEDIUM for the gates (#271, #272, #274, #275); HIGH for #276 (the egress pin, INV-62,
INV-67, G-13)
**Round:** 2 of at most 4. Fresh context: this seat read no authoring session. The author's model family
is not known to this seat, so no cross-family note is made.

## Verdict
MINOR

Every round-1 disposition holds. Each round-1 probe was planted again and now fails where it passed.
The red commit `b2ece4d` fails all seven of its tests, and `9e799b4` passes them.

Seven minor findings remain. Ids are this round's own (N1 to N7), not round 1's.
- Two are the unfinished parts of round-1 remedies: N1 (the M1 remedy's re-check of every `# raw:`
  reason) and N3 (the N1 remedy's INV-78 sentence).
- Two are D-198 sentences that say a little more than the code holds: N2 (clause 4, `_swift`) and N4
  (clause 3, "no code").
- Two are residues that are fine to keep, but are not tracked where the dispositions say: N5 (a wrapped
  blockquote) and N6 (`Foundation.URL`, "#242's").
- N7: the process log's entry for this wave now says what round 1 showed false.

None of them lets a whole class through. The worst, N1, lets one Swift test class skip the tripwire's
check. A leak from it then fails a later test, measured, but under another test's name.

How the review was done:
- **Reading.** Round 1's record and its dispositions, D-198 (`docs/decisions.md:5084`), INV-78, G-13
  and G-15's paragraph in `docs/security-invariants.md`, the process log entry, #278 and #242
  (`gh issue view`), the diff `d62fdbd..9e799b4`, and again the whole range `01c0fc0..9e799b4`.
- **Plants.** Two exports of `9e799b4` and one of `b2ece4d`, each made with `git archive` into a scratch
  folder outside the seat. Every plant went there. Each planted file was then written back from
  `git show 9e799b4:<path>` and compared byte for byte, and each compare passed. A probe file added
  for one plant was deleted after it. The rule probes ran in scratch folders. The backlog-order probes
  ran on scratch repositories and on a scratch clone of the seat. After the last probe, a recursive diff
  of the main export against the seat showed no difference but the seat's caches. The seat's tree is
  unchanged but for this record (`git status` empty before it was written).
- **Swift runs.** In the export, inside `scripts/offline.sb` with `MODEL_RANKING_REQUIRE_OFFLINE=1`, as
  `make swift-test` runs them. Every planted address is `example.invalid`.
- **Baselines in the seat.** Full Python suite: 2897 passed, 29 skipped. `check_records.py` PASS, its
  self-test PASS, `ruff check src tests scripts` clean, `wave_check_all.py` PASS, and
  `branch_adr_problems` on the seat's own range (`01c0fc0..HEAD`) finds nothing.
- **Read trace.** The whole unit suite ran on the export with a scratch pytest plugin. It logged every
  `read_text`, `read_bytes` and `open` of a `.swift` file or a file under `ios/`, with its call site in
  `tests/`. Result: 2828 passed, 69 skipped (the export has no `.git` and no database). Eleven call
  sites read Swift with no `_code(`, `_swift(` or `# raw:` on their line. None is a presence pin on the
  app's Swift:
  - three are shutil copies made for plants;
  - one is `_swift` itself;
  - one is the gate's own fixtures, and one is L1 reading scratch files;
  - three are `swift_xunit_gate.py` reading for skips;
  - two are absence scans the guard cannot see (`test_adr_citations.py:75` and
    `test_engine_service.py:544`), both rightly raw.
- **Held-out discipline.** I read no held-out file and printed no held-out question. The leak probes used
  two made-up questions. The live-set tests ran as the suite runs them, and only their pass or fail was
  read.

## Round 1, planted again

| Round 1 | Probe planted again | Result now |
|---|---|---|
| M1 | Round 1's exact plant: the base's `tearDown` in `/* */`, and a live one after it that calls only `_ = OfflineGuard.drain()` and `super.tearDown()`. | Fails: `test_the_base_fails_a_test_whose_requests_it_recorded`. Holds. The rest of round 1's remedy, re-checking each `# raw:` reason, is N1 below. |
| M2 | `Text(priceInPages(pick.blendedPerM, in: language))` turned into a `//` line (`ContentView.swift:1356`). Then a `//` copy of a required line against four more moved pins: `test_engine_address.py` (the `// MARK:` slice), `test_ios_platform_drift.py` (`.iOS(.v18)` in a comment above a live `.v17`), `test_uitext_sentence_rows.py` (a row), `test_engine_host.py` (the `unknown_host` line). | Each fails. Holds. The guard still accepts `_swift` for a new pin (N2). |
| M3 | Made-up questions in `_record_matches`: a long one wrapped, a long one with two spaces, a short one in backticks, a short one in backticks wrapped across a line, a short one in double quotes, a long one wrapped in a list item. | All found. Holds. A long one wrapped inside a blockquote is not found (N5). |
| N1 | A cited test (`testTheRegisterIsOnlyEverAFileOnThisDevice`) renamed, with its old `func` line in a block comment. | Fails: `test_the_list_holds_together`. Holds. INV-78 does not say what D-198 now says (N3). |
| N2 | In scratch files, each version of `check_records.py` run: `#"bu bir \#u{15F}ey"#`; the same with `##`; JSON ``` around an escaped Turkish letter; JSON ``` around a raw one; Swift `\u{60}` around a raw one. | Flagged by `9e799b4`, all five. At `01c0fc0` the first three pass, so the raw-string escapes and the round-1 regression are both fixed. Escaped Turkish between literal backticks in JSON or Swift still passes, as at `01c0fc0`. Round 1 only suggested a change there, and D-198 clause 1 does not claim it. |
| N3 | A scratch clone of the seat at `9e799b4`. `origin/main` at `01c0fc0`, then at `55da886` (one merge back), then a depth-1 clone. | No findings at `01c0fc0`. At `55da886`, D-196 and D-197, each "read on 55da886..HEAD": the range is named. The depth-1 clone skips. #278 holds the workflow patch. Holds. |
| N4 | Round 1's form in `StandingsStore.load()`: a URL decoded by a generic helper, and a local computed `var url: Foundation.URL` that returns the store's own file on its first read and the decoded URL on its second, for the on-device store only. | Swift suite, offline: 637 tests, 1 failure, the new `StandingsStoreTests.testTheOnDeviceStoreLoadsWithoutReachingOut` (`StandingsStoreTests.swift:201`). Holds. The text pins still pass the form (N6). |
| N5 | The new `match=` regex, checked against the gate's messages. | It matches the exact-snippet message, and not the egress pattern message. Holds. Its first alternative, `guard url\.isFileURL.*exactly once`, can never match: the snippet in the message holds a newline and `.` does not cross it. The second alternative does the work. A note, not a finding. |
| K1 | An ADR in one commit with `tests/unit/test_two.py`. | Refused. Holds for `tests/`. The other paths round 1 named are N4. |
| K2, R1 | Accepted by the author. | Not re-planted. |

## Findings

### BLOCKING
- none

### MAJOR
- none

### MINOR

- **N1** `tests/unit/test_swift_tests_offline.py:50-52`: a presence check reads raw, behind an absence
  reason. The base's own `tearDown` is now read through `_code` (round 1's M1), but its second half
  is not. `_hooks_skipping_super` requires each subclass's `setUp`/`tearDown` body to contain
  `super.<hook>()`, and it reads each file raw, marked `# raw: every test class, live or dead, is held`.
  - **Why the reason is wrong.** Finding a hook in dead code is an absence check, and raw is right for
    that. Requiring `super.tearDown()` inside a live hook is a presence check, and raw lets a comment
    satisfy it.
  - **Measured.** In the export, `StandingsStoreTests.tearDown`'s `super.tearDown()` turned into
    `// super.tearDown()`, and then into `/* super.tearDown() */`. `test_swift_tests_offline.py`: 9
    passed each time. No other test reads the call (`grep` over `tests/`, `scripts/`, `conformance/`).
  - **The failure scenario.** A refactor leaves a subclass's `super.tearDown()` in a comment. The base's
    `XCTAssertEqual(attempts, [])` no longer runs for that class's tests.
  - **Measured in Swift.** The same commented call, plus a planted load that reaches `example.invalid`
    from that class's other tests. The plant also broke what those loads return, so the class's tests
    failed on that too. The reaches themselves were caught only outside the class's own `tearDown`. One
    catch was the on-device test's own drain. The other was
    `SubmissionTests.testAQuestionCanBeSentWhenNothingIsRouting`, the next class, whose base `tearDown`
    drained what was left. So a leak is caught under another test's name. In a parallel run it is lost
    when such a test is the last one a worker runs.
  - **Remedy.** Read the hook bodies through `_code` (a dead hook does not run, so it needs no hold).
    Plant `// super.tearDown()` in `test_hardening_round_one.py`. Then do round 1's M1 remedy in full:
    of the raw reads this range marked, this is the one presence check I found. The others are absence
    checks, or are backed by a whole-file compare (`test_model_families.py:17` by `:41`).

- **N2** `tests/unit/test_swift_reads.py:54`, `:58` and `:91-92`, with `docs/decisions.md:5113-5114`:
  D-198 clause 4 now permits `_swift` only "where a pin cuts a line at its `//`", and nothing holds that.
  - **What the guard accepts.** `explained()` accepts `_swift(` on any line. Its own table counts
    `view = _swift(CLIENT / "ContentView.swift")` as explained. Its failure message tells the next
    author to "go through `_swift(`".
  - **Measured.** In the export, a new pin file reads `_swift(CLIENT / "ContentView.swift")` and
    requires `Text(priceInPages(pick.blendedPerM, in: language))`. With that line turned into a `//`
    line, the new pin and `test_swift_reads.py` pass together (12 passed).
  - **Where it already happens.** `tests/unit/test_credits.py:288` reads `_swift` with no cut at `//`.
    It was written before this range, and it is harmless: a `//` copy cannot stand in for a
    multi-line string literal.
  - **The failure scenario.** M2's hole, closed in the eleven files, opens again in the next pin file,
    and the guard's message points the author at it.
  - **Remedy.** Point the message at `_code(`. Then do one of two things. Accept `_swift(` only with a
    reason on its line, as `# raw:` must carry one. Or name the files allowed `_swift`, each with its
    reason, beside the guard.

- **N3** `docs/security-invariants.md:150` (INV-78) and `:223-225` (G-15's paragraph), with
  `tests/unit/test_swift_reads.py:1-7`: they still claim what round 1's N1 asked to qualify.
  - **What they say.** INV-78: "Every other pin file under `tests/unit/` reads the iOS folder through
    `_swift` or `_code`, or says on the line why it reads raw, as an absence check does." The G-15
    paragraph repeats it. The guard's docstring says every `.read_text(` that reaches the iOS folder
    is held.
  - **What the code holds.** D-198 clause 4 now says the guard cannot see a read through a function's
    parameter. The read trace above found two such reads (both absence scans, rightly raw). N1 is a raw
    read whose check is not an absence check. Round 1's N1 remedy named INV-78 and the docstring. The
    disposition changed D-198 only. INV-78 also still offers `_swift` to every pin file, where D-198
    now restricts it (N2).
  - **Remedy.** Say in INV-78, the G-15 paragraph and the guard's docstring what D-198 clause 4 says:
    the guard reads the reads it can see by their spelling, and a `# raw:` reason is not checked.

- **N4** `scripts/wave_check.py:368` and `:495`, with `docs/decisions.md:5109` (D-198 clause 3: "a
  commit that changes no code (its tests included)"): the backlog rule's code is `src/`, `ios/`,
  `scripts/`, `.claude/`, `.githooks/` and `tests/`.
  - **Measured** on scratch repositories built with the test's own helpers. An ADR written in one
    commit with `tests/unit/test_two.py` is refused. Written with a `Makefile` change, a
    `conformance/test-two.py`, a `runner/run.sh` or `pyproject.toml`, it passes.
  - **Why it matters.** `conformance/` holds tests, so "its tests included" says more than the rule
    reads. The `Makefile` is where this wave's own gates are wired. Round 1's K1 named all five paths;
    the disposition calls K1 fixed but added only `tests/`.
  - **Remedy.** Add `conformance/`, `runner/`, `Makefile` and `pyproject.toml` to the backlog rule's
    code paths, and plant one of them in
    `test_the_backlog_rule_names_the_range_it_read_and_counts_tests_as_code`. Or name in clause 3 the
    paths the rule reads as code.

- **N5** `tests/unit/test_ios_client_contract.py:267` (`_record_matches`): a question quoted in a
  blockquote and wrapped is not found.
  - **Measured** with a made-up question of 56 characters, as `> ...first half\n> ...second half`:
    not found. Whitespace collapse leaves the second line's `>` inside the question.
  - **How records quote.** `docs/` holds 895 blockquote lines in 140 Markdown files (counted, not
    read). Emphasis inside a question (`*three*`) is not found either, but that is rarer.
  - **The failure scenario.** #272's: a record quotes a live question as a wrapped blockquote, and the
    next wave tunes on it. D-198 clause 2 claims only the collapse and the backtick, so this is a
    residue, not an overclaim.
  - **Remedy.** Drop a leading run of `>` and spaces from each line before collapsing. Plant the form
    in `test_a_question_a_record_wraps_or_spaces_or_ticks_is_found`. Re-measure
    `HELD_OUT_PUBLISHED_OVERLAP`.

- **N6** `tests/unit/test_router_hints.py:699` (`EGRESS`, `r":\s*\[?\s*URL\b"`) and round 1's N4
  disposition ("it is #242's"): the module-qualified spelling passes every text pin, and #242 names
  neither form.
  - **Measured.** In the export, round 1's N4 form in `StandingsStore.load()`, with the URL literal
    split as `REBOUND_READ` splits it. With the type spelled `URL`: 1 failed
    (`test_the_gap_register_code_carries_no_egress_spelling_the_pin_reads`). Spelled `Foundation.URL`:
    125 passed, 1 skipped, over `test_router_hints.py` and `test_ios_client_contract.py`.
  - **Where it is held.** The Swift test now catches it, on a Mac (above). CI runs no Swift (#243).
  - **The tracking gap.** #242's body and comments name neither a getter read twice nor a
    module-qualified `URL`. Its comment still says "The stores' `isFileURL` guards refuse to load it
    today", which this form defeats. So the disposition hands the residue to an issue that does not
    hold it.
  - **Remedy.** Add `Foundation\s*\.\s*URL\b` to `EGRESS`, a one-pattern change that turns this form
    red in CI. Or comment on #242 with the form, its measured result and the Swift test that holds it.

- **N7** `docs/process-log.md:865-879`: the wave's entry now says what round 1 showed false. It has no
  `Lesson:` line yet.
  - **What it says.** "#275: every pin file reads the app's Swift through `_swift`" (M2 moved them to
    `_code`, and `_swift` was the gap). "`reading_heldout_m22` overlaps one record written before it"
    (two now, `m20-wave-3-review.md` added by M3's fix).
  - **What it leaves out.** That CI never reads the backlog rule (#278). Round 1's N3 remedy asked for
    that line.
  - **Why it matters.** The log is what `/start-session` reads first.
  - **Remedy.** The log is append-only (AGENTS.md 3.6). Append a line for the round-1 fixes that
    corrects the two facts and names #278, and close the entry with its `Lesson:`.

### PASS (what looks good)
- Each round-1 finding got a red test first (`b2ece4d`; all seven fail there, measured on an export),
  then its fix. The plants are in copies under `tmp_path`, never the app's files.
- M2's move is complete. Outside the two files with their own guards, only two pins read the app's
  Swift through `_swift`. One is `test_engine_address.py:82`, which cuts at `// MARK:` and reads the
  slice through `_code`. The other is `test_credits.py:288`, from before the range (N2).
  (`test_client_decl_gate.py:762` reads the gate's fixtures through it, not the app.)
- The record scan's collapse is applied to both sides, so a question's own spacing does not matter. The
  age check still passes with the second overlap record.
- L1 strips spans before it decodes. So an escaped backtick opens no span, and a decoded backtick cannot
  hide a letter.
- The backlog rule's message names its range. With `tests/` counted, D-198's own range still passes.
- The new Swift test turns red on round 1's N4 form in the store that had none.

## Acceptance criteria evidence
- D-198 clause 1 (#271) -> `tests/unit/test_language_rule_escapes.py:29`, `:40`;
  `tests/unit/test_hardening_round_one.py:63` (raw-string escape, escaped backtick); the self-test
  probe `tr-escaped.json` in `scripts/check_records.py`. Holds.
- D-198 clause 2 (#272) -> `tests/unit/test_ios_client_contract.py:274`, `:283`, `:298`;
  `tests/unit/test_hardening_round_one.py:52`. Holds; residue N5.
- D-198 clause 3 (#274) -> `tests/unit/test_wave_check_backlog_order.py:27-67`;
  `tests/unit/test_hardening_round_one.py:73`; wired at `scripts/wave_check_all.py:219`; not read in CI
  (#278). Says a little more than it reads (N4).
- D-198 clause 4 (#275) -> `tests/unit/test_swift_reads.py:67`, `:73`, `:86`, `:95`;
  `tests/unit/test_hardening_round_one.py:22`, `:39`, `:91`. Holds for the pins as they are; the
  `_swift` restriction is held by nothing (N2), and one raw reason is wrong (N1).
- D-198 clause 5 (#276) -> `tests/unit/test_router_hints.py:660`;
  `tests/unit/test_hardening_round_one.py:83`; `ios/EngineTests/FrontDoorTests.swift:830`;
  `ios/EngineTests/StandingsStoreTests.swift:201`. Holds; residue N6.

## K.8 contract drift check
- `adr_order_problems`, `branch_adr_problems`, `_record_matches`, `declared_names`: `grep -n` evidence:
  ```
  scripts/wave_check.py:441:def adr_order_problems(root: pathlib.Path, base: str, end: str, plan_rel: str | None,
  scripts/wave_check.py:475:def branch_adr_problems(root: pathlib.Path) -> tuple[list[str], str | None]:
  scripts/wave_check.py:495:            adr_order_problems(root, base.strip(), "HEAD", None, (*CODE_DIRS, "tests/"))], None
  scripts/wave_check.py:575:    problems += adr_order_problems(root, base, end, plan_rel)
  scripts/wave_check_all.py:219:    branch_rule = getattr(check, "branch_adr_problems", None)
  tests/unit/test_ios_client_contract.py:262:def _record_matches(held: set[str], texts: dict[str, str]) -> dict[str, int]:
  tests/unit/test_ios_client_contract.py:291:        matches = _record_matches(_held_questions(path), _leak_scan_docs(root))
  tests/unit/test_security_invariants.py:100:def declared_names(path: Path) -> frozenset[str]:
  tests/unit/test_security_invariants.py:141:            elif name not in declared_names(file):
  tests/unit/test_security_invariants.py:339:    return frozenset().union(*(declared_names(ROOT / path) for path in PIN_FILES))
  ```
- The new `code_dirs` parameter defaults to `CODE_DIRS`, so the milestone close's call at `:575` is
  unchanged. Verdict: OK.

## Producers of the hardened invariants
- INV-62 / INV-67 / G-13 (a store reads only its own file): producers are `GapRegisterStore.load()`
  (`ios/ModelRanking/Engine/FrontDoor.swift:313`) and `StandingsStore.load()`
  (`ios/ModelRanking/Engine/StandingsStore.swift:57`). Citing tests: the two cases of
  `test_a_url_rebound_between_a_stores_guard_and_its_read_is_refused` (`test_router_hints.py:660`),
  and `testTheOnDeviceStoreLoadsWithoutReachingOut` in both `FrontDoorTests.swift:830` and
  `StandingsStoreTests.swift:201`. Gaps: N6 (held on a Mac only), #242, #243.
- INV-78 (pins read the Swift a build compiles): producers are the pin files under `tests/unit/`.
  Citing tests: `test_every_read_of_the_ios_folder_in_a_pin_file_goes_through_swift_or_says_why`
  (`test_swift_reads.py:86`) and `test_hardening_round_one.py:22`, `:39`, `:91`. Gaps: N1, N2, N3.

## K.9 candidates spotted outside this wave's scope
- **K1** `ios/EngineTests/OfflineTestCase.swift:116`: the tripwire's check runs in the base's
  `tearDown`, so it holds a class only while every override calls `super`, and N1 shows how thin the
  Python pin on that is. An `XCTestObservation` registered once (its `testCaseDidFinish`) would drain
  and fail after every test, whatever a class overrides, and would make the pin unneeded. Enhancement.

## Risks queued to next M
- **R1** The text pins stay spelling checks (G-14). N6 is one more twin, and CI runs no Swift. The sign it
  is real: a store's `Foundation.URL` getter, or a twin like it, merges green. #242 and #243 are the
  structural fixes.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| N1 | Fixed, red in `4c2b1b5`. The super check reads each subclass through `_code`; a commented `super` call fails it. | `tests/unit/test_swift_tests_offline.py` |
| N2 | Fixed, red in `4c2b1b5`. The guard takes `_code(`, `_swift(` only with `# keeps //: <why>`, or `# raw: <why>`, and its message points to `_code`. | `tests/unit/test_swift_reads.py`, D-198 clause 4 |
| N3 | Fixed. INV-78, the G-15 paragraph and the guard's docstring say what it does not hold: a read through a parameter, and whether a `# raw:` reason is true. | `docs/security-invariants.md`, `tests/unit/test_swift_reads.py` |
| N4 | Fixed, red in `4c2b1b5`. The backlog rule reads `BACKLOG_CODE`: code, tests and the files that build and gate it. D-198 clause 3 says so. | `scripts/wave_check.py`, D-198 |
| N5 | Fixed, red in `4c2b1b5`. The record scan drops blockquote marks before it joins lines; the overlap counts are unchanged. | `tests/unit/test_ios_client_contract.py` |
| N6 | Fixed, red in `4c2b1b5`. `EGRESS` refuses `Foundation.URL` and `Foundation.NSURL`; the shipping client spells neither. | `tests/unit/test_router_hints.py` |
| N7 | Fixed. The wave's entry gains an appended line on what the reviews changed, #278, and a Lesson. | `docs/process-log.md` |
| K.9 | Filed as #279. | #279 |
| R1 | Accepted: #242, #243. | none |

