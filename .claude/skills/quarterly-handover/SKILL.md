---
name: quarterly-handover
description: At every 3rd milestone closure (M%3==0), generate docs/handovers/handover_q{N}.txt — a full state dump for a fresh agent. Use ONLY at Stage 4.3 closure when M%3==0.
---

0. **BLOCKING (v3.1, V3C-81):** `docs/EXPERIENCE.md` must contain a dated entry keyed to the latest CLOSED milestone (a token edit does not count — look for the milestone-keyed dated entry). If missing or stale → STOP: no handover until the EXPERIENCE entry is written (`docs/EXPERIENCE.template.md`).
1. Verify current milestone N satisfies N%3==0 (M3, M6, M9, M12, ...). If not, stop — this skill is quarterly only.
2. Read these source files:
   - `docs/process-log.md` (S{N} entries for the last 3 milestones)
   - `docs/decisions.md` (D-IDs added in the last 3 milestones)
   - `.agents/rules/playbook-seeds.md` (seeds activated in the last 3 milestones — look for ★ active markers added)
   - `docs/retrospectives/m{N-2}-, m{N-1}-, m{N}-retrospective.md` (the 3 most recent G.12 retrospects)
   - Previous `docs/handovers/handover_q{N/3-1}.txt` if it exists (for continuity)
   - `docs/EXPERIENCE.md` (the living experience doc — freshness verified in step 0; harvest source)
3. Generate `docs/handovers/handover_q{N/3}.txt` with these sections:
   - Quarter range + date + status
   - Shipped REQ-IDs (this quarter)
   - New ADRs (D-IDs added this quarter)
   - Activated seeds (this quarter)
   - Open risks queued to next quarter (from MINOR findings)
   - Cumulative state: tests, coverage, token spend, AGENTS.md size, active seeds count, ADR count
   - Next-quarter milestone skeleton (M{N+1} to M{N+3})
   - Fresh-agent navigation map (which files to read in what order)
   - Gotchas + inside jokes (anything not in formal docs but useful to know)
4. Sign off with name + date.
5. Commit: `git add docs/handovers/handover_q{N/3}.txt && git commit -m "docs: quarterly handover Q{N/3} (M{N})"`.
6. Tag the commit: `git tag handover-q{N/3}`.
