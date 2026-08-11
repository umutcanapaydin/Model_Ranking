---
name: standup
description: LLM-free project state dump. Calls scripts/standup.sh. Use at the start of a session, mid-session sanity check, or before milestone closure.
---

1. Run `bash scripts/standup.sh` directly (do not paraphrase or summarize the script's output; show it raw).
2. The script outputs:
   - Latest process-log entry
   - Open ADRs (status: proposed)
   - Latest roadmap snapshot
   - Latest plan
   - Pending review verdicts
   - AGENTS.md size (target ≤80, ceiling 150)
   - Git state (branch, status, last 3 commits)
3. Add one sentence ANALYSIS at the end (the LLM bit): which item warrants the user's attention most. E.g., "M3 retrospective is missing — Stage 4 closure check will fail; run `/retrospect` first."
4. Do not exceed 60 lines of output total.
