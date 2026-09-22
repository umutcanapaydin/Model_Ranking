---
record_type: review
id: m15-wave-2-review
status: ratified
seat: independent
date: 2026-09-21
---

# M15 Wave 2 Code Review — the detail screen

**Reviewer:** independent Code-Reviewer seat (D-133). Did not author any of this wave.
**Tree:** `/tmp/claude-0/w2-review`, working tree on `fc7fe5b` (M14-W3/W4) with the M14 closure wave and M15-W2 uncommitted.
**Risk tier:** MED (`docs/plans/m15-plan.md` §2 W2).
**Verdict:** **BLOCKING.**

---

## 1. How this review was produced

**Read, from the tree, before the code:** `subagent-profiles/Code-Reviewer.md`; `AGENTS.md` §3 (incl. §3.3 V3C-02) and §5 (incl. V4C-49/50); `docs/plans/m15-plan.md` §0 ruling 1, §2 W2, §3 K.8, §4; `docs/decisions.md` D-104, D-105, D-136, D-138, D-140, D-143, D-146; `docs/warnings.ledger.md` W-084/W-085/W-091/W-099/W-105; `docs/reviews/m14-closure-review.md`; `docs/prd.md` §M13/§M14/§M15; `docs/coverage-by-req.md`.

**Read as the change:** `ios/ModelRanking/Engine/Detail.swift` (new, 187 lines), `Models.swift` tail, `Language.swift` `UIText.detailTitle`/`detailCaveat`, `ContentView.swift` (`struct ModelDetail` at :849 and the two doors at :776 and :924), `ios/EngineTests/DetailTests.swift` (new), `tests/unit/test_ios_client_contract.py::test_the_detail_screen_is_reachable_and_composes_nothing_itself` (:817), `.language-allow`, `docs/prd.md` §M15, `docs/warnings.ledger.md` W-105.

**Ran:**

| Gate | Result |
|---|---|
| `python -m ruff check src tests` | `All checks passed!` (exit 0) |
| `python -m pytest -q` | `919 passed, 13 skipped in 25.30s`; coverage 88.72% ≥ 85.0 floor |
| `python3 scripts/check_records.py` | `check_records PASS [repo]: no findings` (110 records) |
| `python3 scripts/wave_check_all.py` | `wave-check-all PASS: 35 v5.0 record(s) validated` |
| `python3 scripts/conformance_gate.py` | `conformance-gate PASS: 7 finding(s), all exempted and all still firing` |

**Every gate in this repository is green on this tree.** 37 mutants were then written and run against `Detail.swift`, `ContentView.swift`, `Language.swift` and the new tests; 26 survived every gate. Each was reverted; the tree is byte-identical to the one I received (`git diff --stat` → 22 files, 520 insertions, unchanged).

**What I could not do.** There is no Swift toolchain on this machine (`which swift` → nothing) and **no CI workflow runs Swift at all** (`grep -rn swift .github/workflows/` → no matches). `make swift-test` prints `swift-test SKIPPED NO-ENVIRONMENT` here. I therefore make **no claim that any Swift file compiles or fails to compile**. Where I say a mutant "would die under `swift test`", that is inferred by reading `DetailTests.swift` line by line, is labelled as inference in the table, and was not executed. Structural reasoning about Swift was done by reading and by regex, not by a compiler.

---

## 2. Findings

### BLOCKING

**B-1 — The D-126 egress ban does not cover `Detail.swift`, and the plan made that a named W2 deliverable.**
`tests/unit/test_router_hints.py:237` and `:242` — the ban enumerates two files by path: `ContentView.swift` and `FrontDoor.swift`. `Detail.swift` is a new Engine file that renders to the reader and is covered by neither.

`docs/plans/m15-plan.md` §2 W2, verbatim: *"`ContentView.swift` grows again, and it is the file with the least proof in the project — so this wave extends the source-contract tests as it goes rather than after, and **the D-126 egress ban (W-099) covers every new file by name**."* It does not. `AGENTS.md` §5 (V4C-49/50) states the same rule generically: *"When you create a NEW standalone artifact … replay the recent rules against it; a lesson attaches to an artifact, not to you."* W-099 was closed **2026-09-21**, the day this wave was written.

Mutant **M1** — two lines added to `detailFacts`:
```swift
var facts: [DetailFact] = []
URLSession.shared.dataTask(with: URL(string: "https://x.example/\(model.model)")!).resume()
```
**SURVIVED** all five gates (`38 passed`). The control mutant **M2**, the same egress inside `ContentView.ModelDetail`, **DIED**: `AssertionError: the screen opens its own network door ('URLSession')` at `test_router_hints.py:238`.

Concrete failure: a future change to the detail screen's composer can open a network connection carrying the model name, the surface, or anything else in scope, and nothing in this repository fails. No egress exists today — this is a hole in the proof, not in the product, which is *exactly* what W-099 said about its own predecessor. **Fourth occurrence of one shape** (M13 security MAJOR-2 / W-090; M13 Stage 4.0 MINOR-4; W-099; this).

