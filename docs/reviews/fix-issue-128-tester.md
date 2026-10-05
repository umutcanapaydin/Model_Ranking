---
record_type: review
id: fix-issue-128-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Issue 128 independent Tester review

**Reviewer:** Tester, a separate session; wrote none of the fix or its test.
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** 0198eb3..b971e57 (`bc4d71f` red test, `b971e57` fix).
**Risk tier:** LOW (test data for an out-of-band probe; the issue's impact is the probe's score only).

**Method.** Profile, `AGENTS.md` and `.agents/rules/issues.md` read from the base `0198eb3`. The
acceptance criterion is the issue body: the off-topic sets' knowledge questions (everyday trivia
outside every measured area, D-169 and REQ-ASK-005) are labelled `NOT_A_SEARCH`, so a probe no longer
counts the right answer as a miss, with each relabel listed in its commit. D-169 and REQ-ASK-005 were
read at the base; the retired M17 not-a-search set (`notasearch_m17_heldout_questions.json`, a tuning
set now) was read for how the project labels its own knowledge questions. No live held-out set was
opened. Red: the two base set files (`git show 0198eb3:<path>`) written in place under the red
commit's test (the test file is identical at `bc4d71f` and `b971e57`), run, original bytes written
back. Gate: `make check-fast` at the head. Faults: one exact unique replacement per mutant, the
original bytes written back and the sha256 compared. `probe.swift` was not run: it loads an
on-device embedding with `try!` and may fetch its assets, so it could crash or reach the network.

## Verdict
MINOR

The three relabels are right and pinned, and the commit lists each one, as the issue asks. The issue's
promise, that the probe no longer counts these rows as misses, also rests on `probe.swift` leaving the
rows out of its score's denominator, and nothing holds that: with the denominator back on every row,
the suite stays green while the issue's symptom returns (M7). The missing test is written below. Two
rows left as they are look like the same class as the relabelled ones (R1); the author decides.

## Acceptance-criterion coverage
- "what is the capital of france", "who won the world cup in 2022" (`offtopic_questions.json`) and
  "who wrote the odyssey" (`offtopic_heldout_questions.json`) are `NOT_A_SEARCH` and nothing else:
  `tests/unit/test_ios_client_contract.py:1405`
  (`test_knowledge_questions_in_the_off_topic_sets_are_not_searches`) (M1, M2, M3, M8, M9 killed).
- `probe.swift` skips a `NOT_A_SEARCH` row: `tests/unit/test_ios_client_contract.py:1385`, the #118
  test (M6 killed). Left out of the score's denominator: only T1's test (below).
- Each relabel listed in its commit: `b971e57`'s message names the three, and names the rows left
  with a reason.
- Red to green: on the base sets the red test fails on the symptom,
  `AssertionError: what is the capital of france` with the label `['assistant|everyday~']`; it
  passes at `b971e57`.
