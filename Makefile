# The single source of truth for build, test, lint and gate commands. Use these targets; do not
# invent ad-hoc shell pipelines. `make help` lists every one of them.

# Auto-detect a Python >= 3.11: the first of these names that runs and is new enough. Override
# with `make install PYTHON=/path/to/python`. Seed C.2: pin a minimum, not a fixed version.
# `python` is last for Windows, where the python.org installer names it so, and where `python3`
# can be the Microsoft Store alias -- it prints an error and exits non-zero, so the version test
# skips it rather than choosing it.
PYTHON ?= $(shell \
  for v in python3.13 python3.12 python3.11 python3 python; do \
    if command -v $$v >/dev/null 2>&1; then \
      if $$v -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then \
        echo $$v; break; \
      fi; \
    fi; \
  done)
# Searched once, not at every use.
PYTHON := $(PYTHON)

# The interpreter for DevFlow's own scripts. They need only the standard library, so they run
# before `make install` too: the one found above, else the venv's (built with PYTHON=...). None at
# all stops the recipe with the reason, rather than running a script through whatever `python3`
# happens to mean on this machine.
SYS_PY = $(or $(PYTHON),$(firstword $(wildcard $(PY) $(PY).exe)),$(error no Python >= 3.11 found on PATH -- install one (INSTALL.md) or pass PYTHON=/path/to/python))

# Every Python this Makefile starts reads and writes UTF-8, whatever the console's code page: on a
# cp1254 (Turkish) Windows console, a file written in the locale encoding and read back as UTF-8
# lost its letters, and a script printing an arrow crashed after its work was done.
export PYTHONUTF8 := 1

VENV ?= .venv
# A Windows venv keeps its interpreter in Scripts/, every other OS in bin/. Read from the venv once
# it exists; before that -- the first `make install` -- from the OS.
VENV_BIN := $(if $(wildcard $(VENV)/Scripts/python.exe),$(VENV)/Scripts,$(if $(wildcard $(VENV)/bin/python),$(VENV)/bin,$(if $(filter Windows_NT,$(OS)),$(VENV)/Scripts,$(VENV)/bin)))
PY := $(VENV_BIN)/python
PIP := $(PY) -m pip

# The product's stack: the one word in `.devflow-stack`, which `/setup-project` writes (`python`
# when the file is absent). On `python`, lint, typecheck, test and deps run as written below. On any
# other stack they run the commands the project binds in its own `stack.mk` -- STACK_LINT,
# STACK_TYPECHECK, STACK_TEST, STACK_DEPS (INSTALL.md, binding another stack) -- and a leg nobody
# bound FAILS with `BIND ME:`: a gate that goes green over a stack it cannot see is the claim nobody
# checks. DevFlow's own tooling (the venv, check_records, conformance, slopsquat, the pip-audit of
# pyproject.toml) stays Python on every stack.
STACK := $(firstword $(shell cat .devflow-stack 2>/dev/null | tr -d '\r') python)
ON_PYTHON := $(filter python,$(STACK))
-include stack.mk
# `make check-fast` only (scripts/check_fast.py), both empty unless `stack.mk` or this file sets them:
# CHECK_FAST_OWN_LEGS -- `check:` prerequisites that each get a leg of their own, beside the code legs;
# CHECK_FAST_FORMS -- `target=form` pairs: check-fast runs `form` in place of `target`
# (`swift-test=swift-test-parallel`). `make check` never uses a form. INSTALL.md has the example.
CHECK_FAST_OWN_LEGS ?=
CHECK_FAST_FORMS ?=
# $(call bound,VAR): the project's command for VAR, or a failure naming what to bind, and where.
bound = $(if $(strip $($(1))),$($(1)),@echo "BIND ME: $(1) is not set for stack '$(STACK)' -- define it in stack.mk (INSTALL.md: binding another stack)" >&2; exit 1)
# $(call need,TOOL,WHAT): stop with exit 2 -- cannot run, not a finding -- when TOOL is not on PATH.
need = @command -v $(1) >/dev/null 2>&1 || { echo "$(1) not installed: cannot $(2) (INSTALL.md)" >&2; exit 2; }