Remedy: extend the ban to every `ios/ModelRanking/**/*.swift` with `EngineClient.swift` named as the one exemption with its ADR — the `SCORE_ARITHMETIC_PERMITTED` shape already in `test_ios_client_contract.py:169`, which is the pattern that made B-1's sibling tripwire work (see *What held*).

---

**B-2 — `SWIFT_TEST_FLOOR` was raised by 1 for 11 new Swift tests, so the whole of `DetailFactTests` is deletable with `make check` green. This is W-091 verbatim, twelve days after the owner ruled on it.**

`Makefile:137` — `SWIFT_TEST_FLOOR := 242`, raised from `241`. Measured:

```
HEAD  (git show HEAD:ios/EngineTests/*)  func test count = 241
tree  (grep -cE '^\s*func test')          func test count = 252
of which DetailTests.swift                             = 10
FrontDoorTests.swift (M14 closure, +1)                 = +1
```

With `DetailTests.swift` deleted the suite reports 242 and the gate's own test is `[ "$n" -lt 242 ]` → false → **`swift-test PASS`**. Mutant **M20** (delete `ios/EngineTests/DetailTests.swift` entirely) **SURVIVED** pytest, and by the arithmetic above survives `make swift-test` on the owner's machine too.

This matters because `docs/prd.md:516` and `:517` cite `DetailTests.swift::DetailFactTests` as the citing test for **both** REQ-DTL-001 and REQ-DTL-002 — and it is the only test in the wave that asserts what the screen *says*, as opposed to that the wiring exists. `AGENTS.md` §3.3 V3C-02: *"A criterion without a citing test is BLOCKING at the Quality Gate."* Here the citing test exists, runs in no lane reachable from this repository or CI, and is deletable in the one lane that does run it.

`docs/warnings.ledger.md` W-091 is this defect, already found and already ruled: *"**The Swift test floor is 121 and the suite runs 215** … The recipe's own comment says to raise the floor when tests are added. **Not raised by the agent:** the floor decides what the gate accepts, so changing it is a gate-definition change and the owner's … **RESOLVED 2026-09-20 — owner ruled RAISE.**"* This wave both (a) moved a gate definition agent-side, which W-091 and W-026 put on the owner's surface, and (b) moved it to the wrong number. `docs/plans/m15-plan.md` §4 requires *"`SWIFT_TEST_FLOOR` at the count it prints"* — 252, not 242.

Remedy: the floor is the owner's line. Escalate with the measured number (252) and a ledger row; do not have an agent set it.

---

### MAJOR

**M-1 — `Detail.swift:96–97` states a publication date the engine never published, bypasses the project's own date validator, and says something different in each language.**

```swift
note: model.evidenceDate.map {
    language == .turkish ? "\($0) tarihli sonuç" : "result published \($0)"
} ?? (language == .turkish ? "bu liste sonuçlarını tarihlendirmiyor"
                          : "this board does not date its results")
```

Three separate problems on two lines:

1. **"published" is a claim `/v1` does not make.** The same served field, on the card, is worded by `Uncertainty.swift:273` as `" (run \(date))"` — the date the board was *run*. Nothing in `evidence_date`'s path (`src/app/workflows/coverage.py:86`, `board_measurement.py:124`) says anything was published on that day. The reader moves between a card saying "run 2026-09-13" and a detail screen saying "result published 2026-09-13": two accounts of one field, and the detail screen's is the stronger one.
2. **The English and the Turkish make different claims.** Turkish reads *"2026-09-13-dated result"*; English reads *"result published 2026-09-13"*. Two readers comparing notes get different facts from the same line.
3. **`isoDate` is bypassed.** `Uncertainty.swift:312–331` exists to refuse a date string this build cannot parse, and the card calls it. `Detail.swift:96` interpolates `$0` raw. An `evidenceDate` of `"unknown"` or `"2026-13-45"` prints as **"result published unknown"**, *and* takes the `.map` branch — so the screen makes up a publication date instead of falling through to the REQ-UNC-003 undated notice. That is the `number(_:)` lesson stated at `Language.swift:228–232` ("This returned `""` until M12-W5, and the composers interpolated it into the sentence anyway") applied to dates and not applied here.

`DetailTests.swift:88–96` tests only `evidenceDate = nil`. A malformed date is never exercised, so the criterion's citing test cannot fail on the case that breaks it. Mutant **M25** (undated board → `"measured recently"`) SURVIVED pytest; it would die under `swift test`, which does not run here.

---

**M-2 — Every note on the detail screen can be hard-coded to English and `testEveryLineIsTranslated` stays green. The test whose docstring names W-085 never reads a single `note`.**

