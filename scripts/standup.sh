#!/usr/bin/env bash
# Seed C.7: project-state dump, LLM-free, fast, cheap.
# Print enough context that any agent (or human) knows "where are we" in 5 seconds.

set -euo pipefail
cd "$(dirname "$0")/.." || exit 1

echo "===== PROJECT STANDUP ====="
echo
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo

# v7.3: what waits for the owner comes first -- the rows of docs/owner-actions.md whose Status is not `done`
# (the last cell: a command may hold a `|`), and the Stops rows of an open run file. /start-session reads them here.
echo "----- Needs the owner -----"
needs=""
if [ -f docs/owner-actions.md ]; then
  needs=$(awk -F'|' '/^\|/ { if (++n <= 2) next; s = $(NF-1); gsub(/^[ \t]+|[ \t]+$/, "", s); if (tolower(s) != "done") print }' docs/owner-actions.md || true)
fi
for f in docs/plans/run-*.md; do
  [ -f "$f" ] && grep -qE '^Ended:[[:space:]]*open[[:space:]]*$' "$f" || continue
  stops=$(F="$f" awk '/^## / { on = ($0 ~ /^## Stops/); n = 0; next } on && /^\|/ { if (++n > 2) print ENVIRON["F"] ": stop " $0 }' "$f" || true)
  if [ -n "$stops" ]; then needs="${needs:+$needs
}$stops"; fi
done
printf '%s\n' "${needs:-(nothing)}"
echo

# The log is append-only, so the latest entry is the LAST `## S` block, not the first.
echo "----- Latest process-log entry -----"
if [ -f docs/process-log.md ]; then
  entry=$(awk '/<!--/{c=1} /-->/{c=0; next} c{next} /^## /{buf=""; on=1} on{buf=buf $0 "\n"} END{printf "%s", buf}' docs/process-log.md | head -25)
  printf '%s\n' "${entry:-(no entry yet)}"
else
  echo "(no process-log yet)"
fi
echo

# An ADR (`## D-NNN — title`, or `P-NNN`) is accepted when the commit that added it is on the default branch
# (v7.3, harvest Q5): one the default branch's docs/decisions.md holds is accepted, whatever an old
# `**Status:**` line says; one it does not hold waits for the owner's merge. New ADRs carry no Status line.
# `./` reads the file beside this script, so a project in a subdirectory of its repository compares its own.
echo "----- ADRs awaiting the owner's merge (not on the default branch) -----"
if [ -f docs/decisions.md ]; then
  base=
  for ref in origin/HEAD origin/main origin/master main master; do
    git rev-parse -q --verify "$ref:./docs/decisions.md" >/dev/null 2>&1 && { base=$ref; break; }
  done
  if [ -z "$base" ]; then
    echo "(no default branch holds docs/decisions.md: nothing to compare)"
  else
    MERGED=$(git show "$base:./docs/decisions.md" 2>/dev/null | grep -oE '^## [DP]-[0-9]+' | sed 's/^## //' | tr '\n' ' ' || true) \
      awk 'BEGIN { n = split(ENVIRON["MERGED"], a, " "); for (i = 1; i <= n; i++) m[a[i]] = 1 }
           /^## [DP]-[0-9]+/ { match($0, /[DP]-[0-9]+/); if (!(substr($0, RSTART, RLENGTH) in m)) print }' \
      docs/decisions.md | head -20
  fi
fi
echo

echo "----- Latest roadmap snapshot -----"
ls -1 docs/ 2>/dev/null | grep "^roadmap-" | sort -r | head -3 || echo "(no roadmap snapshots yet)"
echo

echo "----- Latest plan -----"
# By milestone number, so m10 sorts after m9; wave closes and run files are not plans.
ls -1 docs/plans/ 2>/dev/null | grep -E '^m[0-9]+-plan\.md$' | sed 's/^m\([0-9]*\)-/\1 &/' | sort -rn | cut -d' ' -f2 | head -3 | grep . || echo "(no milestone plans yet; light mode has none)"
echo

echo "----- Pending review verdicts -----"
ls -1 docs/reviews/ 2>/dev/null | tail -5 || echo "(no reviews yet)"
echo

# The cap is read from AGENTS.md itself, which states it; a copy here would drift from it.
echo "----- AGENTS.md size -----"
if [ -f AGENTS.md ]; then
  lines=$(wc -l < AGENTS.md | tr -d ' ')
  cap=$(grep -oE '≤ *[0-9]+ *hard cap' AGENTS.md | grep -oE '[0-9]+' | head -1 || true)
  echo "$lines lines (hard cap: ${cap:-not stated})"
fi
echo

echo "----- Active skills (.claude/skills/) -----"
ls -1 .claude/skills/ 2>/dev/null | wc -l | awk '{print $1, "skills"}'
echo

echo "----- Active hooks (.claude/settings.json) -----"
if [ -f .claude/settings.json ]; then
  py=$(command -v python3 || command -v python || true)
  if [ -n "$py" ]; then
    "$py" -c 'import json; print(" ".join(json.load(open(".claude/settings.json")).get("hooks", {})))' 2>/dev/null \
      || echo "(settings.json unreadable)"
  else
    echo "(no python to read settings.json)"
  fi
  echo
fi
echo

echo "----- Git state -----"
if ! command -v git >/dev/null 2>&1; then
  echo "git not installed: cannot read the git state"
elif git rev-parse --git-dir >/dev/null 2>&1; then
  branch=$(git branch --show-current 2>/dev/null || echo "<detached>")
  echo "Branch: $branch"
  echo "Status:"
  git status -s 2>/dev/null | head -15 || true
  echo
  echo "Last 3 commits:"
  git log --oneline -3 2>/dev/null || echo "(no commits)"
else
  echo "(not a git repository)"
fi
echo

echo "===== END STANDUP ====="
