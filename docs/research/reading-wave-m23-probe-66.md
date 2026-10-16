# The #66 reading rule, measured on the fresh set reading_heldout_m23

**Measured 2026-10-16** on the owner's Mac (Swift 6.3.3, no Apple Intelligence used) by the measuring
seat (D-202 clause 6, D-191, D-196). This seat wrote no rule and reviewed none. It ran and scored only.
The method is the one in reading-wave-m23-probe.md (on integration/run-product-night), beside this file:
- the wording tier, through `44b81c7`'s `scripts/router_probe/ReadingProbe.swift` (`PROBE_TIER=wording`);
- `git archive` copies of each commit's `ios/`, kept in a temporary directory outside any repository;
- two runs per commit, scored by score_heldout.py (the measuring seat's scorer, outside the repository) with base first;
- the same per-language helper, which matches rows by question text.

| name | commit | what it is |
|---|---|---|
| base | `5e881d8` | the integration head #66 was cut from. `git diff 44b81c7 5e881d8 -- ios` is empty |
| #66 | `7b13095` | the wording tier holds more chit-chat, text with no meaning, and a dictated answer (`Reading.swift`, `Router.swift`, tests) |

## 1. The set

reading_heldout_m23_questions.json was written on 2026-10-16 by an independent seat that read no
routing code (its README). Neither rule's implementer has seen it. It holds 168 rows: 96 searches and
72 lines that are not a search. The language of each row comes from the README's counts and the set's
block order, as in the first record. The groups are English (36 searches, 24 not a search), Turkish
(37, 26) and other (23, 22). This set has now been read by one earlier measurement (#273 and #218)
and by no implementer.

## 2. Counts

**For each commit, the two runs are byte-identical** (`cmp`). Base reproduces `44b81c7`'s counts
exactly.

| commit, run | right (168) | searches right (96) | searches not measured | searches asked | not a search caught (72) | vs base: gained, lost, moved |
|---|---:|---:|---:|---:|---:|---|
| base 1 and 2 | 75, 75 | 65, 65 | 15, 15 | 0, 0 | 10, 10 | — |
| #66 1 and 2 | 76, 76 | 65, 65 | 15, 15 | 0, 0 | 11, 11 | 1, 0, 1 |

How each run read the 96 searches and the 72 other lines:
- **Searches.** Base and #66 both read all 96 as a search. None is held as not a search, and none is
  asked.
- **Not a search, base.** 62 are read as a search, 8 are asked and 2 are held.
- **Not a search, #66.** 61 are read as a search, 8 are asked and 3 are held.

## 3. By language

The same in both runs.

| group | count | n | base | #66 |
|---|---|---:|---:|---:|
| English | searches right | 36 | 29 | 29 |
| English | searches not measured | 36 | 0 | 0 |
| English | not a search caught | 24 | 3 | **4** |
| Turkish | searches right | 37 | 30 | 30 |
| Turkish | searches not measured | 37 | 0 | 0 |
| Turkish | not a search caught | 26 | 6 | 6 |
| other | searches right | 23 | 6 | 6 |
| other | searches not measured | 23 | 15 | 15 |
| other | not a search caught | 22 | 1 | 1 |

## 4. Rows gained, lost and moved

- **Gained (1).** A three-word English line that is not a search (row 104). Base read it as a search
  and ranked it on `search`; #66 holds it as not a search.
- **Lost (0).**
- **Moved (1).** The same row; nothing else moved.

No Turkish row and no row in another language moved. The rule caught no further chit-chat or text
with no meaning in Turkish or the other languages on this set.

## 5. Verdict (D-202 clause 6)

The ship rule:
- not-a-search caught must go up;
- searches right must not go down;
- no language group may lose more than one search;
- no real search may be caught as not a search.

**#66 against base: SHIP.**
- Caught goes from 10 to 11.
- Searches right stays at 65.
- No group loses a search (English 29, Turkish 30, other 6 on both commits).
- All 96 searches are still read as a search on both commits: none is held and none is asked.

The margin is one row of 72, in English only. On fresh rows, the wording tier still ranks 61 of 72
lines that are not a search: 20 of 24 English, 20 of 26 Turkish and 21 of 22 in other languages.
#66's wider goal stays open.

This record quotes no question from the set, which stays held out for later waves.
