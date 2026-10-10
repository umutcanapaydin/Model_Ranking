---
record_type: review
id: m21-wave-4-review-round-2
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-10
---
# M21 Wave 4 Code Review, round 2 (the controls)

**Reviewer:** Code-Reviewer subagent, round 2 (fresh eyes; wrote none of the wave and none of round 1).
Author and reviewer family: Claude / Claude (fallback: no second family in this lane). Fresh context: I
read round 1 (`docs/reviews/m21-wave-4-review-round-1.md`), then each fix commit with `git show`, then the
guard and the gates in full.
- **The guard.** It ran only on crafted hook payloads: through the hook command in `.claude/settings.json`
  (both readings, `CLAUDE_PROJECT_DIR` set to the worktree) and through `bash_guard.py` alone. No crafted
  command was executed. The shells' side was checked with harmless `echo`s under `bash -c` and `zsh -c`.
- **The gates.** Plants ran in scratch repositories built with the test file's own helpers, and in a
  `--shared` scratch clone of the real history.
- **Fault plants.** The guard's ran on a scratch copy. The gates' ran in the worktree, each restored by
  bytes and checked by sha256; `git status` was clean after.

Nothing in the worktree changed but this file.

**Independent:** yes
**Date:** 2026-10-10
**Commit range:** `6a41d35..42a47cc` (`origin/wave/m21-w3..42a47cc`, 29 commits, no merges). This round's
fixes are `f3df6ea`, `64b862a`, `1702041`, `da6b95f`, `7830d52` and `42a47cc`.
**Risk tier:** HIGH (plan §2 W4; the range changes `.claude/settings.json` and `.claude/hooks/bash_guard.py`)

## Verdict
BLOCKING

## Round 1's findings, re-run
- **B1: closed.** All 13 commands round 1 listed are BLOCKED by the whole hook. Each is also blocked by
  `bash_guard.py` alone (exit 2).
- **M1: closed for the spellings listed.** All 20 are BLOCKED. Other stdin and zsh forms remain (M1 and M2
  below).
- **M2: closed.** Round 1's six commands are ALLOWED. So are 46 everyday commands of this project. Among
  them:
  - commit and PR bodies through `"$(cat <<'EOF' … EOF)"` that name `fly deploy` and `git push --all` in
    backticks;
  - `gh … --body '…'` and `--body-file`;
  - `make … && git add … && git commit … && git push -u origin wave/…`;
  - python here-documents;
  - `rm -r "${SCRATCH:?}/…"` and `rm -f "${SCRATCH:?}/…"`;
  - sed and awk one-liners holding `#`, `|` and `(`;
  - `case … esac`, `find -exec grep`, `jq`, `sqlite3`, `env -u`, `nohup … &` and `time make`.

  I found no false block.
- **M3: half closed.** Each of these is refused: a start after the wave's base, an empty range, a backdated
  close committed from 2026-10-10, and a rename out of a glob. The range's end is still the author's (M4
  below).
- **M4: closed.**
  - A two-dot range is read from its merge base.
  - I checked a stack on a scratch clone of the real history: I deleted `wave/m21-w2`, then fast-forwarded
    W1 to W3 into main and deleted their branches. W1 to W3 still pass, W3 as SKIPPED (merged). A W4
    close over `origin/wave/m21-w3...HEAD` still reads `.claude/settings.json`.
- **M5: closed for the planted cases.** One heading spelling escapes #201 (M5 below).
- **M6: closed for the seven.** An eighth pair, in a spelling the log uses, has no pointer (M5 below).
- **M7: closed for the planted cases.** The new field can be read from the template's own words (M6 below).
- **M8: closed.** With `_history_absent` patched to report "a shallow clone", `wave_check_all.py` printed
  `docs/plans/m21-wave-3-close.md: SKIPPED [wave-check]: …` above its PASS line.
- **R1: half closed.** A hang no longer stalls the leg. The hung test process survives the kill (M7 below).

## Findings

### BLOCKING

