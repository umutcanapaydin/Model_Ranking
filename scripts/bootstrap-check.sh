#!/usr/bin/env bash
# bootstrap-check.sh -- executable Stage-0 gate (seed C.11 / FB-1, Pipeline v3)
#
# WHY: documented Stage-0 discipline is NOT self-enforcing. A real bootstrap
# (Project-B, 2026-06-18) shipped partial v2.1 discipline -- skipped the L.7
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
# M11-W3 REPAIR (W-015), kept through the DevFlow v6.0 adoption. DevFlow's GPF-003 repair below makes
# both scans position-aware (fences, comment lines, HTML comments, universal ADR bodies). This project
# also strips INLINE code spans, which GPF-003 does not: `--db <path>` inside an error message an
# operator is told to run, or `<artifact>.refresh.json` naming a file pattern, is notation too.

say "[C1] placeholders in must-fill files"
MUST_FILL=("README.md" "pyproject.toml" "src/app/adapter/main.py" \
           "docs/prd.md" "docs/architecture.md")
# docs/decisions.md checked separately: its D-001..D-007 bodies are SHIPPED UNIVERSAL ADRs the
# project must not edit, and they legitimately contain `<pkg>` notation (GPF-003 finding 3).
# D-155 (adoption review MAJOR-4): the counter is set BEFORE this scan -- it was set after, so a hit
# here aborted the script under `set -u` before C2-C10 ran, and a clean run then zeroed the count.
ph_hits=0
if [ -f docs/decisions.md ]; then
  proj_adrs=$(awk '/^## D-(00[1-7])[^0-9]/{skip=1} /^## (D-(0(0[89]|[1-9][0-9])|1[0-9][0-9])|P-)/{skip=0} !skip{print}' docs/decisions.md)
  ph=$(printf '%s' "$proj_adrs" | awk '/^```/{f=!f;next} f{next} /^[[:space:]]*#/{next} {gsub(/`[^`]*`/, "")} /<[A-Za-z][A-Za-z0-9 _\/|.-]{2,}>/{print}' | grep -oE '<[A-Za-z][A-Za-z0-9 _/|.-]{2,}>' | sort -u | tr '\n' ' ')
  if [ -n "$ph" ]; then fail "placeholder(s) left in docs/decisions.md (project sections): $ph"; ph_hits=$((ph_hits+1)); fi
fi
# AGENTS.md: only the PROJECT-SPECIFIC section (stop at the UNIVERSAL marker).
for f in "${MUST_FILL[@]}"; do
  [ -f "$f" ] || { warn "missing file: $f"; continue; }
# v4.3.2 REPAIR. These patterns required UPPERCASE placeholders, so a PRD and an architecture
# doc full of `<one-paragraph summary>`, `<token format ...>` and dozens of other lowercase
# stubs were both reported `[ok] filled`. The gate that decides whether the core documents are
# real yet was reading for a convention the templates do not use.
# v6.0 REPAIR (GPF-003, HIGH). The v5.0 widening made this gate unpassable by any FINISHED project:
# run differentially against the same completed tree, v4.3 said PASS and v5.0 said BLOCKING with five
# findings -- every one of them notation, not a placeholder: `<pkg>` inside a fenced directory
# diagram, `<tag>` in a commented-out lint rule, and the body of a shipped UNIVERSAL ADR the project
# is forbidden to edit. **A Stage-0 gate passable only by editing do-not-edit files trains people to
# edit governed records.** Position-aware now: a token inside a code fence, on a comment line, or in
# HTML-comment guidance is notation; the same token on a live content line is an unfilled field.
  hits=$(awk '
    /^```/ { fence = !fence; next }
    fence { next }
    /^[[:space:]]*#/ { next }
    /<!--/ { next }
    { gsub(/`[^`]*`/, "") }                                  # inline code spans (W-015)
    /<[A-Za-z][A-Za-z0-9 _\/|.-]{2,}>/ { print FILENAME ":" FNR ": " $0 }
  ' "$f" | grep -oE '<[A-Za-z][A-Za-z0-9 _/|.-]{2,}>' | sort -u | tr '\n' ' ')
  if [ -n "$hits" ]; then
    fail "placeholder(s) left in $f: $hits"
    ph_hits=$((ph_hits+1))
  fi
