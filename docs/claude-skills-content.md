# Claude Code Starter Skills — Content for `.claude/skills/`

> **Important:** Cowork cannot write under `.claude/` directly. After cloning this starter package, create 10 directories under `.claude/skills/` and put the corresponding SKILL.md content from this document into each.
>
> Per consortium decision: 10 starter skills (4 issue management + 2 workflow + 3 lifecycle + 1 utility). Cap at 5 fresh additions per project (PM lens — "hard ceiling on opt-in features active by default: 5").

---

## How to create

For each skill below, create:

```
.claude/skills/<name>/SKILL.md
```

Copy the content between the `--- BEGIN <name> ---` and `--- END <name> ---` markers (excluding the marker lines themselves).

---

## ISSUE MANAGEMENT (4 skills)

### Skill 1: `/triage-issue`

Location: `.claude/skills/triage-issue/SKILL.md`

--- BEGIN triage-issue ---
```markdown
---
name: triage-issue
description: Read a single issue, reproduce it if possible, label by real root cause, and post a diagnosis comment. Use when an issue is opened or needs re-triage. Does NOT write code.
---

1. Read every file in `.agents/rules/` so triage matches this repo's conventions.
2. Read the issue body + comments (host MCP, the `gh`/`glab` CLI, or the JSON passed in by CI).
3. Attempt a minimal reproduction using this repo's run/test commands. Note whether it reproduced.
4. Label by ACTUAL root cause, not the reporter's guess: type (bug/feature/docs), area, severity. Use only labels that already exist in the repo (`gh label list` to verify).
5. Post a concise diagnosis comment: what you found, repro result (yes/no/partial), suspected cause, and whether `/fix-issue-implement` is safe to run automatically (yes/no + why). Cite `file:line` for any code references.
6. Do NOT edit code, open a PR, or close the issue. Triage only.
```
--- END triage-issue ---

### Skill 2: `/fix-issue-prepare`

Location: `.claude/skills/fix-issue-prepare/SKILL.md`

--- BEGIN fix-issue-prepare ---
```markdown
---
name: fix-issue-prepare
description: Create a branch and write a failing test (red) for a triaged issue. Stops here for human/agent review before implementation. Use on issues triage marked safe-to-automate.
---

1. Read `.agents/rules/`. Confirm `/triage-issue` marked this issue safe to automate; if not, stop and ask.
2. Create a branch named `fix/issue-<number>-<slug>`. Never work on `main`. Never force-push.
3. Reproduce the failure with a test FIRST. The test must:
   - Cite the issue number in a comment (e.g., `# covers issue #<n>`).
   - Fail (red) before any implementation.
   - Use the project's test framework (`pytest`, `vitest`, etc.).
4. Run the full test suite. Confirm the new test is red and all OTHER tests are green.
5. Push the branch with the failing test only. Add a one-line comment on the issue: `Branch fix/issue-<n>-<slug> prepared with failing test at <file:line>. Ready for /fix-issue-implement.`
6. STOP. Do NOT implement the fix. That's the next skill's job. This split (Quality lens consortium decision) makes red-test failures distinguishable from implementation failures.
```
--- END fix-issue-prepare ---

### Skill 3: `/fix-issue-implement`

Location: `.claude/skills/fix-issue-implement/SKILL.md`

--- BEGIN fix-issue-implement ---
```markdown
---
name: fix-issue-implement
description: On a prepared branch with a red test, implement the smallest fix to green. Run lint + tests + Stage 2 commit-gate. Push branch + open DRAFT PR linked to the issue. Never merge.
---

1. Verify we're on a `fix/issue-<n>-<slug>` branch (set up by `/fix-issue-prepare`). If not, stop and ask.
2. Verify the prepared failing test exists and is currently red.
3. Implement the SMALLEST possible fix to make the test green:
   - Touch only files relevant to the issue (per scope boundary in permission-matrix.md).
   - Do NOT refactor unrelated code.
   - Do NOT add features beyond the issue's acceptance criteria.
4. Run `make check` (lint + type + test). All must be green.
5. Run `make secrets` (gitleaks scan). Must be green.
6. Run `make deps` (pip-audit). Must be green.
7. The Stage 2 PostToolUse hook will fire `make check` automatically; verify the `.claude/last-check.log` is clean.
8. Push the branch.
9. Open a DRAFT PR with body containing:
   - `Closes #<issue-number>` (auto-link)
   - One-paragraph summary of the fix
   - List of files touched
   - Test names that cover the fix (with `file:line` references — required for PASS verdict per permission-matrix §11)
   - What is NOT covered + risks queued to next milestone