`DetailTests.swift:136–154`. Its only per-line assertion is:
```swift
for fact in lines {
    XCTAssertFalse(fact.label.isEmpty, "a Turkish detail line has no label")
}
```
— a non-emptiness check on the label. It then names two values (`"Puan"`, `"Ölçülen değer"`), the caveat (which lives in `Language.swift`, not `Detail.swift`), and asserts four English labels are absent. **`.note` appears nowhere in the function** (verified: `sed -n '136,154p' … | grep note` → no match). Notes are 7 of the 15 language-switched strings in `Detail.swift`.

Mutant **M37** — all seven `language == .turkish` ternaries in the *notes* collapsed to their English arms (verified: 7 of 7 applied, 8 label ternaries left untouched): **SURVIVED** pytest, and by inspection survives `testEveryLineIsTranslated` too. The Turkish reader gets Turkish labels over English sentences — the half-translated screen W-085 caught, inside the test written to catch it.

Mutant **M28c** — the three labels *neither* pytest *nor* `DetailTests.swift` names (`Çalıştırma`, `İkinci kanıt`, `Giriş / çıkış`) hard-coded to English: **SURVIVED**. The English denylist at `DetailTests.swift:151` is `["Score", "Price", "Measured on", "Too close to call"]` — an enumeration, which this project's own `test_ios_client_contract.py:16` calls *"a denylist wearing better clothes"*. The honest form is to iterate the facts and assert no Turkish line contains a string equal to its English arm.

---

**M-3 — `Detail.swift:147` ships an untranslated English line on the Turkish screen.**

```swift
value: "$\(input) / $\(output) per 1M",
```
`per 1M` is prose and is not language-switched. A Turkish reader sees `Giriş / çıkış: $5 / $25 per 1M`. This is not the documented `priceTag` exemption: `Scores.swift:76–85` deliberately never localises the *currency format* (`$7.5/1M`), and says why. `per 1M` is a preposition and a unit word, the kind `localisedUnit` exists for. `grep -rn "per 1M" ios/` returns this line and nothing else — it is the only free-prose "per" in the client.

---

**M-4 — The plan's W2 deliverable "the surface's floor" is absent from the screen, from `docs/prd.md` §M15, and from every record; no ADR records the drop.**

`docs/plans/m15-plan.md` §2 W2 lists what the screen holds: *"the model, its score out of 100, its unit and what the unit is, the benchmark's name and date, the price in the form a reader can check, **and the surface's floor**."* `detailFacts` composes eight lines and none of them is the floor.

The floor (`min_quality`) is also **not served**: the Swift `Category` decodes `id, title, primary_benchmark, metric, ranking_effort, close_call_margin, secondary_benchmark, secondary_age_days, score_anchor` (`Models.swift:41–69`) and `/v1/categories` emits no `min_quality` (`src/app/adapter/main.py:1239–1255`). Plan §3 K.8 is explicit about this case: *"The detail screen is a READER of facts the engine already publishes. **If it needs a fact `/v1` does not carry, that is an ADR, not a quiet addition.**"* Neither an ADR nor a recorded drop exists. `docs/prd.md:516` writes REQ-DTL-001 without the floor clause, so the criterion was quietly narrowed to what was built — the shape W-104 was raised for one milestone ago.

---

**M-5 — The detail screen can disagree with the card that opened it, and the wave's own new test pins argument *names* only.**

`tests/unit/test_ios_client_contract.py:851`:
```python
for argument in ("benchmark:", "anchor:", "closeCallMargin:", "secondaryBenchmark:"):
    assert argument in detail.group(1), (
        f"the {opened} opens a detail screen without `{argument}` — it would then state a "
        "different fact from the card that opened it")
```
The message states the invariant correctly. The assertion checks only that the label is present, never that the value is the same surface's fact. Four mutants:

- **M10** — `anchor: nil` at the row's door (`ContentView.swift:930`): the row reads `Score 65 / 100`, the detail screen reads `Score 1507.6 Elo`. **SURVIVED.** That is precisely the defect D-143 and `Detail.swift:56–58` claim this design prevents ("Same call as the card's, so the two screens cannot disagree about a score"), and it is W-084's shape.
- **M11** — `anchor:` and `closeCallMargin:` swapped, names intact. **SURVIVED.** The out-of-100 conversion then runs against 8, and the tie margin is reported as 1400 Elo.
- **M12** — `benchmark: ""` at the row's door. **SURVIVED.**
- **M33** — `secondaryAgeDays: Int(closeCallMargin ?? 0)`: the tie margin printed as "last run N days ago". **SURVIVED** (`secondaryAgeDays:` is not even in the pinned list).

The stronger form the repository already uses is two files away: `test_every_score_on_screen_goes_through_the_figures_line:783–789` pins `figuresLine(score: pick.score, metric: pick.metric, …, anchor: anchor)` as a whole expression. The same regex shape applied to `ModelDetail(` kills all four.

---

