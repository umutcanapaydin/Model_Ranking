#!/usr/bin/env bash
# bootstrap-check.sh -- the executable Stage-0 gate (seed C.11).
#
# WHY: documented Stage-0 discipline is not self-enforcing. A real bootstrap skipped the L.7
# /health, left architecture.md a template, omitted the universal ADRs and left a <PROJECT_NAME>
# placeholder -- all caught only on a deliberate re-audit. This gate turns "remember to" into
# "cannot close Stage 0 without".
#
# Run it at the END of Stage 0, after `/setup-project` has written docs/project-brief.md, the name
# is set in pyproject.toml, and `make install`, `make hooks` and `make labels` have run:
#     make bootstrap-check
# Exit 0 = Stage 0 may close. Exit 1 = blocking gaps printed below.
#
# The UNFILLED starter package FAILS this gate on purpose: it is a template, not a project.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 2

FAIL=0
WARN=0
say()  { printf '%s\n' "$*"; }
fail() { printf '  [FAIL] %s\n' "$*"; FAIL=$((FAIL+1)); }
warn() { printf '  [warn] %s\n' "$*"; WARN=$((WARN+1)); }
ok()   { printf '  [ ok ] %s\n' "$*"; }

PH='<[A-Za-z][A-Za-z0-9 _/|.-]{2,}>'

# Lines of a file that can hold an unfilled field. Code fences and HTML-comment guidance are
# notation, not fields. In a code or config file a `#` line is a comment and is skipped too -- but
# in Markdown a `#` line is a HEADING, and a placeholder in a heading is still unfilled.
# model_ranking (W-015, kept through D-155 and D-161): INLINE code spans are stripped as well --
# `--db <path>` in an error message an operator is told to run, or `<artifact>.refresh.json` naming
# a file pattern, is notation, not an unfilled field.
# Usage: live_lines md|code < file
live_lines() {
  awk -v md="$([ "$1" = md ] && echo 1 || echo 0)" '
    /^```/ { fence = !fence; next }
    fence { next }
    !md && /^[[:space:]]*#/ { next }
    /<!--/ { next }
    { gsub(/`[^`]*`/, "") }                  # inline code spans are notation too (W-015)
    { print }
  '
}
kind() { case "$1" in *.md) echo md ;; *) echo code ;; esac; }

# docs/decisions.md minus the bodies of the shipped UNIVERSAL ADRs D-001..D-007, which a project
# must not edit and which legitimately contain notation such as `<pkg>`.
project_adrs() {
  awk '/^## /{skip=0} /^## D-00[1-7][^0-9]/{skip=1} !skip{print}' "$1"
}

say "== Stage-0 bootstrap-check =="

# --- C1: no unfilled <PLACEHOLDER> in the files a project must fill --------------------------
# Template files (*.template.*) and reference docs that mention <PLACEHOLDER> as instructions are
# not in this list by construction.
say "[C1] placeholders in must-fill files"
ph_hits=0
MUST_FILL=("README.md" "pyproject.toml" "src/app/adapter/main.py" \
           "docs/prd.md" "docs/architecture.md" ".github/CODEOWNERS")
for f in "${MUST_FILL[@]}"; do
  [ -f "$f" ] || { warn "missing file: $f"; continue; }
  hits=$(live_lines "$(kind "$f")" < "$f" | grep -oE "$PH" | sort -u | tr '\n' ' ')
  if [ -n "$hits" ]; then
    fail "placeholder(s) left in $f: $hits"
    ph_hits=$((ph_hits+1))
  fi
done
if [ -f docs/decisions.md ]; then
  ph=$(project_adrs docs/decisions.md | live_lines md | grep -oE "$PH" | sort -u | tr '\n' ' ')
  if [ -n "$ph" ]; then
    fail "placeholder(s) left in docs/decisions.md (project sections): $ph"
    ph_hits=$((ph_hits+1))
  fi
