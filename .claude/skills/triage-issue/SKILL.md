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
