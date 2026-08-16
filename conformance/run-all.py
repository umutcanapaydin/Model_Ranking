#!/usr/bin/env python3
"""Run every conformance test and report each by name.

V4C-80. `--self-test` calls rule functions directly; it proved `M1`/`M2` worked while they could not
fire through any shipped command. These tests go the other way: they exercise the DOCUMENTED surface --
the Makefile, the workflows, the hook config, the record globs -- and assert the claims match the code.

Every test here must be reachable from `make gate`, or it is a control with no caller, which this
pipeline has now shipped four separate times.

Exit 0 all pass · 1 any fail.
"""
import subprocess, sys, pathlib

TESTS = [
    ("test-ci-yaml.py",         "every CI step runs what its name says"),
    ("test-governed-paths.py",  ".governed-records globs match real paths"),
    ("test-hook-claims.py",     "every control the docs claim is reachable from `make gate`"),
    ("test-git-authority.py",   "no local-lane commit; the CI agent is attributable"),
    ("test-make-targets.py",    "each gate rejects what it must reject"),
    ("test-documented-commands.py", "every `make X` a shipped doc names actually exists"),
    ("test-action-pins.py",      "every GitHub Action pinned to a SHA, not a mutable tag"),
]


# The dev dependencies -- PyYAML among them -- live in `.venv`, not in the system interpreter. Running
# `python3 conformance/run-all.py` with the system python made `test-ci-yaml` report CANNOT RUN, which
# is the correct refusal and the wrong interpreter. Prefer the venv when it exists.
PY = str(pathlib.Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python")
if not pathlib.Path(PY).exists():
    PY = sys.executable


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    fails = []
    for script, why in TESTS:
        p = here / script
        if not p.is_file():
            print(f"  MISSING {script} -- {why}"); fails.append(script); continue
        r = subprocess.run([PY, str(p)], capture_output=True, text=True)
        tail = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
        print(f"  [{'PASS' if r.returncode == 0 else 'FAIL'}] {script:26s} {tail}")
        if r.returncode != 0:
            fails.append(script)
            for line in r.stdout.strip().splitlines()[:-1]:
                print(f"         {line}")
    print(f"conformance {'FAIL' if fails else 'PASS'}: {len(TESTS)} test(s), {len(fails)} failing")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
