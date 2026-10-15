---
record_type: review
id: devflow-v7.1-upgrade-security-rereview
status: draft
process_version: v7.1
date: 2026-10-16
seat: independent
---
# Security Re-review -- DevFlow v6.6 -> v7.1 upgrade, round 2 (draft PR #281)

**Reviewer:** Security-Reviewer subagent (the same seat as round 1, `devflow-v7.1-upgrade-security.md`)
**Independent:** yes
**Date:** 2026-10-16
**Release range:** d09a5b4..b4dc1f3 (the delta since round 1), on top of 7bdb7c5..d09a5b4
**Reviewed head:** b4dc1f371e8ce4868c38f63bc372d11be3c58c71
**Risk tier:** MEDIUM, as in round 1. The delta rewrites the Bash guard, the pin in `.claude/settings.json`
and `scripts/secrets_scan.py`.

**Seat:** I am the independent Security-Reviewer, from the Claude model family (Opus). I wrote none of the fix
commits. I read my policy from `main` only, never from the branch. **Method:**
- **Worktrees.** I made a fresh detached worktree at `b4dc1f3` with its own venv (`make install`).
  `advisor.db` was copied read-only, and its md5 was unchanged. Two more worktrees, at `d09a5b4` and at
  `7bdb7c5`, served the differential.
- **Differential.** Every round-1 payload, plus 47 new ones, went through the three trees' whole PreToolUse
  hooks. Each hook ran with its own pin, and every command was judged only, never run.
- **Probes.** I built real fixtures under a `mktemp` directory: symlinks, an unreadable directory, a bare
  repository, a separate git dir, a nested repository, and a foreign repository with a `core.fsmonitor`.
- **Mutants.** I made 13 mutants: 9 guard mutants in a `git archive` export, re-pinned so the behavioural
  tests decide each one, and 4 in place in the worktree. Every file was restored, and its md5 checked.
- **Gates.** `make check`, `make secrets`, `make deps` and `make slopsquat`.

The worktrees and the export were removed afterwards. Nothing in the author's tree was touched except this
file. Two fixture directories hold git repositories by design, and the patched guard rightly refuses
`rm -rf` of them (MAJOR-1). I did not route around that refusal. They are left for the owner to delete:
- `/var/folders/qf/hmdttd7d5cb6nl3jt1myygqw0000gn/T/tmp.nj1lYKVoXv`
- `/var/folders/qf/hmdttd7d5cb6nl3jt1myygqw0000gn/T/tmp.y8GsLuWx4s` (holds an inert `core.fsmonitor` script)

## Verdict
BLOCKING -- 1 BLOCKING, 0 MAJOR, 3 MINOR, 3 NIT

Every round-1 repro is now refused: 11 of 11 for B1, 7 of 7 for MAJOR-1 and 3 of 3 for M1. #282 holds too.
The pin is right, and both hooks fail closed. Nothing `main` or `d09a5b4` refused is allowed now, beyond what
round 1 already ruled by design. The patch is careful work.

One BLOCKING remains, in B1's class. The guard reads an assignment written before a command (`HOME=… cmd`) as
setting the variable for that command's own words and for every later command. The shell does neither. So the
guard takes `rm -rf "$HOME"` for a `mktemp` directory, while the shell expands it to the real home. The fix is
one more owner patch to the guard, with `make guard-pin`.

## Round-1 findings

