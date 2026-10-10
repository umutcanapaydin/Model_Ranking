---
record_type: review
id: m21-wave-4-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-10
---
# M21 Wave 4 Code Review, round 3 (the controls)

**Reviewer:** Code-Reviewer subagent, round 3 (fresh eyes; wrote none of the wave and none of rounds 1
and 2). Author and reviewer family: Claude / Claude (fallback: no second family in this lane). Fresh
context: I read rounds 1 and 2, then each of this round's commits with `git show`, then the guard and the
gates in full.
- **The guard** ran only on hook payloads: through the hook command in `.claude/settings.json` (both
  readings, `CLAUDE_PROJECT_DIR` set to the worktree) and through `bash_guard.py` alone. No payload was
  executed.
- **The gates' plants** ran in scratch repositories built with the test file's own helpers, in a scratch
  copy of `scripts/` and the test file, and in a `--shared` scratch clone of the real history.
- **Scope of the guard probing (stated so nobody reads more into this verdict).** This round re-ran
  round 2's probes, the project's own MUST_BLOCK and MUST_ALLOW suite, malformed payloads, size and time
  bounds, and the everyday commands below. It did not add a fresh set of crafted evasion forms beyond
  those. "No bypass found" below means no bypass among those inputs.

Nothing in the worktree changed but this file. The test runs left ignored artefacts (`.coverage`,
`coverage.json`, `__pycache__`); I removed them, and `git status --short --ignored` lists only `.gp/`,
`.venv/` and `advisor.db`, as before.

**Independent:** yes
**Date:** 2026-10-10
**Commit range:** `6a41d35..7b8cee3` (`origin/wave/m21-w3..7b8cee3`, 36 commits, no merges). This round's
commits are `ac4a0c8`, `bd55823`, `36e74fa`, `26b6510`, `e3e5a8a` and `7b8cee3`.
**Risk tier:** HIGH (plan §2 W4; the range changes `.claude/settings.json` and `.claude/hooks/bash_guard.py`)

## Verdict
MINOR

## Round 2's findings, re-run

- **B1: closed.** The whole hook blocks all five commands that round 2 listed (unquoted here-document
  bodies holding `$( )` or backticks), and so does `bash_guard.py` alone. The answer is at
  `.claude/hooks/bash_guard.py:265`, which records whether the delimiter was quoted, and `:244-245`, which
  expands an unquoted body. `cat > f <<EOF⏎built $(date)⏎EOF` is in MUST_ALLOW
  (`conformance/test-hook-claims.py:385`), and the suite passes.
- **M1: closed.** The whole hook blocks all nine forms:
  - two arithmetic forms;
  - `$((…) )`;
  - nested backticks;
  - the brace inside `${ }`;
  - zsh's `always` and `if … {`;
  - the glob qualifier and `${(e)…}`. These two are blocked as Unreadable (`:191`, `:364`).
- **M2: closed.** The whole hook blocks all ten forms: a shell reading `-` or `/dev/stdin`, `--rcfile`, a
  `-c` with no string, `source /dev/stdin`, `tcsh`, `csh`, and `heads/main` both ways.
- **M3: closed.**
  - **Brace words.** `{a,b}` repeated 21 or 30 times, before a guarded command, is blocked in 0.09 s. It
    used to take minutes. `_could_name_guarded` (`:510-515`) no longer enumerates.
  - **Size.** 32 768 characters are allowed and 32 769 are blocked (`:455`). `env` repeated 8000 times
    (32 KB) runs in 0.11 s.
  - **The settings.** `.claude/settings.json:49-50` now carries `timeout: 30` and `onFailure: "block"`.
    I checked both against the installed Claude Code binaries, not the online docs, which I could not
    read offline:
    - 2.1.296 (the current symlink) and 2.1.295 define `timeout` as "Timeout in seconds for this
      specific command".
    - Their command-hook predicate is `e.onFailure==="block"&&e.async!==!0`. A timed-out or failed hook
      is then marked blocked: "timed out; blocking because onFailure is \"block\"".
    - The events on which the key is ignored are `Stop`, `SubagentStop`, `TaskCompleted` and
      `TeammateIdle`. `PreToolUse` is not one of them.
    - 2.1.294 has no `onFailure` at all (R1).
