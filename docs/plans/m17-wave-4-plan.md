---
record_type: plan
id: m17-wave-4-plan
status: draft
process_version: v6.6
date: 2026-09-25
---
# M17-W4 plan — board standings to the phone, and the combination on it

**Working plan for the `wave/m17-w4` pull request**, deleted before merge. Issue #50. Milestone
plan: `docs/plans/m17-plan.md` §2 W4, D-160 clauses 1-2. Risk: **HIGH**: a new `/v1` route, a new
thing the phone downloads and stores, and a second file allowed arithmetic. The security pass runs
before merge. The pull request opens only after the wave's reviews and `/pre-merge`.

## Goal

The phone holds every board's standings and can combine any set of boards into one list, by
position, on the device. Nothing about the question leaves the phone, because nothing about the
question shapes what the phone downloads. No screen changes: the question and the screen come in W5.

## Ruled by the owner, 2026-09-25 (in session, translated from Turkish)

1. **One payload, every board, fetched once a day.** The payload is about 250 KB, about 60 KB
   compressed, measured on the served artifact. The phone keeps it, so asking a question does not
   need the network.
2. **Only models present on every chosen board are combined.** Nothing is guessed. The list is at
   most as long as the smallest chosen board.
3. **W4 is infrastructure.** No screen.

Before the wave, #38, #40 and #41 are fixed (draft PRs #46, #49, #47). #38 matters here: without it
the agent boards lose their highest-effort rows.

## Shared contracts (K.8), grep-verified at 7d7a9ac

```
src/app/adapter/main.py:107:DECLARED_ROUTES: frozenset[str] = frozenset(
src/app/adapter/main.py:1249:@app.get(f"/{API_VERSION}/categories")
src/app/workflows/rank.py:109:def attributions_for(evidence_sources: Iterable[str], *, priced: bool) -> tuple[str, ...]:
src/app/workflows/rank.py:176:def build_price_medians(conn: sqlite3.Connection) -> int:
src/app/workflows/boards.py:28:def declared() -> list[Board]:
src/app/workflows/access.py:101:def served(conn: sqlite3.Connection) -> dict[str, str]:
ios/ModelRanking/Engine/EngineClient.swift:193:    private func get<T: Decodable>(_ path: String, query: [URLQueryItem]) async throws -> T {
tests/unit/test_ios_client_contract.py:169:SCORE_ARITHMETIC_PERMITTED = {"Uncertainty.swift": "D-138"}
scripts/client_decl_gate.py:107:NETWORK_FILE = "EngineClient.swift"
scripts/client_decl_gate.py:121:FILESYSTEM_FILE = "FrontDoor.swift"
tests/unit/test_api_v1.py:539:    expected = {"/health", "/v1/categories", "/v1/recommendations", "/v1/budgets"}
```

## Design

**`GET /v1/boards`**, an additive route with no parameters. Any query string is ignored and gets the
same bytes back. Its response:
- **`boards`:** every board the artifact holds with at least one rankable model: the surfaces'
  primary boards, the Arena slices, the Epoch boards and the agent boards. Each board carries:
  - `id` (its source), `benchmark` and `metric`;
  - its date: the newest `run_date`, else the newest `observed_at`;
  - its attribution, from `rank.SOURCE_ATTRIBUTION`; an unmapped source fails, as it does today;
  - `standings`: the rankable models (reconciled and priced) in order, each with a `position`.
    Tied models share a position (competition ranking), so a tie's order carries no meaning (#44).
- **`models`:** each model once: `id`, `display`, `vendor`, the blended price per 1M tokens (the
  same formula `/v1/recommendations` uses, D-109 rounding), and accessibility where W3 linked one.

**No score leaves the engine on this route.** The phone receives positions only, so it cannot
average two scales (D-105), whatever a later change tries. A board's position uses the model's best
row on that board, the same "best score per model" `ranked_population` uses.

**Bounds**, checked when the process boots, as `MAX_PUBLISHED_RANKING_ROWS` is: a ceiling on the
standings rows. Every published board has at least one row, so it also bounds the number of boards. The phone also refuses a response larger than a fixed
byte ceiling before decoding it.

**On the phone:**
- **`EngineClient.boards()`** fetches the route with no query items. It is the one door (D-126),
  and a test pins that nothing else is sent.
- **`StandingsStore.swift`** keeps the last payload in the app's caches directory and refetches when
  the payload is a day old. It becomes the second file the client-declaration gate allows to touch
  the file system, named with this wave's ADR. It writes only the payload the engine sent. Nothing
  typed goes into it (the D-126 text gate still scans it).
- **`Combine.swift`**:
  - input: the stored standings and a set of chosen board ids;
  - it keeps the models present on every chosen board, re-ranks them on each board by position
    among themselves, and orders them by the mean of those ranks;
  - ties are broken by model id, which is stable, never by display name;
  - output: the list, and for each model its position on each board, for W5's detail screen.

  It is the second file the arithmetic gate permits (D-160 clause 2). The gate's pattern is extended
  so it can see arithmetic on positions, and the permission is not left stale.

**A new ADR, D-167**, is written before the code. It records the route's shape, the positions-only
payload, the all-present rule, the tie rule, the store, and the two gate permissions.

## The one alternative (MED/HIGH rule)

**Send scores and let the phone rank.** A senior engineer would argue it keeps the engine thinner and
lets W5 show "how far ahead". It would put every board's raw scale on the phone, so one careless
average in any later file would break D-105. The positions-only payload makes that mistake
impossible, and costs no information the combination rule uses.

## Phases

- **P0:** D-167, this plan, and the issue.
- **P1: the route.** Red first:
  - the route is declared and additive; the existing key sets are unchanged;
  - the shape is frozen in `test_api_v1.py`;
  - only rankable models appear, each board is attributed, tied models share a position;
  - no score field anywhere in the payload;
  - a query string changes nothing;
  - the bounds are checked when the process boots;
  - `test_ios_payload_contract.py` covers the new Codable keys.
- **P2: fetch and store.** Red first:
  - `testTheBoardsRequestCarriesNothing`: no query items, and no header derived from the question;
  - the store refetches after a day and not before;
  - an oversized or undecodable response is refused and the last good payload is kept;
  - the client-declaration gate allows the file system in `StandingsStore.swift` and nowhere new;
  - the D-126 text gate still passes.
- **P3: the combination.** *Taken out of the wave at the three-attempts stop (owner ruling
  2026-09-26); filed as #61.* Red first:
  - a model missing from one chosen board is absent;
  - the order comes from positions, never from scores (the input has none);
  - ties are broken by id; the result is deterministic;
  - one board chosen equals that board's order;
  - an unknown board id is refused, never skipped;
  - each result names the boards it came from.

  The arithmetic gate permits `Combine.swift` by D-160.
- **P4: measured and recorded.** The payload size on the served artifact, raw and compressed. A
  combination on real boards compared by hand with the boards' own orders. The security pass.

## Risks

- **The payload grows with every board.** D-160 names "outgrows what a phone should download
  nightly" as its revisit trigger. P4 measures it, and the byte ceiling makes growth fail loudly.
- **Two gate permissions widen** (the file system, and arithmetic). Each is named in D-167 and scoped
  to one file. The security pass checks that nothing else gained them.
- **Board sizes differ a lot** (agent boards 30, Arena text 190). Under the all-present rule, a list
  including an agent board has at most 30 models. That is the owner's ruling, and W5's screen must
  say so.
