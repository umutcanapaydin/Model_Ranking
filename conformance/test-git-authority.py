#!/usr/bin/env python3
"""No local-lane component may commit; the CI agent must be attributable.

WHY. `AGENTS.md` declared "agents NEVER run git" under operating mode A0.5. Shipped alongside it: a
skill that ran `git commit`, and a workflow granting an agent `contents: write`. An external reviewer
found both. **The policy was in prose, the contradictions were in code, and nothing compared them.**

The rule was never "agents cannot use git" -- it is "no commit may be mistaken for the owner's".
Exit 0 clean, 1 findings.
"""
import sys, re, pathlib, json

LOCAL = ("(^|[^a-z])git\\s+commit", "(^|[^a-z])git\\s+push")
NEGATION = re.compile(
    r"\bnever\b|\bdo not\b|\bdon't\b|\bshall not\b|\bmay not\b|\bmust not\b|\bforbid|"
    r"\bprohibit|\bblocked\b|\bdestructive\b|\bescalate\b|\brefuse|\bwithout owner|"
    # A line that DEFINES the violation is not the violation: `bypass = git commit --no-verify` in a
    # comment, a `DENY always` catastrophe list, and "the OWNER performs all git commits" -- which is
    # the rule itself -- were all reported as breaches by earlier versions of this check.
    r"\bbypass\b|\bno-verify\b|\bfor example\b|\bstage only\b|\bDENY\b|\bcatastrophe|"
    r"\bowner (?:performs|makes|reviews and|commits)\b|performs ALL git", re.I)


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
                for pat in LOCAL:
                    if re.search(pat, line):
                        bad.append(f"{f.relative_to(root)}:{line_no} runs git in the LOCAL lane, which "
                                   f"A0.5 forbids: `{line.strip()[:60]}`")

    # 2. the CI agent is attributable
    wf = root / ".github" / "workflows" / "issue-agent.yml"
    if wf.is_file():
        body = wf.read_text(encoding="utf-8")
        if "GP-Agent:" not in body:
            bad.append("issue-agent.yml requires no `GP-Agent:` trailer -- its commits would be "
                       "indistinguishable from the owner's, which already happened once in the field")
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
