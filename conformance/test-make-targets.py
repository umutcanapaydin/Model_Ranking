#!/usr/bin/env python3
"""Each gate must REJECT what it exists to reject, and ACCEPT correct work.

`make wave-check FILE=README.md` once returned PASS, and `make smoke-deps` returned 0 while
explicitly unwired. Both were "working" by every green board. **A gate is only proven by the input
it refuses.** Positive cases matter equally: a gate that fails everything gets switched off within a
week. A negative fixture must also be refused FOR ITS REASON -- a refusal for some other defect
proves nothing about the rule it was written for.

This runs the checker each target calls (`scripts/wave_check.py`, `scripts/closure_check.py`,
`scripts/check_records.py --install`) on the fixtures, and `make smoke-deps` through make; that each
target reaches its checker is `test-hook-claims`' question. A positive case runs where the project's
own ledger, brief and records cannot reach it -- a throwaway tree, or an empty `--root`: in an
installation they are the project's, and a finding in them is not a gate that failed to accept.
Exit 0 clean - 1 findings - 2 not evaluable here (no `make` for the one case that needs it).
"""
import subprocess, sys, pathlib, tempfile, os

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool                                  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def run(args: list[str], cwd: pathlib.Path | None = None) -> int:
    return subprocess.run(args, cwd=cwd or ROOT, capture_output=True, encoding="utf-8",
                          errors="replace").returncode


