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
JOURNEY ?= scripts/journey.py
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

.PHONY: help install test lint format typecheck check run clean standup secrets deps slopsquat bootstrap-check smoke-deps _check_python

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
	$(PY) -m ruff check src tests

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
check: lint typecheck test check-records check-records-selftest install-check pin-check

pin-check:  ## M3 closure, V4C-49 + INV-14: every workflow action is SHA-pinned (40-hex), never a mutable tag
	@echo "[pin-check] INV-14 — no mutable-tag 'uses:' in .github/workflows"
	@if grep -rnE '^\s*-?\s*uses:\s*[^ ]+@(v[0-9][^ ]*|main|master)\b' .github/workflows/; then \
	  echo "  FAIL: a workflow action is pinned to a MUTABLE tag — pin the 40-hex commit SHA (INV-14)."; exit 1; \
	else echo "  OK: all actions SHA-pinned"; fi

# v2.0: security gates as named Make targets
secrets:
	@command -v gitleaks >/dev/null 2>&1 || { echo "Install gitleaks: brew install gitleaks"; exit 1; }
	gitleaks detect --source . --no-git -v

deps: install
	$(PY) -m pip_audit

slopsquat: install
	@echo "Checking all imports exist on PyPI..."
	@$(PY) -c "import importlib.metadata as m; [print(d.metadata['Name']) for d in m.distributions()]" | sort -u

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
smoke-deps:
	@echo "L.8 (configured != working): add one real invocation per external dependency here."
	@echo "  e.g. call the model endpoint once; publish+consume one queue message; ping the callback."
	@echo "  Inspect the response, not the catalog/config UI. (L.9: also read config back from the process.)"

wave-check:  ## v3.1 V3C-69: verify a filled wave-close checklist (make wave-check FILE=docs/plans/mN-wave-W-close.md)
	@test -n "$(FILE)" || { echo "usage: make wave-check FILE=docs/plans/m{N}-wave-{W}-close.md"; exit 1; }
	@test -f "$(FILE)" || { echo "FAIL [V3C-69]: $(FILE) missing -- copy docs/wave-checklist.template.md"; exit 1; }
	@if grep -qE '\|[[:space:]]*\|[[:space:]]*$$' "$(FILE)"; then echo "FAIL [V3C-69]: empty evidence/status cells remain in $(FILE)"; exit 1; fi
	@if grep -qE '<agent>|<YYYY-MM-DD>|<start>' "$(FILE)"; then echo "FAIL [V3C-69]: placeholders unfilled in $(FILE)"; exit 1; fi
	@echo "wave-check PASS: $(FILE)"

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

check-templates:  ## v3.5 V3C-99 (REPAIRED v4.1): every SHIPPED config template must instantiate the settings parser
	@echo "[check-templates] booting settings from each shipped env template..."
	@found=0; fail=0; \
	for f in .env.example deploy/*.env.example; do \
	  [ -f "$$f" ] || continue; \
	  found=1; \
	  if env $$(grep -vE '^\s*(#|$$)' "$$f" | xargs) $(PY) -c "from app.config import Settings; Settings()" >/dev/null 2>&1; then \
	    echo "  OK   $$f"; \
	  else \
	    echo "  FAIL $$f — the shipped template does not satisfy the settings parser"; fail=1; \
	  fi; \
	done; \
	if [ "$$found" = "0" ]; then \
	  echo "  NOT WIRED [V3C-99]: no .env.example / deploy/*.env.example found."; \
	  echo "  This target is UNWIRED in the starter package and FAILS ON PURPOSE (v4.1 Phase-0 repair:"; \
	  echo "  a declared control that silently passes is worse than an absent one). Wire it to your"; \
	  echo "  settings module + shipped templates, or delete the row from docs/closure-checklist.md §B.3."; \
	  exit 1; \
	fi; \
	exit $$fail

cold-start:  ## v3.5 V3C-99 (REPAIRED v4.1): boot against ZERO persisted state; serve-ready or honest not-ready
	@echo "[cold-start] NOT WIRED [V3C-99] — this target FAILS until the project wires it (v4.1 Phase-0 repair)."
	@echo "  Wire: bring up an EMPTY datastore (e.g. docker run --rm postgres:16), boot the app from the"
	@echo "  SHIPPED template, poll /ready until 200 or exit non-zero WITH the not-ready reason."
	@echo "  Then replace this body and add the CI job. Guidance-only targets must not report success."
	@exit 1

journey:  ## v3.5 V3C-106 (script SHIPPED in v4.1): black-box customer journey (make journey URL=https://...)
	@test -n "$(URL)" || { echo "usage: make journey URL=https://deployed-host [JOURNEY=scripts/journey.py]"; exit 1; }
	@test -f "$(JOURNEY)" || { echo "FAIL [V3C-106]: $(JOURNEY) missing — copy scripts/journey.py and fill the steps"; exit 1; }
	@$(PY) "$(JOURNEY)" --base-url "$(URL)"
