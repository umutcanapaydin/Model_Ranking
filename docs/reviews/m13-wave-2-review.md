---
record_type: review
id: m13-wave-2-review
status: ratified
seat: independent
date: 2026-09-15
---
# M13-W2 — Code-Reviewer seat

**How this record was produced.** A separate session that did not author any of the wave's code
performed this review. It received the frozen diff and read its policy from the protected base ref
(`git show HEAD:subagent-profiles/Code-Reviewer.md`, `HEAD:AGENTS.md`,
`HEAD:docs/reviews/m13-wave-1-review.md` for shape), never from the working tree or the diff
(V4C-06). Nothing in the diff attempted to alter review policy, so there is no injection-class
finding. The seat was read-only on the repository except for this one file. Every measurement below
was taken on private copies under the session scratchpad: `git archive HEAD` (the base), the same
copy with the frozen diff applied (the change), and a copy of the gitignored shipping artifact
`advisor.db`. The review was not made against the working tree, which may move under W3.

**Author family / reviewer family (V4C-03, advisory).** The author and the reviewer are both Claude
sessions, so the models are from one family. No second family was available. Fresh context is
asserted: this seat saw neither the authoring session nor its summaries.

**Diff reviewed:** `m13-w2.diff`, 1279 lines, 13 files (3 new). It applies cleanly to `HEAD` =
`3440abe`. Files: `.language-allow`, `docs/closure-report-m12.md`, `docs/decisions.md` (D-138),
`docs/prd.md` (REQ-UNC-001..003), `ios/ModelRanking/ContentView.swift`,
`ios/ModelRanking/Engine/Models.swift`, `ios/ModelRanking/Engine/Uncertainty.swift` (new),
`ios/EngineTests/UncertaintyTests.swift` (new), `src/app/adapter/main.py`,
`src/app/workflows/recommend.py`, `tests/unit/test_rosters.py`,
`tests/unit/test_secondary_evidence_age.py`, `tests/unit/test_uncertainty_contract.py` (new).
**Plan checked against:** `docs/plans/m13-plan.md` §1 rows 5–7, §2 W2, §3 (K.8 freeze), §7 (D1).
**Risk tier:** HIGH (plan §2 W2).

All `file:line` references below are to the tree with the diff applied.

## Baseline the seat established

| Check | HEAD (`3440abe`) | HEAD + diff |
|---|---|---|
| `pytest tests/unit` (with a copy of `advisor.db` present) | 843 passed, **1 failed**, 7 skipped. The failure is `test_rosters.py::test_stale_unselected_roster_link_is_not_disclosed`, the wall-clock fixture the wave fixes | **855 passed**, 7 skipped |
| `pytest tests/unit` without the artifact (a fresh clone) | 42 failed / 4 errors | 41 failed / 4 errors. These are the same artifact-dependent tests in both copies, so the cause is the environment, not the diff |
| New `tests/unit/test_uncertainty_contract.py` run against HEAD | collection error (`secondary_age_days` is not public at HEAD) | 11 passed |
| `swift test` (Engine package) | — | 163 passed, 0 failures |
| `xcodebuild -scheme ModelRanking -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build` | — | **BUILD SUCCEEDED**. `ContentView.swift` is outside the Swift package, so this is the only check that compiles it. `Uncertainty.swift` is picked up by the project's synchronized groups |
| `ruff check` on the touched Python files | — | clean |
| `mypy src` | — | clean (33 files) |
| `black --check` (what `make format` runs) | clean on the touched files | `test_secondary_evidence_age.py` and `test_uncertainty_contract.py` would be reformatted (NIT-4) |
| `scripts/check_records.py --root .` | — | PASS, 77 records |

Measurements taken on a copy of the shipping artifact are quoted in each finding. The Python
mutants and the Swift probe ran only on private copies.

## Verdict: BLOCKING

REQ-UNC-001, the wave's central criterion, fails on the shipping artifact, and it fails exactly as
the criterion describes. On one screen the engine says two models are indistinguishable and the
client presents them as ordered. D-138's main justification also states something false. The
endpoint, the evidence-count logic, the wiring and the records are otherwise sound. The details
follow.

---

### BLOCKING-1: the screen presents as ordered a pair the engine's own `close_call` calls tied

