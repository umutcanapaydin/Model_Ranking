#!/usr/bin/env python3
"""F.8 — slopsquat / dependency-confusion check.

WHAT IT CHECKS. Every DECLARED dependency (requirements.txt, and pyproject.toml's `dependencies`
and `optional-dependencies`) must exist on PyPI, and its FIRST release must be at least
MIN_AGE_DAYS (90) days old. A name that does not exist is a typo or an attack; a name whose first
release is days old, in a tree where every other dependency is years old, is the shape of a
slopsquat. It does not grade maintainers or how recently a project last released.

WHY DECLARED, NOT INSTALLED. A package that is already installed has survived the only question
this check asks, and an LLM-hallucinated dependency reaches the manifest before it reaches the
virtualenv -- so listing the installed set verifies nothing.

OFFLINE IS NOT PASS. If PyPI cannot be reached the check exits non-zero and says so. A supply-chain
control that reports clean because it could not run is a false pass.

Exit: 0 clean · 1 findings · 2 could not run (network, no manifest).
"""
import datetime
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

MIN_AGE_DAYS = 90
TIMEOUT = 6
DEP_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def declared(root: pathlib.Path) -> list[str]:
    """Every dependency this project declares — PARSED, not pattern-matched.

    **M7 Stage-4.0 MINOR-3: this function used to return `['fastapi']`.** One name, out of five,
    and the gate printed PASS on it. The cause is worth keeping: the dependency block was located
    with a NON-GREEDY bracket match, so it stopped at the first closing bracket in the file — the
    one inside `uvicorn[standard]`. Everything past that extra was invisible, including four
    dependencies and every optional group.

    A dependency gate that inspects one fifth of the dependencies and reports success is this
    project's most-repeated defect wearing a regex. `tomllib` reads the file the way the packaging
    tools do, so a dependency cannot be added in a shape the gate cannot see.
    """
    names: list[str] = []

    req = root / "requirements.txt"
    if req.is_file():
        for raw in req.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.split("#")[0].strip()
            if line and not line.startswith("-"):
                m = DEP_RE.match(line)
                if m:
                    names.append(m.group(1))

    pyp = root / "pyproject.toml"
    if pyp.is_file():
        # Parsed, not regexed: a regex over `dependencies = [...]` stops at the `]` inside
        # `uvicorn[standard]`, and grades one dependency of seven.
        try:
            import tomllib
        except ImportError:                  # Python < 3.11: say so, never grade a partial set
            print("slopsquat CANNOT RUN: needs Python >= 3.11 (tomllib) to read pyproject.toml -- "
                  "run it through the project venv: `make slopsquat`")
            raise SystemExit(2) from None
        data = tomllib.loads(pyp.read_text(encoding="utf-8", errors="replace"))
        proj = data.get("project", {})
        items = list(proj.get("dependencies", []))
        for group in proj.get("optional-dependencies", {}).values():
            items += list(group)
        for item in items:
            m = DEP_RE.match(item)
            if m:
                names.append(m.group(1))
    return sorted(set(names))


def pypi(name: str) -> tuple[str, str]:
    """-> (verdict, detail). verdict in {ok, missing, young, unreachable}"""
    url = f"https://pypi.org/pypi/{name}/json"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return "missing", "no such project on PyPI"
        return "unreachable", f"HTTP {e.code}"
    except Exception as e:
        return "unreachable", type(e).__name__
    stamps = [f["upload_time_iso_8601"] for rel in data.get("releases", {}).values() for f in rel
              if f.get("upload_time_iso_8601")]
    if not stamps:
        return "missing", "project exists but has no released files"
    first = min(stamps)[:10]
    age = (datetime.date.today() - datetime.date.fromisoformat(first)).days
    return ("young", f"first release {first}, {age}d old") if age < MIN_AGE_DAYS else ("ok", f"since {first}")


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    names = declared(root)
    if not names:
        print("slopsquat CANNOT RUN: no requirements.txt or pyproject.toml dependency list found.")
        print("  Refusing to report clean. Declare your dependencies, or record a refusal in docs/refusals.md.")
        return 2

    bad, unreachable = [], []
    for n in names:
        verdict, detail = pypi(n)
        if verdict == "unreachable":
            unreachable.append(f"{n} ({detail})")
        elif verdict != "ok":
            bad.append(f"{n}: {detail}")

    if unreachable:
        print(f"slopsquat CANNOT RUN: PyPI unreachable for {len(unreachable)} name(s): "
              f"{', '.join(unreachable[:4])}")
        print("  Exiting non-zero on purpose. A supply-chain check that reports clean because it could")
        print("  not reach the network is the exact false pass this pipeline exists to remove.")
        return 2
    for b in bad:
        print(f"  FAIL [F.8] {b}")
    print(f"slopsquat {'FAIL' if bad else 'PASS'}: {len(names)} declared dependency(ies), {len(bad)} suspect")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