- **M4: closed for the typed end.** An end the author names is refused before any skip
  (`scripts/wave_check.py:453-455`). An unmerged close's `main..main` is read and refused. Both are held
  by `tests/unit/test_wave_check_m21_rules.py:460` and `:471`. The pin raises a new gap in the other
  direction (M1 below).
- **M5: closed.**
  - `-G` reads the heading in each spelling (`:494-498`).
  - A1 reads the field in any case (`scripts/check_records.py:1544`).
  - D-138 carries D-160's pointer (`docs/decisions.md:1719`).
  - Held by `:482` and `:495`.
- **M6: closed.**
  - The session field is read from row 8's evidence cell, and both answers together are refused
    (`:578-583`).
  - N/A rows count, and the label's three other spellings are read (`:561`, `:571`).
  - Held by `:502` and `:511`.
- **M7: closed as far as the tests reach.** `scripts/watchdog.py` lists the tree with `pgrep -P`, sends
  SIGINT to each group, then after 3 s sends SIGKILL. It sends no abort. The grandchild and Ctrl-C tests
  pass (`tests/unit/test_swift_watchdog.py:73`, `:82`), and no `sleep` process was left after the run. I
  did not rerun the scratch Swift package.
- **M8: closed.**
  - **The guard.** Each of the eight docstring items now has a MUST_BLOCK case
    (`conformance/test-hook-claims.py:354-357`).
  - **The gates.** I planted round 2's faults and three others in a scratch copy, and each turns a test
    red:
    - `_wave_base` ignores the previous close;
    - the recorded merge base is dropped;
    - N/A rows are not counted;
    - the session field is read from the whole text;
    - a typed end is accepted.
  - Two new branches have no test (M4 below).
- **K1: closed.** All four commands are blocked (`bash_guard.py:648-659`).

## The guard (question 2)
- **No bypass found among the inputs this round ran.**
  - Every form that round 2 listed is blocked.
  - All 137 MUST_BLOCK cases block, and all 46 MUST_ALLOW cases pass: `conformance/test-hook-claims.py`
    PASS, 19.8 s.
- **Unreadable input blocks.** Each of these exits 2 through the whole hook and through the guard alone:
  - a payload that is not JSON;
  - a truncated payload;
  - an empty payload;
  - invalid UTF-8;
  - an unclosed quote.
- **The record matches the code.** The docstring's "Not held, by class" (`bash_guard.py:29-38`) and G-7
  (`docs/security-invariants.md:191`) now describe a best effort and list the classes it misses. Neither
  claims any spelling the lexer does not read.
- **The limit.** As stated above, this round added no new crafted forms. R2 carries what that leaves.

## Everyday commands (question 3)
The whole hook allowed 15 of 16:
- `git commit -m "$(cat <<'EOF' … EOF)"` whose body names `fly deploy` in backticks;
- `git commit -F - <<EOF` (unquoted) whose body holds backticks of ordinary words;
- `gh pr create --body '…'` holding backticks;
- `gh … --body-file`;
- `gh issue comment --body "$(cat <<'EOF' …)"`;
- `make check-fast > log 2>&1 && git add … && git commit … && git push -q origin wave/m21-w4`;
- python here-documents, quoted and unquoted;
- `sed -n`, `sed -i ''` and `awk -F,` one-liners holding `#`, `|` and `$1`;
- `git log … | cat`;
- `fly status`, `fly logs` and `deploy_hosted_engine.sh --dry-run`.

`rm -rf "${S:?}/x"` is blocked by both readings. That is the rule, not a false block:
`permission-matrix.md:53` says "`rm -rf` anything: DENY", and the text reading blocked it before this wave
(at `6a41d35`). `rm -r` and `rm -f` of the same path pass.

## Findings

### BLOCKING
None

### MINOR

