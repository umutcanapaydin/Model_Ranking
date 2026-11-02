---
record_type: review
id: fix-issue-553-security
status: draft
seat: independent
process_version: v7.3.1
date: 2026-11-02
---
# Security Review — fix-issue-553

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need` says `security`: a policy edit of `scripts/deploy_gate.py`, #283)
**Independent:** yes. This seat wrote none of `ae0d42a` or `c4a0ad1`. It worked in its own detached work tree (`wt-sec-553`) with its own venv, and it read policy from the base.
**Date:** 2026-11-02
**Release range:** 799efe5..c4a0ad1
**Reviewed head:** 6bc67ac38c5866540f1e30bb7ce679cf63553031
**Risk tier:** MEDIUM. The change edits a fail-closed deploy control (D-239, D-242). The brief declares no HIGH paths (`Paths that make a change HIGH: none`), and no auth, PII, payment or migration code is touched, so no senior-review line is owed.

## Verdict
MINOR

*(Round 2 at `6bc67ac`; round 1 below was BLOCKING at `c4a0ad1`. Each round-1 item's disposition is under "Round 2".)*

Round 1 (at `c4a0ad1`): the fix closes every shape #553 names: all 19 REFUSED and 6 QUIET cases pass. The real `nightly-hosted.yml` stays quiet. But three of the fix's own mechanisms make the gate **refuse less than at the base**. With each shape below planted in a dispatched deploy workflow, `799efe5` refuses `fly deploy` and `c4a0ad1` lets it through (exit 0).

Method: a side-by-side probe imports `scripts/deploy_gate.py` at `799efe5` and at `c4a0ad1` and runs `_unreadable_runs` + `_startup_values` + `_run_values` → `_run_commands` → `_unnamed_shapes` over the same workflow text. Each regression was then driven through the real entry point (`tests/unit/test_deploy_gate_549.py::_dispatched` + `_deploy`, i.e. `deploy_gate.py` judging `fly deploy`): every one exits 0, and the control `bash scripts/*.sh` exits 2. The shell readings were checked by running them under `/bin/bash` 3.2 and Homebrew bash 5.x.

## Findings

### BLOCKING

- **B1** `scripts/deploy_gate.py:987` (`_strip_comment`, called at `:1016`) — a regression in the comment stripper. It treats `#` after a blank, `;`, `&`, `|`, `(`, `)`, `<` or `>` as a comment start everywhere outside `'`/`"`. The shell does not, inside a parameter expansion `${...}`, an ANSI-C string `$'...'` (where `\'` does not close), a backtick or `$(( ))`. The stripper drops the rest of the line. At the base, `lexer.commenters = ""` (`:1002`) read those words.
  Failure scenarios (base refuses, head passes `fly deploy`):
  ```yaml
        - run: |
            script=${entry%% #*}; bash "$script"
  ```
  ```yaml
        - run: |
            echo $'it\'s # ' ; bash scripts/*.sh
  ```
  ```yaml
        - run: |
            echo `echo hi #x` ; bash scripts/*.sh
  ```
  Evidence: bash 3.2 and 5.x print `RAN` for each of these (the file after `;` is started). Base reader: `['5: a name built at run time in the file `bash` runs `$script`']`. Head reader: `[]`. Real gate at head: `exit=0`.
  `${line%% #*}` (strip a trailing comment) is a common idiom.
  Remedy: do not strip a `#` inside `${`, `$(`, `$((` or a backtick, and read `$'...'` with its `\'` escape. Or, simpler and fail closed: read each line both stripped and unstripped, and refuse if either reading refuses.

- **B2** `scripts/deploy_gate.py:1078-1080` (`_run_commands`, the descriptor pop) — a regression in the descriptor pop. It pops any all-digits word that comes right before a redirection token. The tokens come from `shlex`, which drops whitespace, so `60 >x` cannot be told from `60>x`. The shell reads digits as a descriptor only when they touch the operator: `timeout 60 >log x` gives `timeout` the duration `60`. Popping the digits shifts a wrapper's value or a starter option's value onto the started file, which `_program_position` / `_starter_shapes` then consume as the value.
  Failure scenarios (base refuses, head passes):
  ```yaml
        - run: timeout 60 >/dev/null scripts/*.sh
        - run: timeout 60 >log "$S"
        - run: nice -n 5 >log scripts/*.sh
        - run: python -W 2 >x scripts/*.py
  ```
  Evidence: probe `timeout-space-redir` base=1 finding, head `[]`. Real gate at head: `exit=0`.
  Remedy: pop only when the digits touch the operator in the source text, which needs offsets. Or read both ways (with and without the pop) and refuse if either refuses.

- **B3** `scripts/deploy_gate.py:218` (`WRAPPER_VALUED["env"]` holds `-S` and `--split-string`), used by `_program_position` (`:1493-1513`) — a regression in the reader and in the deploy matcher. `env -S STRING` does not take a value beside the program: STRING *is* the command line, which env splits and runs. Reading it as an option value drops the program.
  - Run reader. `env -S 'bash scripts/*.sh'` and `env -S "$CMD"`: at the base the program word held `*`/`$` and refused. At the head, nothing is left after the value, so nothing refuses. Verified: `env -S "bash s.sh"` prints `RAN`. Real gate at head: `exit=0`.
  - Deploy matcher. `_runs_deploy` (`:1768-1779`, which decides which workflows are deploy workflows in `deploy_workflows` `:1799`) at the base reads `run: env -S fly deploy --remote-only` as `fly deploy`: `_runs_deploy` → `True`, and `matches(['env','-S','fly','deploy'], ['fly','deploy'])` → `True`. At the head both are `False`. A workflow that deploys this way (one no declared `gh workflow run` dispatches) drops off the deploy surface, and D-239 no longer reads its run values. The Bash guard's own path still catches `env -S fly deploy` typed as a command, because the guard reads `-S` itself and tries every word after a wrapper (`.claude/hooks/bash_guard.py:1784-1808`). The workflow-reading path has no such fallback.
  Remedy: in the run reader, read the `-S` value as run text (as `eval`'s is, `_shapes_in(value + " " + rest)`). In `_program_position`, do not consume `-S` / `--split-string` (or `-S...` glued). Return the split string's words instead, or treat the command as unread.

### MINOR

- **M1** `scripts/deploy_gate.py:940-948` (`_yaml_quoted`) — the unquoting is not correct enough (question 3).
  (a) Double decoding, a regression. `re.sub` turns `\\` into `\`, and the chained `.replace("\\t", "\t")` then turns that `\t` into a TAB. `run: "bash scripts/\\t*.sh"` (YAML value `bash scripts/\t*.sh`, which bash reads as the pattern `scripts/t*.sh`) is split by the reader at the TAB into `bash`, `scripts/`, `*.sh`, so it no longer refuses. The base refused it. Real gate at head: `exit=0`.
  (b) Escapes it does not decode hide a pattern or an expansion: `run: "bash scripts/\x2a.sh"`, `"*"`, `"bash \x24S"` (YAML: `*` and `$`). They are read literally and not refused. The base missed these too, but the new quoted-value path claims to read them.
  `'*'` single-quoted is correct (no escapes in YAML single quotes, `''` handled).
  Remedy: decode in one pass with the full YAML double-quoted escape table, or count any `\` escape other than `\"`, `\\` and `\/` as unreadable (refuse).

- **M2** `scripts/deploy_gate.py:1166-1167` (interpreter clusters ending in `W`/`X` take a value) — a narrow regression. The rule is right for python (`-W arg`, `-X opt`). For perl, `-X` and `-W` are flags, and ruby's and lua's `-W` is a flag. `run: perl -wX scripts/*.pl` refused at the base; at the head the cluster consumes the script. Verified: `perl -wX s.sh` runs `s.sh` as perl. Real gate at head: `exit=0`. The bare `-W`/`-X` in `STARTER_VALUED` (`:872`) has the same flaw for perl, from before this change.
  Remedy: valued options per interpreter family, as `WRAPPER_VALUED` does for wrappers.

- **M3** Shapes the reader cannot place and does not refuse (question 2; not regressions — base missed each too, but the fix's rule "what it cannot place refuses" does not hold for them). Each was probed, and none refuses at the head:
  - `- run : bash scripts/*.sh` and `- "run" : bash scripts/*.sh` (blank before the colon, valid YAML): `_RUN_KEY` (`:879`) needs `run:`.
  - `- ? run` / `  : bash scripts/*.sh` (explicit key).
  - `- run: &a bash scripts/*.sh` (anchor on a plain value: read as `&` then the program `a`).
  - `- run: !!str bash scripts/*.sh` and `- run: !!str "bash scripts/*.sh"` (tag).
  - A folded scalar with a blank or more-indented line. YAML keeps those newlines, but `:921` joins every line into one, so a command after the break is read as arguments: `- run: >` / `    echo hi` / *(blank)* / `    bash scripts/*.sh` passes. So does `run: >-` with `echo hi # c` followed by a more-indented `  bash scripts/*.sh`, where the stripped comment now also swallows the next line's text. Real gate at head: `exit=0`.
  - `env: {BASH_ENV: "$F"}` (flow mapping): `_STARTUP_KEY` (`:884`) reads block keys only.
  - `bash -oe pipefail scripts/*.sh`: bash consumes `pipefail` for an `o` anywhere in the cluster (verified: `pipefail on`), but `:1166` only for a trailing `o`/`O`.
  - `bash {fd}>/dev/null scripts/*.sh` (named descriptor; bash 5 runs `s.sh`): `{fd}` is read as the file.

  Anchors and aliases are already safe: a `<<: *x` merge or `run: *r` alias refuses, since `*r` reads as a pattern. A multi-document file and a block scalar whose quote runs on also refuse. Tabs in indentation are invalid YAML, so GitHub rejects them.
  Remedy: refuse on `run\s+:`, a `?` key, a run value starting with `&` or `!`, a folded scalar holding a blank or more-indented line (or fold it as YAML does), and `BASH_ENV`/`ENV` inside a flow mapping. Treat each `o`/`O` in a shell cluster as taking one word.

- **M4** `scripts/deploy_gate.py:884`, `:1132` — over-refusal, which fails closed but teaches the owner to fight the gate. (a) `ENV` is read as a startup file for every shell, yet `sh` and `dash` read `ENV` only when interactive. `env:` / `  ENV: ${{ inputs.environment }}`, a common workflow idiom, now refuses every deploy (probe `env-ENV-key`: `startup 5 ${{ inputs.environment }}`), as does `run: ENV=$STAGE scripts/ship_it.sh`. (b) `run: "scripts/ship_it.sh" # ship`, a quoted value with a YAML comment, is refused as "a quote running past its line".
  Remedy: limit `ENV` to an interactive start (`sh -i`, `bash --posix -i`), or note the false refusal in D-239. Strip a YAML comment after a closed quote before `_yaml_quoted`.

### PASS
- Every REFUSED shape #553 names refuses and every QUIET one passes: `tests/unit/test_deploy_gate_553.py`, 25 cases.
- The D-239/D-242 suites stay green at `c4a0ad1`: `test_deploy_gate_553.py`, `test_deploy_gate_549*.py`, `test_deploy_gate_522*.py`, `test_deploy_gate_541*.py` and `test_deploy_gate_dispatch.py` give **238 passed** (pytest-xdist, own venv). The subset's coverage-floor line is expected.
- `make deploy-check` on the tree prints `workflows: nightly-hosted.yml read, 37 run command(s), no start of a file without its name (D-239)`. It then fails only on the stale release verdicts at `1a5fec0`, as expected for an unreleased change.
- The head reads the real workflows no worse than the base: `nightly-hosted.yml` gives `[]` at both. `contract-tests.yml:160`'s comment line was a false read at the base and is gone at the head.
- These pieces are correct and refuse more than the base:
  - per-wrapper valued sets for `sudo -n`, `doas -s`, `caffeinate -s` and `ionice -t`, which the base default set mis-read as valued and so consumed the program;
  - `timeout --foreground 600 fly deploy`, now seen as a deploy;
  - `exec -a`, `stdbuf -o`, `time -o`;
  - `--` ending wrapper options;
  - `bash -eo pipefail`;
  - `BASH_ENV` set inline, exported, through `env` or `declare -x`, and under a job- or step-level `env:`;
  - a plain value continued on the next line, and a value on the next line;
  - flow-mapping refusal, quoted keys, and `|2` indentation indicators.
- No new import, subprocess, `eval` or file write in the diff: it is parsing only.

## Gates passed
- [x] Secret scan green: `make secrets` in the review tree at `c4a0ad1` — `no leaks found`
- [x] `make deps`: no dependency added; the only new import is `pytest` in a test, already declared
- [x] `make slopsquat`: no new third-party import
- [x] Default-deny preserved for new external surfaces: none added
- [ ] Permission-matrix not violated: the control's fail-closed direction (AGENTS.md section 5, "auth/safety fail CLOSED") is loosened by B1–B3
- [x] Prompt-injection hygiene: n/a (no external content consumed beyond workflow text read as data)
- [x] Auth/PII checks + human review trigger: n/a (no HIGH path; no auth, PII, payment or migration)
- [x] SAST: bandit is not in the venv. Manual review: the diff adds regexes and string handling only, with no `subprocess`, `eval` or `exec`.

## Acceptance criteria evidence
- #553 M1 (comments) → `tests/unit/test_deploy_gate_553.py:25-27` (refused), `:56` (quiet), code `scripts/deploy_gate.py:970-991`, `:1016`. Holds for the named shapes; B1 is the regression it introduces.
- #553 M2 (option values, descriptors, wrappers, BASH_ENV) → `tests/unit/test_deploy_gate_553.py:29-40`, `:58-60`, code `:1078-1080`, `:1130-1135`, `:1165-1168`, `:211-224`, `:1493-1513`. B2, B3 and M2 are the regressions.
- #553 M3 (plain continued, quoted, flow, quoted key) → `tests/unit/test_deploy_gate_553.py:42-46`, `:57`, `:62`, code `:879-884`, `:891-962`. M1 and M3 are the gaps.
- D-239 clause 4 (fail closed) and D-242 → the 549/522/541/dispatch suites stay green (238 passed).

## Risks queued
- **R1** `BASH_ENV` written to `$GITHUB_ENV` for later steps (`printf 'BASH_ENV=%s\n' "$F" >> "$GITHUB_ENV"`, or a heredoc into it) is not read. `echo "BASH_ENV=$F" >> $GITHUB_ENV` refuses only by accident, because the echo argument looks like an assignment word. D-239 and D-242 do not name this class; it needs an issue or a line in D-239's mitigation.
- **R2** The 553 test file has no differential guard of the kind "never refuses less than the base". Every regression above is a shape the base refused. A corpus test (each shape refused at the merge-base stays refused) would have caught B1–B3, M1(a) and M2.
- **R3** Still unseen as deploys by `_runs_deploy`, at the base as at the head: `run: env -S "fly deploy"` (quoted `-S` string) and `run: nice -n 5 2>&1 fly deploy` (`split_line` splits at `>&`, so the command is cut at the redirection).

## Round 2

**Head:** `6bc67ac38c5866540f1e30bb7ce679cf63553031` (the review tree checked out detached there; code delta `c4a0ad1..6bc67ac` in `scripts/deploy_gate.py` and `tests/unit/test_deploy_gate_553.py`). **Verdict: MINOR.** No change in the range now makes the gate refuse less than the base `799efe5` does, on any shape this seat can reproduce in a real shell.

**Method.**
- A differential probe runs the base reader against the round-2 reader, read as `unnamed_starts` now reads it (`new=True` and `new=False`, the findings unioned). It covered 251 workflow texts: every round-1 probe, plus every multi-line string holding `run` in `tests/unit/test_deploy_gate_5*.py`. One case is refused at the base and passed at the head: `timeout 60 -s KILL scripts/*.sh`, which is not a real start (see the union check below).
- Every round-1 BLOCKING shape, driven through the real entry point (`_dispatched` + `_deploy`, the gate judging `fly deploy`), now exits 2.
- The D-239 suites pass: `test_deploy_gate_553.py`, `549*`, `522*`, `541*`, `556`, `dispatch` give **266 passed**.
- `make deploy-check` prints `workflows: nightly-hosted.yml read, 37 run command(s), no start of a file without its name (D-239)`, the same count as at the base.

### Dispositions
- **B1 — fixed.**
  - `scripts/deploy_gate.py:1028-1033`: `_strip_comment` now treats `$'`, `${` and `$(` as openers.
  - `:1036-1039`: the closers and the backtick toggle are tracked.
  - `:1040`: a `#` at depth or inside backticks is not a comment.
  - `:1069`: the comment strip runs in the new reading only.
  - Probes `param-hash`, `ansi-c-quote` and `backtick-comment` refuse (real gate exit 2). Tests: `tests/unit/test_deploy_gate_553.py` `REVIEW_REFUSED` `hash-in-*`.
- **B2 — fixed by the union.**
  - `:1132`: the descriptor pop runs in the new reading only.
  - `:1269-1274`: the old reading keeps the digits, and either reading's start is a finding.
  - Probes `timeout-space-redir`, `nice-n-redir` and `python-W-space-redir` refuse. Tests: `REVIEW_REFUSED` `*-then-redirect`.
- **B3 — fixed.**
  - `:219`: `env` no longer counts `-S`/`--split-string` as valued, so `env -S 'bash scripts/*.sh'` and `env -S "$CMD"` refuse again (exit 2).
  - `_runs_deploy("run: env -S fly deploy --remote-only", [["fly","deploy"]])` is `True` again.
  - Test: `test_env_split_string_still_names_a_deploy_workflow`.
  - `sudo -h` was dropped from the valued set (`:221`). This is harmless: real sudo refuses `-h host cmd` unless it is listing.
- **M1 — fixed.**
  - `:956-990`: `_yaml_quoted` decodes in one pass from YAML's escape table (`:892-894`), including `\x`, `\u` and `\U`.
  - An escape YAML refuses returns None and so refuses (`:981`).
  - A trailing comment after the closing quote is allowed (`:989-991`).
  - `"bash scripts/\\t*.sh"` now reads `scripts/t*.sh` and refuses; `\x2a`, `*` and `\x24` refuse.
- **M2 — fixed.**
  - `:1222-1223`: the `W`/`X` cluster rule applies to `python*`/`pypy*` only, and in the new reading only.
  - `perl -wX scripts/*.pl` refuses.
  - The bare `-W`/`-X` in `STARTER_VALUED` (`:874`) still reads perl's flags as valued. That is pre-existing, and the base misses `perl -X scripts/*.pl` too: see R4.
- **M3 — fixed, except tabs (invalid YAML, so not a hole).**
  - `run :` and `"run" :` (`:881`), `? run` (`:885`, refused at `:1001`), and `&`/`!` values (refused at `:1002`) are now placed or refused.
  - A folded value is read line by line as well as joined (`:936`), so the blank-line and more-indented shapes refuse.
  - `BASH_ENV` in a flow mapping is read (`:888`).
  - A shell cluster holding `o` anywhere takes a value (`:1222`).
  - `{fd}` is popped as a descriptor (`:1134`).
  - Each one is in `REVIEW_REFUSED`.
- **M4 — fixed.**
  - `ENV` is dropped (`:886-889`, `_STARTUP_WORD`), so `env:` / `ENV: ${{ inputs.environment }}` passes (exit 0).
  - A quoted value followed by a comment passes.
  - Tests: `REVIEW_QUIET`.
- **R1, R3 — not blocking.** Both were missed at the base too and neither is a regression. R1 (`BASH_ENV` through `$GITHUB_ENV`) is a class D-239 and D-242 do not name: file it, or add a line to D-239's mitigation. R3 is outside #553's reader.
- **R2 — taken** as the class fix: the union at `:1269-1274`.

### The union and the count (the coordinator's two questions)
- **Is the old reading the base reader? Yes, except for three shared pieces.**
  - `new=False` drops the comment strip (`:1069`), the descriptor pop (`:1132`) and the new clusters (`:1220-1223`). It reads the raw value (`:915-916`) and joins a folded value (`:937-938`).
  - Three pieces are shared by both readings and changed since the base:
    1. `_RUN_KEY`'s column now counts `- `. The base ended a `- run: |` block at the dash's column, the head at the key's. PyYAML rejects block content at column 7 or 8 under `      - run: |`, so the head drops no line YAML keeps.
    2. The early `BASH_ENV` return in `_unnamed_shapes` returns only when it holds a finding.
    3. `_program_position`'s per-wrapper sets: the only base-refused case they lose is `timeout 60 -s KILL x`. GNU `timeout` parses with a leading `+` in its getopt string, so options after the duration are not its own, and the program it runs is `-s`, not `x`. This is not a start.
  - No hole found.
- **Does `runs` count each command once? Not quite, and only for folded values: R5.** `runs += new` (`:1272`) counts the new reading only, so the old reading does not double the count. `nightly-hosted.yml` reads 37, as at the base. But a folded (`>`) value is read twice in the new reading (`:936`: line by line, then joined), so its commands count twice. The probe `folded-count`, two `echo` lines, gives `runs=3`.

### Round 2 findings

#### BLOCKING
- none

#### MINOR
- **M5** `scripts/deploy_gate.py:915-917`, `:956-990` — a decoded `\n` is not a command break. `_yaml_quoted` turns a YAML `\n` escape into a newline, but `_run_values` keeps the result as one line, and `shlex` reads the newline as a blank, not a command separator. So `run: "echo hi\nbash scripts/\x2a.sh"` passes the gate: real gate exit 0. PyYAML reads that value as `echo hi` / `bash scripts/*.sh`, and bash starts the pattern. This is not a regression, since the base passed it too: the raw word holds no `*`. The hole is in the new quoted reader, and needs both a `\n` escape and an escaped pattern or expansion character (`\x2a`, `\x24`, `*`). A literal `*` or `$` is caught by the old reading. Remedy: `out.append((i, quoted.split("\n")))` at `:917`, plus a test.

#### Risks queued
- **R4** Pre-existing, not a regression. `STARTER_VALUED`'s bare `-W`/`-X` (`:874`) makes `perl -X scripts/*.pl` and `ruby -W scripts/*.rb` pass at the base and at the head. `bash -oc pipefail 'scripts/*.sh'` also passes at both: the `c` cluster rule (`:1212`) takes `pipefail` as the `-c` string. A per-interpreter valued table would close both.
- **R5** `:936`, `:1272`: the #556 run count counts a folded value's commands twice in the new reading. This is evidence accuracy, not a loosening: the nightly has no folded `run:` and still reads 37.
