#!/usr/bin/env python3
"""No local component may push the protected branch, merge, or skip a hook.

WHY. A git policy written only in prose drifts from the code that runs git: a rule once said
"agents never run git" while a shipped skill ran `git commit` and a workflow granted an agent
`contents: write`. **The policy was in prose, the contradictions were in code, and nothing compared
them.**

The agent commits on its own branch, pushes THAT branch and opens a draft pull request. What no
local component may do, whatever it says about itself: push the protected branch, force-push, skip
a hook, merge, or mark a pull request ready. Exit 0 clean, 1 findings.
"""
import sys, re, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import is_record

# A skill saying `git commit` is correct behaviour: the agent commits on its own branch. The
# property that matters -- **no commit may be mistaken for a human's** -- is carried by the branch,
# the draft state, the absent AI attribution and `test-commit-identity`. What is left for THIS
# control is the boundary: the things a local component may never do, whatever it says about itself.
LOCAL = (
    r"(^|[^a-z])git\s+push[^\n]*\b(origin\s+)?(main|master)\b",   # pushing the protected branch
    r"(^|[^a-z])git\s+push[^\n]*(--force|--force-with-lease|\s-f\b)",
    r"--no-verify",                                                  # a hook skipped is a gate removed
    r"(^|[^a-z])gh\s+pr\s+merge",                                    # the human merges
    r"(^|[^a-z])gh\s+pr\s+ready",                                    # the human marks ready
)
NEGATION = re.compile(
    r"\bnever\b|\bdo not\b|\bdon't\b|\bshall not\b|\bmay not\b|\bmust not\b|\bforbid|"
    r"\bprohibit|\bblocked\b|\bdestructive\b|\bescalate\b|\brefuse|\bwithout owner|"
    # A line that DEFINES the violation is not the violation: `bypass = git commit --no-verify` in a
    # comment, a `DENY always` catastrophe list, and "the OWNER performs all git commits" -- which is
    # the rule itself -- were all once reported as breaches.
    # `bypass` and `no-verify` are deliberately NOT on this list: a control that exempts the exact
    # string it hunts can never catch it (`Run git commit --no-verify` once passed this scan). The
    # fix for over-firing is by ARTIFACT CLASS (records are exempt, below), never by widening
    # NEGATION.
    r"\bfor example\b|\bstage only\b|\bDENY\b|\bcatastrophe|"
    r"\bowner (?:performs|makes|reviews and|commits)\b|performs ALL git", re.I)


PROHIBITION = re.compile(r"\bno\b|\bnot\b|\bnever\b|\bbypass\b|\bwithout\b|"
                         r"\bforbid|\bprohibit|\brefuse|=\s*$|:\s*$", re.I)


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    bad = []

    # 1. no local component crosses the boundary (every skill, command, rule, script and doc)
    for area in (".claude", ".agents", "scripts", "docs"):
        base = root / area
        if not base.is_dir():
            continue
        for f in base.rglob("*"):
            if not f.is_file() or f.suffix not in {".md", ".sh", ".py", ".json"}:
                continue
            # A reviewer's ATTESTATION -- "no git commit was run", followed by its `git status`
            # evidence -- once fired this check: the artefact that PROVES compliance read as the
            # breach, which teaches reviewers to stop writing it. The fix is by artifact class, NOT
            # by widening NEGATION -- a word list fails OPEN (a live push --force under a "we never
            # bypass review" heading passes it). Records are exempt; skills, scripts and configs
            # stay fully scanned.
            if is_record(f):
                continue
            body = f.read_text(encoding="utf-8", errors="replace")
            heading = ""
            for line_no, line in enumerate(body.splitlines(), 1):
                # Only a Markdown HEADING sets `heading`. When any `#` line did, one comment containing
                # "never" -- or a shebang in a .sh file -- switched the check off for the rest of the
                # file ("# Note: we never bypass review."). **A sticky exemption is an off switch.**
                if line.lstrip().startswith("#"):
                    heading = line if re.match(r"^\s*#{1,6}\s", line) else heading
                    continue
                # A line that FORBIDS a git command mentions it too: a checker that reads the ban as
                # the instruction flags every profile's prohibited-operations section. **A checker
                # that cannot tell a rule from its violation produces noise, and noise is how a real
                # finding gets scrolled past.**
                # Section-aware: `Security-Reviewer.md` lists `git push --force` under a heading
                # reading "Destructive operations (always)" -- the ban is in the heading, the command is
                # in the bullet. Checking the line alone read an audit QUESTION as an instruction.
                if NEGATION.search(line) or NEGATION.search(heading):
                    continue
                if line.rstrip().endswith("?"):
                    continue        # a reviewer profile asking "did anyone do X?" is not doing X
                # POSITION-AWARE. A position-blind list lets any negation word anywhere on the line
                # exempt the whole line. A prohibition governs what comes AFTER it, so the test is
                # whether a negation appears to the LEFT of the match. `no \`--no-verify\`` is a
                # rule; `--no-verify && git push` at the start of a line is not.
                for pat in LOCAL:
                    hit = re.search(pat, line)
                    if hit and PROHIBITION.search(line[:hit.start()]):
                        continue
                    if hit:
                        bad.append(f"{f.relative_to(root)}:{line_no} crosses the local boundary, which "
                                   f"the draft-PR model forbids: `{line.strip()[:60]}`")

    # 2. the CI agent is attributable
    wf = root / ".github" / "workflows" / "issue-agent.yml"
    if wf.is_file():
        body = wf.read_text(encoding="utf-8")
        # AI attribution is forbidden everywhere, so the CI agent is attributable by its MACHINE
        # identity (never a trailer) and by opening a DRAFT.
        if any(m in body for m in ("Co-Authored-By: Claude", "Generated with [Claude")):
            bad.append("issue-agent.yml writes AI attribution into its commits -- forbidden "
                       "everywhere, in commits, PR bodies, issues and comments")
        # model_ranking (D-155 clause 2): the owner kept the trailer, so the CI agent owes it too.
        # A trailer is attribution to a MACHINE ROLE, not AI attribution; the two rules coexist.
        if "GP-Agent:" not in body:
            bad.append("issue-agent.yml requires no `GP-Agent:` trailer -- its commits would be "
                       "unattributable agent work (D-155 clause 2, V4C-64)")
        if "GIT_AUTHOR_NAME" not in body:
            bad.append("issue-agent.yml sets no machine identity -- it would commit as whoever the "
                       "runner's default is")
        if "contents: write" in body and "draft" not in body.lower():
            bad.append("issue-agent.yml has commit rights but never says DRAFT -- an agent that can "
                       "merge its own work bypasses the human who merges")

    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-git-authority {'FAIL' if bad else 'PASS'}: {len(bad)} violation(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
