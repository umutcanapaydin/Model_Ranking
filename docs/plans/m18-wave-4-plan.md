---
record_type: plan
id: m18-wave-4-plan
status: draft
process_version: v6.6
date: 2026-10-04
---
# M18-W4 plan — the engine and data backlog

**Working plan for `wave/m18-w4`**, deleted before merge. Milestone plan: `docs/plans/m18-plan.md` §2 W4.
Risk: **HIGH**. The wave touches `src/app/adapter/main.py` and `src/app/clients/**`, which are security
globs. By D-172 there is no security pass on the slice; the Tester's fault injection is owed.

**Order.** The owner chose on 2026-10-04 to run W4 before W2, because W2 needs the simulator, which he
keeps off for now (translated from Turkish: "not yet, W4 first"). The wave is stacked on
`wave/m18-w1` (PR #99) until that merges.

**Scope moved to W2.** #74 (`combine` is quadratic) and #56 (the phone reads a whole response) are the
app's code. #74 lands with #70, which is W2's, as its triage asks. Both go to W2; the plan amendment
in this wave's close says so.

## Decisions (made on the owner's standing instruction of 2026-09-29; recorded as D-173)

Each one marked "owner decision" in its triage is decided here as the agent recommends:
1. **Ties are ordered by model id, not by display name (#44).** A re-spelled name moves no position.
   The served order changes once, on the first night, and D-164's fingerprint moves with it.
2. **The night-to-night roster guards compare model ids (#39).** A display change is reported in the
   refresh record as information, never as a lost model and a gained one.
3. **Accessibility gets a loss guard (#42).** A night is refused when the number of models with an
   accessibility value falls by a quarter or more against the served artifact. The count goes in the
   refresh record. This is the same quarter D-128 uses for boards.
4. **The refresh checks the serving bounds on the candidate (#57).** These are the bounds the startup
   check enforces (`_egress_problems`). A candidate past one is refused with the bound named, and the
   live artifact keeps serving.
5. **`/v1/boards` is built once per artifact and compressed (#55).**
   - The payload is memoised on the artifact's identity, the key `_database_unusable` already uses.
   - Responses of 1 KB or more are gzip-compressed for clients that accept it. This applies on every
     route, through one middleware, with every security header kept. The data is public, so
     compression leaks nothing.
   - No ETag for now.
6. **Unselectable boards stay published (#77), with the reason recorded.** The phone selects boards by
   id from its own table (`Refinements.swift`). A new refinement then needs no engine release, because
   the phone already holds the board. After (5), the daily payload costs about a tenth of what it did.
7. **The retired refresher's installer is removed (#76).** The engine service runs the nightly
   refresh (D-170, D-154). `scripts/README.md` lists the service scripts.

Two fixes are pinned by their triage and need no decision: **#45**, which counts unknown efforts after
reconcile, and **#48**, which refuses a `-latest` token unless a date follows it. **#71** is pinned too:
the bounded fetch decides "late" before it closes the socket. **#79** follows the existing
contract-test shape.

## Phases (each red first, `make check-fast` green after each)

| Phase | Issues | Acceptance check |
|---|---|---|
| P0 | — | This plan and D-173 committed |
| P1 identity and ranking | #44, #45, #48 | Two tied models whose display names swap alphabetical order keep their positions. A derived `_high` row stored with effort `high` is not counted unknown. `grok-4.20-beta-latest-reasoning` derives nothing; `chatgpt-4o-latest-20250326` still derives |
| P2 the refresh's guards | #39, #42, #57 | A candidate that only re-spells N models yields no degradation and no anomaly, and its record lists the display changes. A candidate with 1 of 219 accessibility values is refused, naming the attribute, while a normal night still publishes. A candidate past `MAX_PUBLISHED_STANDINGS_ROWS` is refused with the bound named |
| P3 serving | #55, #77 | A second `/v1/boards` request does not rebuild. A gzip request gets the compressed body with every security header. A non-gzip request is unchanged. D-173 records #77's reason |
| P4 egress, contracts, scripts | #71, #79, #76 | A forced interleaving (the worker records EBADF after the close) still reports the deadline. `RUN_CONTRACT_TESTS=1` tests exist for the Epoch boards and `model_metadata.csv`, and are skipped otherwise. The retired installer is gone, and a test fails if any script installs `com.hcs.modelranking.refresh` |

## K.8 contracts (grep at `d528fd3`)

```
src/app/workflows/rank.py:323:        ORDER BY b.best DESC, m.display
src/app/workflows/refresh.py:374:    models: dict[str, frozenset[str]]
src/app/adapter/main.py:515:def _egress_problems(db: Path) -> list[str]:
src/app/adapter/main.py:1457:def boards() -> Any:
src/app/clients/protocols.py:129:    worker.join(total)
```

`/v1` changes no field and no route. The order of tied rows changes once (decision 1). Compression
changes encoding only, and only when the client asks for it.

## The one alternative

**Disclose ties instead of ordering them** (#44). The engine would mark tied rows so the phone shows
them as one shared place, as the combined list already does (D-168). That is better for a reader, but
it changes `/v1`'s shape and the cards. It is filed for W2's screen work if the owner wants it. A
stable key is the smallest change that stops the order moving for no reason.