.DEFAULT_GOAL := help

# Every target is declared phony. `conformance` is also a directory: undeclared, make called the
# target "up to date" and never ran it, so `make gate` skipped the whole conformance suite.
.PHONY: help install test lint format typecheck check check-fast check-fast-config ci-liveness gate falsify conformance shell-dialect secrets deps slopsquat run clean standup bootstrap-check cold-start journey smoke-deps closes closure-check wave-check export-project labels hooks install-check check-records check-records-selftest coverage-floor swift-test swift-test-parallel client-decls wave-check-all harvest-context harvest-context-check

help:  ## this list, generated from the annotation on each target (a hand-written list drifts)
	@grep -hE '^[a-zA-Z0-9_.-]+:[^#]*## ' $(MAKEFILE_LIST) | sort \
	  | sed -E 's/^([a-zA-Z0-9_.-]+):[^#]*## /\1|/' | awk -F'|' '{printf "  %-24s %s\n", $$1, $$2}'

# The venv is built only when it is missing (`pyvenv.cfg` exists in every venv, on every OS), and
# the editable install runs only when pyproject.toml changed since the last one. A phony
# prerequisite here once kept the venv permanently out of date: every target rebuilt it over the
# network, and an offline `make check` failed on pip rather than on anything it checks.
$(VENV)/pyvenv.cfg:
	@echo "Using Python: $$($(SYS_PY) --version) at $$(command -v $(SYS_PY))"
	$(SYS_PY) -m venv --upgrade-deps $(VENV)

$(VENV)/.installed: pyproject.toml | $(VENV)/pyvenv.cfg
	$(PIP) install -e ".[dev]"
	@touch $@

install: $(VENV)/.installed  ## Stage 0: create the venv, install the project, write .gp/installed
# The marker records the version this tree installed, derived from the records' own
# `process_version`. It fails closed: a version nobody can establish is what it exists to prevent.
	@$(PY) scripts/write_install_marker.py

test: install  ## pytest in parallel, with the served artifact required (another stack: STACK_TEST)
	@# `-n auto`: one worker per core (8 on the owner's Mac). Measured before adopting it: three
	@# parallel runs, 908 passed each time, and coverage.json identical to a serial run (3188
	@# lines, 89%) -- the coverage floor below reads that file, so a parallel run that lost
	@# coverage data would have turned the floor into a false alarm. CI stays serial: `.github/`
	@# is a DevOps-owned surface (AGENTS.md section 5). A single test by hand: plain `pytest path`.
	$(if $(ON_PYTHON),MODEL_RANKING_REQUIRE_ARTIFACT=1 $(PY) -m pytest -n auto,$(call bound,STACK_TEST))
	@# W-041's per-module floor reads the coverage.json this run just wrote, so it runs HERE, in the
	@# same recipe: under DevFlow v6.6's check-fast a separate `coverage-floor` prerequisite would run
	@# in another leg, beside the tests, and read the previous run's file (D-161).
	$(if $(ON_PYTHON),$(PY) -B scripts/module_coverage_floor.py)

lint: install  ## ruff over src, tests and scripts (another stack: STACK_LINT)
	$(if $(ON_PYTHON),$(PY) -m ruff check src tests scripts,$(call bound,STACK_LINT))

format: install  ## black, then ruff --fix, over src and tests
	$(PY) -m black src tests
	$(PY) -m ruff check --fix src tests

typecheck: install  ## mypy (strict) over src (another stack: STACK_TYPECHECK)
	$(if $(ON_PYTHON),$(PY) -m mypy src,$(call bound,STACK_TYPECHECK))

check: lint typecheck test check-records check-records-selftest install-check harvest-context-check shell-dialect wave-check-all conformance swift-test client-decls  ## the offline half of the gate, one leg after another (the post-edit hook runs check-fast)

