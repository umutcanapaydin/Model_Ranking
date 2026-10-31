---
record_type: review
id: fix-issue-522-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-31
---
# Security Review — fix-issue-522

**Reviewer:** Security-Reviewer subagent (light mode; a deploy-gate control change under D-232 clause 2, the owner's ruling of 2026-10-31: tightening only)
**Independent:** yes. I wrote neither the red test nor the fix, and I have not reviewed this code before.
**Date:** 2026-10-31
**Release range:** bf3f0af..d29e91d (`ee14e1d` red test alone, `d29e91d` fix), stacked on #517's head
**Reviewed head:** 6d2e10de6cafc6e52c0e29930a8985e1d48d45a5
**Risk tier:** HIGH (what the deploy gate exempts; the brief's `Paths that make a change HIGH:` is `none`, and the tier
comes from the control class)

## Verdict
PASS

Round 2 (6d2e10d): PASS. B1 is fixed and held, with no loosening against bf3f0af. M1 is fixed, apart from two `env -C` cluster
spellings (R4), and one fail-closed false refusal is queued (R5). Round 1's text follows unchanged; round 2 is at the end.

Round 1 (d29e91d): BLOCKING. The change closes every spelling in #522's body. On the real nightly workflow the surface stays readable. But
replacing `_runs_unread`'s program-position test with `_UNREAD_IN_WORKFLOW` LOOSENS the gate for a recipe runner named
by a path or in another case (B1). A dispatched deploy workflow with `run: /usr/bin/make ship` exempted nothing at
bf3f0af, and at d29e91d it exempts again. D-232 allows tightening only, and its own mitigation line says a change that
loosens the gate "is refused at review". The fix for B1 is small, and I tried it on a copy (below).

Worked in `/private/tmp/claude-501/-Users-umutcanapaydin-Desktop-ILGAR-model-ranking/cbf5c80e-9000-4990-acff-ddcfbf8972cf/scratchpad/sec-522`
at `d29e91d` and `.../scratchpad/sec-517` at `bf3f0af` (detached). Each has its own venv from `make install` and its
own copy of `advisor.db` (D-174). The probes are pytest files in `scratchpad/sec522probe/`. I copied each into the
tree only for its run, then removed it. The candidate remedy was restored from a byte copy, and both trees were left
clean.

## Findings

### BLOCKING
- **B1** scripts/deploy_gate.py:518-520 (`_UNREAD_IN_WORKFLOW`), :525-528 (`_runs_unread`). The lookbehind
  `(?<![\w/.])` refuses a recipe runner preceded by `/` or `.`, and the pattern has no `re.IGNORECASE`. The old test
  read the program's `basename(...).lower()`, so `/usr/bin/make`, `./make`, `Make`, `~/.cargo/bin/just` and
  `/usr/local/bin/gmake` were all refused. Now none of them is. A Makefile recipe the workflow runs, and every tooling
  file the recipe starts, becomes exemptible after an upgrade again: the safety class fails OPEN (AGENTS.md section 5;
  OWASP A08). It is BLOCKING because it loosens a control that D-232 permits only to tighten, it is exploitable with
  one ordinary spelling in a reviewed workflow, and no test holds it.
  Evidence (the #522 fixture: a dispatched `release.yml` in the reviewed head, then an upgrade ships `scripts/tool.py`;
  `--check` exit 1 = refused, 0 = exempt):
  ```
  == bf3f0af (before #522)          == d29e91d
  plain-make  1 refused             plain-make  1 refused
  abs-make    1 refused             abs-make    0 EXEMPT
  dot-make    1 refused             dot-make    0 EXEMPT
  upper-Make  1 refused             upper-Make  0 EXEMPT
  abs-just    1 refused             abs-just    0 EXEMPT
  abs-gmake   1 refused             abs-gmake   0 EXEMPT
  ```
  **Remedy (tried on a copy, then restored):** use `(?<![\w.-])` as the lookbehind (a `/` before the name is a path to
  the runner), compile with `re.IGNORECASE` (which also catches `USES: ./`), allow `uses\s*:`, and keep the old program-position
  test OR'ed in, so the new reading can only add refusals:
  ```python
  return _UNREAD_IN_WORKFLOW.search(text) is not None or any(
      (run := _program_position(words)) and os.path.basename(run[0]).lower() in UNREAD_RECIPES
      for words in _line_commands(text))
  ```
  With it, all six probes are refused. All 212 tests in `tests/unit/test_deploy_gate*.py` pass. The real nightly
  workflow's surface does not change (printed below), and neither nightly copy matches. Add the six spellings to
  `tests/unit/test_deploy_gate_522.py`'s parametrisation.

### MINOR
- **M1** scripts/deploy_gate.py:518-533: two common, innocent ways of starting a script still leave it exemptible.
  First, a changed directory that is not `cd`/`pushd`: `working-directory: scripts` (on the step, or under
  `defaults: run:`) with `run: ./ship_it.sh`, and `env -C scripts ./ship_it.sh`. D-232 clause 2 refuses `cd` for
  exactly this reason ("what a relative path after it names cannot be read"). Second, a path anchored at the checkout:
  `$GITHUB_WORKSPACE/scripts/ship_it.sh`, `${{ github.workspace }}/scripts/ship_it.sh` and `"$PWD/scripts/ship_it.sh"`.
  `_PATH_WORD` yields `/scripts/ship_it.sh`, which `_named_files` reads as an absolute path outside the root. Each one
  probes exit 0 (exempt). None of these is a regression (at bf3f0af nothing a workflow started was on the surface), and
  a reviewer would read each spelling as harmless. **Remedy:** add `working-directory` and `chdir`/`-C`/`--chdir` to the
  unread set, and also look up each `_PATH_WORD` with its leading `/` stripped (a name relative to the checkout). The
  nightly workflow has none of these, so its surface stays readable.

### PASS
- Every spelling in #522's body is closed and held (`tests/unit/test_deploy_gate_522.py:34-51`): YAML-quoted, `bash -c`,
  `xargs make`, `${MAKE:-make}`, a script, an interpreter, `cd` then a relative path, and `uses: ./`. My extra probes
  were refused too: `source scripts/x.sh`, `. scripts/x.sh`, `env -S 'scripts/x.sh'`, and a heredoc that names the
  script. The `-c` and heredoc bodies count because the whole text is read.
- The real surface stays readable at d29e91d: `nightly-hosted.yml` is the one dispatched workflow, `_UNREAD_IN_WORKFLOW`
  matches neither copy, and the surface is `.github/workflows/nightly-hosted.yml, AGENTS.md, requirements/build.lock,
  requirements/ingest.lock, runner, scripts/ci/nightly-hosted.yml, scripts/deploy_hosted_engine.sh,
  scripts/nightly_hosted.sh, tests/unit/test_nightly_hosted.py`. `AGENTS.md`, `runner` and the test come from its
  comments, which only tightens. The control test (`:54-60`) holds that setup steps leave a plain tooling file exempt.
- Reading comments is not a security problem. A word in a comment can only add a file to the surface or empty it to
  None, and both refuse more. The cost is usability: `contract-tests.yml` ("just ran") and `ci.yml`/`issue-agent.yml`
  (`make ...`) would exempt nothing if they were ever dispatched. That is fail closed, and none of them is dispatched
  today.
- `_workflow_names` (:531-533) only adds names, and only for files git lists, and `deploy_surface` (:567) adds them
  only on the non-None path. No path that was None at bf3f0af becomes a set, apart from B1's.
- Red test `ee14e1d` is alone (one file). The fix follows it, and all 212 deploy-gate tests pass at d29e91d.

## Gates passed
- [x] Secret scan green (`make secrets` at d29e91d, run by me: "no leaks found")
- [x] `make deps` (pip-audit) green ("No known vulnerabilities found")
- [x] `make slopsquat` green ("slopsquat PASS: 20 declared dependency(ies), 0 suspect"; no new import)
- [ ] Default-deny preserved for new external surfaces: no new surface, but the exemption's fail-closed reading is
  loosened for a path-spelled runner (B1)
- [x] Permission-matrix not violated (no protected-path edit; no workflow file touched)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model; the workflow text is read as data, by regex)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path)
- [x] SAST (bandit is not in the lock; I read the diff by hand: two regexes and set comprehensions, no subprocess or
  eval. `_UNREAD_IN_WORKFLOW` and `_PATH_WORD` have no nested quantifier, so they are linear). Conformance at
  d29e91d, run by me: "conformance PASS: 33 test(s) derived from conformance/, 0 failing, 0 caller-liveness
  finding(s)"

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #522: each spelling in the issue's body leaves nothing exemptible → scripts/deploy_gate.py:518-533, :562, :567;
  tests/unit/test_deploy_gate_522.py:34-51
