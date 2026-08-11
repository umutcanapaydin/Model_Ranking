# Onboarding — Day 1 to Week 1 (Pipeline v2.0)

> New engineer (or agent)? This is your Monday-start, Friday-milestone-bitir rehberi. ≤40 lines.

---

## Day 1 (≤ 2 hours)

1. `git clone` this repo.
2. **Create files Cowork blocked during generation** (see `docs/claude-harness-config.md` + `docs/claude-skills-content.md`):
   - `.claude/settings.json` (permissions + 2 baseline hooks)
   - `.mcp.json` (GitHub or GitLab MCP)
   - `.claude/skills/<name>/SKILL.md` × 10 (starter skills)
3. `ln -s AGENTS.md CLAUDE.md` (so Claude Code finds it natively).
4. Create your own `.agents/rules/environment.md` (rename from `.template`; gitignored).
5. `make install` then `make check` — must be **GREEN** on day 1.
6. Read in order:
   - `AGENTS.md` (house rules ≤80 lines)
   - `permission-matrix.md` (default-deny + BLOCKING taxonomy §11)
   - `docs/decisions.md` (D-001..D-007 universal; project starts at D-008)
   - `.agents/rules/practices.md`
   - `note.txt` (current-turn state)

## Day 2-3
7. Read `docs/prd.md` end-to-end. Note REQ-IDs.
8. Skim `.agents/rules/playbook-seeds.md` — themes A through K + v1.1 ADDENDUM. Know where things live.
9. Run `make standup` — see project state report.
10. Try `/standup` skill in a Claude Code session.

## Day 4-5
11. Read latest plan in `docs/plans/`. Trace one wave: plan → commits → review verdict.
12. Use `/log-decision` skill to add D-008 (your project's first decision).
13. Author your first proposed seed candidate.

## Week 2 onward

You should now:
- Dispatch K.4 waves of subagents per plan.
- Run Stage 3 Per-Wave Review (Code-Reviewer + Tester profiles) at every wave-end; each agent also runs a dev-test loop in the wave (v3, V3C-68). Security-Reviewer runs at milestone closure (Stage 4.0), BLOCKING before deploy — not per-wave.
- Run Stage 4 closure at milestone end (Quality Gate + Capture + Handoff).
- Use `/triage-issue`, `/fix-issue-prepare`, `/fix-issue-implement` for inbound bugs.
- Write `m{N}-plan.md` for next milestone with user approval.

## Anti-patterns to avoid

- Skip `make check` "just this once"
- Edit AGENTS.md UNIVERSAL section without ADR
- Fix one wave's BLOCKING inside another wave (re-dispatch the same wave)
- Dispatch Code-Reviewer for code you wrote yourself (fresh-eyes only)
- `git reset --hard` / `git push --force` / LLM-revert (catastrophe-class per §11)

## Help

- Stuck on a discipline → re-read `.agents/rules/practices.md`
- Stuck on a decision → check `docs/decisions.md`; if not there, use `/log-decision` to propose ADR
- Stuck on a process step → re-read `AGENTS.md` §3 (workflow)
- Stuck on a permission question → check `permission-matrix.md`
