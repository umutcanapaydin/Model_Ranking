---
record_type: plan
id: m19-wave-4-plan
status: draft
process_version: v6.6
date: 2026-10-07
---
# M19-W4 plan — reading the question, a second round

**Working plan for `wave/m19-w4`**, deleted at the wave's close. The milestone plan
(`docs/plans/m19-plan.md` §2 W4) is the approved scope. W3 merged on 2026-10-06 (#184).

**Risk: HIGH.** What the on-device model's output decides (D-126) is touched, and
`ios/ModelRanking/Engine/Router.swift` is a security glob (`m19-plan.md` §3). The owner reviews the
wave (AGENTS.md §3). By D-172 no security pass runs on the slice.

## Issues

| Issue | What | Phase |
|---|---|---|
| #177 | Signal words entered after the M18 held-out sets that alone hold them | P1 |
| #66 | Knowledge questions are answered with a ranking (M18-W3: 1 of 10 caught) | P3 |
| #113 | A request to make an image is answered as measured (7 of 15 caught as shipped; 3 ranked on `web-dev`) | P4 |

## Decisions taken on the owner's standing instruction

The owner's standing instruction (2026-09-29): take the agent's recommendation, don't ask.
- **#177:** the three M18 held-out sets are retired to tuning, and W4 measures on fresh ones. Each
  was spent before W4: run held out, then read or run again
  (`docs/research/m18-w3-question-reading-probe-2026-10-04.md` §5, §6). This beats showing an origin
  for each of the four words, which the commits do not record.
- **The held-out set:** the owner has not run a stranger's session
  (`docs/research/stranger-first-use-protocol.md`), so an independent seat writes the fresh sets.

## The sets (D-147 clause 5)

A new independent seat writes two sets. Before writing, it reads nothing in the repository: not the
app, not the router's wording, not any probe set, test or research record. Its brief carries what
it needs: D-169 clause 1 and REQ-ASK-005, which are the owner's definitions of the classes, and the
engine's own name and benchmark for each surface (`src/app/workflows/categories.py`). Half of each set
is in Turkish, and the questions are written the way people type. The author never reads either set
until the wave's last held-out measure, and scores runs only by count (`score_reading.py` with no
`--show`).

- `notasearch_heldout_m19_questions.json` (100):
  - 50 not a search: 20 knowledge questions, and 10 each of instructions to the app, chit-chat or
    nonsense, and content pasted to act on;
  - 40 genuine searches across every surface, at least 10 of them close to a knowledge question
    (asking which model knows facts, history or science, or naming a factual task);
  - 10 ambiguous.
- `image_heldout_m19_questions.json` (50): 20 requests to make or change an image (at least 5 for a
  website, an app or a brand); 10 requests to read one; 20 questions that only mention images (code,
  websites, documents and the rest).

The same commit retires `coding_heldout_m18_questions.json`, `notasearch_heldout_m18_questions.json`
and `image_heldout_m18_questions.json` (`RETIRED_HELD_OUT`). Their entries leave
`HELD_OUT_ONLY_REVIEWED`. The seat writes any entry the fresh sets bring, each in the app before the
set was written, and the author does not read them before the last measure. Swapping the live sets
must be one commit: the held-out gates fail with no live set.

**Tuning, for every variant:**
- reading: the retired M17 and M18 not-a-search sets (170, with 22 knowledge questions) and
  `docs/research/m18-w3-runs/reading_tuning.json` (139);
- images: the three image sets (12, 30, 40);
- coding, as a guard on any change to the model's instructions: the retired M18 coding set (80).

## How it is measured

- **Harnesses:** `scripts/router_probe/ReadingProbe.swift`, run in a scratch copy of `ios/` on the
  owner's Mac, where Apple Intelligence runs (checked 2026-10-07). It gains a wording-tier mode
  (`PROBE_TIER=wording`: `TieredRouter` with no model), since #113 names that tier.
- **Two runs each:** the model is not deterministic. Run outputs and scorers go in
  `docs/research/m19-w4-runs/`, and the record goes in `docs/research/m19-w4-question-reading-probe.md`.