- D-232 clause 2 control: setup steps still exempt a plain tooling file → tests/unit/test_deploy_gate_522.py:54-60
- D-232: tightening only → NOT MET: B1 (a runner spelled by path or case, refused at bf3f0af, exempt at d29e91d)

## Risks queued
- **R1** scripts/deploy_gate.py:522 (`_PATH_WORD`): a script whose path the workflow builds or splits stays exemptible.
  Probed exit 0: `scripts/${NAME}.sh`, a glob `scripts/ship_*.sh`, a quote split `ship"_"it.sh`, a YAML escape
  `"ship\x5fit.sh"`, a backslash-newline inside the word, `find scripts -name 'ship*' -exec bash {} \;`, and Python
  that joins the path at run time. D-232's "Revisit when" names this class. Each one needs an odd spelling inside a
  workflow file that is itself never exempt, so a reviewer of that file sees it. Queue it. Do not fix it by
  enumeration.
- **R2** scripts/deploy_gate.py:518-520: code from outside the tree runs unread. A composite action or reusable workflow
  from another repository, pinned by sha (`uses: someone/actions/ship@<sha>`), can start a local script by a
  convention its text never names, and `uses: <this owner>/<this repo>/.github/workflows/x.yml@main` is a local
  workflow spelled remotely. The first one probes exempt, and the second one does so on reading. The second is the `uses: ./` case by another name, and it could join
  the unread set by matching this repository's own slug.
