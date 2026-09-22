---
record_type: review
id: m15-wave-3-review
status: ratified
seat: independent
date: 2026-09-22
---
# Wave 3 Code Review and Tester Review (m15), retroactive

**Reviewer:** independent Code-Reviewer + Tester seat. I did not write any of the wave's code. I read the plan and the diff, not the wave's commit message.
**Commit reviewed:** `d8cd650` against its parent `93686df` (M15-W3 + D-147).
**Risk tier:** HIGH (`docs/plans/m15-plan.md` §2 W3), so the review is at Code-Reviewer + Tester depth, including mutation testing.
**Policy read from the base ref `855b44a`:** `subagent-profiles/Code-Reviewer.md`, `subagent-profiles/Tester.md`, `AGENTS.md`. No policy was taken from the change.
**Model routing (V4C-03):** the author and this seat are both Claude-family models. No second family was available. This seat ran in a fresh context and had no access to the authoring session.
**This review is RETROACTIVE.** The wave was committed before any code review or tester review ran. No `docs/plans/m15-wave-3-close.md` exists. The security pass is in `docs/reviews/m15-closure-security-review.md` and I did not repeat it.
**Already known, not re-reported here:** W-113 (the vision count and the close_call pairing), W-114 (deleted screen strings), W-115 (crossed search hints and the image decline hint), W-116 (D-144 not built). Their fixes are assessed at the end.

## Verdict

**BLOCKING: 2 BLOCKING, 3 MAJOR, 6 MINOR, 2 NIT.** The wave does what its source code claims. It adds one board, one source id, one label and one attribution per surface, and the routing reaches all three new surfaces through the real embedding router. Both suites are green at `d8cd650`: Python 951 passed and 12 skipped, Swift 257 executed with 0 failures. The two blocking findings are test-integrity findings, and the base Tester profile makes both blocking at HIGH tier. First, the criterion REQ-SUR-002 cites a board-isolation test that does not cover any of the three new surfaces. A mutant that makes `vision` rank the chat board survived every gate. Second, a floor assertion was loosened from 25 to 20 so the new boards would pass. Its comment describes a rule based on proportion, but the test does not check one. The three MAJOR findings are these. D-147 changed how routing scores are computed, but the 0.15 similarity floor was not re-measured. The search surfaces are priced without the search call. The wave was closed with no review. I ran 16 mutants: 11 died and 5 survived.

## Findings

### BLOCKING

**B-1. REQ-SUR-002's board-isolation citation does not exercise the three new surfaces.**
`docs/prd.md:523` cites `tests/unit/test_categories.py::test_a_board_only_reaches_its_own_surface_through_the_ranking_query` for "each rank ONLY their own board". That test (`tests/unit/test_categories.py:439`) ingests only `arena`, `arena_document` and `arena_factuality`, and it checks only `("assistant", "document", "factuality")` (`:493`). The two neighbouring guards have the same gap. `test_ingest_stores_each_board_under_its_own_benchmark` (`tests/unit/test_arena_client.py`, the loop over three source ids) and the client-class table (`tests/unit/test_arena_client.py:244-247`) also stop at the pre-M15 boards.
*Failure scenario:* mutant M7 changes `vision`'s `primary_benchmark` from `"Arena vision"` to `"Arena text"`. The full Python suite stays green, and `vision` would then serve chat-board Elo against a vision-board floor. That is the comparison D-105 forbids. Under the Tester profile §1, a criterion whose cited test does not assert the claimed behaviour is BLOCKING.
*Remedy:* extend the fixture with the three boards: one model on each board at a distinct rating, plus one model that appears on a single board only. Assert over every Arena-sourced surface in `CATEGORIES` instead of a hand-written tuple. Add the three clients to the class table and the three source ids to the ingest test.