coverage-floor: install  ## W-041: no module carries materially less test proof than the rest
	@# W-041. The per-module half of the coverage gate; the global floor lives in pyproject.
	@# `make test` runs it after pytest; this target is for running it by hand on the last run.
	$(PY) -B scripts/module_coverage_floor.py

#: D-150 clause 1 as amended (W-111). The floor is no longer typed: it is the number of lines in
#: the committed test manifest, and the manifest is compared NAME BY NAME with the tests the
#: toolchain discovers. A typed integer could not see a deleted test -- the count and the
#: declarations drop together -- and it had been wrong three times. Deleting a test now requires
#: deleting its line here, which a reviewer sees in the diff.
SWIFT_TEST_MANIFEST := ios/EngineTests/test-manifest.txt
SWIFT_TEST_FLOOR := $(shell grep -c . $(SWIFT_TEST_MANIFEST))

swift-test: ## W-038: run the Engine layer's Swift tests against the SHIPPING sources
	@# A test nobody types is a test that does not run -- W-032, this project's own finding, which
	@# is why this is in `check:` and not a thing you remember. SKIPPED rather than failed where
	@# there is no toolchain: a gate that fails on a machine without Xcode gets switched off, and
	@# the skip is loud so it cannot be mistaken for a pass.
	@# NO PIPE. `swift test | tail -3` was written here first and `make swift-test` returned 0 with
	@# a deliberately broken assertion -- the pipe hands make `tail`'s status, and the failure did
	@# not even appear in the three lines shown. A gate that cannot fail, shipped inside the wave
	@# whose whole subject is code nothing executes. Proven broken, then fixed, then proven again.
	@# A COUNT FLOOR, because `swift test` exits 0 having executed nothing. Measured: a package
	@# whose test target contains no cases prints `Executed 0 tests, with 0 failures` and returns 0,
	@# so a target excluded by a bad `path:`, or a suite that stops being discovered, would pass this
	@# gate in silence. That is the THIRD time in this one wave that a Swift gate could not fail --
	@# first a pipe swallowing the status, then `runner` calling commands that do not exist, now
	@# this. Same shape as `coverage-floor`: the floor is raised deliberately, never lowered quietly.
	@if command -v swift > /dev/null 2>&1; then \
		out=`cd ios && swift test 2>&1`; rc=$$?; mkdir -p build; echo "$$out" > build/swift-test.log; [ $$rc -eq 0 ] || { echo "$$out" | grep -E "error:|failed \(" | head -30; echo "(full swift output: build/swift-test.log)"; exit 1; }; \
		line=`echo "$$out" | grep -E "Executed [0-9]+ tests, with" | tail -1`; \
		if echo "$$line" | grep -q "skipped"; then \
			echo "swift-test FAIL: a test was SKIPPED, which counts as executed."; \
			echo "$$line"; \
			echo "  M16-W1 review, M-3: a skipped test left the count and the manifest intact."; \
			exit 1; \
		fi; \
		n=`echo "$$line" | sed -E 's/.*Executed ([0-9]+) tests.*/\1/'`; \
		if [ -z "$$n" ] || [ "$$n" -lt $(SWIFT_TEST_FLOOR) ]; then \
			echo "swift-test FAIL: ran $${n:-0} test(s), floor is $(SWIFT_TEST_FLOOR)."; \
			echo "  A suite that stops being discovered exits 0 and reports nothing."; \
			exit 1; \
		fi; \
		( cd ios && swift test --list-tests 2>/dev/null ) | sort > build/swift-tests-discovered.txt; \
		if ! diff -u $(SWIFT_TEST_MANIFEST) build/swift-tests-discovered.txt > build/swift-manifest.diff 2>&1; then \
			echo "swift-test FAIL: the discovered tests are not the manifest (D-150)."; \
			head -20 build/swift-manifest.diff; \
			echo "  A test deleted from the code but left here, or added and not listed, stops the gate."; \
			echo "  Regenerate deliberately: cd ios && swift test --list-tests | sort > EngineTests/test-manifest.txt"; \
			exit 1; \
		fi; \
		echo "swift-test PASS: $$n test(s), each one named in $(SWIFT_TEST_MANIFEST)"; \
	else \
		echo "swift-test SKIPPED NO-ENVIRONMENT: no swift toolchain on PATH"; \
	fi


