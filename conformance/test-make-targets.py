#!/usr/bin/env python3
"""Each gate must REJECT what it exists to reject, through the documented command.

The gap this closes, stated by an external reviewer: `make wave-check FILE=README.md` returned PASS,
and `make smoke-deps` returned 0 while explicitly unwired. Both were "working" by every green board we
had. **A gate is only proven by the input it refuses**, and until now nothing recorded a refusal.

Positive cases matter equally: a gate that fails everything gets switched off within a week.
Exit 0 clean · 1 findings.
"""
import subprocess, sys, pathlib, tempfile, os

ROOT = pathlib.Path(__file__).resolve().parent.parent


def run(args: list[str], cwd: pathlib.Path | None = None) -> int:
    return subprocess.run(args, cwd=cwd or ROOT, capture_output=True, text=True).returncode


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
    expect("wave_check(negative fixture) must REJECT",
           run([py, str(wave), "conformance/wave/m1-wave-3-close.md"]), False)
    # ...and accepts a correctly filled one, or nobody will keep using it
    expect("wave_check(positive fixture) must ACCEPT",
           run([py, str(wave), "conformance/wave/m1-wave-2-close.md"]), True)

    # install-check behaves OPPOSITELY in the two trees, and that is the point of v4.3.2: the
    # distribution must refuse (it legitimately holds every GP-INTERNAL file), an installation must
    # pass. This suite ships to projects, so it has to know which tree it is in -- the first version
    # asserted "the distribution must reject" unconditionally and therefore failed in every exported
    # project. **A test that assumes it is at home fails as soon as the thing it tests is delivered,
    # which is precisely the class of defect this release is about.**
    cr = ROOT / "scripts" / "check_records.py"
    if (ROOT / ".gp-distribution").is_file():
        expect("install-check in the DISTRIBUTION must REJECT",
               run([py, str(cr), "--install", "."]), False)
    else:
        expect("install-check in an INSTALLATION must ACCEPT",
               run([py, str(cr), "--install", "."]), True)
    with tempfile.TemporaryDirectory() as d:
        empty = pathlib.Path(d) / "empty"
        empty.mkdir()
        (empty / "INSTALL-MANIFEST.md").write_text(
            "## PROJECT\n```\nAGENTS.md\n```\n\n## GP-INTERNAL\n```\ndocs/x.md\n```\n")
        expect("install-check on an EMPTY tree must REJECT",
               run([py, str(cr), "--install", "."], cwd=empty), False)
        # a 0-byte file is not an installation
        (empty / "AGENTS.md").write_text("")
        expect("install-check on a 0-BYTE required file must REJECT",
               run([py, str(cr), "--install", "."], cwd=empty), False)
        (empty / "AGENTS.md").write_text("real content\n")
        (empty / ".install-lock").write_text("# synthetic\n")     # M4: a hand-copied tree is not checkable
        expect("install-check on a COMPLETE tree must ACCEPT",
               run([py, str(cr), "--install", "."], cwd=empty), True)

    # smoke-deps: unwired must be loud
    if not (ROOT / "docs" / "smoke-deps.sh").is_file():
        expect("smoke-deps UNWIRED must REJECT", run(["make", "smoke-deps"]), False)

    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-make-targets {'FAIL' if bad else 'PASS'}: {len(bad)} gate(s) not proven")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