def output(args: list[str], cwd: pathlib.Path | None = None) -> tuple[int, str]:
    r = subprocess.run(args, cwd=cwd or ROOT, capture_output=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    bad: list[str] = []

    def expect(label: str, got: int, want_zero: bool):
        ok = (got == 0) if want_zero else (got != 0)
        if not ok:
            bad.append(f"{label}: exit {got}, expected {'0' if want_zero else 'non-zero'}")

    py = sys.executable
    wave = ROOT / "scripts" / "wave_check.py"

    # wave-check: refuses a document that is not a wave checklist
    expect("wave_check(README.md) must REJECT", run([py, str(wave), "README.md"]), False)
    expect("wave_check(closure-checklist) must REJECT",
           run([py, str(wave), "docs/closure-checklist.md"]), False)
    # The fixtures run in a throwaway tree: wave_check reads the ledger, the brief and the install
    # marker of the tree it runs in, and in an installation that is the project's. fitness_app's eight
    # free-form ledger rows were reported here as "gate not proven" (v7.1.1). The tree carries the
    # fixtures, their verdicts, the row-kind legend this package delivers and a header-only ledger.
    import shutil as _shutil
    with tempfile.TemporaryDirectory() as d:
        tree = pathlib.Path(d)
        for sub in ("wave", "reviews"):
            _shutil.copytree(ROOT / "conformance" / sub, tree / "conformance" / sub)
        (tree / "docs").mkdir()
        _shutil.copy(ROOT / "docs" / "warnings.ledger.template.md", tree / "docs")
        (tree / "docs" / "control-events.csv").write_text("control,wave,kind,reason,date\n",
                                                          encoding="utf-8")
        rc, out = output([py, str(wave), "conformance/wave/m901-wave-3-close.md"], cwd=tree)
        expect("wave_check(negative fixture) must REJECT", rc, False)
        # ...for the two reasons the fixture declares, not only for being thin.
        for why, said in (("an undeclared SKIPPED", "SKIPPED without PRESSURE or NO-ENVIRONMENT"),
                          ("an unevidenced PASS", "carry no evidence")):
            if said not in out:
                bad.append(f"wave_check(negative fixture) was not refused for {why}: it never printed "
                           f"`{said}` -- a refusal for another reason proves nothing about this rule")
        # ...and accepts a correctly filled one, or nobody will keep using it
        rc, out = output([py, str(wave), "conformance/wave/m901-wave-2-close.md"], cwd=tree)
        expect("wave_check(positive fixture) must ACCEPT", rc, True)
        if rc != 0:
            bad.append("  " + " | ".join(out.strip().splitlines()[-3:]))

    # closure-check: the milestone half of the same rule. A pack missing §1b hides the judgment
    # calls; a pack whose §6 is a heading has skipped the one section a human must write.
    closure = ROOT / "scripts" / "closure_check.py"
    expect("closure_check(template) must REJECT",
           run([py, str(closure), "docs/closure-report.template.md"]), False)
    expect("closure_check(hollow fixture) must REJECT",
           run([py, str(closure), "conformance/closure/closure-report-m908.md"]), False)
    expect("closure_check(filled fixture) must ACCEPT",
           run([py, str(closure), "conformance/closure/closure-report-m907.md"]), True)
    # v7.1.1: a report from before closure front matter (`record_type: ratification`, no version) is
    # history, graded by filename and id -- v7.1 asked for the front matter first and kept it red.
    rc, out = output([py, str(closure), "conformance/closure/closure-report-m910.md"])
    expect("closure_check(pre-front-matter history fixture) must ACCEPT", rc, True)
    if "history" not in out:
        bad.append("closure_check(pre-front-matter history fixture) was not graded as history: it never "
                   "printed `history`")
    # v7.1: a filled report carrying the milestone Tester's verdict beside it (`closure/reviews/`).
    # `test-milestone-tester.py` proves the refusals; this proves the fixture a project copies passes.
    # In a throwaway tree with a HEAVY brief: the check reads the project's working mode, and in a
    # light project the fixture would be graded against `release-tester.md`, which it does not ship
    # -- a suite that fails in every light installation on its own fixture grades nothing.
    import re as _re
    with tempfile.TemporaryDirectory() as d:
        tree = pathlib.Path(d)
        (tree / "docs" / "reviews").mkdir(parents=True)
        (tree / "docs" / "project-brief.md").write_text(
            "---\nrecord_type: brief\nid: project-brief\nstatus: draft\n---\n- **Working mode:** `heavy`\n",
            encoding="utf-8")
        report = ROOT / "conformance" / "closure" / "closure-report-m909.md"
        _shutil.copy(report, tree / "docs" / "closure-report-m909.md")
        _shutil.copy(ROOT / "conformance" / "closure" / "reviews" / "m909-tester.md", tree / "docs" / "reviews" / "m909-tester.md")
        for path, _ in _re.findall(r"`([\w./-]+\.\w+):(\d+)`", report.read_text(encoding="utf-8")):
            f = tree / path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("x\n" * 200, encoding="utf-8")
        expect("closure_check(v7.1 filled fixture with its Tester verdict, heavy brief) must ACCEPT",
               run([py, str(closure), "docs/closure-report-m909.md"], cwd=tree), True)

    # install-check behaves OPPOSITELY in the two trees: the distribution must refuse (it
    # legitimately holds every GP-INTERNAL file), an installation must pass. This suite ships to
    # projects, so it has to know which tree it is in. **A test that assumes it is at home fails as
    # soon as the thing it tests is delivered.**
    cr = ROOT / "scripts" / "check_records.py"
    if (ROOT / ".gp-distribution").is_file():
        expect("install-check in the DISTRIBUTION must REJECT",
               run([py, str(cr), "--install", "."]), False)
    else:
        # M1, M2 and M4 only: the record rules run on an empty root. `--install .` alone also graded
        # the project's own records, and fitness_app's duplicate process-log session (S1) read as
        # "install-check not proven" (v7.1.1); `make check-records` is the leg that grades those.
        with tempfile.TemporaryDirectory() as d:
            rc, out = output([py, str(cr), "--root", d, "--install", str(ROOT)])
            expect("install-check in an INSTALLATION must ACCEPT", rc, True)
            if rc != 0:
                bad.append("  " + " | ".join(ln for ln in out.splitlines() if "[M" in ln)[:400])
    with tempfile.TemporaryDirectory() as d:
        empty = pathlib.Path(d) / "empty"
        empty.mkdir()
        (empty / "INSTALL-MANIFEST.md").write_text(
            "## PROJECT\n```\nAGENTS.md\n```\n\n## GP-INTERNAL\n```\ndocs/x.md\n```\n",
            encoding="utf-8")
        expect("install-check on an EMPTY tree must REJECT",
               run([py, str(cr), "--install", "."], cwd=empty), False)
        # a 0-byte file is not an installation
        (empty / "AGENTS.md").write_text("", encoding="utf-8")
        expect("install-check on a 0-BYTE required file must REJECT",
               run([py, str(cr), "--install", "."], cwd=empty), False)
        (empty / "AGENTS.md").write_text("real content\n", encoding="utf-8")
        # M4: a hand-copied tree is not checkable
        (empty / ".install-lock").write_text("# synthetic\n", encoding="utf-8")
        expect("install-check on a COMPLETE tree must ACCEPT",
               run([py, str(cr), "--install", "."], cwd=empty), True)

    # smoke-deps: unwired must be loud. Through make, so without make it is not graded -- and says so.
    no_make = None
    if not (ROOT / "docs" / "smoke-deps.sh").is_file():
        no_make = missing_tool("make", "grade `make smoke-deps` (an unwired gate must refuse)")
        if not no_make:
            expect("smoke-deps UNWIRED must REJECT", run(["make", "smoke-deps"]), False)

    for b in bad:
        print(f"  FAIL {b}")
    if no_make:
        print(f"  NOT-EVALUABLE {no_make}")
    verdict = "FAIL" if bad else ("NOT-EVALUABLE" if no_make else "PASS")
    print(f"test-make-targets {verdict}: {len(bad)} gate(s) not proven")
    return 1 if bad else (2 if no_make else 0)


if __name__ == "__main__":
    sys.exit(main())