**M-6 — `PickRow.benchmark` defaults to `""`, and `detailFacts` renders an empty board name rather than omitting the line.**

`ContentView.swift:706` — `var benchmark: String = ""`, while the consumer `ModelDetail.benchmark` (`:850`) is a required `let`. `Detail.swift:92–102` appends the "Measured on" line unconditionally with `value: benchmark` and no guard.

Mutant **M9** — drop `benchmark: answer.primaryBenchmark` from the single `PickRow(` site (`ContentView.swift:159`): **SURVIVED** every gate. Every pick's detail screen then reads `Measured on:` with an empty value and `on , on that board's own scale`.

This contradicts the file's own stated rule, `Detail.swift:15–17`: *"A fact this build cannot state HONESTLY is left out rather than rendered empty … a row reading 'Measured: —' tells a reader the measurement is missing, which is a claim, and usually a false one."* Per `AGENTS.md` §5 V4C-49 — *"when you write a rule that bans a specific literal or shape, ship the grep gate in the same change"* — the rule shipped and the gate did not. Remove the default; guard the append on a non-empty `benchmark`.

---

**M-7 — The Price line renders `—` for a missing price, which `Detail.swift:15–17` declares forbidden, and the test that asserts the invariant never exercises it.**

`Detail.swift:136–142` appends unconditionally with `value: priceTag(model.blendedPerM)`, and `Scores.swift:77` returns `"—"` for any price that is zero, negative or non-finite. So a model whose price the engine could not resolve gets a detail line reading **`Price —`** with the note `price unavailable` (`Router.swift:685`).

`DetailTests.swift:132` asserts exactly the right invariant —
```swift
XCTAssertFalse(facts(subject).contains { $0.value.isEmpty || $0.value == "—" })
```
— but only against `Subject()`, whose `blendedPerM = 7.5`. The one input that breaks the invariant is never passed. This is the pattern the brief names: a criterion whose citing test cannot fail.

---

**M-8 — The new "composes nothing itself" ban is scoped to a text slice and is evaded by moving the helper below the last `struct`; and it does not stop the view adding facts or claims.**

`tests/unit/test_ios_client_contract.py:858–862`:
```python
body = view[view.index("struct ModelDetail: View") :]
body = body[: body.index("\nstruct ")]
for composed in ("String(format:", "NumberFormatter", "/ 100", "%.1f"):
    assert composed not in body