- **B1** `.claude/hooks/bash_guard.py:6`, `:229-230`, `:199-212`, `:504`: a here-document whose delimiter is
  not quoted is read as data. The shell runs every `$( )` and backtick in its body.
  - **How.** Line 230 records the delimiter's text but not whether it was quoted. Lines 199-212 keep the
    body as plain text, and line 504 reads it only when a shell owns it.
  - **Measured.** The whole hook ALLOWED each command below:
    - ``git commit -q -F - <<EOF⏎fix: the guard (M21-W4)⏎⏎- it now blocks `fly deploy` and `git push --all origin`⏎EOF``
    - ``gh pr create --draft --title 'M21-W4' --body "$(cat <<EOF⏎- agents run `fly launch` never⏎EOF⏎)"``
    - ``cat > ../notes.md <<EOF⏎Run `fly secrets set A=b` from the owner's terminal only.⏎EOF``
    - `cat <<EOF | tee ../x.md⏎Pushed with $(git push origin HEAD:main)⏎EOF`
    - `cat <<EOF⏎$(fly deploy)⏎EOF`

    On the shell's side, ``bash -c`` and ``zsh -c`` given
    ``cat <<EOF⏎- it now blocks `echo RAN-1` and $(echo RAN-2)⏎EOF`` print `RAN-1` and `RAN-2`: both ran.
    The text reading misses all five, since `fly` and `git` follow a backtick or `$(` there, not the start
    of a line or `;&|`.
  - **Why blocking.**
    - The first command is the commit message this project writes every wave, with the delimiter's
      quotes left off. Its Markdown backticks then run `fly deploy`, which D-185 keeps for the owner.
    - The owner is asked to approve this guard (`64b862a`, OWNER APPROVAL) on two statements. The
      docstring says "a here-document's body, is data" (line 6). G-7 says the lexer reads "here-strings
      and here-documents" (`docs/security-invariants.md:191`).
    - This is round 1's B1 class: an ordinary shape that lets a real deploy through the whole hook, in
      the record the owner approves on.
  - **Fix.**
    1. In `_redirect`, record whether any part of the delimiter word was quoted. `_Builder.add` already
       knows.
    2. In `_bodies`, read the body of an unquoted delimiter the way the shell does: `\` escapes only `$`,
       a backtick, `\` and a newline; `"` is text. Judge each `$( )`, backtick and `$(( ))` in it. A
       quoted delimiter's body stays data.
    3. Add the five commands above to MUST_BLOCK.
    4. Add `cat > f <<EOF⏎built $(date)⏎EOF` to MUST_ALLOW.

### MINOR

