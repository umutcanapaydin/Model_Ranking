#!/usr/bin/env bash
# bootstrap-check.sh -- executable Stage-0 gate (seed C.11 / FB-1, Pipeline v3)
#
# WHY: documented Stage-0 discipline is NOT self-enforcing. A real bootstrap
# (HCS MaaS, 2026-06-18) shipped partial v2.1 discipline -- skipped the L.7
# /health, left architecture.md a template, omitted universal ADRs, and left a
# <PROJECT_NAME> placeholder -- all caught only on a deliberate re-audit. This
# gate turns "remember to" into "can't close Stage 0 without."
#
# Run it at the END of Stage 0 (after filling the PROJECT placeholders):
#     make bootstrap-check
# Exit 0 = Stage 0 may close. Exit 1 = blocking gaps printed below.
#
# v3 adds C7: the web/API security baseline gate (V3C-11) -- fails on an obvious
# default-admin password / plaintext-credential pattern in source. The full
# baseline (server-side authz, CORS allowlist, startup config validation,
# encrypt-at-rest, generic errors) lives in docs/security-baseline.md.
#
# NOTE: the UNFILLED starter package intentionally FAILS this gate (it still has
# template placeholders). That is correct -- the starter is a template, not a
# project. The gate is meant to pass only after a project has been bootstrapped.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 2

FAIL=0
WARN=0
say()  { printf '%s\n' "$*"; }
fail() { printf '  [FAIL] %s\n' "$*"; FAIL=$((FAIL+1)); }
warn() { printf '  [warn] %s\n' "$*"; WARN=$((WARN+1)); }
ok()   { printf '  [ ok ] %s\n' "$*"; }

say "== Stage-0 bootstrap-check (Pipeline v3 / FB-1 + V3C-11) =="

# --- C1: no unfilled <PLACEHOLDER> in the must-fill files -------------------
# Scan only files a real project MUST fill. Template files (*.template.*) and the
# design/seed docs (which legitimately mention <PLACEHOLDER> as instructions) are
# excluded by construction (not in this list).
say "[C1] placeholders in must-fill files"
MUST_FILL=("README.md" "pyproject.toml" "src/app/adapter/main.py" \
           "docs/prd.md" "docs/architecture.md" "docs/decisions.md")
# AGENTS.md: only the PROJECT-SPECIFIC section (stop at the UNIVERSAL marker).
ph_hits=0
for f in "${MUST_FILL[@]}"; do
  [ -f "$f" ] || { warn "missing file: $f"; continue; }
  if grep -nE '<[A-Z][A-Z0-9_]+>' "$f" >/dev/null 2>&1; then
    fail "placeholder(s) left in $f: $(grep -oE '<[A-Z][A-Z0-9_]+>' "$f" | sort -u | tr '\n' ' ')"
    ph_hits=$((ph_hits+1))
  fi
done
if [ -f AGENTS.md ]; then
  proj=$(awk '/UNIVERSAL/{exit} {print}' AGENTS.md)
  if printf '%s' "$proj" | grep -qE '<[A-Z][A-Z0-9_]+>'; then
    fail "placeholder(s) left in AGENTS.md PROJECT section"
    ph_hits=$((ph_hits+1))
  fi
fi
[ "$ph_hits" -eq 0 ] && ok "no stray placeholders"

# --- C2: /health is the L.7 contract, not v2.0 {status:ok} ------------------
say "[C2] L.7 version-stamped /health"
MAIN="src/app/adapter/main.py"
if [ -f "$MAIN" ]; then
  if grep -q 'APP_BUILD' "$MAIN" && grep -q '"build"' "$MAIN" && grep -q '"version"' "$MAIN"; then
    ok "/health returns {status, version, build} (L.7)"
  else
    fail "$MAIN /health is not L.7 -- must return {status, version, build} (APP_BUILD env)"
  fi
else
  warn "no $MAIN (skip if this project has no adapter)"
fi

# --- C3: prd / architecture / decisions are filled, not templates -----------
say "[C3] core docs are filled (not still templates)"
for f in docs/prd.md docs/architecture.md docs/decisions.md; do
  [ -f "$f" ] || { fail "missing $f"; continue; }
  if grep -qE '<[A-Z][A-Z0-9_]+>|TEMPLATE|fill this|TODO: replace' "$f"; then
    fail "$f still looks like a template (placeholder / TEMPLATE / 'fill this')"
  else
    ok "$f filled"
  fi
done

# --- C4: universal ADRs D-001..D-005 present --------------------------------
say "[C4] universal ADRs D-001..D-005 present in docs/decisions.md"
if [ -f docs/decisions.md ]; then
  miss=""
  for n in 001 002 003 004 005; do
    grep -qE "D-$n" docs/decisions.md || miss="$miss D-$n"
  done
  if [ -n "$miss" ]; then fail "missing universal ADRs:$miss"; else ok "D-001..D-005 present"; fi
else
  fail "docs/decisions.md missing"
fi

