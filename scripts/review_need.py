#!/usr/bin/env python3
"""Which review does this change need? Computed from the diff and the working mode, never from the
author's judgment.

    python3 scripts/review_need.py [--range A..B] [--at <sha>] [--plan docs/plans/mN-plan.md]
      (default range: merge-base with the default branch..HEAD; --at reads the brief and the plan
       as of that commit -- how `make wave-check` grades a close by the rules of its own time)

The last line is the answer, and `/close-wave`, `/fix-issue` and `make wave-check` read it:

    review-need: none | code-reviewer | security | code-reviewer+security

The lines above it say why, and the first of them names the working mode the answer was computed
under (`working mode: light -- ...`): in the field the skills said "light runs no Code-Reviewer"
while this script, mode-blind, said `code-reviewer`, and two projects followed each in turn (24
contradictions, DevFlow #16). The mode is the brief's `Working mode:` (`make mode`; unset: heavy),
read as of `--at` when given, so a close is graded by the mode of its own time.

MEASURED, not invented (the 2026-09-28 review of three field repositories, 483 commits, 109 security
findings, 58 pull requests):
  * **A reviewer pays for itself above ~130 product lines.** Below it, a fix's verdict ran to
    ~100 lines for 6-10 changed lines of code, and 3 of 4 such fixes got no product change from it.
    Gate and control code is the exception: the one small fix whose reviewer found a real defect
    was a gate script. So: more than 130 product lines, or any gate code -> a Code-Reviewer.
    **In light mode there is no Code-Reviewer** (AGENTS.md: light runs security only); the product
    lines and the gate paths are still printed, so the owner can see what light mode is not reviewing.
  * **Security follows three signals together**, which matched 56 of 62 real security findings:
    the paths the owner declared HIGH (the brief's `Paths that make a change HIGH:` and a plan's
    `security-globs:` line), sensitive path names (auth, session, token, crypto, secret, migration,
    deploy, payment ...), and a NEW parser of untrusted input -- the largest class of real findings
    in the field (hostile archives, oversized parquet pages, malformed JSON; in Go, `json.Unmarshal`,
    `json.NewDecoder(` and `.Decode(`). PII words alone fired on 15 of 19 pull requests in one
    project and missed 4 of 7 in another; they are not a signal.
  * **Test files are not a security signal on their own.** A test under a HIGH glob, or named
    `test_auth.py`, reads fixtures the test wrote; a range that touches only tests on those paths
    was routed to security in the field for no product change. Such hits are printed as
    `test-only` and do not count. The same test-path set already kept test parsers out of the
    parser signal.
  * **The agent's own judgment is not a trigger**: in the field agents skipped security passes the
    rules asked for, and every escalation to HIGH came from a reviewer applying the globs.

**A branch stacked on another branch.** The default range starts at the merge-base with the default
branch, so a branch cut from `wave/m3-w2` is measured together with everything `wave/m3-w2` added --
in the field that reported the lower branch's "gate code changed" for six re-runs. Pass the base
yourself: `make review-need RANGE=$(git merge-base wave/m3-w2 HEAD)..HEAD` (or the lower branch's
tip) measures only this branch's own commits. The `range:` line prints what was measured.

Product lines are code and tests: records (`docs/`, Markdown) do not count. Exit 0 with an answer;
2 when the range cannot be read -- a review decision with no diff behind it decides nothing.
"""
from __future__ import annotations

import atexit
import fnmatch
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brief_fields  # noqa: E402

PRODUCT_THRESHOLD = 130
GATE_CODE = re.compile(r"^(scripts/|conformance/|\.claude/|\.githooks/|\.github/|Makefile$|stack\.mk$)")
RECORDS = re.compile(r"^docs/|\.md$")
SENSITIVE_PATH = re.compile(
    r"(^|[/_.-])(auth\w*|login|logout|session|token|oauth|jwt|crypto\w*|cipher|secret\w*|credential\w*|"
    r"password|keychain|permission\w*|acl|migrat\w*|deploy\w*|payment\w*|billing|invoice)([/_.-]|$)", re.I)
UNTRUSTED_PARSER = re.compile(
    r"\b(json\.loads?|yaml\.(?:safe_)?load|csv\.(?:reader|DictReader)|read_csv|read_parquet|ParquetFile|"
    r"pyarrow|zipfile\.|tarfile\.|ElementTree|lxml|xml\.etree|pickle\.loads?|marshal\.loads?|"
    r"JSONDecoder|PropertyListDecoder|XMLParser|json\.Unmarshal|xml\.Unmarshal|json\.NewDecoder\(|"
    r"\.Decode\(|gzip\.open|urllib\.request|requests\.(?:get|post)|httpx\.|URLSession|fetch\()")
# The test-path set, ONE definition for the three security signals. As git pathspecs for the parser
# scan (`*` crosses `/`, so each pair covers the top level and any depth) and as a path test here.
TEST_PATHSPECS = [":(exclude)tests/*", ":(exclude)*/tests/*", ":(exclude)test_*", ":(exclude)*/test_*",
                  ":(exclude)*_test.*", ":(exclude)*Tests/*"]
TEST_PATH = re.compile(r"(^|/)(tests/|test_[^/]*$|[^/]*_test\.[^/]+$|[^/]*Tests/)")


