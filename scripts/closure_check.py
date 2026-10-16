#!/usr/bin/env python3
"""Is this file actually a FILLED closure report?

The closure report `docs/closure-report-m{N}.md` is written only when the owner turns the milestone
Quality Gate on (AGENTS.md §6, Stage 4.1; `docs/closure-checklist.md` §B.1). When it exists it is
the owner's review pack for the milestone, and `make closes` grades it inside `make check`: a pack
that was generated and never filled would otherwise pass as a milestone that closed.

WRITTEN AGAINST THE TEMPLATE, not against an idea of one: every rule below is read off
`docs/closure-report.template.md`, the file the Makefile tells you to copy. (`wave_check.py` shows
why: its first version accepted `README.md`, its second rejected every row of correct work.)

WHAT IT REFUSES, and each one is a real way a closure pack goes hollow:
  * a filename that is not `closure-report-m{N}.md` -- a gate that reads whatever it is handed
  * no `record_type: closure` frontmatter -- then `check_records.py` cannot see it at all (a report
    graded by today's rules only: history is decided before it)
  * a frontmatter `id` that differs from the filename -- two milestones' packs sharing an id
  * a missing section. §1 is what shipped, §1a is per wave, §1b is what was decided on the owner's
    behalf, §3 is the mechanical telemetry, §5 is the ledgers. A pack missing §1b hides the
    judgment calls, which is that section's whole reason for existing.
  * a §1 criterion with no citing test `file:line`, or whose status is not ✅ -- the Quality Gate
    is "every criterion has a citing test, and a milestone with a failing criterion does not close"
  * a placeholder left anywhere -- `<criterion>`, `<run id>`, `<initials/date>`
  * an empty cell in a table that claims evidence
  * §6 empty. Every other section is ASSEMBLED from referents; §6 is the one section a human must
    write, and it is the comprehension-debt countermeasure.
  * more than 150 lines. The template states a hard cap of two pages; a pack too long to read
    defeats the review it exists to enable.
  * from `v6.7`, a §1 citation `file:line` whose file does not exist here, or is shorter than the
    line it names -- a Quality Gate that accepts `tests/does_not_exist.py:4242` checks the form of
    a citation, not the test it claims
  * from `v7.1`, no milestone Tester verdict beside the report -- IN BOTH WORKING MODES (the owner's
    ruling of 2026-10-13 on DevFlow #16: in the field a light-mode release went out with no
    fault-injection review at all). The file is read from `<report dir>/reviews/`, so for
    `docs/closure-report-m{N}.md` it is `docs/reviews/`. Heavy mode: `m{N}-tester.md`, the verdict
    the plan's last wave carried. Light mode: the close is the one before a release, on everything
    merged since the Tester's last verdict, and the file is `release-tester.md` with a
    `**Reviewed head:** <sha>` line -- graded by the deploy gate's currency rule (`scripts/deploy_gate.py`):
    no file other than a record may differ from that head in the working tree, committed or not.
    Either file must carry `## Verdict` PASS or MINOR and `**Independent:** yes`. The mode is the
    brief's `Working mode:` (`make mode`; unset: heavy), and the output names it.
  * from `v7.1.2`, in heavy mode, no milestone Security-Reviewer verdict `m{N}-security.md` beside the
    report, PASS or MINOR and `**Independent:** yes`: heavy mode runs security once per milestone, on
    the plan's last wave (the owner's ruling of 2026-10-16).

GRADED BY THE VERSION THE REPORT DECLARES, like `wave_check.py`: a report is append-only evidence.
This check first shipped in `v6.0`; a report that declares an earlier version, or none, is history
and is held only to its filename and its id. Until v6.7 every report was graded by today's
template, and a field project whose fifteen older reports could never pass took `closes` out of
`make check` to get green again (field report, 2026-09-23). Until v7.1.1 the front-matter rule ran
before the version was read, so a report written before closure front matter existed
(`record_type: ratification`) stayed red as history and `closes` stayed out (model_ranking, twelve
reports): history is decided first.

Exit: 0 pass · 1 fail · 2 usage.
"""
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import brief_fields  # noqa: E402