fi
# AGENTS.md: only the PROJECT section, which ends at the UNIVERSAL marker.
if [ -f AGENTS.md ]; then
  if awk '/UNIVERSAL/{exit} {print}' AGENTS.md | grep -qE "$PH"; then
    fail "placeholder(s) left in AGENTS.md PROJECT section"
    ph_hits=$((ph_hits+1))
  fi
fi
[ "$ph_hits" -eq 0 ] && ok "no stray placeholders"

# --- C2: /health is the L.7 contract, not a bare {status:ok} ----------------------------------
# It reads the Python scaffold, so it grades a Python product only. On another stack
# (`.devflow-stack`) the scaffold says nothing about the product, and a pass here would be a claim
# about the wrong tree: it warns until the project binds its own L.7 check.
say "[C2] L.7 version-stamped /health"
MAIN="src/app/adapter/main.py"
STACK=python
if [ -f .devflow-stack ]; then
  STACK=$(tr -d '\r' < .devflow-stack | awk 'NF { print $1; exit }')
  [ -n "$STACK" ] || STACK=python
fi
if [ "$STACK" != python ]; then
  warn "stack '$STACK': this check reads the Python scaffold ($MAIN) only -- bind L.7 for your stack (INSTALL.md)"
elif [ -f "$MAIN" ]; then
  if grep -q 'APP_BUILD' "$MAIN" && grep -q '"build"' "$MAIN" && grep -q '"version"' "$MAIN"; then
    ok "/health returns {status, version, build} (L.7)"
  else
    fail "$MAIN /health is not L.7 -- must return {status, version, build} (APP_BUILD env)"
  fi
else
  warn "no $MAIN (skip if this project has no adapter)"
fi

# --- C3: prd / architecture / decisions are filled, not templates ---------------------------
say "[C3] core docs are filled (not still templates)"
for f in docs/prd.md docs/architecture.md docs/decisions.md; do
  [ -f "$f" ] || { fail "missing $f"; continue; }
  if project_adrs "$f" | live_lines md | grep -qE "$PH|TEMPLATE|fill this|TODO: replace|\bTBD\b"; then
    fail "$f still looks like a template (placeholder / TEMPLATE / 'fill this')"
  else
    ok "$f filled"
  fi
done

# --- C4: the universal ADRs D-001..D-007 are present -----------------------------------------
say "[C4] universal ADRs D-001..D-007 present in docs/decisions.md"
if [ -f docs/decisions.md ]; then
  miss=""
  for n in 001 002 003 004 005 006 007; do
    grep -qE "^#+ *D-$n([^0-9]|$)" docs/decisions.md || miss="$miss D-$n"
  done
  if [ -n "$miss" ]; then fail "missing universal ADRs:$miss"; else ok "D-001..D-007 present"; fi
else
  fail "docs/decisions.md missing"
fi

# --- C5: ADR-ID convention (seed B.6) --------------------------------------------------------
# Process ADRs use P-00x; project ADRs start at D-100, so they never collide with the universal
# D-001..D-007 or the reserved band above them. Only HEADINGS are read: the file's own sentence
# "the D-001..D-099 band is reserved" is the rule, not an instance of it.
say "[C5] ADR-ID convention (projects start at D-100; process ADRs = P-00x)"
if [ -f docs/decisions.md ]; then
  if grep -qE '^#+ *D-0(0[89]|[1-9][0-9])\b' docs/decisions.md; then
    warn "project ADRs found in reserved D-008..D-099 band -- prefer D-100+ (or reconcile per the Stage-0 recipe in docs/decisions.md)"
  else
    ok "no project ADRs in the reserved universal band"
  fi
fi

# --- C6: license review of any wrapped/forked OSS engine (seed F.10) -------------------------
# Only the filled brief can answer this, and a CHECKED box is the answer -- not the presence of the
# words, which the template's own checkbox label contains. With no brief at all, that is the gap.
say "[C6] OSS-engine license review"
if [ -f docs/license-review.md ] && ! grep -qE "$PH|TEMPLATE" docs/license-review.md; then
  ok "docs/license-review.md present and filled"
elif [ ! -f docs/project-brief.md ]; then
  fail "docs/project-brief.md absent -- run /setup-project: it asks the setup questions and writes
       the brief. Until then nobody can tell whether this project wraps an OSS engine, which
       decides whether a license review applies"
