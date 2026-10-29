#!/usr/bin/env python3
"""Which review does this change need? Computed from the diff and the working mode, never from the
author's judgment.

    python3 scripts/review_need.py [--range A..B] [--at <sha>] [--plan docs/plans/mN-plan.md] [--wave-security]
      (default range: merge-base with the default branch..HEAD; --at reads the brief and the plan
       as of that commit -- how `make wave-check` grades a close by the rules of its own time;
       --wave-security routes heavy mode's security per wave, the rule before v7.1.2, for such a close)

The last line is the answer, and `/close-wave`, `/fix-issue` and `make wave-check` read it:

    review-need: none | code-reviewer | security | code-reviewer+security

The lines above it say why, and the first of them names the working mode the answer was computed
under (`working mode: light -- ...`): in the field the skills said "light runs no Code-Reviewer"
while this script, mode-blind, said `code-reviewer`, and two projects followed each in turn (24
contradictions, DevFlow #16). The mode is the brief's `Working mode:` (`make mode`; unset: heavy),
read as of `--at` when given, so a close is graded by the mode of its own time.

**The brief is read at the range's base, never from the change** (AGENTS.md section 5, base-pinned
policy; #283). Without `--at`, `Working mode:` and `Paths that make a change HIGH:` are read from the
brief at the merge-base of the range's two ends: a change that sets `light`, or deletes the mode line,
or empties the HIGH globs, is judged by the brief it started from. **A range that edits policy** --
changes the answer of a brief policy field (`Working mode:`, `Paths that make a change HIGH:`,
`Deploy commands:`) between the base and the range's end, or touches `scripts/review_need.py`,
`scripts/deploy_gate.py` or `scripts/brief_fields.py` -- needs a security review whatever else it
holds: `security` in light mode, `code-reviewer+security` in heavy mode (heavy's once-per-milestone
rule does not take it). A base git cannot read is `CANNOT RUN` (exit 2), never the defaults.

**Heavy mode runs the Security-Reviewer once per milestone** (the owner's ruling of 2026-10-16, v7.1.2):
on the plan's last wave, over the whole milestone, beside the milestone Tester (`/close-wave`). A wave
or a fix in heavy mode is never routed to security here; its signals are still printed, for the
milestone's review to read. Light mode (v7.2): security per change only on the declared HIGH
paths; the other signals are printed for the release review.

MEASURED, not invented (the 2026-09-28 review of three field repositories, 483 commits, 109 security
findings, 58 pull requests):
  * **A reviewer pays for itself above ~130 product lines.** Below it, a fix's verdict ran to
    ~100 lines for 6-10 changed lines of code, and 3 of 4 such fixes got no product change from it.
    Gate and control code is the exception: the one small fix whose reviewer found a real defect
    was a gate script. So: more than 130 product lines, or any gate code -> a Code-Reviewer.
    **In light mode there is no Code-Reviewer** (`.agents/rules/issues.md`, "Two working modes"); the product
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

import fnmatch
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brief_fields  # noqa: E402

PRODUCT_THRESHOLD = 130
#: The gate code's places: a directory, or one file. GATE_CODE and the policy readers' search are both made from it.
GATE_ROOTS = ("scripts/", "conformance/", ".claude/", ".githooks/", ".github/", "Makefile", "stack.mk")
GATE_CODE = re.compile("^(" + "|".join(re.escape(r) + ("" if r.endswith("/") else "$") for r in GATE_ROOTS) + ")")
#: The modules that read the policy fields, or decide from them (#283): a change to one is a policy edit. Each is
#: also a token below, so a script that names one is a policy reader too (#319).
POLICY_MODULES = ("review_need", "deploy_gate", "brief_fields")
POLICY_SCRIPTS = tuple(f"scripts/{name}.py" for name in POLICY_MODULES)
#: D-221 clause 4 (#418): an exception to a product safety guard is policy too. `data/accepted-cuts.yaml` lets the
#: refresh excuse rows a board loses, so any change to it is a security review in either mode.
#: `tests/unit/test_accepted_cuts.py` holds this equal to the path `app.workflows.refresh` reads.
#: #444 M1: the DevFlow pin decides which bytes the deploy gate exempts from the release verdicts, so a change to it
#: is policy too. `tests/unit/test_deploy_gate_444.py` holds it equal to the path `deploy_gate` reads.
EXCEPTION_FILES = ("data/accepted-cuts.yaml", "docs/devflow-pin.txt")
#: #319 (D-209 clause 5): what names a policy reader -- a policy module, its make target, a plan's
#: `security-globs:` line or a policy field's label. A script under POLICY_READER_DIRS that names one, at either end
#: of the range, is a policy script; in LINE_POLICY_PATHS (the Makefile, the plans) only a changed line naming one
#: is a policy edit, so an unrelated Makefile change is not.
POLICY_TOKENS = (*POLICY_MODULES, "review-need", "deploy-check", "security-globs", *brief_fields.POLICY_FIELDS)
POLICY_PATTERN = re.compile("|".join(re.escape(token) for token in POLICY_TOKENS))
#: The security review's M4: the readers are searched for wherever gate code lives, less the line-read files.
LINE_POLICY_PATHS = ("Makefile", "docs/plans")
POLICY_READER_DIRS = tuple(r.rstrip("/") for r in GATE_ROOTS if r.rstrip("/") not in LINE_POLICY_PATHS)
#: The security review's M1 and M3: a diff no attribute or driver can hide, with paths git does not quote.
PLAIN_DIFF = ("-c", "core.quotePath=false", "diff", "--text", "--no-textconv", "--no-ext-diff", "--no-renames")
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
    """A throwaway root holding `docs/project-brief.md` as it stood at commit `at` (empty if absent there).
    RuntimeError when `at` is not a commit git can read: a policy read from nowhere is not the defaults."""
    return brief_fields.root_at(at)


def range_base(rng: str) -> tuple[str, str]:
    """(the merge-base of the range's two ends, its end) for `A..B` or `A...B`; an empty end is HEAD, as git
    reads it. RuntimeError when the range is not one, or git cannot find the base (#283: fail closed)."""
    sep = "..." if "..." in rng else ".." if ".." in rng else ""
    if not sep:
        raise RuntimeError(f"the range {rng!r} is not A..B, so it has no base to read the brief's policy at")
    start, end = (side or "HEAD" for side in rng.split(sep, 1))
    found = subprocess.run(["git", "merge-base", start, end], capture_output=True, text=True, check=False)
    base = found.stdout.strip()
    if found.returncode != 0 or not base:
        raise RuntimeError(f"no merge-base of {start} and {end}, so the brief's policy fields at the range's "
                           "base cannot be read")
    return base, end


def policy_readers(revs: tuple[str, ...]) -> set[str]:
    """#319: the scripts that name a policy reader at any of `revs`, with the policy modules themselves.
    RuntimeError when git cannot search a commit (fail closed: an unsearched tree has no readers to miss)."""
    found = set(POLICY_SCRIPTS)
    for rev in revs:
        tokens = [arg for token in POLICY_TOKENS for arg in ("-e", token)]
        grep = subprocess.run(["git", "grep", "-z", "-l", "-F", "--text", *tokens, rev, "--", *POLICY_READER_DIRS],
                              capture_output=True, text=True, check=False)
        if grep.returncode not in (0, 1):
            raise RuntimeError(f"git grep cannot search {rev[:12]} for the policy readers: {grep.stderr.strip()}")
        found |= {name.split(":", 1)[1] for name in grep.stdout.split("\0") if ":" in name}
    return {path for path in found if not path.endswith(".md")}


def policy_lines(rng: str) -> list[str]:
    """#319: each file under LINE_POLICY_PATHS whose changed lines name a policy reader, in diff order."""
    hits: list[str] = []
    for path in (p for p in git(*PLAIN_DIFF, "--name-only", "-z", rng, "--", *LINE_POLICY_PATHS).split("\0") if p):
        diff = git(*PLAIN_DIFF, "-U0", rng, "--", path)
        if any(line[:1] in "+-" and not line.startswith(("+++ ", "--- ")) and POLICY_PATTERN.search(line)
               for line in diff.splitlines()):
            hits.append(path)
    return hits


def policy_edits(base_root: Path, end_root: Path, changed: list[str], rng: str = "",
                 revs: tuple[str, ...] = ()) -> list[str]:
    """What in the range edits policy: each brief policy field whose answer differs between the base and
    the end, each policy script the range touches (#319: derived at `revs`), and each Makefile or plan line
    that names a policy reader."""
    before, after = brief_fields.policy(base_root), brief_fields.policy(end_root)
    edits = [f"the brief's `{name}:` ({before[name] or 'unset'} -> {after[name] or 'unset'})"
             for name in brief_fields.POLICY_FIELDS if before[name] != after[name]]
    readers = policy_readers(revs) if revs else set(POLICY_SCRIPTS)
    scripts = sorted(path for path in changed if path in readers)
    lines = [path for path in policy_lines(rng) if path not in scripts] if rng else []
    exceptions = sorted(path for path in changed if path in EXCEPTION_FILES)
    return edits + scripts + lines + exceptions


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


def assess(rng: str, at: str | None = None, plan: str | None = None,
           wave_security: bool = False) -> tuple[str, list[str]]:
    base, end = range_base(rng)
    base_root = brief_root_at(base)
    root: Path = brief_root_at(at) if at else base_root
    mode = brief_fields.mode(root)
    changed = [p for p in git("diff", "--name-only", "--no-renames", "-z", rng).split("\0") if p]
    edits = policy_edits(base_root, brief_root_at(end), changed, rng, (base, end))
    numstat = git(*PLAIN_DIFF, "--numstat", rng)
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
                       ".agents/rules/issues.md, two working modes). Measured anyway, not routed:")
    else:
        reasons.append("working mode: heavy -- a Code-Reviewer above the size threshold or on gate code")
    reasons.append(f"brief read at {at} (--at)" if at else
                   f"brief read at {base[:12]}, the range's merge-base -- not from the change (#283)")
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
    added = [ln[1:] for ln in git(*PLAIN_DIFF, "-U0", rng, "--", ".", ":(exclude)docs", ":(exclude)*.md",
                                  *TEST_PATHSPECS).splitlines()
             if ln.startswith("+") and not ln.startswith("+++")]
    parsers = sorted({m.group(1) for ln in added for m in [UNTRUSTED_PARSER.search(ln)] if m})
    if parsers:
        security.append(f"new parser or fetch of untrusted input: {', '.join(parsers[:5])}")
    reasons += security or ["no security signal"]
    if edits:
        reasons.append(f"policy edit: {', '.join(edits[:4])}{' ...' if len(edits) > 4 else ''} -- a security "
                       f"review whatever the mode{', and a Code-Reviewer' if mode != 'light' else ''} (#283)")
        need = "security" if mode == "light" else "code-reviewer+security"
        return need, reasons
    # Light mode, from v7.2 (the owner's ruling of 2026-10-17): per change only the brief's declared HIGH
    # paths go to the Security-Reviewer; sensitive names and new parsers are read at the release review.
    if security and mode == "light":
        later = [s for s in security if not s.startswith("declared HIGH paths")]
        if later:
            reasons.append("light mode: per change only the brief's declared HIGH paths go to the Security-Reviewer; "
                           "these signals are for the release review (`/going-live`): " + "; ".join(later))
        security = [s for s in security if s.startswith("declared HIGH paths")]
    if security and mode != "light" and not wave_security:
        reasons.append("heavy mode: security runs once per milestone, on the plan's last wave, over the whole "
                       "milestone (`/close-wave`, docs/reviews/m<N>-security.md) -- these signals are for it, "
                       "not routed to this range")
        security = []
    need = ("code-reviewer+security" if need_cr and security else "code-reviewer" if need_cr
            else "security" if security else "none")
    return need, reasons


def main(argv: list[str]) -> int:
    try:
        rng = argv[argv.index("--range") + 1] if "--range" in argv else default_range()
        # A side that is empty or names no commit is not a range: `..HEAD` diffs nothing and would
        # answer `none` for any change (a merge-base that failed upstream of this script). `A...B` is
        # split on its three dots: on two, its right side would read `.B`, and no commit is named that.
        sep = "..." if "..." in rng else ".." if ".." in rng else None
        sides = rng.split(sep, 1) if sep else ["", ""]
        for side in sides:
            if not side.strip() or subprocess.run(["git", "rev-parse", "-q", "--verify", f"{side}^{{commit}}"],
                                                  capture_output=True).returncode != 0:
                raise RuntimeError(f"`{rng}` is not a range of two commits")
        at = argv[argv.index("--at") + 1] if "--at" in argv else None
        plan = argv[argv.index("--plan") + 1] if "--plan" in argv else None
        need, reasons = assess(rng, at, plan, wave_security="--wave-security" in argv)
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
