# CI traps — for an agent working on issues

Read this when the brief says `The CI issue agent: yes`, or when a draft shows no CI run. Two repository
facts make the CI issue agent (`.github/workflows/issue-agent.yml`) fail quietly. Neither is a defect in the
change, and neither is yours to fix: each is the owner's step, one row in `docs/owner-actions.md` (add it if
it is missing).

1. **Actions may not open a pull request.** Until the owner allows it (Settings → Actions → General →
   "Allow GitHub Actions to create and approve pull requests"), the fix lane's `gh pr create` fails with
   "GitHub Actions is not permitted to create or approve pull requests". The branch is pushed; the draft is
   not. Say so in the issue; do not retry it or open the draft another way. The owner's command:
   `gh api -X PUT repos/{owner}/{repo}/actions/permissions/workflow -F can_approve_pull_request_reviews=true`
2. **The agent's draft starts no CI.** A push or a pull request made with the workflow's `GITHUB_TOKEN`
   starts no other workflow, so `ci.yml` never runs on it and its required checks wait. That is not a red
   check, and there is no CI failure to diagnose. CI starts at the next push made with a person's
   credentials: a session pushing its next commit, or the owner. The lasting fix is the owner's: a GitHub App
   or fine-grained token for the agent's push, a secret and a workflow change (`make ci-diff`).