**B-2. The truncation-floor assertion was weakened to admit the new boards, and it does not check the rule its comment states.**
At `tests/unit/test_arena_client.py:326-332`, the assertion changed from `minimum_rows >= 25` to `>= 20` because `search` and `search_factuality` ship with 20. The comment says "Proportion, not an absolute" and argues from percentages, but the assertion is still an absolute value.
*Failure scenario:* mutant M9 lowers `vision`'s floor from 60 to 20, which is 13% of the 152 rows the board returns today. It survived. A fetch truncated after the first page would then be served as a whole board. The Tester profile's "weakened/deleted-to-green" check is BLOCKING at HIGH tier. No ADR or owner ruling is attached to the change.
*Remedy:* check the rule the comment states. One option is to pin each board's measured size, taken from `docs/research/m15-board-survey-2026-09-21.md`, and require `minimum_rows >= 0.5 * size`. The other is to pin each board's `minimum_rows` value in a table. Either version kills M9.

### MAJOR

**M-1. D-147 changed the similarity score but did not re-measure the 0.15 floor, and the floor has stopped doing its job.**
`ios/ModelRanking/Engine/Router.swift:217-231` justifies `defaultFloor = 0.15` with a measurement taken when a question was compared with one hint sentence. The wave now scores a surface as the mean of its two closest examples out of six (`:332`). It also centres the vectors on the mean of 84 examples, so the numbers are on a different scale. `ios/EngineTests/RouterBoundaryTests.swift:204` pins the literal value, so the test enforces a number whose measurement no longer applies. `docs/reviews/m15-router-recalibration.md` re-measured routing accuracy but not the floor.
*Evidence:* I ran the wave's own probe (`scripts/router_probe/probe.swift`, top2 mode, examples extracted from this commit). Every nonsense input scored above the floor: `asdf qwer zxcv` 0.196, `lorem ipsum dolor sit amet` 0.229, `blue banana seventeen` 0.212, `ok` 0.235. Each one was declined only because a decline group happened to score higher. Off-topic questions route confidently with `unmeasured` false: `what is the capital of france` goes to `vision` at 0.506, `what time is it` to `vision` at 0.548, and `recommend a good pizza place` to `web-dev` at 0.341.
*Failure scenario:* REQ-RTR-005 exists so that the product never implies it measured something it did not. A general-knowledge question is now sent to "Reading images and screenshots" with no disclosure.
*Remedy:* re-measure the floor under the scoring that ships, using a nonsense set and an off-topic set, and record the result. Update the pin to the new value. Add a real-router test in which a nonsense string comes back `unmeasured` under the default floor.

**M-2. `search` and `search_factuality` rank on per-token price, and the search call itself is not priced.**
The W1 survey (`docs/research/m15-board-survey-2026-09-21.md:127`) says "What is still unpriced is the search call itself, and that is the same pricing-basis ruling the image boards need". The image boards were refused on exactly that ground (`docs/reviews/m15-category-calibration.md`, "What was refused"), yet the two search surfaces shipped without the ruling. `src/app/workflows/registry.py:194` deliberately reconciles `gpt-5-search-api` and `o4-mini-deep-research` to their families, so these models are priced at their base models' token price. No text in `src/`, `ios/` or `docs/decisions.md` at this commit discloses this.
*Failure scenario:* the Budget Pick and Best Value on these surfaces compare token prices only. A model whose per-search fee dominates what a reader actually pays looks cheap. Plan §2 W1 asked "whether the engine's per-token price can honestly rank it", and this was answered with "smaller than it looked" rather than with a ruling.
*Remedy:* get an owner ruling as an ADR. It should say one of two things: either both surfaces state that the search call is not in the price, or they withhold price-based picks until the call is priced.

**M-3. A HIGH-risk wave was closed with no review and no close record.**
No `docs/plans/m15-wave-3-close.md` exists, and no Code-Reviewer or Tester record for W3 existed before this one. Plan §4 requires every wave close to cite an independent review dated after the code. `AGENTS.md` §3 treats a HIGH-tier review gap as an escalate-now item. W-114 and W-115 were found by a seat that read the tree, but that seat left no review file, and K.7 requires the review to be a file.
*Remedy:* add a ledger row for the bypass (V4C-13), and write the W3 close record citing this review. The close record should also list B-1, B-2, M-1 and M-2 as open.

### MINOR

**m-1. The new surfaces' thresholds are not pinned to their calibration record.**
In `src/app/workflows/categories.py:286-330`, only `score_anchor` is pinned (in `tests/unit/test_uncertainty_contract.py`). Mutant M5 moved the `search` floor from 1206.9 to 1100.0 and survived. Mutant M8 raised `vision`'s close_call and window by five times and survived. W-113 later showed these values do drift. *Remedy:* add a table test for `min_quality`, `close_call` and `value_window` that cites the calibration record.