def is_test_path(path: str) -> bool:
    return bool(TEST_PATH.search(path))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def default_range() -> str:
    for ref in ("origin/HEAD", "origin/main", "origin/master", "main", "master"):
        try:
            base = git("merge-base", ref, "HEAD").strip()
            if base:
                return f"{base}..HEAD"
        except (OSError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("no default branch to measure against -- pass --range A..B")


def brief_root_at(at: str) -> Path:
    """A throwaway root holding `docs/project-brief.md` as it stood at commit `at` (empty if absent)."""
    r = subprocess.run(["git", "show", f"{at}:docs/project-brief.md"], capture_output=True, text=True)
    tmp = Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, tmp, True)
    (tmp / "docs").mkdir()
    (tmp / "docs" / "project-brief.md").write_text(r.stdout if r.returncode == 0 else "", encoding="utf-8")
    return tmp


def declared_globs(root: Path | str, at: str | None = None, plan: str | None = None) -> list[str]:
    """The owner's HIGH paths: the brief's line (read from `root`), plus the plan's `security-globs:`.

    With `at`, the plan is read as it stood at that commit, and `plan` names the milestone's own
    plan: a wave close is graded by the rules of its own time, never by a later plan's globs --
    a check that turns an old record red whenever a new plan lands grades history by today."""
    globs = brief_fields.listing("Paths that make a change HIGH", root)
    if at:
        r = subprocess.run(["git", "show", f"{at}:{plan}"], capture_output=True, text=True) if plan else None
        plan_text = r.stdout if r is not None and r.returncode == 0 else ""
    else:
        plans = sorted(Path("docs/plans").glob("m*-plan.md"), key=lambda p: [int(x) for x in re.findall(r"\d+", p.name)] or [0])
        chosen = Path(plan) if plan else (plans[-1] if plans else None)
        plan_text = chosen.read_text(encoding="utf-8", errors="replace") if chosen and chosen.is_file() else ""
    m = re.search(r"^\s*security-globs:\s*(.+)$", plan_text, re.M | re.I)
    if m and m.group(1).strip().lower() not in ("none", "-"):
        globs += [g.strip().strip("`") for g in m.group(1).split(",") if g.strip()]
    return globs


def assess(rng: str, at: str | None = None, plan: str | None = None) -> tuple[str, list[str]]:
    root: Path | str = brief_root_at(at) if at else "."
    mode = brief_fields.mode(root)
    numstat = git("diff", "--numstat", rng)
    product = 0
    gate: list[str] = []
    paths: list[str] = []
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add, rem, path = parts
        paths.append(path)
        if GATE_CODE.search(path):
            gate.append(path)
        elif not RECORDS.search(path) and add != "-":
            product += int(add) + int(rem)
    reasons: list[str] = []
    if mode == "light":
        reasons.append("working mode: light -- no Code-Reviewer in light mode (security only; "
                       "AGENTS.md, two working modes). Measured anyway, not routed:")
    else:
        reasons.append("working mode: heavy -- a Code-Reviewer above the size threshold or on gate code")
    reasons.append(f"product lines changed: {product} (a Code-Reviewer above {PRODUCT_THRESHOLD})")
    need_cr = (product > PRODUCT_THRESHOLD or bool(gate)) and mode != "light"
    if gate:
        reasons.append(f"gate or control code changed: {', '.join(gate[:4])}{' ...' if len(gate) > 4 else ''}")
    security: list[str] = []
    globs = declared_globs(root, at, plan)
    hit = [p for p in paths if any(fnmatch.fnmatch(p, g) for g in globs)]
    test_only = [p for p in hit if is_test_path(p)]
    hit = [p for p in hit if not is_test_path(p)]
    if hit:
        security.append(f"declared HIGH paths: {', '.join(hit[:4])}")
    if test_only:
        reasons.append(f"test-only files under declared HIGH paths (not a signal on their own): "
                       f"{', '.join(test_only[:4])}")
    hit = [p for p in paths if SENSITIVE_PATH.search(p) and not RECORDS.search(p)]
    test_only = [p for p in hit if is_test_path(p)]
    hit = [p for p in hit if not is_test_path(p)]
    if hit:
        security.append(f"sensitive path names: {', '.join(hit[:4])}")
    if test_only:
        reasons.append(f"test-only files with sensitive names (not a signal on their own): "
                       f"{', '.join(test_only[:4])}")
    # A parser in a TEST reads fixtures the test wrote; the signal is product code taking input.
    added = [ln[1:] for ln in git("diff", "-U0", rng, "--", ".", ":(exclude)docs", ":(exclude)*.md",
                                  *TEST_PATHSPECS).splitlines()
             if ln.startswith("+") and not ln.startswith("+++")]
    parsers = sorted({m.group(1) for ln in added for m in [UNTRUSTED_PARSER.search(ln)] if m})
    if parsers:
        security.append(f"new parser or fetch of untrusted input: {', '.join(parsers[:5])}")
    reasons += security or ["no security signal"]
    need = ("code-reviewer+security" if need_cr and security else "code-reviewer" if need_cr
            else "security" if security else "none")
    return need, reasons


def main(argv: list[str]) -> int:
    try:
        rng = argv[argv.index("--range") + 1] if "--range" in argv else default_range()
        at = argv[argv.index("--at") + 1] if "--at" in argv else None
        plan = argv[argv.index("--plan") + 1] if "--plan" in argv else None
        need, reasons = assess(rng, at, plan)
    except (OSError, subprocess.CalledProcessError, RuntimeError, IndexError) as e:
        print(f"review-need CANNOT RUN: {e} -- a review decision with no diff behind it decides nothing")
        return 2
    print(f"range: {rng}")
    for r in reasons:
        print(f"  {r}")
    print(f"review-need: {need}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
