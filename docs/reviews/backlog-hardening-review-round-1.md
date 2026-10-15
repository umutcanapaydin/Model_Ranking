---
record_type: review
id: backlog-hardening-review-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-14
---
# Independent review, round 1: the hardening wave (#276, #271, #272, #275, #274, D-198)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-14
**Commit range:** `01c0fc0..d62fdbd` (12 commits; `origin/main` is `01c0fc0`)
**Risk tier:** MEDIUM for the gates (#271, #272, #274, #275); HIGH for #276 (the egress pin, INV-62,
INV-67, G-13)

## Verdict
MAJOR

Each fix does what its issue asked, in the form the issue named, and every check in the range is green.
But three of D-198's clauses claim more than the code holds:
- **M1.** Two pins on the offline base read its Swift raw, with the reason an absence check gives. They are
  presence pins. A dead copy of the base's `tearDown` satisfies both, and with the live one gutted, no
  Swift test can fail for reaching the network.
- **M2.** `_swift` keeps `//` comments. Every pin #275 moved to `_swift` passes a `//` copy of the line it
  requires. D-198 clause 4 says these pins read the Swift "as the build compiles it".
- **M3.** The leak check now reads `docs/**/*.md`, but with the matcher built for code. A question quoted
  across a wrapped line, or a short one in backticks, is not found. Both are how records quote.

Five minor findings (N1 to N5).

How the review was done:
- **Reading.** D-198, the five issues (`gh issue view`), the whole diff, INV-78, G-13, the process log
  entry, `.github/workflows/ci.yml` (read only), `tests/skips.py`, the egress pin, the leak check and its
  helpers, rule L1, `wave_check.py` and `wave_check_all.py`.
- **Plants.** I exported `d62fdbd` with `git archive` to a scratch tree outside the seat. Every plant
  went there. After each one the file was restored and a byte compare against `d62fdbd` passed. Rule
  probes ran on files in scratch folders. The backlog-order rule ran on a local clone in scratch, with
  merge commits and a shallow clone made there. The seat's tree is unchanged but for this record.
- **Swift runs.** Inside `scripts/offline.sb` with `MODEL_RANKING_REQUIRE_OFFLINE=1`, as `make
  swift-test` runs them. Every planted address is `example.invalid`.
- **Baselines in the seat.** Full Python suite: 2890 passed, 29 skipped; skip budget PASS (29 of 2919,
  budget 86). `check_records.py` PASS, its self-test PASS, `ruff check src tests scripts` clean,
  `wave_check_all.py` PASS.
- **Read trace.** I ran the whole unit suite on the export with a scratch pytest plugin that logs every
  `read_text`, `read_bytes` and `open` of a `.swift` file or a file under `ios/`, with its call site.
  2821 passed, 69 skipped (the export has no `.git` and no database).
- **Held-out discipline.** I read no held-out file and printed no held-out question. Leak probes used a
  made-up question. The L1 run over the export reads the live set as the gate does; only its file name and
  a count were printed.

## Findings

### BLOCKING
- none

### MAJOR

- **M1** `tests/unit/test_swift_tests_offline.py:46` and `:85`: two presence pins carry an absence
  check's reason.
  - **The lines.** Both read `OfflineTestCase.swift` raw, marked `# raw: every test class, live or dead,
    is held`. Line 46 then requires `override func tearDown()` with `OfflineGuard` in it. Line 85 requires
    that `tearDown` drains the tripwire and asserts the drained list is empty. Both require a line to be
    there. A dead copy of it satisfies them.
  - **Measured.** In the export, the base's `tearDown` wrapped in `/* ... */` and a live one put after it
    that only calls `_ = OfflineGuard.drain()` and `super.tearDown()`. `test_swift_tests_offline.py`: 9
    passed. Read through `_swift`, the block comment is blanked and line 85's pin fails. The docstring of
    the second pin says Swift cannot hold this, so this pin is the only thing that does.
  - **The failure scenario.** The `XCTAssertEqual(attempts, [])` in the base's `tearDown` is what turns a
    request into a failed Swift test (INV-6). A refactor that leaves it only in a comment or a dead branch
    passes every Python test, and every Swift test that reaches the network then passes.
  - **Remedy.** Read both through `_swift` (line 46 and line 85). Then re-check every `# raw:` reason the
    range wrote: the guard accepts any reason, so a wrong one is a pin let through.

