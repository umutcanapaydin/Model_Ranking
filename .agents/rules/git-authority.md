# Git authority — why it is shaped this way

The rule itself is in `AGENTS.md` §3 and `.agents/rules/issues.md`: **the agent opens drafts; a
human marks them ready and merges.** This file keeps its history, moved out of `AGENTS.md` at the
M16 closure to hold D-003's 150-line cap. Nothing here is a second statement of the rule.

**What this replaced, and why it is written down rather than quietly swapped:** shipped a
flat *"agents NEVER run git"* that two shipped components contradicted; replaced it
with the checkpoint lane, where the agent committed through a dedicated make target (removed at
) and never pushed at
all, and the owner merged `--no-ff` locally at each milestone. That worked and it does not
survive contact with a forge: a review that happens in pull requests needs the branch to be
pushed, and an owner merging locally is an owner reviewing a diff nobody else can see. The
property both versions were protecting is the same one — **no commit may be mistaken for the
owner's** — and it is now carried by the branch, the draft state and the absence of AI
attribution rather than by withholding `push`.

`conformance/test-commit-identity.py` still verifies the range mechanically for what it can see: no AI address or attribution, no stranger, and the `GP-Agent:` trailer on every machine-identity commit. Since D-161 session commits carry the owner's identity, so on those the trailer is a convention: nothing can tell an agent's session commit from the owner's own. A stale statement of
this rule elsewhere in the tree is a finding, not a footnote: the methodology this merges with
found two of them in its own repository, both still declaring a policy replaced eighteen days
earlier.
