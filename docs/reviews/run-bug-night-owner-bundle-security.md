---
record_type: review
id: owner-bundle-bug-night-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-18
---
# Security Review — run bug-night owner bundle (guard + workflows)

**Reviewer:** Security-Reviewer subagent, D-209 clause 2 / D-206 clause 9 (a guard change passes a security review before it reaches the owner)
**Independent:** yes. I wrote none of the patch, the agent-half tests, or the issues.
**Date:** 2026-10-18
**Release range:** `f12219c..c6faf1e` (agent half, branch `owner/bug-night-bundle`) + `owner.patch`
**Reviewed head:** c6faf1eee99a1ea957ae584d8d074101b8736709 + owner.patch sha256 9c1f4b45b1157d344947b96b79abb2f7cfeda4fcc16c0fef461bdfe04cc1a5f9
**Risk tier:** HIGH (the Bash guard and the Write/Edit guard, `.claude/settings.json`, `.githooks/`, `.github/workflows/`)

## Verdict
PASS WITH FINDINGS (round 2: B1 and M1-M4 verified fixed; NIT N1, N2; risk R1 stands)

Round 1 was BLOCKING; its text below is kept as found.

The #287 change (`FLOW["scoped"]` in `_assign`) turns a literal assignment into UNKNOWN wherever it sits after a
function definition, inside an `if`/`case` body, or after an `&&` that a later `;` does not wait on. The refusals
that read a name's literal value (owner dirs, `.git/config`, `.env`, `git push main`, `reset --hard`,
`--no-verify`, deploy commands) treat UNKNOWN as "not protected", so the patch LOOSENS them. That fails open in
a safety control, against the paired fail direction.

## Method
- `owner.patch` applies cleanly to `c6faf1e`. `orig/` matches the branch byte for byte, and the old guard's sha is
  the current pin `3aea0170...`.
- Unit corpus (`tests/unit/test_bash_guard_bounds.py`, a scratch copy pointed at each guard): old 133 failed /
  473 passed; new 606 passed. The pin test passes against `tree/claude/settings.json`.
- Conformance corpus (`conformance/test-bash-guard.py`, a scratch copy that runs each guard through the same
  hook shape): the same per-case verdicts on old and new (591 calls; the 53 that fail in both are deploy-gate
  cases my out-of-checkout harness cannot reproduce, identical in both).
- About 200 adversarial probes, each fed as a PreToolUse payload to old and new guard in a scratch repository,
  with `CLAUDE_PROJECT_DIR` set to it. Harness: `scratchpad/harness/probe.py`, inputs `p1..p6.txt`.

## Findings

### BLOCKING
- **B1** `.claude/hooks/bash_guard.py` `_assign` (patched hunk @@ -1101 `if (FLOW["scoped"] or ...)`) and
  `judge_text` (`inside`/`defined`/`unwaited`): the patch loosens existing refusals (fail-open, OWASP A01-class
  broken access control on the agent's own sandbox). Old guard exit 2, new guard exit 0, from the project root:
  - `f() { :; }; d=.claude; echo x > "$d"/settings.json`
  - `true && d=.claude/hooks/bash_guard.py; cp /tmp/x $d`
  - `if :; then d=.claude; fi; cp /tmp/x "$d"/settings.json`
  - `f() { :; }; d=.git; echo x >> "$d"/config`  ·  `f() { :; }; d=~/.gitconfig; echo x >> $d`
  - `f() { :; }; k=core.hooksPath; git config $k /dev/null`  ·  `f() { :; }; o=--no-verify; git commit $o -m x`
  - `f() { :; }; b=main; git push origin $b`  ·  `f() { :; }; o=--hard; git reset $o HEAD~1`  ·  `f() { :; }; o=--force; git push $o origin x`
  - `f() { :; }; p=fly; $p deploy` (deploy refusal, D-185)  ·  `f() { :; }; d=.env; echo x > $d`
  In bash, every one of these runs with the literal value: a function definition does not scope later top-level
  assignments, an `if :` body runs, and `true &&` assigns.
  Remedy: when an assignment is scoped, keep both candidates (the prior value or unset, and the new literal)
  and judge every candidate, as `_project_tree`/CANDIDATES already do for places. Or apply `scoped` only to the
  scratch (`mktemp`) question #287 is about. Add the commands above as must-block cases to
  `test_bash_guard_bounds.py`. Re-verify by me.

### MINOR
- **M1** #318 is incomplete. Each of these moves `main` and passes the new guard (verified with git 2.50 in a
  scratch repo): `git checkout -Bmain feat` · `git switch -Cmain feat` · `git switch --force-cr main feat` ·
  `git switch --cr main`. `_moves_default` matches only exact `-B`/`-C`/`--force-create` words: no attached
  short value, no long-option prefix (`given()` is not used there). Also `git config url./tmp/evil.insteadOf
  <origin-url>` (and `-c`/`GIT_CONFIG_*`) redirects origin with `remote.origin.url` untouched, so the next
  `git fetch origin` rewrites `origin/main`. Fix before #318 is closed, or file the gaps.