- **M1** `scripts/wave_check.py:444-445`, `:456-458`; `docs/decisions.md:4712`: the range ends at the
  commit that first added the close. Any commit after that is never read, even when the close itself is
  edited later.
  - **Failure (planted in scratch repositories):**
    - A close is committed as a MED draft. Then a commit changes `src/app/adapter/main.py`, and a third
      commit edits the close. `history_problems` returns `([], None)`.
    - The same happens with an ADR written after its code, both after the close's first commit.
    - The M21 closes were each their branch's last commit, so the real tree is not affected. But
      `status: draft` closes are a legal shape, and a close fixed up after a late finding is a plausible
      one.
  - **Fix.**
    1. Pin the end to the last commit that changes the close (`git log -1 --format=%H -- <close>`), or
       HEAD when the working tree's close differs.
    2. Or refuse when `added_sha..HEAD` holds a commit that changes a security glob, a `CODE_DIRS` path
       or `docs/decisions.md`.
    3. Plant both cases in the test file.

- **M2** `scripts/wave_check.py:571-575`; `docs/decisions.md:4729`: a SKIPPED, WAIVED or N/A row is taken as
  ledgered whenever the name of any ledger row for the wave or its milestone appears anywhere in that
  row's text, the evidence cell included.
  - **Failure (planted).** I gave a row `| 7 | make ui-test ran | not run; the security pass is at closure |
    SKIPPED |` a ledger that holds only `security-pass,m30`. It raises no problem.
  - For M21, the ledger now holds `security-pass` and `repository-hooks` (`docs/control-events.csv:24`,
    `:25`). Any skipped row whose evidence mentions either one passes, whatever it skipped.
  - **Fix.**
    1. Match the ledger name against the row's check cell (`cells[1]`) only.
    2. Or map each template row to the control it names.
    3. Add the planted row to the test file.

- **M3** `scripts/wave_check.py:359`, `:507`, `:510`; `docs/decisions.md:4718`: for #201, a change under
  `.claude/` (or `.githooks/`) is not code. Round 2 noted this beside its M5, and this round did not answer
  it.
  - **Failure (planted).** I committed `.claude/hooks/guard.py`, then wrote ADR D-2 in a later docs-only
    commit. `history_problems` returns no problem.
  - This wave's own guard and settings are exactly that kind of change: the ADR that governs them could
    have come after them, and #201 would pass.
  - **Fix.** Add `.claude/` and `.githooks/` to `CODE_DIRS` and to D-192 clause 2's list. Or record in
    D-192 why a hook is not code for #201.

- **M4** `scripts/wave_check.py:499-501`, `:456`; `tests/unit/test_wave_check_m21_rules.py`: two of this
  round's new branches have no test.
  - **Measured** in a scratch copy, where 35 of the 35 tests pass with the code as it stands. With each
    fault below planted, all 35 still pass:
    - The "ADR added with no commit found adding its heading" problem is removed.
    - `_merged(root, added_sha)` is changed to `_merged(root, "HEAD")`.
  - **Why the second one matters.** D-192 says a close is merged "when the commit that added it is on
    main". Suppose W4 is merged and W5 stacks on it. On W5's branch, HEAD is not on main, so the faulted
    check would read W4's merged close again, from a base branch that may be gone.
  - **Fix.** Add one test for each:
    1. an ADR heading that arrives only through a merge commit, or any case where `-G` finds no commit;
    2. a merged close checked from an unmerged later branch, which must say SKIPPED.

## Acceptance criteria evidence
The plan's §1 row for W4 adds no REQ-ID. This round's evidence:
- **B1, M1, M2 and K1 of round 2:**
  - cases at `conformance/test-hook-claims.py:336-357`;
  - held at `.claude/hooks/bash_guard.py:233-247`, `:265`, `:341-371`, `:426-440`, `:581-618` and
    `:641-659`.
- **M3 of round 2:**
  - the time-bound case at `conformance/test-hook-claims.py:477`;
  - held at `bash_guard.py:54-56`, `:455`, `:499-500`, `:510-515` and `:669-680`, and at
    `.claude/settings.json:49-50`.
- **M4 to M6 of round 2:** `tests/unit/test_wave_check_m21_rules.py:460`, `:471`, `:482`, `:495`, `:502` and
  `:511`; held at `scripts/wave_check.py:453-458`, `:494-501` and `:561-588`, and at
  `scripts/check_records.py:1544`.
