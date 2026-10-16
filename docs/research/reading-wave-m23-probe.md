# The #273 and #218 reading rules, measured on the fresh set reading_heldout_m23

**Measured 2026-10-16** on the owner's Mac (Swift 6.3.3, no Apple Intelligence used) by the measuring
seat (D-202 clause 6, D-191, D-196). This seat wrote neither rule and reviewed neither. It ran and
scored only. The wording tier was measured through the base commit's
`scripts/router_probe/ReadingProbe.swift` (`PROBE_TIER=wording`) in `git archive` copies of each
commit's `ios/`, kept in a temporary directory outside any repository. So all three commits were read
by the same harness.

| name | commit | what it is |
|---|---|---|
| base | `44b81c7` | the shipped rule |
| #273 | `0f7d57a` | an unsure non-English reading declines unless English is among its readings |
| #218 | `1e59068` | stacked on #273 (`1e59068~2` = `0f7d57a`): a short Turkish question that names a model is read as Turkish |

## 1. The set

`scripts/router_probe/reading_heldout_m23_questions.json` (kept out of the repository until #66 and #301 were measured; provenance: `docs/research/reading-heldout-m23-set.md`) was written on 2026-10-16 by an independent seat: a subagent
dispatched only to write this set. It read no routing code or examples (its README lists what it did
read). Neither rule's implementer has seen it. It holds 168 rows: 96 searches and 72 lines that are not
a search. Labels are a surface, `a|b`, or `NOT_A_SEARCH`. No question equals or nearly equals any
string in `scripts/router_probe/` or `docs/research/judgement/` (the set's README).

**Language per row.** The set has no language column. The language was taken from the set's README
and the set's block order: searches first, then the lines that are not a search, and within each block
English, Turkish, Spanish, German, French, Portuguese, Kurmanji, Azerbaijani, Russian (Cyrillic),
Russian (Latin letters), Arabic, and then the one keyboard-mash row. A helper outside the repository
checked that these row ranges give exactly the README's count for each language and kind. It also
checked that a separate script-and-lexicon tagger agrees with the ranges: the tagger contradicted the
ranges on 1 row, a Portuguese line it read as Spanish. Run rows were matched to set rows by question
text. The helper printed counts and row numbers only.

Groups below: English (36 searches, 24 not a search), Turkish (37, 26), and other (23, 22: every
other language, plus the keyboard-mash row).

## 2. Counts

Each commit was run twice. **For each commit, the two runs are byte-identical**
(`cmp base-1 base-2`, `273-1 273-2`, `218-1 218-2`). The scorer is score_heldout.py (the measuring seat's scorer, outside the repository) (counts only),
with base first.

| commit, run | right (168) | searches right (96) | searches not measured (96) | searches asked (96) | not a search caught (72) | vs base: gained, lost, moved |
|---|---:|---:|---:|---:|---:|---|
| base 1 and 2 | 75, 75 | 65, 65 | 15, 15 | 0, 0 | 10, 10 | — |
| #273 1 and 2 | 75, 75 | 65, 65 | 16, 16 | 0, 0 | 10, 10 | 0, 0, 5 |
| #218 1 and 2 | 75, 75 | 65, 65 | 16, 16 | 0, 0 | 10, 10 | 0, 0, 6 |

Against #273, #218 gained 0 rows, lost 0, and moved 1.

## 3. By language

The same in both runs.

| group | count | n | base | #273 | #218 |
|---|---|---:|---:|---:|---:|
| English | searches right | 36 | 29 | 29 | 29 |
| English | searches not measured | 36 | 0 | 0 | 0 |
| English | not a search caught | 24 | 3 | 3 | 3 |
| Turkish | searches right | 37 | 30 | 30 | 30 |
| Turkish | searches not measured | 37 | 0 | 0 | 0 |
| Turkish | not a search caught | 26 | 6 | 6 | 6 |
| other | searches right | 23 | 6 | 6 | 6 |
| other | searches not measured | 23 | 15 | 16 | 16 |
| other | not a search caught | 22 | 1 | 1 | 1 |

Turkish searches of five words or fewer (20 of the 37, which is #218's target): 17 right on every
commit.

## 4. Rows gained, lost and moved

**No row was gained or lost**, by either rule, against either comparison. The rows that moved, by
category (row numbers in the set):

**base -> #273 (5 rows):**
- **Searches (1).** A Kurmanji search labelled `assistant` (row 85) went from `expert` (wrong) to
  "not measured" (still wrong).
- **Not a search (4).** These lines went from a ranking to "not measured" on `assistant`: one English
  (row 115, `everyday` before), two Kurmanji (rows 157 and 158, `mathematics` and `expert` before) and
  one Russian in Latin letters (row 163, `web-dev` before). The reading still reads each as a search,
  so none counts as caught. They are not ranked now, but the ship rule does not count that.

**#273 -> #218 (1 row):**
- **Not a search (1).** A three-word Turkish line (row 120) moved from `factuality` to `everyday`. It
  is still read as a search and still ranked, so it is uncaught before and after.

No Turkish search moved under #218. No English search moved under either rule.

## 5. Verdict (D-202 clause 6)

The ship rule: searches right goes up or stays equal, not-a-search caught goes up or stays equal, at
least one of the two goes up, and no language group loses more than one search.

- **#273 against base: DO NOT SHIP.** Searches right stays at 65 and not-a-search caught stays at 10.
  Neither goes up, so it does not beat the shipped rule. It loses no search in any group. Its only
  effect on this set is to stop ranking 4 lines that are not a search and 1 Kurmanji search that was
  already wrong.
- **#218 against #273: DO NOT SHIP.** Searches right stays at 65 and caught stays at 10. Its one moved
  row is a line that is not a search, moving between two wrong surfaces. The short Turkish searches
  it targets are 17 of 20 right on both commits.
- **#218 against base: DO NOT SHIP.** It is the same as #273 against base, plus that one row: 65 and 10
  on both commits, no gain and no loss.

What stays open: on this set the wording tier catches 10 of 72 lines that are not a search (3 of the 24
English lines, 6 of the 26 Turkish lines, 1 of the 22 in other languages; #66). It also leaves 15 or 16
of the 23 searches in other languages not measured. The implementer's tuning-set gains for #218 (short
Turkish 39 -> 41) did not appear on fresh rows.

This record quotes no question from the set, which stays held out for later waves.
