---
record_type: review
id: m13-wave-2-rereview
status: ratified
seat: independent
date: 2026-09-15
---
# M13-W2 — Code-Reviewer seat, re-review of the fixes

**How this record was produced.** This is the same independent seat that wrote
`docs/reviews/m13-wave-2-review.md`, working under the same rules. It read its policy from the
protected base ref (`HEAD` = `3440abe`) and was read-only on the repository apart from this one new
file. It received the post-fix diff `m13-w2-r2.diff`: 1566 lines, 15 files, the full W2 against
HEAD with `docs/reviews/` excluded. The diff was applied to a fresh `git archive HEAD` export in
the session scratchpad, with a copy of the shipping artifact `advisor.db`. All measurements were
made there. Nothing was measured against the working tree. Every `file:line` below is in the tree
with the post-fix diff applied.

**My first record was edited by the lead agent.** Lines 228 and 257 of `m13-wave-2-review.md` now
wrap the quoted words `confidence` / `güven` (and `confiden`) in backticks so the L1 gate reads
them as code. I checked both lines. The words are unchanged, the record is still 290 lines, and
the verdict and finding headings are intact. **I do not object.** The edit is formatting only and
changes no judgement.

## Baseline at the post-fix tree

| Check | Result |
|---|---|
| `pytest tests/unit` (with a copy of `advisor.db`) | **857 passed**, 7 skipped. The coordinator reports 866 / 12 for the working tree; the difference comes from files outside this diff, which excludes `docs/reviews/` |
| `swift test` | 163 tests, 0 failures |
| `xcodebuild` (iOS Simulator, `CODE_SIGNING_ALLOWED=NO`) | **BUILD SUCCEEDED** |
| `ruff check src tests` / `mypy src` | clean / clean (33 files) |
| `check_records.py --root .` | PASS, 77 records |
| `black --check` on the touched Python files | only `test_ios_client_contract.py` would be reformatted, and HEAD has the same result, so it predates this diff |

## Verdict: PASS WITH FINDINGS

BLOCKING-1 is discharged by construction and by measurement. The rank ranges cannot order two
models whose raw gap is inside the margin, and this holds on every surface of the shipping
artifact. MAJOR-1 and MAJOR-2 are discharged in code and in D-138, but each leaves one stale
sentence or figure behind. The fixes introduce one new finding, NEW-1: REQ-APP-005's requirement
row is now contradicted by design, and the gate that enforces it cannot see the contradiction.
No finding blocks the wave.

---

## Disposition of each finding from the first review

### BLOCKING-1: DISCHARGED

`ios/ModelRanking/Engine/Uncertainty.swift:67-86` (`rankRanges`), wired at
`ios/ModelRanking/ContentView.swift:151-153`.

**The mechanism is sound.** Take models *i* above *j* whose served gap is at most
`sep = margin + 0.1 + 1e-9`. Let A be the models clearly ahead of *j* and B the models clearly
behind *i*. A and B are disjoint, because a model in both would put *i* and *j* more than 2·sep
apart. Neither set contains *i*. So |A| + |B| ≤ n − 1, which is `best(j) ≤ worst(i)`. The proof
covers every pair whose served gap is within `sep`, so it includes the one rounding step, not only
pairs within the margin itself.

**Replayed on the shipping artifact** with a Python mirror of the Swift arithmetic:

```
pairs with RAW gap <= margin whose ranges do NOT overlap, all nine surfaces: 0
coding/medium, the case BLOCKING-1 reproduced:
    engine: "GLM-5.2 is only 0.6 points behind … either choice is defensible"
    screen: Gemini 3.5 Flash #2–6   GLM-5.2 #3–9   -> overlap
```

**Citing tests.** `UncertaintyTests.swift:32` is the overlap property over all nine shipping
margins and randomised rankings. `:74` pins both the rounding step and the float tolerance
(`[94.4, 89.3]` must overlap, `[94.4, 89.2]` must not). `:23` gives exact expected ranges.
`tests/unit/test_ios_client_contract.py:441` is a structural check that ContentView passes the
published margin into `rankRanges` and calls `rankLabel`, `shortRankLabel`, `evidenceLine` and
`leaderSentence`. Swift mutants are listed under "Mutants" below.

