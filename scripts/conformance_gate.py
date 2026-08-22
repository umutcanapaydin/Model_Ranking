#!/usr/bin/env python3
"""Run the conformance suite and fail on anything that is not a NAMED, reasoned exemption.

**Why this exists.** `make check` did not run `conformance/run-all.py` at all, so the suite ran only
in CI — and CI had been RED since at least M8 on two legs that fail for reasons handed back to the
pipeline (GPF-001, GPF-004). A permanently red CI teaches everyone to stop reading it, and that is
what happened: the M9 closure push was the first time anyone looked, and it turned out one of the
five findings was NEW and ours.

The obvious fixes are both wrong. Leaving conformance out of `make check` is what caused this.
Skipping the two failing LEGS would have hidden our own defect, which lived inside a leg that was
already failing for someone else's reason.

So the exemption is per FINDING, not per leg: every known failure is listed with the GP finding it
belongs to, and anything else fails the build. An exemption that stops firing is also a failure —
an exemption outliving its cause silently widens.

Usage:  conformance_gate.py
Exit:   0 clean or only-exempted · 1 a new finding, or a stale exemption · 2 the suite did not run
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: `<path>:<line>` -> why it is not ours to fix. Every entry names the finding it belongs to.
EXEMPT: dict[str, str] = {
    # GPF-001: v5.0 removed the `pin-check` Make target, which retroactively invalidates the
    # records of every project that documented it. These are append-only historical records; the
    # remedy is GP's, and rewriting history to match a tool is the thing GPF-001 argues against.
    "docs/closure-report-m3.md:69": "GPF-001 — a removed Make target invalidates historical records",
    "docs/reviews/m4-security-review.md:80": "GPF-001 — same",
    "docs/reviews/m5-security-review.md:101": "GPF-001 — same",
    "docs/reviews/m7-wave-1-review.md:369": "GPF-001 — same",
    # GPF-004: `test-git-authority.py` cannot tell a compliance ATTESTATION from an instruction.
    # Both lines are a security review stating that it did NOT run git — the check reads the
    # sentence as the act it forbids.
    "docs/reviews/m6-security-review.md:556": "GPF-004 — an attestation read as an instruction",
    "docs/reviews/m6-security-review.md:989": "GPF-004 — same",
}

FINDING = re.compile(r"^\s*FAIL\s+(\S+?:\d+)\s+(.*)$")


def _load_suite():
    """Import `conformance/run-all.py` by path; the directory is not a package."""
    spec = importlib.util.spec_from_file_location("conformance_run_all", ROOT / "conformance/run-all.py")
    if spec is None or spec.loader is None:  # pragma: no cover - a missing suite is a broken tree
        msg = "conformance/run-all.py is missing; the suite cannot run"
        raise SystemExit(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    # Called IN-PROCESS rather than shelled out, for the reason the security lint gives and for a
    # better one: spawning an interpreter made this gate's answer depend on which interpreter was
    # on PATH — the same "the thing you measured is not the thing that runs" shape this project
    # keeps finding elsewhere.
    suite = _load_suite()
    captured = io.StringIO()
    cwd = pathlib.Path.cwd()
    try:
        import os

        os.chdir(ROOT)
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            code = suite.main()
    finally:
        os.chdir(cwd)
    output = captured.getvalue()
    if not output.strip():
        print("conformance-gate: the suite produced no output; it did not run")
        return 2

    seen: dict[str, str] = {}
    for line in output.splitlines():
        match = FINDING.match(line)
        if match:
            seen[match.group(1)] = match.group(2).strip()

    unexpected = sorted(where for where in seen if where not in EXEMPT)
    stale = sorted(where for where in EXEMPT if where not in seen)

    for where in unexpected:
        print(f"conformance-gate: NEW finding at {where}: {seen[where]}")
    for where in stale:
        print(
            f"conformance-gate: {where} is exempted ({EXEMPT[where]}) and no longer fires; "
            "remove the exemption rather than leaving it to cover something else later"
        )

    if unexpected or stale:
        print(
            f"conformance-gate FAIL: {len(unexpected)} new finding(s), {len(stale)} stale exemption(s)"
        )
        return 1

    if code != 0 and not seen:
        print("conformance-gate: the suite failed without reporting a finding this gate can read")
        print(output[-2000:])
        return 1

    print(
        f"conformance-gate PASS: {len(seen)} finding(s), all exempted and all still firing "
        f"({len(EXEMPT)} exemptions, every one handed back to the pipeline)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