10. Post a one-line comment on the issue: `Draft PR opened: <PR-link>. Human review required.`
11. NEVER merge. NEVER `--no-verify`. NEVER force-push. The agent opens; the human merges. Branch protection on `main` enforces this.
```
--- END fix-issue-implement ---

### Skill 4: `/file-issue`

Location: `.claude/skills/file-issue/SKILL.md`

--- BEGIN file-issue ---
```markdown
---
name: file-issue
description: Open a well-formed issue for a problem you discovered (failing check, flaky test, dep CVE, doc drift). Use during sweeps or when you hit a problem outside the current task's scope.
---

1. Search existing open issues for a duplicate FIRST. Use `gh issue list --search "<topic>"` or the GitHub MCP `issues.search` tool. If a duplicate exists, comment on it instead of opening a new one.
2. Open an issue with:
   - **Title:** precise, ≤60 chars, no leading bug/feature prefix (labels handle that).
   - **Body:** repro steps (numbered), observed/expected, environment (OS / Python version), severity (low / medium / high).
   - **Code references:** `file:line` for any specific locations.
3. Apply existing labels matching the problem area (`gh label list` first; do not invent labels).
4. If the problem is something `/fix-issue-prepare` + `/fix-issue-implement` could safely handle, add the `agent:triage` label and say so in the body. Do NOT start fixing here.
5. If the problem is auth/PII/payment/migration-related, do NOT label `agent:fix` (must stay human-reviewed per permission-matrix §7).
```
--- END file-issue ---

---

## WORKFLOW (2 skills)

### Skill 5: `/test-and-commit`

Location: `.claude/skills/test-and-commit/SKILL.md`

--- BEGIN test-and-commit ---
```markdown
---
name: test-and-commit
description: Run this repo's tests; if they pass, draft a conventional commit and ask before committing. Use after finishing a logical change.
---

1. Run `make check`. If it fails, stop and report the failures — do not stage or commit.
2. If it passes, run `git status` and `git diff --staged`. If nothing is staged, stage tracked changes with `git add -u` (never `git add -A` — risks pulling in secrets or local junk).
3. Look at the last 10 commits with `git log --oneline -10` to infer this repo's commit message style (conventional, sentence-case, prefix tags, etc.).
4. Draft a commit message in that style. Show it to the user. Do NOT commit until the user approves.
5. On approval, create the commit. Never use `--amend` or `--no-verify`.
```
--- END test-and-commit ---

### Skill 6: `/repo-review`

Location: `.claude/skills/repo-review/SKILL.md`

--- BEGIN repo-review ---
```markdown
---
name: repo-review
description: Review the current branch's changes against this repo's documented practices. Loads .agents/rules/ before reviewing. Use before opening a PR.
---

1. Read every file in `.agents/rules/` so the review is grounded in this repo's standards, not generic best practices.
2. Read `subagent-profiles/Code-Reviewer.md` to align with the K.7 fresh-eyes review pattern.
3. Run `git diff <base-branch>...HEAD` to see the full set of changes on this branch.
4. Run the built-in `/review` workflow on the diff, with the rules loaded in Step 1-2 as additional context.
5. In the report, flag specifically:
   - Violations of `.agents/rules/practices.md`
   - Missing tests for new capabilities (with `file:line` evidence of REQ-ID citations per seed E.2)
   - README / CLAUDE.md / AGENTS.md drift
   - K.8 contract drift (run `grep -n` to verify shared symbol names)
   - PASS verdicts WITHOUT `file:line` evidence (automatically BLOCKING per permission-matrix §11)
6. Keep the review under ~30 bullet points. Prioritize correctness > clarity > nits.
7. Output verdict as PASS / MINOR / BLOCKING.
```
--- END repo-review ---

---

## LIFECYCLE (3 skills)

### Skill 7: `/quarterly-handover`

Location: `.claude/skills/quarterly-handover/SKILL.md`

--- BEGIN quarterly-handover ---
```markdown
---
name: quarterly-handover
description: At every 3rd milestone closure (M%3==0), generate docs/handovers/handover_q{N}.txt — a full state dump for a fresh agent. Use ONLY at Stage 4.3 closure when M%3==0.
---

1. Verify current milestone N satisfies N%3==0 (M3, M6, M9, M12, ...). If not, stop — this skill is quarterly only.
2. Read these source files:
   - `docs/process-log.md` (S{N} entries for the last 3 milestones)
   - `docs/decisions.md` (D-IDs added in the last 3 milestones)
   - `.agents/rules/playbook-seeds.md` (seeds activated in the last 3 milestones — look for ★ active markers added)
   - `docs/retrospectives/m{N-2}-, m{N-1}-, m{N}-retrospective.md` (the 3 most recent G.12 retrospects)
   - Previous `docs/handovers/handover_q{N/3-1}.txt` if it exists (for continuity)
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
```
--- END quarterly-handover ---

### Skill 8: `/log-decision`

Location: `.claude/skills/log-decision/SKILL.md`

--- BEGIN log-decision ---
```markdown
---
name: log-decision
description: Append a new ADR to docs/decisions.md in the standard format (D-NNN with Status/Decision/Rationale/Mitigation/Revisit-when). Use whenever a non-trivial design choice is made under uncertainty. Append-only — never edits.
---