- **M2** #256 defence in depth: `GIT_DIR=.claude/.git git init` and `git --git-dir=.claude/.git init` still
  plant a `.git` in `.claude/`. The new every-work-tree walk in `_owned` keeps the owner's files refused after
  such a plant (unit cases pass), so this is not exploitable today. File it or refuse it in `_git_made`.
- **M3** #317: `sed -i '' d <dirty-wt>/.git` (and by the same path `perl -i`) passes. `rm`, `mv`, `cp`,
  `truncate`, `chmod`, `unlink` and `>` are refused. The docstring says the programs of the owner's-directory
  rule are covered, and `sed -i` is one of them.
- **M4** `governance-contract.yml` is deleted, but the patched `docs/branch-protection.md:50,59-60` still lists
  `governance-contract (aggregate, unconditional)` as required and cites the deleted file. `docs/owner-actions.md`
  has no row for dropping it from branch protection (D-161 clause 4 and UPGRADING.md:552 name the step). Until
  the owner does it, every PR waits on a check that never reports (fails closed: availability, not security).
  Its fake-pin grep leg is not carried into `ci.yml` (`check_records` and `--self-test` are, in
  `install-and-governance`).

### PASS
- Pin: both PreToolUse guard entries in `tree/claude/settings.json` carry `ca2259ff...6fffd`, equal to
  `shasum -a 256 tree/claude/hooks/bash_guard.py`. No old pin remains, and the JSON is valid.
- Parse errors still fail closed (`rm -rf $(`, an unclosed quote). The new code paths do not crash on
  degenerate input (`git worktree move`, `git checkout -B`, `git update-ref`, `git fetch . :` with no operands).
- #320 holds against every variant I tried: `--tem`, `--templ=`, `-c Init.TemplateDir`, `GIT_CONFIG_*`,
  `--config-env`, `export`, `env`, `declare -x`, `printf -v`, `read`, `${:=}`, `for`, `eval`, `declare -n`.
- #305 holds: `' !rm -rf ~'`, `-c`, `--add`, `config set`, `credential.<url>.helper`, `core.sshCommand`. Allowed
  as it should be: osxkeychain, `!gh auth git-credential`, `less -R`.
- #256 `git init/clone/worktree add/submodule add` into `.claude`/`.githooks` (quoting, `$PWD`, case, `cd`,
  `-C`, `--separate-git-dir`, `.claude/worktrees/../x`) is refused; `git worktree add .claude/worktrees/x` is allowed.
- #287 holds for its own target (`mktemp` scratch): subshell, pipe, `||`, `&`, loop, `if`, `case`, function,
  `bash -c`, `eval` after `&&`. The legitimate forms stay allowed.
- #317: `rm`/`mv`/`truncate`/`chmod`/`unlink` of a dirty worktree's `.git`, and `git worktree move` (with `-f`,
  `-C <wt> .`, or by name), are refused.
- Workflows: no `uses:` added or changed, `permissions:` unchanged, no new `secrets.*`, and `issue-agent.yml`
  changes only a comment. Installs are hash-checked locks (`--require-hashes`). `pip-audit --strict
  --disable-pip` over every `requirements/*.lock` fails closed when there is no lock, and matches `make deps`.