- **M2** `docs/decisions.md:5109` (D-198 clause 4: "Every pin file reads the app's Swift as the build
  compiles it"): `_swift` keeps `//` comments (`tests/unit/test_ios_client_contract.py:35-43`, its
  docstring says so), so a `//` copy of a required line still satisfies every pin #275 moved to it.
  - **Measured.** In the export, `Text(priceInPages(pick.blendedPerM, in: language))` in
    `ContentView.swift:1356` turned into `// Text(...)`: `test_ios_visual_contract.py` 2 passed
    (`tests/unit/test_ios_visual_contract.py:15`). The same line in `/* */`: it fails, as #275 meant.
  - **Why it matters.** #275's own failure scenario is "a refactor leaves a required line only in a
    comment". A line comment is the common way to do that. Eleven files import `_swift` in this range
    (`test_engine_host`, `test_engine_address`, `test_families`, `test_screen_paths`,
    `test_tier_stubs_shared`, `test_ios_platform_drift`, `test_refinements`, `test_uitext_sentence_rows`,
    `test_error_codes`, `test_ios_payload_contract`, `test_ios_visual_contract`). Their pins do not cut a
    line at `//` as the contract pins do. INV-78 states the limit correctly; D-198 does not.
  - **Remedy, measured.** Read those files through `_code` (`tests/unit/test_router_hints.py:80`), which
    drops both kinds of comment. With `_swift` replaced by a `_code` read in all eleven files: 73 passed,
    1 skipped, 1 failed. The one failure is `test_engine_address.py:85`, which cuts its section at
    `// MARK:` and so needs comments; it can cut at the next `private func` instead. Or keep `_swift` and
    correct D-198's clause 4, and say in INV-78 that a `//` copy passes these pins.

- **M3** `tests/unit/test_ios_client_contract.py:260-266` with `:372-385` (`_record_matches` reuses
  `_held_out_leaks`): the matcher made for code misses the two ways a Markdown record quotes.
  - **Measured** with a made-up question of 56 characters and one of 17:

    | Planted in `docs/r.md` | Found? |
    |---|---|
    | the long question on one line | yes |
    | the long question across a line break, as records wrap at about 110 characters | no |
    | the long question with two spaces between two words | no |
    | the short question in backticks | no |
    | the short question in double quotes | yes |

  - **Why.** A question of 25 characters or more must appear as a substring with its exact spacing
    (`_forms`, `:362`, folds case and letters, not white space). A shorter one counts only inside double
    quotes. Records in `docs/` are hard-wrapped and quote in backticks.
  - **The failure scenario.** #272's sign: a wave quotes a live question in its record, wrapped as the
    paragraph falls, and the next wave tunes on it. The check passes.
  - **Remedy.** For `docs/`, collapse every run of white space to one space on both sides before
    matching, and accept a short question whole between backticks too. Plant both forms in
    `test_a_held_out_question_quoted_in_a_record_is_found`. Re-measure `HELD_OUT_PUBLISHED_OVERLAP`
    after the change; the count may rise.

### MINOR

