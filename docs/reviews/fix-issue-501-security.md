---
record_type: review
id: fix-issue-501-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-30
---
# Security Review — fix-issue-501

**Reviewer:** Security-Reviewer subagent (light mode, run 1030; a deploy-gate control change that D-231 clause 1 pre-approves as tightening only)
**Independent:** yes. I wrote neither the red test nor the fix, and I have not reviewed this code before.
**Date:** 2026-10-30
**Release range:** d7780fc..0bc39ca (`bde8f45` red test, `0bc39ca` fix)
**Reviewed head:** 0bc39caeeb29d6761c55f5fdefb2c0eec76c2c12
**Risk tier:** HIGH (a deploy-gate policy change; a control change that must only tighten)

## Verdict
MINOR

The branch only tightens. Every spelling in the issue body is now refused when it is the declared command, the
`make`/`just` reading of a dispatched workflow is new, and none of my probes passes at 0bc39ca where it was refused at
the base `d7780fc`. The three fixture changes weaken no test (see PASS). The allowlist still has gaps. It reads only the
first simple command of a declared command (M1). It reads a dispatched workflow's run lines only for a bare recipe
runner (M2). And it lets a `gh` dispatch by id through (M3). Each of these behaves the same at the base and none is
reachable from the repository's four declared commands, so none is BLOCKING.

I worked in my own worktree `scratchpad/sec-501` at `0bc39ca` (detached), with its own venv (`make install`) and a copy
of `advisor.db` (D-174). For base comparisons I swapped in `d7780fc`'s `scripts/deploy_gate.py` by copy and restored
it by copy (`cmp` clean). The probes were throwaway pytest files that used the suite's own fixtures (`_installed`,
`_upgrade_shipping`, `_brief`), and I deleted them afterwards. The policy (this profile, D-231) is the same at `main`
and at the head.

## Findings

### BLOCKING
- none

### MINOR
- **M1** scripts/deploy_gate.py:398 with :555 — `_command_surface` reads only the first simple command of each
  declared command. `declared()` splits with `shlex.split`, so `&&`, `;` and `|` stay words (`deploy;` is one word),
  and every word after the first program is read only as a possible path. With `scripts/ship_it.sh` shipped
  byte-identical by an upgrade, each of these exits 0 at 0bc39ca, and at d7780fc too:
  `fly deploy && make ship`, `fly deploy; make ship`, `fly deploy && just ship`,
  `fly deploy | python -m scripts.ship_it`, `fly deploy && bash -c 'make ship'`. These are the issue's own spellings
  (`just`, `python -m`, `bash -c`) placed after a known first program, so D-231 clause 1 ("any other program ...
  exempts nothing") does not hold for the second command. This is not reachable today, because all four declared
  commands in `docs/project-brief.md:107` are simple. Remedy: in `deploy_surface`, read each declared text with
  `split_line` (as the guard does) and require `_command_surface` to be non-None for every simple command, or return
  None when a declared word is a control operator or ends in one. Add one test per operator.
- **M2** scripts/deploy_gate.py:418-421, :450 — a dispatched deploy workflow's run lines are read only for a recipe
  runner standing as the first word. With the workflow committed at the reviewed head and `gh workflow run release`
  declared, each of these exits 0 at 0bc39ca, with the surface being only the workflow files:
  - a YAML-quoted value, `run: "make ship"` or `run: 'make ship'`. `split_line` turns it into the single word
    `make ship`, which is not `make`.
  - `run: bash -c 'make ship'`, `run: echo ship | xargs make` and `run: ${MAKE:-make} ship`.
  - a run line that starts a script some other way: `run: scripts/ship_it.sh`, `run: python scripts/ship_it.py`,
    `run: cd scripts && ./ship_it.sh`, and `uses: ./.github/workflows/inner.yml` calling a workflow that runs `make`.
    What these start is never added to the surface.

  All of these exit 0 at d7780fc as well. The block (`run: |`) and folded (`run: >-`) forms of `make` are newly refused
  (a tightening). This is not reachable today: `.github/workflows/nightly-hosted.yml` runs only `pip`, `gh api` and
  `scripts/nightly_hosted.sh`, which is safety surface. Remedy: read each dispatched workflow's run lines through
  `_command_surface` (None for an unknown program), unquote a YAML scalar before splitting it, and treat a local
  `uses:` as None (or recurse into it).
- **M3** scripts/deploy_gate.py:410-412 with :806 — `gh workflow run 12345` (a numeric id) passes `_command_surface`,
  because `gh_dispatch` returns `{UNKNOWN}`, not None. `deploy_workflows` then drops UNKNOWN, so the workflow it
  dispatches is not on the surface. An upgrade that ships `.github/workflows/release.yml` byte-identical stays
  exempt (probe exit 0, the same at d7780fc). What this command starts cannot be derived, and that is exactly the
  issue's "None for any other program" case. Remedy: return None when the dispatch set contains UNKNOWN.

### PASS
- **The fixture changes weaken no test.** This is the B1 question from #494's review: does a fixture's declared
  command name something a test proves is code for another reason?
  1. `_installed` (tests/unit/test_deploy_gate_pin.py:62-64) adds `scripts/ship_it.sh` ("echo installed") before
     the reviewed head. It is not declared (the fixture still declares `fly deploy`, :59) and it is not on
     `SAFETY_SURFACE`. So a test that ships it is refused only because a declaration that names it puts it on the
     derived surface. Mutant A (`_command_surface` never returns None) fails 4 cases. The B1 invariant still holds:
     dropping `scripts/deploy_hosted_engine.sh` from `SAFETY_SURFACE` fails 2 pin tests.
  2. conformance/test-deploy-shipped.py:58-60 now declares `fly deploy` instead of `scripts/deploy.sh`, a file that
     was never in its tree. Both name no file, and the surface is `{}` either way. The PASS cases still pass, which
     means the surface is not None. The refusal cases still refuse for the reason each one names. Dropping
     `.claude/settings.json` from `SAFETY_SURFACE` still fails the conformance run (probe). `test-deploy-shipped
     PASS: 7 cases` at 0bc39ca.
  3. tests/unit/test_deploy_gate_494.py:32 renames `Ship_It.sh` to `Ship_Now.sh`. The case is still a mixed-case
     declared path, and the rename avoids a collision with the fixture's `ship_it.sh` on a case-blind disk. One
     side effect of #501 is worth recording: when the lookup finds nothing, the surface is now None, which also
     refuses. So #494's spelling cases now prove refusal rather than derivation. A lookup that returns the wrong
     file is still caught (mutant S3: 4 failed), and dropping the case-folding is still caught (mutant S2: 1
     failed). Nothing about security is lost.
- Mutants killed: A (no None), B (recipe check removed), C (`python` added to KNOWN_PROGRAMS), D (`_path_like`
  always False), I (an unknown program accepted). G (`bash -x` allowed) is equivalent, because the option names no
  listed file.
- On the real tree the surface at 0bc39ca and at 39f0829 is the same four paths: `.github/workflows/nightly-hosted.yml`,
  `scripts/ci/nightly-hosted.yml`, `scripts/deploy_hosted_engine.sh` and `scripts/nightly_hosted.sh`. `fly deploy` ships
  only `Dockerfile`, `pyproject.toml`, the two locks and `src/` (`.dockerignore`), and none of those is DevFlow
  tooling. That bears out the KNOWN_PROGRAMS comment (scripts/deploy_gate.py:351-355) for this repository.
- These spellings are refused, which is correct: `exec`, `nohup`, `timeout 5`, `sudo -u x` and `command bash` in
  front of a script; `sh -e script`; `./fly deploy` with no such file; `env -S 'bash -c make' x`; `xargs script`;
  `gh workflow run $WF`; `fly deploy -c ./fly.toml` with no such file; and `SCRIPTS/SHIP_IT.SH`.
  `env fly deploy` and `FOO=1 fly deploy` still derive.
- No new import, no secret, no destructive operation, and no edit under `.github/workflows/**`, `.claude/`,
  `.githooks/`, `pyproject.toml` or a lock. The red test (`bde8f45`) was committed alone first. Both commits carry
  `GP-Agent: claude-code` / `GP-Task: issue-501` and no AI attribution.

## Gates passed
- [x] Secret scan green (`make secrets`, run by me at 39f0829, which contains this head: "no leaks found")
- [x] `make deps` (pip-audit) green ("No known vulnerabilities found", at 39f0829)
- [x] `make slopsquat` green ("slopsquat PASS: 20 declared dependency(ies), 0 suspect", at 39f0829; no dependency
  file in the range)
- [x] Default-deny preserved for new external surfaces (no new surface; the change only narrows an exemption)
- [x] Permission-matrix not violated (no protected-path edit)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path; the brief declares
  no HIGH paths)
