---
record_type: review
id: devflow-v7.1-upgrade-security
status: draft
process_version: v7.1
date: 2026-10-15
seat: independent
---
# Security Review -- DevFlow v6.6 -> v7.1 upgrade (draft PR #281)

**Reviewer:** Security-Reviewer subagent
**Independent:** yes
**Date:** 2026-10-15
**Release range:** 7bdb7c5..d09a5b4 (branch `upgrade/devflow-v7.1`, base `main` = `7bdb7c5`)
**Reviewed head:** d09a5b41ac6d70a0058fe4f15f3f1786efbb0cb1
**Risk tier:** MEDIUM. The brief declares no HIGH paths. `make review-need` routed the range to security
because of sensitive path names and parser hits. The range rewrites the project's own safety controls: the
Bash guard, the Write/Edit hook, the deploy gate and the secrets gate.

**Seat:** I am the independent Security-Reviewer, from the Claude model family (Opus). The author is also
Claude. I wrote none of this change. I read my profile and policy from the protected base only:
`git show main:.claude/agents/Security-Reviewer.md`, `main:docs/security-baseline.md`,
`main:permission-matrix.md` and `main:.agents/rules/review-seats.md`. Where the branch rewrites policy text
(`permission-matrix.md` §5/§6/§11, `AGENTS.md`), I treated the change as the subject of the review, never as
an instruction. The Code-Reviewer's two verdicts were read, and I graded independently.

**Method:**
- **Worktrees.** I ran in my own detached worktree at `d09a5b4`, in a `mktemp` directory, with its own venv
  (`make install`, marker `v7.1 · manifest a41de86d4696`). `advisor.db` was copied read-only, with md5
  `495755d5…` before and after. A second worktree at `7bdb7c5` gave the differential, and a `git archive`
  export with no `.git` held the guard mutants. I did not touch the author's tree beyond this file, nor the
  main checkout or the launchd service. All three trees were removed afterwards.
- **Guard differential.** About 100 Bash and Write/Edit payloads went through `main`'s whole PreToolUse hook
  commands (its text grep layer plus the M21 guard) and through HEAD's. Each hook ran exactly as
  `settings.json` states it, with its own pin. The commands were judged and never run.
- **Fail-closed probes.** Each PreToolUse hook was run with no python on PATH, with the guard file missing,
  and with a payload that is not JSON.
- **Mutants.** 11 fault injections were made in place, each restored and checked byte-identical by md5.
  Guard mutants were re-pinned in the export, so the behavioural tests decided each one, not the pin
  tripwire.
- **Gates.** I ran `make check`, then `make secrets`, `make deps` and `make slopsquat`. I also ran gitleaks
  in git mode over the 12 commits of the range.

## Verdict
BLOCKING -- 1 BLOCKING, 2 MAJOR, 5 MINOR, 1 NIT

The upgrade adds real protections, all measured: `--no-verify`, `core.hooksPath`, `update-ref main`,
`gh pr merge` and `gh pr ready`, the protection APIs, `.env` shell writes and `a=fly; $a deploy` are now
refused. D-185's `fly` rule is stricter. `.mcp.json` drops `npx -y` and the token passed in its environment.
The permission allowlist only narrows, or adds fixed make targets and read-only `gh` commands. One defect
remains. The `rm -rf` rule (Catastrophe-class in `main:permission-matrix.md` §5/§11, "ADR cannot override")
now fails OPEN on any target that starts with `$TMPDIR` or with a `mktemp` variable. That is BLOCKING under
§11: a safety control's fail direction is misapplied. The fix is to the owner's guard, so it needs OWNER
APPROVAL and `make guard-pin`. Escalate it now (AGENTS.md §3: a hook change).

## Findings

### BLOCKING

