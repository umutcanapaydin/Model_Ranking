---
record_type: review
id: m21-wave-4-review-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-10
---
# M21 Wave 4 Code Review (the controls)

**Reviewer:** Code-Reviewer subagent (fresh eyes; wrote none of the wave). Author and reviewer family:
Claude / Claude (fallback: no second family in this lane). Fresh context: I read plan §2 W4 and D-192
first, then each commit with `git show`, then ran the gates and planted each rule's violation in scratch
repositories under the session's scratchpad. The Bash guard was run only on crafted hook payloads,
through the hook command in `.claude/settings.json` and through `bash_guard.py` alone; no crafted command
was executed. Nothing in the worktree changed but this file.
**Independent:** yes
**Date:** 2026-10-10
**Commit range:** `6a41d35..d3596e1` (`origin/wave/m21-w3..d3596e1`, 22 commits, no merges)
**Risk tier:** HIGH (plan §2 W4, `docs/plans/m21-plan.md:66`; the range changes `.claude/settings.json`, a §3 security glob)

## Verdict
BLOCKING

## Findings

### BLOCKING

- **B1** `.claude/hooks/bash_guard.py:143`, `:151`, `:93`: the second reading stops at a comment, takes a
  redirection for the end of a command, and reads a here-string as a here-document. With any of these, a
  deploy passes the whole Bash hook.
  - **How.** Each line has its own fault:
    - Line 143: `shlex.shlex(..., posix=True)` keeps its default `commenters = "#"`. By then
      `_flattened` has joined every line into one with ` ; `. So the first `#` shlex meets drops the
      rest of the command, every later line included. That `#` can start a token or sit inside a word
      (`a#b`, a URL fragment); the shell treats neither the second nor the URL case as a comment.
    - Line 151: any token made of `<>&` counts as a command separator, so a redirection's target is
      judged as the program.
    - Line 93: `<<<` is skipped only at its first `<`. At the next character `<< x` is read as a
      here-document, and the lines up to a line `x` are dropped as its body.
  - **Measured.** Each command below ran through the full hook: both readings, with `CLAUDE_PROJECT_DIR`
    set to the worktree, given as payload only. Every one was ALLOWED:
    `# check status first⏎env fly deploy` · `# note⏎FLY_API_TOKEN=x fly deploy` · `# note⏎(fly deploy)` ·
    `>/dev/null fly deploy` · `</dev/null fly deploy` · `fly >/dev/null secrets set A=b` ·
    `2>/dev/null fly launch` · `# push⏎bash -c "git push --all origin"` · `# x⏎git push origin \--mirror` ·
    `curl -s https://x.dev/#a; fly launch` · `fly status#x; fly launch` · `true # <<EOF⏎fly launch⏎EOF` ·
    `cat <<< x⏎fly launch⏎x`.
    - Without its comment or redirection, each one is BLOCKED.
    - Three of them are spellings that `conformance/test-hook-claims.py` lists as MUST_BLOCK.
    - I checked the shell's side with harmless echoes. `bash -c '>/dev/null echo …'` runs the echo, and
      `zsh -c 'echo a#b # c'` prints `a#b`.
  - **Why blocking.** The owner is asked to approve this guard (`c3b8b9a`, OWNER APPROVAL) on two
    statements:
    - G-7 says it "blocks the spellings #189 and the release verdict's RS1 list"
      (`docs/security-invariants.md:191`);
    - the docstring says "in any of those spellings" (`bash_guard.py:10`).

    A comment line above a command is an everyday shape for an agent's Bash call. After one, the second
    reading allows everything below it, including a real `fly deploy` (D-185). That is #248's class,
    a record saying more than the gate holds, and here it is in the record the owner approves on.
  - **Fix.**
    1. Set `lexer.commenters = ""`.
    2. In `_flattened`, drop a comment only where `#` begins a word outside quotes, up to the end of
       its line. Do this before the here-document scan, so `# <<EOF` opens nothing.
    3. On `<<<`, append it and advance three characters.
    4. In `judge_text`, let a redirection operator, and an fd number written against it, consume its
       target word and keep the simple command going. Split only on `;`, `&&`, `||`, `|`, `|&`, `&`,
       `(`, `)` and `;;`.
    5. Add the thirteen commands above to MUST_BLOCK.

