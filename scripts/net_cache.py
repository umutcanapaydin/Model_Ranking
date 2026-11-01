#!/usr/bin/env python3
"""A local, twelve-hour memory of the two network legs of `make gate` -- `deps` and `slopsquat` -- and their outage.

WHY (v7.2, the owner's ruling of 2026-10-17, process audit F-11). Both legs ask the network about the
DECLARED dependencies, which a change rarely touches: tens of seconds each on every gate, three to five
times a day per branch. Their answer depends only on the manifest -- and on the advisory databases,
which is why the memory expires.

  fresh <leg>   exit 0, printing why, when this leg passed within 12 hours on the very same manifest
                (`pyproject.toml`, `requirements*.txt`, `.devflow-stack`, `stack.mk`, `.deps-accept`);
                otherwise exit 1 and the leg runs. Never fresh in CI (CI, GITHUB_ACTIONS), with
                DEVFLOW_FRESH set, or on a stack other than python (its manifest is not read here).
  record <leg>  after the leg passed: remember it for this manifest.
  outage <leg>  exit 0 when PyPI does not answer and the outage may pass (below); exit 1 otherwise, and
                the leg runs as it always has.

What it does not hold: an advisory published inside the twelve hours is seen at the next run after
they pass, or in CI, which always runs the legs fresh.

A PyPI OUTAGE ON ANOTHER STACK (#51, the owner's ruling of 2026-10-28). On a stack other than python the
two legs grade only DevFlow's own tooling, and a PyPI outage (Project-K: HTTP 502) refused a Swift push.
There, outside CI, the leg passes with a WARN and one `skip` row in `docs/control-events.csv` -- once per
leg, wave and day, so three of them put the control under review. The row's wave is read from the branch
(`wave/m<N>-w<W>`, `*issue-<n>*`, `release/`, `setup/`, `upgrade/`); a branch that names none, a missing
ledger, a python stack or CI: no row is written and the leg stays CANNOT RUN.
An outage is the network's failure: a 5xx, or a connection refused, unresolved, timed out or cut off. A
certificate that does not verify, any other TLS failure or a 4xx is not one, and stays CANNOT RUN.
"""
import csv
import datetime
import hashlib
import http.client
import io
import os
import pathlib
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "build" / "net-cache"
TTL_S = 12 * 3600
LEDGER = pathlib.Path("docs") / "control-events.csv"
#: What the deps leg asks before its audit: PyPI's index page of one package every Python has.
PROBE = "https://pypi.org/simple/pip/"


def manifest_key() -> str:
    h = hashlib.sha256()
    for path in sorted([*ROOT.glob("requirements*.txt"), ROOT / "pyproject.toml", ROOT / ".devflow-stack",
                        ROOT / "stack.mk", ROOT / ".deps-accept"]):
        if path.is_file():
            h.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return h.hexdigest()


def stack(root: pathlib.Path = ROOT) -> str:
    """The first word of `.devflow-stack`, as the Makefile reads it; python when there is none."""
    f = root / ".devflow-stack"
    return (f.read_text(encoding="utf-8").split() or ["python"])[0] if f.is_file() else "python"


def wave(root: pathlib.Path = ROOT) -> str | None:
    """The ledger's wave for this branch, in a shape `make wave-check` counts; None when it names none."""
    try:
        r = subprocess.run(["git", "symbolic-ref", "--short", "-q", "HEAD"], cwd=root, capture_output=True,
                           encoding="utf-8", errors="replace", check=False, timeout=30)
        branch = r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        branch = ""
    if m := re.fullmatch(r"wave/(m\d+-w\d+)", branch):
        return m.group(1)
    if m := re.search(r"(?:^|/)issue-(\d+)(?:-|$)", branch):
        return f"issue-{m.group(1)}"
    if branch.startswith(("release/", "setup/")):
        return branch.split("/", 1)[0]
    installed = root / ".gp" / "installed"
    m = re.search(r"^gp_version:\s*v(\d+(?:\.\d+)*)", installed.read_text(encoding="utf-8"), re.M) \
        if branch.startswith("upgrade/") and installed.is_file() else None
    return f"upgrade-v{m.group(1)}" if m else None