**m-2. The three new boards have no contract test against the real API (V3C-44).**
`tests/integration/test_arena_openrouter_contract.py:32` fetches only the `text` config. I fetched all three live with the wave's clients: `vision` returned 152 rows, `search` 34 and `search_factuality` 32, with 0 skipped, so the parser holds today. *Remedy:* parametrize the contract test over `ARENA_BOARDS`.

**m-3. W-115's narrowing of the image decline hint has no regression test.**
Mutant M16 put `describe this photo` and `what is in this picture` back into the image decline group (`Router.swift:126`), and all 257 Swift tests stayed green. *Remedy:* add a real-router test that `describe this photo` routes to `vision` and is not declined.

**m-4. The positive routing tests use the examples' own wording.**
At `ios/EngineTests/FrontDoorTests.swift:332-334`, "search the web for today's gold price" and "look it up online and give me the real source" are close paraphrases of the examples at `Router.swift:193-197`. These tests prove that the example wording reaches a surface. They do not prove that a reader's own words do, which is what REQ-SUR-002 claims. The held-out set in `scripts/router_probe/heldout_questions.json` is the only evidence of generalisation, and no gate runs it. *Remedy:* move the held-out set's questions for the new surfaces into a Swift test.

**m-5. The calibration record cannot be reproduced from the repository.**
`docs/reviews/m15-category-calibration.md:15` names `~/Desktop/terminal_output/model_ranking/calibrate_new.sh`, a file outside the repository (seed F.4). At this commit the record was `status: draft` while its numbers were being served. *Remedy:* commit the exact command lines and ratify the record.

**m-6. W-113's test checks the helper function but not the script's use of it.**
I established this by reading the code and did not run a mutant. `tests/unit/test_calibrate_board.py` checks `one_name_per_model` and `_overlapping_gaps`. It does not check that `main()` passes the helper's output into the gap measurement. Reverting `list(best_name.values())` to `rankable` inside `main()` would stay green. *Remedy:* factor the population step out of `main()` into a function and test that function.

### NIT

**n-1.** At `src/app/clients/arena.py:90`, the comment "152 rows, 41 rankable" describes `vision`, but it sits under the `vision` line and directly above `search`, so it reads as if it describes `search`.
**n-2.** The test named `FrontDoorTests.swift:327` `testTheTwoNewSurfacesAreReachableByAsking` now covers five surfaces.

## Plan W3 criteria and contracts, with evidence

| Criterion (plan §2 W3, §3, §4) | Evidence | Result |
|---|---|---|
| One board, one source id, one benchmark label | `arena.py:89-95`; label uniqueness at `test_arena_client.py:239-242` (M2 died); registry and client name at `tests/unit/test_sources.py:157` (M1 died) | met |
| Refused if unattributed | `rank.py:58-60`; `test_arena_client.py:324` (M3 died) | met |
| The source disclosure seam | `test_categories.py` pairs table covering all 14 surfaces (M4 died) | met |
| Each new surface ranks only its own board (REQ-SUR-002) | cited test does not cover the new surfaces (M7 survived) | **not proven (B-1)** |
| Thresholds derived and recorded | `m15-category-calibration.md`; values not pinned (M5, M8 survived) | partial (m-1, m-5) |
| A hint worded away from its neighbours, and a positive routing test that runs the real embedding router (plan §4) | `Router.swift:191-197`; `FrontDoorTests.swift:327-339` (M15 and M14 died) | met, weakly (m-4) |
| Turkish title for each new surface | `Language.swift:494-496`; `LanguageTests.swift` (M10 died) | met |
| D-144 carry-forward built | not built | W-116, not re-reported |
| `/v1` gains no field without an ADR | `git diff 93686df d8cd650 -- src/app/adapter` is empty. The new surfaces are new values in an existing list, not new fields | met |
| D-104 / D-105 | `secondary_benchmark=None` on all three; separate labels per board | met in code, unproven in tests (B-1) |
| D-126 | no new network code under `ios/ModelRanking`; the router embeds on the device | met |
| D-138 | router arithmetic works on embeddings, never on a served score | met |