- **R3** what a script on the surface starts in turn (for example `scripts/nightly_hosted.sh` running other files) is
  not derived. This is pre-existing (#444/#501's design for declared commands), and not this change.

## Round 2 — re-verification at 6d2e10d (fix diff d29e91d..6d2e10d)

**Reviewed head:** 6d2e10de6cafc6e52c0e29930a8985e1d48d45a5

Round-2 verdict: PASS. B1 is fixed and held. M1 is fixed for every spelling I reported, and two cluster spellings
of `env -C` remain as R4. Nothing loosens against bf3f0af: the old first-word check is OR'ed back in, so every
workflow bf3f0af refused is still refused, and the new reading only adds refusals and surface names.

- **B1 — fixed.** scripts/deploy_gate.py:523-526 (lookbehind `(?<![\w.-])`, `re.IGNORECASE`, `uses\s*:`) and :533-538
  (`_runs_unread` ORs the `_program_position` basename check). My round-1 regression probe is now refused in all six
  cases (`/usr/bin/make`, `./make`, `Make`, `~/.cargo/bin/just`, `/usr/local/bin/gmake`, plain `make`; exit 1 each).
  So are these extras: `MAKE`, `/usr/bin/Make`, `\make`, `m''ake` (caught by the restored first-word check),
  `uses : ./`, `USES: ./`. Held by `tests/unit/test_deploy_gate_522.py:43-47` (the five B1 spellings).
- **M1 — fixed.** `working-directory:` on the step and under `defaults: run:`, `env -C scripts`, `env --chdir=scripts`,
  `env --chdir scripts`, `$GITHUB_WORKSPACE/…`, `${GITHUB_WORKSPACE}/…`, `${{ github.workspace }}/…`, `"$PWD/…"`,
  `"$(pwd)/…"`, `"$(git rev-parse --show-toplevel)/…"` and `"$(dirname "$0")/…"` each probe exit 1 (refused).
  :528-530 (`_EXPANSION`) and :541-547 (`_workflow_names`, each word looked up with and without its leading `/`) only
  add names to the surface. Held by `tests/unit/test_deploy_gate_522.py:48-51` (the four M1 spellings).
- The real surface is unchanged and readable at 6d2e10d. `nightly-hosted.yml` is the one dispatched workflow, and
  `_UNREAD_IN_WORKFLOW` matches neither copy. The surface is `.github/workflows/nightly-hosted.yml, AGENTS.md,
  requirements/build.lock, requirements/ingest.lock, runner, scripts/ci/nightly-hosted.yml,
  scripts/deploy_hosted_engine.sh, scripts/nightly_hosted.sh, tests/unit/test_nightly_hosted.py`, the same as round 1.
- Tests: all 223 tests in `tests/unit/test_deploy_gate*.py` pass at 6d2e10d. Gates at 6d2e10d, run by me: `make secrets` "no leaks found"; `make deps` "No known vulnerabilities found"; `make slopsquat` "slopsquat PASS: 20 declared dependency(ies), 0 suspect"; conformance "conformance PASS: 33 test(s) derived from conformance/, 0 failing, 0 caller-liveness finding(s)".

- Gates passed, round 2: every line of round 1's list now holds, including "Default-deny preserved" (B1 is fixed).

Round-2 risks queued (in addition to round 1's R1-R3, which stand):
- **R4** scripts/deploy_gate.py:525 (`\benv\b[^\n]*\s(?:-C|--chdir)\b`): two cluster spellings still change directory
  unread. `env -Cscripts ./ship_it.sh` (the value attached) and `env -iC scripts ./ship_it.sh` (a cluster) both probe
  exit 0. Both are rare, deliberate spellings inside a workflow file that is itself never exempt. Remedy, if it is
  wanted: `\s-[A-Za-z]*C` for the short form.
- **R5** the same alternative under `re.IGNORECASE` also matches a lower-case `-c`, so `run: env FOO=1 bash -c 'echo hi'`
  makes the surface None (probe: a plain tooling file is refused, exit 1). This is a false refusal that fails closed,
  and nothing on the nightly workflow triggers it. It is usability, not security. Remedy: match `-C` case-sensitively
  (an inline `(?-i:-C)`).

Round-2 acceptance criteria evidence:
- #522 B1: a runner spelled by path or case exempts nothing (no loosening against bf3f0af) → scripts/deploy_gate.py:523-538;
  tests/unit/test_deploy_gate_522.py:43-47
- #522 M1: a directory change and a checkout-anchored path → scripts/deploy_gate.py:525, :528-530, :541-547;
  tests/unit/test_deploy_gate_522.py:48-51
- #522 (round 1, unchanged): every spelling in the issue's body → tests/unit/test_deploy_gate_522.py:34-41