NAME_RE = re.compile(r"^closure-report-m\d+\.md$")
# The deploy gate's notion of a record: everything else is code, and code changed after the reviewed
# head means the Tester did not see what ships (`scripts/deploy_gate.py`, same rule).
# What counts as code after a verdict's reviewed head is decided in ONE place, `deploy_gate.is_deploy_record`
# (`.claude/`, `.githooks/`, `scripts/`, `conformance/`, `.github/` and the Makefile are code whatever
# their extension; `docs/` and other `.md` are records). A second copy here would drift.
from deploy_gate import is_deploy_record  # noqa: E402
PLACEHOLDER = re.compile(r"<[^<>\n]{3,}>|\bTBD\b|\bTODO\b|\bFIXME\b")
SECTIONS = [
    (r"^##\s*1\.\s", "§1 What shipped -- the criteria this milestone claims"),
    (r"^##\s*1a\.\s", "§1a Per-wave table -- one row per wave, each cell citing committed evidence"),
    (r"^##\s*1b\.\s", "§1b Decisions made on the owner's behalf -- the judgment calls"),
    (r"^##\s*2\.\s", "§2 Git record"),
    (r"^##\s*3\.\s", "§3 Trust telemetry -- computed, not asserted"),
    (r"^##\s*4\.\s", "§4 Security & invariants -- the invariants table and ⛔-zone touches "
                     "(the release security review is Stage 5.1, not a milestone)"),
    (r"^##\s*5\.\s", "§5 Ledgers -- nothing silent"),
    (r"^##\s*6\.\s", "§6 Architecture delta -- the one section a human writes"),
]
LINE_CAP = 150


def code_changed_since(head: str) -> list[str] | None:
    """Files that are not records and differ from `head` in the WORKING TREE (committed, uncommitted
    or untracked) -- the deploy gate's currency rule. None when git cannot answer."""
    try:
        changed = subprocess.run(["git", "diff", "--name-only", head], capture_output=True, text=True,
                                 check=True).stdout.split()
        changed += subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], capture_output=True,
                                  text=True, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        return None
    return [f for f in changed if not is_deploy_record(f)]


def milestone_security(p: pathlib.Path) -> list[str]:
    """From v7.1.2, heavy mode: the milestone Security-Reviewer's verdict `<report dir>/reviews/m{N}-security.md`,
    written on the plan's last wave over the whole milestone -- heavy mode's one security review before
    the release's (the owner's ruling of 2026-10-16). PASS or MINOR, `**Independent:** yes`."""
    n = re.match(r"closure-report-(m\d+)", p.name)
    f = p.resolve().parent / "reviews" / f"{n.group(1) if n else 'm{N}'}-security.md"
    if not f.is_file():
        return [f"no milestone Security-Reviewer verdict at `{f.parent.name}/{f.name}` -- heavy mode runs "
                "security once per milestone, on the plan's last wave (`/close-wave`)"]
    body = f.read_text(encoding="utf-8", errors="replace")
    bad: list[str] = []
    v = re.search(r"^##\s*Verdict\s*\n+\s*\W*(PASS|MINOR|BLOCKING)\b(.*)$", body, re.M)
    if not v or "|" in v.group(2):
        bad.append(f"`{f.name}` carries no `## Verdict` of PASS / MINOR / BLOCKING")
    elif v.group(1) == "BLOCKING":
        bad.append(f"`{f.name}` is BLOCKING -- the milestone does not close on a BLOCKING security review")
    if not re.search(r"^\s*\*\*Independent:\*\*[ \t]*yes\b", body, re.M | re.I):
        bad.append(f"`{f.name}` does not declare `**Independent:** yes`")
    return bad


