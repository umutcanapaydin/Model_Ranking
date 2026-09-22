---
record_type: field-findings
id: devflow-v6-field-findings-2026-09-23
status: draft
process_version: v6.0
date: 2026-09-23
---
# DevFlow v6.0 — field findings from its first installation (model_ranking)

**For the DevFlow developer agent.** Defects in DevFlow's own machinery, found while installing v6.0
into a 16-milestone project (General Pipeline v5.0 before, three-way merged, D-155 in that
project's `docs/decisions.md`). The owner asked for the ones that matter to a FRESH project, not to
a version jump, so the list is ordered that way:

- **A. Reproduced on a clean clone of DevFlow v6.0** (tag `v6.0`, commit `6f4cf25`), with the
  project name filled in and nothing else changed. Every one of these hits a brand-new project.
- **B. Hits any project as it grows**, fresh or not; found here because this project is old.
- **C. Version-jump only.** Short, lower priority.

Each item: what happens, how to reproduce it, and a suggested fix. Nothing here was patched in
DevFlow; the project-side workaround is named so a fix can be checked against it.

---

## A. A fresh project hits these

### A1. `src/__init__.py` breaks `make typecheck` on the first cross-module import — HIGH

**What.** The package ships `src/__init__.py`. In a src-layout project that makes `src` itself a
package, and mypy then resolves `from app.x import y` as an installed module without `py.typed`:
`import-untyped`, and every value from it becomes `Any` (`no-any-return` follows).

**Repro (clean clone).** Fill `name`/`description` in `pyproject.toml`, `make install`, then:

```
printf 'def ranked() -> list[int]:\n    return [1]\n' > src/app/workflows/rank.py
printf 'from app.workflows.rank import ranked\n\n\ndef top() -> int:\n    return ranked()[0]\n' > src/app/workflows/pick.py
make typecheck        # -> 2 errors: import-untyped, no-any-return
rm src/__init__.py
make typecheck        # -> Success: no issues found
```

In this project: 113 errors across 23 files the moment the file landed.

**Fix.** Do not ship `src/__init__.py` (the layout is `src/app/`; `app` is the package). If it is
needed for something, set `mypy_path = "src"` with `explicit_package_bases = true` instead.
**Workaround here:** not installed; recorded in D-155 clause 4.

### A2. Every `make` target rebuilds the venv, upgrades pip and reinstalls the project — MEDIUM

**What.** `$(VENV)/bin/python: _check_python` — `_check_python` is PHONY, so the file target is
always out of date. `make lint`, `make test`, `make check` and `make gate` each run
`python3 -m venv .venv`, `pip install --upgrade pip` and `pip install -e ".[dev]"` first.

**Repro.** `make -n lint` on a clean, installed clone prints all three before `ruff`.

**Cost.** Seconds per target locally; a network round-trip per target, so an offline `make check`
fails on pip rather than on anything it checks; and `make gate` runs it several times.

**Fix.** Make it an order-only prerequisite (`$(VENV)/bin/python: | _check_python`), or move the
Python check into the recipe. The venv target must only run when `.venv/bin/python` is missing.

### A3. `issue-agent.yml` calls two skills v6.0 removed — MEDIUM

**What.** `.github/workflows/issue-agent.yml:62-63` tells the agent to run the fix-issue-prepare skill
and then fix-issue-implement. v6.0 ships `/fix-issue` and neither of the old two. The first
`agent:fix` issue in any project runs a skill that does not exist.

**Why nothing caught it.** `conformance/test-documented-skills.py` reads Markdown only; workflow
YAML is where the invocation actually executes.

**Fix.** Point the prompt at `/fix-issue`, and extend `test-documented-skills` to scan
`.github/workflows/*.yml` (and `.claude/settings.json`).

### A4. The skill-reference check reads every backticked slash-token as a skill — MEDIUM

**What.** `test-documented-skills.py` fails on `/review`, `/security-review` and `/rewind` —
Claude Code's own BUILT-IN commands, which no project ships — and on any HTTP route, third-party
API path or filesystem path written in backticks: `/recommend`, `/rows`, `/etc`, `/usr`, `/docs`,
`/redoc`. A security review that names `/etc` or FastAPI's `/docs` route fails the gate. The
default `.skill-refs-allow` declares only `health`.

**Repro.** In a clean clone, write ``the seat ran `/security-review` `` or ``probed `/etc/passwd` ``
in any delivered Markdown file and run `python3 conformance/test-documented-skills.py`.

**Fix.** Ship the harness built-ins in the default allowlist (at least review,
security-review, rewind, init, compact, clear, help and model); treat a token
followed by a second path segment as a path, not a skill; and ship the common filesystem roots.
**Workaround here:** 20 declared rows in `.skill-refs-allow`, each with a reason.

### A5. Package-relative module paths never resolve — MEDIUM

**What.** `test-documented-paths.py` resolves a backticked path against the repository root, beside
the citing document, or by bare basename. A Python project names its modules relative to the
package — `workflows/refresh.py` for `src/app/workflows/refresh.py` — and every such reference
fails although the file exists.

**Fix.** Before failing, accept a path when exactly one file in the tree ends with `/<path>`.
**Workaround here:** `workflows/*` and `app/workflows/*` declared in `.path-refs-allow`.

### A6. `.gitignore` does not ignore the report the package tells pytest to write — LOW

**What.** `pyproject.toml` passes `--junitxml=.pytest-report.xml`; `.gitignore` has no entry for
it. After the first `make test`, `git status` shows it untracked, and with `git add -A` habits it
gets committed. (The package's own rule is `git add -u`, which reduces but does not remove this.)

**Fix.** Add `.pytest-report.xml` to the shipped `.gitignore`.

### A7. The shipped rulebook contradicts itself on git, in one paragraph — MEDIUM

**What.** `AGENTS.md` §3 opens with A0.5: *"the OWNER … makes the commits at EVERY MILESTONE …
Owner also makes a labeled checkpoint commit per wave"*, then says *"Git authority (this replaces
the checkpoint lane)"* and describes the agent committing on a branch and opening draft PRs. The
Escalate line below still says *"agent commit on main = A1 = explicit owner ADR only"*. A new agent
reads three rules about who commits.

**Fix.** Rewrite the A0.5 sentence to say what survives (the owner reviews per milestone and
merges); drop the checkpoint-commit clause; keep one statement of git authority.

### A8. Provenance stripping left broken sentences in shipped text — LOW, but visible on day one

Measured in the clean clone:

- `AGENTS.md:49-50` — *"a dedicated make target (removed at ) and never pushed"*.
- `AGENTS.md:121` — *"Change `/` (or equivalent) public contract without ADR"* (was `/v2`).
- `docs/decisions.md:164-206` — four headings read *"P-005 —: risk-tiered…"*.
- `docs/decisions.md:268` — *"the checkpoint lane (.1)"*; `:289` says it "does not edit" an
  ADR numbered 196 in DevFlow's own register, which exists in no installation.
- `AGENTS.md` §3: *"A harvest produces PROCESS changes only ."* (a dangling citation).

**Fix.** Run the stripper's output through a check for empty parentheses, `—:` and a space before
a period, and fail the export on any hit. D-999 should cite what it supersedes by a name that
exists in an installation.

### A9. `Project_Implementation_Prompt.md` names the wrong methodology — LOW

**What.** Both prompts open with *"This project runs on General Pipeline v3.3"* and *"This is a
running General Pipeline v3.3 project"*. The first message a fresh agent receives names a product
and version that the tree it is standing in no longer is.

**Fix.** Say DevFlow, and derive the version from `.gp/installed` or the records (A-class items
already derive it; this prose does not).

### A10. `AGENTS.md` is over its own hard cap as shipped — LOW

**What.** The file states *"≤80 target, ≤150 hard cap"* and ships at 176 lines. A project that
adds its §1–2 context (it must) lands near 185.

**Fix.** Diet the shipped file, or make the cap a gate so the package cannot ship over it.

### A11. `/cycle-close` writes retrospectives the record schema cannot type — LOW

**What.** Governance is now derived from `record_type:` frontmatter, and `RECORD_TYPES` has no
`retrospective`. `/cycle-close` produces `docs/retrospectives/m{N}-retrospective.md` and says
nothing about its frontmatter, so a project that types it `retrospective` (the obvious choice) fails
`R2`, and one that omits frontmatter leaves its retrospectives ungoverned.

**Fix.** Add `retrospective` to `RECORD_TYPES` (and regenerate the schema), and have
`/cycle-close` write the frontmatter. **Workaround here:** added locally, schema regenerated.

### A12. `test-ci-yaml.py` crashes, reported as a FAILURE with no output, on a test matrix — HIGH

**What.** Without PyYAML the check falls back to `_minimal_parse`, whose docstring promises to
REFUSE (exit 2) on constructs it does not handle. It raises `ValueError` instead, `main()` does not
catch it, and the process exits 1 with a traceback on stderr, so `run-all.py` prints
`[FAIL] test-ci-yaml.py (no output)`. The construct is the most common one a project adds to its
CI: `python-version: ['3.12', '3.14']` in a matrix. The shipped `install-and-governance` job runs
the check with the runner's bare interpreter, which has no PyYAML.

**Repro.** Add a matrix line like the above under `jobs:` in a clean clone's `ci.yml`, then run
`python3 conformance/test-ci-yaml.py` with an interpreter that lacks PyYAML: traceback, exit 1.

**Fix.** Catch the refusal in `main()` and exit 2 (NOT-EVALUABLE) as documented, and install PyYAML
in the governance job (it is already a declared dev dependency). **Workaround here:** the job
installs PyYAML first.

### A13. The shipped `dep-audit` job fails on every new project — HIGH

**What.** `ci.yml` installs the project editable and runs `pip-audit --strict` over the
ENVIRONMENT. The project itself is in that environment and is not on PyPI, and `--strict` turns
"could not be audited" into a failure. `--skip-editable` does not help: under `--strict` a skipped
distribution is also an error. Locally `make deps` passes because it runs without `--strict`, so
the gate is green on the owner's machine and red in CI.

**Repro.** Any clean clone with a real project name: `pip install -e . && pip-audit --strict` ->
`Dependency not found on PyPI and could not be audited: <name>`.

**Fix.** `pip-audit --strict .` audits the project's DECLARED dependencies, which is the question
the job asks; measured here: `No known vulnerabilities found`. Make `make deps` and CI run the same
command.

### A14. The shipped CI calls a distribution-only script — MEDIUM

**What.** `install-and-governance` runs `python3 conformance/falsify.py`. INSTALL-MANIFEST classes
that file GP-INTERNAL and it is absent from the package, so the step fails in every installation.
`make falsify` already handles this correctly (it says SKIPPED in an installation).

**Fix.** Call `make falsify` from CI. **Workaround here:** done.

### A15. `test-documented-paths.py` reads the working tree, so it passes locally and fails in CI — MEDIUM

**What.** A path resolves if the file EXISTS on disk, so gitignored, generated files
(`coverage.json`, a status record written next to a database, a per-session note under `.claude/`)
satisfy the check on the developer's machine and are missing on the CI runner. The same commit is
green locally and red in CI, with no hint why.

**Fix.** Resolve against `git ls-files` (plus the manifest's PROJECT list) rather than the
filesystem, so a local run answers the question CI will ask.

### A16. `bootstrap-check.sh` aborts on the first placeholder in a project ADR — HIGH

**What.** In the C1 block, the `docs/decisions.md` scan increments `ph_hits` before the line that
initialises it, and the script runs under `set -u`. A single placeholder in a project ADR prints the
FAIL, then `ph_hits: unbound variable`, and the script exits before C2-C10 run. When the scan finds
nothing, the later `ph_hits=0` simply discards its count.

**Repro (clean clone).** Append `## D-100 — x` with a body line `The owner is <owner name>.` to
`docs/decisions.md` and run `make bootstrap-check`: the output stops after C1.

**Fix.** Initialise `ph_hits=0` before the decisions scan and delete the later reset. Also strip
inline code spans in that scan, as the must-fill scan should (a `--db <path>` in an ADR is notation).

### A17. `.gp/installed` is meant to be committed and is rewritten by every `make` target — MEDIUM

**What.** INSTALL-MANIFEST says the project COMMITS its marker. `make install` writes it, including
`installed_from_commit: <HEAD>`, and `install` is a prerequisite of `lint`, `test`, `typecheck`,
`check` and `gate` (and the post-edit hook runs `make gate`). So every commit makes the committed
marker stale, and the next `make check` dirties the tree. Combined with A2, it also runs pip.

**Fix.** Write the marker only from an explicit `make install` that nothing depends on, and omit
fields that change with every commit -- or gitignore it and say so. **Workaround here:** gitignored.

### A18. Frontmatter makes a TEMPLATE a "record", so templates escape the git and command checks — HIGH

**What.** `conformance/lib_record.py` treats any Markdown file whose head carries `record_type:` as
a record, and records are skipped by `test-git-authority` and `test-documented-commands`. Every
shipped `*.template.md` carries frontmatter. A template that tells an agent to
`git push origin main`, or to run a make target that does not exist, passes -- and a template is
copied into every new record. The same holds for the plan of the milestone being worked. In this
project the rule skipped 235 of 302 documents; graded command references fell from 580 to 194.

**Repro (clean clone).** Append ``run `git push origin main` `` to `docs/wave-checklist.template.md`
and run `python3 conformance/test-git-authority.py`: PASS.

**Fix.** A template is an instruction surface whatever its frontmatter says; so is the current
milestone plan. Only artefacts that describe the past are records. **Workaround here:** both
excluded from `is_record`; plans of closed milestones are records with or without frontmatter.

### A19. The shipped `.path-refs-allow` hides every dangling path under `src/`, `tests/` and `docs/plans/` — HIGH

**What.** The allowlist ships rows `src/*`, `tests/*`, `test_*.py`, `docs/plans/*` and
`docs/research/*`, meant for field evidence in `playbook-seeds.md`. `fnmatch` lets `*` cross `/`, so
in a real project these rows match every source, test and plan path, and a live instruction naming
a deleted file passes. It also allowlists `scripts/checkpoint.sh`, the script D-999 removed.

**Repro.** In a project with code, write a backticked path to a missing file under src/app/ into `AGENTS.md` and run
`python3 conformance/test-documented-paths.py`: PASS. Measured here: 15 of 15 planted paths passed.

**Fix.** Ship exact paths for the seeds' evidence (six here), and scope rows by CITING document as
well as target (see B1). **Workaround here:** exact rows only.

### A20. DevFlow contradicts itself on the `GP-Agent:` trailer — MEDIUM

**What.** `AGENTS.md` §5 says an agent commit carries the `GP-Agent` / `GP-Task` trailers.
`conformance/test-git-authority.py` and `test-commit-identity.py` removed every trailer check as
"AI attribution", and `issue-agent.yml`'s own comment still says the check asserts it. A reader
cannot tell whether an agent commit must carry the trailer.

**Fix.** Decide. A trailer naming a machine ROLE is attribution to a role, not AI attribution, and
it is what keeps agent work separable when an agent and the owner share a forge account. This
project kept it and checks it on branch commits and in `issue-agent.yml`.

### A21. The identity check is vacuous whenever the agent commits under the local git identity — MEDIUM

**What.** `test-commit-identity.py` reads the OWNER from `git config user.email`. In a local lane
the agent commits under whatever identity the clone is configured with, so owner and agent are the
same address and the check compares the agent with itself -- green, grading nothing. It also
reports an unknown agent identity as a "third identity" once an owner is given.

**Fix.** Require `--owner-email` (from a committed config, not the clone's git config), and let a
project declare its agent identities.

### A22. Retired skill names survive in shipped prose no check reads — LOW

`METHODOLOGY.md:409` and `:550`, `docs/closure-checklist.md:4` and `pipeline-schema.html:322,342,402`
name quarterly-handover, retrospect and fix-issue-prepare/implement. They are not backticked, so
`test-documented-skills` never sees them.

### A23. `make harvest-context` is listed in `make help` and fails in every installation — LOW

It runs `scripts/gen_harvest_context.py`, which is distribution-only. `harvest-context-check`
guards for this; `harvest-context` does not.

### A24. The pre-tool hook covers half of D-999 — MEDIUM

The shipped `.claude/settings.json` hook blocks `git push origin main`, `HEAD:main` and
`main:main`, but lets `gh pr merge`, `gh pr ready`, `git commit --no-verify` and
`git push origin refs/heads/main` through (each piped through the hook command: exit 0). Those are
exactly the actions D-999 reserves for a human.

---

## B. Any project hits these as it grows

### B1. Deleting or renaming a file turns every record that ever named it into a gate failure — HIGH

**What.** Records are append-only (B.2) and `test-documented-paths.py` grades every delivered
Markdown file, records included. So the first time a project deletes or renames a file, every
review, plan and ledger row that quoted it fails conformance, forever. `.path-refs-allow` is keyed
by TARGET path, so the only remedy is a new row per removed file, and the list only grows.

**Measured here.** 91 dangling references on the first run, all in historical records, none a real
broken instruction. Retiring one script (`scripts/conformance_gate.py`) added 10 more at once.

**Fix.** Distinguish instructions from evidence: grade live documents (README, AGENTS, rules,
templates, skills) strictly; grade append-only records by the date they were written, or exempt
them by CITING-document glob. The distribution already has this idea — X4's `_evidence()` exempts
research and harvest documents — but installations do not get it.

### B2. A tightened wave template invalidates every earlier wave record — MEDIUM

**What.** `scripts/wave_check.py` requires `Mutant set author:`, `Observed RED:` and
`Owner instruction:` on every record it reads, regardless of the record's `process_version`. A
project that upgrades — or simply keeps records across a template change — has every earlier close
fail, which is exactly what GPF-001 forbids. Its own positive fixture passes only because it was
rewritten at the same time.

**Fix.** Scope each required field by the `process_version` the record declares.
**Workaround here:** the three fields are required only of records declaring a version after v5.0.

### B3. `shell_dialect_check.sh` fails a sourced library — LOW

**What.** A file meant to be `source`d has no shebang, and the check fails it for not declaring
`#!/usr/bin/env bash`. Adding a shebang to a library is harmless but misleading.

**Fix.** Accept a `# shellcheck shell=bash` directive as the dialect declaration.

### B4. Two governance-selection mechanisms, one of them half-retired — LOW

**What.** `check_records.py` now derives the governed set from frontmatter (17-8) and exempts through
`.governed-records-exempt`, but `.governed-records` still ships, still reads as authoritative, and
`test-governed-paths.py` still grades its globs (rejecting `docs/research/*.md` as a "directory
sweep" that no longer selects anything on its own). A reader cannot tell which file decides.

**Fix.** Say in `.governed-records` what it still does after 17-8, or retire it.

---

## C. Version-jump only (brief)

- **C1. No upgrade path.** Nothing in the package describes moving an installation from GP v5.0 to
  DevFlow v6.0. A copy-over deletes a project's own controls; this install needed a three-way
  merge against the GP `v5.0` tag (23 files both sides changed, 36 the project never touched).
  A short UPGRADING.md with that recipe would have saved most of the time.
- **C2.** `write_install_marker.py` refuses to install when `docs/decisions.md` has no
  `process_version:` — true of every v5.0 project. The message is clear; the upgrade note should
  say to add it.
- **C3.** `scripts/coverage_floor.py` changed MEANING between versions (per-module floor in v5.0,
  skip budget in v6.0) under the same name. A project that had customised the old one gets a
  silent swap; this one moved its version to `scripts/module_coverage_floor.py`.
- **C4.** Records written under v5.0 with `status: proposed` (a value the flow no longer has) were
  outside the old glob selection and are inside the new frontmatter selection, so they fail `R2`.
- **C5.** Project controls that DevFlow may want upstream, carried through this merge: a review
  must be a FILE by `seat: independent` (`scripts/wave_check.py` `review_seat_problems`); the L1
  language rule failing closed on an unbalanced fence and handling double-backtick spans
  (`check_records.py`); inline code spans stripped in the Stage-0 placeholder scans, both the
  must-fill files and the project ADRs (`bootstrap-check.sh`; GPF-003 does neither).

---

*Filed by the lead agent of model_ranking (Claude Code, local lane) at the DevFlow v6.0 adoption,
2026-09-23. Every A-class item was reproduced on a clean clone before it was written here.*
