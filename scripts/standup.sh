#!/usr/bin/env bash
# Seed C.7: project-state dump, LLM-free, fast, cheap.
# Print enough context that any agent (or human) knows "where are we" in 5 seconds.

set -euo pipefail
cd "$(dirname "$0")/.." || exit 1

echo "===== PROJECT STANDUP ====="
echo
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo

# The log is append-only, so the latest entry is the LAST `## S` block, not the first.
echo "----- Latest process-log entry -----"
if [ -f docs/process-log.md ]; then
  awk '/^## S/{buf=""; on=1} on{buf=buf $0 "\n"} END{printf "%s", buf}' docs/process-log.md | head -25
else
  echo "(no process-log yet)"
fi
echo

# An ADR is `## D-NNN — title`, a blank line, then `**Status:** ...`: print the heading.
echo "----- Open ADRs (status: proposed) -----"
if [ -f docs/decisions.md ]; then
  awk '/^## /{h=$0} /^\*\*Status:\*\*[[:space:]]*proposed/{print h}' docs/decisions.md | head -20
fi
echo

echo "----- Latest roadmap snapshot -----"
ls -1 docs/ 2>/dev/null | grep "^roadmap-" | sort -r | head -3 || echo "(no roadmap snapshots yet)"
echo

echo "----- Latest plan -----"
ls -1 docs/plans/ 2>/dev/null | sort -r | head -3 || echo "(no plans yet)"
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
  grep -oE "PreToolUse|PostToolUse|UserPromptSubmit|Stop|SubagentStop" .claude/settings.json | sort -u | tr '\n' ' '
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