def milestone_tester(p: pathlib.Path, mode: str) -> list[str]:
    """From v7.1 every milestone close carries the milestone Tester's verdict, in both modes.

    Heavy: `<report dir>/reviews/m{N}-tester.md` (what the plan's last wave carried). Light:
    `<report dir>/reviews/release-tester.md`, current for the working tree by its `**Reviewed head:**`.
    """
    bad: list[str] = []
    reviews = p.resolve().parent / "reviews"
    n = re.match(r"closure-report-(m\d+)", p.name)
    if mode == "light":
        f = reviews / "release-tester.md"
        who = ("milestone Tester release verdict (light mode: the close before a release, on "
               "everything merged since the Tester's last verdict)")
    else:
        f = reviews / f"{n.group(1) if n else 'm{N}'}-tester.md"
        who = "milestone Tester verdict (heavy mode: written on the plan's last wave)"
    print(f"  NOTE working mode: {mode} -- the milestone Tester runs at every milestone close in "
          f"light mode too (owner ruling 2026-10-13); expected at `{f.parent.name}/{f.name}`")
    if not f.is_file():
        bad.append(f"no {who} at `{f.parent.name}/{f.name}` -- a milestone does not close without the "
                   "Tester's fault injection, in either mode (.claude/agents/Tester.md)")
        return bad
    body = f.read_text(encoding="utf-8", errors="replace")
    v = re.search(r"^##\s*Verdict\s*\n+\s*\W*(PASS|MINOR|BLOCKING)\b(.*)$", body, re.M)
    if not v or "|" in v.group(2):
        bad.append(f"`{f.name}` carries no `## Verdict` of PASS / MINOR / BLOCKING")
    elif v.group(1) == "BLOCKING":
        bad.append(f"`{f.name}` is BLOCKING -- the milestone does not close on a BLOCKING Tester")
    if not re.search(r"^\s*\*\*Independent:\*\*[ \t]*yes\b", body, re.M | re.I):
        bad.append(f"`{f.name}` does not declare `**Independent:** yes` -- a Tester that wrote the "
                   "code cannot close the milestone")
    m = re.search(r"^\s*\*\*Reviewed head:\*\*\s*`?([0-9a-f]{7,40})`?", body, re.M)
    if not m:
        bad.append(f"`{f.name}` names no `**Reviewed head:** <sha>` -- the Tester's verdict is scoped by "
                   "the head it tested, like docs/reviews/release-security.md; the deploy gate reads it in "
                   "both modes")
    if mode == "light":
        if m:
            code = code_changed_since(m.group(1))
            if code is None:
                bad.append(f"git cannot compare `{f.name}`'s reviewed head {m.group(1)[:7]} with the "
                           "working tree -- the verdict's currency cannot be established (fail closed)")
            elif code:
                bad.append(f"{len(code)} file(s) changed since `{f.name}`'s reviewed head "
                           f"{m.group(1)[:7]}: {', '.join(code[:5])}{' ...' if len(code) > 5 else ''} "
                           "-- the Tester did not see what this milestone ships; re-run it on the "
                           "delta and record the new head")
    return bad