## Gates passed
- [x] Secret scan: no credential-shaped text in the patch (reviewed by hand; gitleaks not re-run on a patch file)
- [x] `make deps`: not re-run. No dependency added; the CI audit now matches `make deps`
- [x] `make slopsquat`: no new import
- [ ] Default-deny preserved: NO (B1)
- [ ] Permission-matrix not violated: B1 reopens permission-matrix S5/S6 refusals
- [x] Prompt-injection hygiene: n/a (no untrusted-content consumer changed)
- [x] Auth/PII: n/a. The guard is the agent's control surface; the owner applies it (D-209 clause 2)
- [x] SAST: n/a for a patch file; the guard ran over about 200 hostile inputs without a crash

## Acceptance criteria evidence
- #256/#287/#305/#317/#318/#320: `tests/unit/test_bash_guard_bounds.py` at c6faf1e (133 red on the pinned
  guard, green on `tree/`). B1 and M1-M3 have no citing must-block case.
- #81: `tree/github/workflows/ci.yml:47-51,112-116`, `contract-tests.yml:84-89,106-111`

## Risks queued
- **R1** The guard treats a path with an UNKNOWN expansion as unprotected for writes, so any future widening of
  UNKNOWN reopens B1's class. Make the write-target checks refuse an unreadable owner-directory candidate (the
  way the `rm -rf` scratch rule already does), so a fail-open regression cannot come back through scoping.

## Round 2

**Date:** 2026-10-18
**Reviewed head:** e4f01c4 (agent half, `owner/bug-night-bundle`) + owner.patch sha256 b3cfcabd0a15e330e9947f8ae27627ab43cbdcaacf7d90811c0fbdcd861e37ad
**Guard:** `tree/claude/hooks/bash_guard.py` sha256 0e267250ff1a7a5fc4cc8288539fe1f729d97eecd923facd87276df3544f0278. Both hook entries in
`tree/claude/settings.json` pin it, and no other pin remains. `orig/` still matches the branch, and the patch applies to e4f01c4.

### Verdict
PASS WITH FINDINGS. BLOCKING 0 · MINOR 0 · NIT 2.

### Re-verification (old guard vs new guard, same harness as round 1)
- Unit corpus at e4f01c4: the pinned guard fails 156 and passes 501; the new guard passes all 657.
- Conformance corpus: the same per-case verdicts on old and new (591 calls).
- All round-1 probes (p1-p6) plus new ones (p7: B1 variants; p8: 32 everyday commands; p9: M1-M3 variants):
  **no command the old guard refuses passes the new one.**
- **B1 fixed.** Every round-1 B1 command is refused again. The new variants are refused too: nested functions,
  `case`, `while true ... break`, `||`, `export`, `local` inside a function, `declare`, `readonly`, `typeset`,
  values split over two doubtful assignments (`if :; then d=.cl; fi; e=aude; ... "$d$e"`), and two `&&`
  assignments joined in one path. A `$( )` assignment and an array element pass both guards alike (pre-existing, R1).
- **M1 fixed:** `-Bmain`, `-bmain`, `-Cmain`, `-fBmain`, `--force-cr`, `--force-c=main`, `--cr`, and
  `url.<x>.insteadOf` through `git config`, `-c` and `GIT_CONFIG_*` (any case).
- **M2 fixed:** `GIT_DIR=`, `export GIT_DIR=...;`, `GIT_WORK_TREE=`, `--git-dir=` and `--work-tree=` into `.claude`/`.githooks`.
- **M3 fixed:** `sed -i ''`, `sed -i.bak`, `sed --in-place`, `perl -i` on a dirty worktree's `.git`. `sed -i` on an ordinary file stays allowed.
- **M4 fixed** in the patch: `docs/branch-protection.md:50` no longer lists `governance-contract` as required and points to
  the owner-actions row. That row is uncommitted in the worktree (`M docs/owner-actions.md`); the coordinator commits it.
- Double-judging: 30 of 32 everyday commands give the same verdict as before (status, diff, add, commit, push of
  a branch, make, pytest, gh, a function then a call, loops, `case`, `mktemp` + trap cleanup). The "none made"
  pass does not block them en masse.

### NIT
- **N1** `f() { :; }; X=$(mktemp -d); rm -rf "$X"` is now refused (old: allowed): an assignment after any function
  definition is doubtful. It errs closed, as #287's text says; the plain form without a function still passes.
- **N2** `git -c url.https://github.com/.insteadOf=git@github.com: fetch` (an ordinary SSH-to-HTTPS rewrite) is now
  refused. This also errs closed. The owner may want to allow an `insteadOf` whose base is a well-known host.