**The ruling is recorded.** It is in `docs/plans/m13-plan.md` §8 row 4, in D-138's status line
(`docs/decisions.md:1626`, *"supersedes the plan's §7 ruling 4"*), and in the amended prd row
(`docs/prd.md:469`). An owner ruling made in session cannot be verified from the diff. It is
recorded in the same way as every other ruling here.

**An observation for the owner, not a defect.** Ranges are wide on the noisy boards. On the shipping
artifact, 72 of 402 positions are exact. The `expert` leader reads `#1–27 of 50`, and the widest
range (on `expert` and `mathematics`) spans 37 places. That width is what the ruling chose to
disclose, and it is honest. It may still surprise a first reader.

### MAJOR-1: DISCHARGED in D-138 and in the test. One false sentence remains (OPEN-1)

- D-138 now says the field sets do not move, and says in as many words that the answer is not
  byte-identical and why (`docs/decisions.md:1665-1670`).
- `test_uncertainty_contract.py:254` compares every answer against `ANSWER_KEYS` from
  `test_api_v1`. That kills the first review's M6 mutant, which added an answer field.
- **Still open:** the `categories()` docstring at `src/app/adapter/main.py:1190` still ends *"and it
  is byte-identical."* This is the same false claim, now contradicted by the ADR it cites. See
  OPEN-1.

### MAJOR-2: DISCHARGED in code. One figure remains in D-138 (folded into OPEN-2)

- The client now errs only toward uncertainty. `separable = margin + servedResolution +
  floatTolerance` (`Uncertainty.swift:41`, `:71`). The replay above shows that rounding cannot
  order a pair the engine calls tied. The cost is stated in the docstring at `:58-63` and in
  D-138's "The rounding direction" paragraph.
- The false comment *"can disagree by one row"* is gone.
- `Uncertainty.swift:4` and `UncertaintyTests.swift:3` now say 25 of 50, which is the raw count.
  D-138 at `docs/decisions.md:1635` still says **26**. See OPEN-2.

### MINOR findings