done
if [ -f AGENTS.md ]; then
  proj=$(awk '/UNIVERSAL/{exit} {print}' AGENTS.md)
  if printf '%s' "$proj" | grep -qE '<[A-Za-z][A-Za-z0-9 _/|.-]{2,}>'; then
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
  # v6.0 (GPF-003): position-aware here too, or C1's repair is undone one check later. Fences,
  # comment lines and the shipped UNIVERSAL ADR bodies (D-001..D-007) are notation, not fields.
  body=$(awk '/^## D-(00[1-7])[^0-9]/{skip=1} /^## (D-(0(0[89]|[1-9][0-9])|1[0-9][0-9])|P-)/{skip=0} !skip{print}' "$f")
  if printf '%s' "$body" | awk '/^```/{c=!c;next} c{next} /^[[:space:]]*#/{next} /<!--/{next} {gsub(/`[^`]*`/, ""); print}' \
       | grep -qE '<[A-Za-z][A-Za-z0-9 _/|.-]{2,}>|TEMPLATE|fill this|TODO: replace|\bTBD\b'; then
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
  # v5.0. This band started at D-006 while the package SHIPS `D-006` and `D-007`, both labelled
  # UNIVERSAL in `docs/decisions.md`, and the orientation file said "D-001..D-007 universal". So every
  # correctly-installed project carried this warning forever, about content the package put there.
  # **A permanent warning on correct work is how warnings become invisible** -- which is the exact
  # doctrine `docs/warnings.ledger.md` exists to enforce, contradicted by a check two files away.
  # Found by installing the package as a user and reading what it said. The band starts at D-008.
  # project ADRs in the reserved D-008..D-099 band are a collision smell
  # ...and only in HEADINGS. Scanning the whole file made the check fire on the file's own
  # explanation of the rule -- `docs/decisions.md` says "the D-001..D-099 band is reserved", so
  # every project has carried this warning since v2.2 because the convention documents itself.
  # **A checker that cannot tell a rule from an instance of it will cry wolf forever.**
    if grep -qE '^#+ *D-0(0[89]|[1-9][0-9])\b' docs/decisions.md; then
    warn "project ADRs found in reserved D-008..D-099 band -- prefer D-100+ (or reconcile per Stage-0 recipe)"
  else
    ok "no project ADRs in the reserved universal band"
  fi
fi

# --- C6: license review of any wrapped/forked OSS engine (FB-4 / F.10) ------
say "[C6] OSS-engine license review (FB-4)"
if [ -f docs/license-review.md ] && ! grep -qE '<[A-Za-z][A-Za-z0-9 _/|.-]{2,}>|TEMPLATE' docs/license-review.md; then
  ok "docs/license-review.md present and filled"
# v4.3.2 REPAIR: this read only `docs/project-brief.md`, but the file the workflow tells you to fill is
# `docs/project-brief.template.md`. With just the template present the grep matched nothing and the OSS
# wrap/fork licence question was skipped in silence -- on a project whose whole architecture is a wrap.
# v5.0 REPAIR, and it is a repair of the previous repair. TB-031's fix widened this to read the
# TEMPLATE as well as the filled brief -- and the template's own checkbox label reads
# "Wraps / forks an OSS engine", so the check fired on EVERY project, unconditionally, telling
# everyone they wrap an OSS engine. Found by running the installation as a user would.
#
# The filled brief is the only thing that can answer this, and a CHECKED box is the answer -- not the
# presence of the words. If the brief has not been filled at all, say THAT: it is the real Stage-0 gap,
# and "you wrap an OSS engine" is a false and confusing way to report a missing file.
elif [ ! -f docs/project-brief.md ]; then
  fail "docs/project-brief.md absent -- copy docs/project-brief.template.md and fill it. Until then
       nobody can tell whether this project wraps an OSS engine, which decides whether FB-4 applies"
elif grep -qiE '^\s*-\s*\[[xX]\].*(wrap|fork)' docs/project-brief.md 2>/dev/null; then
  fail "project wraps/forks an OSS engine but docs/license-review.md is absent (AGPL/GPL/SSPL => wrap-not-fork + legal sign-off)"
else
  warn "no docs/license-review.md -- required only if you wrap/fork an OSS engine (FB-4); confirm N/A"
fi

# --- C8: multi-repo declaration (15-13, ratified Increment 15, built Increment 19) -----------
# A product is not a repository. The measured case: a customer-facing product split across two
# trees, GP installed in one, the second running ungoverned -- not by decision but because nothing
# ever asked. The first harvest refused to guess at it and handed the question back.
#
# SCOPE, stated because this cut is about controls whose declared and actual subjects had drifted:
# this asserts the DECLARATION exists and is filled. It claims NOTHING about the contents of the
# other trees, which it cannot see. That boundary is what the council ratified.
say "[C8] every customer-reachable repo is declared (15-13)"
if [ ! -f docs/project-brief.md ]; then
  : # already reported by the brief check above -- one absent file, one finding
elif ! grep -q '^## 2.1 Repositories' docs/project-brief.md; then
  fail "docs/project-brief.md has no '## 2.1 Repositories' section -- recopy it from
       docs/project-brief.template.md. A product split across trees with only one of them
       governed is the field case this rule exists for, and nobody decided it; nobody asked"