check-fast: install  ## `make check`'s legs side by side -- what the post-edit hook runs; `make check` stays the merge gate
	@$(PY) scripts/check_fast.py --make "$(MAKE)"

swift-test-parallel:  ## `swift-test` for `check-fast`: the same suite with --parallel, judged from xUnit
	@# `swift test --parallel` prints no `Executed N tests` line, and a serial run writes no xUnit
	@# report, so this leg reads the report: failures, skips, and EXACTLY the manifest's tests
	@# (scripts/swift_xunit_gate.py). The report is removed first so a stale one cannot pass.
	@# A skip is read from the SOURCES: measured, `--parallel` reports a skipped test as passed.
	@if command -v swift > /dev/null 2>&1; then \
		mkdir -p build; rm -f build/swift-xunit.xml; \
		out=`cd ios && swift test --parallel --xunit-output ../build/swift-xunit.xml 2>&1`; rc=$$?; \
		echo "$$out" > build/swift-test-parallel.log; \
		[ $$rc -eq 0 ] || { echo "$$out" | grep -E "error:|failed|✘" | head -30; echo "(full swift output: build/swift-test-parallel.log)"; exit 1; }; \
		$(SYS_PY) -B scripts/swift_xunit_gate.py build/swift-xunit.xml $(SWIFT_TEST_MANIFEST) $(dir $(SWIFT_TEST_MANIFEST)); \
	else \
		echo "swift-test SKIPPED NO-ENVIRONMENT: no swift toolchain on PATH"; \
	fi

client-decls: install  ## W-122 / D-126: the privacy invariant checked against RESOLVED declarations
	@# Six rounds of a word list over the client were each bypassed by the next seat -- backticks,
	@# a comment between two tokens, a typealias, `NSMutableURLRequest`, a markdown link, Handoff.
	@# This type-checks the client against the iOS SDK and reads what the COMPILER bound each
	@# reference to, where all of those are the same declaration. SKIPPED, loudly, with no Xcode.
	$(PY) -B scripts/client_decl_gate.py

wave-check-all: install  ## every wave-close record validated, not only the one you name
	@# W-032 / this project's own field finding: a gate that is not in the command people type
	@# does not run. The wave-record validator failed all four of one milestone's records on the
	@# same three lines and nobody knew until someone ran it by hand at closure.
	$(PY) -B scripts/wave_check_all.py

harvest-context:  ## v5.2 (16-2): regenerate the control roster a field harvest grades GP against
	@$(SYS_PY) scripts/gen_harvest_context.py

# What check_fast.py reads: exactly these two lines. Asking make, not parsing stack.mk, reads a value
# wherever it was set -- stack.mk, this file, the command line.
check-fast-config:  ## the two check-fast settings, CHECK_FAST_OWN_LEGS and CHECK_FAST_FORMS, as make sees them
	@echo "own: $(strip $(CHECK_FAST_OWN_LEGS))"
	@echo "forms: $(strip $(CHECK_FAST_FORMS))"

# ADVISORY, and deliberately not reachable from `gate`: it asks GitHub about runs that already
# happened, so it can say CI has stopped starting (a billing or runner limit) but cannot stop a push.
# It always exits 0. `/start-session` and bootstrap-check C12 run it and report its one line.
ci-liveness:  ## ADVISORY, never a gate leg: did the latest CI runs start any step? (gh; always exits 0)
	@$(SYS_PY) scripts/ci_liveness.py

# `gate` is the ONE name that means "everything this pipeline claims to enforce". The pre-push hook
# and `/pre-merge` run it, the post-edit hook runs its offline half (`make check-fast`), and CI runs
# the same legs step by step. A control that is not reachable from here is not claimed anywhere.
gate: check conformance falsify secrets deps slopsquat  ## THE gate -- everything the documents claim, actually wired
	@echo "gate PASS: $^"

