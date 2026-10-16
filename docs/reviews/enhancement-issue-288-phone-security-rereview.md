---
record_type: review
id: enhancement-issue-288-phone-security-rereview
status: draft
seat: independent
process_version: v7.1
date: 2026-10-16
---
# Security Re-review: enhancement #288, the fixes to round 1 (draft PR #296)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`, read from `main`), the same
seat as round 1 (`docs/reviews/enhancement-issue-288-phone-security.md`)
**Independent:** yes. I wrote none of this change's code, tests or records.
**Seat and method:** the round-1 Security-Reviewer seat, Claude model family (Opus). A fresh worktree detached
at `4bd11b0` under a `mktemp -d` directory, with its own venv (`make install`), per D-174; the author tree and
the owner's launchd service were not touched. Policy read from `main`. The fix range was read in full, then
5 new mutants and 2 round-1 mutants were fault-injected in place and 2 gate probes run, each file restored
byte-identical (md5 checked).
**Date:** 2026-10-16
**Release range:** `1cb49b7..4bd11b0` (6 commits: `127311f`, `4975040`, `fed15ec`, `803ba5e`, `af2c95d`, `4bd11b0`)
**Reviewed head:** 4bd11b0890cea7ba8c899a6d46b4b7b5c081b1c1
**Risk tier:** MEDIUM (unchanged from round 1)

## Round-1 findings, re-verified

- **MJ1: narrowed to MINOR, not closed by type.** `keep` now takes only `Recommendation` or `[Category]`
  (`ios/ModelRanking/Engine/StandingsStore.swift:206`, `:214`). It is keyed by the engine's `query` echo and
  dated by `Date()` inside the store, and the private `store(_:)` (`:224`) is the only writer. The round-1
  probe P1 (`keep(route:task: asked ...)`) no longer compiles: client-decls reports "no exact matches in call
  to instance method 'keep'". No free `String`, `Data` or `Date` of the caller's reaches the file any more,
  and mutant F5 (keyed by `apiVersion` instead of the echo) fails 9 tests. The remaining hole is R-m1 below:
  the two types can still be forged from typed text in any app file.
- **M2: holds.** `keptAnswers()` refuses a file over 8 MiB before decoding (`:196`). The write loop drops the
  oldest entries until the encoded file fits, and skips the write when one entry alone does not fit
  (`:236-243`). F1 (read ceiling removed) and F2 (write ceiling removed) are both killed. One residue is N1.
- **M3: the retention half holds.** Every write drops entries dated ahead of the clock or a week old or older
  (`:228-231`), and `KeptAnswers.maxAge` is now `StandingsStore.maxAnswerAge`, so nothing is kept that may not
  be shown. F3 (future entries kept) and F4 (expired entries kept) are both killed. The protection-class half
  is deferred to #297 as a gate edit, and the code says so (`:184-188`).
- **M1 (INV-73 wording): open, in #297.** Accepted as a deferral for the owner.
- **N1 and N2 (round 1): accepted.** No change expected.

## Is anything weaker than at `1cb49b7`?

No. `KeptAnswers.payload` is gone, and both call sites in `ContentView.load()` pass only the decoded value
(`ContentView.swift:1119`, `:1131`). The read-side checks are unchanged: the round-1 mutants M2 (query echo
on read) and M6 (answers written into `standings.json`) still fail tests. The categories payload changed from
`CategoryList` to `[Category]`, so an entry written by the old build fails to decode and reads as nothing
kept, which fails closed.

## Findings

### BLOCKING
- none

### MAJOR
- none