| First-review finding | Status | Evidence |
|---|---|---|
| MINOR-1 (a stale age produces a false reason) | **DISCHARGED** | `ContentView.swift:504` re-reads categories on every `load()`, and a failed re-read keeps the old list. Some exposure remains: two separate requests can still straddle an artifact swap, but the window is now the gap between two requests, not a whole session |
| MINOR-2 (a null age read as "undated") | **DISCHARGED** | `Uncertainty.swift:251` says *"its run dates are not available"*; the Turkish at `:254` means the same. D-138 `:1638` says a client may claim only that the age is unavailable. Test: `UncertaintyTests.swift:224` |
| MINOR-3 (the contradiction reprinted through the fallback) | **DISCHARGED** | `evidenceLine` (`Uncertainty.swift:158-177`) falls back to the basis only for an unknown verdict. A contradictory "High" returns nil and nothing is rendered (`ContentView.swift:672`). Test: `UncertaintyTests.swift:265` |
| MINOR-4 (the note claimed a property of the board) | **DISCHARGED** | `main.py:685`: *"The {benchmark} evidence in this answer carries no evaluation dates"*. Test: `test_uncertainty_contract.py:206` |
| MINOR-5 (the `#` comment was false) | **DISCHARGED** | The comment at `ContentView.swift:635` is now true by construction: a single number appears only when no model is within `sep` on either side. Its example `#1–26` is covered by OPEN-2 |
| MINOR-6 (a fact stated twice under D-135; "margin of error") | **DISCHARGED** | The leader sentence appears only in the full-list header (`ContentView.swift:736`), not beside the engine's `close_call`. It says *"too close … to separate — its margin is N"* (`Uncertainty.swift:116-131`), and the docstring explains why it avoids "margin of error". Test: `UncertaintyTests.swift:148` |
| MINOR-7 (test quality) | **DISCHARGED** | (i) The test now inserts three real MMLU rows with a null `run_date` and asserts they are present (`test_uncertainty_contract.py:129`). (ii) The property test covers all nine shipping margins (`UncertaintyTests.swift` `shippingMargins`, `:32`). (iii) The tolerance is pinned (`:74`, see the mutants). The margins are copied by hand from `categories.py`, but the property holds for any margin, so a drift would not weaken it |
| MINOR-8 (the REQ-UNC-002 text; the "oldest" comment) | **DISCHARGED** | `docs/prd.md:470` is now the plan's criterion verbatim, plus its "Verified by" line. The docstring at `Uncertainty.swift:191-194` now states truthfully what the line shows and why it does not pick the older of the two boards |
| MINOR-9 (grammar) | **DISCHARGED** | `marginUnit(… singular:)` (`Uncertainty.swift:138`); `main.py:690` reads "an evaluation date from X". Test: `UncertaintyTests.swift:170` |
| MINOR-10 (drive-bys; the bypass not ledgered) | **NOT YET VERIFIABLE** | Plan §8 row 1 says the bypass is *"ledgered in the W2 close"*. That close file does not exist in the diff or in the working tree yet (only `m13-wave-1-close.md` exists). This stays open until the W2 close carries the row. Plan §8 row 3 ("commit and push") is consistent with D-117, which is already in force, so it adds no new git authority |
| NIT-1 ("Amends nothing") | **DISCHARGED** | `docs/decisions.md:1626-1627` |
| NIT-2 (`isoDate`) | **DISCHARGED** | `Uncertainty.swift:261-280` validates real calendar days. Test: `UncertaintyTests.swift:303`, including a leap day |
| NIT-3 (`_secondary_ages` was silent) | **DISCHARGED** | `main.py:1164`, `:1173`. It logs the exception type only, so no path is written to the log. The new test `test_uncertainty_contract.py:164` covers a file that exists but will not open |
| NIT-4 (black) | **DISCHARGED** | The touched test files pass `black --check`. `test_ios_client_contract.py` fails `black --check` at HEAD as well, and this diff only appends to it (`@@ -436,3 +436,27`) |

---

## Findings that remain or are new

| # | Severity | `file:line` | Finding | Remedy |
|---|---|---|---|---|
| OPEN-1 | MINOR | `src/app/adapter/main.py:1190` | The `categories()` docstring still says the answer payload *"is byte-identical"*. D-138 (`decisions.md:1668`) now says the opposite, and the diff itself changes `evidence_dating_note`. MAJOR-1 corrected the ADR and left the same false claim in the code | Change the sentence to "its field sets do not move" |
| OPEN-2 | MINOR | `decisions.md:1635`; `prd.md:469`; `m13-plan.md:320`; `ContentView.swift:635` | The records give three different figures for one fact. The raw leader band on `expert` is **25** (plan §0, `Uncertainty.swift:4`, `UncertaintyTests.swift:3`). D-138's context still says **26**. The example `#1–26 of 50` appears in the prd, the plan and ContentView. The screen will print **`#1–27 of 50`** and *"The top 27 of 50…"*, because the served count within `5.0 + 0.1` is 27. Each number is defensible on its own basis, but no record says which basis it uses | Say which count each figure is, or use the one the screen prints |
| NEW-1 | MINOR | `docs/prd.md:381` (REQ-APP-005); `docs/decisions.md:1660-1663`; `Uncertainty.swift:12-16`, `:78-81` | REQ-APP-005 still reads *"The app computes no ranking value of its own."* `rankRanges` computes positions from served scores. D-138 records that it crosses the requirement, but the requirement row itself is not amended, so a standing criterion is false by design. The ADR also records that the client-contract tripwire *"cannot see a subtraction on an array element"*, and leaves it that way. This is the V4C-49 pattern: a rule whose gate is known to be blind, now with a sanctioned instance passing through the blind spot. **The seat also missed this in round one**: the greedy `tieBands` subtracted served scores in the same way (`anchor - scores[end]`), and the first review did not flag it | Amend the REQ-APP-005 row to name the one exception (D-138, `Uncertainty.swift` only). Add a structural test that confines subtraction on served scores to `Uncertainty.swift`, or cite W-038 as the tracked gap |
| NEW-2 | NIT | `ios/ModelRanking/Engine/Models.swift:50` | The comment still says *"Absent means 'no bands'"*. Bands no longer exist. It should say "exact positions" | Change the wording |
| NEW-3 | NIT | `ContentView.swift:151`; `Uncertainty.swift:72-83` | `rankRanges` is O(n²) and runs inside the view body, so it recomputes on every render, including each keystroke in the filter. The greedy bands were O(n). The cost is trivial at today's n ≤ 65, but `MAX_RANKED_ROWS` is 5000 (`main.py:189`), which would mean about 25M comparisons per render at the ceiling | Compute once when an answer loads, or accept and state it |
| NEW-4 | NIT | `decisions.md:1645`; `prd.md:469`; `m13-plan.md:320`; `UncertaintyTests.swift:9`, `:35` | All five places say the review measured **49** within-margin pairs printed in different bands. The first review reported **47** (served scores; 45 on raw scores). Five records attribute to the review a number it did not report | Use 47, or cite whichever basis produced 49 |