`ios/ModelRanking/Engine/Uncertainty.swift:62-79` (`tieBands`) and
`ios/ModelRanking/ContentView.swift:150-153` (bands computed from the whole, unfiltered ranking).

The engine decides `close_call` on the **budget-filtered Pareto frontier**
(`src/app/workflows/recommend.py:475` `eligible_rows(...)`, `:479` `pareto_frontier(rows)`,
`:495-497` raw `gap <= close_pts`). The client bands the **unfiltered full ranking**, greedily from
the global leader. When a budget excludes the models at the top, the greedy boundaries fall
wherever they fall, and they can separate the one pair the engine has just called tied.

Reproduced on the shipping artifact for `task=coding`, `budget=medium`:

```
engine close_call: "GLM-5.2 is only 0.6 points behind — the gap is within the margin of error and
                    either choice is defensible."
served ranking:    1 Claude Opus 4.7 83.5 | 2 GPT-5.5 80.6 | 3 Gemini 3.5 Flash 79.3 |
                   4 Claude 4.5 Opus 79.2 | 5 Claude Opus 4.6 78.7 | 6 GLM-5.2 78.7 | 7 ... 77.6
tieBands(margin 1.5), run through the shipping Swift on a private copy:
                   ["1", "=2", "=2", "=2", "=5", "=5", "=5"]
best-quality pick: Gemini 3.5 Flash -> "=2 of 44";   GLM-5.2 in the ranking list -> "=5"
```

The reader sees the disclosure *"either choice is defensible"* beside a pick labelled `=2` and the
named alternative labelled `=5`. That is a strict order between two models the engine calls
indistinguishable, which is the literal case REQ-UNC-001 forbids (`docs/prd.md:469`: *"Where the
engine's own `close_call` margin says two models are indistinguishable, the screen does not
present them as ordered"*). It happens on 1 of the 27 (surface, budget) combinations. The
budget picker (REQ-BGT-001) makes this state reachable in normal use.

This is not only a budget effect. The plan's own verification wording (`m13-plan.md` §1 row 5:
*"models within `close_call` of each other render a shared band"*) fails on **47 adjacent pairs**
on the shipping artifact. These are pairs within the margin of each other that sit in different
bands: coding 8, assistant 11, everyday 10, expert 4, mathematics 3, abstract 4, web-dev 7. The
code comment `Uncertainty.swift:50-54` accepts this as "Known and accepted". D1 (plan §7) does
rule greedy bands anchored at the top. But D1 does not rule that the client may contradict the
engine's `close_call` sentence on the same screen, and the prd row restates the unqualified
criterion as delivered.

**Why BLOCKING and not MAJOR.** The plan rates W2 HIGH because *"getting it wrong … re-creates the
problem it exists to solve"*. This wave's prd row claims REQ-UNC-001 as delivered, and on the
product's own data it fails the criterion's literal test. What the criterion means once greedy
bands meet a budget filter is a **criteria-meaning question**, and AGENTS.md §3 says to escalate
those now. Neither the author nor this seat can settle it.

