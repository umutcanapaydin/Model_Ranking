#!/usr/bin/env python3
"""F.8 — slopsquat / dependency-confusion check.

WHAT IT REPLACES. The `slopsquat` target printed the names of the distributions already installed in
the virtualenv, sorted, and exited 0. It verified nothing. `pipeline-design.md` described it as
"PyPI existence + maintainer-age". **A package that is already installed has by definition survived the
only question this check was pretending to ask**, and an LLM-hallucinated dependency reaches your lock
file before it reaches your venv -- so the check ran at the one moment it could not possibly help.

WHAT IT DOES. Reads DECLARED dependencies (requirements.txt / pyproject.toml), asks PyPI whether each
one exists, and how old its first release is. A name that does not exist is a typo or an attack. A name
whose first release is days old, in a tree where every other dependency is years old, is the shape of a
slopsquat.

OFFLINE IS NOT PASS. If PyPI cannot be reached the check exits non-zero and says so. A supply-chain
control that reports clean because it could not run is the failure this whole lineage is about.

Exit: 0 clean · 1 findings · 2 could not run (network, no manifest).
"""
import sys, json, re, pathlib, datetime, urllib.request, urllib.error

MIN_AGE_DAYS = 90
TIMEOUT = 6
DEP_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def declared(root: pathlib.Path) -> list[str]:
    names: list[str] = []
    req = root / "requirements.txt"
    if req.is_file():
        for line in req.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.split("#")[0].strip()
            if line and not line.startswith("-"):
                m = DEP_RE.match(line)
                if m:
                    names.append(m.group(1))
    pyp = root / "pyproject.toml"
    if pyp.is_file():
        body = pyp.read_text(encoding="utf-8", errors="replace")
        for block in re.findall(r"dependencies\s*=\s*\[(.*?)\]", body, re.S):
            for item in re.findall(r"['\"]([^'\"]+)['\"]", block):
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
    except Exception as e:                                   # noqa: BLE001 - offline must be loud
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