harvest-context-check:  ## v5.2 (16-2): fail if HARVEST-CONTEXT.md is stale against the controls
# Distribution-side, like `falsify`. An installation has no roster to keep current and no
# `falsifications.py` to derive one from, so it SAYS so rather than failing on a file it never had.
	@if [ -f .gp-distribution ]; then $(SYS_PY) scripts/gen_harvest_context.py --check; else \
	  echo "harvest-context SKIPPED: this is an installation, not the distribution package."; fi
falsify:  ## break every control on purpose; one that cannot be broken is not a control (distribution only)
# In an installation there is no `.gp-distribution` and no falsification registry, so this SAYS it
# skipped rather than failing on a file the project never had. It is never silent: silence is how a
# leg leaves a gate unnoticed.
	@if [ -f .gp-distribution ]; then $(SYS_PY) conformance/falsify.py; else \
	  echo "falsify SKIPPED: this is an installation, not the distribution package."; \
	  echo "  The falsification registry proves the pipeline's own controls before a package ships."; \
	  echo "  Your project does not maintain them, so there is nothing here to falsify."; fi

# The venv's interpreter when there is one (the workflow check needs its PyYAML), else the one
# found above. Decided when the recipe runs: a venv built earlier in the same `make gate` counts.
conformance:  ## every gate proven against inputs it must reject
	@if [ -f "$(PY)" ] || [ -f "$(PY).exe" ]; then $(PY) conformance/run-all.py; \
	  else $(SYS_PY) conformance/run-all.py; fi

shell-dialect:  ## every shipped .sh parses and declares one dialect
	$(call need,bash,check the shell scripts)
	@bash scripts/shell_dialect_check.sh

secrets:  ## gitleaks over the working tree (install it first: INSTALL.md)
	@command -v gitleaks >/dev/null 2>&1 || { echo "gitleaks not installed: cannot scan the tree for secrets. Install gitleaks (INSTALL.md)" >&2; exit 2; }
	gitleaks detect --source . --no-git -v

deps: install  ## the DECLARED dependencies against known advisories -- the same command CI runs (another stack: STACK_DEPS too)
	$(PY) -m pip_audit --strict .
	$(if $(ON_PYTHON),,$(call bound,STACK_DEPS))

slopsquat:  ## seed F.8: DECLARED deps exist on PyPI and are not brand new (offline = non-zero, never clean)
	@$(SYS_PY) scripts/slopsquat_check.py

run: install  ## the engine on :8080, serving the repo's own artifact
	@# W-061, found by running it: `make run` is the command `note.txt` tells a developer to use to
	@# reach the engine, and from a clean environment it DID NOT START. `validate_startup_config`
	@# fails closed on an unset `MODEL_RANKING_DB` (nothing to serve) and an unset `APP_BUILD`
	@# (`/health` cannot say which code is live -- L.7). Both refusals are correct; what was wrong
	@# is that the documented command supplied neither, so the only way to run the engine was to
	@# already know something the documentation did not say.
	@#
	@# The defaults are the developer defaults and nothing more: the repo's own artifact, and a
	@# build stamp derived from HEAD so `/health` reports the commit it was started from. `?=`
	@# means an operator who sets either one keeps it -- these do not override a real deployment.
	MODEL_RANKING_DB="$${MODEL_RANKING_DB:-$(CURDIR)/advisor.db}" \
	APP_BUILD="$${APP_BUILD:-dev-$$(git rev-parse --short HEAD 2>/dev/null || echo unknown)}" \
	$(PY) -m uvicorn app.adapter.main:app --host 0.0.0.0 --port 8080 --reload

clean:  ## remove the venv and every tool cache
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage build/check-fast
	find . -type d -name __pycache__ -exec rm -rf {} +