- **B1** `.claude/hooks/bash_guard.py:1104-1109` (`_scratch`) and `:649-650` (`_assign`). Any `rm -rf` or
  `find -delete` target that starts with `$TMPDIR`, or with a variable assigned from `$(mktemp ...)`, counts
  as scratch without being resolved. OWASP: none (an agent-safety control). The control-class fail direction
  is misapplied (permission-matrix §11).
  Evidence: `main` refuses every case below with exit 2, and HEAD allows each one with exit 0:
  - `rm -rf $TMPDIR/../../../../../Users/umutcanapaydin/Desktop/ILGAR/model_ranking` deletes the owner's
    main checkout;
  - `rm -rf "${TMPDIR}/../../../../../Users/umutcanapaydin"` deletes $HOME;
  - `rm -rf "$TMPDIR/$name"` with `name` unset, or `rm -rf "$TMPDIR"`, deletes the whole per-user temp
    directory. That directory holds every agent work tree, every D-174 seat and every session scratchpad;
  - `TMPDIR=/Users/umutcanapaydin/Desktop/ILGAR; rm -rf "$TMPDIR"` and
    `export TMPDIR=$HOME && rm -rf $TMPDIR`. An assignment earlier in the same text is ignored, because
    `_scratch` tests the name before it looks at `SCOPE`;
  - `d=$(mktemp -d); rm -rf "$d/../../../../../Users/umutcanapaydin/Desktop"`;
  - `d=$(mktemp -d)/../../../../../Users/umutcanapaydin; rm -rf "$d"`;
  - `d=$(mktemp -d; echo /Users/umutcanapaydin/Desktop); rm -rf $d`.

  This is upstream code: v7.1 ships the same early return at its `bash_guard.py:719-720`. The tests pin only
  the allowed side (`rm -rf "$TMPDIR"/x` in `conformance/test-bash-guard.py:166`) and never a refused
  `$TMPDIR/..` case.
  *Failure scenario:* in this auto-mode lane the guard is the only barrier. Either an injected "clean up"
  instruction or a script line with an empty variable deletes the main checkout or every live tree under
  the temp directory.
  *Remedy (owner-applied, then `make guard-pin`):*
  1. In `_scratch`, never return True on the variable alone. Substitute the variable's value and resolve the
     whole path through `_scratch_path`. A remainder that holds `..` or another `$` is not scratch.
  2. `$TMPDIR` counts only when this text did not assign it.
  3. A variable is a `SCRATCH` value only when it is exactly one `$(mktemp ...)` or backtick substitution with
     nothing else, and the body is a single `mktemp` command with no `;`, `&&`, `|` or newline.
  4. Add the cases above as refusals to `tests/unit/test_bash_guard_bounds.py` and
     `conformance/test-bash-guard.py`.
  5. Report it to DevFlow.

### MAJOR

