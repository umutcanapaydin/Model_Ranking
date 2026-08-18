# Pipeline v3 Makefile -- single source of truth for build / test / lint commands.
# Any agent must use these targets; do not invent ad-hoc shell pipelines.

# Auto-detect a Python >= 3.11. Override with `make install PYTHON=/path/to/python`.
# Seed C.2: pin a minimum, not a fixed version.
PYTHON ?= $(shell \
  for v in python3.13 python3.12 python3.11 python3; do \
    if command -v $$v >/dev/null 2>&1; then \
      if $$v -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then \
        echo $$v; break; \
      fi; \
    fi; \
  done)

VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
RECORDS ?= docs

# Hard fail if no compatible Python was found.
_check_python:
	@if [ -z "$(PYTHON)" ]; then \
	  echo ""; \
	  echo "ERROR: no Python >= 3.11 found on PATH."; \
	  echo "  Install via Homebrew:  brew install python@3.12"; \
	  echo "  Or override:           make install PYTHON=/path/to/python"; \
	  echo ""; \
	  exit 1; \
	fi
	@echo "Using Python: $$($(PYTHON) --version) at $$(command -v $(PYTHON))"

# v4.3.2 REPAIR (audit B1). `conformance` is also a DIRECTORY in this package. Make saw a target
# with no prerequisites whose name is an existing file, called it up to date, and never ran the recipe:
#   $ make conformance   ->  "make: 'conformance' is up to date."  exit 0, recipe never expanded
# So `make gate` -- the one name this release says means "everything we claim" -- silently skipped the
# entire conformance suite, which is this release's flagship deliverable. **A control with a caller,
# a name, and no execution.** Every target is declared here now, not just the ones that collide today.
# v5 control screen (2026-08-12): `check-templates`, `cold-start` and `journey` were REMOVED.
# All three test the SHIPPED artifact against the real world, which is a good idea and the reason they
# were written. All three need a deployed URL and a live environment that neither this package nor a
# fresh project has -- so in five versions nobody was ever able to write down how to break them, and
# none was ever demonstrated to catch anything. Two of them are TB-001 and TB-002, the ORIGINAL dead
# controls whose discovery produced "a declared control that silently passes is worse than an absent
# one." They are on `docs/watchlist.md` with their triggers, and they come back the day a project can
# actually run them. **Unprovable here is not the same as wrong -- but it is not a control either.**
.PHONY: falsify bootstrap-check check check-records check-records-selftest  clean  conformance deps export-project format gate help install install-check  lint run secrets slopsquat smoke-deps standup test typecheck wave-check

help:
	@echo "Commands:"
	@echo "  make install      Create venv and install dev dependencies"
	@echo "  make test         Run pytest with coverage"
	@echo "  make lint         Run ruff"
	@echo "  make format       Run black + ruff --fix"
	@echo "  make typecheck    Run mypy"
	@echo "  make check        lint + typecheck + test (the merge gate)"
	@echo "  make secrets      Run gitleaks (secret scan)"
	@echo "  make deps         Run pip-audit (dependency vuln scan)"
	@echo "  make slopsquat    Verify all imports exist on PyPI"
	@echo "  make run          Start the API service locally on :8080"
	@echo "  make standup      Print project state (LLM-free)"
	@echo "  make bootstrap-check  Stage-0 gate: placeholders/L.7 health/templates/ADRs/license + no default-admin/plaintext creds (FB-1, V3C-11)"
	@echo "  make smoke-deps   Stage 4.3 go-live: invoke each external dependency once (L.8)"
	@echo "  make clean        Remove venv and caches"

$(VENV)/bin/python: _check_python
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

install: $(VENV)/bin/python
	$(PIP) install -e ".[dev]"

test: install
	$(PY) -m pytest

lint: install
	$(PY) -m ruff check src tests scripts

format: install
	$(PY) -m black src tests
	$(PY) -m ruff check --fix src tests

typecheck: install
	$(PY) -m mypy src

# v4.3 REPAIR (V4C-78). `check:` used to be `lint typecheck test` — and `bootstrap-check` and
# `check-records` had targets that NOTHING called: not here, not in .pre-commit-config.yaml, not in
# ci.yml. The gate that decides whether a project is correctly INSTALLED was reachable only by
# someone who already knew its name. Measured in the field: a project closed two milestones with 37
# declared files missing. The owner, translated from Turkish: "you wrote a verify script -- that one does not fire either."
# v4.3.2. `pipeline-design.md` described a commit hook running make check + gitleaks + pip-audit +
# slopsquat, and a PreToolUse hook blocking .env writes AND destructive git commands. The hook ran
# `make check` and blocked .env. `make check` called no security target at all. **Four of six advertised
# controls did not exist**, in the document every reviewer reads to learn what is enforced.
#
# `gate` is now the ONE name that means "everything this pipeline claims to enforce". The hook calls it,
# CI calls it, and the design doc points at it. If a control is not reachable from here, we do not claim it.
gate: check conformance falsify secrets deps slopsquat  ## THE canonical gate -- everything the docs claim, actually wired
	@echo "gate PASS: lint typecheck test records install secrets deps slopsquat"

falsify:  ## v5: break every control on purpose; one that cannot be broken is not a control
# Distribution-side. In an installation there is no `.gp-distribution` and no `export_project.py`,
# so this SAYS SO rather than failing on a missing file the user never had. It does not silently
# skip: silence is how a leg leaves a gate unnoticed.
	@if [ -f .gp-distribution ]; then python3 conformance/falsify.py; else \
	  echo "falsify SKIPPED: this is an installation, not the distribution package."; \
	  echo "  The falsification registry proves GP's own controls before a package ships."; \
	  echo "  Your project does not maintain them, so there is nothing here to falsify."; fi