- **M1** `.claude/hooks/bash_guard.py:166-167`, `:303-305`, `:335-343`, `:244-249`, `:310-318`, `:371-378`:
  the lexer skips other text that the shells run.
  - **Measured.** The whole hook ALLOWED each command below. An `echo` in the same form ran under the shell
    named.
    - **Arithmetic holding a substitution** (bash and zsh): `echo $(( $(fly deploy) + 1 ))` and
      `(( $(fly deploy) ))`. `_arithmetic` (`:335`) skips everything between the parentheses.
    - **`$((fly deploy) )`** (bash and zsh): both shells read it as `$( (fly deploy) )`. The lexer reads it
      as arithmetic.
    - **Nested backticks** (bash and zsh): ``` echo `echo \`fly deploy\`` ```. Inside backticks, `` \` `` opens
      a nested substitution. Line 248 keeps it as a literal backtick.
    - **A brace inside `${ }`** (bash): `bash -c 'echo ${x:-{} ; fly launch ; echo }'`. Bash ends the
      expansion at the first `}`. The count at line 313 runs to the last one, so `fly launch` is read as
      part of it.
    - **zsh forms:**
      - `{ true } always { fly deploy }` and `if true { fly deploy; }`. Only a command's first word is
        tried as its program, unless that word is a wrapper (`:377`).
      - A glob qualifier, `ls /etc/hosts(e:'fly deploy':)`.
      - `echo ${(e):-'$(fly deploy)'}`. zsh evaluates the quoted text.
  - **Failure.** None of these is an everyday shape, and the guard need not chase each one. But the
    docstring's "Not held" list (lines 32-40) and G-7 name none of them. G-7 says the lexer reads
    "substitutions".
  - **Fix.**
    1. Scan arithmetic for `$(` and backticks.
    2. Read `$((` as a substitution when it closes with `) )`.
    3. Re-lex backtick text after removing one level of `` \` ``, `\\` and `\$`.
    4. End `${` at the first unquoted, unescaped `}`, and lex its inner text.
    5. Treat a lone unquoted `{` or `}` word as a command boundary.
    6. Refuse a word that holds an unquoted `(e` qualifier or `(e)` flag.
    7. Or list whichever forms stay in the docstring and in G-7.

- **M2** `.claude/hooks/bash_guard.py:489`, `:502-503`, `:486`, `:497-501`, `:444-445`, `:65`, `:533`: a shell
  that reads its commands from stdin still passes. The docstring (lines 15-16) and G-7 say "a shell reading
  its commands from a pipe or a file" is blocked.
  - **Measured.** The whole hook ALLOWED each command below. Its `echo` form ran under both shells.
    - `echo 'fly launch' | bash -`. Line 489 skips no option of one character, so `-` is read as a script
      named `-`.
    - `bash /dev/stdin <<< 'fly launch'` and `bash /dev/stdin <<'EOF'⏎git push --all origin⏎EOF`. Line 502
      reads `/dev/stdin` as a script's name.
    - `echo 'fly launch' | bash --rcfile /dev/null`. Line 486 knows only that `-o` and `-O` take a value.
    - `printf 'fly launch' | xargs -0 bash -c`. At line 497 a `-c` with no string passes, and its string
      comes from the pipe.
    - `source /dev/stdin <<< 'fly launch'`. Line 444 does not read `source`'s here-string.
    - `tcsh -c 'fly launch'` and `csh -c 'fly deploy'`. Both ship with macOS (`/bin/tcsh`, `/bin/csh`), and
      neither is in SHELLS (line 65).
    - `git push origin heads/main` and `git push origin HEAD:heads/main`. git resolves `heads/main` to
      `refs/heads/main`. Line 533 strips only `refs/heads/`.
  - **Fix.**
    1. Read `-`, `/dev/stdin`, `/dev/fd/0` and `/proc/self/fd/0` as stdin, for a shell and for `source` and
       `.`.
    2. Skip the value of `--rcfile` and `--init-file`.
    3. Block a `-c` with no string.
    4. Add `csh`, `tcsh` and `fish` to SHELLS.
    5. Strip `heads/` as well as `refs/heads/`.
    6. Add each command to MUST_BLOCK.

- **M3** `.claude/hooks/bash_guard.py:404-418`, `:377-397`: the guard has no time bound of its own, and one
  input grows its time exponentially.
  - **Measured.**
    - **Brace expansion.** `_could_name_guarded` expands every brace in a program word before matching. I
      timed `{a,b}` repeated N times, followed by `; fly launch`:
      - N=16 (80 characters): 2.1 s;
      - N=18 (90 characters): 8.6 s, at 74 MB.

      Each group doubles the time, so N=21 (105 characters) takes about 70 s, and N=24 about 9 minutes and
      several GB.
    - **The wrapper loop.** It is quadratic. `nohup` followed by `rm x` 8000 times (40 KB) takes 5.1 s;
      `env` 8000 times takes 1.8 s.
  - **Failure.** A crash does block. Each of these exited 2: a lone surrogate, a bad `$'\x'`, a
    `RecursionError` from 3000 `source`s, an unclosed `${`, and invalid UTF-8. A hang does not block: the
    guard never answers, and what follows the hook's timeout is Claude Code's choice.
    `.claude/settings.json` sets no `timeout` on the hook, and I did not confirm whether a timed-out hook
    blocks or proceeds. On the owner's Mac, the memory alone does harm.
  - **Fix.**
    1. Refuse more than 64 alternatives as `Unreadable`, which blocks.
    2. Match each brace alternative against GUARDED without building the product.
    3. Bound the candidate loop.
    4. Give the guard a deadline of its own: `signal.alarm(5)` raising `Unreadable`.
    5. Add a 120-character brace word to MUST_BLOCK, with a time bound.

- **M4** `scripts/wave_check.py:460`, `:462-475`; `docs/decisions.md:4719`: the range's end is still the
  author's. A close can narrow its range from the end, or skip every history rule.
  - **Measured in scratch repositories.** Each close was MED, over a commit that changes
    `src/app/adapter/main.py`:
    - An end named before the glob change (`<base>...<early commit>`) raises no problem.
    - An end on main (`main..main`, `<base>...main`) says SKIPPED "merged into main" and exits 0. The
      empty-range refusal (line 475) is never reached.
  - **On the real history.**
    - A MED W4 close over `origin/wave/m21-w3...425dfd6` passes; the guard's `.claude/settings.json`
      commit `c3b8b9a` comes after `425dfd6`.
    - One over `origin/main..origin/main` says SKIPPED and passes.
    - The same close over `origin/wave/m21-w3...HEAD` is refused, as it should be.
  - **Why it fails.** D-192 clause 2 says "A close merged into main is not read again". Line 460 asks
    whether the range's end is on main, not whether the close is.
  - **Fix.**
    1. Ask `_merged` about the commit that added the close (`added_sha`), not `end`.
    2. Require `end` to be that commit, or an ancestor of it with no commit between them that changes a
       security glob or a CODE_DIRS path: `git rev-list end..added_sha -- <paths>` must be empty.
    3. Run the empty-range check before any skip.
    4. Plant each case in the test file.

- **M5** `scripts/wave_check.py:494-497`; `scripts/check_records.py:1543`; `docs/decisions.md:2848`, `:4704`:
  each rule still reads one spelling, and a miss passes silently.
  - **#201.** `git log -S "## D-n "` needs a space after the id. I planted an ADR headed `## D-2: Two`, and
    one headed with a bare `## D-2`, each written after its code or beside it. Neither finds a first
    commit, so line 497 `continue`s and no problem is raised.

    Related: a change under `.claude/` is not code for #201, because D-192 clause 2 names only `src/`,
    `ios/` and `scripts/`. This wave's own guard could have been written before its ADR and passed.
  - **A1.** `AMENDS_FIELD` is case-sensitive.
    - D-160's Status line says `**amends** D-138's arithmetic permission`, and D-138 carries no
      `**Amended by D-160` line. D-192 clause 1 (line 4704) says the field "is read in each spelling the
      log uses".
    - Planted on D-192, with D-183's pointer removed, `**amends** D-183`, `Amends D-183` and
      `**Amending** D-183` each pass.
  - **Fix.**
    1. Find the first commit with `-G '^## D-n\b'`.
    2. When no first commit is found for an ADR the range adds, raise a problem instead of skipping.
    3. Read the field without regard to case.
    4. Add D-138's pointer.

- **M6** `scripts/wave_check.py:571`, `:556`, `:566`, `:38`; `docs/wave-checklist.template.md:40`: the ledger
  rule can take the template's own words as the answer, and two kinds of skip stay off the ledger.
  - **The field.** Row 8 of the template says: "Say also, in these exact words,
    `Session started in the repository: yes` or `Session started in the repository: no`".
    `SESSION_FIELD.search` takes the first match anywhere in the close.
    - I planted a close dated 2026-10-11 that copies row 8's check text and answers
      `Session started in the repository: no`. It is read as `yes` and needs no ledger row.
    - Five of the 87 closes copy row 8's check text word for word.
  - **`N/A` rows.** `N/A` is a legal status (line 38). The template's row 9 counts an N/A among the skips
    that go to the ledger. A row marked `N/A (no simulator)` needs no ledger row (planted).
  - **The run line's label.** In another spelling it is not read. Each of these passed with no ledger row
    (planted): `gates SKIPPED : make ui-test`, `gates **SKIPPED**: make ui-test` and
    `gates SKIPPED — make ui-test`. `SKIP` and `NOT RUN` are refused anyway, as statuses not in STATUSES.
  - **Fix.**
    1. Read the field from row 8's evidence cell only, and refuse a close that holds both answers.
    2. Count N/A rows with the SKIPPED and WAIVED ones.
    3. Refuse a row 9 whose run line lacks the exact label `gates SKIPPED:`.

- **M7** `scripts/watchdog.py:5`, `:21-23`, `:31`; `docs/decisions.md:4732`: the watchdog kills
  `swift test`'s process group, but SwiftPM runs the test process (`xctest`) in a group of its own. The hung
  test survives as an orphan.
  - **Measured.** I used a scratch package whose one test sleeps 75 s.
    - **On timeout.** I ran it under the Makefile's capture:
      ``out=`python3 -B scripts/watchdog.py 12 swift test --skip-build 2>&1` ``. The capture returned
      with rc 124 and the watchdog's line. At 17 s, `xctest` was still running, with parent 1 and a
      process group of its own. I killed it with SIGKILL.
    - **On Ctrl-C.** SIGINT to a plain `swift test` left no test process. SIGINT to the watchdog running
      it left `xctest` running, orphaned. The watchdog starts its child in a new session, so the
      terminal's SIGINT reaches only the watchdog. The watchdog answers with SIGKILL, and SwiftPM cannot
      pass anything on.
  - **Failure.** The leg does fail as it should: the watchdog's line holds `error:`, so the grep at
    `Makefile:184` and `:225` shows it, with `(full swift output: …)`. But in a real hang (round 1's
    `firstWithin(1e30)`), the orphan keeps spinning on the owner's Mac after each run. The docstring ("the
    whole group is killed") and D-192 clause 5 ("kills it") say more than the code does.
  - **Fix.**
    1. On a timeout or an interrupt, first list the descendants (`ps -axo pid,ppid,pgid`).
    2. Send SIGINT to the group, so SwiftPM stops its children.
    3. Wait a few seconds, then send SIGKILL to every descendant's process group. Neither signal leaves a
       crash report.
    4. Add a test whose child starts a grandchild with `start_new_session=True`, and assert the grandchild
       is gone.

- **M8** `conformance/test-hook-claims.py:284`, `:335`; `tests/unit/test_wave_check_m21_rules.py:369`;
  `tests/unit/test_swift_watchdog.py:23`: the tests hold less than the docstrings claim.
  - **Method.** I planted each fault below and every test stayed green.
    - The guard's faults went into a scratch copy, with `CLAUDE_PROJECT_DIR` pointed at it, and were
      judged by MUST_BLOCK (97 cases) and MUST_ALLOW (37).
    - The gates' faults went into the worktree. Each was restored by bytes and checked by sha256.
  - **Guard faults that survived.** Each removes something the docstring's first list says the guard
    reads, and no case reads it:
    - `${x:-$(…)}` is no longer lexed;
    - `|&` is no longer a pipe;
    - `<` no longer counts as a file;
    - `find -exec` is not read;
    - `source` is not read;
    - backticks inside double quotes are read as text;
    - `<( )` is not read;
    - `xargs git push` is not judged as behind xargs.
  - **Gate faults that survived:**
    - `_wave_base` ignores the previous wave's close. The stacked test also finds its glob from main's
      base.
    - The recorded `merge base` fallback is dropped.
    - A WAIVED row is not read.
    - The watchdog kills only its child (`child.kill()`), not the group.
  - **Faults the tests killed:** here-document tracking, the keywords, `env -S`, the merged check, a
    rename's old path, an ADR's citing commit, the session field's date, and the new session.
  - **Fix.** Add one MUST_BLOCK case for each line of the docstring's first list, and one test for each
    surviving gate fault above.

### PASS (what looks good)
- **The real tree.** Every leg I ran passes:
  - `wave_check_all.py`: 67 records validated;
  - `wave_check.py` on `m21-wave-1-close.md` to `m21-wave-3-close.md`;
  - `history_problems` on every close dated since 2026-10-01: each returns `([], None)`;
  - `check_records.py --root .`: no findings;
  - `conformance/test-hook-claims.py`: PASS;
  - `test_wave_check_m21_rules.py` and `test_swift_watchdog.py`: 32 passed.
- **The guard's failures block.** No crafted input crashed the guard into an allow. The hook answers any
  non-zero exit of the guard with exit 2, an uncaught exception's exit 1 included. A lone surrogate makes
  the guard alone exit 1, and the whole hook blocks it.
- **The OWNER APPROVAL commit.** `64b862a` holds only `.claude/hooks/bash_guard.py`. No other commit of
  this round touches `.claude/`, `.githooks/` or `.github/`.
- **The seven pointers** that M6 named are in place (`da6b95f`), each inside the section of the ADR it
  amends.
- **The watchdog's message reaches the gate's output,** and the leg exits non-zero.

## Acceptance criteria evidence
The plan's §1 row for W4 adds no REQ-ID. Round 1 cites the wave's controls; this round's evidence:
- **B1 and M1 of round 1:** `conformance/test-hook-claims.py:318`, `:326`.
- **M2 of round 1:** `conformance/test-hook-claims.py:347`.
- **M3 of round 1:** `tests/unit/test_wave_check_m21_rules.py:310`, `:322`, `:331`, `:341`; held at
  `scripts/wave_check.py:470`, `:475`, `:479`.
- **M4 of round 1:** `tests/unit/test_wave_check_m21_rules.py:356`, `:369`, `:209`; held at
  `scripts/wave_check.py:462-468`.
- **M5 of round 1:** `tests/unit/test_wave_check_m21_rules.py:385`, `:397`.
- **M6 of round 1:** `tests/unit/test_wave_check_m21_rules.py:407`, `:91`; held at
  `scripts/check_records.py:1543`.
- **M7 of round 1:** `tests/unit/test_wave_check_m21_rules.py:420`, `:429`, `:437`.
- **M8 of round 1:** `tests/unit/test_wave_check_m21_rules.py:448`; held at `scripts/wave_check_all.py:221`.
- **R1 of round 1:** `tests/unit/test_swift_watchdog.py:23`, `:32`, `:39`; held at `Makefile:149-151`.

## Producers of hardened invariants (2a-bis)
- **INV-82 (G-7).**
  - Producers: the text reading at `.claude/settings.json`, and the second reading,
    `.claude/hooks/bash_guard.py`.
  - Citing test: `conformance/test-hook-claims.py`, which runs both through the hook command.
  - Gaps:
    - B1, M1, M2 and M3 above;
    - a session started outside the repository loads neither reading (#142; ledger row
      `docs/control-events.csv:24`).
- **INV-6 (G-5).**
  - Producers: `make test`, `make swift-test`, `make swift-test-parallel` and the strict-pool rerun, now
    under `scripts/watchdog.py` (`Makefile:149-151`).
  - Citing tests: `tests/unit/test_offline_run.py`, `tests/unit/test_swift_strict_pool.py` and
    `tests/unit/test_swift_watchdog.py:39`.
  - Gaps: CI's test job (#122), and M7's orphan.

## K.8 contract drift check
Plan §5: no `/v1` change. `git diff --name-only 6a41d35..42a47cc -- src/ ios/ModelRanking/` lists 0 files.
The new symbols and their only callers:
```
scripts/wave_check.py:462:    wave_base = _wave_base(root, ids, end)
scripts/wave_check.py:516:    if not any(first_day <= high and last_day >= low and (not ids or _names_wave(rest, ids.group(1), int(ids.group(2))))
scripts/wave_check.py:557:    for entry in (_outside_parentheses(listed.group(1)) if listed else []):
scripts/wave_check.py:571:    field = SESSION_FIELD.search(text)
scripts/wave_check_all.py:176:        skipped += record_lines(record.relative_to(ROOT), code, captured.getvalue())
Makefile:151:SWIFT_TEST = $(if $(filter Darwin,$(UNAME_S)),MODEL_RANKING_REQUIRE_OFFLINE=1 $(SWIFT_WATCHDOG) /usr/bin/sandbox-exec -f ../scripts/offline.sb swift test --disable-sandbox,$(SWIFT_WATCHDOG) swift test)
```
Verdict: OK.

## K.9 candidates spotted outside this wave's scope
- **K1** `.claude/hooks/bash_guard.py:540`; `permission-matrix.md:50`: S5 names `git checkout -- <path>` and
  `git checkout .`. Other commands destroy the same uncommitted work, and both readings ALLOWED each of
  them:
  - `git checkout HEAD src/app/adapter/main.py`;
  - `git checkout -f <branch>`;
  - `git switch --discard-changes <branch>`;
  - `git stash clear`.

  An agent reverting one file by ref loses the owner's edits to it.
  - **Fix** (an enhancement for the owner): widen S5 to cover a checkout that names a path after a ref,
    `-f`/`--force`, `--discard-changes`, and `stash drop` and `stash clear`. Change the matrix and both
    readings together.

## Risks queued to next M
- **R1** `.claude/hooks/bash_guard.py` (the whole file): each round finds spellings the lexer misses. Round 1
  found 33 and this round about 20, because the reader re-implements two shells' grammars.
  - **What would show it is real:** a third round that finds more.
  - **An alternative for the owner to weigh:** put a `fly`/`flyctl` shim that refuses first on the
    agent's PATH, as this seat's own `guard-bin` does. It holds every spelling that reaches `fly` through
    PATH, `python -c` and scripts included. The lexer would remain for `git`.
