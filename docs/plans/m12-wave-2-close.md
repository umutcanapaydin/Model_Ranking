---
record_type: wave
id: m12-wave-2-close
status: ratified
process_version: v5.0
date: 2026-08-25
---
# Wave-Close Checklist — M12 Wave 2 (the comprehension pass)

> **STATUS: CLOSED 2026-08-25.** The wave that stops this product explaining what it measured in
> the language of the measurement. The work list was the council's 28-row inventory, not the
> owner's five items — he found the ones he happened to hit.

## What the wave delivered

- **Six surfaces renamed** to say what they measure. `Agentic coding` was renamed and then
  **reverted by owner ruling** — see below.
- **A rank beside every score**, and one line saying what the scale is. `161.7 ECI` now reads
  `#1 of 58 · an overall capability index — the scale has no fixed maximum`.
- **Price in pages**: `$10/1M` gains `about $10 per 1,500 pages of text`.
- **Disclosures under D-135**: classified without parsing text, deduplicated, and weighted — the
  real staleness keeps its orange, the five that can never clear go calm.
- **Three defects the council found**, fixed with tests: a false ordering note, `1x cheaper`, and
  an app telling end users to run `make run`.

**Measured at the closing tree:** `make check` exit **0** · `make gate` exit **0** ·
**747 Python passed / 12 skipped** (726 at wave start) · **88 Swift tests** (64 at start) ·
ruff, mypy, gitleaks clean · `check_records` PASS across 69 records · `wave-check-all` PASS.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m12-plan.md` §3 records W2 **MED** — presentation, but on every screen a reader sees | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → screenshot the running app → fix what the screenshot showed → test. The `1500` grouping defect was found that way, in a wave whose entire subject is readability | ✅ |
| 3 | Review per tier — V3C-78 / K.7 | `docs/reviews/m11-council-product.md`, `seat: independent` — this wave implements its inventory, so the review preceded the code **WAIVED — ledger row W-087.** Corrected at M12-W5: that review is dated 2026-08-24 and every commit in this wave is 2026-08-25, so it shaped the wave but did not read it (D-137). The independent read happened at Stage 4.0 and found two BLOCKING defects. | WAIVED |
| 4 | Fault injection — V3C-72 | **6 mutants, 6 killed** over `ios/ModelRanking/Engine/Router.swift`, `src/app/workflows/recommend.py`, `src/app/workflows/categories.py`; md5 restore verified | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-CMP-001/002: `ios/EngineTests/OwnerSessionDefectTests.swift` · REQ-CMP-003: `tests/unit/test_category_titles.py` · REQ-DSC-001: `DisclosureClassificationTests` | ✅ |
| 6 | New REQ-IDs in the PRD at the wave | `docs/prd.md` REQ-CMP-001, REQ-CMP-002, REQ-CMP-003, REQ-DSC-001 | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · `make gate` exit 0 · figures above | ✅ |
| 8 | ADRs for decisions made | `docs/decisions.md` **D-135** (taken before the wave, as the ruling this wave implements) | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md` — W-080, W-081, W-082 raised and **FIXED** | ✅ |
| 10 | Plan promises delivered | `docs/plans/m12-plan.md` §W2 — all four items | ✅ |

## The three findings this wave should be remembered for

**1. The owner's ruling outranks the council's recommendation, and a test caught me forgetting it.**
The council proposed renaming `Agentic coding` to `Coding on its own`. The owner had already
answered that question — *"Coding, Agentic Coding ok, there is no simpler version of those"* — and
the rename went in anyway. The no-two-titles-share-a-first-word test failed, because `Coding on its
own` collides with `Coding`. **Two corrections in one failure:** the owner had ruled, and the new
name was worse. The ruling is now recorded in the test file so it is not re-litigated.

**2. A disclosure pinned to an implementation detail has an expiry date.** `ORDERING_NOTE` said
answers were ordered alphabetically. That was true when written and false from the moment M11 made
the selected surface lead — a note asserting an ordering the reader could see was not happening,
shipped for a whole milestone, by our own hand. It now states what is INVARIANT.

**3. A phrase pin makes any rewording look like a regression, and a real regression look like a
rewording.** Two tests failed on this wave's rewrites while every word of their intent survived:
one required the literal "carries no meaning", another required `NSAllowsArbitraryLoads` within 600
characters of a specific case. Both now pin the claim and the audience instead of the offset. **A
test that fails when text MOVES teaches people to leave text where it is** — which is how a
user-facing string ends up explaining App Transport Security to a CFO.

## What is NOT closed

- **The engine's composed prose** — `pick.why`, `trade_off`, the notices — is unchanged except
  where it was defective. Rewording it now means writing it twice: W4 turns those sentences into
  FACTS and the client composes them, in two languages. Deliberate sequencing, not an omission.
- The council's inventory rows about benchmark names reaching the screen verbatim (`AIME (mock)`,
  `GPQA Diamond`) are W4's, for the same reason.
- W-074 (no shell linting) — declined by the owner, stays open.

---

Touched: `docs/plans/m12-wave-2-close.md`, `docs/prd.md`, `docs/warnings.ledger.md`, `ios/EngineTests/EngineClientTests.swift`, `ios/EngineTests/OwnerSessionDefectTests.swift`, `ios/ModelRanking/ContentView.swift`, `ios/ModelRanking/Engine/EngineClient.swift`, `ios/ModelRanking/Engine/Router.swift`, `Makefile`, `src/app/adapter/main.py`, `src/app/workflows/categories.py`, `src/app/workflows/recommend.py`, `tests/unit/test_api_v1.py`, `tests/unit/test_category_titles.py`, `tests/unit/test_cheaper_phrase.py`, `tests/unit/test_ios_client_contract.py`

K.8 contracts: `ORDERING_NOTE`'s text changed — it is rendered verbatim by the client and is therefore part of what a reader is promised; the CLAIM it makes is unchanged and is now pinned as a claim. `EngineError` gained `diagnostic`; `recovery` is now for the person holding the phone. Category TITLES moved; the ids did not (D-127). Frozen surfaces untouched: the `/v1` payload SHAPE, D-104.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-25 · Wave commit range: `2eba6ac..HEAD`