- **M7 of round 2:** `tests/unit/test_swift_watchdog.py:73`, `:82`; held at `scripts/watchdog.py:27-67`.
- **M8 of round 2:** `tests/unit/test_wave_check_m21_rules.py:524`, `:539`.
- **The real tree.**
  - `wave_check_all.py`: PASS, 67 records.
  - `wave_check.py` on `m21-wave-1-close.md` to `m21-wave-3-close.md`: PASS.
  - `history_problems` and `skip_ledger_problems` on all 13 closes from M19-W1 to M21-W3: each
    `([], None)` and `[]`.
  - `check_records.py --root .`: no findings.
  - The two test files: 42 passed.
- **The stacked W1 to W3 closes, on a `--shared` scratch clone.** I checked three states:
  - as they stand;
  - with `wave/m21-w1`, `wave/m21-w2` and `closure/m20` deleted;
  - with main fast-forwarded to W3 and `wave/m21-w3` deleted.

  W1 and W2 (dated and committed 2026-10-09) are not read, under GPF-001. W3 passes, then says SKIPPED
  (merged). On the merged stack, a MED W4 close over `origin/wave/m21-w3...HEAD` is refused for
  `.claude/settings.json`; a HIGH one passes.
- **The OWNER APPROVAL commits.** `36e74fa` holds only `.claude/hooks/bash_guard.py`, and `bd55823` holds
  only `.claude/settings.json`. No other commit of this round touches `.claude/`, `.githooks/` or
  `.github/`.
- **The records.**
  - D-192 (`docs/decisions.md:4692`) states clauses 1 to 3 and 5 as the code now does, apart from M1 and
    M3 above.
  - G-7 (`docs/security-invariants.md:191`) matches the docstring.
  - The ledger row `security-pass,m21` (`docs/control-events.csv:25`) is matched by row 4 of each M21
    close ("security pass" in its check text).

## Producers of hardened invariants (2a-bis)
- **INV-82 (G-7).**
  - Producers: the text reading (`.claude/settings.json:51`) and the second reading
    (`.claude/hooks/bash_guard.py`), bounded by `timeout`/`onFailure` (`:49-50`) and the guard's own
    deadline (`bash_guard.py:676`).
  - Citing test: `conformance/test-hook-claims.py`, run through the hook command.
  - Gaps:
    - the classes the docstring lists as not held;
    - a session started outside the repository (#142; `docs/control-events.csv:24`);
    - R1 and R2 below.
- **INV-6 (G-5).**
  - Producers: the Swift legs under `scripts/watchdog.py`.
  - Citing tests: `tests/unit/test_swift_watchdog.py:25`, `:34`, `:41`, `:73` and `:82`.
  - Gap: CI's test job (#122).

## K.8 contract drift check
Plan §5: no `/v1` change. `git diff --name-only 6a41d35..7b8cee3 -- src/ ios/ModelRanking/` lists 0 files.
This round added no public symbol. `history_problems`, `skip_ledger_problems`, `stop` and `judge_text`
keep their signatures. Verdict: OK.

## K.9 candidates spotted outside this wave's scope
None

## Risks queued to next M
- **R1** `.claude/settings.json:50`; `INSTALL.md:47-53`: Claude Code reads `onFailure` only from 2.1.295.
  The 2.1.294 binary installed beside it has no such key, so there a timed-out hook proceeds and the
  guard's own 5 s bound is the only bound. INSTALL.md names no minimum Claude Code version.
  - **What would show it is real:** a session on an older Claude Code whose hook times out.
  - **Fix:** name the minimum version in INSTALL.md.
- **R2** `.claude/hooks/bash_guard.py` (the whole file): this round confirmed the guard only against the
  inputs listed above, and added no new crafted forms. Each earlier round found spellings the lexer
  missed. So whether forms inside the docstring's "What it blocks" list are still missed is not ruled out
  here.
  - **What would show it is real:** a later probe that finds one.
  - **Defence in depth for the owner to weigh:** round 2's R1. A refusing `fly`/`flyctl` shim on the
    agent's PATH holds every spelling that reaches `fly` through PATH, whatever the lexer reads.
