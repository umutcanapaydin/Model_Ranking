---
record_type: plan
id: m17-wave-5-plan
status: draft
process_version: v6.6
date: 2026-09-28
---
# M17-W5 plan — the question selects the boards, and the combined list on the screen

**Working plan for the `wave/m17-w5` pull request**, deleted before merge. Issue #64. Milestone
plan: `docs/plans/m17-plan.md` §2 W5; D-160 clauses 3-4, D-167. Risk: **HIGH**: the on-device model's
output now selects what the reader sees, and the screen changes. The security pass runs before
merge. The pull request opens only after the wave's reviews and `/pre-merge`.

**Depends on #61** (the combination, `Combine.swift`, restored with a property test). No code phase
starts before #61 is merged into `main` and `main` is merged into this branch.

## Goal

A question selects the boards it is about, and when it selects more than one, the reader gets the
product's own combined list. The detail screen says which boards it came from, their dates, how
many models they share, and that the combination is the product's own. Nothing about the question
leaves the phone (D-160 clause 1), and the on-device model can only choose among declared values
(D-104, D-126).

## Ruled by the owner, 2026-09-28 (in session, translated from Turkish)

1. **Surface plus refinement.** The 14 surfaces stay; each keeps its primary board. When the question
   concerns a language, a domain or a kind of conversation, the matching Arena slice is added: at
   most 2-3 boards. Without the on-device model, today's router picks the surface, and so its primary
   board alone.
2. **#54: D-167 clause 3 exactly.** Only the models every chosen board ranks; no threshold. The
   detail screen states how many models the chosen boards share.
3. **#53: both publishers count.** Two boards of one benchmark each count when both are chosen.
4. **The screen:** the combined list is the main answer when more than one board is chosen; one
   board keeps today's cards.

## Shared contracts (K.8), grep-verified at cce2ced

```
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:204:protocol QuestionRouter {
ios/ModelRanking/Engine/Router.swift:464:enum ModelOutputBoundary {
ios/ModelRanking/Engine/Router.swift:483:    static func schemaChoices(for known: [String]) -> [String] {
ios/ModelRanking/ContentView.swift:567:    private func submit() {
tests/unit/test_ios_client_contract.py:178:POSITION_ARITHMETIC_PERMITTED: dict[str, str] = {}
```

`Combine.swift`, `combine(_:boards:)` and its permissions arrive with #61.

## Design

**Refinements are declared, not generated.** A table in the Engine layer (`Refinements.swift`)
names each refinement and the board it adds:
- **Language** of the TASK: the Arena text slices chinese, french, german, japanese, korean, polish,
  russian, spanish and english.
- **Domain:** the Arena text industry slices: legal, medicine, business and finance, software,
  writing, entertainment, science, mathematical.
- **Kind:** multi-turn, longer query, creative writing, hard prompts, instruction following.
- **Vision kind:** ocr, diagram, homework, captioning, entity recognition, humor.

Each refinement also declares the surfaces it may refine, with a reason. Vision slices refine only
the vision surface. Which text surfaces each text slice may refine (for example, whether the Arena
coding slice refines the coding surface) is decided in P1 and measured in P4, not assumed here. A
test holds every entry against `/v1/boards` ids, so a slice the engine stops serving fails loudly.

**The on-device model fills a schema, not a sentence.** The schema that today has one field (the
surface) gains optional enumerated fields: `language`, `domain` and `kind`. Each is `anyOf` the
declared values plus `none`, restricted to the values the chosen surface allows.
`ModelOutputBoundary` checks every field as it checks the surface: a value outside the table is
dropped, never used. The language is the language the task concerns, not the language the question
is written in. A question written in Turkish about Python adds no language board.

**Without the on-device model**, the similarity tier and the manual tier return a surface only: one
board, today's cards.

**The boards chosen** are the surface's primary board, then at most two refinements in a declared
order (language, then domain, then kind). #53 is ruled: two boards of one benchmark each count.

**The screen.**
- **More than one board:** the main answer is the combined list, built by `Combine.swift` from the
  kept standings (D-167). It shows each model's position in the combined order, name, vendor and
  blended price, as a plain list with no badges.
- **One board:** today's cards, unchanged.
- **The detail screen** of a combined list names each chosen board with its date and attribution,
  states the number of models they share (#54), and says in one sentence that the list is the
  product's own combination, not a published leaderboard (D-160 clause 3).
- **Refinements are shown**, so the reader can see why a board was added and remove it with one tap.
  Removing one is a local choice and sends nothing.
- **The standings** come from `StandingsStore.current(now:fetch:)` (D-167), fetched once a day; the
  combined list works offline from the kept standings.

**A new ADR, D-168**, is written before the code. It records the refinement table and its
compatibility rule, the schema fields, the task-language rule, the fallback, #53's ruling and the
screen rule. It amends D-160's "intent" wording to "surface plus refinement".

## The one alternative (MED/HIGH rule)

**A free intent schema** (task, domain, language, input size, constraints), as the milestone plan
first described, with a table from each value to boards. A senior engineer would argue it
generalises to questions no surface names. It selects more boards per question, which under D-167
clause 3 shrinks lists sharply (#54 measured 3 models for three boards). It also puts more of the
model's output in charge of what the reader sees. The owner chose surface plus refinement.

## Phases

- **P0:** D-168, this plan, the issue.
- **P1: the refinement table.** Red first:
  - every entry names a board `/v1/boards` serves;
  - every refinement declares the surfaces it may refine, with a reason, and vision slices refine
    only the vision surface;
  - the board order is primary, then at most two refinements in the declared order.
- **P2: the schema and its boundary.** Red first:
  - `ModelOutputBoundary` drops a value outside the table and a value the surface does not allow;
  - `none` adds nothing;
  - the similarity and manual tiers return no refinement;
  - nothing new is sent (the D-126 gates pass unchanged in scope).
- **P3: the screen.** Red first, in the Engine layer's view models:
  - more than one board selects the combined list, one board the cards;
  - the detail names each board, its date and attribution, the shared count and the "product's own
    list" sentence;
  - removing a refinement recombines on the device.
- **P4: measured and recorded.**
  - The router probe (`scripts/router_probe/`) on both question sets, including a set of
    refinement questions written by someone other than the table's author (D-147 clause 5).
  - The combined lists on the served standings for the probe questions.
  - The security pass.

## Risks

- **The on-device model's output now selects boards.** The boundary is a schema plus
  `ModelOutputBoundary`, tested on every machine, as for the surface today. The security pass checks
  that no free text reaches a choice.
- **Short lists.** Under D-167 clause 3 exactly (#54), a small refinement board shortens the list.
  The Arena text slices rank 136 or more models, but the vision slices rank as few as 28
  (captioning), and the detail screen states the count.
- **The on-device model is unavailable on most test machines.** Every rule above is a function of
  its inputs, tested without the model. Only the session call itself is untested, as today.
- **Milestone closure** (Stage 4.0 security seat, closure report, retrospective, EXPERIENCE, M18
  plan) follows this wave as its own step, not inside it.