def is_outage(exc: BaseException) -> bool:
    """Whether a failure asking PyPI is the network's: a 5xx answer, or a connection refused, unresolved, timed
    out or cut off. A certificate that does not verify, any other TLS failure, a 4xx and anything else are not:
    they stay CANNOT RUN on every stack (the security review's R1)."""
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code >= 500
    if isinstance(exc, urllib.error.URLError):
        exc = exc.reason if isinstance(exc.reason, BaseException) else ValueError(exc.reason)
    return not isinstance(exc, ssl.SSLError) and isinstance(exc, (OSError, http.client.IncompleteRead))


def describe(exc: BaseException) -> str:
    """A failure in a word or two: `HTTP 502`, or the class of what failed under urllib's wrapper."""
    if isinstance(exc, urllib.error.HTTPError):
        return f"HTTP {exc.code}"
    inner = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    return type(inner if isinstance(inner, BaseException) else exc).__name__


def unreachable(url: str = PROBE) -> tuple[str, bool] | None:
    """None when PyPI answered; else (what went wrong, whether it is an outage)."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=6) as r:
            return None if 200 <= r.status < 400 else (f"HTTP {r.status}", r.status >= 500)
    except Exception as e:                                   # noqa: BLE001 -- classified, never ignored
        return describe(e), is_outage(e)


def outage(leg: str, detail: str, root: pathlib.Path = ROOT) -> bool:
    """True, with a WARN and the ledger row, when this PyPI outage may pass the leg; False otherwise."""
    st = stack(root)
    if st == "python" or os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        return False
    w, ledger, today = wave(root), root / LEDGER, datetime.date.today().isoformat()
    if not w or not ledger.is_file():
        print(f"  {leg}: a PyPI outage passes on the {st} stack only with a skip row in {LEDGER}, and "
              f"{'this branch names no wave for it' if ledger.is_file() else 'there is no ledger'}")
        return False
    try:
        text = ledger.read_text(encoding="utf-8")
        rows = [r for r in csv.reader(ln for ln in text.splitlines() if ln and not ln.startswith("#"))]
        if not any(r[:3] == [leg, w, "skip"] and r[-1:] == [today] for r in rows):
            reason = (f"NO-ENVIRONMENT: PyPI unreachable ({detail}) -- this {st} stack's gate passed without "
                      f"{leg}; CI runs it fresh").replace('"', "'").replace("\n", " ")
            row = io.StringIO()
            csv.writer(row, lineterminator="\n").writerow([leg, w, "skip", reason, today])
            with ledger.open("a", encoding="utf-8", newline="") as f:
                f.write(("" if text.endswith("\n") or not text else "\n") + row.getvalue())
    except OSError as exc:
        print(f"  {leg}: the skip row could not be written to {LEDGER} ({exc})")
        return False
    print(f"{leg} WARN: PyPI unreachable ({detail}) -- on this {st} stack the leg passes, and the skip is a row "
          f"in {LEDGER}: commit it")
    return True


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] not in ("fresh", "record", "outage") or argv[1] not in ("deps", "slopsquat"):
        print("usage: net_cache.py fresh|record|outage deps|slopsquat")
        return 2
    action, leg = argv
    entry = CACHE / leg
    if action == "outage":
        if stack() == "python" or os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            return 1
        found = unreachable()
        return 0 if found and found[1] and outage(leg, found[0]) else 1
    if action == "record":
        if stack() == "python":
            CACHE.mkdir(parents=True, exist_ok=True)
            entry.write_text(manifest_key() + "\n", encoding="utf-8")
        return 0
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS") or os.environ.get("DEVFLOW_FRESH") \
            or stack() != "python" or not entry.is_file():
        return 1
    age = time.time() - entry.stat().st_mtime
    if age >= TTL_S or entry.read_text(encoding="utf-8").strip() != manifest_key():
        return 1
    print(f"{leg}: PASS {age / 3600:.1f} h ago on this same manifest -- not asked again for 12 h "
          "(DEVFLOW_FRESH=1 asks now; CI always asks)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