### MINOR
- **R-m1** `ios/ModelRanking/Engine/Models.swift:17` and `:41` (`Recommendation`, `Category`), reached through
  `StandingsStore.swift:206` and `:214`. The narrowed types are still built freely in the module, by
  `JSONDecoder` or by the memberwise initialiser. **Failure scenario (probe P5):** I added this line to
  `ContentView.load()`:
  `if let forged = try? JSONDecoder().decode([Category].self, from: Data("[{\"id\":\"\(asked)\",...}]".utf8)) { StandingsStore.onDevice.keep(forged) }`
  It puts the typed question into `answers.json`. With it in place, `make client-decls` passed in all four
  configurations and the full Python suite passed (3134 passed). This now takes a deliberate forgery rather
  than a stray argument, hence MINOR. But #297 says "typed text cannot reach it by type", and its stated
  remedy (limit `keep`'s callers to the load path) would not refuse P5, because the forgery sits in the load
  path. **Remedy (for #297, owner's gate edit):** also put the construction of `Recommendation` and
  `Category` under `PROVENANCE`: a decode or initialiser only in `EngineClient.swift`, plus the store's and
  `KeptAnswers.swift`'s own read-back. Add P5 as a fixture case the gate must refuse, and correct #297's
  sentence.
- **M1 (carried)**: INV-73's wording, #297.
- **M3, second half (carried)**: `.completeFileProtection` for `answers.json`, #297.

### NIT
- **N1** `StandingsStore.swift:83-90` and `:196`. The 8 MiB ceiling is checked after `Data(contentsOf:)` has
  read the whole file into memory, so it bounds the decode but not the read. A larger file can be planted
  only by something with write access to the app container. **Remedy:** read the size first (a file
  attribute or a bounded handle read), when the sink's Foundation list is next widened.

### PASS
- Fault injection: 7 of 7 mutants killed, each restored byte-identical. F1 to F5 on `StandingsStore.swift`
  (md5 `e4860da2…` restored each time); round-1 M2 on `KeptAnswers.swift` (md5 `dd2fbc89…`); round-1 M6.
  Probes on `ContentView.swift` (md5 `3e81710b…` restored): P1 is refused (it does not compile), P5 survives
  (R-m1).
- The new Python pin `test_the_kept_answers_store_takes_only_what_the_engine_sent` holds `keep`'s two
  declarations, the store's own clock and the echo key.

## Gates passed
- [x] `make check` on `4bd11b0`, own worktree: exit 0. pytest 3136 passed, 27 skipped; coverage-floor PASS;
  check_records PASS; self-test PASS; shell_dialect PASS; wave-check-all PASS; conformance PASS (26); swift-test
  PASS (666, each in the manifest; SlowTierTests 7 of 7); client-decls PASS (22 files, 4 configurations).
- [x] `make secrets`: gitleaks, no leaks found.
- [x] `make deps`: pip-audit, no known vulnerabilities.
- [x] `make slopsquat`: PASS, 20 declared dependencies, 0 suspect. `make secrets deps slopsquat` exit 0.
- [x] No dependency, CI, hook or gate file changed in the range.

## Acceptance criteria evidence
- MJ1 (narrowed) → `ios/ModelRanking/Engine/StandingsStore.swift:206-217`;
  `tests/unit/test_engine_address.py::test_the_kept_answers_store_takes_only_what_the_engine_sent`;
  `ios/EngineTests/KeptAnswerTests.swift` (F5 killed).
- M2 → `StandingsStore.swift:196`, `:236-243`; `KeptAnswerTests` (F1, F2 killed).
- M3 retention → `StandingsStore.swift:228-231`; `KeptAnswerTests` (F3, F4 killed).
- INV-66 → `KeptAnswerTests::testKeepingAnAnswerNeverTouchesTheStandingsFile` (round-1 M6 killed again).

## Risks queued
- **R1** #297 must cover the construction of the kept types (R-m1), INV-73 (M1) and the protection class (M3);
  as filed, it covers only `keep`'s call sites and INV-73.

**Verdict:** PASS WITH FINDINGS: BLOCKING 0 · MAJOR 0 · MINOR 3 (1 new, R-m1; 2 carried in #297) · NIT 1.