conformance:  ## v4.3.2: every gate proven against inputs it must reject (V4C-80)
	@$(PY) conformance/run-all.py 2>/dev/null || python3 conformance/run-all.py

check: lint typecheck test check-records check-records-selftest install-check

# v2.0: security gates as named Make targets
secrets:
	@command -v gitleaks >/dev/null 2>&1 || { echo "Install gitleaks: brew install gitleaks"; exit 1; }
	gitleaks detect --source . --no-git -v

deps: install
	$(PY) -m pip_audit

slopsquat:  ## F.8: DECLARED deps exist on PyPI and are not brand new (offline = non-zero, never clean)
	@python3 scripts/slopsquat_check.py

run: install
	$(PY) -m uvicorn app.adapter.main:app --host 0.0.0.0 --port 8080 --reload

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

# Project-state ops (per seed C.7): LLM-free, deterministic, fast.
standup:
	@bash scripts/standup.sh

# Stage-0 executable gate (FB-1 / seed C.11; v3 adds V3C-11): run at the END of
# Stage 0, after filling PROJECT placeholders. Fails on stray placeholders, a
# non-L.7 /health, still-template prd/decisions/architecture, missing universal
# ADRs, a wrapped/forked OSS engine without a license review, or an obvious
# default-admin password / plaintext-credential pattern in source (V3C-11; full
# baseline in docs/security-baseline.md). The UNFILLED starter is expected to
# fail this (it is a template).
bootstrap-check:
	@bash scripts/bootstrap-check.sh

# Stage 4.3 go-live readiness (L.8 "configured != working"): invoke EACH external
# dependency once for real and inspect the RESULT, not the config screen. Replace
# the body below with one real smoke call per dependency (model / queue / store /
# callback target). Until filled, this is a no-op reminder so it never blocks CI.
smoke-deps:  ## Stage 4.3 (L.8): invoke EACH external dependency for real and inspect the RESULT
# v4.3.2 REPAIR. This target shipped as an explicit no-op that exited 0 -- with a comment saying
# "until filled, this is a no-op reminder so it never blocks CI." That sentence is the exact inverse of
# this lineage's founding doctrine: **a declared control that silently passes is worse than an absent
# one.** An unwired control must FAIL LOUDLY. It now does, and wiring it is a one-line file.
	@test -f docs/smoke-deps.sh || { \
	  echo "FAIL [L.8]: docs/smoke-deps.sh does not exist."; \
	  echo "  This gate says every external dependency was invoked for real and its RESULT inspected."; \
	  echo "  Nothing is wired, so that claim is currently false and this build is red on purpose."; \
	  echo "  Write one real call per dependency (model / queue / store / callback), then re-run."; \
	  echo "  Refusing the gate is also a legal answer: record it in docs/refusals.md and say why."; \
	  exit 1; }
	@bash docs/smoke-deps.sh

wave-check:  ## v3.1 V3C-69: verify a filled wave-close checklist (make wave-check FILE=docs/plans/mN-wave-W-close.md)
# v4.3.2 REPAIR. `make wave-check FILE=README.md` returned PASS, and so did the closure checklist. The
# gate tested "is this a file with no empty table cells and no three specific placeholders" -- which
# almost any document satisfies. It never checked that the file WAS a wave checklist. **A gate that
# passes a file it was never meant to read is not lenient, it is uninstalled**, and this one signed off
# five wave closes in the field.
	@test -n "$(FILE)" || { echo "usage: make wave-check FILE=docs/plans/m{N}-wave-{W}-close.md"; exit 2; }
	@test -f "$(FILE)" || { echo "FAIL [V3C-69]: $(FILE) missing -- copy docs/wave-checklist.template.md"; exit 1; }
	@python3 scripts/wave_check.py "$(FILE)"

export-project:  ## v4.3.2: produce an INSTALLATION from this distribution package (DEST=/path/to/project)
	@test -n "$(DEST)" || { echo "usage: make export-project DEST=/path/to/your-project"; exit 2; }
	@test ! -e "$(DEST)" -o -d "$(DEST)" || { echo "FAIL: $(DEST) exists and is not a directory"; exit 2; }
	@python3 scripts/export_project.py "$(DEST)"
	@echo "  now: cd $(DEST) && make install-check"

install-check:  ## v4.3 V4C-72/76: is this tree a COMPLETE install? (M1/M2/M3 vs INSTALL-MANIFEST.md)
	@echo "[install-check] V4C-72/76 — every PROJECT path present, no GP-INTERNAL path leaked"
# v4.3 REPAIR (auditor B2): without the python3 fallback, exit 127 from a missing interpreter was
# laundered into the specific and FALSE diagnosis "this tree is not a complete install" -- on the
# very first command the documentation tells a user to type.
	@$(PY) scripts/check_records.py --install . 2>/dev/null || python3 scripts/check_records.py --install . || { \
	  echo "  FAIL: this tree is not a complete install. See INSTALL-MANIFEST.md."; \
	  echo "  A missing PROJECT path means a rule was never read, not that a file is untidy."; exit 1; }

check-records:  ## v4.1 V4C-30: validate governance records (frontmatter, refs, propagation)
	@$(PY) scripts/check_records.py --root . || python3 scripts/check_records.py --root .

check-records-selftest:  ## v4.1 V4C-32: prove the validator is not a no-op (conformance fixtures)
	@python3 scripts/check_records.py --self-test --root .