else
  repo_rows=$(awk '/^## 2\.1 Repositories/{f=1;next} /^## /{f=0} f' docs/project-brief.md \
              | grep -E '^\|' | grep -vE '^\|[- :|]*\|$' | grep -vE '^\|[[:space:]]*Repo[[:space:]]*\|' || true)
  real_rows=$(printf '%s\n' "$repo_rows" | grep -vE '<[^>]*>' | grep -E '\S' || true)
  if [ -z "$real_rows" ]; then
    fail "docs/project-brief.md 2.1 Repositories has no filled row -- every row is still a
       <placeholder>. A single-repo product declares its one repo; an empty table declares nothing"
  else
    # Every `no` owes a ruling. The third column is the answer, the fourth is the refusal entry.
    unruled=$(printf '%s\n' "$real_rows" | awk -F'|' '{
        g=$4; r=$5; gsub(/[[:space:]]/,"",g);
        if (tolower(g)=="no" && (r ~ /^[[:space:]]*$/ || r ~ /^[[:space:]]*.?-.?[[:space:]]*$/)) print $0 }' || true)
    if [ -n "$unruled" ]; then
      fail "a repo is declared NOT GP-installed and names no owner ruling in docs/refusals.md.
       Neither installed nor refused is not a decision, it is an omission:"
      printf '%s\n' "$unruled" | head -n 3 | sed 's/^/        /'
    else
      n=$(printf '%s\n' "$real_rows" | grep -cE '\S')
      ok "$n customer-reachable repo(s) declared (this gate reads the DECLARATION only; it makes no claim about those trees)"
    fi
  fi
fi

# --- C7: web/API security baseline -- no default-admin / no plaintext creds --
# V3C-11 (GATE, v3): two ad-hoc projects + Project-C re-derived GP's security gates
# the hard way; Project-C shipped a literal hardcoded default admin password. This
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
  # **0 hits across Project-B/src (576-test production codebase)**. If this starts crying wolf,
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


# --- C9: CORS allow-all TOGETHER WITH credentials (V3C-13/51) ---------------
# The rule has been in `docs/security-baseline.md` and AGENTS.md since v3 -- "CORS
# allowlist (never allow-all + credentials)" -- with nothing that could read a line
# of source. V4C-49 in one sentence: writing a rule does not install it.
#
# The CONJUNCTION is the defect, and each half alone is legitimate: a public
# read-only API is correctly `*`, and an allowlisted API correctly sends
# credentials. Together they are the one combination the CORS spec refuses -- which
# is why frameworks implement it by REFLECTING the request's Origin header instead,
# and a reflected origin with credentials means any site the victim visits can read
# their authenticated responses.
#
# SCOPE, and this is the part the first version got wrong. Asking whether one FILE
# contains both halves fired on a file holding TWO CORS configurations -- a public
# one with `*` and credentials off, and an allowlisted one with credentials on.
# Neither is the defect; the check accused their coexistence. Caught by the
# must-not-fire fixture, not by reading it.
#
# So the unit is a WINDOW of +/-6 lines around each `*`, which is the span of the
# multi-line `add_middleware(...)` form this is really hunting. And an ambiguous
# window -- one holding a FALSY credentials flag as well -- is a `warn`, never a
# `fail`: a check that cannot tell two configurations apart may report what it saw,
# but it may not block on it.
say "[C9] CORS is not allow-all with credentials (V3C-13/51)"
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
    fail "CORS allow-all together with credentials (V3C-13/51). Name the origins; see docs/security-baseline.md:"
    printf '%s\n' "$cors_bad" | cut -f2- | head -n 5 | sed 's/^/        /'
  elif [ -n "$cors_amb" ]; then
    warn "allow-all origins near a credentials flag, with a falsy one in the same window -- two configurations, or one bug? read it:"
    printf '%s\n' "$cors_amb" | cut -f2- | head -n 5 | sed 's/^/        /'
  else
    ok "no allow-all origin configured together with credentials"
  fi
fi

# --- C10: destructive behaviour defaulting ON (V3C-06/53) -------------------
# "Any reseed/reset-on-boot defaults OFF or is loud + explicit" -- also written
# since v3, also with no reader. The failure it prevents is not subtle: a service
# that drops and reseeds its schema when a flag it defaults to ON is not overridden
# loses production data the first time someone deploys it without the override.
#
# The pattern requires a destructive VERB bound to a data-scope NOUN, because the
# verbs alone are everywhere in ordinary code -- `reset_index=True`,
# `drop_duplicates`, `reset_password` -- and a check that fires on those gets
# switched off in a week. `drop_table = True` is caught; `df.reset_index(drop=True)`
# is not. `<verb>_on_<boot|start|deploy>` is caught without a noun, because there is
# no innocent reading of `reseed_on_boot`.
#
# The ENV-READ form is caught on purpose and was missed by the first version:
# `os.getenv("SEED_ON_STARTUP", "true")` is where this actually ships. The literal
# form is what someone writes while developing; the env form with a truthy fallback
# is what survives review, because it LOOKS configurable. The default is what runs
# when nobody sets the variable, and nobody sets the variable.
say "[C10] no destructive behaviour defaulting ON (V3C-06/53)"
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
    fail "destructive behaviour defaults ON (V3C-06/53). Default it OFF, or make it loud and explicit:"
    printf '%s\n' "$dest_hits" | head -n 5 | sed 's/^/        /'
  else
    ok "no reseed/reset/drop defaulting ON in source"
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