elif grep -qiE '^\s*-\s*\[[xX]\].*(wrap|fork)' docs/project-brief.md 2>/dev/null; then
  fail "project wraps/forks an OSS engine but docs/license-review.md is absent (AGPL/GPL/SSPL => wrap-not-fork + legal sign-off)"
else
  warn "no docs/license-review.md -- required only if you wrap/fork an OSS engine (seed F.10); confirm N/A"
fi

# --- C7: web/API security baseline -- no default-admin / no plaintext creds --------------------
# A deliberately simple grep heuristic over source (not docs or templates): fail on an obvious
# default-admin password or a plaintext credential. Full baseline: docs/security-baseline.md.
say "[C7] no default-admin / plaintext-credential pattern"
SEC_DIRS=""
for d in src app server backend services internal; do
  [ -d "$d" ] && SEC_DIRS="$SEC_DIRS $d"
done
if [ -z "$SEC_DIRS" ]; then
  warn "no source dir (src/app/server/...) to scan -- confirm N/A for this project"
else
  # Each pattern is a strong default-credential smell:
  #   - a default/admin/root password assigned a non-empty literal
  #   - a password/secret/token/key assigned an inline literal of 8+ characters
  # The second one was once declared and never passed to grep, so it never ran; it is scoped (an
  # 8-character floor, test and fixture paths excluded) so that it can run without crying wolf.
  sec_pat='(default[_-]?admin|admin[_-]?pass(word)?|root[_-]?pass(word)?|default[_-]?pass(word)?)[^=:\n]{0,40}[=:][[:space:]]*["'"'"'][^"'"'"']+["'"'"']'
  sec_pat2='(password|passwd|secret|api[_-]?key|access[_-]?key|token|credential)[[:space:]]*[=:][[:space:]]*["'"'"'][A-Za-z0-9!@#$%^&*_+./=-]{8,}["'"'"']'
  # Exclude obvious non-secrets: env reads, settings classes, placeholders, empty values.
  sec_hits=$(grep -rEniI --include='*.py' --include='*.js' --include='*.ts' --include='*.go' --include='*.java' --include='*.rb' --include='*.php' \
               -e "$sec_pat" -e "$sec_pat2" $SEC_DIRS 2>/dev/null \
             | grep -viE 'getenv|os\.environ|process\.env|Settings|BaseSettings|Field\(|<[A-Z][A-Z0-9_]+>|\$\{|=[[:space:]]*("")|=[[:space:]]*(null|none|nil)|example|placeholder|dummy|redact' \
             | grep -viE '/(tests?|fixtures?|conftest|mocks?|__tests__)/' || true)
  if [ -n "$sec_hits" ]; then
    fail "possible hardcoded default-admin / plaintext credential. Move to env + hash; see docs/security-baseline.md:"
    printf '%s\n' "$sec_hits" | head -n 5 | sed 's/^/        /'
  else
    ok "no obvious default-admin / plaintext-credential pattern in source"
  fi
fi

# --- C8: every customer-reachable repository is declared --------------------------------------
# A product is not a repository: the measured case was a product split across two trees, the
# pipeline installed in one, the second running ungoverned because nothing ever asked. This checks
# that the DECLARATION exists and is filled. It claims nothing about the other trees, which it
# cannot see.
say "[C8] every customer-reachable repo is declared"
if [ ! -f docs/project-brief.md ]; then
  : # already reported by C6 -- one absent file, one finding
elif ! grep -q '^## 2.1 Repositories' docs/project-brief.md; then
  fail "docs/project-brief.md has no '## 2.1 Repositories' section -- run /setup-project again, or
       copy the section from docs/project-brief.template.md. A product split across trees with only
       one of them governed is the case this rule exists for, and nobody decided it; nobody asked"
