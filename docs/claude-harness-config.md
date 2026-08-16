# Claude Code Harness Configuration

> **Important:** Files under `.claude/` and `.mcp.json` cannot be written by Cowork during pipeline generation (security restriction). This document contains the content for those files. After cloning this starter package, **manually create** the following files using the exact content below.

---

## File 1: `.claude/settings.json`

Create this file at the repo root inside a `.claude/` directory. Commit it (it's the team's shared harness config). Personal additions go in `.claude/settings.local.json` which is gitignored.

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git branch:*)",
      "Bash(git show:*)",
      "Bash(ls:*)",
      "Bash(cat:*)",
      "Bash(grep:*)",
      "Bash(find:*)",
      "Bash(make gate:*)",
      "Bash(make test:*)",
      "Bash(make lint:*)",
      "Bash(make typecheck:*)",
      "Bash(make standup:*)",
      "Bash(gh issue list:*)",
      "Bash(gh issue view:*)",
      "Bash(gh pr list:*)",
      "Bash(gh pr view:*)",
      "Bash(gh label list:*)",
      "PowerShell(git status:*)",
      "PowerShell(git diff:*)",
      "PowerShell(git log:*)",
      "PowerShell(git branch:*)",
      "PowerShell(Get-ChildItem:*)",
      "PowerShell(Test-Path:*)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$TOOL_INPUT_FILE_PATH\" | grep -qE '(^|/)\\.env(\\.|$|/)'; then echo 'BLOCKED: writes to .env / *.env* are denied per permission-matrix.md §6 (default-deny secrets). Use environment variables instead.' >&2; exit 1; fi"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "cd \"$CLAUDE_PROJECT_DIR\" && { make gate 2>&1 | tee -a .claude/last-check.log; } && echo 'POST-EDIT GATE: make gate GREEN' || { echo 'POST-EDIT GATE: make gate RED -- fix before next edit (see .claude/last-check.log)' >&2; exit 1; }"
          }
        ]
      }
    ]
  },
  "env": {
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONUNBUFFERED": "1"
  }
}
```

### What this configures

**Permissions (OS-aware allowlist per consortium §10):** Read-only git / gh / file inspection commands don't prompt. Write actions (commit, push, create) remain prompts.

**PreToolUse hook (baseline #1):** Blocks writes to any `.env` / `*.env*` file with a clear error message. Catches accidental secret commit at the model layer before gitleaks fires at commit time.

**PostToolUse hook (baseline #2):** Runs `make gate` after every Write / Edit / MultiEdit. Logs to `.claude/last-check.log`. Exits non-zero (visible failure) when red — the subagent must fix before continuing.

**Promotion rule:** A rule from AGENTS.md or `.agents/rules/practices.md` gets promoted to a hook only after Claude violates it 3+ times in measured sessions (PM lens). Catastrophe-class items (per `permission-matrix.md` §11) can ship as hooks day-1.

---

## File 2: `.mcp.json`

Create this file at the repo root. Commit it (it's the team's shared MCP server config).

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### What this configures

**GitHub MCP server (default per v2.0 consortium):** Gives interactive sessions native access to GitHub issues / PRs / labels without parsing `gh` JSON.

**Token comes from `.env`** (gitignored). Stage 0 admin task: add `GITHUB_TOKEN` to `.env` + schedule 90-day rotation.

**GitLab alternative:**

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gitlab"],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "${GITLAB_TOKEN}",
        "GITLAB_API_URL": "https://gitlab.com/api/v4"
      }
    }
  }
}
```

**Additional MCP servers (Linear / Notion / Slack / Atlassian / etc.) are opt-in per project.** Add only when the team genuinely uses the tool daily. Maintenance cost (auth tokens, breaking changes, server uptime) > ROI otherwise. Quarterly handover harness diet: retire any MCP not actively used in 90 days.

---

## File 3-12: Skill files at `.claude/skills/<name>/SKILL.md`

The 10 starter skills' content is in `docs/claude-skills-content.md` (next document). Create the 10 directories and SKILL.md files manually following that doc.

After all files are created, your repo should have:

```
.claude/
  settings.json
  skills/
    triage-issue/SKILL.md
    fix-issue-prepare/SKILL.md
    fix-issue-implement/SKILL.md
    file-issue/SKILL.md
    test-and-commit/SKILL.md
    repo-review/SKILL.md
    quarterly-handover/SKILL.md
    log-decision/SKILL.md
    retrospect/SKILL.md
    standup/SKILL.md
.mcp.json
```

---

## After manual creation

1. Run `make gate` — must be GREEN.
2. Run any skill once (e.g., `/standup`) to verify the harness loads.
3. Set up `GITHUB_TOKEN` in `.env` and verify `mcp` connects.
4. **Stage only — never commit** (A0.5, and `conformance/test-git-authority.py` enforces it): stage the files, print the commit message, and stop. The owner commits. *This step used to say "Commit:" and contradicted `AGENTS.md` for several versions.*
