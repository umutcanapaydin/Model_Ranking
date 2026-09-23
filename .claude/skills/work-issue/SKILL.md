---
name: work-issue
description: Use to work an issue WITH a human in the loop — triage judged it not safe to automate because it needs design judgment, touches a sensitive area, or its scope is not pinned down. Same branch and PR discipline as fix-issue; the difference is that it plans before coding and pauses at every decision.
---

Same branch, same commit discipline, same draft PR, same gates as `/fix-issue`. The convention
has no carve-out for interactive work. Three differences:

1. **Plan before coding.** Write the ambiguities, the options with their trade-offs, and what is
   in and out of scope. Get direction before you write code.
2. **Pause at every decision triage flagged**, and before anything large or irreversible.
3. **Name the sensitive areas you are about to touch** and confirm before touching them.

A human may choose this lane for something triage would have let run alone. The triage verdict is
a default, not a lock.

Everything else — red test as its own commit, smallest fix, the Tester's fresh-eyes check, gates
green, draft PR, no closing keyword on a bug, no AI attribution, workflows untouched — is
`/fix-issue` unchanged.