```

- **M22c** — `Text(detailShare(fact))` added under `Text(fact.value)`, with `func detailShare(_ f: DetailFact) -> String { String(format: "%.1f%% of the leader", (Double(f.value) ?? 0) / 100) }` **appended at the end of the file**: **SURVIVED.** The screen then prints a percentage the client computed, which is Trap 1 and D-104/D-105 at once. (The same helper placed *above* `struct RankingList` dies — **M22** — so the tripwire is position-sensitive, not behaviour-sensitive.)
- **M21** — `detailFacts(...) + [DetailFact(label: "Verdict", value: "Best value overall")]`: **SURVIVED.** `re.search(r"detailFacts\(\s*model:", view)` is satisfied by the call still being there.
- **M13** — `Text("Independently verified by our own testing")` added inside the `ForEach`: **SURVIVED.**
- **M29** — `Text("Scores are comparable across surfaces.")` added beside the D-105 caveat, directly contradicting it: **SURVIVED.**

So the ban proves that four literals are absent from one slice; it does not prove the view renders only what the Engine sent, which is what its docstring claims (*"the view renders the Engine's facts rather than writing lines of its own (D-104)"*).

---

### MINOR

**N-1 — `Detail.swift:78` labels a *score* with the *margin's* unit function.** `marginUnit`'s own doc, `Uncertainty.swift:143–148`, says: *"The unit a MARGIN is counted in, **which is not always the unit a score is printed in**. A percentage board's margin is a distance in points: `5 % correct` reads as a score, not as a gap."* For `% resolved` / `% correct` it returns `points` / `puan`. That path is unreachable today (see *What held*, family trace), so nothing is wrong on screen — but the moment a bounded family acquires a conversion, the "Measured value" line reads `83.5 points` for a `% resolved` board. Mutant **M35** (unit forced to `"points"`) SURVIVED pytest. A score's unit is `localisedUnit(metric, in:)`, which is what `scoreText`'s `.unknown` branch uses.

**N-2 — `Detail.swift:106–116` drops the harness entirely when `effort` is nil,** and prints raw English engine tokens (`arena-crowd · high`) on the Turkish screen. The harness is a served fact; when the engine sends a harness and no effort, the reader is shown neither.

**N-3 — `language:` and `secondaryAgeDays:` are not pinned at either door.** `ModelDetail.language` defaults to `.english` (`ContentView.swift:852`). Mutants **M30**/**M31** (drop `language:` from the pick's / the row's `ModelDetail(`) SURVIVED: a Turkish reader gets an English detail screen. **M32** (`secondaryAgeDays: nil`) SURVIVED: the second board loses the age D-139 requires. The default is the project's convention for these views (`PickRow` :695, `RankedRow` :815, `RankingList` :905 all do it), so this is consistency rather than novelty — but the test's own message says a missing argument means the screen "would state a different fact from the card", and these two are the ones it left out.

**N-4 — `.language-allow`'s header note is now false, and this wave widened it without correcting it.** The note reads: *"`.swift` is now scanned, and **these four files** are exempt BY NAME … the client is ~30 Swift files and four of them hold Turkish. **The other twenty-six are now guarded for the first time.**"* The list holds eleven `ios/` entries after this wave's two. Drift predates W2 (nine entries before), but W2 added to it and left the count standing. The two new entries are themselves reasoned and follow the `Uncertainty.swift` / `FrontDoor.swift` precedent exactly, so the *exemptions* are honest; the *note above them* is a record stating the opposite of the code, which is the failure mode this project names most often.

**N-5 — There is no `docs/plans/m15-wave-2-close.md`.** Every prior wave in `docs/plans/` has one (60+ files, m1 through m14-wave-5). `wave_check_all.py` validates records that exist and does not require one, so the gate cannot see the absence. Without it there is no committed checklist pinned to this closing tree, which `AGENTS.md` §3 (operating mode A0.5) makes a condition of an agent-side wave close.

**N-6 — `docs/decisions.md` D-146 body edited in place (`**Decision (proposed).**` → `**Decision.**`) — not chargeable to W2.** Recorded so it is not: `docs/reviews/m14-closure-review.md:456` claims it as the M14 closure seat's MINOR fix. It aligns the body with an already-accepted header rather than reversing anything, so B.2 is not engaged.

### NIT

- `test_ios_client_contract.py:842` — `assert set(doors) == {"pick", "row"}` makes a legitimate *third* entry point into the detail screen a test failure. `>=` is the invariant that is meant.
- `_swift_sources()` (`:31`) keys by `p.name`, so two Swift files sharing a basename anywhere under `ios/ModelRanking` silently shadow each other and one is never scanned by the arithmetic or disclosure tripwires.
- `Detail.swift`'s Turkish could live in `Language.swift`, which is already exempt, instead of widening `.language-allow` by one product file. The wave's choice follows the `Uncertainty.swift`/`FrontDoor.swift`/`Router.swift` precedent, so this is a preference, not a defect.

---

## 3. Mutants run

"swift test?" is **inferred by reading `DetailTests.swift`**, not executed — there is no Swift toolchain here and no CI job runs one. "n/a" means the file is not in the Engine target (`ContentView.swift` is not compiled by `ios/Package.swift`).

| # | Mutant | pytest + gates | swift test? (inferred) |
|---|---|---|---|
| M1 | `URLSession` + `URL(string:)` egress added to `Detail.swift::detailFacts` | **SURVIVED** | survives (Engine compiles, nothing asserts it) |
| M2 | control: same egress in `ContentView.ModelDetail` | DIED (`test_router_hints.py:238`) | n/a |
| M3 | `model.score * 1.05` in `Detail.swift` (D-138) | DIED (`test_ios_client_contract.py:196`) | survives |
| M4 | laundered: `let raw = model.score; raw / 20.0` in `Detail.swift` | **SURVIVED** | survives — known PARTIAL, `:181` |
| M5 | board name removed from the Measured-value note | **SURVIVED** | dies (`DetailTests:57`) |
| M6 | detail `Score` drops the anchor → disagrees with the card | **SURVIVED** | dies (`DetailTests:55`) |
| M7 | D-105 caveat `Section` deleted from `ModelDetail` | DIED (`:864`) | n/a |
| M8 | `detailCaveat` gutted to `"Detail"`, call site intact | **SURVIVED** | dies (`DetailTests:150`) |
| M9 | `PickRow(` built without `benchmark:` → empty board name | **SURVIVED** | n/a |
| M10 | row's detail opened with `anchor: nil` | **SURVIVED** | n/a |
| M11 | row's detail: `anchor:` / `closeCallMargin:` swapped | **SURVIVED** | n/a |
| M12 | row's detail opened with `benchmark: ""` | **SURVIVED** | n/a |
| M13 | `Text("Independently verified by our own testing")` in `ModelDetail` | **SURVIVED** | n/a |
| M14 | ranking rows stop opening the detail screen | DIED (`:842`) | n/a |
| M15 | picks stop opening the detail screen | DIED (`:842`) | n/a |
| M16 | `ModelDetail` stops calling `detailFacts` | DIED (`:836`) | n/a |
| M17 | whole `Measured value` block deleted (REQ-DTL-002's only line) | **SURVIVED** | dies (`DetailTests:56`) |
| M18 | tie-margin block deleted (REQ-DTL-001's margin clause) | **SURVIVED** | dies (`DetailTests:110`) |
| M19 | `Input / output` per-million line deleted | **SURVIVED** | dies (`DetailTests:104`) |
| M20 | `ios/EngineTests/DetailTests.swift` deleted entirely | **SURVIVED** | **survives** — 242 tests vs floor 242 |
| M21 | `ModelDetail` appends a hand-built `Verdict: Best value overall` | **SURVIVED** | n/a |
| M22 | `String(format:` helper placed *above* `struct RankingList` | DIED (`:862`) | n/a |
| M22b | helper at EOF, replacing `Text(fact.value)` | DIED (`:863`) | n/a |
| M22c | helper at EOF, **adding** a computed `% of the leader` line | **SURVIVED** | n/a |
| M23 | caveat rendered `.english` regardless of the reader | **SURVIVED** | n/a |
| M24 | `Run at` invents `"high"` when the engine sent no effort | **SURVIVED** | dies (`DetailTests:127`) |
| M25 | undated board reported as `"measured recently"` | **SURVIVED** | dies (`DetailTests:94`) |
| M26 | price's pages form removed | **SURVIVED** | dies (`DetailTests:105`) |
| M27 | Turkish Measured-value **note** replaced by its English arm | **SURVIVED** | **survives** — no note is asserted |
| M28 | four detail labels hard-coded to English | **SURVIVED** | dies (`DetailTests:149,151`) |
| M28b | the four labels the English denylist omits | **SURVIVED** | partially dies (`:149`) |
| M28c | the three labels **neither** suite names | **SURVIVED** | **survives** |
| M29 | `"Scores are comparable across surfaces."` beside the caveat | **SURVIVED** | n/a |
| M30 | pick's `ModelDetail` built without `language:` | **SURVIVED** | n/a |
| M31 | row's `ModelDetail` built without `language:` | **SURVIVED** | n/a |
| M32 | both doors pass `secondaryAgeDays: nil` | **SURVIVED** | n/a |
| M33 | tie margin reported as the second board's age in days | **SURVIVED** | n/a |
| M34 | `Score` line's "what this means" note dropped | **SURVIVED** | **survives** — no test asserts it |
| M35 | native value labelled `points` on every board | **SURVIVED** | dies (`DetailTests:56`) |
| M36 | Measured value gains an invented `(top 1%)` | **SURVIVED** | dies (`DetailTests:56`) |
| M37 | **all seven** Turkish notes hard-coded to English | **SURVIVED** | **survives** |

**26 of 37 survived every gate that runs.** Six more (M5, M6, M8, M17, M18, M19 …) die only under `swift test`, which runs on one machine and, per B-2, is satisfied with `DetailTests.swift` deleted. Four (M27, M28c, M34, M37) survive both suites.

---

## 4. What held

Stated with evidence, because a review that only lists failures is not a measurement.

**The "does not repeat what the card shows" logic is correct for every metric family.** I traced `Detail.swift:74–77` against `Scores.swift:29–66` by hand for all five cases; the brief asked specifically about this and I found no defect:

| Family | Card shows | `cardConverted` | `rankOnly` | Measured value line | Correct? |
|---|---|---|---|---|---|
| `% resolved` / `% correct` | `Score 83.5 / 100` | false (anchor ignored for `.bounded`) | false | absent | yes — native *is* the card's number |
| `elo` **with** anchor | `Score 65 / 100` | true | false | `1507.6 Elo` | yes — this is REQ-DTL-002 |
| `elo` **without** anchor | `Score 1507.6 Elo` | false (both calls identical) | false | absent | yes — the unit is already on the card |
| `eci` | nothing (`scoreText` → nil) | false | **true** | `161.7 ECI` | yes — the only place the number exists (D-140) |
| unknown metric | `161.7 <engine label>` | false (`.unknown` ignores anchor) | false | absent | yes — the engine's own label is already shown |

Edge case, also correct: a `.bounded` score above 100 yields no `Score` line *and* no `Measured value` line — `scoreText` refuses it (`Scores.swift:50`) and both branches are false. That is a refusal, not a silent empty, and it is the right call. It is untested.

**The D-138 tripwire does reach `Detail.swift`, and I verified it rather than assuming.** `_swift_sources()` at `test_ios_client_contract.py:31` is `CLIENT.rglob("*.swift")` over `ios/ModelRanking`, so every Engine file is scanned. Mutant M3 died with `arithmetic on a served score outside the files an ADR permits`. `SCORE_ARITHMETIC_PERMITTED` (`:169`) still names only `Uncertainty.swift`, the staleness half (`:199–203`) still fires, and `Detail.swift` does no arithmetic — the two conversions genuinely route through `Uncertainty.swift` as the file header (`Detail.swift:9–13`) claims. The laundering gap (M4) is pre-existing and the test's own docstring concedes it at `:180–182`; the prd row for REQ-APP-005 says PARTIAL. **This is the pattern B-1 should copy.**

**Both doors are pinned, and the prd's cited mutant really is red.** `docs/prd.md:516` claims REQ-DTL-001 is *"shown RED on a mutant that stops the ranking rows opening it"*. Reproduced: M14 dies with `the detail screen is opened from ['pick']; it must be reachable from a pick AND from a ranking row`. M15 (the mirror) dies too. The record's claim is true.

**`detailFacts` must be *called*, not merely defined** (M16 died) — the `test_the_disclosure_view_is_actually_reached_from_the_rendered_screen` lesson at `:92–119` was applied to the new screen rather than re-learned.

**The D-105 caveat is present, pinned (M7 died), and substantively right.** `Language.swift:368–373` — *"Each surface is measured on its own board. Two surfaces' scores do not compare."* D-143's own text confirms it does not amend D-105, and its cost paragraph names exactly this confusion. Putting the sentence on the screen where a reader arrives comparing something is the correct place for it.

**The conformances are declared where the payload lives** (`Models.swift:53–60`) with a stated reason, and `DetailTests.swift:158–161` pins that `Pick` and `RankedModel` really do satisfy `DetailSubject` rather than copying their fields.

**The wave extended the contract tests as it went**, as plan §2 W2 asked, and the new test kills six mutants I threw at it. Its blind spots (M-5, M-8) are real, but it is not a test that cannot fail.

**No drive-by edits inside the wave's own files**, and `ruff`, `pytest`, `check_records`, `wave_check_all` and `conformance_gate` are all green on the tree as delivered.

---

## 5. Producers of the hardened invariants (V3C-101)

- **D-138 (score arithmetic):** producers — `Uncertainty.swift::scoreOutOf100`, `rankRanges`, `leaderSentence`. Citing test per producer: `test_score_arithmetic_happens_only_where_an_adr_permits_it` (`:172`) + `UncertaintyTests.swift`. `Detail.swift` is a *consumer* only; verified by M3/M4. Gap: laundering through a binding not named `score`/`scores` (M4) — pre-existing, PARTIAL in prd, tracked.
- **D-126 / W-099 (egress):** producers — `EngineClient.swift` (the one sanctioned door, arguments pinned by `test_the_client_sends_only_the_surface_and_budget`). Citing test: `test_the_gap_register_stays_on_the_device` (`test_router_hints.py:207`). **Gap: `Detail.swift`, and every future Engine file — B-1.**
- **D-104/D-140 (the client composes no number):** producers — `Scores.swift::figuresLine`/`scoreText`, `Detail.swift::detailFacts`. Citing tests: `test_every_score_on_screen_goes_through_the_figures_line` (`:763`), `test_the_detail_screen_is_reachable_and_composes_nothing_itself` (`:817`). **Gap: the detail screen's half is slice-scoped and additive changes pass — M-8.**
- **REQ-DTL-001/002:** producer — `Detail.swift::detailFacts`. Citing tests: `DetailTests.swift::DetailFactTests` (content) + the contract test (wiring). **Gap: the content half executes in no lane reachable from this repository and is deletable under the floor — B-2.**

## 6. K.9 candidates outside this wave's scope

- The `.language-allow` header note's file count (N-4) has been wrong since M13; correct it wherever the next wave touches that file.
- `_swift_sources()` keying by basename (NIT) affects every tripwire in `test_ios_client_contract.py`, not just this wave's.
- `docs/coverage-by-req.md` carries no REQ-DTL row; that is M14's trace and belongs to the M15 quality gate, noted so it is not forgotten.

## 7. Risks queued to next M

- The Swift half of this client is guarded by a single integer in a Makefile that runs on one machine. B-2 is the third time that integer has been wrong (W-091, the M14 closure's `241`-vs-`242` note in `docs/coverage-by-req.md`, and this). A floor derived from `grep -c 'func test'` at check time, rather than typed, would end the class.
- `ios/EngineTests` runs nowhere in CI. Every honesty invariant on the detail screen's *words* rests on that fact, and W-108 already escalates two other gates that only reproduce on the owner's machine.

---

## VERDICT

**BLOCKING** — the wave ships the screen W-105 demanded and the Engine composer is sound, but the D-126 egress ban the plan required it to extend does not cover the new file (B-1, mutant M1 survives), and `SWIFT_TEST_FLOOR` was raised by one for eleven new tests, so the only citing test that asserts what the screen *says* can be deleted with `make check` green (B-2, W-091 recurring); eight further MAJOR findings, including a published date the engine never published and seven Turkish notes no test reads, survive every gate.

---

## Disposition (author, 2026-09-21, after the seat)

| # | Finding | Disposition |
|---|---|---|
| B-1 | The D-126 egress ban names two files, so it does not reach `Detail.swift` | **FIXED** (W-110). The ban is now on every file under `ios/ModelRanking`, with `EngineClient.swift` named as the one exemption and a staleness assertion, the `SCORE_ARITHMETIC_PERMITTED` shape the seat pointed at. The seat's M1 mutant was re-run: **red**, green when reverted |
| B-2 | `SWIFT_TEST_FLOOR` raised by 1 for 11 new tests, so `DetailTests.swift` is deletable | **ESCALATED to the owner** (W-111). The seat is right that the number is wrong and right that an agent should not be setting it: the floor is the owner's line (W-091, W-026). It is left at 242 rather than guessed at — `grep -c 'func test'` counts 257 in this tree while his last run printed 242 from 241 declarations, so the two counts do not agree and only his run is authoritative. He sets it to the printed number after the next runner pass, and W-111 carries the proposal to derive it instead of typing it |
| M-1 | "result published" for a field the engine sends as a RUN date; unvalidated; different claim per language | **FIXED.** `isoDate` is applied, the wording is "run on <date>" in both languages, and a malformed date falls through to the undated notice. `testTheDateIsTheRunDateAndNothingStronger`, `testAnUnreadableDateIsNotPrintedAsADate` |
| M-2 | Every note could be English and the translation test stayed green | **FIXED.** `testNoLineSurvivesInEnglishOnTheTurkishScreen` composes the same subject in both languages and asserts every label AND every note differs, plus equal line counts. The seat's M37 (all seven notes in English) and M28c (the three unnamed labels) both die on it |
| M-3 | `per 1M` was untranslated prose on the Turkish screen | **FIXED** — `· 1M jeton`, asserted in the same test. `priceTag`'s `$7.5/1M` stays as it is: a currency format, with its own recorded reason |
| M-4 | The plan's "and the surface's floor" was dropped with no record | **ESCALATED** (W-112). The floor is not on `/v1` at all, and plan §3 says a fact `/v1` does not carry is an ADR rather than a quiet addition. The plan line is amended to record the drop; whether to publish `min_quality` is the owner's, queued with the M15-W3 surfaces |
| M-5 | Both doors pinned by argument NAME, so a swapped or defaulted value passed | **FIXED.** Each door's whole argument list is pinned as one expression, plus a count assertion so a third door cannot appear unpinned. The seat's M10, M11, M12, M33, M30, M31, M32 all die |
| M-6 | `PickRow.benchmark` defaulted to `""` and the line rendered empty | **FIXED.** The composer guards on a non-empty board name, and the contract test pins `benchmark: answer.primaryBenchmark` at the `PickRow` call. `testAnEmptyBoardNameProducesNoMeasuredLine` |
| M-7 | A model with no resolved price rendered `Price —` | **FIXED.** No price, no line. `testAModelWithNoResolvedPriceGetsNoPriceLine` over 0, negative and NaN |
| M-8 | The "composes nothing" ban was a four-literal check on a text slice | **FIXED.** The slice is brace-matched (the seat's below-the-last-struct evasion fails), the facts property must be the Engine's list with no `+` and no hand-built `DetailFact`, and every `Text(...)` in the view must be a served value or a named `UIText` line. M21, M22c, M13, M29 all die |
| N-1 | A score labelled with the margin's unit | **FIXED** — `scoreUnit(for:in:)`, with the margin's own documentation quoted as the reason. `testTheNativeValueUsesTheScoresUnitNotTheMargins` |
| N-2 | The harness vanished when the engine sent no effort | **FIXED** — the harness is shown either way, with the right note. `testTheHarnessIsShownWithOrWithoutAnEffort` |
| N-3 | `language:` and `secondaryAgeDays:` unpinned at both doors | **FIXED** by M-5's whole-expression pins |
| N-4 | `.language-allow`'s header note says four files; there are eleven | **FIXED** — the note is corrected where this wave touched the file |
| N-5 | No `docs/plans/m15-wave-2-close.md` | **FIXED** — written with this record cited |
| N-6 | D-146's body edited in place at the M14 closure | **ACCEPTED**, recorded by the seat as not chargeable to W2 and not reversed here |
| NITs | `set(doors) == {...}` refuses a third door; `_swift_sources()` keys by basename; Turkish could live in `Language.swift` | **ACCEPTED, stated.** The door count is deliberate — an unpinned third door is the defect M-5 is about, and adding one means adding its pin. The basename shadowing is pre-existing and wider than this wave (the seat files it as K.9); `Detail.swift`'s exemption follows the `Uncertainty.swift` / `FrontDoor.swift` precedent |

**What the seat changed about this wave.** Of 37 mutants, 26 survived the tree it reviewed. After
these fixes the ones that survive are B-2's (the floor, the owner's line) and the two the seat
itself marks pre-existing (the arithmetic-laundering PARTIAL, `_swift_sources`' basename key). The
screen's words are now held by tests that compare two languages rather than by a list of four
strings, and both doors are held by their values rather than by their labels.
