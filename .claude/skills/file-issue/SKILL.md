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
