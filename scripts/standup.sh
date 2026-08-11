#!/usr/bin/env bash
# Seed C.7: project-state dump, LLM-free, fast, cheap.
# Print enough context that any agent (or human) knows "where are we" in 5 seconds.

set -euo pipefail
cd "$(dirname "$0")/.." || exit 1

echo "===== PROJECT STANDUP ====="
echo
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo

echo "----- Latest process-log entry -----"
if [ -f docs/process-log.md ]; then
  awk '/^## S/{c++} c==1' docs/process-log.md | head -25
else
  echo "(no process-log yet)"
fi
echo

echo "----- Open ADRs (status: proposed) -----"
if [ -f docs/decisions.md ]; then
  grep -B1 "Status:.*proposed" docs/decisions.md | head -20 || echo "(none)"
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

echo "----- Latest retrospective -----"
ls -1 docs/retrospectives/ 2>/dev/null | sort -r | head -1 || echo "(no retrospectives yet; M3+ trigger)"
echo

echo "----- Latest quarterly handover -----"
ls -1 docs/handovers/ 2>/dev/null | grep "^handover_q" | sort -r | head -1 || echo "(no quarterly handovers yet; M%3==0 trigger)"
echo

echo "----- AGENTS.md size -----"
if [ -f AGENTS.md ]; then
  lines=$(wc -l < AGENTS.md)
  echo "$lines lines (target <=80, hard cap <=150)"
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
if [ -d .git ]; then
  branch=$(git branch --show-current 2>/dev/null || echo "<not git>")
  echo "Branch: $branch"
  echo "Status:"
  git status -s 2>/dev/null | head -15 || true
  echo
  echo "Last 3 commits:"
  git log --oneline -3 2>/dev/null || echo "(no commits)"
fi
echo

echo "===== END STANDUP ====="