# --- C5: ADR-ID convention (FB-2 / B.6) -------------------------------------
# Process/universal ADRs use P-00x; projects start at D-100 to avoid colliding
# with the reserved universal range D-001..D-099.
say "[C5] ADR-ID convention (projects start at D-100; universal/process = P-00x)"
if [ -f docs/decisions.md ]; then
  # project ADRs in the reserved D-006..D-099 band are a collision smell
  if grep -qE 'D-0(0[6-9]|[1-9][0-9])\b' docs/decisions.md; then
    warn "project ADRs found in reserved D-006..D-099 band -- prefer D-100+ (or reconcile per Stage-0 recipe)"
  else
    ok "no project ADRs in the reserved universal band"
  fi
fi

# --- C6: license review of any wrapped/forked OSS engine (FB-4 / F.10) ------
say "[C6] OSS-engine license review (FB-4)"
if [ -f docs/license-review.md ] && ! grep -qE '<[A-Z][A-Z0-9_]+>|TEMPLATE' docs/license-review.md; then
  ok "docs/license-review.md present and filled"
elif grep -RqiE 'wrap|fork' docs/project-brief.md 2>/dev/null; then
  fail "project wraps/forks an OSS engine but docs/license-review.md is absent (AGPL/GPL/SSPL => wrap-not-fork + legal sign-off)"
else
  warn "no docs/license-review.md -- required only if you wrap/fork an OSS engine (FB-4); confirm N/A"
fi

# --- C7: web/API security baseline -- no default-admin / no plaintext creds --
# V3C-11 (GATE, v3): two ad-hoc projects + one-api re-derived GP's security gates
# the hard way; one-api shipped a literal hardcoded default admin password. This
# is a deliberately simple grep heuristic over source files (not docs/templates):
# fail on an obvious default-admin password or a plaintext-credential pattern.
# Full baseline lives in docs/security-baseline.md.
say "[C7] no default-admin / plaintext-credential pattern (V3C-11)"
SEC_DIRS=""
for d in src app server backend services internal; do
  [ -d "$d" ] && SEC_DIRS="$SEC_DIRS $d"
done
if [ -z "$SEC_DIRS" ]; then
  warn "no source dir (src/app/server/...) to scan -- confirm N/A for this project"
else
  # Heuristic patterns (case-insensitive). Each is a strong default-credential smell:
  #   - a default/admin password assigned a non-empty literal
  #   - DEFAULT_*PASSWORD / ADMIN_PASSWORD = "literal"
  #   - generic password/secret/token assigned an inline string literal in code
  sec_pat='(default[_-]?admin|admin[_-]?pass(word)?|root[_-]?pass(word)?|default[_-]?pass(word)?)[^=:\n]{0,40}[=:][[:space:]]*["'"'"'][^"'"'"']+["'"'"']'
  # v4.2 REPAIR (Increment 12, Security seat). `sec_pat2` was DECLARED here in v3 and never passed
  # to grep — the call below only ever used `-e "$sec_pat"`. So the "generic credential assigned an
  # inline literal" heuristic described in the comment above has NEVER executed, across 8 shipped
  # cuts and in every project that copied this package. Cluster A, exactly (council-telemetry.md
  # §6.1): a control ratified without a fixture proving it fires.
  # Wired now, and SCOPED rather than shipped raw — an 8-char floor, test/fixture paths excluded,
  # and a wider non-secret exclusion list. Measured false-positive rate before shipping:
  # **0 hits across hcs_maas_vib/src (576-test production codebase)**. If this starts crying wolf,
  # that is a V4C-13 bypass row, not a reason to quietly unwire it again.
  sec_pat2='(password|passwd|secret|api[_-]?key|access[_-]?key|token|credential)[[:space:]]*[=:][[:space:]]*["'"'"'][A-Za-z0-9!@#$%^&*_+./=-]{8,}["'"'"']'
  # Exclude obvious non-secrets: env reads, getenv, placeholders, "", empty, "changeme"-style TODO markers are still flagged on purpose.
  sec_hits=$(grep -rEniI --include='*.py' --include='*.js' --include='*.ts' --include='*.go' --include='*.java' --include='*.rb' --include='*.php' \
               -e "$sec_pat" -e "$sec_pat2" $SEC_DIRS 2>/dev/null \
             | grep -viE 'getenv|os\.environ|process\.env|Settings|BaseSettings|Field\(|<[A-Z][A-Z0-9_]+>|\$\{|=[[:space:]]*("")|=[[:space:]]*(null|none|nil)|example|placeholder|dummy|redact' \
             | grep -viE '/(tests?|fixtures?|conftest|mocks?|__tests__)/' || true)
  if [ -n "$sec_hits" ]; then
    fail "possible hardcoded default-admin / plaintext credential (V3C-11). Move to env + hash; see docs/security-baseline.md:"
    printf '%s\n' "$sec_hits" | head -n 5 | sed 's/^/        /'
  else
    ok "no obvious default-admin / plaintext-credential pattern in source"
  fi
fi

# --- verdict ----------------------------------------------------------------
say ""
say "bootstrap-check: $FAIL fail / $WARN warn"
if [ "$FAIL" -gt 0 ]; then
  say "RESULT: BLOCKING -- Stage 0 cannot close. Fix the [FAIL] items above."
  exit 1
fi
say "RESULT: PASS -- Stage 0 gate clear (review any [warn] items)."
exit 0
