---
record_type: wave
id: m8-wave-2-close
status: ratified
process_version: v5.0
date: 2026-08-19
---
# Wave-Close Checklist — M8 Wave 2 (Ruling A and the disclosures, gated by reading the client)

> **CLOSED 2026-08-19.** The wave the plan called "the one that matters", because this is where a
> client most easily undoes server-side honesty. It found one disclosure the app never showed.

## What the wave delivered

The app reaches all nine surfaces: `ContentView` asked for `task: "coding"` and nothing else, so
nine categories in the engine were one category on screen. It now fetches `/v1/categories` and
renders a chip strip — fetched, never listed in Swift, because a hardcoded roster is a second copy
of a list the engine already derives. `ranking_effort` is displayed for the first time. Four client
invariants became executable gates, and `app.sh restart` stopped lying about what it restarts.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m8-plan.md` §2 records W2 **MED**. The client is not the scoring path, so D-122 puts it in the single-pass column | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → test → self-review → fix on `ios/ModelRanking/ContentView.swift` and `tests/unit/test_ios_client_contract.py`. The author's own fault injection found the fixture check was worthless before it was committed | ✅ |
| 3 | Review per tier — V3C-78 / D-122 | **WAIVED under PRESSURE**, 2026-08-19, recorded as a `control-bypass` under V4C-13. Owner ruling of 2026-08-18 lightened the methodology and directed that waves not stop *(owner, translated from Turkish)*. `docs/plans/m8-wave-1-close.md` row 3 carries the same bypass; **this is the second, and a third sends the CONTROL for review under `C2b`** | WAIVED — PRESSURE, D-122 |
| 4 | Fault injection — V3C-72 | 5 mutants over the delta, 5 killed, `ios/ModelRanking/ContentView.swift` md5-verified restored. One needed a second attempt: the fixture check searched for a bare `"api_version"` and Swift escapes its quotes, so a real embedded payload would have walked past it | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-APP-002: `tests/unit/test_ios_client_contract.py::test_the_client_applies_no_ordering_of_its_own`. REQ-APP-003: `::test_the_client_references_every_optional_field_the_answer_carries`. REQ-APP-005: `::test_the_client_performs_no_arithmetic_on_a_number_the_engine_sent`. All three proven RED against mutants on 2026-08-19 | ✅ |
| 6 | New REQ-IDs in the PRD, at the wave not at closure | `docs/prd.md` — REQ-APP-001..005 and REQ-API-010 added here. Late for W1's rows (see `docs/plans/m8-wave-1-close.md` row 6), on time for this wave's | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · **530 passed / 12 skipped** · `xcodebuild` exit 0 · ruff and mypy clean · `check_records` PASS | ✅ |
| 8 | ADRs for decisions made | None needed. `/v1` was not moved, so **D-124**'s single permitted move remains UNSPENT — the client's needs were met by fields the payload already carried | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md`: **W-038** (there is no iOS test target at all) opened and ACCEPTED with M9 as the owning milestone | ✅ |
| 10 | Plan promises delivered | `docs/plans/m8-plan.md` §2 W2 asked for both coding answers with neither leading, and every disclosure visible. Both delivered; the second was delivered only because the test went looking | ✅ |

## The two findings this wave should be remembered for

**1. A disclosure the client never named.** `ranking_effort` is sent by the engine, decoded by the
Swift model, and mentioned by no view. `agentic-coding` ranks at a named comparable level, so a
score shown without it invites the reader to compare it against one measured elsewhere — which is
the entire reason the field exists. **It was found by a test, not by reading the screen**, because
`disclosures(_:)` is a hand-written list of five fields and this project has repeatedly found that
an enumeration typed out is a denylist wearing better clothes. The test derives the set from
`Answer`'s optional properties instead.

**2. `app.sh restart` restarted the app and not the engine**, while `up` advertised it as the thing
to run after a code change — true for Swift, silently false for Python and for a rebuilt
`advisor.db`, because a running process keeps the replaced file's inode and `/health` goes on
answering 200. Nine categories in the artifact, three on the wire, every check green. The only thing
that gave it away was the build stamp reading `dev-60cce36` against a HEAD of `d47a379`.

## What is NOT closed

- **W-038** — no Swift is executed by any gate. These tests gate the SEAM, not the rendering.
- **No fresh-eyes review ran.** Row 3, stated not implied.

---

Touched: `docs/prd.md`, `docs/warnings.ledger.md`, `ios/ModelRanking/ContentView.swift`, `ios/ModelRanking/Engine/EngineClient.swift`, `ios/ModelRanking/Engine/Models.swift`, `ios/app.sh`, `tests/unit/test_ios_client_contract.py`, `tests/unit/test_ios_payload_contract.py`

K.8 contracts: `/v1/categories` gains a consumer. Frozen surfaces untouched: `/v1` payload (D-115) — D-124's permitted move is UNSPENT.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-19 · Wave commit range: `a9dc034..c10bf3a`