| Finding | Status | Evidence |
|---|---|---|
| **B1** | **Partly closed; still BLOCKING (B1-R, below)** | All 11 round-1 repros, and the new `read`, `for`, `unset`, `printf -v`, `mktemp()` and `export "$(…)DIR="` forms, now exit 2 (`bash_guard.py:689-703,1260-1295`). Mutants N2 and N3 are killed. A prefix assignment still passes |
| **MAJOR-1** | **Closed** for trees under temp; a residual is MINOR R1 | `rm -rf .`, `./src ./ios`, `.git`, `../`, `/private/tmp/claude-501`, `/var/folders/qf` and the author's tree now exit 2. A nested repository, a separate work tree, an unreadable directory and a symlink to a tree are refused too (`:1234-1257`). Mutant N1 is killed (10 tests) |
| **MAJOR-2** | **Downgraded to MINOR R2**: closed for the case round 1 showed; the residual is acceptable as documented | `ls` in a foreign repository no longer runs its script (`:1560-1600`; mutant N7 killed, 3 tests). Residual measured below |
| **M1** | **Closed**; two narrow residuals are NIT N2 and N3 | The three repros, `git config --global alias.x '!rm -rf ~'`, `git config set alias.x 'push --force'`, `ssh -p 22 host rm -rf …` and `ssh host 'rm -rf ~/Desktop'` are refused (`:1393-1411,1466-1510`). Mutants N5 and N6 are killed |
| **M2** | Open, filed #283, out of #281 by the owner's choice | -- |
| **M3** | **Closed** | The mutants that copy no file, that return 0 with no gitleaks, and that skip the new `n == 0` check (`scripts/secrets_scan.py:59-64`) each fail `tests/unit/test_secrets_scan.py` |
| **M4** | **Closed** | The `hit = []` mutant fails 2 tests in `tests/unit/test_review_need_sensitive_paths.py` |
| **M5** | Open, filed #284, out of #281 by the owner's choice | -- |
| **N1** | **Closed** | The dead `~` line is gone from `_scratch` |
| #282 | **Closed** | `rm -r .`, `rm -r ..`, `mv ../sec ../gone` and `git rm -r .` are refused; `git rm -r --cached .` is allowed. Mutant N4 is killed (10 tests) |

## New findings

### BLOCKING

- **B1-R** `.claude/hooks/bash_guard.py:735-739` (`judge_command` calls `_assign` for the assignments before a
  program word) together with `:1281-1284` (a `SCRATCH` variable is scratch). OWASP: none. This is the
  control-class fail direction misapplied (`main:permission-matrix.md` §11), on the same Catastrophe-class
  rule as B1.
  - **The shell.** In bash and zsh, `NAME=value cmd` sets NAME only in `cmd`'s environment. It does not
    change how `cmd`'s own words expand, nor what NAME holds afterwards. The guard records the value in
    `SCOPE` for both.
  - **Measured.** `main` exits 2 on each of these. `d09a5b4` and `b4dc1f3` both exit 0:
    - `HOME=$(mktemp -d) true && rm -rf "$HOME"` (real: `rm -rf ~`);
    - `TMPDIR=$(mktemp -d) make test; rm -rf "$TMPDIR"` (real: the whole per-user temp directory, with every
      work tree and seat in it);
    - `HOME=$(mktemp -d) rm -rf "$HOME"`;
    - `HOME=/tmp/fake-home true; rm -rf $HOME`;
    - `PWD=/tmp/x rm -rf $PWD` (real: the current tree);
    - `d=/Users/umutcanapaydin/Desktop; d=$(mktemp -d) rm -rf $d`.
  - **Failure scenario.** "Run the tool with a throwaway HOME (or TMPDIR), then clean it up" is an ordinary
    agent idiom for isolating a test. The cleanup deletes the owner's home directory or every live tree under
    temp, and the guard is the only barrier in auto mode.
  - **Remedy (owner patch, `make guard-pin`).** When a program word follows, set every prefix-assigned name to
    `UNKNOWN` instead of calling `_assign`. Keep `_assign` for a command made only of assignments. Add the six
    cases above to `test_rm_rf_of_a_path_that_only_starts_with_a_temp_variable_is_refused`. `env NAME=… cmd`
    is already right: the wrapper loop skips its assignments.

### MINOR

- **R1** `.claude/hooks/bash_guard.py:1169-1172,1250-1251`. This is MAJOR-1's remaining exception.
  - `rm -rf .claude/worktrees/<name>` passes whatever the worktree holds, uncommitted work included. The
    round-1 remedy asked for a clean `git status --porcelain`.
  - `git worktree remove --force <dirty tree>` is allowed by all three guards. That includes the author's live
    tree, and `-f -f` for a locked one. The patch now recommends the command.

  This is not a regression, because `main` allows `git worktree remove` too. But it is the same loss of work
  that `git checkout -- .` is refused for.
  *Remedy:* refuse `git worktree remove` with `-f`/`--force` (and `rm -rf` of a `.claude/worktrees/<name>`)
  unless `git -C <path> status --porcelain` is empty, or file it as an issue.