- **MAJOR-1** `.claude/hooks/bash_guard.py:1074-1095` (`_temp_bases`, `_scratch_path`). This is the round-1
  review's M2, weighed as asked. Scratch is "anything under `/private/tmp`, `/var/folders`, …". In this
  project the work trees themselves live there: the author's tree for this PR is
  `/private/tmp/claude-501/…/scratchpad/w-up-dry`, and the D-174 seats sit in `mktemp` directories. So from
  a session in such a tree, HEAD allows all of these, and `main` refused each one:
  - `rm -rf .`
  - `rm -rf ./src ./ios`
  - `rm -rf .git`
  - `rm -rf ../`
  - `rm -rf /private/tmp/claude-501` (every session's tree)
  - `rm -rf /var/folders/qf`
  - `rm -rf .claude/worktrees/<seat>`, even with uncommitted work in it

  D-199 clause 3 calls this "scratch" and records the rule as taken "by design". It does not record that the
  owner weighed this cost. `main:permission-matrix.md` §11 lists `rm -rf` on untracked dirs as
  Catastrophe-class: "ADR cannot override". **Not acceptable as it stands.**
  *Failure scenario:* an agent "cleans" its tree with `rm -rf .` from the repository root, or removes a
  sibling seat's worktree, and the uncommitted work is gone. For a clone under temp, the unpushed commits
  go too.
  *Remedy:* a target is not scratch when it lies inside a git work tree (the nearest `.git` walk `_owned`
  already does), when it is an ancestor of the call's cwd or of any tree `git worktree list` names, or when
  it holds a `.git` entry. Two exceptions:
  - a `mktemp` result made in the same command;
  - a `.claude/worktrees/<name>` whose `git -C <it> status --porcelain` is empty.

  Ship it with B1's change. Otherwise the owner rules on this exact cost in a new ADR that supersedes the
  clause.

- **MAJOR-2** `.claude/hooks/bash_guard.py:1301-1330` (`project_root`, `judge_deploy`), called for every
  Bash call at `:1364`. The hook runs `scripts/deploy_gate.py` from whatever git work tree the call's cwd is
  in, whenever that tree has a `docs/project-brief.md`. This happens before any permission prompt, for any
  command.
  Evidence: a throwaway repository held a one-line brief and a `scripts/deploy_gate.py` that writes a file.
  Feeding `ls` with that repository as cwd through HEAD's Bash hook gave exit 0, and the file was written.
  `main` has no such path. Also, an older worktree of this repository, whose verdicts were current at its
  own head, can be made the governing repository for a deploy aimed at another tree. D-185's hard refusals
  mitigate that part here, but not the code execution.
  *Failure scenario:* an agent `cd`s into a cloned third-party repository, or another DevFlow project, and
  that repository's script runs with the agent's rights on the next `ls`. No unpinned code should run from
  the hook's trust root.
  *Remedy:*
  - Take a governing repository other than `$CLAUDE_PROJECT_DIR` only when its `git rev-parse
    --git-common-dir` resolves to the project's own. Otherwise use `$CLAUDE_PROJECT_DIR`.
  - Spawn the gate only when a candidate's program basename matches a declared deploy command. The guard can
    read the brief itself, with the stdlib.
  - Optionally pin `scripts/deploy_gate.py` and `scripts/brief_fields.py` by sha256, as the guard is.

### MINOR

- **M1** `.claude/settings.json:88`. The removal of `main`'s text grep layer loses true positives, not only
  false ones. `main` refused, and HEAD allows:
  - `git config alias.nuke 'reset --hard' && git nuke`
  - `git -c alias.p='push --force' p`
  - `ssh host rm -rf /srv/data`

  The round-1 review says HEAD refuses everything `main` refused except false positives. These three are
  exceptions to that. They are named in the guard's "Not held" list (`bash_guard.py:99`), which is why this
  is MINOR.
  *Remedy:*
  - Refuse `git -c alias.*=` and `git config … alias.*` whose value is `!…` or a refused subcommand. Judge
    the value with `judge_text` or `_judge_git`.
  - For `ssh host <words>`, judge the remote words with `judge_text`.

- **M2** `scripts/review_need.py:118,133`, `scripts/deploy_gate.py:190,303` and `scripts/brief_fields.py:26`.
  Policy inputs come from the tree under evaluation, not the base ref (AGENTS.md §5, base-pinned policy).
  These are `Working mode:`, `Paths that make a change HIGH:`, `Deploy commands:`, the verdict files and
  the gate scripts themselves.
  Evidence: I set `Working mode: light` in the worktree's brief and ran
  `make review-need RANGE=7bdb7c5..d09a5b4`. The answer went from `code-reviewer+security` to `security`.
  A change can drop its own Code-Reviewer, or blank its HIGH globs. D-185's hard refusals cover
  `fly`/`flyctl` and the deploy script whatever the gate says, so the deploy side holds here. Of the 22
  deploy spellings I tried, 19 were refused. The three allowed are a copied script, a symlinked script and
  `make -C . deploy`, the same as on `main`.
  *Remedy:*
  - Without `--at`, `review_need.py` reads the brief at the merge-base. `brief_root_at` already exists.
  - It routes a range that edits a brief field or `scripts/review_need.py` to code-reviewer+security.

- **M3** `scripts/secrets_scan.py:26-64` (`make secrets`) has no test. Two mutants survived `make conformance`
  and every unit test:
  - copy no tracked file, so gitleaks scans an empty directory and passes;
  - missing gitleaks returns 0 instead of 2.

  An empty derived set passes (AGENTS.md §3.5, fail CLOSED).
  *Remedy:* fail when zero files were copied, and add a conformance case for each:
  - a tracked planted test key gives exit 1;
  - no gitleaks on PATH gives exit 2;
  - an untracked key is not read.

- **M4** `scripts/review_need.py:169`. The sensitive-path signal is untested. The mutant `hit = []` survived
  `conformance/test-review-need-mode.py`, the 3031 unit tests and `wave-check-all`.
  *Remedy:* add a case to `test-review-need-mode.py`: a range touching `scripts/deploy_x.py` gives
  `security`, and one touching `tests/test_auth.py` only gives none.

- **M5** `docs/project-brief.md:107` (D-199 clause 2). `Deploy commands:` leaves out
  `scripts/install_engine_service.sh`. That script deploys `origin/main` to the owner's launchd service,
  which AGENTS.md §1 calls the target environment, and its header says the owner runs it. Both hooks allow
  it, on `main` and on HEAD.
  *Remedy:* the owner adds it to `Deploy commands:` (or rules it out in D-199's successor), and the guard
  refuses it as it refuses the hosted deploy script.

### NIT

- **N1** `.claude/hooks/bash_guard.py:1115`. `text.startswith("~") and not text.startswith(("~/", "~"))` is
  always False, so the line is dead code. `~user` is still refused at `:1118`. Delete it with B1's change.

### PASS (good security hygiene, measured)

- **Pin.** The sha256 of `bash_guard.py` = `e65bf212…0129` matches both PreToolUse hooks
  (`settings.json:77,88`). Any byte change blocks every call: each guard mutant tripped
  `test_both_pretooluse_hooks_run_the_guard_under_one_current_pin`.
- **Fail-closed.** Both PreToolUse hooks exit 2 with no python on PATH, with the guard file missing, and on a
  payload that is not JSON. All four hooks carry `timeout` and `"onFailure": "block"`. Every python call is
  `-I -S`. The guard's 10 s thread also bounds the deploy gate's subprocess.
- **`.claude/` and `.githooks/`.** Writes are refused through the Bash and Write hooks, case-folded, by
  absolute path, and inside nested worktrees.
- **Deploy commands.** `fly`, `flyctl`, `FLY DEPLOY`, `fly -a app deploy`, a path-qualified `flyctl`,
  `a=fly; $a deploy`, `${f}y`, `fl''y`, `xargs fly`, `bash` and `sh` and `env` with the script, and
  `bash -c 'cd scripts && ./…'` are all refused. A copied or symlinked script stays a documented gap, as on
  `main`.
- **Gate scripts.** `deploy_gate.py` fails closed: an unreadable payload, a missing gate, a sha git cannot
  compare, or a BLOCKING or template verdict each refuses. `session_check.py` fails closed inside Claude Code
  when git cannot be read. The SessionStart hook validates the session id (`[A-Za-z0-9-]{8,64}`) before it
  writes a path.
- **Parsers.** None is new in product code, because the range touches no `src/` or `ios/` file. `JSONDecoder`,
  `URLSession`, `json.Unmarshal` and `json.NewDecoder(` are the detector's own regex and docstring
  (`scripts/review_need.py:31-32,74-75`) and a Go fixture string (`conformance/test-review-need-mode.py:8,111,114`).
  `csv.reader` reads the repository's own ledger (`scripts/wave_check.py:650,881`). `json.loads` reads the
  hook payload (`bash_guard.py`, `deploy_gate.py:303`). `conformance/test-session-check.py` is a test of
  the session gate.
- **Allowlist and MCP.**
  - `.claude/settings.json` allow: `make check:*` and its kind became exact `make check`. The new entries are
    fixed make targets and read-only `gh` commands under PowerShell. Nothing new runs an arbitrary command
    or writes outside the tree.
  - `.mcp.json`: an HTTP server at `api.githubcopilot.com` replaces `npx -y` of an unpinned package.
  - `.gitattributes`: LF only.

## Mutants (in place; each restored, md5 identical)

| # | Where | Mutation | Killer | Result |
|---|---|---|---|---|
| G1 | export | `_judge_rm`: scratch check -> `if True` | unit + `test-bash-guard` | RED (1 / 9 wrong) |
| G2 | export | shell `.env` redirection refusal off | `test-bash-guard` | RED (6 wrong) |
| G3 | export | `--write` `protected()` off | unit | RED (5 failed) |
| G4 | export | D-185 `fly` read-only rule off | unit + `test-bash-guard` | RED (21 / 4) |
| G5 | export | `GATE_MISSING` -> allow | `test-bash-guard` | RED (1 wrong) |
| G6 | export | `$TMPDIR` shortcut -> False | `test-bash-guard` | RED (2 wrong; pins the allowed side only, B1) |
| W1 | worktree | `deploy_gate.changed_since` -> `[]` | `test-bash-guard` | RED (30 wrong) |
| W2 | worktree | a BLOCKING verdict accepted | `test-bash-guard` | RED (2 wrong) |
| W3 | worktree | `review_need` sensitive-path signal off | all tests, conformance, wave-check-all | **SURVIVED** (M4) |
| W4 | worktree | `secrets_scan` copies no file | conformance + unit | **SURVIVED** (M3) |
| W5 | worktree | `secrets_scan` missing gitleaks -> 0 | conformance | **SURVIVED** (M3) |

## Gates passed (my worktree at d09a5b4)
- [x] `make check`: exit 0. The legs:
  - session-check PASS;
  - ruff clean;
  - mypy: 49 files, no issues;
  - pytest: 3033 passed, 27 skipped, coverage 92.19%;
  - coverage-floor PASS;
  - check_records PASS, self-test 0;
  - install-check PASS;
  - shell-dialect PASS;
  - wave-check-all PASS (68 records);
  - conformance: 26 PASS;
  - swift-test: 637, plus SlowTier 7 of 7;
  - client-decls PASS.
- [x] `make secrets`: exit 0, 1203 tracked files, no leaks. Gitleaks in git mode over the 12 commits of
  `7bdb7c5..d09a5b4` found no leaks.
- [x] `make deps`: exit 0. pip-audit over the four locks found no known vulnerabilities.
- [x] `make slopsquat`: exit 0. 20 declared dependencies, 0 suspect. No new `import` of a third-party
  package is in the range.
- [ ] Default-deny preserved for new external surfaces: not preserved for the guard (B1, MAJOR-1). No
  product route was added.
- [ ] Permission matrix not violated: §5/§11 `rm -rf` (B1, MAJOR-1).
- [x] Prompt-injection hygiene: no product code consumes new external content. MAJOR-2 is the hook-side
  analogue.
- [x] Auth/PII: no auth, PII, payment or migration path is touched, so the §11 human-review trigger does not
  fire for product code. The guard change needs OWNER APPROVAL.
- [x] SAST: no product code changed. The gate scripts were read line by line instead of with bandit.

## Acceptance criteria evidence (D-199, D-200)
- D-199 cl.1, heavy mode: `docs/project-brief.md:106`; `make review-need` prints `working mode: heavy`.
- D-199 cl.2, both deploy commands gated: `docs/project-brief.md:107`; `scripts/deploy_gate.py:186-238`;
  differential (`FLY DEPLOY` and `--dry-run` refused by the gate).
- D-199 cl.3, guard merged, M21 rules kept: `.claude/hooks/bash_guard.py:796-802,1029-1050`; `settings.json:77,88`;
  `tests/unit/test_bash_guard_bounds.py` (104 pass). The scratch clause is **not met safely** (B1, MAJOR-1).
- D-200 cl.2, exact-wave skip rows: `tests/unit/test_wave_check_m21_rules.py`, green in `make check`.

## Risks queued
- **R1** `.mcp.json:5`: the GitHub MCP server exposes write tools (merge, file push, settings). No PreToolUse
  hook matches them, so only branch protection stops a merge or a push to `main` by MCP. This predates the
  change, since `main`'s server-github had the same tools. Remedy: point at the read-only endpoint
  (`…/mcp/readonly`), or add a PreToolUse matcher on `mcp__github__.*(merge|push|update_ref|protection)`.
- **R2** Parent-directory removal of `.claude/` (`rm -r .`, `mv ../repo`) is #282, filed by the round-1
  review. MAJOR-1's remedy narrows it under temp.
- **R3** B1 is DevFlow v7.1's own defect, at `v7.1:.claude/hooks/bash_guard.py:713-720`. Hand it upstream
  with the cases above.