else
  repo_rows=$(awk '/^## 2\.1 Repositories/{f=1;next} /^## /{f=0} f' docs/project-brief.md \
              | grep -E '^\|' | grep -vE '^\|[- :|]*\|$' | grep -vE '^\|[[:space:]]*Repo[[:space:]]*\|' || true)
  real_rows=$(printf '%s\n' "$repo_rows" | grep -vE '<[^>]*>' | grep -E '\S' || true)
  if [ -z "$real_rows" ]; then
    fail "docs/project-brief.md 2.1 Repositories has no filled row -- every row is still a
       <placeholder>. A single-repo product declares its one repo; an empty table declares nothing"
  else
    # Every `no` owes a ruling. The third column is the answer, the fourth is the refusal entry;
    # only an empty or dash-only cell is "no ruling" -- a short id such as `R-1` is a ruling.
    unruled=$(printf '%s\n' "$real_rows" | awk -F'|' '{
        g=$4; r=$5; gsub(/[[:space:]]/,"",g);
        if (tolower(g)=="no" && r ~ /^[[:space:]]*(-|—|–)?[[:space:]]*$/) print $0 }' || true)
    if [ -n "$unruled" ]; then
      fail "a repo is declared NOT installed and names no owner ruling in docs/refusals.md.
       Neither installed nor refused is not a decision, it is an omission:"
      printf '%s\n' "$unruled" | head -n 3 | sed 's/^/        /'
    else
      n=$(printf '%s\n' "$real_rows" | grep -cE '\S')
      ok "$n customer-reachable repo(s) declared (this gate reads the DECLARATION only; it makes no claim about those trees)"
    fi
  fi
fi

# --- C9: CORS allow-all TOGETHER WITH credentials ---------------------------------------------
# The CONJUNCTION is the defect; each half alone is legitimate: a public read-only API is
# correctly `*`, and an allowlisted API correctly sends credentials. Together they are what the
# CORS spec refuses -- which is why frameworks REFLECT the request's Origin instead, and a reflected
# origin with credentials lets any site the victim visits read their authenticated responses.
#
# The unit is a WINDOW of +/-6 lines around each `*` (the span of a multi-line
# `add_middleware(...)`), not a file: a file holding a public `*` config with credentials off and
# an allowlisted one with credentials on is correct, and a per-file check accused it. A window that
# also holds a FALSY credentials flag is ambiguous, and ambiguity is a `warn`, never a `fail`.
say "[C9] CORS is not allow-all with credentials"
if [ -z "$SEC_DIRS" ]; then
  warn "no source dir (src/app/server/...) to scan -- confirm N/A for this project"
