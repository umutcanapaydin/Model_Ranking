---
record_type: review
id: fix-issue-17-tester
status: draft
process_version: v6.6
date: 2026-09-24
seat: independent
---

# Issue #17 Tester Review (fix-issue)

**Reviewer:** Tester subagent (fresh eyes; did not write the fix or its tests)
**Independent:** yes
**Date:** 2026-09-24
**Commit range:** `main..fix/issue-17-trailer-and-undated-close` = `b4d9b54` (red tests) + `e0fc426` (fix), base `main` = `b7f3577`
**Risk tier:** LOW (triage: fix-issue, severity low)
**Policy read from:** `git show main:.claude/agents/Tester.md` (protected base)
**Workspace:** a scratch clone of the branch, with `make install`, and `advisor.db` copied in read-only (md5 unchanged before and after). Nothing committed.

## Verdict

**PASS WITH FINDINGS.** Both halves of #17 are fixed. The red commit fails for the reasons the issue gives, and HEAD is green. Each acceptance criterion has a test that cites it. 8 of 10 mutants are killed by the branch's own tests. `make check-fast` and `make check` both exit 0. No real commit and no historical wave close changes result.

Nothing blocks. MAJOR-1 is a fail-closed trap: the repository's own habit of writing trailers is now a violation for the machine identity. M1 to M3 are gaps next to the criteria: one untested polarity and two date shapes that still escape. Each should be fixed on this branch or filed as an issue.

## Acceptance-criterion coverage

