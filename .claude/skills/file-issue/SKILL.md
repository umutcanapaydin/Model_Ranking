---
name: file-issue
description: Use the moment you find a problem outside the scope of what you are doing — a failing check, a flaky test, a dependency advisory, drifted documentation, a gate that does not fire, a stale claim. Also for an improvement noticed along the way, and for a problem given up on after three failed attempts. Writes it down, then hands it to /triage-issue, instead of fixing it inline or remembering it. A finding nobody filed is a finding nobody has.
---

1. **Search for a duplicate first**, open and closed:
   `gh issue list --state all --search '<key words> in:title,body' --json number,title,state`.
   If one exists, comment on it rather than opening a second — never edit its body or labels.
   Two issues for one problem is how a fix lands twice and a verification lands never.
   Nothing matches → `gh issue create --title '…' --body '…' --label <existing label>`.
2. Precise title. A defect is a `bug` with exactly one `severity:*`, by measured impact: exact
   reproduction steps, observed and expected, environment. An improvement you noticed is an
   `enhancement`: what would change and why, no severity. Say where it was found (the wave, the
   review id, or the session).
3. **Only labels that already exist** — see `.agents/rules/issues.md`. A label nobody created is
   a label no skill and no CI rule will ever match.
4. If `/fix-issue` could safely handle it, say so in the body.
5. **Do not start fixing it here.** You are in the middle of something else; that is why this
   skill exists.
6. **It is not filed until it is triaged.** When the task you are in ends, run `/triage-issue`
   on it — inside a wave, `/close-wave` step 6 does it for everything the wave filed. An issue
   with no `Triage verdict:` line is one no lane will pick up; `/start-session` lists them.