## Mutants

**Python.** The first review's six mutants were checked against the post-fix tests. M6 (a new
answer field) is now caught by `test_uncertainty_contract.py:254`. The Tester seat's mutant
(`_secondary_ages` raising on an artifact that exists but will not open) is covered by `:164`.

**Swift, run on a private copy**, filtered to `RankRangeTests|LeaderSentenceTests|EvidenceBreadthTests`:

| Mutant | Result |
|---|---|
| A: drop the rounding step (`separable = margin + floatTolerance`) | caught by 4 tests, including `testOneRoundingStep…` and the exact-range test. The overlap property alone does **not** catch it, because the property checks pairs within `margin`. That is the rounding test's job, and it does it |
| B: drop the float tolerance | caught (`testOneRoundingStep…`, the `5.1000000000000085` case) |
| C: every model ranged `1…n` ("all tied") | caught by 8 tests |
| D: the contradiction returns the "two independent benchmarks" claim | caught (`testAPayloadThatContradicts…`) |
| E: the leader sentence counts exact positions instead of `best == 1` | caught by 3 tests |

None survived.

## Acceptance criteria evidence

| REQ-ID | Verdict | Code | Citing test |
|---|---|---|---|
| REQ-UNC-001 | **PASS** | `Uncertainty.swift:67-86` (`rankRanges`), `:88-104` (labels), `:116-131` (leader sentence); `ContentView.swift:151-153`, `:168`, `:635-645`; margin served at `main.py` (`close_call_margin`) | `UncertaintyTests.swift:32` (overlap property, nine margins), `:74`, `:23`, `:148`; `test_ios_client_contract.py:441` (wiring); `test_uncertainty_contract.py:56`, `:82`. Shipping replay: 0 raw-within-margin pairs ordered |
| REQ-UNC-002 | **PASS** | `Uncertainty.swift:158-257` (`evidenceLine`, `evidenceBreadth`); `ContentView.swift:617`, `:672`; age at `main.py` `_secondary_ages` | `UncertaintyTests.swift:192` (a second board over 180 days old carries its age), `:274` (no `confiden` or `güven` in any branch, either language), `:224`, `:265`; `test_uncertainty_contract.py:89` |
| REQ-UNC-003 | **PASS** | `main.py:685`, `:690` | `test_uncertainty_contract.py:206` (live route names DeepSWE), `:220` (mixed branch); `UncertaintyTests.swift:224` (unavailable second-board dates named) |

## K.8 contract drift check

The answer, pick and ranking field sets are unchanged. `test_uncertainty_contract.py:254` and
`test_api_v1.py:218` both compare every answer against `ANSWER_KEYS`. `/v1/categories` gains three
optional fields under D-138. **OK.**
