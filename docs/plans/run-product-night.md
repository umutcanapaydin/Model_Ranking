# Run — product-night

Mode: light
Started: 2026-10-16
Ended: 2026-10-16 — stopped at not-assumable, nothing independent left
Integration branch: `integration/run-product-night` · PR: #291
Plan PR: #290
Rulings: D-201, D-202, D-204

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | queue | e588910 | issues | stopped |

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| issue-288 | enhancement/issue-288-phone | #296 | none | stacked |
| issue-289 | enhancement/issue-289-golden | #302 | none | stacked |
| issue-273 | fix/issue-273-unsure-language | #298 | none | stopped |
| issue-218 | fix/issue-218-short-turkish | #299 | none | stopped |
| issue-66 | enhancement/issue-66-guiding-note | #300 | none | stacked |
| issue-301 | fix/issue-301-quantum | #303 | none | stopped |

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|
| 2026-10-16 | issue-273 | not-assumable | Ship #298 anyway? On the fresh set it scores the same as the shipped rule (65 of 96 searches, 10 of 72 non-searches caught), so D-202 clause 6 holds it back; its only effect is 5 confident answers in other languages (4 of them to non-searches) turned into "not measured" (`docs/research/reading-wave-m23-probe.md`) | issue-66 |
| 2026-10-16 | issue-218 | not-assumable | Ship #299? It scores the same as #273 and the base on the fresh set; short Turkish searches are 17 of 20 right on all three, so the issue's symptom is not seen there | issue-66 |
| 2026-10-16 | issue-301 | not-assumable | Ship #303? `quantum`/`kuantum` as expert words moves 1 of 1247 probe questions from wrong to right and loses none, but the fresh m23 set has no quantum question, so it does not beat the shipped rule there (D-202 clause 6) | nothing independent left |

## For the owner

The run ended on 2026-10-16. Nothing was deployed and nothing went to TestFlight (D-202 clause 7). The morning, in order:

1. Merge #281, the DevFlow v7.1 upgrade. #290 and #291 are built on it.
2. Merge #290, the plan PR. Its merge accepts D-201 and D-202.
3. Merge #291, the integration PR, as a **merge commit, never a squash**. It carries #296 (#288, the phone), #300 (#66, the guiding note) and #302 (#289, the golden set). `/post-merge` then closes them.
4. Decide each stop. Each is a ship-or-close, and each scored the same as the shipped rule on the fresh set:
   - #298 (#273)
   - #299 (#218), stacked on #298
   - #303 (#301), stacked on #302
5. Accept or amend D-203 (#66's wording tier, proposed).
6. Correct the golden set. Edit the human fields in `ios/EngineTests/Golden/golden-questions.json` (`question`, `language`, `expected_surface`, `disputed`, `reason`), then run `.venv/bin/python scripts/golden_questions.py` and `make check` (D-202 clause 2). It reports 36 of 42 asserted questions passing, 6 known misses (#292–#295, #301) and 7 disputed.
7. Test on the phone. Install from Xcode on the iPhone. A device build talks to the hosted engine, `https://model-ranking.fly.dev` (D-202 clause 4). With no connection, each surface shows its last answer, dated (clause 5).

Filed and left open: #297 (#288's security rereview, the rest), #283–#287 (the upgrade's guard and brief findings, for one small owner PR), #304 (L1 reads gitignored build output). `make deploy-check` stays red until a release security review and a milestone Tester run.