| Criterion (issue #17) | Citing test | Asserts | Result |
|---|---|---|---|
| (1) `GP-Agent` is read as a git trailer, not a substring: a machine commit that only mentions `GP-Agent:` in its body is refused | `tests/unit/test_wave_check_versions.py:135` `test_a_trailer_is_read_as_a_trailer_not_a_substring` (docstring `#17 (1)`) | exit 1 and the message `no \`GP-Agent:\` trailer`, for a body that mentions `GP-Agent:` in a middle paragraph and ends in a trailer block without it (`Reviewed-by: nobody`) | GREEN at HEAD |
| (1, other polarity) a real trailer still passes | `tests/unit/test_wave_check_versions.py:85` `test_the_trailer_check_on_agent_commits_holds_in_the_gate` (runs `--self-test`: case a must stay quiet, case k must fire) | the self-test passes, 11 cases, 0 wrong | GREEN |
| (2) a close with no date is not assumed old: it is graded, or refused as out of scope | `tests/unit/test_wave_check_versions.py:108` `test_a_close_with_no_version_and_no_date_is_graded_not_skipped` (docstring `#17 (2)`) | no longer "0 validated / 1 pre-migration"; either exit != 0 or the record is validated | GREEN at HEAD |

## Red to green on the reported symptoms

The red commit was replayed with a `git archive b4d9b54` export and the clone's venv:

- `test_a_close_with_no_version_and_no_date_is_graded_not_skipped` FAILED: `wave-check-all PASS: 0 v5.0-or-later record(s) validated; 1 pre-migration record(s) out of scope`. This is the symptom in the issue.
- `test_a_trailer_is_read_as_a_trailer_not_a_substring` FAILED: `assert 0 == 1`, `test-commit-identity PASS: 2 commit(s), 0 violation(s)`. This is the symptom in the issue.
- Red commit: 2 failed, 12 passed. HEAD: 14 passed, in the same file.

## Findings

### MAJOR-1: this repository's usual trailer layout is not a git trailer, and the machine identity is now refused for it

- **Where:** `conformance/test-commit-identity.py:237-238` and `:269`; the convention is stated in `AGENTS.md:42` and `.github/workflows/issue-agent.yml:92`.
- **What:** git reads trailers only from the message's final paragraph. It also refuses a block that mixes trailers with prose unless the block has a git-generated trailer. I scanned every commit in the clone (`git log --all`): 220 have `GP-Agent:` in the body, and for **113** of them git finds no `GP-Agent` trailer. They use `GP-Agent: x` + blank line + `GP-Task: y`, or a `Co-Authored-By` paragraph after the trailers. Recent examples on `main`: `b569de5`, `9207f33`, `96778b0`, `e973a05` (the v6.4 upgrade), and all of M16/M17. None of them uses the machine identity, so today's gate is unaffected (`machine-identity=0` in history). However, AGENTS.md calls these lines "trailers" without saying where they must go.
- **Failure scenario:** the CI issue agent, or any automation committing as `gp-agent@users.noreply.github.com`, writes the message the way 113 of this repository's commits do: `GP-Agent: issue-agent ...`, a blank line, then `GP-Task: #N`. Its draft PR's gate then fails with "machine identity with no `GP-Agent:` trailer", even though the line is visibly in the message. The check fails closed (it refuses rather than lets through), but the message misleads, and it points at a rule no document states.
- **Suggested fix:** say "in the final trailer block (git interpret-trailers)" in the failure message and in `AGENTS.md:42` / `.agents/rules/git-authority.md:18`. Optionally, add a self-test case for the `GP-Agent` / blank line / `GP-Task` shape, so the choice is pinned either way.

### M1: an empty `GP-Agent:` value is refused, but no test pins it (mutants MB and MC survive)

- **Where:** `conformance/test-commit-identity.py:269` (`not trailer.strip()`) and `:237` (`valueonly`).
- **What:** at HEAD, `GP-Agent:` with no value (or only spaces) in the final block is correctly refused (probe: exit 1). The branch's tests do not notice when this is lost. Changing `not trailer.strip()` to `not trailer`, or dropping `valueonly`, leaves all 14 tests green. With either mutant, a machine commit whose trailer names no agent passes, which breaks "an agent commit must say which agent made it".
- **Fix:** add the parametrised test `test_an_empty_trailer_value_names_no_agent` shown below. It kills both mutants.

### M2: an empty `date:` line is still read as pre-migration, depending on its position

- **Where:** `scripts/wave_check_all.py:52` (`^{field}:\s*(\S+)\s*$`) and `:80`/`:86`.
- **What:** `\s*` also matches the newline. For a record whose last frontmatter line is an empty `date:`, the value read is the closing `---`, and `"---" < "2026-08-16"`, so the record is filed as pre-migration: `wave-check-all PASS: 0 ... validated; 1 pre-migration record(s) out of scope`. The same empty `date:` followed by `status: draft` reads `"status:"`, sorts after the migration date and is refused. The outcome depends on which line follows, not on the record.
- **Failure scenario:** a template leaves `date:` blank as the last frontmatter field, and the close escapes the gate. That is the issue's criterion 2 ("a close with no date is not assumed old") through a different door.
- **Fix:** use `[ \t]*` instead of `\s*` in `_front`, and/or require `date` to match `\d{4}-\d{2}-\d{2}` before comparing, treating anything else as undated. The seat test `test_an_empty_date_line_is_no_date` below is RED at HEAD.

### M3: a quoted date is filed as pre-migration (this gap was already on `main`, and it sits next to #17)

- **Where:** `scripts/wave_check_all.py:80,86`.
- **What:** `date: "2026-10-01"` or `date: '2026-10-01'` is compared as a string that starts with a quote character. The quote sorts before `2`, so a close dated after the migration is reported as pre-migration and never graded. `main` behaves the same. No real close is quoted today: all 63 carry an unquoted date.
- **Fix:** the same one as M2: parse the date (strip quotes, match `YYYY-MM-DD`) and treat a value that does not parse as undated.

### NIT-1: on a git too old for `valueonly`, the check lets everything through

- **Where:** `conformance/test-commit-identity.py:237`.
- **What:** git prints a `%(trailers:...)` placeholder with an option it does not recognise as literal text. This was verified on git 2.50 with `%(trailers:key=GP-Agent,bogusopt)`. On a git older than `valueonly` (about 2.22), every machine commit would therefore have a non-empty "trailer" and pass. This is unlikely on current runners.
- **Fix:** treat a value that starts with `%(trailers` as CANNOT RUN.

### NIT-2: a message whose only paragraph is `GP-Agent: x` is refused

- **Where:** `conformance/test-commit-identity.py:237`.
- **What:** git never reads the first paragraph (the subject) as trailers. `GP-Agent: x` alone, with or without a trailing newline, therefore has no trailer, and the commit is refused (exit 1). On `main` it passed. The same happens to a final block such as `GP-Agent: x` followed by a prose line without a git-generated trailer. A final block that does include `Signed-off-by` is accepted.
- **Does it matter:** no. The check fails closed, and a real agent commit has a subject line. The behaviour is recorded here so nobody takes it for a bug later. The characterisation test `test_a_message_that_is_only_the_trailer_line_has_no_trailer` is below.

### NIT-3: the date test asserts through a disjunction and never checks the wording

- **Where:** `tests/unit/test_wave_check_versions.py:130-132`.
- **What:** `code != 0 or "1 v5.0-or-later ... validated"` accepts either outcome, which suits the issue's "graded or refused". However, it leaves the new `undated` wording (`scripts/wave_check_all.py:90`) untested, and mutants MI (undated sent to `in_scope`) and MJ (wording dropped) survive. Asserting `code == 1 and "is undated and declares" in out` pins the branch the fix actually chose.

### NIT-4: the review file name differs from the profile

- The base profile names a fix's verdict file `docs/reviews/fix-issue-<n>-tester.md`. This file is named `issue-17-tester.md` because the dispatcher asked for that name. If `/pre-merge` looks for the verdict by the profile's name, rename the file.

## Mutants (in place, restored by string replacement, md5 confirmed after each)

The md5 of both source files before and after the whole run was `6198f671…` (`conformance/test-commit-identity.py`) and `9d2f3b1e…` (`scripts/wave_check_all.py`); no git checkout or restore was used. The "branch tests" column is `tests/unit/test_wave_check_versions.py` as shipped. The "with seat tests" column adds the probe file below.

| id | mutation (changed line) | branch tests | with seat tests |
|---|---|---|---|
| MA | `:269` → old `AGENT_TRAILER not in body` (a trailer in a middle paragraph counts again) | KILLED (`test_a_trailer_is_read_as_a_trailer_not_a_substring`) | KILLED |
| MB | `:269` `not trailer.strip()` → `not trailer` (empty value `GP-Agent:` passes) | **SURVIVED** | KILLED (`test_an_empty_trailer_value_names_no_agent`) |
| MC | `:237` drop `valueonly` (key text makes an empty value non-empty) | **SURVIVED** | KILLED |
| MD | `:247` swap the `trailer` and `body` fields | KILLED (2 tests) | KILLED |
| ME | `:237` key `GP-Agentx` (a real final-block trailer is not seen) | KILLED (self-test, case a) | KILLED |
| MF | `:269` inverted guard | KILLED (2 tests) | KILLED |
| MG | `wave_check_all.py:86` → old `elif date > MIGRATION_DATE` (the date test) | KILLED (`test_a_close_with_no_version_and_no_date_is_graded_not_skipped`) | KILLED |
| MH | `:86` `not date` → `date is None` (never true) | KILLED | KILLED |
| MI | undated sent to `in_scope` instead of refused | SURVIVED (equivalent under "graded or refused") | KILLED (`test_an_undated_close_is_named_undated`) |
| MJ | `:90` drop the `undated` wording | SURVIVED (cosmetic) | KILLED |

Behaviour probes run against the HEAD script. Each is a machine-identity commit on a branch; exit 1 means refused.

| message shape | git's `GP-Agent` trailer | exit |
|---|---|---|
| subject, blank line, `GP-Agent: x` (final block) | `x` | 0 |
| `GP-Agent: x` in a middle paragraph, then a prose paragraph | none | 1 |
| `GP-Agent: x` in a middle paragraph, then `Reviewed-by: y` | none | 1 |
| `GP-Agent:` with an empty value (also only spaces) | empty | 1 |
| only paragraph `GP-Agent: x` (with or without a trailing blank line) | none (the subject is never read as trailers) | 1 |
| `GP-Agent: x` followed by a prose line in the final block | none | 1 |
| the same with a `Signed-off-by` in the block | `x` | 0 |
| `gp-agent: x` (lower case) / `GP-Agent : x` | `x` | 0 |
| `GP-Agent-Extra: x` / `GP-Agent=x` | none | 1 |

Date probes, `wave_check_all.main()` run on a one-record tree. The main column uses `main`'s script.

| frontmatter | HEAD | main |
|---|---|---|
| no `date:`, no `process_version:` | exit 1, "undated" | exit 0, pre-migration |
| no frontmatter at all | exit 1 | exit 0 |
| `date:` empty, last line before `---` | **exit 0, pre-migration** (M2) | exit 0 |
| `date:` empty, followed by `status:` | exit 1 | exit 0 |
| `date: "2026-10-01"` / `'2026-10-01'` | **exit 0, pre-migration** (M3) | exit 0 |
| `date: TBD` | exit 1 | exit 1 |
| `date: 2026-08-01` / `2026-08-16` | exit 0, pre-migration (as intended) | same |

## No regression

- `test-commit-identity` at HEAD: `PASS: 200 commit(s), 0 violation(s)`, with scope `main..HEAD` = 2 commits. With `--range main~50..HEAD`: `PASS: 143 commit(s), 0 violation(s)`. The branch's own two commits carry `GP-Agent` / `GP-Task` in a final trailer block, and git reads them.
- Full-history scan: 290 commits, 0 under the machine identity, so the change of rule flags no real commit. 113 of them would not count as having the trailer if they had been machine commits (MAJOR-1).
- `make wave-check-all` at HEAD: exit 0, `43 v5.0-or-later record(s) validated; 20 pre-migration record(s) out of scope`. `main`'s script on the same tree gives the same 43/20. No historical close moves in or out of scope, and every one of the 63 closes has an unquoted `date:`.

## Gate results (clone at `e0fc426`)

| gate | exit | counts |
|---|---|---|
| `make check-fast` | 0 | 6 legs PASS (lint, typecheck, records, test, client-decls, swift-test); `check-fast PASS in 80.7s` |
| `make check` | 0 | pytest `1224 passed, 15 skipped`, coverage 90.28% (floor 60%), `coverage-floor PASS: 36 module(s)`; `wave-check-all PASS` 43/20; `conformance PASS: 16 test(s)`, including `test-commit-identity PASS: 200 commit(s), 0 violation(s)`; `swift-test PASS: 268 test(s)`; `client-decls PASS` |
| `test-commit-identity --self-test` | 0 | 11 cases, 0 wrong |
| `tests/unit/test_wave_check_versions.py` | 0 | 14 passed (red commit: 2 failed, 12 passed) |

Coverage on touched code: the two touched scripts sit outside the `src/` coverage measure. Their changed lines are covered by the subprocess and in-process tests above, as the mutant table shows.

## Weakened or deleted tests

None. The diff to `tests/` only adds lines (+58, -0). The self-test cases are unchanged. Case c ("ai") has `GP-Agent:` in a middle paragraph, so it now also lacks the trailer, but it still fails for its intended reason: the attribution check fires.

## Tests added or extended by this review (seat probes, NOT committed)

These are in the seat's scratch file `test_seat17.py`, run against the clone. At HEAD: 6 pass, 1 is RED (M2). The author may adopt them:

- `test_an_empty_trailer_value_names_no_agent` (parametrised: `GP-Agent:` and `GP-Agent:   `). Criterion (1), M1; kills MB and MC.
- `test_a_trailer_in_a_middle_paragraph_is_not_the_trailer_block`: criterion (1).
- `test_a_trailer_in_the_final_block_among_others_passes`: criterion (1), the quiet polarity.
- `test_a_message_that_is_only_the_trailer_line_has_no_trailer`: NIT-2, a characterisation test.
- `test_an_undated_close_is_named_undated`: criterion (2), NIT-3; kills MI and MJ.
- `test_an_empty_date_line_is_no_date`: M2, **RED at HEAD**.

The core of the helper, for adoption:

```python
def _identity(tmp_path, message):  # a machine commit on work/1 over an owner commit on main
    ...
    git("commit", "-q", "--cleanup=verbatim", "-F", str(tmp_path / "msg"),
        email="gp-agent@users.noreply.github.com")
    return subprocess.run([sys.executable, str(ROOT / "conformance/test-commit-identity.py"),
                           "--owner-email", "o@x"], cwd=repo, capture_output=True,
                          encoding="utf-8", env=base, check=False)

@pytest.mark.parametrize("message", ["agent\n\nGP-Agent:\n", "agent\n\nGP-Agent:   \n"])
def test_an_empty_trailer_value_names_no_agent(tmp_path, message):
    r = _identity(tmp_path, message)
    assert r.returncode == 1 and "no `GP-Agent:` trailer" in r.stdout, r.stdout

def test_an_empty_date_line_is_no_date(tmp_path):
    code, out = _wca(tmp_path, "---\nrecord_type: wave\nstatus: draft\ndate:\n---\n# x\n")
    assert "pre-migration record(s) out of scope" not in out or "0 pre-migration" in out, out
```

## BLOCKING

- none

## MINOR (the author fixes each on this branch or files it as an issue)

- **M1** `conformance/test-commit-identity.py:269`: the empty-value trailer is not pinned by a test (MB and MC survive).
- **M2** `scripts/wave_check_all.py:52,86`: an empty `date:` as the last frontmatter line is still filed as pre-migration.
- **M3** `scripts/wave_check_all.py:80,86`: a quoted date is filed as pre-migration (the gap was already on `main`).
