# The run golden-night reading rules, measured on the fresh set reading_heldout_m24

D-206 clause 2: a reading rule ships when it turns no row of a fresh held-out set from right to wrong, and fixes the golden question it was written for.

## The set

The set reading_heldout_m24_questions.json was written on 2026-10-17 by an independent seat: a subagent dispatched only to write it. It read no routing code, no examples and no tests. What it did read:
- the served surfaces;
- the m23 set and its README, for the format;
- issues #292, #293 and #295, for the shapes the rules target.

It holds 173 rows: 112 searches and 61 lines that are not a search. The languages are English (79), Turkish (78) and seven others (16). A script checked the set against every JSON under `scripts/router_probe/` and `docs/research/judgement/`, and against the golden set. No row equals one of those strings, none is within a `difflib` ratio of 0.9, and none is contained in a longer one. No implementer saw the set. It is kept out of the repository while #295 is open, so that it can still judge #295's rule.

## How it was run

The wording tier (`PROBE_TIER=wording`), through the harness at `44b81c7`. Each commit ran twice, and the two runs agreed every time. The scoring rule is the one in `docs/research/reading-wave-m23-probe.md`. Only counts were read. The measuring seat (the run's coordinator) read no question from the set.

## Results

| Commit | What | Right of 173 | Searches right of 112 | Not measured | Non-searches caught of 61 | Against its base |
|---|---|---:|---:|---:|---:|---|
| `58e9f21` | the shipped rule | 81 | 68 | 4 | 13 | -- |
| `89eefee` | #293: example sentences for search, factuality and assistant | 81 | 68 | 4 | 13 | 0 gained, 0 lost, 3 moved between wrong surfaces |
| `ab82d5c` | #292: an agent with its own coding verb (on #293) | 82 | 69 | 4 | 13 | 1 gained, 0 lost, 1 moved |

- **#293 ships.** It loses no row, and both of its golden questions pass.
- **#292 ships.** It gains a search, loses none, and its golden question passes.
- **#295 is stopped** before a rule was committed. The owner's design default could not fix the golden question without moving general Turkish "yapay zeka" questions off everyday (see #295 and the run file's Stops).

## #295, measured after the owner's ruling (D-208)

The owner chose option (a) on 2026-10-17. The rule was measured on the same set by a measuring seat that did not write it, with the wording tier and `fe35bc3`'s harness, each commit run twice (byte-identical runs). The implementer saw counts and surface ids only.

| Commit | What | Right of 173 | Searches right of 112 | Not measured | Non-searches caught of 61 | Against its base |
|---|---|---:|---:|---:|---:|---|
| `fe35bc3` | main, with #293 and #292 | 82 | 69 | 4 | 13 | -- |
| `afab5ec` | #295: a verb clause before "yapay zeka" names the task | 83 | 70 | 4 | 13 | 1 gained, 0 lost, 3 moved between wrong surfaces |

- **#295 ships.** It loses no row and gains a `computer-use` search, and its golden question passes (41 of 41 asserted).