**Producers of the hardened invariant "one board reaches one surface":** `ARENA_BOARDS` (`arena.py`), the three client classes, `REMOTE_SOURCES` (`sources.py`), `ingest_arena` (`ingest.py:155`) and `CategorySpec.primary_benchmark`. The citing tests are `test_arena_client.py:239-242` for the board table, `test_sources.py:157` for the client name, and the `test_categories.py` pairs table for the source. **Gaps:** `primary_benchmark` of the new specs, the ingest label for the new source ids, and the new client classes (B-1).

## Fixes to earlier findings: are they adequate?

- **W-113** (fixed in the uncommitted working tree): the diagnosis and the corrected margins are sound. The remaining test gap is m-6.
- **W-114:** adequate. `test_every_screen_string_the_client_calls_exists` covers the class of defect.
- **W-115:** the crossed hints are fixed, and I reproduced 21 of 21 on the wave's own probe. The fix brought two new problems: the floor drift in M-1, and an image decline narrowing that no test checks (m-3).
- **W-116:** correctly recorded as a scope drop and deferred by the owner.

## Mutants

Each mutant was applied by script in a private worktree at `d8cd650`. The gate ran, and the file was then restored and checked to be byte-identical by md5. The gate was the Python suite, plus `swift test` for Swift files when Python stayed green.

| id | mutation | target rule | result |
|---|---|---|---|
| M1 | `ArenaSearchClient` fetches config `search_factuality` | REQ-SRC-011, D-105 | DIED (`test_sources.py:157`) |
| M2 | `search_factuality` board labelled `Arena search` | D-104/D-105 | DIED (`test_arena_client.py:242`) |
| M3 | `arena_vision` attribution removed | licence attribution | DIED (`test_arena_client.py:324`) |
| M4 | `vision` `primary_source` set to `arena` | D-121 disclosure | DIED (`test_categories.py:412`) |
| M5 | `search` `min_quality` 1206.9 changed to 1100.0 | D-145 threshold | **SURVIVED** |
| M6 | `search_factuality` `score_anchor` 1203.7 changed to 1210.0 | D-146 | DIED (`test_uncertainty_contract.py:284`) |
| M7 | `vision` `primary_benchmark` set to `Arena text` | D-105, REQ-SUR-002 | **SURVIVED** |
| M8 | `vision` close_call 8.1 changed to 40, window 32.3 to 90 | calibration record | **SURVIVED** |
| M9 | `vision` `minimum_rows` 60 changed to 20 | truncation floor | **SURVIVED** |
| M10 | Turkish title for `vision` removed | UI title | DIED (`LanguageTests.swift:232`) |
| M11 | `search` examples keyed to an unknown id | D-147 clause 4 | DIED (`test_router_hints.py`) |
| M12 | `search` and `search_factuality` example keys crossed | D-147, W-115 | DIED (`test_router_hints.py`) |
| M13 | `defaultFloor` 0.15 changed to 0.0 | REQ-RTR-005 | DIED, but only on the literal pin (`RouterBoundaryTests.swift:205`) |
| M14 | top-two scoring reverted to the single closest example | D-147 | DIED (`FrontDoorTests.swift:311`) |
| M15 | positive routing expectation for `search` changed to `search_factuality` | W-103 shape | DIED (`FrontDoorTests.swift:339`) |
| M16 | image decline group given `describe this photo` and `what is in this picture` again | W-115 | **SURVIVED** |

11 died and 5 survived, a kill rate of 69%. M13 counts as died, but only a literal pin killed it, which is the point of M-1.

## What I did not check

- Security. It is covered by `docs/reviews/m15-closure-security-review.md`.
- The Xcode app build and the app's behaviour on a device, including D-147's untimed cost of about 100 embeddings per question.
- Whether the shipped floors are correct against the live board. I fetched the boards and counted rows but did not re-run `scripts/calibrate_board.py`.
- The W-113 working-tree test suite. I read it but did not run it or mutate it.
- `note.txt`, `docs/process-log.md` and the `scripts/router_probe/` files beyond running the probe.
- Coverage numbers on the touched modules.