standup:  ## where are we, in five seconds: latest process-log entry, open ADRs, plans, git state
	$(call need,bash,print the standup)
	@bash scripts/standup.sh

bootstrap-check:  ## the Stage-0 gate: placeholders, /health, core docs, universal ADRs, brief, what gates a push, CI liveness (advisory)
	$(call need,bash,run the Stage-0 gate)
	@bash scripts/bootstrap-check.sh

# Stage 5.2 go-live gates. Each binds to the DEPLOYED artefact, and each fails LOUDLY until the
# project wires it: a gate that passes before it is wired teaches the team that the board means
# nothing. Refusing one is a legal answer too -- record it in docs/refusals.md with the reason.
cold-start:  ## Stage 5.2: boot against ZERO persisted state, via the deployment's real mechanism
	@test -f docs/cold-start.sh || { \
	  echo "FAIL [cold-start]: docs/cold-start.sh does not exist."; \
	  echo "  This gate says the artefact boots from nothing -- fresh volume, fresh container, the"; \
	  echo "  REAL image, not a repo-local approximation. Nothing is wired, so that claim is false."; \
	  echo "  binds: name the artefact the deployment actually consumes."; \
	  echo "  Refusing the gate is also a legal answer: record it in docs/refusals.md and say why."; \
	  exit 1; }
	@bash docs/cold-start.sh

journey:  ## Stage 5.2: one recorded walkthrough at human speed against the DEPLOYED url (URL=...)
	@test -n "$(URL)" || { \
	  echo "FAIL [journey]: no URL. Usage: make journey URL=https://<deployed>"; \
	  echo "  This gate binds to the DEPLOYED artefact. A journey against localhost is a different"; \
	  echo "  claim about a different object -- that is the NOT-BINDING finding, not a pass."; \
	  exit 1; }
	@test -f docs/journey.sh || { \
	  echo "FAIL [journey]: docs/journey.sh does not exist."; \
	  echo "  Cold entry, credential lifecycle, a paying-customer round trip asserting CONTENT, and"; \
	  echo "  one cross-wave sequence. ~60 lines and one URL, for the best catch ratio we have."; \
	  echo "  Refusing the gate is also a legal answer: record it in docs/refusals.md and say why."; \
	  exit 1; }
	@URL="$(URL)" bash docs/journey.sh

smoke-deps:  ## Stage 5.2 (seed L.8): invoke EACH external dependency for real and inspect the RESULT
	@test -f docs/smoke-deps.sh || { \
	  echo "FAIL [smoke-deps]: docs/smoke-deps.sh does not exist."; \
	  echo "  This gate says every external dependency was invoked for real and its RESULT inspected."; \
	  echo "  Nothing is wired, so that claim is currently false and this build is red on purpose."; \
	  echo "  Write one real call per dependency (model / queue / store / callback), then re-run."; \
	  echo "  Refusing the gate is also a legal answer: record it in docs/refusals.md and say why."; \
	  exit 1; }
	@bash docs/smoke-deps.sh

closes:  ## every filled wave-close checklist and closure report in the tree, checked -- none is optional
# In DevFlow this is part of `make check`. In model_ranking it is NOT (D-161): closure_check.py grades
# every closure report by today's template, so M1-M15's fail; `wave-check-all` grades the wave closes,
# and a closure report is checked at its own closure with `make closure-check FILE=...`.
	@n=0; rc=0; for f in docs/plans/m*-wave-*-close.md; do [ -f "$$f" ] || continue; n=$$((n+1)); \
	  $(SYS_PY) scripts/wave_check.py "$$f" || rc=1; done; \
	for f in docs/closure-report-m*.md; do [ -f "$$f" ] || continue; n=$$((n+1)); \
	  $(SYS_PY) scripts/closure_check.py "$$f" || rc=1; done; \
	echo "closes: $$n close record(s) checked"; exit $$rc

