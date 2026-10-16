---
record_type: review
id: integration-run-product-night-security
status: draft
seat: independent
process_version: v7.1
date: 2026-10-16
---
# Security Review: integration PR #291, run product-night (branch `integration/run-product-night`), delta of the stack

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`, read from `main`)
**Independent:** yes. I wrote none of this stack's code, tests, fixtures or records.
**Seat and method:** a fresh Security-Reviewer seat, Claude model family (Opus). Own worktree detached at
`d953ca5` under a `mktemp -d` directory with its own venv (`make install`), per D-174. The author tree was
read with git only, and the owner's launchd service was not touched. No `advisor.db` was copied or built.
Policy was read from `main` (`main:docs/security-baseline.md`, `main:docs/security-invariants.md`,
`main:docs/project-brief.md`). The stacked verdicts stand and were not re-run. This seat reviewed what only
the combination, or the code after each verdict's reviewed head, could break. I ran 7 fault injections in
place. Each file was restored byte-identical (`cmp`, and `shasum -c` for the contract test), and
`git status` was clean after each one.
**Date:** 2026-10-16
**Release range:** `7bdb7c5..d953ca5` (`git merge-base origin/main HEAD`..head, 65 commits)
**Reviewed head:** d953ca59e719568ac1a076bc9402a227732b6503
**Risk tier:** MEDIUM. The brief declares no HIGH paths (`docs/project-brief.md:109`, the same on `main`).
The highest tier of any stacked part is MEDIUM: #288 adds an egress default to the hosted engine and a parse
of a file on the device, and #281 changes the Bash guard. The range changes nothing under `src/`, no
`Dockerfile`, no `deploy/`, no `fly.toml` and no `.github/` (`git diff --stat` over them is empty).

## What the stack carries, and what this seat read

| part | verdict and reviewed head | after the head, in this range |
|---|---|---|
| #281, DevFlow v7.1 upgrade | `devflow-v7.1-upgrade-security*.md`; round 3 at `b39bbe8` | `ab8686f` (test-only, covered by round 3's addendum, `rereview-2.md:123`), `aea7d96` and `aaa02c3` (docs) |
| #290, the run plan | docs only | `8206ba4`, `e588910` (docs, including the brief's `Working mode:` flip, see M1) |
| #288, merge `8e2798b` | `enhancement-issue-288-phone-security*.md`; `4bd11b0` | `7ccdcbb`, `783e5c6` (docs) |
| #66, merge `21e7c9a` | none (`make review-need`: none) | the whole of `d5f1753`, `2e73c27`, `7b13095`, `c2df37e` |
| #289, merge `2e11607` | `enhancement-issue-289-golden-security.md`; `d67bc4d` | `9531f44` (test-only) |
| integration branch | none | run file and docs commits, the manifest resolution in `2e11607`, `03e845a` |

## Verdict

PASS WITH FINDINGS: BLOCKING 0 · MAJOR 0 · MINOR 1 · NIT 2.

The combination introduces no exposure. All three merges are clean. `8e2798b` and `21e7c9a` are exactly
the trees `git merge-tree` writes. `2e11607` differs from the automatic merge only in
`ios/EngineTests/test-manifest.txt`, where it takes the union of both sides, and the manifest gate holds
that union (probe F1). #288's networking and caching do not interact with #66's reading change in a way
that matters for security. A held reading sends no request, keeps no answer and records no gap. A kept
answer is shown only on the not-held path, and only for an engine that could not be reached. Every code
commit after a stacked verdict's head is test-only, and each of them strengthens a check. The
security-invariant tests and the gates are green on the combined tree. `03e845a` follows the exactness
rule mechanically and touches no security invariant. It retires the fresh set without the one review
the hygiene gate would have given it while live (NIT N1). The one MINOR is a routing fact only the
combination creates. The review routing that grades this PR reads its working mode from the PR's own
brief, and the PR is the one that switches that mode to light (M1).

## Findings

### BLOCKING
- none

### MAJOR
- none

### MINOR
- **M1** `scripts/review_need.py:133-134` (from #281) with `docs/project-brief.md:106` (from #290, `8206ba4`).
  `assess()` reads the working mode from the tree under evaluation (`root = "."` unless `--at` is given).
  #290, stacked in this PR, changes the brief's `Working mode:` from `heavy` (as on `main`) to `light`. So
  the routing this PR is graded by, `/pre-merge` §1a, takes its mode from the PR itself. On the same range:
  - `make review-need` → `review-need: security` (`working mode: light`, 3281 product lines, "measured
    anyway, not routed");
  - `python3 scripts/review_need.py --range 7bdb7c5..HEAD --at 7bdb7c5` (the brief on `main`) →
    `review-need: code-reviewer+security`.

  Neither #281 alone nor #290 alone shows this. Together, #288 (about 1,100 lines of networking and
  on-device caching), #66 and #289 merge with no Code-Reviewer, on a mode switch that `main` does not hold
  yet. AGENTS.md section 5 ("Base-pinned policy") reads such policy from the protected base ref. I rate it
  MINOR, not an injection finding, because the switch is the owner's own ruling on record (D-201, "Owner
  ruling: 2026-10-16, in chat", `docs/decisions.md`, added in `8206ba4`). A run's plan PR is that ruling's
  signature (AGENTS.md section 3, "A run"). Nothing is exploitable at runtime, and nothing deploys from
  this PR. **Remedy:** the owner merges #290 (the plan PR that carries D-201) before #291, so the light
  mode is the base's policy when #291 is graded. Or the owner says on #291 that D-201 governs its own
  routing. Making `review_need.py` read the mode from the merge-base (`--at <merge-base>` by default) is a
  gate-definition change, so it belongs to the owner (AGENTS.md section 3, Escalate NOW). If it is wanted,
  file it with the guard follow-ups (#282-#287).

### NIT
- **N1** `tests/unit/test_ios_client_contract.py:337` (`03e845a`). Committing
  `reading_heldout_m23_questions.json` straight into `RETIRED_HELD_OUT` skips the one comparison the
  hygiene gates would have made while it was live. I checked whether the commit weakens a check. It does
  not, and the removals are mechanical. With m23 read as tuning, the eight entries removed from
  `HELD_OUT_ONLY_REVIEWED` (`:1887`) and `WORDING_HELD_OUT_ONLY_REVIEWED` (`:2122`) are held by a tuning set,
  so the exactness assertions (`:1879`, `:2110`) require their removal. The gate the security-invariants
  file names, `test_no_held_out_question_is_written_into_the_code_or_its_tests`, is declared "Not a row"
  there (`main:docs/security-invariants.md:181`). It "guards nothing an attacker could reach", so this is
  not an Escalate-NOW "security-invariant test modified" event. The function bodies are unchanged.

  Probe F4 read m23 back as live (`RETIRED_HELD_OUT` without it). Four hygiene tests then failed, which
  shows what the retirement skipped:
  - two of #66's own entries are held by m23 and by no other JSON set:
    `"im bored"` (`ios/ModelRanking/Engine/Reading.swift:162`) and `"sıkıldım"` (`:177`);
  - m23's row 127 (0-based, 30 characters) sits inside a string of the retired
    `notasearch_heldout_m19_questions.json`, although the provenance record says "0 collisions"
    (`docs/research/reading-heldout-m23-set.md:25`). That check compared whole strings, not substrings;
  - `docs/research/reading-wave-m23-probe-66.md:85` still says the set "stays held out for later waves".

  Neither m23-only entry moved a scored row. #66's only gained row (0-based 104) is caught by `"whats up"`,
  which a tuning set holds, and the search that holds `"im bored"` (row 9) is still read as a search, so
  D-203's one-row margin does not rest on them. Both words plausibly come from issue #66 and the tuning
  tests (`d5f1753` asserts "I'm bored"). Measurement integrity, outside security. **Remedy (optional):**
  one line in `docs/research/reading-heldout-m23-set.md` giving the two entries' provenance and the row-127
  overlap, and line 85 of the probe record corrected to "retired at `03e845a`".
- **N2** `ios/EngineTests/OfflineTestCase.swift:141-143`. A bare `cd ios && swift test`, as this seat was
  asked to run, fails `OfflineGuardTests/testAChildTheSuiteStartsCannotNameAnOutsidePeer` (2 failures of
  676). That is by design: the test asserts the suite runs inside `scripts/offline.sb`. Through
  `make swift-test` the same tree passes all 676 tests, each named in the manifest. This is noted so a later
  seat's brief names `make swift-test` and does not read the bare run as red. No code change.

### PASS
- **Merge resolutions.** `git merge-tree --write-tree` of each merge's parents gives exactly the committed
  tree for `8e2798b` (`5c1b32b`) and `21e7c9a` (`46b4806`). `2e11607` conflicts only in
  `ios/EngineTests/test-manifest.txt`. The resolution keeps #289's three `GoldenQuestionTests` and #66's
  seven `GuidingNoteTests` lines, sorted. `make swift-test` reports "676 test(s), each one named in
  ios/EngineTests/test-manifest.txt". Probe F1 dropped one merged line, and the gate failed with "the
  discovered tests are not the manifest (D-150)".
- **#288 × #66.** `ContentView.ask()` returns at `ios/ModelRanking/ContentView.swift:999-1004` for any held
  reading, before `apply()` and `load()`. A line #66 now holds (small talk, no meaning, a dictated answer)
  sends no request, writes nothing to `StandingsStore`, and goes neither to the gap register
  (`:1027-1030`, reached only through `apply`) nor to the engine. The request still carries only a surface
  id and a budget (`EngineClient.swift:268-273`). The kept-answer notice and the reading card are exclusive
  branches (`ContentView.swift:196-206`). An answer is kept only after a decoded engine reply
  (`:1131`, `:1119`). A kept one stands in only for `.unreachable`, `.timedOut` and `.offline`. It never
  stands in for `.insecureTransport`, `.refused` or `.undecodable` (`KeptAnswers.swift:25-31`), so a
  cleartext refusal is never hidden behind an old answer. `select()` still admits only a listed surface,
  and a kept categories list comes only from the engine (#288 MJ1, its verdict).
- **#66's control direction.** Both new signals fail closed: what they catch is held and never routed.
  `noMeaning` decides as `noWord` does (`Router.swift:1141`). The dictated-answer phrases join
  `rolePhrases` (`Reading.swift:130-137`), which is the instruction-to-the-app doubt. Small talk still
  needs every word to be small talk, so an injection line that carries other words is not waved through as
  chit-chat. Probe F2 (`noMeaning` unwired) and probe F3 (the two English dictated-answer phrases removed)
  are each killed by their `GuidingNoteTests` case. The filtered baseline (`GuidingNoteTests`,
  `GoldenQuestionTests`, `ReadingTests`) is 25 tests with 0 failures.
- **After the stacked heads.** `9531f44` adds `test_a_broken_folder_exits_one_and_writes_nothing`. Probe F5,
  the #289 verdict's F7 mutant (`return 1` → `return 0` in `scripts/golden_questions.py:211-213`), is now
  killed (2 failed). The commits after `4bd11b0` (#288) and after `b39bbe8` (#281's round 3, apart from
  `ab8686f`, which round 3's addendum covers) are records only. #289's golden set is apart from both
  held-out sets on the combined tree: 0 overlaps with m22 or m23 by the leak gate's own rule, and
  `test_the_golden_set_is_apart_from_the_held_out_sets` now reads m23 too.
- **Startup validation fails closed (baseline item 4).** Importing the adapter outside `APP_ENV=test`, with
  `MODEL_RANKING_DB` and `APP_BUILD` unset or pointing at nothing, raised `ConfigError`
  (`src/app/adapter/main.py:729`). Probe F6 was an observation, not a mutant.
- **Secrets and PII.** gitleaks over the history of `7bdb7c5..d953ca5` (60 commits scanned) and `make secrets`
  over the tree both report no leaks. The range adds no email address. The new URLs are public benchmark
  pages, the hosted HTTPS engine, loopback and RFC 5737 test addresses, and `attacker.example` in a test.
  No `.env` or key file is in the range. The committed m23 set holds 9 prompt-injection lines. They are
  test data that only the probe scripts read, as JSON, and nothing executes them.
- **Baseline walk (`main:docs/security-baseline.md`, unchanged in the range).** Items 1-3 and 6 (no plaintext
  credentials, server-side authorization, CORS, generic errors) are not touched: no `src/` change. Item 4
  holds (above). Item 5: the kept answers file holds engine payloads (surfaces, models, prices) and no PII.
  Typed questions stay on the device, as before.
- **Suites and gates on the combined tree.**
  - Python: `.venv/bin/python -m pytest -q -p no:cacheprovider -n auto` gave 3103 passed, 81 skipped,
    0 failed (the skips need `advisor.db`).
  - Swift: `make swift-test` passed, 676 tests, the manifest exact.
  - `make conformance`: PASS, 26 tests, 0 failing.
  - `make check-records`: PASS, 409 records.
- **Fault injection: 7 probes, each restored byte-identical.**
  - Killed: F1 (manifest), F2 (`noMeaning`), F3 (dictated-answer phrases), F5 (golden error exit).
  - F4 (m23 read as live) is the N1 evidence.
  - F6 is the startup-config observation.
  - F7: bandit on `src/` and `scripts/golden_questions.py` reported 0 findings in the range's code. Its 13
    Low or Medium findings are all in `src/`, which the range does not change, and they predate it.

## Gates passed
- [x] Secret scan green: `make secrets` on the seat tree ("no leaks found"), and gitleaks over the range's
  history.
- [x] `make deps` (pip-audit, strict, four locks): "No known vulnerabilities found".
- [x] `make slopsquat`: PASS, 20 declared dependencies, 0 suspect. No new import: Python is stdlib plus
  `pytest`; Swift is Foundation, NaturalLanguage and XCTest.
- [x] Default-deny preserved for new external surfaces: no route or endpoint was added. The one egress
  default is #288's hosted HTTPS engine, already reviewed, and unchanged after `4bd11b0`.
- [x] Permission matrix not violated: no destructive operation in the range's commits, no CI or deploy file,
  and no `.claude/` or `.githooks/` change after #281's reviewed rounds.
- [x] Prompt-injection hygiene: #66 moves only in the holding direction (F2, F3). The injection lines in the
  committed m23 set are inert data.
- [ ] Auth/PII checks and the human-review trigger: not applicable (no auth, PII, payment or migration path).
- [x] SAST: bandit 1.9.4 over `src/` and `scripts/golden_questions.py`: nothing new in the range.

## Acceptance criteria evidence
- REQ-RTR-004 (what the reader typed never reaches the engine) → `ios/ModelRanking/ContentView.swift:999-1004`
  (held, no request), `:1012-1016`; `ios/ModelRanking/Engine/EngineClient.swift:268-273` (task and budget only).
- D-202 clause 5 (a kept answer only when the engine cannot be reached) →
  `ios/ModelRanking/Engine/KeptAnswers.swift:25-31`; `ios/EngineTests/KeptAnswerTests.swift` (676 tests green).
- D-150 (the discovered tests are the manifest, including the merge) → `ios/EngineTests/test-manifest.txt`;
  `make swift-test` (F1 killed).
- #66 / D-203 (held lines fail closed) → `ios/ModelRanking/Engine/Router.swift:1141`,
  `ios/ModelRanking/Engine/Reading.swift:130-137`, `:184-190`; `GuidingNoteTests` (F2, F3 killed).
- #289 M2 (the deriver's error exit) → `tests/unit/test_golden_questions.py:132-144` (F5 killed).

## Risks queued
- **R1** M1's routing question goes to the owner: merge #290 before #291, or rule on #291 that D-201 governs
  its own routing. Under `main`'s brief this stack would owe a Code-Reviewer as well.
- **R2** #287 (B1-S, the third BLOCKING on B1) and #282-#286 stay open for the owner's guard PR. Not
  re-litigated here, and not a regression against `main` (round 3's verdict).
- **R3** `.language-allow`'s `ios/.build/` entry (#289 M1) stays until #304 lands.
