#!/usr/bin/env python3
"""A local, twelve-hour memory of the two network legs of `make gate` -- `deps` and `slopsquat`.

WHY (v7.2, the owner's ruling of 2026-10-17, process audit F-11). Both legs ask the network about the
DECLARED dependencies, which a change rarely touches: tens of seconds each on every gate, three to five
times a day per branch. Their answer depends only on the manifest -- and on the advisory databases,
which is why the memory expires.

  fresh <leg>   exit 0, printing why, when this leg passed within 12 hours on the very same manifest
                (`pyproject.toml`, `requirements*.txt`, `.devflow-stack`, `stack.mk`); otherwise exit 1
                and the leg runs. Never fresh in CI (CI, GITHUB_ACTIONS), with DEVFLOW_FRESH set, or on
                a stack other than python (its manifest is not read here).
  record <leg>  after the leg passed: remember it for this manifest.

What it does not hold: an advisory published inside the twelve hours is seen at the next run after
they pass, or in CI, which always runs the legs fresh.
"""
import hashlib
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "build" / "net-cache"
TTL_S = 12 * 3600


def manifest_key() -> str:
    h = hashlib.sha256()
    for path in sorted([*ROOT.glob("requirements*.txt"), ROOT / "pyproject.toml", ROOT / ".devflow-stack",
                        ROOT / "stack.mk"]):
        if path.is_file():
            h.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return h.hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] not in ("fresh", "record") or argv[1] not in ("deps", "slopsquat"):
        print("usage: net_cache.py fresh|record deps|slopsquat")
        return 2
    action, leg = argv
    stack = (ROOT / ".devflow-stack").read_text(encoding="utf-8").strip() if (ROOT / ".devflow-stack").is_file() \
        else "python"
    entry = CACHE / leg
    if action == "record":
        if stack == "python":
            CACHE.mkdir(parents=True, exist_ok=True)
            entry.write_text(manifest_key() + "\n", encoding="utf-8")
        return 0
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS") or os.environ.get("DEVFLOW_FRESH") \
            or stack != "python" or not entry.is_file():
        return 1
    age = time.time() - entry.stat().st_mtime
    if age >= TTL_S or entry.read_text(encoding="utf-8").strip() != manifest_key():
        return 1
    print(f"{leg}: PASS {age / 3600:.1f} h ago on this same manifest -- not asked again for 12 h "
          "(DEVFLOW_FRESH=1 asks now; CI always asks)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