closure-check:  ## check one filled milestone closure report (make closure-check FILE=docs/closure-report-mN.md)
# Written only when the milestone Quality Gate is on. A report whose criteria cite no test, or are
# not all passing, is refused.
	@test -n "$(FILE)" || { echo "usage: make closure-check FILE=docs/closure-report-m{N}.md"; exit 2; }
	@test -f "$(FILE)" || { echo "FAIL [closure-check]: $(FILE) missing -- copy docs/closure-report.template.md"; exit 1; }
	@$(SYS_PY) scripts/closure_check.py "$(FILE)"

wave-check:  ## check one filled wave-close checklist (make wave-check FILE=docs/plans/mN-wave-W-close.md)
# It refuses a file that is not a wave checklist, a close without both review verdicts, and a
# close whose review verdict is BLOCKING.
	@test -n "$(FILE)" || { echo "usage: make wave-check FILE=docs/plans/m{N}-wave-{W}-close.md"; exit 2; }
	@test -f "$(FILE)" || { echo "FAIL [wave-check]: $(FILE) missing -- copy docs/wave-checklist.template.md"; exit 1; }
	@$(SYS_PY) scripts/wave_check.py "$(FILE)"

export-project:  ## produce an INSTALLATION from this distribution package (DEST=/path/to/project; distribution only)
	@test -n "$(DEST)" || { echo "usage: make export-project DEST=/path/to/your-project"; exit 2; }
	@test ! -e "$(DEST)" -o -d "$(DEST)" || { echo "FAIL: $(DEST) exists and is not a directory"; exit 2; }
# Distribution-side, like `falsify`: the exporter never ships, so an installation SAYS so and exits
# non-zero rather than dying on a missing file. The export is refused if any delivered file carries
# the pipeline's internal provenance.
	@if [ -f scripts/export_project.py ]; then $(SYS_PY) scripts/export_project.py "$(DEST)" \
	  && $(SYS_PY) scripts/provenance_check.py "$(DEST)"; else \
	  echo "export-project UNAVAILABLE: this is an installation, not the distribution package."; \
	  echo "  Exporting is how the pipeline PRODUCES a delivery; you are already holding one."; exit 2; fi
	@echo "  now: cd $(DEST) && make install-check"

labels:  ## Stage 0: create the issue-label vocabulary on GitHub, once per repo -- only the missing ones
# Without `gh` it prints the table to create by hand, and exits 2.
	@$(SYS_PY) scripts/create_labels.py

hooks:  ## Stage 0, once per clone: `make gate` runs before every push (the enforcement where CI does not run)
	$(call need,git,install the pre-push hook)
	@git config core.hooksPath .githooks
	@echo "core.hooksPath = $$(git config core.hooksPath) -- pre-push now runs make gate"

install-check:  ## is this tree a COMPLETE install? (M0-M4 against INSTALL-MANIFEST.md)
	@echo "[install-check] every PROJECT path present, no GP-INTERNAL path leaked"
# The distribution package is not an installation (M0 says so), so here it SAYS it skipped: an
# export is graded as an installation by conformance/test-delivered-tree.py, and the package's own
# manifest (M3) by check-records. It runs with the interpreter found above, which needs no venv:
# run with the venv's, before `make install` had built it, exit 127 was reported as "this tree is
# not a complete install", on the first command a user types.
	@if [ -f .gp-distribution ]; then \
	  echo "install-check SKIPPED: this is the distribution package, not an installation."; \
	  echo "  make export-project DEST=/path produces one; run install-check inside THAT tree."; \
	else \
	  $(SYS_PY) scripts/check_records.py --install . || { \
	  echo "  FAIL: this tree is not a complete install. See INSTALL-MANIFEST.md."; \
	  echo "  A missing PROJECT path means a rule was never read, not that a file is untidy."; exit 1; }; fi

check-records:  ## validate the governance records (frontmatter, references, manifest)
	@$(SYS_PY) scripts/check_records.py --root .

check-records-selftest:  ## prove the validator is not a no-op: it must reject the conformance fixtures
	@$(SYS_PY) scripts/check_records.py --self-test --root .