1. Read `docs/decisions.md` to find the next available D-ID number.
2. IMPORTANT: IDs are immutable (seed B.5). If D-013 was previously used but the decision was superseded, the next new decision is D-NNN where N = last number + 1. Never reuse IDs. Never edit old entries (B.2 — supersede, don't edit).
3. Ask the user for the decision content if not provided. The minimum required:
   - Topic (one sentence)
   - Decision (what we're choosing)
   - Rationale (why this option won)
4. Construct the ADR-lite entry:
   ```
   ## D-NNN — <Topic>

   **Status:** proposed
   **Decision:** <what we chose>
   **Rationale:** <why>
   **Mitigation if violated:** <what would go wrong>
   **Revisit when:** <trigger to reopen>
   ```
5. Append to `docs/decisions.md` (do NOT insert in the middle; chronological append-only).
6. If this decision supersedes an earlier one (e.g., D-013 → D-NNN):
   - DO NOT edit D-013's body.
   - DO append a "Status: superseded by D-NNN" line to D-013, but only as a NEW line (not in-place edit).
7. Confirm to the user: "ADR D-NNN appended (status proposed). User approval moves it to status accepted."
```
--- END log-decision ---

### Skill 9: `/retrospect`

Location: `.claude/skills/retrospect/SKILL.md`

--- BEGIN retrospect ---
```markdown
---
name: retrospect
description: Walk the G.12 retrospective format at milestone closure (M≥3 only). Categorize every discipline that fired this cycle with PULLED-WEIGHT / PARTIAL / THEORETICAL / TOO-EARLY verdicts. Use ONLY at Stage 4.2 closure when M≥3.
---

1. Verify current milestone N satisfies N≥3. If not, stop — G.12 retrospectives need a minimum sample size to differentiate verdict columns.
2. Read these source files:
   - `docs/plans/m{N}-plan.md` (what disciplines were planned to fire)
   - `docs/reviews/m{N}-*.md` (what disciplines actually caught BLOCKING / MINOR)
   - `docs/process-log.md` S{N} entry
   - Prior `docs/retrospectives/m{N-1}-retrospective.md` (continuity)
3. For every discipline that fired this milestone, assign one of:
   - **PULLED-WEIGHT** — fired AND caught something that would have shipped broken otherwise. Provide a concrete example with `file:line`.
   - **PARTIAL** — fired but the catch was small / cosmetic / redundant with another discipline.
   - **THEORETICAL** — fired but caught nothing this milestone. Don't kill yet; sample size matters.
   - **TOO-EARLY** — discipline is new (first 1-2 milestones); insufficient signal.
4. Write `docs/retrospectives/m{N}-retrospective.md` with format:
   ```
   # M{N} Retrospective — G.12 (Sample N=<N - 2>)

   Date: YYYY-MM-DD
   Milestone: M{N}
   Disciplines evaluated: <count>

   ## PULLED-WEIGHT (the proven ones)
   - <Discipline> (e.g., K.7 fresh-eyes review)
     - Concrete catch: file:line — issue avoided
   ## PARTIAL
   - <Discipline> — explanation
   ## THEORETICAL
   - <Discipline> — explanation
   ## TOO-EARLY
   - <Discipline> — explanation

   ## Disciplines-retired count this milestone
   <number>: <list of disciplines marked for retirement per anti-bloat>

   ## Implications for next milestone (M{N+1})
   - <action 1>
   - <action 2>
   ```
5. Append to `docs/process-log.md` S{N} entry: `Lesson: <retrospective key takeaway>`.
6. The Stage 4 closure check fails if this file is missing for M≥3.
```
--- END retrospect ---

---

## UTILITY (1 skill)

### Skill 10: `/standup`

Location: `.claude/skills/standup/SKILL.md`

--- BEGIN standup ---
```markdown
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
```
--- END standup ---

---

## After all 10 skills are created

1. Verify: `ls .claude/skills/` shows 10 directories.
2. Test invocation: type `/standup` in a Claude Code session — should execute.
3. Run `/log-decision` to add D-006 (your project's first project-specific ADR).
4. Run `make check` once — confirm the PostToolUse hook fires correctly.
5. Commit: `git add -A && git commit -m "chore: pipeline v2.0 starter skills"`.
