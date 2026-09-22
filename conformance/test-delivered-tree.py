#!/usr/bin/env python3
"""Run the suite inside the tree a PROJECT actually receives.

Increment 19 council, DevOps seat, the cross-cutting risk the packet missed:

    "Nothing ever runs the tree a project receives. All four new controls were proven in a tree
    that has `.gp-distribution`, a local `main`, `HARVEST-CONTEXT.md`, and `src/`. None of those
    four preconditions holds in an export, and no gate, recipe or CI step executes
    `conformance/run-all.py` inside the output of `export_project.py`. One command -- export,
    `git init`, run the suite -- found it in ten seconds. Add it as a recipe and the whole class
    stops shipping."

What it found in ten seconds was the worst defect in the cut: `test-harvest-context-hash`
returned 1 rather than 2 when no roster could be derived, and a roster is GP-INTERNAL by
manifest, so **every project installing v5.4 would have met a red required gate it could never
turn green**. The chair had run every new control in trees he built for it and never once in the
delivery.

The scratch-tree caveat the packet did carry (18-K's PROVEN-IN-SCRATCH) named the wrong gap. A
hand-shaped scratch tree per recipe is not the delivery; the delivery is the one artefact GP
ships and the one nobody was executing.

WHAT THIS ASSERTS. Export the package, make it a git repository, and run the conformance suite
inside it. Any FAIL is a finding. `NOT-EVALUABLE` is fine and expected -- an installation holds
no harvests, no roster history and no deployment surface, and controls that say so are behaving.
A control that CANNOT distinguish those two is the whole subject of this increment.

Guarded against recursion by the same marker everything else uses: the export carries no
`.gp-distribution`, so inside it this test reports CANNOT RUN and the suite does not nest.

Exit: 0 clean - 1 findings - 2 cannot run.
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent
TIMEOUT = 600


def run(cmd, cwd, env=None):
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                          timeout=TIMEOUT, env=env)


def _declared_version(record: pathlib.Path):
    m = re.search(r"^process_version:\s*(\S+)\s*$", record.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def main() -> int:
    if not (PKG / ".gp-distribution").is_file():
        print("test-delivered-tree CANNOT RUN: this is an installation, not the distribution. "
              "There is no export to make from here, and nesting one would recurse.")
        return 2
    exporter = PKG / "scripts" / "export_project.py"
    if not exporter.is_file():
        print(f"test-delivered-tree CANNOT RUN: no {exporter.name}. The delivery cannot be built, "
              "so it cannot be graded -- which is not the same as it being correct.")
        return 2

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="delivered-"))
    try:
        dest = tmp / "proj"
        r = run([sys.executable, str(exporter), str(dest)], PKG)
        if r.returncode != 0:
            print("test-delivered-tree FAIL: `export_project.py` itself failed, so no project can "
                  "be delivered at all:")
            print((r.stdout + r.stderr).strip()[:600])
            return 1

        # A real project is a git repository. Several controls resolve refs, and an export with
        # no history is not the tree anyone actually receives either.
        for args in (["init", "-q", "-b", "main"], ["config", "user.email", "delivery@probe"],
                     ["config", "user.name", "delivery-probe"], ["add", "-A"],
                     ["commit", "-qm", "delivered tree"]):
            run(["git", *args], dest)

        r = run([sys.executable, "conformance/run-all.py"], dest)
        out = r.stdout + r.stderr
        fails = [ln.strip() for ln in out.splitlines() if "[FAIL" in ln or "caller-liveness:" in ln]
        summary = next((ln.strip() for ln in out.splitlines()
                        if ln.startswith("conformance ")), "(no summary line)")
        if r.returncode != 0 or fails:
            print("test-delivered-tree FAIL: the suite does not pass in the tree a project "
                  "receives. This is the delivery, not a scratch tree:")
            for ln in fails[:8]:
                print(f"    {ln[:200]}")
            print(f"    {summary}")
            return 1

        # v6.0. The suite passing is not the install passing. `make install` ends in
        # `write_install_marker.py`, which derives the version from the delivered records'
        # frontmatter -- and the export's provenance strip had emptied that field, so every
        # delivery since the split REFUSED at install, and `test`, `check` and `gate` all depend on
        # `install`. Nothing ran the marker in a delivery; this does, and asks it for the version
        # the package declares.
        want = _declared_version(PKG / "docs" / "decisions.md")
        r = run([sys.executable, "scripts/write_install_marker.py"], dest)
        marker = dest / ".gp" / "installed"
        got = None
        if marker.is_file():
            m = re.search(r"^gp_version:\s*(\S+)\s*$", marker.read_text(encoding="utf-8"), re.M)
            got = m.group(1) if m else None
        if r.returncode != 0 or want is None or got != want:
            print("test-delivered-tree FAIL: the install marker refuses in the tree a project "
                  f"receives -- every `make install` there fails closed. package declares "
                  f"{want!r}, delivery recorded {got!r}:")
            print(f"    {(r.stdout + r.stderr).strip()[:300]}")
            return 1

        # And the check that runs next. The marker is the project's own, so a complete install
        # must still pass M1/M2 with it present -- it did not: M2 read it as a GP-INTERNAL leak,
        # and every `make check` after a successful install was red.
        r = run([sys.executable, "scripts/check_records.py", "--install", "."], dest)
        if r.returncode != 0:
            print("test-delivered-tree FAIL: after `make install` wrote its marker, the install "
                  "check refuses the tree a project receives:")
            for ln in (r.stdout + r.stderr).splitlines():
                if re.search(r"\[M\d\]", ln):
                    print(f"    {ln.strip()[:200]}")
            return 1

        neval = len(re.findall(r"\[NOT-EVALUABLE", out))
        print(f"test-delivered-tree PASS: exported, committed and ran the suite in the delivery. "
              f"{summary} ({neval} NOT-EVALUABLE, which is correct in an installation: no "
              f"harvests, no roster history, no deployment surface); install marker records {got}")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:                                              # noqa: BLE001
        print(f"test-delivered-tree internal error: {exc}", file=sys.stderr)
        sys.exit(2)
