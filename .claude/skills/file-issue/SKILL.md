---
name: file-issue
description: Use the moment you find a problem or an improvement outside what you are doing — a failing check, a flaky test, an advisory, drifted docs, a gate that does not fire — or give one up after three attempts. Files it instead of fixing it inline.
---

1. **Search for a duplicate first**, open and closed:
   `gh issue list --state all --search '<key words> in:title,body' --json number,title,state`.
   If one exists, comment on it rather than opening a second — never edit its body or labels.
   Two issues for one problem is how a fix lands twice and a verification lands never.
   Nothing matches → `gh issue create --title '…' --body '…' --label <existing label>`.
   **A requirement filed from `docs/prd.md`** (light mode's intake): the title starts with its REQ-ID
   (`REQ-012: …`), the body is its acceptance bullets — the release Tester proves those — and on an
   empty repository the duplicate search can be skipped.
2. Precise title. A defect is a `bug` with exactly one `severity:*`, by measured impact: exact
   reproduction steps, observed and expected, environment. An improvement you noticed is an
   `enhancement`: what would change and why, no severity. Say where it was found (the wave, the
   review id, or the session). **Found in a review record** → cite it as
   `` `<sha>:docs/reviews/<file>`, <finding> `` — the sha of the commit that wrote that round, so
   `git show <sha>:<path>` shows the finding however the rounds are renamed later (#252). A bare
   path moves: the next round takes the unnumbered name and the earlier one becomes `-round-K.md`.
3. **Only labels that already exist** — see `.agents/rules/issues.md`. A label nobody created is
   a label no skill and no CI rule will ever match.
4. **Do not start fixing it here.** You are in the middle of something else; that is why this
   skill exists.
5. **It is not filed until it is triaged.** When the task you are in ends, run `/triage-issue`
   on it — inside a wave, `/close-wave` step 6 does it for everything the wave filed. An issue
   with no `Triage verdict:` line is one no lane will pick up; `/start-session` lists them.