- **R2** `.claude/hooks/bash_guard.py:1566-1600`, documented at `:116`. This is MAJOR-2's residual.
  - **Measured.** A foreign repository whose brief declares `ls`, with a crafted `release-security.md` and a
    `core.fsmonitor` in its `.git/config`. Through the patched hook, `ls` there ran the fsmonitor script. An
    undeclared command (`echo hi`) did not.
  - **Why MINOR, not MAJOR.** The code comes only from that repository's own `.git/config`, which `git clone`
    never carries. It takes an archive that ships `.git/`, plus a command that the repository's own brief
    declares as a deploy. A `git status` there runs the same code with no guard involved. So the guard adds
    little exposure beyond git's own. **Acceptable as documented**, but cheap to close.
  - *Remedy:* accept a governing tree other than the project root only when its `git rev-parse
    --git-common-dir` resolves to the project's own. That also removes the "an older worktree with current
    verdicts governs" path. Otherwise run its git with `-c core.fsmonitor=false`.
- **R3** `.claude/hooks/bash_guard.py:1242-1243`. The fail-closed branch for a walk that runs out of budget is
  untested. Mutant N8 changes `except _Unwalked: return True` to `return False`, and every test stays green.
  The rule is right today: an unreadable directory is refused, as I measured. But a refactor could turn it
  open silently (`main:docs/security-baseline.md`, negative test per invariant).
  *Remedy:* a unit test that monkeypatches `WALK_S` or `MAX_WALK` to 0, then asserts that `rm -rf` of a
  directory under temp is refused.

### NIT

- **N2** `.claude/hooks/bash_guard.py:1398-1407`. OpenSSH reads options after the destination too, so
  `ssh host -t rm -rf /srv/data` still passes: the remote words start at `-t`. Skip leading options in
  `remote` as well.
- **N3** `.claude/hooks/bash_guard.py:1506-1510`. `git config alias.x reset && git x --hard` passes. The alias
  value alone is harmless, and the danger is in the later call's arguments. Recording this text's aliases
  and expanding `git <alias>` would hold it. `main` allowed it too.
- **N4** `.claude/hooks/bash_guard.py:1234-1243`. Scratch looks for a `.git` entry, so a bare repository and a
  `--separate-git-dir` under temp pass `rm -rf` (measured), and their history goes with them. Rare here. Also,
  every `rm -r` and `mv` of a directory is now walked: `mv /System /tmp/x` is refused as too large, which is
  correct, but it is a cost on big trees.

## Questions asked

1. **B1, MAJOR-1, M1 and N1** are closed for every round-1 call, and #282 is closed. B1's class is not: see
   B1-R. The "too large or unreadable" refusal fails closed: an unreadable directory and `/System` were both
   refused. Its rm-side branch is untested (R3).
2. **The test fix is sound.** It replaces a fixed `../`×8 with one more `..` than `$TMPDIR` has parts, so the
   target always lands at `/Users/x`, outside temp, whatever depth xdist uses. The assertion
   (`"destructive" in why`) is unchanged. The only other removed lines are the `ungoverned` fixture's
   `delenv("CLAUDE_PROJECT_DIR")`. It now points that variable at a directory with no brief, which keeps
   "no deploy gate" true under MAJOR-2's project-root rule. No assertion was weakened.
3. **The pin is right.** The sha256 of `bash_guard.py` is
   `fda573c6cba071c693adae312e9d014b23792ee71d94330fb63bbda16ec623e0`, equal to both PreToolUse pins
   (`settings.json:77,88`), and no old pin is left. Both hooks exit 2 with no python on PATH, with the guard
   missing, and on a payload that is not JSON. All four hooks carry `timeout` and `onFailure: block`.
   `b4dc1f3` carries `GP-Agent:` trailers, and its subject says OWNER APPROVAL. The owner's application of the
   patch is asserted, not something this seat can verify.
4. **No refusal was weakened.** Across the 126 payloads, no command that `main` or `d09a5b4` refused is allowed
   at `b4dc1f3`, except the cases round 1 already ruled by design: true scratch, `.claude/worktrees/<name>` and
   `.env.example`. The B1-R calls were already allowed at `d09a5b4`, so they are not new, only still open.
   Newly refused: `rm -r .`, `rm -r ..`, `mv ../<tree>`, `git rm -r .`, `ssh host '<rm>'`, and the alias forms.

