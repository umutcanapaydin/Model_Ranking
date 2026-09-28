---
record_type: plan
id: issue-66-plan
status: draft
process_version: v6.6
date: 2026-09-28
---
# Issue #66 plan — a question that is not a model search gets a guiding note, not a ranking

**Working plan for the `enhancement/issue-66-not-a-model-search` pull request**, deleted before merge
(an enhancement's plan never lands on the default branch). Issue #66. Risk: **HIGH**: the change
widens what the on-device model may answer and what `RoutingOutcome` carries (D-126), and the screen
changes. An independent Code-Reviewer, a Tester and a security pass run before the pull request opens.
By the owner's rule, the pull request opens only after those reviews and `/pre-merge`.

## Goal

Some input is not a search for a model at all:
- an attempt to instruct the model behind the text box;
- a knowledge question;
- chit-chat or nonsense;
- a request that the app do the task itself.

Today the on-device tier sends such input to a surface, and the reader gets a ranking that answers a
question they did not ask. After this change, the on-device model can say so, and the screen then
shows a guiding note with an example instead of a ranking.

## Ruled by the owner, 2026-09-28 (in session, translated from Turkish)

1. **Which inputs get the note:** all four classes above.
2. **The wording:** example-based guidance, in the app's informal register. Turkish: "This does not
   look like a model search. Tell me what you will use the model for; for example: 'I want to
   translate an email into French.'" English says the same.
3. **Timing:** after M17-W5 and before M17 closes, with its own probe (injection attempts included)
   and its own review.
4. **Only the on-device model decides.** Without Apple Intelligence, the wording tier behaves as
   today. Its similarity scores for nonsense and for correct routes overlap
   (`docs/reviews/m16-router-floor-measurement.md`), so no threshold separates them.
5. **Not recorded** in "Asked but not measured" (REQ-GAP-001). These inputs are not unmet model
   needs, and an injection attempt's text is not kept on the device.
6. **The screen:** the note and "Change" only. No ranking below it, and the previous question's
   ranking goes too, so it cannot read as the answer.
7. **The acceptance measure**, on the on-device model, twice:
   - at most **2** genuine model searches per run get the note (false positives), counted over every
     genuine question in the probe;
   - at least **80 %** of the not-a-search inputs get it.

   If a run misses, the instructions are corrected. After three failed attempts, the work stops
   and goes to the owner.

## Shared contracts (K.8), grep-verified at 3f2e91d

```
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:421:    static func schema(for known: [String]) throws -> GenerationSchema {
ios/ModelRanking/Engine/Router.swift:449:            If NOTHING here measures what was asked — image editing, cooking, travel, anything \
ios/ModelRanking/Engine/Router.swift:509:    static let declineSentinel = "__none__"
ios/ModelRanking/Engine/Router.swift:512:    static func schemaChoices(for known: [String]) -> [String] {
ios/ModelRanking/Engine/Router.swift:543:    static func outcome(
ios/ModelRanking/Engine/FrontDoor.swift:68:public func echoLine(question: String, surfaceTitle: String) -> String? {
ios/ModelRanking/Engine/FrontDoor.swift:116:func routingNotice(_ outcome: RoutingOutcome, _ language: Language) -> String {
ios/ModelRanking/Engine/FrontDoor.swift:332:func recordsGap(_ outcome: RoutingOutcome) -> Bool {
ios/ModelRanking/ContentView.swift:145:                let plan = answerPlan(
ios/ModelRanking/ContentView.swift:396:    private var matchedSurfaceRow: some View {
ios/ModelRanking/ContentView.swift:697:    private func ask() async {
ios/ModelRanking/Engine/AnswerPlan.swift:86:func answerPlan(
tests/unit/test_router_hints.py:209:        f"RoutingOutcome carries {sorted(fields)}; anything beyond a surface id, how it was chosen, "
```

**No `/v1` change.** Nothing new leaves the device: a not-a-search outcome sends no request at all.

## Design

**A second way out in the schema, not a second schema.**
- The surface field's closed set becomes the served ids, plus the decline sentinel, plus
  `ModelOutputBoundary.notASearchSentinel`.
- The instructions describe the four classes and say that a task description, even one with its
  content pasted in, is a model search.
- Only `ModelOutputBoundary` maps the new sentinel. The outcome it returns has
  `notASearch == true`, and it carries no refinement and no alternative.
- `categoryID` stays a served id (the unmeasured fallback), so every existing invariant on it holds.
  `unmeasured` stays true, because nothing was measured.

**The Engine layer decides; the view follows.**
- `showsAnswer(_:)` is false for a not-a-search outcome.
- `routingNotice` returns the guiding note for it.
- `recordsGap` returns false for it.
- The echo shows the question without a surface.
- `ask()` changes no surface, loads nothing, and resets the refinements.
- The view hides the cards and the combined list when `showsAnswer` is false.

Every one of these is a function with a test. The view itself stays untested (#69); the simulator
run covers it.

**Held from the source, as W5 did.**
- Only `ModelOutputBoundary` builds an outcome with `notASearch:`.
- Nothing assigns it later.
- The encoded-schema test holds the surface field's exact choices, the new sentinel included.
- The D-126 field-set gate names the new field.

**A new ADR** is written before the code. It records the rulings and amends:
- REQ-ASK-003: this class gets a note, not a ranking;
- REQ-GAP-001: not recorded;
- D-126: one more outcome field and one more closed value.

A prd row, REQ-ASK-005, states the requirement and cites the tests.

## The one alternative (MED/HIGH rule)

**A separate `request` field** in the schema ("model search" / "not a model search"), beside the
surface. A senior engineer would argue it keeps the surface field's meaning pure. But it lets the model
answer both at once (a surface AND "not a search"), and that contradiction has to be resolved somewhere.
One exclusive value in one field cannot contradict itself, and the decline sentinel already set that
precedent (D-126).

## Phases

- **P0 — the ADR and this plan.** The new ADR and the prd row. No code.
- **P1 — the boundary.** Red first:
  - the new sentinel maps to a not-a-search outcome with no refinement and no alternative;
  - the wording and manual tiers never produce one (source pin);
  - the encoded schema offers exactly the served ids and the two sentinels;
  - the D-126 field-set gate names the new field.

  Check: the tests, then `make check-fast`.
- **P2 — the screen.** Red first:
  - `showsAnswer`, `routingNotice` (both languages, the example included), `recordsGap` and the echo
    without a surface;
  - in `ContentView`, `ask()` and the hidden answer.

  Check: the tests, `make check-fast`, and the simulator. The simulator run covers a not-a-search
  input (note, no ranking, "Change" works), then a genuine question afterwards, which must bring
  back the answer.
- **P3 — the instructions, measured.**
  - **Tuning sets:** the existing `offtopic_questions.json`, `offtopic_heldout_questions.json` and
    `nonsense_questions.json`, and the genuine sets (`probe_questions.json`, `heldout_questions.json`,
    `refinement_heldout_questions.json`).
  - **Final measure:** a NEW set written by an independent agent who sees only the four class
    descriptions and the surface list, never the instructions (D-147 clause 5). It covers each class
    in Turkish and English, injection attempts in several forms, and genuine model searches that sit
    near the line (for example "which model is best at trivia questions?").
  - Two runs; the acceptance measure is ruling 7.
  - Recorded in `docs/research/issue-66-not-a-model-search-probe-2026-09-28.md`; the new set is
    committed under `scripts/router_probe/`.
- **P4 — the reviews.** An independent Code-Reviewer, then a Tester, then a security pass, each a
  separate seat run one after another. Then `/repo-review` over the branch and `/pre-merge`. Only
  then does the draft pull request open.

## Risks

- **False positives.** A genuine search told "this is not a model search" is worse than an
  off-topic ranking: the reader gets nothing. Hence the ≤ 2 bound, and a "Change" control that is
  always there.
- **The model is not deterministic** (W5 probe: 35 of 43 surfaces agree across runs). Two runs,
  ranges reported.
- **Injection as data.** The guarantee does not rest on the instructions. The schema admits only
  declared values, and the boundary returns declared outcomes (W5 security pass). This work changes
  what the screen does with one more declared value; it adds no free text.
- **#73** (the routing of coding questions) touches the same instructions. It follows as its own
  pull request and may reuse this probe's harness.