### MINOR

- **M1** `docs/security-invariants.md:191` (G-7); `.claude/hooks/bash_guard.py:233`, `:237`, `:240`, `:39`,
  `:190`. Beyond B1, the guard does not hold some spellings that the record either says it holds or
  leaves off its list of what it misses.
  - **Measured.** The whole hook ALLOWED each command below.
    - **Option prefixes.** git takes any unique prefix of a long option; `git status --b` printed the
      branch header here, on git 2.50.1.
      - `git push --m origin` is `--mirror`. The check needs four characters and the text reading
        needs `--mi`.
      - `git push --al origin` and `git push --branches origin` push every branch (`--branches` is
        git's own synonym for `--all`).
      - `git reset --ha HEAD~1` is `--hard`.
      - `git restore --staged --work x` writes the work tree.
    - **A shell reading its script from stdin.** `bash <<'EOF'⏎fly launch⏎EOF`,
      `bash <<'EOF'⏎git push origin \--mirror⏎EOF` and `echo 'fly deploy' | bash`. The docstring calls a
      here-document's body data, but to a shell it is the script.
    - **Wrappers the lists lack.**
      - `env -S 'fly deploy'`: the string is skipped as an option's value.
      - `env -P /usr/local/bin fly deploy`, `echo deploy | xargs fly`, `coproc fly deploy` and
        `caffeinate -i fly deploy`.
      - `bash -c -- 'fly deploy'`. Checked: `bash -c -- 'echo …'` runs the echo.
    - **zsh, not bash.** The Bash tool runs zsh here, and the guard parses bash.
      - `=fly deploy`. Checked: `zsh -c '=echo …'` runs the echo.
      - `noglob fly launch`, `nocorrect fly deploy`, `- fly launch` and `repeat 1 fly launch`.
      - A glob as the program's name: `fl[y] deploy`.
  - **What the record claims.**
    - G-7 says the text reading blocks "`--mirror` and its abbreviations".
    - It says the second reading blocks "every `fly` subcommand but a read-only few".
    - Its list of what is not held names variables, aliases, functions, scripts and `python -c`, and
      none of the above.
  - **Fix.**
    1. Match a long option by prefix: `"--mirror".startswith(a)` from three characters, and likewise
       for `--all`, `--branches`, `--hard`, `--worktree` and `--force`.
    2. Block a shell that has neither `-c` nor a script file (it reads stdin), and read `--` after `-c`.
    3. Judge `env -S`'s string.
    4. Add `coproc`, `caffeinate`, `noglob`, `nocorrect`, `-` and `repeat N` to the wrappers. Refuse a
       glob character or a leading `=` in a program word.
    5. Rewrite G-7 and the docstring so that they list these classes, or whichever stay, as not held.
       How far to chase them is the owner's call. The record must say which ones remain.

- **M2** `.claude/hooks/bash_guard.py:121`, `:93`, `:190`: the second reading refuses ordinary commands this
  project runs. The text reading allows each command below; the second reading blocks it.
  - **The `/file-issue` and `/fix-issue` form.**
    `gh issue comment 189 --body 'the guard reads `fly deploy` and git push --all'` is blocked.
    `_substitutions` takes every backtick pair, quoted or not, but inside single quotes a backtick is
    plain text. The skills write their bodies this way (`gh issue create --body '…'`,
    `.claude/skills/file-issue/SKILL.md:10`).
  - **The standard commit and PR body form.**
    `gh pr create --draft --title 'x' --body "$(cat <<'EOF'⏎- blocks `git push --all`⏎EOF⏎)"` is
    blocked. The here-document inside `"$( )"` is read as quoted text, so its backticks are judged.
    MUST_ALLOW holds this form only with a body that names nothing guarded (`It's done`).
  - **A here-string and a shift.** `cat <<< 'hello'` and `echo $((1<<2))` are refused as Unreadable:
    "a here-document that never ends".
  - **A dry run through a shell.** `bash scripts/deploy_hosted_engine.sh --dry-run` and the same with
    `sh` are blocked. Line 190 drops every argument that starts with `-`, so the dry run reaches `judge`
    with no arguments. The docstring allows the dry run "through a shell", and the text reading allows
    it.
  - **Fix.**
    1. Track quoting in `_substitutions`, or judge only the substitutions the lexer meets outside
       single quotes.
    2. Start a fresh quoting context at `$(` inside double quotes, so its here-document is found.
    3. Skip `<<<` (see B1), and skip `<<` inside `$(( ))`.
    4. Keep the arguments that follow a shell's script name.
    5. Add each command above to MUST_ALLOW.

- **M3** `scripts/wave_check.py:409`, `:404`, `:434`, `:463`: the history rules read whatever range the
  author types, so a wave can escape the HIGH rule by its range.
  - **Measured** in scratch repositories built with the test file's own helpers:
    - **Narrow range.** A MED close whose range is `HEAD~1..HEAD`, `c3b8b9a..HEAD` or `HEAD..HEAD` passes
      against this wave's real history, which changes `.claude/settings.json`. With
      `origin/wave/m21-w3...HEAD` the same close is refused, as it should be.
    - **Empty range.** It passes all three rules. With no commit dates, `if days:` (line 463) skips the
      process-log rule without saying so.
    - **Backdated close.** A close dated `2026-10-09` returns `([], None)` for this wave's range
      (line 404). Nothing compares the close's date with the dates of its range's commits.
    - **Rename.** Renaming a file out of a glob (`git mv src/app/adapter/main.py
      src/app/adapter/main2.py`, MED) raises no problem. When `git diff --name-only` detects a rename,
      it reports only the new path (line 434).
  - #183 moved the authority from a footprint the author types to a range the author types. Nothing
    ties that range to the wave's branch.
  - **Fix.**
    1. Refuse an empty range.
    2. Refuse a range whose start is not an ancestor of both merge-bases: of its end with `origin/main`,
       and of its end with the previous wave's close commit. Or compare the range with the
       Code-Reviewer verdict's `**Commit range:**`.
    3. Refuse a close dated before the last commit in its range.
    4. Pass `--no-renames`, or use `--name-status` and read both paths.

- **M4** `scripts/wave_check.py:424`, `:426`: a close that passed can later turn red with no change of its
  own.
  - **Two-dot ranges.** A two-dot range diffs from the start ref's current tip, not from where the wave
    forked.
    - Planted: a MED close with range `main..HEAD` passes on its branch.
    - After its `--no-ff` merge and one later commit on main that touches `src/app/adapter/main.py`,
      the same close fails with "changes its plan's security globs".
    - M20-W1's close named `origin/main..HEAD`, and the template's footer reads `<start>..<end>`.
    - Once a MED close in that form is merged, `make check` on main would go red for every later session.
  - **Stacked waves.** A stacked wave's close (`origin/wave/m21-w3...HEAD`) fails with "cannot be read"
    once the wave below is merged and its branch deleted, and keeps failing until this wave is merged
    too. D-192 chose this, but it is the order in which the owner merges a stack.
  - **Fix.**
    1. Resolve every range to `merge-base(start, end)..end` (the semantics of `git diff A...B`). That
       reads the wave's own changes before the merge and nothing after it.
    2. When the base cannot be resolved and the end is not yet merged, fall back to
       `merge-base(end, origin/main)` instead of failing.

- **M5** `scripts/wave_check.py:456`, `:467`: #201 and #203 check a weaker property than their issues
  describe.
  - **#201.** The rule reads only the files of the commit where the ADR first appears, not where that
    commit falls in the range.
    - Planted: commit 1 changes `src/app/other.py`; commit 2, docs only, adds `## D-2`.
    - Result: no problem, although the ADR was written after the code it governs.
  - **#203.** Any heading whose dates overlap the range's days passes.
    - Planted on this wave: `## 2026-10-10 — M21-W4: the controls` removed from `docs/process-log.md`.
    - W4's range still passes, because the W1 to W3 heading `## 2026-10-09/10` covers 2026-10-10.
    - The rule fails only when that span is narrowed as well.
  - **Fix.**
    - For #201: refuse when a code-changing commit in the range comes before the ADR's first commit.
      That is, a commit that cites the ADR in its message, or any code commit unless the plan names
      the ADR.
    - For #203: require the range's own diff to add a `## ` heading to `docs/process-log.md`, or a
      heading that names the wave (`M21-W4`).

- **M6** `scripts/check_records.py:1541`: A1 reads only one spelling of the field, and seven amendments in
  the live log have no pointer back.
  - **Planted.** I changed D-192's `**Amends** D-183` to `**Amends:** D-183` and deleted D-183's pointer.
    A1 reported nothing.
  - **The live log.** I read it with the other spellings too. These targets carry no `**Amended by` line
    naming the ADR that amends them:
    - D-124 → D-115 (written `**Amends:**`);
    - D-135 → D-121;
    - D-143 → D-140;
    - D-146 → D-143;
    - D-151 → D-149 (written `**Amends D-149**`);
    - D-161 → D-155;
    - D-162 → D-143. D-143's Status line does say "amended by D-162", in another form.
  - For these seven, #200's defect stands: a reader of the amended ADR sees the rule as it was. A new
    ADR written with `**Amends:**` would also pass A1.
  - **Fix.**
    1. Read `\*\*Amends:?\*\*` and `\*\*Amends (?=D-\d)` as well.
    2. Add the seven pointers, or list them in the check as accepted older forms.

- **M7** `scripts/wave_check.py:485`, `:493`: #202 reads only row 9's run line and one sentence, so a skip
  can stay off the ledger. Each case below was planted through `skip_ledger_problems`.
  - **Missed** (no problem raised):
    - a row whose status is `SKIPPED NO-ENVIRONMENT` (`| 7 | make ui-test | … | SKIPPED NO-ENVIRONMENT |`),
      while row 9 says `gates SKIPPED: none`;
    - the label in lower case: `gates skipped: make ui-test`;
    - a paraphrase: "The session began outside the repo, so the hooks never loaded".
  - **Wrongly refused:**
    - "The session was not started outside the repository";
    - `gates SKIPPED: make ui-test (no simulator, no Xcode)`, even with a `ui-test` row in the ledger.
      The comma inside the parentheses produces a gate named `no-xcode)`, and that name is refused.
  - **Fix.**
    1. Also require a ledger row for every checklist row whose status is SKIPPED or WAIVED.
    2. Match the label without regard to case.
    3. Split the list only on commas outside parentheses.
    4. Have the template's row 8 ask for a yes/no field, "session started in the repository:", and read
       that instead of prose.

- **M8** `scripts/wave_check_all.py:196`, `:199`; `docs/decisions.md:4698`: where it matters, the history
  rules skip silently.
  - **Where the line is lost.** `wave_check.py` prints `SKIPPED [wave-check]: …` (line 666). But
    `wave_check_all.py` captures each record's output and prints it only when the record fails. CI runs
    only `python scripts/wave_check_all.py` (`.github/workflows/ci.yml:69`), and so does `make check`'s
    `wave-check-all`.
  - **Measured.** With `_history_absent` patched to report "a shallow clone", the run printed
    `wave-check-all PASS: 67 v5.0-or-later record(s) validated` and no SKIPPED line.
  - **Why it matters.**
    - D-192 clause 2 says these rules "say SKIPPED loudly".
    - The comment on #122 tells the owner to expect `SKIPPED [wave-check]: ... a shallow clone` in CI's
      output. Neither line will appear.
    - A merged close whose base branch was deleted is skipped the same way, also silently.
  - **Fix.** Have `wave_check_all.py` print each record's SKIPPED lines on a pass too, or count them in
    its PASS line (`…; history rules SKIPPED on N`).

### PASS (what looks good)
- **The gates on the real tree.** Every `make check` leg I ran passes:
  - `wave_check_all.py`: 67 records validated;
  - `wave_check.py docs/plans/m21-wave-3-close.md`: the one close dated from 2026-10-10, whose history
    rules ran and found nothing;
  - `check_records.py --root .`: no findings;
  - `conformance/test-hook-claims.py`: PASS;
  - the 13 touched Python test files: 324 tests pass, with 2 skips (the offline-run pair, which runs
    only under `make test`).
- **Earlier closes.** Every close from M19 on still passes. The history rules grade only closes dated
  from 2026-10-10 (GPF-001), and they did run on M21-W3's.
- **Merged closes.** A merged close whose base branch was deleted says SKIPPED. The test merges with
  `--ff-only`. The real history uses merge commits, and `merge-base --is-ancestor` holds there too.
- **#179, measured.** From a clean scratch build,
  `sandbox-exec -f ../scripts/offline.sb swift test --disable-sandbox --filter OfflineGuardTests` builds
  and passes 4 of 4. Outside the profile, the new `testAChildTheSuiteStartsCannotNameAnOutsidePeer`
  fails on 2 assertions. So the build itself works inside the profile, and the test goes red when the
  profile is missing.
- **#181, measured.** `SlowTierTests/` with `LIBDISPATCH_COOPERATIVE_POOL_STRICT=1`, inside the profile:
  7 of 7 pass. The Makefile requires the manifest's count.
- **#248.** None of the fifteen renamed tests' old names is left in any live file. They remain only in
  the history records (reviews, closes, process log). `test_prd_citations.py` and
  `test_security_invariants.py` resolve every citation.
- **#200.** A1 is red on a planted missing pointer and on a pointer naming `D-1920`, and quiet on the real
  log.
- **The guard's commit and failure modes.**
  - The OWNER APPROVAL commit `c3b8b9a` holds only `.claude/hooks/bash_guard.py` and
    `.claude/settings.json`. No other commit touches `.claude/`, `.githooks/` or `.github/`.
  - The hook fails closed when the second reading is missing, cannot parse the command, or raises: any
    non-zero exit becomes exit 2.
  - No crafted command made it crash into an allow.
- **D-192.** It first appears in `9cf8e12`, a docs-only commit before the code. D-183 carries its pointer
  back.

### The tests' strength
- **`conformance/test-hook-claims.py`.** Every MUST_BLOCK case is a lone command: none has a comment line,
  a leading or mid-command redirection, a here-string, or a shell fed from stdin. That is why B1 and M1
  pass it.
- **`test_wave_check_m21_rules.py`.** It plants the obvious violation for each rule. It plants none of
  these: a narrow or empty range, a backdated close, a rename, a two-dot range read after a merge, or an
  ADR written after its code.
- **`test_ci_needs.py`.** It flips each need on a planted workflow and holds the marks equal to the real
  one. That is strong for what it reads.
- **`test_needs_git.py`.** It reads only list literals that start with `"git"` and mention `ROOT` in the
  call. A command held in a constant, or `shell=True`, is not seen; its docstring names its own shapes.

## Acceptance criteria evidence
The plan's §1 row for W4 (`docs/plans/m21-plan.md:28`) adds no REQ-ID; the wave's criteria are the
controls below.
- **#200:** `scripts/check_records.py:1544`, wired at `:1842`;
  `tests/unit/test_wave_check_m21_rules.py:72`, `:83`, `:91`.
- **#183, #201, #203:** `scripts/wave_check.py:392`, wired at `:661`;
  `tests/unit/test_wave_check_m21_rules.py:141`, `:155`, `:166`, `:183`, `:192`, `:200`, `:209`, `:231`,
  `:248`.
- **#202:** `scripts/wave_check.py:473`; `tests/unit/test_wave_check_m21_rules.py:267`, `:277`, `:286`;
  the ledger row at `docs/control-events.csv:24`.
- **#182:** `tests/skips.py:83`; `tests/unit/test_ci_needs.py:38`, `:60`, `:66`.
- **#249:** `tests/unit/test_needs_git.py:74`, `:84`.
- **#179:** `Makefile:147`; `tests/unit/test_offline_run.py:146`;
  `ios/EngineTests/OfflineTestCase.swift:131`.
- **#181:** `Makefile:152`, run at `:203` and `:223`; `tests/unit/test_swift_strict_pool.py:18`;
  `ios/EngineTests/FrontDoorTests.swift:518`.
- **#178:** `tests/unit/test_fetch_bounds.py:272`.
- **#248:** `tests/unit/test_security_invariants.py:706`, `:716`.
- **#227:** `ios/UITests/ScrollStep.swift:18` and `ios/UITests/ScreenPathTests.swift:129`. ScrollStepTests
  run in `make ui-test`'s online leg, which this seat did not run.
- **#189:** `.claude/hooks/bash_guard.py` and `.claude/settings.json:49`; held by
  `conformance/test-hook-claims.py` (MUST_BLOCK and MUST_ALLOW).
- **#122:** the patch is posted on the issue (2026-10-10T00:18Z). **#108:** carried (D-183's revisit).
- **Scope.** #248 and #249 were delivered but appear neither in plan §2 W4 nor in §7's inventory; D-192
  names them. The close's row 9b should record them as added.

## Producers of hardened invariants (2a-bis)
- **INV-82 (G-7).**
  - Producers: the text reading at `.claude/settings.json:49`, and the second reading,
    `.claude/hooks/bash_guard.py`.
  - Citing test: `conformance/test-hook-claims.py`, which runs both through the hook command.
  - Gaps: B1 and M1. A session started outside the repository loads neither reading (#142).
- **INV-6 (G-5).**
  - Producers: `make test` (`scripts/offline.sb`); `make swift-test` and `make swift-test-parallel`
    (`Makefile:147`); the strict-pool rerun (`Makefile:152`).
  - Citing tests: `tests/unit/test_offline_run.py:146`, `tests/unit/test_swift_strict_pool.py:18` and
    `OfflineGuardTests/testAChildTheSuiteStartsCannotNameAnOutsidePeer`.
  - Gaps:
    - CI's test job (G-5, #122).
    - A bare `swift test` run outside `make`. This one is not silent: the new test goes red there.

## K.8 contract drift check
Plan §5: no `/v1` change; W4 changes gates. `git diff --name-only 6a41d35..d3596e1 -- src/
ios/ModelRanking/` lists 0 files. The new symbols and their only callers:
```
scripts/wave_check.py:663:        history, skipped = history_problems(p, text, root)
scripts/wave_check.py:672:            bad.extend(skip_ledger_problems(text, f"m{wave_ids.group(1)}-w{wave_ids.
scripts/check_records.py:1842:    findings += adr_pointer_findings(root)                            # A1 (#200
tests/unit/test_ci_needs.py:39:    assert ci_job_facts(WORKFLOW) == _marks()
```
Verdict: OK.

## K.9 candidates spotted outside this wave's scope
- None

## Risks queued to next M
- **R1** `Makefile:152`: the Swift legs have no timeout.
  - **Why it matters now.** The strict-pool rerun is the configuration in which a blocking regression
    hangs instead of failing. `114b4f9`'s message records an unbounded plant that hung the strict run at
    `firstWithin(1e30)` and had to be killed.
  - **What would show it is real:** a `make check` or pre-push gate that never returns after a Router
    change.
  - **Fix.** Run the strict rerun, and the legs, under a watchdog that fails with its own message. macOS
    has no `timeout`, so use a background `sleep N; kill` or a Python wrapper.