## Mutants (each restored; md5 identical)

| # | Where | Mutation | Killer | Result |
|---|---|---|---|---|
| N1 | export | MAJOR-1: in/at a work tree -> not near | unit (10 failed) | RED |
| N2 | export | B1: the `mktemp` remainder unchecked | unit (2) | RED |
| N3 | export | B1: a loose `mktemp` assignment | unit (1) | RED |
| N4 | export | #282: the holds-owned check off | unit (10) | RED |
| N5 | export | M1: alias judging off | unit (7) | RED |
| N6 | export | M1: ssh remote words off | unit (5) | RED |
| N7 | export | MAJOR-2: run the governing tree's gate | unit (3) | RED |
| N8 | export | a walk out of budget -> not near | unit, `test-bash-guard` | **SURVIVED** (R3) |
| N9 | export | `judge_call`'s TMPDIR trust line -> True | unit, `test-bash-guard` | survived; redundant with `judge_command`'s per-word check (`:727-728`) |
| W3 | worktree | `review_need` sensitive paths off | `test_review_need_sensitive_paths.py` (2) | RED (M4 closed) |
| W4 | worktree | `secrets_scan` copies no file | `test_secrets_scan.py` (2) | RED (M3 closed) |
| W5 | worktree | `secrets_scan` missing gitleaks -> 0 | `test_secrets_scan.py` (1) | RED (M3 closed) |
| W6 | worktree | `secrets_scan` `n == 0` check off | `test_secrets_scan.py` (1) | RED |

## Gates (my worktree at b4dc1f3)
- `make check`: exit 0. The legs:
  - session-check PASS;
  - ruff clean;
  - mypy: 49 files, no issues;
  - pytest: 3123 passed, 27 skipped, coverage 92.19%;
  - coverage-floor PASS;
  - check_records PASS, self-test 0;
  - install-check PASS;
  - shell-dialect PASS;
  - wave-check-all PASS (68);
  - conformance: 26 PASS;
  - swift-test: 637, plus SlowTier 7 of 7;
  - client-decls PASS.
- `make secrets`: exit 0, 1206 tracked files, no leaks. Gitleaks in git mode over `d09a5b4..b4dc1f3` found no
  leaks.
- `make deps`: exit 0, no known vulnerabilities.
- `make slopsquat`: exit 0, 20 declared, 0 suspect. The delta adds no dependency.

## Risks queued
- **R4** #285 (`git config core.hooksPath <dir>`, allowed by all three guards) stays open outside #281. It
  belongs with the next guard patch, together with B1-R.
- **R5** If `$CLAUDE_PROJECT_DIR` is unset, the hook takes the guard from the call's tree (`settings.json:88`,
  the `r=` fallback) and `GUARD_ROOT` follows it. A foreign repository that carries a byte-identical public
  guard would then supply the deploy gate. Claude Code always sets the variable for hooks, so this is not a
  finding.

**Verdict: BLOCKING** -- 1 BLOCKING (B1-R), 0 MAJOR, 3 MINOR (R1, R2, R3), 3 NIT (N2, N3, N4). B1-R needs one
owner patch, and a delta re-review of that patch.

## Dispositions

By the author, after the verdict.

| Finding | Disposition | Where |
|---|---|---|
| B1-R | **Owner's patch**: prefix assignments (`NAME=value cmd`) set nothing for the command's words or for later commands; the name becomes unknown, so a target built from it is not scratch | red `f1e844a`; the owner's second patch re-pins the guard at sha256 `8788704f5cef` |
| R1 | **Filed** #286, `work-issue` | #286 |
| R2 | **Accepted**, as the seat rules: the residual of MAJOR-2 is documented under the guard's "Not held" | -- |
| R3 | **Fixed**: a test refuses `rm -rf` of scratch that is too large to walk, and kills mutant N8 | `f1e844a` |
| NITs | **Accepted** as written | -- |

The two fixture directories the seat left under the temp directory are removed by the owner with the patch, since the guard rightly refuses an agent `rm -rf` of a tree that holds a git repository.
