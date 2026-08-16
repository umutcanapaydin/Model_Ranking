#!/usr/bin/env python3
"""Every GitHub Action must be pinned to a commit SHA, not a tag.

WHY. A tag is mutable by whoever owns the action's repository. `gitleaks/gitleaks-action@v2` is the
secret scanner -- an attacker who can move that tag runs their code against our tree with our token.
This package ships `anthropics/claude-code-action@v1` a few lines from `ANTHROPIC_API_KEY` and
`contents: write`.

`V4C-44` has required SHA pinning since v4.1. The shipped workflows carried **ten** `# TODO: pin to SHA`
comments instead, one of them annotated "supply-chain critical", and **nothing ever checked** -- while
the repo's own `governance-contract.yml` was correctly pinned, so the rule was demonstrably known and
demonstrably unenforced. Security seat, Increment 14, §10.

Exit 0 clean, 1 findings.
"""
import re, sys, pathlib

USES = re.compile(r"uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([^\s#]+)")
SHA = re.compile(r"^[0-9a-f]{40}$")


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    wfdir = root / ".github" / "workflows"
    if not wfdir.is_dir():
        print("test-action-pins PASS: no workflows"); return 0

    bad, n = [], 0
    for wf in sorted(list(wfdir.glob("*.yml")) + list(wfdir.glob("*.yaml"))):
        for i, line in enumerate(wf.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            m = USES.search(line)
            if not m:
                continue
            n += 1
            repo, ref = m.groups()
            if not SHA.match(ref):
                bad.append(f"{wf.name}:{i} `{repo}@{ref}` is a MUTABLE reference. Whoever owns that "
                           "repository can repoint it, and this workflow would run the new code with "
                           "this repository's token. Run `bash scripts/pin-actions.sh`")

    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-action-pins {'FAIL' if bad else 'PASS'}: {n} action reference(s), {len(bad)} unpinned")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