- The held-out leak gate still passes with the three questions now written into a test: both
  off-topic sets are on its retired list, and no live set holds them (check-fast's test leg).

## Suite result
- `make check-fast` at `b971e57`: PASS in 79.8s, six legs; test leg 1797 passed, 25 skipped; swift
  leg 462 tests.

## Mutants

| ID | Fault | Run | Result |
|---|---|---|---|
| M1 | "what is the capital of france" back to `assistant\|everyday~` | contract file | KILLED (`test_knowledge_questions_..._not_searches`) |
| M2 | "who wrote the odyssey" back to `assistant\|everyday~` (held-out set) | contract file | KILLED (same) |
| M3 | "who won the world cup in 2022" as `NOT_A_SEARCH\|assistant\|everyday~`, which `probe.swift` would score as a surface | contract file | KILLED (same) |
| M4 | a fourth trivia row, "who painted the mona lisa", added as `assistant\|everyday~` | whole suite | SURVIVED (R2) |
| M5 | a row left as it is, "how long does it take to walk 10 km", relabelled `search\|assistant\|everyday~` | whole suite | SURVIVED (R2) |
| M6 | `probe.swift`'s `if want == "NOT_A_SEARCH" { unscored += 1; continue }` removed | contract file | KILLED (#118 test) |
| M7 | `probe.swift` prints `pass/cases.count`: the skipped row counted as a miss again | whole suite | SURVIVED; KILLED by T1's test |
| M8 | a second "what is the capital of france" row expecting a surface | contract file | KILLED (`test_knowledge_questions_..._not_searches`) |
| M9 | the relabelled question's text changed ("France") | contract file | KILLED (same) |

"Contract file" is `tests/unit/test_ios_client_contract.py`; "whole suite" is `pytest -n auto` with
the artifact required (1797 passed, 25 skipped on each survivor). As committed: 6 of 9 killed; with
T1's test, 7 of 9.

## Findings
- **T1** Nothing holds the score's denominator. The issue's symptom is a probe counting the right
  answer as a miss; the fix relabels the rows and relies on `probe.swift`, which the #118 test pins
  only at the `continue`. With the printed score over `cases.count` (M7) each `NOT_A_SEARCH` row is a
  miss again and the suite stays green. Written this review and appended to
  `tests/unit/test_ios_client_contract.py`: RED on M7
  (`assert ['cases.count'] == ['cases.count-unscored']`), GREEN at `b971e57`; `ruff check` clean.
  It reads the script's text, as the #118 test does, because the script is never built or run by the
  suite. Removed again so the worktree holds only this record; the author adds it to the branch.
  Full text:

```python
def test_the_probe_leaves_a_not_a_search_row_out_of_its_score() -> None:
    """#128 (the fix Tester's T1): the relabelled rows stop counting as misses only if `probe.swift`
    leaves them out of the score's denominator as well as its pass count. With the printed score
    over `cases.count`, each NOT_A_SEARCH row was a miss again, the issue's symptom, and the suite
    stayed green: the #118 test pins only the `continue`."""
    probe = (CLIENT.parents[1] / "scripts/router_probe/probe.swift").read_text(encoding="utf-8")
    score = re.findall(r'print\("\\\(pass\)/\\\(([^)]*)\)"', probe)
    assert score, "probe.swift prints no score"
    assert [part.replace(" ", "") for part in score] == ["cases.count-unscored"], (
        f"probe.swift's score is not over the scored rows only: {score}"
    )
```

- **R1** Two rows left as they are read as knowledge questions by the project's own labels. The
  retired M17 not-a-search set labels "how many bones does an adult human have" `NOT_A_SEARCH` and
  "what's the difference between a virus and a bacterium" `NOT_A_SEARCH|expert`; the off-topic sets
  keep "how long does it take to walk 10 km" and "what is the difference between rent and lease" as
  `assistant|everyday~`. The commit's reason for keeping them, that a model may be asked for them,
  holds for the three it relabelled too. The author either relabels them (and adds them to the
  pin) or states the line between the two groups in the pull request. Probe score only; not
  blocking.
- **R2** M4 and M5 survive by design: the rows are pinned by name, and which question is everyday
  trivia is a judgement no rule derives, so a row added or relabelled later is caught only by a
  reader. No test asked.

## Clean-up evidence
- Every mutant and the red run: original bytes written back and sha256 compared
  (`offtopic_questions.json` 4ef09d172d03..., `offtopic_heldout_questions.json` b0fc996b7c6d...,
  `probe.swift` 23cf445f10b9..., `test_ios_client_contract.py` d176803385a1...). No
  mismatch.
- `git hash-object` equals `HEAD:<path>` for each of those four files and
  `tests/unit/test_ios_client_contract.py`. No checkout, restore, stash, reset or commit.
  `git status --short` lists only this record.

## Dispositions, at the fix

Written by the author after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| T1 | fixed: the seat's `test_the_probe_leaves_a_not_a_search_row_out_of_its_score`, committed as written |
| R1 | refused: the three relabelled rows each ask for one settled fact (a capital, a winner, an author). "How long does it take to walk 10 km" asks for an estimate and "the difference between rent and lease" for an explanation, nearer the advice and how-to rows the sets keep as searches. D-169 names knowledge questions without drawing this line; #66 stays open for knowledge questions, and the line belongs there |
| R2 | accepted as the issue's scope: the test names the relabelled rows, as #118's did |