else
  cors_out=$(find $SEC_DIRS -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.go' \
               -o -name '*.java' -o -name '*.rb' -o -name '*.php' \) 2>/dev/null \
             | grep -viE '/(tests?|fixtures?|conftest|mocks?|__tests__)/' \
             | while read -r f; do awk -v F="$f" '
      {
        L = tolower($0); n = NR; line[n] = $0
        if (L ~ /access-control-allow-origin[^=:]{0,20}[=:][[:space:]]*"?\*/ ||
            L ~ /allow_?origins?[^=]{0,20}[=:][[:space:]]*[\[(]?[[:space:]]*["'"'"']\*["'"'"']/ ||
            L ~ /origin[[:space:]]*:[[:space:]]*(true|"\*"|'"'"'\*'"'"')/) star[n] = 1
        if (L ~ /allow_?credentials["'"'"']?[[:space:]]*[=:][[:space:]]*["'"'"']?(true|1|yes)[^a-z0-9_]?/ ||
            L ~ /access-control-allow-credentials[^=:]{0,20}[=:][[:space:]]*"?true/ ||
            L ~ /credentials["'"'"']?[[:space:]]*:[[:space:]]*["'"'"']?true/) credT[n] = 1
        if (L ~ /allow_?credentials["'"'"']?[[:space:]]*[=:][[:space:]]*["'"'"']?(false|0|no)[^a-z0-9_]?/ ||
            L ~ /credentials["'"'"']?[[:space:]]*:[[:space:]]*["'"'"']?false/) credF[n] = 1
      }
      END {
        for (s in star) {
          hitT = 0; hitF = 0
          for (i = s - 6; i <= s + 6; i++) { if (i in credT) hitT = 1; if (i in credF) hitF = 1 }
          if (hitT && !hitF) printf "FAIL\t%s:%d\t%s\n", F, s, line[s]
          else if (hitT && hitF) printf "WARN\t%s:%d\t%s\n", F, s, line[s]
        }
      }' "$f"; done)
  cors_bad=$(printf '%s\n' "$cors_out" | grep '^FAIL' || true)
  cors_amb=$(printf '%s\n' "$cors_out" | grep '^WARN' || true)
  if [ -n "$cors_bad" ]; then
    fail "CORS allow-all together with credentials. Name the origins; see docs/security-baseline.md:"
    printf '%s\n' "$cors_bad" | cut -f2- | head -n 5 | sed 's/^/        /'
  elif [ -n "$cors_amb" ]; then
    warn "allow-all origins near a credentials flag, with a falsy one in the same window -- two configurations, or one bug? read it:"
    printf '%s\n' "$cors_amb" | cut -f2- | head -n 5 | sed 's/^/        /'
  else
    ok "no allow-all origin configured together with credentials"
  fi
fi

# --- C10: destructive behaviour defaulting ON --------------------------------------------------
# A service that drops and reseeds its schema when a flag it defaults ON is not overridden loses
# production data the first time someone deploys it without the override.
#
# The pattern binds a destructive VERB to a data-scope NOUN, because the verbs alone are everywhere
# in ordinary code -- `reset_index=True`, `drop_duplicates`, `reset_password` -- and a check that
# fires on those gets switched off in a week. `<verb>_on_<boot|start|deploy>` needs no noun: there
# is no innocent reading of `reseed_on_boot`. The ENV-READ form is caught on purpose:
# `os.getenv("SEED_ON_STARTUP", "true")` LOOKS configurable, and the default is what runs when
# nobody sets the variable.
say "[C10] no destructive behaviour defaulting ON"
if [ -z "$SEC_DIRS" ]; then
  warn "no source dir (src/app/server/...) to scan -- confirm N/A for this project"
else
  d_verb='(reset|reseed|re-?create|drop|wipe|purge|truncate|destroy|erase|flush)'
  d_noun='(db|database|schema|tables?|collections?|storage|volume|bucket|migrations?)'
  d_when='on[_-]?(boot|start|startup|launch|deploy)'
  d_wverb='(seed|reset|reseed|wipe|purge|drop|truncate|re-?create|flush)'
  d_true='(true|1|yes|on|enabled)'
  # A destructive flag NAME, in any of the three shapes that carry no innocent reading.
  d_name="([a-z0-9_]*${d_verb}[_-]?${d_noun}[a-z0-9_]*|[a-z0-9_]*${d_noun}[_-]?${d_verb}[a-z0-9_]*|[a-z0-9_]*${d_wverb}[_-]?${d_when}[a-z0-9_]*)"
  dest_lit="${d_name}[[:space:]]*[=:][[:space:]]*[\"']?${d_true}\\b"
  dest_env="(getenv|environ\\.get|env\\.get)\\([[:space:]]*[\"']${d_name}[\"'][[:space:]]*,[[:space:]]*[\"']?${d_true}[\"']?"
  dest_hits=$(grep -rEniI --include='*.py' --include='*.js' --include='*.ts' --include='*.go' --include='*.java' --include='*.rb' --include='*.php' --include='*.yaml' --include='*.yml' \
                -e "$dest_lit" -e "$dest_env" $SEC_DIRS 2>/dev/null \
              | grep -viE '/(tests?|fixtures?|conftest|mocks?|__tests__)/' || true)
  if [ -n "$dest_hits" ]; then
    fail "destructive behaviour defaults ON. Default it OFF, or make it loud and explicit:"
    printf '%s\n' "$dest_hits" | head -n 5 | sed 's/^/        /'
  else
    ok "no reseed/reset/drop defaulting ON in source"
  fi
fi

# --- C11: something gates a push ------------------------------------------------------------
# Two things can: the pre-push hook in this clone (`make hooks`), or the server -- CI that runs,
# on a default branch that is protected. The brief records the second (setup question 7). Where it
# records BOTH as `yes`, a clone without the hook only warns: the server refuses what the clone
# lets through. Anything else -- a `no`, an unfilled answer, no brief at all, which setup records as
# "assume neither" -- leaves the hook as the only gate, and a clone without it FAILS: that is the one
# configuration in which nothing gates a push, and it once passed Stage 0.
say "[C11] something gates a push (make hooks, or CI plus branch protection)"
# brief_answer "<field>": `yes` only when the brief's first line naming the field answers yes.
brief_answer() {
  [ -f docs/project-brief.md ] || { echo no; return; }
  awk -v want="$(printf '%s:' "$1" | tr '[:upper:]' '[:lower:]')" '
    { low = tolower($0); at = index(low, want) }
    at {
      rest = substr(low, at + length(want)); sub(/^[ \t*_`]+/, "", rest)
      print ((rest ~ /^yes([^a-z|\/]|$)/ && rest !~ /^yes[ \t]*[|\/]/) ? "yes" : "no"); found = 1; exit
    }
    END { if (!found) print "no" }
  ' docs/project-brief.md
}
ci=$(brief_answer "GitHub Actions run here")
protected=$(brief_answer "The default branch can be protected")
if [ -f docs/project-brief.md ]; then
  server="docs/project-brief.md records GitHub Actions: $ci, branch protection: $protected"
else
  server="there is no docs/project-brief.md to record GitHub Actions or branch protection"
fi
if ! command -v git >/dev/null 2>&1; then
  hooks="git not installed: cannot read core.hooksPath"
elif ! git rev-parse --git-dir >/dev/null 2>&1; then
  hooks="not a git repository yet, so no pre-push hook"
elif [ "$(git config core.hooksPath 2>/dev/null)" = ".githooks" ]; then
  hooks=""
else
  hooks="core.hooksPath is not .githooks"
fi
if [ -z "$hooks" ]; then
  ok "core.hooksPath = .githooks -- make gate runs before every push"
elif [ "$ci" = yes ] && [ "$protected" = yes ]; then
  warn "$hooks -- run make hooks; meanwhile CI on the protected branch gates a push ($server)"
else
  fail "$hooks, and $server -- nothing gates a push. Run make hooks (an unanswered field counts as no)"
fi

# --- C12: CI still starts (ADVISORY: a [warn] at most, never a fail) -------------------------------
# C11 reads what the brief SAYS about CI; this asks GitHub whether its runs start at all. A billing
# or runner limit fails every job before its first step, and a red check nobody reads looks like
# every other red check. Advisory because it reads a server this tree does not control, and cannot
# stop a push -- `make gate` at pre-push can (scripts/ci_liveness.py; also `make ci-liveness`).
say "[C12] CI still starts a step (advisory)"
LPY=""
for c in python3 python; do "$c" -c 'import sys' >/dev/null 2>&1 && { LPY=$c; break; }; done
if [ ! -f scripts/ci_liveness.py ]; then
  say "  [info] scripts/ci_liveness.py is not in this tree -- nothing asked GitHub"
elif [ -z "$LPY" ]; then
  say "  [info] ci-liveness: CANNOT CHECK -- no working python3 or python on PATH"
else
  live=$("$LPY" scripts/ci_liveness.py 2>&1 | tail -n 1)
  case "$live" in
    "ci-liveness: WARN"*) warn "$live" ;;
    "ci-liveness: ok"*)   ok "$live" ;;
    *)                    say "  [info] ${live:-ci-liveness: printed nothing}" ;;
  esac
fi

# --- verdict -----------------------------------------------------------------------------------
say ""
say "bootstrap-check: $FAIL fail / $WARN warn"
if [ "$FAIL" -gt 0 ]; then
  say "RESULT: BLOCKING -- Stage 0 cannot close. Fix the [FAIL] items above."
  exit 1
fi
say "RESULT: PASS -- Stage 0 gate clear (review any [warn] items)."
exit 0
