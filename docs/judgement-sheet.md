---
record_type: register
id: judgement-sheet
status: draft
process_version: v6.6
date: 2026-10-09
---
# The owner's judgement sheet: is our list the better answer? (#226, D-188's revisit)

D-188 makes our own family list the default answer. No board can say whether it is the better answer
than the primary board's own, so the owner judges a sample. D-188 is revisited when he prefers the
primary board's answer on more questions than ours (`scripts/judgement_sheet.py`, `revisit`).

**What the sheet holds.** Per question, two lists, A and B: our family list's first five, as the screen
shows it, and the primary board's own first five. A seeded coin chose which is A; the sheet does not
say. A question the screen answers with one board's cards is left out: there is nothing to compare.

**Steps** (about 15 minutes; the agent can do steps 1 and 2 and hand you the sheet):

1. **The rows**, from the hosted engine's answers and the questions in
   `docs/research/judgement/questions.json` (20, written for this sheet; replace them with your own if
   you like). In a scratch copy of `ios/`, with `scripts/router_probe/JudgementProbe.swift` in its
   `EngineTests/`:
   ```
   curl -s https://model-ranking.fly.dev/v1/categories > /tmp/categories.json
   curl -s https://model-ranking.fly.dev/v1/boards > /tmp/boards.json
   JUDGE_QUESTIONS=$PWD/docs/research/judgement/questions.json JUDGE_CATEGORIES=/tmp/categories.json \
   JUDGE_BOARDS=/tmp/boards.json JUDGE_OUT=/tmp/rows.json swift test --filter JudgementProbe
   ```
2. **The sheet:** `.venv/bin/python scripts/judgement_sheet.py make --probe /tmp/rows.json --sheet
   docs/research/judgement/sheet.csv --key docs/research/judgement/key.json --seed 2026`. Do not open
   the key.
3. **Judge:** open `sheet.csv`. In `choice`, write A, B or `same` for the list you would use for that
   question; `note` is free. Leave a row blank to skip it.
4. **Score:** `.venv/bin/python scripts/judgement_sheet.py score --sheet docs/research/judgement/sheet.csv
   --key docs/research/judgement/key.json`. It prints how many times ours, the primary board's or neither
   was preferred, and `revisit`: whether D-188 is to be revisited.