**Remedy (the owner's choice, one of):**
(a) Make the pair the engine calls tied impossible to split. The client knows the best-quality
pick. It does not know `frontier[1]` without parsing prose, so this needs either a band anchored at
the budget's leader for the pick rows, or engine data. Per-row band membership is a payload move,
which D-138's "Revisit when" already names.
(b) Amend REQ-UNC-001 to D1's form: *"the leader's band is exact; lower bands are greedy and two
rows either side of a boundary may be within the margin"*. The amendment must state the measured
exception (47 straddles, 1/27 contradiction with `close_call`) and the owner must sign it.
(c) At minimum, when `answer.closeCall != nil`, do not print a `#`/`=N` distinction between the two
rows the sentence names. This is still (a) in disguise, because the client needs the runner-up's
identity.

Whichever is chosen, it needs a citing test that feeds a budget-filtered leader and asserts the
engine's close-call pair shares a label. No such test exists today.

### MAJOR-1: "`/v1/recommendations` is byte-identical" is false, and the test that is cited as proof asserts less

`docs/decisions.md:1643` and `src/app/adapter/main.py:1179` both claim the answer payload is
byte-identical. The same diff changes the **values** of `evidence_dating_note`
(`main.py:678`, `:683`): *"This answer's benchmark publishes…"* became *"TerminalBench publishes…"*.
Measured on the shipping artifact, 12 sampled bodies (coding / expert / everyday / computer-use ×
low / medium / unlimited) were hashed before and after. **9 of 12 changed.** Only the three `expert`
bodies, whose picks are dated, are identical.

The field set did not move. The frozen set is pinned by `tests/unit/test_api_v1.py:43`/`:218`
(`set(answer) == ANSWER_KEYS`), and plan §3 freezes field sets, not prose, so the change itself is
permitted. The problem is that the ADR's central argument is stated falsely. The test D-138 names
as the proof, `test_uncertainty_contract.py:208-212`, asserts only that three specific names are
absent. Mutant M6, which adds a new `tie_band` field to every answer, passes it (11 passed). The
wave's own change of values passes it as well.

**Remedy:** Rewrite the claim in D-138 and in the `categories()` docstring as *"the field set is
unchanged; `evidence_dating_note` now names the benchmark"*. Cite the `ANSWER_KEYS` test. Rename
the new test, or make it compare the whole answer key set.

### MAJOR-2: banding on rounded scores departs from the engine's raw decision in the loose direction, and the comment understates it

`ios/ModelRanking/Engine/Uncertainty.swift:55-58` says: *"Near the margin, this and the engine's
raw comparison can disagree by one row."* Measured on the shipping artifact by banding the served
scores against the raw ones:

- **28 rows carry a different label** (expert 16, everyday 12), not one. A single flipped row moves
  the anchor of every band below it, so the whole remainder of the list is re-banded.
- On `expert`, Gemini 3 Flash has a raw score of 89.3939 against the leader's 94.4444, a **raw gap
  of 5.0505**, which is above the 5.0 margin. The served gap is 5.0, so the model is printed
  `=1 of 50`. This is the **loose** direction, and the plan names it as the reason W2 is HIGH.
- As a result the leader-band count in the records is the rounded count. D-138
  (`decisions.md:1634`) and `Uncertainty.swift:4` say *"26 of 50"*. The plan's council-reproduced
  figure is **25** (`m13-plan.md` §7: *"The leader-band counts reproduce exactly (expert
  25/50…)"*). The raw comparison gives 25. The two records now disagree, and the new one inherited
  its number from the rounding.

The repository treats a false comment as a defect (compare M13-W1 MAJOR-3).

**Remedy:** Correct the comment and the two "26" figures. Have the owner decide whether a loose
error of up to 0.1 is acceptable. A conservative comparison on rounded scores
(`gap <= margin - 0.1`) is never loose but is sometimes tight. Either way, state which direction
the product errs in and cite the measurement.

---

### MINOR findings

| # | `file:line` | Finding | Remedy |
|---|---|---|---|
| MINOR-1 | `Uncertainty.swift:199-204`, `ContentView.swift:500-502` | For **any** Medium pick that has a second score and an age, the sentence gives the age as the reason: *"…last ran 17 days ago, so it is not counted"* (confirmed by a probe). For an age of 90 days or less that reason is false. It is reachable because `/v1/categories` is fetched **once per app session** (`if categories.isEmpty`) while answers refresh, and the refresh replaces the artifact (D-129). The cached age can come from an earlier artifact than the verdict | Drop the causal "so", or re-fetch categories on every `load()` |
| MINOR-2 | `decisions.md:1638`, `main.py:1140-1164`, `Uncertainty.swift:206` | A null `secondary_age_days` means two things: the board is undated, **or** the artifact could not be read. The client renders null as *"Aider polyglot … publishes no run dates"*. On the shipping artifact Aider polyglot is dated on 68 of 68 rows. So the sentence makes a false claim about a named third-party board whenever the null came from the unreadable case. A negative age (`UncertaintyTests.swift` "AnAgeThatCannotBeADayCount") produces the same sentence | Use neutral wording (*"its run date could not be checked"*), or distinguish the two cases on the wire |
| MINOR-3 | `Uncertainty.swift:154`, `:171`; `ContentView.swift:621` | For a contradictory payload ("High" with no second score), `evidenceBreadth` returns nil *"so printing 'Measured on 2' would not repeat the contradiction"*. The caller then renders `pick.confidenceBasis`, which is *"two independent benchmarks (…)"*: the same claim. `UncertaintyTests.swift:210` asserts nil at the function, but the screen still prints the claim | In the contradictory case, fall back to the one-benchmark sentence, or to nothing |
| MINOR-4 | `main.py:678` | The named note asserts a property of the **board** (*"TerminalBench publishes no evaluation dates"*), when the evidence is only this artifact's rows. On the shipping artifact the statement is false for TerminalBench, whose `Run date` is read since HEAD (`sources.py:251`). The prd row admits the artifact is stale, but naming the board turned an imprecise sentence into a false claim about a named source | Say what the rows show: *"TerminalBench's scores in this build carry no evaluation dates…"* |
| MINOR-5 | `ContentView.swift:631-632` | The comment *"`#4 of 50` only where the position is real"* is false in 6 places on the shipping artifact: rows printed with `#` that sit within the margin of an adjacent row, e.g. everyday `#3` at 161.0 below 161.5 (margin 0.5), abstract `#4` at 96.5 below 97.5 (margin 1.0), web-dev `#21` | Fix the comment, or fold it into BLOCKING-1's remedy |
| MINOR-6 | `ContentView.swift:169-174`, `Router.swift:620-621`; `categories.py:118-119` | D-135: the leader-band note and the engine's `close_call` disclosure state one fact twice on one screen. On `assistant`: *"Claude Opus 4.6 is only 1.5 Elo behind — within the margin of error"* plus *"The top 2 of 65 are within 8 Elo of the leader — inside this benchmark's margin of error"*. Separately, "margin of error" is a statistical claim, but where a board publishes no stderr the margin is the *median adjacent gap* (`categories.py:118-119`). The engine's existing sentence already says this, and the client now repeats it | Deduplicate in `classifyDisclosures`; queue the "margin of error" wording for K.9 |
| MINOR-7 | `test_uncertainty_contract.py:129-133`; `UncertaintyTests.swift:31`, `:98` | Test quality. (i) `test_an_undated_second_board_publishes_no_age` claims MMLU "publishes no run dates", but the seeded fixture contains **no MMLU rows at all** (only DeepSWE and SWE-bench Verified), so it tests an *absent* board, not an undated one. (ii) Plan §1 row 5 asks for *"a citing test per surface"*. The Swift tests pin 5 of 9 margins as hand-copied literals (none for coding, agentic-coding, abstract, web-dev) and never read the served values. (iii) `testAGapExactlyAtTheMarginIsATie` survives the mutant `<=` → `<`. The mutant is equivalent under the 1e-9 tolerance, so the test pins the tolerance, not the inclusive comparison its name cites | Seed an MMLU row with a null `run_date`; drive the Swift cases from a table of the nine served margins; rename (iii) |
| MINOR-8 | `docs/prd.md:470`; `Uncertainty.swift:193` | The prd criterion for REQ-UNC-002 is not the plan's. Plan §1 row 6 reads *"…and how old the oldest of them is"*. The prd row substitutes the plan's *verification* text (*"a board more than 180 days old carries that age"*), with no amendment. The comment *"Its age still answers 'how old is the oldest'"* is also false: the value is the age of the secondary **board's newest run**, which is neither the pick's own second score nor necessarily the oldest of the pick's benchmarks | Restore the plan's criterion text or record the amendment; correct the comment |
| MINOR-9 | `Uncertainty.swift:118`; `main.py:683` | Rendered grammar. *"The top 3 of 39 are within **1 points** of the leader"* is live on `abstract` (leader band of 3, margin 1.0; confirmed by a probe). *"carry **a** Epoch Capabilities Index / AIME (mock) / ARC-AGI evaluation date"* | Singular unit at 1; rephrase to avoid the article |
| MINOR-10 | `test_rosters.py:225`; `closure-report-m12.md:9` | Drive-bys (profile §2b) inside a HIGH wave's diff. **Both are correct on their merits** (see below). But the M12 banner records that *"M13 had been open over this unsigned milestone since 2026-09-06"*, which bypasses the plan's own prerequisite (*"M13 must not open over an unsigned milestone"*). Under V4C-13 a bypassed control belongs in the wave-checklist ledger, not only in a sentence in another milestone's report. This seat also cannot verify the quoted owner answer; only the owner can, at the milestone commit | Land the two in a separate commit; add a ledger row for the prerequisite bypass |

### NITs

- **NIT-1** `decisions.md:1625`: *"Amends nothing"*. D-138 lifts plan §3's *"no field may be added
  or renamed in `/v1` during M13"* for `/v1/categories`. It should say that it amends plan §3 by
  the owner's decision.
- **NIT-2** `Uncertainty.swift:214-224`: `isoDate("2026-99-99")` returns `"2026-99-99"` (confirmed
  by a probe). It checks the shape, not the calendar.
- **NIT-3** `main.py:1153-1163`: `_secondary_ages` swallows `sqlite3.Error` without a log line. The
  only symptom of an unreadable artifact is null ages, which the client then renders as MINOR-2's
  sentence.
- **NIT-4** `black --check` (the repo's `make format`) would reformat `test_secondary_evidence_age.py`,
  which HEAD had clean (the diff's assert rewrite uses the other formatter's style), and
  `test_uncertainty_contract.py`. `make check` does not gate this.

---

## What the seat checked hardest and found sound

- **The D-138 endpoint.** It opens read-only through `schema.open_readonly` (INV-23, a derived
  URI), closes the handle in `finally`, returns `{}` on `sqlite3.Error` at open and at query time,
  and returns `{}` when the variable is unset or the file is missing. All three are exercised by
  `test_uncertainty_contract.py:137`. It writes nothing. Cost, measured over 200 requests on the
  shipping artifact: **0.556 → 1.218 ms/request**. That is negligible, so no memo is needed. The
  route calls the engine's own `secondary_age_days`; on the shipping artifact it serves coding 328
  and everyday `null` (MMLU is undated on 136 of 136 rows).
- **The key test pins the served margin.** Six mutants were run against
  `test_uncertainty_contract.py` on a private copy:

  | Mutant | Result |
  |---|---|
  | M1: serve `value_window` | caught (`[outside]` + per-surface test) |
  | M2: serve an import-time snapshot of the margins, ignoring the steered spec | caught (`[inside]`) |
  | M3: wall-clock age computed with a copied query | caught (317) |
  | M4: revert to the unnamed dating note | caught |
  | M5: undated age reported as 0 | caught (4 tests) |
  | M6: add a new answer field | **survives** (MAJOR-1). `test_api_v1`'s `ANSWER_KEYS` would catch it |

  The steer is two-sided: a served value that does not follow the patched `close_call` fails one
  side. What the test does **not** show is that the client's banding reproduces the engine's
  decision. It proves that one number is read from one place (BLOCKING-1, MAJOR-2).
- **`evidenceBreadth` never prints a count the engine did not decide.** The count comes only from
  the verdict ("High" gives 2, "Medium" gives 1, anything else returns nil and falls back). "High"
  with no second score returns nil. A benchmark name reaches the sentence only through `label()`,
  and `testABenchmarkNameThatIsASentenceIsNotInterpolated` pins that. Ages outside 0…100 000 are
  dropped. No rendered string anywhere in `ios/ModelRanking` contains `confidence` or `güven`; the
  only match is the `confidenceBasis` CodingKey (`Models.swift:227`).
- **`tieBands` edge cases.** A nil, negative, NaN or infinite margin gives the strict order
  (`UncertaintyTests.swift:42`, `:49`). An empty ranking gives no bands. A non-finite score ends a
  band and stands alone. Greedy anchoring versus chaining is pinned by `:21`. The 1e-9 tolerance
  is what carries the engine's inclusive `<=`, so `<` and `<=` are equivalent in practice (MINOR-7
  iii). Out-of-order input would be absorbed into a band, but the served ranking is in descending
  order on all nine surfaces, and the client never re-sorts (Trap 1).
- **The ContentView wiring.** Bands are computed once per answer (`:150-157`) and passed to the
  picks, the preview (`:238`) and the list (`:252`). The list reads ranks from the **full** ranking,
  never the filtered one (`:756-757`). The pick row, the preview and the list use the same `bands`
  value. The Turkish and English labels come from the same functions. The app compiles.
- **`Category` decoding.** The three fields are optional, and an older engine still decodes
  (`UncertaintyTests.swift` `D138CategoryDecodingTests`).
- **The roster fixture pin is correct.** At HEAD, `_scored_db` stamped `plans.observed_at` with the
  wall clock. On 2026-09-15 the plan's 2026-08-15 `last_verified` passed the 30-day window, so the
  plan-table staleness notice fired and `test_stale_unselected_roster_link_is_not_disclosed` failed.
  With `observed_at` pinned to 2026-08-16 the test **still discriminates**: the unselected roster
  link it sets to 2026-05-01 is 107 days old and would be disclosed if staleness followed every
  candidate. The comment's arithmetic (`observed_at - last_verified`, expired 2026-09-15) matches
  `subscribe.py:328-331`.
- **`.language-allow`.** Both new entries carry a written reason, and both files do contain Turkish
  prose (the composers and the assertions on them). `check_records` passes.

## Acceptance criteria evidence

| REQ-ID | Verdict | Code | Citing test |
|---|---|---|---|
| REQ-UNC-001 | **FAIL** (BLOCKING-1) | `Uncertainty.swift:62` (`tieBands`), `:90` (`rankLabel`), `:109` (`leaderBandSentence`); `ContentView.swift:150-157`, `:631-640`, `:756`; margin served at `main.py:1193` | `UncertaintyTests.swift:60` (a shared rank inside a band), `:111` (band stated once); `test_uncertainty_contract.py:56`, `:82`. No test covers a budget-filtered leader or the engine's close-call pair, and that is the case that fails |
| REQ-UNC-002 | **PASS WITH FINDINGS** (MINOR-1, -2, -3, -8) | `Uncertainty.swift:157-208` (`evidenceBreadth`); `ContentView.swift:613-621`, rendered at `:668`; age served at `main.py:1140-1164`, `:1197`; engine rule `recommend.py:268` | `UncertaintyTests.swift:156` (a second board over 180 days old carries its age, verbatim shipping case), `:218` (no rendering says `confiden`/`güven`, both languages); `test_uncertainty_contract.py:89` (the served age is the engine's, 317) |
| REQ-UNC-003 | **PASS WITH FINDINGS** (MINOR-4) | `main.py:678`, `:683` (the undated / mixed note names the benchmark); rendered through `Router.swift:623-624`; undated second board named at `Uncertainty.swift:206` | `test_uncertainty_contract.py:160` (the live route names DeepSWE), `:174` (mixed branch); `UncertaintyTests.swift:177` |

## K.8 contract drift check

```
$ grep -n "PUBLIC_ANSWER_FIELDS = \|PUBLIC_PICK_FIELDS = \|PUBLIC_RANKING_FIELDS = " src/app/adapter/main.py
  (unchanged by the diff; no hunk touches them)
$ grep -n "ANSWER_KEYS = \|set(answer) == ANSWER_KEYS" tests/unit/test_api_v1.py
43:ANSWER_KEYS = {
218:        assert set(answer) == ANSWER_KEYS, f"answer key set changed: {set(answer) ^ ANSWER_KEYS}"
```

The answer, pick and ranking field sets are **OK**. Values moved (MAJOR-1). `/v1/categories`
widened under D-138, which is recorded as the owner's decision.

## K.9 candidates outside this wave's scope

- **The first half of W2 rode in the W1 commit** (`3440abe`: terminalbench's `Run date`, and ruling
  A3 in `confidence_of`). The W1 review record does not mention either change. REQ-UNC-002 and
  REQ-UNC-003 rest on them, and they are outside this frozen diff, so no independent seat has
  reviewed them as W2 work. This seat read `confidence_of` (`recommend.py:244-274`) and found it
  consistent with A3. It did not review the ingest change.
- The "margin of error" wording in the engine's `close_call` sentence, for surfaces whose margin
  is a median adjacent gap rather than twice a stderr (`categories.py:118-119`).
- `evidence_dating` is decided from the picks alone. AIME (mock) and GPQA Diamond each carry one
  undated row on the shipping artifact, and nothing names such a row unless it is a pick.

## Risks queued to next M

- If REQ-UNC-001 is kept literal, it probably needs per-row band membership from the engine. That
  is a payload move, which D-138's "Revisit when" already anticipates.
- Categories are cached for the whole app session, so any per-artifact fact published on
  discovery will go stale in the client while answers stay fresh.