- **Baseline:** the shipped code at `3426ff3` (the wave's base), on the fresh sets, twice. Model tier
  and wording tier, counts only.
- **Bars,** fixed by these rules and committed with the baseline, before any variant runs. Each run of
  the final measure must meet each bar:
  - D-169 clause 6, fixed:
    - at most 2 genuine searches given the note without being asked;
    - at least 40 of the 50 not-a-search inputs given the note or asked.
  - M18-W3's bound, fixed: at most 4 genuine searches asked.
  - **#66:** knowledge questions given the note or asked. The bar is the baseline plus two thirds
    of the gap to 20, rounded up; the baseline is the lower of its two runs.
  - **#113:** requests to make an image told "not measured". The bar is the baseline plus two
    thirds of the gap to 20, on the model tier and on the wording tier alike.
  - **Guards,** each against the baseline's lower run:
    - genuine searches on their expected surface lose at most 2;
    - requests to read an image reaching `vision` lose at most 1;
    - questions that only mention images are overridden to "not measured" at most once per run.
- **Variants:** three per problem, each run twice on the tuning sets only. The best is built red-first
  and measured once, twice, on the held-out sets.

## Phases

| Phase | Issues | Acceptance check |
|---|---|---|
| P1 | #177 | The fresh sets and the retirement land in one commit, by the seat. The held-out gates pass on it: no fresh question is in code, a test or a tuning set, and every held-out-only entry is reviewed. #177's outcome is in the `RETIRED_HELD_OUT` comment |
| P2 | — | The probe's wording-tier mode. The baseline on the fresh sets, both tiers, twice. The bars, computed by the rules above, committed with the runs before any variant runs |
| P3 | #66 | Three variants on the reading tuning sets, each run twice. The starting points: (a) the model's instructions define a knowledge question by what is asked, a fact wanted now with no task named, and `assistant`'s description stops saying "answer a general question"; (b) a doubt in code for a short question of fact that names no model, AI, task or time ("who wrote …", "which year did …", and their Turkish forms), weighed with the model's verdict as the other doubts are (D-169 clause 4 as amended); (c) both. The best is built red-first, with `ReadingTests` holding each side of its line |
| P4 | #113 | Three variants on the image tuning sets, each run twice. The starting points: (a) the image rule reaches every surface the tier chose, not only `vision`, where the image is the making verb's object and no website, page, app or code word is in the question (the M18 reviews' B4 line); (b) the model is asked in a closed yes/no field whether the text asks to make or change an image, combined with the rule in code; (c) the rule's vocabulary from the tuning misses, Turkish forms included. The best is built red-first, on both tiers |
| P5 | #66, #113 | The held-out measure, twice on the model tier and on the wording tier, against the bars. The record, a new ADR amending D-169 (and REQ-IMG-003's refusal half), and REQ-ASK-005, REQ-IMG-003 and REQ-RTR-005 updated with what was measured |

**The valve.** D-169 clause 6: three variants per problem, then the held-out measure, once. A bar
missed there goes back to the owner as one question in the pull request, and nothing more is
tuned. A variant that does worse than the shipped code on its tuning set is not built: the shipped
code stays for that problem. #113 is cut before #66 if the wave runs long. #66 is the larger gap
(REQ-ASK-003's W-123).

**The issues' outcomes.** #66 and #177 are enhancements: closing keywords only if delivered in full.
#113 is a bug: it closes after the merge, and only if its bar is met (D-178).

## K.8 contracts

```
ios/ModelRanking/Engine/Router.swift:70:    static let byID: [String: String] = [
ios/ModelRanking/Engine/Router.swift:449:    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
ios/ModelRanking/Engine/Router.swift:553:    static let requestGuidance = "A model search, or something else: instructions to you, small talk, "
ios/ModelRanking/Engine/Router.swift:704:    static func read(_ question: String, _ outcome: RoutingOutcome) -> RoutingOutcome {
ios/ModelRanking/Engine/Reading.swift:148:    static func makesAnImage(_ text: String) -> Bool {
ios/ModelRanking/Engine/Reading.swift:324:func inputReading(noWord: Bool, smallTalk: Bool, doubt: Bool, modelSaysNotASearch: Bool?) -> InputReading {
tests/unit/test_ios_client_contract.py:208:RETIRED_HELD_OUT = {"heldout_questions.json", "refinement_heldout_questions.json",
scripts/router_probe/ReadingProbe.swift:22:    func testProbe() async throws {
```

No `/v1` field or route changes. A new closed field in the model's schema (P4's variant b), if
built, is D-126's closed set and is recorded in that ADR.