def release_records(root: pathlib.Path = pathlib.Path(".")) -> int:
    """`make closes` in both modes: a release that had its security review had its milestone Tester.

    A light project has no plans and no closure report, so nothing above ever runs for it; its
    milestone close is the release. The deploy gate and `make deploy-check` ask for the Tester's
    verdict at the deploy -- but the brief's `Deploy commands:` defaults to `none`, and a deploy made
    from a dashboard meets no gate at all. This is the one `make check` leg that looks back: once
    `docs/reviews/release-security.md` exists, a release was reviewed, and the Tester's verdict for
    it must exist beside it -- light `release-tester.md` with a `**Reviewed head:**`, heavy at
    least one `m<N>-tester.md` -- each `**Independent:** yes` and not BLOCKING. Exit 0 pass · 1 fail.
    """
    mode = brief_fields.mode(root)
    reviews = root / "docs" / "reviews"
    security = reviews / "release-security.md"
    if not security.is_file():
        print(f"release-records: no docs/reviews/release-security.md yet -- no release to grade ({mode} mode)")
        return 0
    bad: list[str] = []
    if mode == "light":
        files = [reviews / "release-tester.md"]
        who = "the milestone Tester's release verdict (light mode: before a release, on everything merged since its last verdict)"
    else:
        files = sorted(f for f in reviews.glob("m*-tester.md") if re.match(r"^m\d+-tester\.md$", f.name))
        who = "a milestone Tester verdict (heavy mode: docs/reviews/m<N>-tester.md, written on a plan's last wave)"
    if not files or not all(f.is_file() for f in files):
        bad.append(f"docs/reviews/release-security.md exists and {who} is missing -- a release went out "
                   "without the milestone Tester, in a mode where the Tester runs at every milestone close")
    for f in (f for f in files if f.is_file()):
        body = f.read_text(encoding="utf-8", errors="replace")
        v = re.search(r"^##\s*Verdict\s*\n+\s*\W*(PASS|MINOR|BLOCKING)\b(.*)$", body, re.M)
        if not v or "|" in v.group(2):
            bad.append(f"`{f.name}` carries no `## Verdict` of PASS / MINOR / BLOCKING")
        elif v.group(1) == "BLOCKING":
            bad.append(f"`{f.name}` is BLOCKING -- a release does not ship on a BLOCKING Tester")
        if not re.search(r"^\s*\*\*Independent:\*\*[ \t]*yes\b", body, re.M | re.I):
            bad.append(f"`{f.name}` does not declare `**Independent:** yes`")
        if not re.search(r"^\s*\*\*Reviewed head:\*\*\s*`?([0-9a-f]{7,40})`?", body, re.M):
            bad.append(f"`{f.name}` names no `**Reviewed head:** <sha>` -- the deploy gate cannot scope it")
    for b in bad:
        print(f"FAIL [release-records]: {b}")
    if bad:
        return 1
    print(f"release-records PASS: a reviewed release has its milestone Tester verdict ({mode} mode: "
          f"{', '.join(f.name for f in files)})")
    return 0


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):    # a console that cannot encode a character prints `?`
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")
    if argv == ["--release-records"]:
        return release_records()
    if len(argv) != 1:
        print("usage: closure_check.py FILE | --release-records")
        return 2
    p = pathlib.Path(argv[0])
    if not p.is_file():
        print(f"closure_check CANNOT RUN: {p} does not exist -- copy "
              f"docs/closure-report.template.md to docs/closure-report-m{{N}}.md")
        return 2
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    bad: list[str] = []

    if not NAME_RE.match(p.name):
        bad.append(f"`{p.name}` is not a closure report filename. Expected "
                   f"`closure-report-m{{N}}.md` -- a gate that reads whatever it is handed is "
                   f"not a gate")
    stem = p.stem
    m = re.search(r"^id:\s*(\S+)", text, re.M)
    if m and m.group(1) != stem:
        bad.append(f"frontmatter `id: {m.group(1)}` does not match the filename `{stem}` -- two "
                   f"milestones' packs with one id resolve to whichever the validator reads last")

    # History is decided FIRST. v6.7 demanded `record_type: closure` before it asked the version, so
    # a report written before closure front matter existed (`record_type: ratification`, or none)
    # stayed red as history -- model_ranking's twelve, and `make closes` stayed out of its
    # `make check`, so `--release-records` never ran there (v7.1.1).
    vm = re.search(r"^process_version:\s*v?(\d+(?:\.\d+)*)\s*$", text, re.M)
    version = tuple(int(x) for x in vm.group(1).split(".")) if vm else None
    if version is not None and version >= (6, 0) and not re.match(
            r"^---\s*\n(.*?\n)?record_type:\s*closure\b", text, re.S):
        bad.append("no `record_type: closure` frontmatter -- a closure report is a governance "
                   "record, and `check_records.py` is blind to it without one")
    if version is None or version < (6, 0):
        declared = f"v{vm.group(1)}" if vm else "no process_version"
        print(f"  NOTE {p.name} declares {declared} -- graded as history: filename and id only")
        for b in bad:
            print(f"  FAIL {b}")
        print(f"closure_check {'FAIL' if bad else 'PASS'}: {p.name}, history, {len(bad)} finding(s)")
        return 1 if bad else 0
    root = pathlib.Path.cwd()          # `make closes` runs at the project root; so do citations

    for pattern, why in SECTIONS:
        if not re.search(pattern, text, re.M):
            bad.append(f"missing {why}")

    for n, line in enumerate(lines, 1):
        hit = PLACEHOLDER.search(line)
        if hit and not line.lstrip().startswith(("<!--", ">")):
            bad.append(f"line {n} is still template: `{hit.group(0)[:48]}` -- a pack with "
                       f"placeholders was generated, not filled")
            break

    # §1 is read for its CONTENT, not only its shape: a pack whose citing test was `none` and whose
    # status was `❌ FAILED` must not pass.
    in_s1 = False
    for n, line in enumerate(lines, 1):
        if re.match(r"^##\s*1\.\s", line):
            in_s1 = True
            continue
        if in_s1 and line.startswith("## "):
            break
        if not in_s1 or not line.startswith("|") or re.match(r"^\|[\s:|-]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0].lower().startswith("acceptance"):
            continue
        if not re.search(r"[\w./-]+:\d+", cells[1]):
            bad.append(f"line {n}: criterion `{cells[0][:40]}` has no citing test `file:line` "
                       f"(`{cells[1][:30]}`) -- BLOCKING at the Quality Gate")
        elif version >= (6, 7):
            for path, num in re.findall(r"([\w./-]+\.\w+):(\d+)", cells[1]):
                f = root / path
                if not f.is_file():
                    bad.append(f"line {n}: criterion `{cells[0][:40]}` cites `{path}:{num}`, and "
                               f"`{path}` does not exist here -- a citation is checked, not read")
                elif len(f.read_text(encoding="utf-8", errors="replace").splitlines()) < int(num):
                    bad.append(f"line {n}: criterion `{cells[0][:40]}` cites `{path}:{num}`, and "
                               f"`{path}` is shorter than that")
        if "✅" not in cells[3] or re.search(r"❌|FAIL", cells[3], re.I):
            bad.append(f"line {n}: criterion `{cells[0][:40]}` is `{cells[3][:20]}` -- a milestone "
                       f"with a criterion that is not ✅ does not close")

    for n, line in enumerate(lines, 1):
        if not line.startswith("|") or re.match(r"^\|[\s:|-]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) > 1 and any(c == "" for c in cells):
            bad.append(f"line {n} has an empty cell in an evidence table -- an unfilled row is "
                       f"not a claim, and this pack is read as one")
            break

    body6 = re.split(r"^##\s*6\.\s", text, maxsplit=1, flags=re.M)
    if len(body6) == 2:
        prose = re.sub(r"^\*.*\*$", "", body6[1].strip(), flags=re.M).strip()
        if len(prose) < 120:
            bad.append("§6 is empty or near-empty. Every other section is ASSEMBLED from "
                       "referents; §6 is the one a human writes, and it is the whole "
                       "comprehension-debt countermeasure")

    if len(lines) > LINE_CAP:
        bad.append(f"{len(lines)} lines, cap is {LINE_CAP}. The template states a hard cap of two "
                   f"pages: a pack too long to read defeats the review it exists to enable")

    if version >= (7, 1):
        bad += milestone_tester(p, brief_fields.mode(root))
    if version >= (7, 1, 2) and brief_fields.mode(root) != "light":
        bad += milestone_security(p)

    for b in bad:
        print(f"  FAIL {b}")
    print(f"closure_check {'FAIL' if bad else 'PASS'}: {p.name}, {len(lines)} line(s), "
          f"{len(SECTIONS)} required section(s), {len(bad)} finding(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
