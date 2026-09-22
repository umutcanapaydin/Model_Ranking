#!/usr/bin/env python3
"""No local component may push the protected branch, merge, or skip a hook.

WHY. `AGENTS.md` declared "agents NEVER run git" under operating mode A0.5. Shipped alongside it: a
skill that ran `git commit`, and a workflow granting an agent `contents: write`. An external reviewer
found both. **The policy was in prose, the contradictions were in code, and nothing compared them.**

The rule was never "agents cannot use git" -- it is "no commit may be mistaken for the owner's".
Exit 0 clean, 1 findings.
"""
import sys, re, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import is_record

# v6.0. This banned `git commit` and `git push` outright, under a model where agents never ran
# git at all. That model is replaced: the agent now commits on its own branch, pushes THAT branch
# and opens a draft pull request, so a skill saying `git commit` is correct behaviour and banning
# it would ban the flow.
#
# The property the ban protected -- **no commit may be mistaken for the owner's** -- survives, and
# is now carried by the branch, the draft state, the absent AI attribution and
# `test-commit-identity`. What is left for THIS control is the boundary the new model actually
# draws: the things a local component may never do, whatever it says about itself.
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
    # the rule itself -- were all reported as breaches by earlier versions of this check.
    # v6.0. `\bbypass\b` and `\bno-verify\b` were REMOVED from this list, and their presence was
    # the fail-open the Security seat warned about, realised: a control that exempts the exact
    # string it hunts can never catch it. `Run git commit --no-verify` passed this scan cleanly.
    # The comment four lines up already said the fix was "by artifact class, NOT by widening
    # NEGATION" -- and then two hunted strings were added to NEGATION anyway. The file contradicted
    # its own doctrine, which is why the doctrine is the thing to trust here.
    r"\bfor example\b|\bstage only\b|\bDENY\b|\bcatastrophe|"
    r"\bowner (?:performs|makes|reviews and|commits)\b|performs ALL git", re.I)


PROHIBITION = re.compile(r"\bno\b|\bnot\b|\bnever\b|\bbypass\b|\bwithout\b|"
                         r"\bforbid|\bprohibit|\brefuse|=\s*$|:\s*$", re.I)


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    bad = []

    # 1. nothing in the local lane commits or pushes
    # `.claude/commands/` and `scripts/` were unscanned; an auditor planted a commit in each.
    for area in (".claude", "subagent-profiles", ".agents", "scripts", "docs"):
        base = root / area
        if not base.is_dir():
            continue
        for f in base.rglob("*"):
            if not f.is_file() or f.suffix not in {".md", ".sh", ".py", ".json"}:
                continue
            # GPF-004 (v5.1): a reviewer's ATTESTATION -- "no git commit was run", followed by its
            # `git status` evidence -- fired this check twice. The artifact that PROVES compliance
            # read as the breach, which teaches reviewers to stop writing the attestation. The fix is
            # by artifact class, NOT by widening NEGATION: the Security seat measured that word list
            # failing OPEN four ways (a live push --force under a "we never bypass review" heading
            # passes it). Records are exempt; skills, scripts and configs stay fully scanned.
            if is_record(f):
                continue
            # The `checkpoint.sh` exemption stood here until v6.0, naming the one sanctioned
            # commit door. The door is gone -- the agent commits on a branch like anything else --
            # and so is the exemption. A named exemption outliving the thing it exempted is the
            # shape this package measured in its own alias register one increment ago.
            body = f.read_text(encoding="utf-8", errors="replace")
            heading = ""
            for line_no, line in enumerate(body.splitlines(), 1):
                # v4.3.2 (audit S8). `heading` was set by ANY line starting with `#` and never reset,
                # so one comment containing "never" -- or a shebang in a .sh file -- switched the check
                # off for the remainder of the file. An auditor disabled it with a single line reading
                # "# Note: we never bypass review." **A sticky exemption is an off switch.**
                if line.lstrip().startswith("#"):
                    heading = line if re.match(r"^\s*#{1,6}\s", line) else heading
                    continue
                # A line that FORBIDS a git command mentions it too. The first version of this check
                # flagged three profiles for listing `git push --force` in their prohibited-operations
                # section -- it read the ban as the instruction. **A checker that cannot tell a rule
                # from its violation produces noise, and noise is how a real finding gets scrolled past.**
                # Section-aware: `Security-Reviewer.md` lists `git push --force` under a heading
                # reading "Destructive operations (always)" -- the ban is in the heading, the command is
                # in the bullet. Checking the line alone read an audit QUESTION as an instruction.
                if NEGATION.search(line) or NEGATION.search(heading):
                    continue
                if line.rstrip().endswith("?"):
                    continue        # a reviewer profile asking "did anyone do X?" is not doing X
                # v6.0, POSITION-AWARE. The old list was position-blind: any negation word
                # anywhere on the line exempted the whole line, which is how `--no-verify` --
                # itself on the list -- exempted every line that contained it. A prohibition
                # governs what comes AFTER it, not what came before, so the test is whether a
                # negation appears to the LEFT of the match. `no \`--no-verify\`` is a rule;
                # `--no-verify && git push` at the start of a line is not.
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
        # v6.0: the trailer requirement is GONE and inverted. AI attribution is forbidden
        # everywhere now, so demanding a `GP-Agent:` trailer would demand the thing the rule bans.
        # What replaces it: the CI agent must be a machine identity and must open a DRAFT.
        if any(m in body for m in ("Co-Authored-By: Claude", "Generated with [Claude")):
            bad.append("issue-agent.yml writes AI attribution into its commits -- forbidden "
                       "everywhere since v6.0, in commits, PR bodies, issues and comments")
        if "GIT_AUTHOR_NAME" not in body:
            bad.append("issue-agent.yml sets no machine identity -- it would commit as whoever the "
                       "runner's default is")
        if "contents: write" in body and "draft" not in body.lower():
            bad.append("issue-agent.yml has commit rights but never says DRAFT -- an agent that can "
                       "merge its own work is not Layer 2")

    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-git-authority {'FAIL' if bad else 'PASS'}: {len(bad)} violation(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
