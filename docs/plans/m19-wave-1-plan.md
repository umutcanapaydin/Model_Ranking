---
record_type: plan
id: m19-wave-1-plan
status: draft
process_version: v6.6
date: 2026-10-06
---
# M19-W1 plan — what the reader sees

**Working plan for `wave/m19-w1`**, deleted at the wave's close. The milestone plan
(`docs/plans/m19-plan.md` §2 W1) is the approved scope; the owner merged it on 2026-10-06.

**Risk: HIGH.** The registry and the refresh's board guards are touched, and #100 changes what an
upstream's names can move (`src/app/clients/**` and the guards, `m19-plan.md` §3). By D-172 no
security pass runs on the slice; the milestone closure's security seat reads it.

## Issues

| Issue | What | Phase |
|---|---|---|
| #101 | The subscription engine breaks ties by plan name | P1 |
| #106 | A moving `-latest-vN` alias could derive a fixed model id | P1 |
| #130 | `o3-mini-high` is served as a model of its own | P1 |
| #129 | One release is served under two model ids, its evidence split | P2 |
| #100 | The board guards compare raw names, so a re-spelling reads as names lost and gained | P2 |
| #124 | Attribution lags the publishers' terms (the parts that need no #88 ruling) | P3 |
| #112 | 68 models served under a lower-case spelling of their id | P3 |

## Phases

| Phase | Issues | Acceptance check |
|---|---|---|
| P0 | — | This plan |
| P1, small | #101, #106, #130 | Each red first. Plans break ties by their stable id, as models do, and one test states the rule for both engines. A derived id holding `latest-v` is said on the refresh record, not refused. `o3-mini-high` is `o3-mini` at effort `high`, and the effort grammar's other `-high` names are listed and ruled |
| P2, identity and guards | #129, #130's neighbours, #100 | Each dated id that names the only snapshot of its release is one model with the undated id, each pair ruled with its maker's evidence written beside it. A board's rows are compared by model id where the reconcile linked one; an upstream re-spelling that keeps every id moves no board guard, and one that changes ids still does |
| P3, what the reader reads | #124, #112 | Epoch's external boards credit their original sources; SWE-bench's licence is named; OpenRouter's code comment says what its terms say. Where attribution appears waits for #88, by name. Each of the 68 names reads as its maker spells it, from the maker's page or, failing that, the source that publishes it, with the source written beside each |

**The valve.** #112 is the part to cut if the wave runs long: each of the 68 names needs its
maker's own spelling checked. #129's pairs that cannot be ruled from a maker's page stay as they are,
listed on the issue.

## K.8 contracts

```
src/app/workflows/registry.py:277:_EFFORT_SUFFIX = re.compile(r"(?P<separator>[-_])(?P<effort>max|xhigh|high|medium|low)\Z", re.I)
src/app/workflows/registry.py:461:#: digit after a dash. A version (`-latest-v2`) names one release too, as a date does (W4 review R3).
src/app/workflows/registry.py:518:DISPLAY_NAMES: dict[str, str] = {
src/app/workflows/subscribe.py:286:def _pareto(rows: list[PlanRank]) -> list[PlanRank]:
src/app/workflows/subscribe.py:290:        key=lambda r: (-r.score, r.monthly_usd, r.plan),
src/app/workflows/rank.py:48:SOURCE_ATTRIBUTION: dict[str, str] = {
```

No `/v1` field changes. `models.display` values move (#112), and model ids join (#129, #130):
the refresh's guards compare ids, so the first night after the change is read with the owner.
