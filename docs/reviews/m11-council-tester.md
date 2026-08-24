---
record_type: review
id: m11-council-tester
status: ratified
seat: independent
date: 2026-08-24
---
# M11 Council — Tester seat: does this suite CATCH or DESCRIBE?

**Seat:** independent. This seat authored none of the code or tests under assessment. Policy was
read from the protected base ref (`git show HEAD:AGENTS.md`, `subagent-profiles/Tester.md`) —
V4C-06. Nothing in the working tree was consulted for policy.

**This is a situation assessment, not a wave gate.** No verdict is issued and nothing is blocked.

**Baseline, measured rather than quoted.** `python -B -m pytest`: **714 passed, 12 skipped** in
5.7 s. Coverage **88.34 %** (`coverage.json` totals), `scripts/coverage_floor.py` PASS — 33 modules,
floor 60 %, 1 exemption. `make swift-test`: **59 Swift tests, 0 failures** against a floor of 59.

---

## 1. Mutation sample (V3C-72 protocol)

**Protocol.** Every mutant is an exact string replace applied IN PLACE with `pathlib.write_text`.
The suite is run with `python -B -m pytest -q --no-cov`. The change is then string-replaced back IN
PLACE — **no `git checkout`, no `git restore`, at any point** — and the file's md5 is compared
against the hash captured before injection. Every one of the 54 injections below restored to a
byte-identical file; the pre-injection hashes are recorded in §1.5 and were re-verified from the
shell after each round.

### 1.1 Round A — the headline sample (17 mutants across the scoring path, refresh, adapter, client)

