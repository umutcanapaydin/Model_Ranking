GPF-003 fixtures (condition 15-1). `finished-tree/` is a completed project whose files contain
`<pkg>`-style NOTATION in fences, comments and a shipped UNIVERSAL ADR — `bootstrap-check` C1/C3 must
report it clean. `unfilled.md` carries a real placeholder on a live content line — it must FAIL.
The v5.0 repair shipped without these two fixtures, which is the only reason it reached the field:
a checker that has never been shown its pass case will eventually fail correct work, and did —
the same finished tree was PASS under v4.3 and BLOCKING under v5.0.