- [x] SAST (`ruff check --select S` on scripts/deploy_gate.py: clean in the range. `conformance`, run by me at 39f0829:
  "conformance PASS: 33 test(s) derived from conformance/, 0 failing". Tests at 0bc39ca: `-k deploy` 360 passed)

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #501, each spelling in the body refuses an upgrade-shipped file it starts → scripts/deploy_gate.py:393-415,
  :418-421, :448-451; tests/unit/test_deploy_gate_501.py:23-37 (cd then relative, `$PWD`, `python -m`, a directory,
  `just`, `bash -c`, a known program given an expansion) and :40-48 (a dispatched workflow that runs `make`). Met
  for these spellings as written; their compound and quoted forms are M1 and M2.
- #501, a control still exempts a plain tooling file → tests/unit/test_deploy_gate_501.py:51-59 (`fly deploy`, a
  script, `bash` with a script, `gh workflow run`)
- #501, the four declared commands derive the same surface → probe on the real tree (above); no citing test, since
  the brief is the input
- D-231 clause 1, tightening only → no probe refused at d7780fc passes at 0bc39ca (the M1 to M3 probes exit 0 at both)

## Risks queued
- **R1** tests/unit/test_deploy_gate_501.py — three loosening mutants survive all 47 tests in the 501, 494, 444
  and pin files. E: `just` removed from UNREAD_RECIPES (no workflow-runs-`just` case). F: a shell given a bare word
  that names no listed file is accepted (`bash ship_it.sh` with no such file). H: `gh` accepted whatever it
  dispatches (`gh release create`). Remedy: one parametrized case each.
- **R2** scripts/deploy_gate.py:398 (`_program_position`) — assignments and wrapper options before the program are
  skipped and never read. `BASH_ENV=scripts/ship_it.sh bash scripts/deploy_hosted_engine.sh` makes bash source
  `ship_it.sh`, yet the gate exempts it (probe exit 0). It is the same at the base and is not reachable from the
  brief. Remedy: None for an assignment to a variable the started program reads as code (`BASH_ENV`, `ENV`,
  `PYTHONSTARTUP`, `PYTHONPATH`, `LD_PRELOAD`, `DYLD_*`), or for any assignment that is path-like.
- **R3** (D-231 "Revisit when") — M1 and M2 are what the next allowlist change has to cover. Each is a gate bypass
  that stays green with no test, though none is reachable from today's declarations. File them as one issue with
  the probe spellings above.