- **N1** `tests/unit/test_swift_reads.py:35-48` and `docs/security-invariants.md:150` (INV-78: "Every
  other pin file under `tests/unit/` reads the iOS folder through `_swift` or `_code`, or says on the line
  why it reads raw"): the guard finds a read only where the `.read_text(` line names the folder, a
  module constant bound to it, or a local bound within a few lines. A read through a function parameter
  is not seen. The read trace found one: `tests/unit/test_security_invariants.py:101`
  (`declared_names`) reads seven Swift files under `ios/EngineTests/` raw, with no reason. It is a
  presence check: a cited negative test must be declared. Planted: a cited test's `func` line moved into
  a block comment passes `test_security_invariants.py`; `test_swift_test_manifest.py` catches it, so the
  harm is covered there. Remedy: read it through `_swift` (Swift) or mark it raw with its reason, and say
  in the guard's docstring and INV-78 that the guard reads spellings, not every call path.

- **N2** `scripts/check_records.py:1321-1343` and `:1411` (rule L1, #271): two variants pass.
  - A Swift raw string's escape: `#"bu bir \#u{15F}ey"#` (and `##"...\##u{15F}..."##`) is not decoded.
    Not flagged.
  - The decode runs before the code-span strip, so an escaped backtick makes a code span. A JSON line
    `"`` + raw Turkish + ``"` is not flagged now; at `origin/main`, L1 flags the same file
    (measured with both versions of `check_records.py`). Swift's `\u{60}` does the same. This is a small
    regression.
  - Remedy: strip code spans on the raw line, then decode; decode `\#+u{...}` in Swift. Consider not
    exempting code spans in `.json` and `.swift` at all: the exemption is for quotation in records, and a
    JSON or Swift string with escaped Turkish between two backticks passes today.

- **N3** `scripts/wave_check.py:474-491` and `.github/workflows/ci.yml:29-70`, `:120`: the backlog-order
  rule (#274) never runs in CI. `wave_check_all.py` runs in the `test` job, whose checkout sets no
  `fetch-depth`, and the `install-and-governance` job sets none either; only `secret-scan` fetches the
  whole history. So on every pull request the rule prints SKIPPED. D-198 clause 3 says a shallow clone
  skips; it does not say CI is always one. The rule does run locally in `make check` and `check-fast`
  (it is a `check:` prerequisite), where I measured it right: it refuses an ADR written beside code on
  a branch and on a PR-style merge commit, passes D-198's own range, and skips on a depth-1 clone. One
  local hazard: with a stale `origin/main` (set to `55da886`, one merge back), `d62fdbd` fails on D-196
  and D-197, which are already merged, and the message does not name the range it read. Remedy: say in
  D-198 and the process log that CI does not read the rule; file the workflow change for the owner
  (`fetch-depth: 0` on the step's job), as #122's patch was; name `base..HEAD` in each message.

- **N4** `ios/EngineTests/FrontDoorTests.swift:830` and G-13 (`docs/security-invariants.md:197`): the
  one-expression pin holds a spelling, and the Swift test that backs it covers one store.
  - **Measured.** In `GapRegisterStore.load()`, before the guard: a URL decoded by a generic helper whose
    type is inferred, for the on-device store only, and a local computed `var url: Foundation.URL` that
    returns the store's own file on its first read and the decoded URL on its second. The guard and the
    read stay one exact expression. Text pins (`test_router_hints.py`, `test_ios_client_contract.py`):
    125 passed. Compiled gate: `client-decls PASS` in all four configurations. Swift suite, offline: 636
    tests, 1 failure, the new `testTheOnDeviceStoreLoadsWithoutReachingOut`. So the new test holds this
    form, on the Mac only; CI runs no Swift. No `EGRESS` pattern reads the type spelled `Foundation.URL`.
  - **The gap.** `StandingsStore.onDevice` is not loaded under the tripwire by any test, though #276's
    scope named `StandingsStoreTests.swift`. The same rebinding limited to the caches store would pass
    every gate.
  - **Remedy.** Add `StandingsStore.onDevice.load()` under the tripwire to `StandingsStoreTests`. Add a
    module-qualified URL type to `EGRESS` (`Foundation\s*\.\s*URL\b`). Name in G-13 that a getter read
    twice is held by the Swift tests only.

- **N5** `tests/unit/test_router_hints.py:677`: `pytest.raises(AssertionError)` takes any assertion of the
  whole client gate. It passes today because the exact snippet's count check fires. A copy that tripped a
  different assertion first (a stale exemption, a project-file check) would also pass it. Remedy:
  `match="must contain"`.

### PASS (what looks good)
- D-198 was committed alone, before any code (`7e89544`), and the rule it adds passes its own range.
- #276: the guard and the read as one exact expression is the measured remedy from the round-4 review,
  in both stores. The plant test fails on the old `EGRESS_EXACT` shape by construction (the exact
  snippet is absent from the probe). The new Swift test catches a rebinding the compiled gate misses.
- #271: the decode handles surrogate pairs, an escaped backslash, and eight-digit Swift escapes. Each of
  the five new `.language-allow` entries is needed: removing any one gives an L1 finding (measured).
- #272: the age check fails closed (a record with no adding commit fails), the CI count test reports by
  file and count only, and the `git_history` need matches what `ci_job_facts` reads.
- #274: the refactor keeps the milestone path's logic; only one message changed its wording.
- #275: the guard's line check is tested on planted lines, and its floor checks keep it from passing
  vacuously.

## Acceptance criteria evidence
- D-198 clause 1 (#271) -> `tests/unit/test_language_rule_escapes.py:29-37` and the self-test probe
  `scripts/check_records.py` (`tr-escaped.json`); partly held (N2).
- D-198 clause 2 (#272) -> `tests/unit/test_ios_client_contract.py:269` (planted record),
  `:278` (live sets by file and count), `:292` (age, `needs("git_history")`); partly held (M3).
- D-198 clause 3 (#274) -> `tests/unit/test_wave_check_backlog_order.py:27-69`; wired at
  `scripts/wave_check_all.py:219`; not read in CI (N3).
- D-198 clause 4 (#275) -> `tests/unit/test_swift_reads.py:62-103`; overclaims (M1, M2, N1).
- D-198 clause 5 (#276) -> `tests/unit/test_router_hints.py:660-678`, `EGRESS_EXACT` at `:756` and
  `:767`; `ios/EngineTests/FrontDoorTests.swift:830`; one store only (N4).

## K.8 contract drift check
- `adr_order_problems`, `branch_adr_problems`, `git_history`: `grep -n` evidence:
  ```
  scripts/wave_check_all.py:219:    branch_rule = getattr(check, "branch_adr_problems", None)
  scripts/wave_check.py:441:def adr_order_problems(root: pathlib.Path, base: str, end: str, plan_rel: str | None) -> list[str]:
  scripts/wave_check.py:474:def branch_adr_problems(root: pathlib.Path) -> tuple[list[str], str | None]:
  scripts/wave_check.py:491:            adr_order_problems(root, base.strip(), "HEAD", None)], None
  scripts/wave_check.py:571:    problems += adr_order_problems(root, base, end, plan_rel)
  tests/skips.py:79:    "git_history": Need("a git checkout with its whole history",
  tests/skips.py:116:        "git_history": any(str(step.get("uses", "")).startswith("actions/checkout@")
  tests/unit/test_ios_client_contract.py:292:@pytest.mark.needs("git_history")
  ```
- Verdict: OK.

## Producers of the hardened invariants
- INV-62 / G-13 (a store reads only its own file): producers are `GapRegisterStore.load()`
  (`ios/ModelRanking/Engine/FrontDoor.swift:313`) and `StandingsStore.load()`
  (`ios/ModelRanking/Engine/StandingsStore.swift:57`). Citing tests:
  `test_a_url_rebound_between_a_stores_guard_and_its_read_is_refused[FrontDoor.swift]` and
  `[StandingsStore.swift]`; `testTheOnDeviceStoreLoadsWithoutReachingOut` for the first only. Gap: N4.
- INV-78 (pins read the Swift a build compiles): producers are the pin files under `tests/unit/`.
  Citing test: `test_every_read_of_the_ios_folder_in_a_pin_file_goes_through_swift_or_says_why`. Gaps:
  M1, M2, N1.

## K.9 candidates spotted outside this wave's scope
- **K1** `scripts/wave_check.py:368`: `CODE_DIRS` leaves out `tests/`, `Makefile`, `conformance/`,
  `runner/` and `pyproject.toml`, so an ADR first written in a commit that also adds its tests, or after a
  test commit that cites it, passes the decision-order rule, for milestone and backlog waves alike.
  Enhancement: decide whether tests are code the decision governs.
- **K2** `scripts/check_records.py:1093`: L1 decodes no Python escape. Two tracked Python files hold
  Turkish letters written as `\u` escapes (`tests/unit/test_engine_address.py`, 6;
  `tests/unit/test_ios_client_contract.py`, 55; counts of escapes only). The same gap as #271, one suffix
  over. Enhancement.

## Risks queued to next M
- **R1** The one-expression pin and every `_swift` pin are spelling checks (G-14). The sign it is real: a
  form outside the spellings, as N4's getter, passes CI, which runs no Swift. #242 and #243 are the
  structural fixes.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| M1 | Fixed in `05ebda7`, red in `b2ece4d`. Both pins on `OfflineTestCase.swift` read it through `_code`; the planted block-commented tearDown above an empty one now fails them. | `tests/unit/test_swift_tests_offline.py` |
| M2 | Fixed in `05ebda7`, red in `b2ece4d`. The pins #275 moved read through `_code`, which drops `//` comments too; `test_engine_address.py` keeps `_swift` where it cuts at `// MARK:`, and `_code`s the slice. D-198 clause 4 says so. | the eleven pin files, D-198 |
| M3 | Fixed in `05ebda7`, red in `b2ece4d`. The record scan collapses whitespace and reads a backtick as a quote. Read so, it finds one more overlap, in `m20-wave-3-review.md`, which the age check confirms is older than the set; the table holds it. | `tests/unit/test_ios_client_contract.py`, D-198 clause 2 |
| N1 | Fixed in `05ebda7`. `declared_names` reads Swift through `_code`. D-198 clause 4 names what the guard cannot see: a read through a function's parameter. | `tests/unit/test_security_invariants.py`, D-198 |
| N2 | Fixed in `05ebda7`, red in `b2ece4d`. L1 decodes `\#u{...}`, and strips code spans before it decodes, so an escaped backtick opens none. | `scripts/check_records.py` |
| N3 | Fixed in `05ebda7` and this commit. A finding names the range it read; D-198 clause 3 says CI's one-commit checkout skips the rule; the workflow patch is the owner's, filed as #278. | `scripts/wave_check.py`, D-198, #278 |
| N4 | Fixed in this commit. A Swift test loads `StandingsStore.onDevice` under the tripwire. The computed-local `url` variant is a spelling the compiled gate does not read; it is #242's (G-14), and the Swift test catches it on a Mac. | `ios/EngineTests/StandingsStoreTests.swift` |
| N5 | Fixed in `05ebda7`, red in `b2ece4d`. The pin's `pytest.raises` matches the egress rule's own message. | `tests/unit/test_router_hints.py` |
| K1 | Fixed in `05ebda7`. The backlog rule counts `tests/` as code; a milestone close keeps its rule. | `scripts/wave_check.py` |
| K2 | Accepted. D-198 clause 1 reads JSON and Swift escapes; Python tests write Turkish inputs as escapes by the project's long practice, and the two files assert router inputs. Decoding Python escapes is a wider change to L1 than #271 asked. | none |
| R1 | Accepted: spelling checks (G-14); the structural fixes are #242 and #243. | #242, #243 |