| # | Mutant | Result | Killed by |
|---|---|---|---|
| R1 | `rank.py` `BLEND_INPUT_WEIGHT` 0.75 → 0.70 | **KILLED** | `test_rank.py::test_ranking_takes_best_score_and_its_harness` |
| R2 | `rank.py` reference price = `min()` instead of `median()` (REQ-CAN-003's headline rule) | **KILLED** | `test_rank.py::test_median_of_per_source_medians_beats_outlier_source` |
| R3 | `rank.py` `require_price_medians`: `built <= 0` → `built < 0` | **KILLED** | 7 tests incl. `test_cli_e2e.py::test_cli_an_unbuilt_artifact_exits_2_not_1`, `test_api_v1.py::test_an_unbuilt_artifact_is_refused_rather_than_answered_empty` |
| R4 | `rank.py` `attributions_for`: unattributed source `continue`s instead of raising | **SURVIVED** | — |
| R5 | `rank.py` `ORDER BY b.best DESC` → `ASC` (ranking inverted) | **KILLED** | `test_categories.py::test_assistant_ranking_orders_by_elo`, `test_rank.py::…`, `test_ranking_payload.py::test_the_ranking_is_in_the_engines_order_and_the_client_never_re_sorts` |
| C1 | `recommend.py` budget cap `<= cap` → `< cap` | **SURVIVED** | — |
| C2 | `recommend.py` value window × 100 (window effectively removed) | **KILLED** | `test_recommend.py::test_value_pick_rule_within_window_cheapest`, `test_recommend_assistant.py::test_assistant_value_window_uses_elo_threshold` |
| C3 | `recommend.py` quality floor `>= floor` → `> floor` | **SURVIVED** | — |
| C4 | `recommend.py` near-tie `gap <= close_pts` → `gap < close_pts` | **SURVIVED** | — |
| C5 | `recommend.py` `STALE_NOTICE_DAYS` 90 → 900 (REQ-REC-006 notice never fires) | **KILLED** | `test_coverage.py::test_stale_window_matches_the_engines_disclosure_window`, `test_recommend_assistant.py::test_stale_primary_source_is_disclosed` |
| C6 | `recommend.py` Pareto dominance price axis `<` → `<=` | **SURVIVED** | — |
| F1 | `refresh.py` `MAX_SURFACE_LOSS` 0.25 → 0.95 (D-128 shrinkage guard) | **KILLED** | `test_refresh.py::test_a_loss_of_exactly_a_quarter_is_refused` + 2 |
| F2 | `refresh.py` `MAX_MEDIAN_PRICE_MOVE` 0.25 → 25.0 (D-132) | **KILLED** | `test_refresh.py::test_a_median_price_collapse_is_refused` |
| F3 | `refresh.py` add `evidence_date` to `UNHASHED_ROW_FIELDS` (re-creates W-049) | **KILLED** | `test_refresh.py::test_a_freshness_or_provenance_update_is_published[run_date-2026-08-22]` |
| A1 | `main.py` `_bounded_pick` bound × 10000 (third-party text unbounded) | **KILLED** | `test_ranking_payload.py::test_third_party_text_in_a_ranking_row_is_bounded`, `test_stage40_minors.py::test_a_hostile_harness_string_is_bounded_before_it_reaches_a_caller` |
| A2 | `main.py` `/v1` ranking publication allowlist removed | **KILLED** | `test_ranking_payload.py::test_the_ranking_publishes_only_its_declared_field_set` |
| L1 | `litellm.py` `_is_price` `v > 0` → `v >= 0` (a zero price becomes usable) | **KILLED** | 4 tests in `test_litellm_ingest.py` |

**Round A kill rate: 12 / 17 = 71 %.**

### 1.2 Round B — coarse mutations of the nine surfaces' calibrated thresholds (15 mutants)

Every `min_quality` set to 1.0, one `close_call` to 500, three `value_window`s inverted.
**15 / 15 KILLED.** But look at *what* killed them: eleven of the fifteen died to a single test,
`test_categories.py::test_no_threshold_is_on_a_scale_its_own_metric_cannot_reach`, and three more to
`test_no_category_can_exclude_a_model_it_calls_level_with_the_leader`. Those are **scale and
relational invariants** — "a percentage floor lives in (0,100]", "value_window ≥ close_call". They
are good tests and their docstring says exactly what they do not do: *"This does not pin the
calibrated VALUES."* Round B therefore measures the invariants, not the calibration. Round C
measures the calibration.

### 1.3 Round C — *plausible* mis-calibrations (18 mutants)

Each threshold moved by the amount a real calibration error would move it — 5–15 %, staying on the
right scale, staying inside every existing invariant.

| # | Mutant | Result | Killed by |
|---|---|---|---|
| P1 | `everyday` min_quality 149.9 → 140.0 | **SURVIVED** | — |
| P2 | `expert` min_quality 83.6 → 80.0 | **SURVIVED** | — |
| P3 | `computer-use` min_quality 53.4 → 48.0 | **SURVIVED** | — |
| P4 | `abstract` min_quality 72.8 → 68.0 | **SURVIVED** | — |
| P5 | `web-dev` min_quality 1478.9 → 1450.0 | **SURVIVED** | — |
| P6 | `mathematics` min_quality 84.4 → 80.0 | **SURVIVED** | — |
| P7 | **`coding` min_quality 65.0 → 58.0** | **SURVIVED** | — |
| P8 | `assistant` min_quality 1400.0 → 1350.0 (its pre-M3 value) | **KILLED** | `test_recommend_assistant.py::test_assistant_budget_floor_uses_elo` + 2 |
| P9 | `everyday` close_call 0.5 → 1.4 | **SURVIVED** | — |
| P10 | `computer-use` close_call 0.8 → 2.0 | **SURVIVED** | — |
| P11 | `abstract` close_call 1.0 → 2.5 | **SURVIVED** | — |
| P12 | `web-dev` close_call 6.8 → 15.0 | **SURVIVED** | — |
| P13 | `mathematics` close_call 9.5 → 4.0 (below the board's own stderr) | **SURVIVED** | — |
| P14 | `assistant` close_call 8.0 → 12.0 | **KILLED** | `test_recommend_assistant.py::test_close_call_threshold_is_the_calibrated_elo_value` |
| P15 | `everyday` value_window 3.0 → 4.5 | **SURVIVED** | — |
| P16 | `mathematics` value_window 10.0 → 7.0 | **KILLED** | `test_categories.py::test_no_category_can_exclude_a_model_it_calls_level_with_the_leader` (only because 7.0 < close_call 9.5 — the *relational* invariant, not the value) |
| P17 | `web-dev` value_window 100.0 → 60.0 | **SURVIVED** | — |
| P18 | `assistant` value_window 30.0 → 45.0 | **KILLED** | `test_recommend_assistant.py::test_close_call_threshold_is_the_calibrated_elo_value` |

**Round C kill rate: 4 / 18 = 22 %.** Three of the four kills are on `assistant` — the one surface
with a fixture deliberately bracketing its threshold. The fourth is a relational accident.

### 1.4 Rounds D and E — positive controls on the repo-scanning guards (4 mutants)

I planted the *defect* rather than removing the *guard*, which is the harder direction.

| # | Planted defect | Result | Killed by |
|---|---|---|---|
| G1 | a calibration script reaching the population without importing `ranked_population` | **KILLED** | `test_ranked_population.py::test_every_threshold_producing_script_imports_the_named_accessor` |
| G2 | a hand-built `f"file:…?mode=ro"` sqlite URI planted in `src/app/workflows/rank.py` | **KILLED** | `test_readonly_uri.py::test_nothing_in_the_repository_builds_a_read_only_uri_by_hand` |
| G3 | an ASCII-Turkish user-facing sentence planted in `src/app/workflows/recommend.py` | **KILLED** | `test_language_of_shipped_strings.py::test_no_shipped_string_is_turkish_written_in_ascii` |
| H1 | `rank.py` swallows every `sqlite3.OperationalError` into "unbuilt artifact" | **KILLED** | `test_unbuilt_evidence.py::test_an_operational_error_that_is_not_a_missing_table_is_re_raised` |

**4 / 4 KILLED.** These are real controls, not decoration. H1 is also the round's methodological
lesson: `coverage.json` lists `rank.py:216,220` as uncovered, so a coverage reading would have
called that guard untested. The mutation says it is tested. **Coverage measured the message
strings; mutation measured the branch.**

### 1.5 Totals and restoration proof

**54 mutants, 35 killed — 65 % overall; 71 % on the headline engine sample; 22 % on plausible
calibration drift.**

Pre-injection md5, re-verified from the shell after the final round, all matching:

```
e9a687ba2e0f34803cc49294485af135  src/app/workflows/rank.py
4c17631e454a08004b0a4d138bd5069d  src/app/workflows/recommend.py
33b65fbfa6f37fcc1669d0e5f7a6c378  src/app/workflows/categories.py
784f1bad077be481528b4f043652d398  src/app/workflows/refresh.py
4705dadc2546cdd547409de08397ea42  src/app/adapter/main.py
d53202a22b08ee0d8b65d2b131d896b2  src/app/clients/litellm.py
8a33b5af2b866126364c6841d253cf1f  scripts/arena_calibration.py
```

Suite re-run after restoration: **714 passed, 12 skipped**. Working tree unmodified.

---

## 2. What the survivors have in common

Nineteen mutants survived. They are not scattered — they fall into exactly two shapes, and the two
shapes are the same defect wearing different clothes.

### Shape 1 — the comparison is exercised, the BOUNDARY is not (C1, C3, C4, C6)

Four of the five Round-A survivors are a single character: `<=`→`<`, `>=`→`>`, `<`→`<=`. Each is the
case where a value sits **exactly on** the threshold. Measured:

- **C1, budget cap.** The canonical coding fixture (`tests/unit/test_recommend.py:82-100`) has
  blended prices **{10.00, 3.44, 1.12, 0.31, 0.14}**. The `low` cap is 2.00. The nearest model is
  0.88 away. Any cap in **[1.12, 3.44)** produces an identical answer — the test pins a $2.00
  constant to a $2.32-wide band. I checked the shipped artifact too: `advisor.db` has 72 priced
  models and **none** at exactly 2.00 or 8.00 (the nearest is `glm-5.2` at **1.98**, two cents
  away). The boundary is unreachable in fixture *and* in production data today, and two cents from
  reachable tomorrow.
- **C3, quality floor.** Same fixture: scores **{79.2, 75.8, 74.4, 70.0, 40.0}**, floor 65.0. There
  is a **30-point hole** between 40.0 and 70.0. Any floor in (40.0, 70.0] gives the same three
  picks. P7 confirms it: 65.0 → 58.0, fully green.
- **C4, near-tie.** Both tests that reach the branch (`test_recommend.py:259`, `:414`) construct an
  **exact tie** and assert the word `"is level"`. The 1.5-point threshold is exercised only at
  gap = 0.0, so it is pinned to "≥ 0".
- **C6, Pareto price tie.** Every fixture has all-distinct prices, so "same price, worse score" can
  never occur. In the **shipped `advisor.db` it occurs 9 times** — 19 of 72 models share a blended
  price with another (ties at 6.00 ×3, 10.00 ×3, 8.75, 4.50, 3.44, 3.06, 3.00, 0.52, 0.51). The one
  input shape that distinguishes `<` from `<=` is absent from every test and present in the
  artifact the product actually serves.

### Shape 2 — the number is asserted, but not the number the engine reads (all 14 Round-C survivors, and R4)

`recommend.py:43-48` defines `MIN_QUALITY_PCT`, `VALUE_WINDOW_PTS`, `CLOSE_CALL_PTS`,
`MIN_QUALITY_ELO`, `VALUE_WINDOW_ELO`, `CLOSE_CALL_ELO` and says in its own comment that they exist
"for tests/documentation of the shipped values". The engine reads **`spec.min_quality`,
`spec.value_window`, `spec.close_call`** from `categories.py` (`recommend.py:305-307`). The tests
assert the alias:

- `tests/unit/test_recommend.py:238` — `assert MIN_QUALITY_PCT == 65.0`
- `tests/unit/test_recommend.py:225` — `assert VALUE_WINDOW_PTS == 6.0`
- `tests/unit/test_recommend.py:261` — `assert CLOSE_CALL_PTS == 1.5`
- `tests/unit/test_recommend.py:167` — `assert BUDGETS["low"] == 2.0`

Mutating the alias (E1) turns one test red. Mutating **the value the engine actually applies** (P7)
turns nothing red. The assertion is a literal compared to itself in the same module — the purest
form of the defect this council named. `assistant` is the exception and the proof that the shape is
avoidable: `test_close_call_threshold_is_the_calibrated_elo_value`
(`tests/unit/test_recommend_assistant.py:165-195`) places a runner-up **6.5 Elo behind — inside the
calibrated 8, outside the superseded 5** — so the assertion can only hold if the shipped number is
the calibrated one. It was written after a stay-green fault at M3 closure, and it is the only
threshold test in the repository built that way. It killed P14 and P18 and helped kill P8.

**R4 belongs to Shape 2 as well.** `attributions_for` raises on an unattributed source; the tests
that care about attribution (`test_categories.py:213`) assert the **map** covers the source
registry, never driving the function with an unknown source. `rank.py:98-99` is executed by no
test, so replacing `raise ValueError` with `continue` — which silently drops a CC-BY obligation
rather than failing loud — is invisible.

**The common root, stated once.** Every survivor is a place where the test names the right subject
and then asserts against something the fixture can satisfy without the subject being right: a
constant that mirrors itself, a comparison restated verbatim from the implementation, or a
threshold with no data on either side of it. That is precisely the recorded twelve-times defect —
*a test whose fixture cannot reach what it asserts*. It has not been fixed; it has moved from
labels and gates into **numbers**, which is a quieter place to hide.

---

## 3. Fixtures that cannot fail — concrete instances

1. **`tests/unit/test_recommend.py:174`** — `assert p.blended_per_m <= 2.0`. Verbatim restatement of
   `recommend.py:147`'s own comparison (`r.blended_per_m <= cap`), evaluated against a fixture with
   no model within 0.88 of the cap. Mirror-implementation *and* unreachable boundary in one line
   (V3C-86).
2. **`tests/unit/test_recommend.py:245`** — `assert cheap.score >= 65.0`. Same shape against
   `recommend.py:312`. The fixture's 30-point score hole makes the number unfalsifiable to ±7.
3. **`tests/unit/test_recommend.py:207`** — `dominated = any(o.score > p.score and o.blended_per_m <
   p.blended_per_m for o in ranking)`. A **character-for-character copy** of `recommend.py:156`. If
   the implementation's predicate changes, the test's private copy does not, and the assertion
   ("the picks are not dominated") remains satisfiable under both. C6 survived here.
4. **`tests/unit/test_recommend.py:219-221`** — `assert "GPT-5" not in names` / `assert "Gemini 3
   Flash" in names`. Real behavioural assertions, but the fixture's five distinct prices mean the
   frontier is identical under `<` and under `<=`. The case the assertion is *about* cannot arise.
5. **`tests/unit/test_recommend.py:238` / `:225` / `:261` / `:167`** — four constants asserted equal
   to their own literals in the module that defines them. These are the "count that equals itself"
   class exactly, and §2 shows they are decoupled from the engine.
6. **`tests/unit/test_budgets_endpoint.py:71-73`** — `for answer in answers: ranking = … ; if not
   ranking: continue`. If the shipped artifact ever stopped publishing a ranking for a surface, the
   loop body never runs and the test is green having asserted nothing. Its sibling four lines below
   (`:91`, `assert rows, "fixture assumption: the surface must publish a ranking on real data"`)
   has exactly the guard this one lacks — same file, same author, one protected and one not. I
   measured today's artifact: all eight (task, budget) combinations do return rows (44–65 per
   surface), so this is **latent, not currently vacuous**. It is one bad refresh from becoming a
   green test that checks nothing.
7. **`tests/unit/test_ranked_population.py:188-192`** — the loop over `scripts/*.py` skips any file
   not containing the literal `"value_window"` or `"min_quality"`. Measured: **exactly one script
   qualifies** (`arena_calibration.py`). A future calibration script that spells the concept
   differently is silently exempt, and if that one script were renamed, `offenders` would be empty
   and the test green having inspected nothing. There is no "at least one script was examined"
   assertion. (The rule itself does work — G1 proved it.)
8. **`tests/unit/test_language_of_shipped_strings.py:82-93`** — asserts the guard's own word list is
   ASCII and `len >= 20`. Self-consistency about a fixture; it says nothing about the product. The
   *real* test in that file (`:59`) is sound and G3 proved it fires.

---

## 4. What is untested by construction — and is the line in the right place?

### `ios/ModelRanking/ContentView.swift` — the line is in the WRONG place, and by ~200 lines

W-060 (`docs/warnings.ledger.md:106`) states the scope honestly: *"`ContentView.swift` and
`ModelRankingApp.swift` are SwiftUI and remain unexecuted — a deliberate scoping decision (the
Engine is where a defect changes what a reader is TOLD)."* The rationale is right. The **boundary
drawn from it is not**, because the file is 551 lines and only some of it is layout. Inside it:

- **`ContentView.swift:538-551`, `enum Format`** — a `NumberFormatter` pinned to `en_US_POSIX` with
  `maximumFractionDigits = 3`, `usesGroupingSeparator = false`, and a `?? "\(value)"` fallback. This
  is the only number-formatting code in the app, it has a **recorded locale defect in its own
  history (`$2,06`)**, and it decides what price a reader sees. It is pure, deterministic, has no
  view dependency, and has zero tests. By W-060's own criterion — *"where a defect changes what a
  reader is TOLD"* — this belongs inside the line, not outside it.
- **`ContentView.swift:200-204`** — `answer.eligibleCount < answer.ranking.count ? "See all N — M
  fit your budget" : "See all N"`. A threshold comparison producing the budget disclosure that an
  independent payload review specifically demanded. Untested.
- **`ContentView.swift:129-139`** — two different sentences depending on whether `rankingEffort` is
  nil. That is REQ-REC-011's disclosure rendered, and the Python side treats the equivalent branch
  as load-bearing enough to have `effort_disclosure()` tested directly.
- **`ContentView.swift:246-254`** — a five-optional `compactMap` that decides **which disclosures
  appear at all**: stale notice, effort-mix notice, close call, unavailable reason, ordering note.
  Every one of those is a thing the engine went to considerable trouble to compute honestly.
- **`ContentView.swift:68-70` and `:165-170`** — `orderAnswers`, `previewRows` and `filterRanking`
  are individually well tested in `EngineTests`, but their **composition** is written inline in the
  view and is not compiled by the test target at all.

**Judgement.** The decision to leave SwiftUI *layout* unexecuted is correct and I would not move it.
What is wrong is that roughly 200 lines of *decision logic* have been classified as layout by
adjacency — they are in the view file, so they are outside the line. The remedy is not "test
SwiftUI": it is to move `Format`, the disclosure aggregation, and the eligible-count sentence into
`Engine/` where the existing 59 tests already run, after which the untested remainder really is
layout and the line is in the right place. This is also the cheapest fix in this document.

**One gate observation, found by running it.** `make swift-test` greps `Executed [0-9]+ tests, with`
and floors at 59. The `swift test` output carries **two** runners: XCTest reports `Executed 59
tests`, and swift-testing separately reports `Test run with 0 tests in 0 suites passed`. The floor
sees only the XCTest line. A future test written with the `@Test` macro would run, pass, and be
**invisible to the count floor** — so the floor could never be raised to protect it. The gate still
fails closed if the XCTest suite stops being discovered, which is the direction it was built for.
MINOR, and worth a line in the Makefile comment that already documents three prior versions of this
same gate being unable to fail.

### `scripts/` — the gates are unevenly tested, and the ones with no test are the ones with authority

Measured, per script: **tested** — `ci_coverage_gate.py` (8 tests), `slopsquat_check.py` (via
`test_dependency_gate.py`), `arena_calibration.py` (2 tests in `test_ranked_population.py`);
**partially tested** — `wave_check.py` (18 tests, but only the `review_seat_problems` block of a
20 KB script); **NO TEST** — `coverage_floor.py`, `check_records.py` (64 KB, the largest script in
the repo), `wave_check_all.py`, `conformance_gate.py`, `smoke_deps.py`, `journey.py`.

Two of those matter more than the rest:

- **`scripts/coverage_floor.py` — untested, and it is the control that exists *because* a global
  percentage lied.** Its own docstring records that 88 % concealed a module at 32 %. It reads
  `coverage.json` from the repo root with **no freshness check**: nothing ties the file's mtime to
  the source tree. `make check` happens to run `test` before `coverage-floor`, so in practice it is
  fresh — but the ordering is the only thing preventing this gate from certifying a stale artifact,
  and that ordering is a Makefile line, not an assertion. This is the same class as the `make
  conformance` directory-collision and the `swift test | tail -3` pipe already recorded in the
  Makefile: a control whose correctness depends on something outside itself.
- **`scripts/check_records.py`** has no pytest coverage at all. It is exercised only by `make
  check-records-selftest` against `conformance/` fixtures — which is a real control (V4C-32 exists
  precisely to prove the validator is not a no-op) and I am not calling it untested. But it is the
  one script every governance record in the repository depends on, and it is outside the suite that
  this project's whole culture is organised around.

### Shell — W-074's line is right, and it is drawn one file short

W-074 (`docs/warnings.ledger.md:120`) is exact: *"the shell in this repository is **unlinted**,
`shellcheck` is not installed and no gate runs it, across `runner` and every script under
`scripts/`"*, escalated to the owner because adding it to `make check` is a gate-definition change.
Confirmed independently: `make lint` is `ruff check src tests scripts` (`Makefile:75-76`), ruff
reads only `.py`, and `shellcheck` appears **nowhere** in `Makefile`, `.github/`, or
`.pre-commit-config.yaml` — only in prose records.

The inventory is **1133 lines of shell**: `runner` (327), `scripts/bootstrap-check.sh` (225),
`scripts/simulator_session.sh` (200), **`ios/app.sh` (171)**, `scripts/standup.sh` (77),
`scripts/pin-actions.sh` (71), `scripts/enable_refresh.sh` (53), `docs/smoke-deps.sh` (9).
`ios/app.sh` is **not in W-074's stated scope** (`runner` + `scripts/`) — 171 unlinted, untested
lines that the ledger row does not cover. The escalation is correct and pending; the row should be
widened to name it before M12 acts on it, or M12 will fix seven files and leave the eighth.

---

## 5. Is any of the suite ceremony?

Mostly no, and I went looking hard. The repo-scanning guards are the obvious suspects — they are
the shape that usually turns out to be theatre — and **all four positive-control probes were caught
(G1, G2, G3, H1)**. `test_ci_argument_drift.py` executes real workflow YAML under `bash -e` and
carries explicit falsifiability probes at `:68` and `:118`. `test_stage40_minors.py` drives real
production code through the real `TestClient`. Several tests carry an anti-vacuity guard in the
exact place one is needed (`test_budgets_endpoint.py:91`, `test_ci_coverage_gate.py:79`,
`test_ios_platform_drift.py:28`). This is a suite written by people who know the failure mode.

Three things are ceremony, and they are small and specific:

1. **The four alias-constant assertions** (`test_recommend.py:167, 225, 238, 261`). A literal
   compared to itself, in the module that defines it, decoupled from the engine — measured in §2.
   These are the only assertions in the suite I would call purely decorative, and they are
   load-bearing decoration: they are what makes `coding`'s thresholds *look* covered.
2. **`test_language_of_shipped_strings.py:82-93`**, the meta-test about the guard's own word list.
3. **A proportion problem rather than a ceremony problem:** `tests/unit/test_review_seat_gate.py` is
   302 lines and 18 tests, entirely synthetic subject and synthetic input, proving a wave-checklist
   parser behaves on markdown the test wrote three lines earlier. It is *correct* and it repaired a
   real unwiring defect (its comment at `:140-145` records it). But 302 lines of tests for a
   governance-record parser, against **0 executing lines for the 551-line screen the customer
   actually looks at**, is a statement about where this project believes risk lives. On the
   evidence of §1 and §4, that belief is misplaced.

---

## 6. The ONE test I would add

> **`tests/unit/test_categories.py` — `test_every_calibrated_threshold_still_selects_the_population_the_record_defends`**

**What it does.** Open the shipped `advisor.db` read-only (the precedent exists —
`test_budgets_endpoint.py:27` already does this). For each of the nine surfaces, call
`ranked_population(conn, spec)` — the named accessor REQ-EVI-002 created for exactly this purpose —
and assert two derived counts against the numbers the ratified calibration record defends
(`docs/reviews/m8-category-calibration.md`, the 2026-08-19 correction table):

- how many of the ranked population clear `min_quality`;
- how many sit within `value_window` of the leader.

**Why those two numbers, and why they are the right referent.** I measured them today, against the
live artifact:

| Surface | ranked | clears floor | record | within window | record |
|---|---|---|---|---|---|
| everyday | 58 | 29 | — | **5** | **5** |
| expert | 50 | **37** | **37** | **25** | **25** |
| mathematics | 51 | **34** | **34** | **28** | **28** |
| computer-use | 33 | **14** | **14** | **5** | **5** |
| abstract | 39 | **20** | **20** | **8** | **8** |
| web-dev | 49 | **23** | **23** | **3** | **3** |
| coding | 44 | 33 | — | **7** | **7** |

**Every number the record states still reproduces exactly, four days later, on today's artifact.**
That is a set of currently-true, falsifiable, cross-artifact facts that no test asserts. The record
is the external referent the constants lack — which is why this cannot degenerate into the mirror
test that a fixture derived from `spec.min_quality` would be.

**Why there, and not somewhere else.**

1. **It kills the survivors that matter.** P1–P7, P9–P13, P15 and P17 all move an admitted or
   candidate count and would go red. That converts a **22 % kill rate into something near 100 %** on
   the single largest untested surface in the engine — 27 numbers across 9 surfaces, of which 7
   surfaces currently have no data-driven test at all (`recommend()` is called for `coding`,
   `assistant` and `agentic-coding` only; the other six are reached through the API, never with
   their thresholds asserted).
2. **It targets the defect this project has actually had, three times.** W-037 records thresholds
   sized against the wrong population *three separate times* — CSV rows, parsed board rows, then the
   full board — *"and all three were caught by measuring rather than by review."* This test is that
   measurement, executed on every run.
3. **It is the only one of my candidates that catches the FUTURE defect as well as the present
   one.** The refresh publishes twice a day from live boards. The thresholds are static. The
   realistic next failure is not a hand edit — it is the boards moving until a floor that admitted
   14 of 33 admits 30 of 33, at which point `computer-use`'s Budget Pick stops having a quality bar
   and every gate stays green, exactly as W-041's 32 % module did. Nothing in the repository can
   currently see that happen. This test sees it on the first refresh that crosses the line.
4. **It is the shape that already works here.** It is
   `test_close_call_threshold_is_the_calibrated_elo_value` — the one threshold test with an external
   referent, born of a stay-green fault — generalised from one surface to nine, and
   `test_contract_change_provenance.py`'s code-versus-record cross-check applied to numbers instead
   of ADR IDs. Both patterns are this project's own.

**Second choice, named so it is not lost:** a boundary case at each threshold — one model priced at
exactly the cap, one scoring exactly the floor, two tied on blended price. It kills C1, C3, C4 and
C6 in one fixture, and C6's input shape occurs **nine times in the artifact being served right
now**. I rank it second only because a mis-calibration changes what every reader is told, while a
boundary defect changes what one reader is told about one model.

---

## 7. What I did NOT cover

- **Only 54 mutants, hand-picked.** No mutation runner is wired for this stack (mutmut/cosmic-ray),
  so this is a judgement sample of the scoring path, refresh, adapter and one client — not an
  exhaustive kill-rate. `subscribe.py` (599 lines), `build.py` (553), `schema.py` (497),
  `board_measurement.py` (616), `coverage.py`, `plans.py`, `rosters.py`, `registry.py`, `sources.py`,
  `ingest.py`, `yaml_guard.py` and six of the eight clients were **not mutated at all**. The 65 %
  figure should not be read as the repository's kill rate.
- **No Swift mutation.** I ran the 59 Swift tests and read the sources, but injected nothing into
  `Engine/`. The `EngineTests` kill rate is unmeasured.
- **`scripts/` not mutated.** I established which gates have tests and probed four of them with
  planted defects; I did not mutate `check_records.py`, `wave_check.py`, `conformance_gate.py` or
  `coverage_floor.py` to measure whether their tests would catch a weakening.
- **The 12 skipped tests were left skipped.** Five contract tests need `RUN_CONTRACT_TESTS=1` and
  network; seven need `EPOCH_DATA_DIR`. I did not supply either, so the real-API contract tests
  (V3C-44) are **unverified by this seat** — including whether the canonical mocks have drifted from
  the live feeds. That is a meaningful gap given six of nine surfaces are fed from the Epoch bundle.
- **`make check` was not run end to end.** I ran `pytest`, `coverage_floor.py` and `swift-test`. I
  did not run `lint`, `typecheck`, `check-records`, `conformance-gate`, `wave-check-all`,
  `install-check`, `secrets`, `deps` or `slopsquat`.
- **No red→green work.** This is an assessment, so I wrote no tests and fixed nothing. Every finding
  above is a description of a hole, not a repair — including the one in §6, which I recommend and
  did not write.
- **No review of M11's diff.** I did not read the wave commits, the M11 plan's acceptance criteria,
  or whether each has a citing test. This seat assessed the suite as a whole, per the convening
  brief; the per-criterion V3C-02 trace for M11 is not covered here and should not be assumed from
  this record.
