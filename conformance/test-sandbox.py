#!/usr/bin/env python3
"""In a sandbox that refuses a local bind and `ps`, with a temp path near 200 characters, no test crashes or passes what it could not judge.

WHY (#72, run v73). A sandboxed Claude Code session on macOS (`allowLocalBinding` off) refuses binding a local
port and running `ps`, and its TMPDIR's real path is about 199 characters. A fresh v7.3 install's `make gate`
failed there on three tests: two died with a PermissionError traceback, and test-cost miscounted. A test that
cannot judge a case here says so -- NOT-EVALUABLE, exit 2, with the reason -- and still judges every other case;
it never crashes, and never passes a case it did not judge.

The subjects are DERIVED: every conformance test whose source binds a socket or runs `ps`. Each must say
NOT-EVALUABLE here, naming the required CI job (docs/branch-protection.md) that judges what it skipped: the call
it makes is refused, so a case went unjudged, and a PASS would hide that. (One that judges such a case another
way becomes a named entry below, with its reason.) A test whose source imports a socket module or names `ps`
but that the scan did not select fails: a spelling the scan does not know never drops a subject silently.
test-cost is a named entry that must PASS: the long temp path broke its product (scripts/cost_ledger.py), not
a call a scan can see.
Each subject runs under a driver that makes `socket.bind` and an exec of `ps` raise PermissionError (EPERM) in
the test's own process, as the sandbox does, and hides /proc as macOS has none (so Linux CI reaches `ps` too),
with TMPDIR at a real path of at least 199 characters. The test's children are not patched: what they would
meet in a real sandbox is out of this test's reach.

Exit: 0 every subject gives its verdict - 1 one crashes, fails, passes unjudged, or exits otherwise.
"""
import os
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import scrubbed_env  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
#: Named, not derived, each with the exit it must give and why (#72's issue 2: the long temp path broke this
#: test's product, not a call in its source).
NAMED = {"test-cost.py": (0, "the field's long TMPDIR made scripts/cost_ledger.py miscount")}
CALLS = re.compile(r"\.bind\(|create_server\(|start_server\(|HTTPServer\(|socketserver\."
                   r"|[\[(]\s*[\"'](?:/usr)?(?:/bin/)?ps[\"']|[\"']ps\s+-[op]")
#: Wider than CALLS on purpose: what it holds that CALLS does not is a FAILURE, never a dropped subject.
NET = re.compile(r"^\s*(?:import|from)\s[^\n#]*\b(?:socket|socketserver|http\.server|asyncio)\b|\bps\b", re.M)
JOBS = re.compile(r"^\|\s*\**`([a-z][a-z0-9-]*)`\**\s*\|", re.M)    # the required checks, as test-ci-yaml reads them
FIELD_TMP = 199

DRIVER = """\
import errno, os, pathlib, runpy, socket, subprocess, sys
read_text = pathlib.Path.read_text
def no_proc(self, *a, **k):
    if str(self).startswith("/proc/"):
        raise FileNotFoundError(errno.ENOENT, "No such file or directory", str(self))
    return read_text(self, *a, **k)
pathlib.Path.read_text = no_proc
def bind(self, *a, **k):
    raise PermissionError(errno.EPERM, "Operation not permitted")
socket.socket.bind = bind
real = subprocess.Popen._execute_child
def execute(self, args, executable, *rest, **kw):
    cmd = [os.fsdecode(a) for a in ([args] if isinstance(args, (str, bytes)) else args)] or [""]
    line = cmd[2] if len(cmd) > 2 and cmd[1] == "-c" else cmd[0]      # a shell line: its first word
    if "ps" in {os.path.basename(os.fsdecode(executable or "")), os.path.basename(cmd[0]),
                os.path.basename((line.split() or [""])[0])}:
        raise PermissionError(errno.EPERM, "Operation not permitted", "ps")
    return real(self, args, executable, *rest, **kw)
subprocess.Popen._execute_child = execute
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


def main() -> int:
    me = pathlib.Path(__file__).name
    src = {p.name: p.read_text(encoding="utf-8") for p in HERE.glob("test-*.py") if p.name != me}
    derived = sorted(n for n, s in src.items() if CALLS.search(s))
    unseen = sorted(n for n, s in src.items() if NET.search(s) and n not in derived and n not in NAMED)
    if unseen:
        print("\n".join(f"  {n}: its source names a socket module or `ps`, but the scan of calls did not select it"
                        for n in unseen))
        print("test-sandbox FAIL: widen CALLS to its spelling, or name it in NAMED with its exit and reason")
        return 1
    bp = HERE.parent / "docs" / "branch-protection.md"
    jobs = set(JOBS.findall(bp.read_text(encoding="utf-8"))) if bp.is_file() else set()
    if not jobs:
        print(f"test-sandbox FAIL: no required CI job read from {bp} -- nothing to name as the cover of a skipped case")
        return 1
    if not derived:
        print("test-sandbox FAIL: no conformance test binds a socket or runs `ps` -- the derived set is empty, "
              "so the scan, not the suite, has changed")
        return 1
    missing = [n for n in NAMED if not (HERE / n).is_file()]
    if missing:
        print(f"test-sandbox FAIL: a named subject is gone: {missing} -- drop its entry with the reason it no longer holds")
        return 1
    bad: list[str] = []
    verdicts: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        long_tmp = pathlib.Path(os.path.realpath(tmp))
        while len(str(long_tmp)) < FIELD_TMP:
            long_tmp = long_tmp / ("t" * max(1, min(64, FIELD_TMP - len(str(long_tmp)) - 1)))
        long_tmp.mkdir(parents=True, exist_ok=True)
        env = scrubbed_env({"TMPDIR": str(long_tmp), "TEMP": str(long_tmp), "TMP": str(long_tmp)})
        for name in sorted(set(derived) | set(NAMED)):
            try:
                r = subprocess.run([sys.executable, "-c", DRIVER, str(HERE / name)], capture_output=True,
                                   encoding="utf-8", errors="replace", env=env, timeout=600)
            except subprocess.TimeoutExpired:
                bad.append(f"  {name}: no verdict within 600 s")
                continue
            out = r.stdout + r.stderr
            last = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
            if "Traceback (most recent call last)" in out:
                tb = [ln for ln in r.stderr.strip().splitlines() if ln.strip()][-1:] or ["?"]
                bad.append(f"  {name}: crashed (exit {r.returncode}): {tb[0][:200]}")
            elif r.returncode == 2 and "NOT-EVALUABLE:" not in last:
                bad.append(f"  {name}: exit 2 without a NOT-EVALUABLE line naming why: {last[:200]}")
            elif r.returncode == 2 and name not in NAMED and not any(f"`{j}`" in last for j in jobs):
                bad.append(f"  {name}: NOT-EVALUABLE names no required CI job ({', '.join(sorted(jobs))}) that "
                           f"judges what it skipped (writing-a-control §5): {last[:200]}")
            elif r.returncode == 0 and name not in NAMED:
                bad.append(f"  {name}: exit 0 although its bind or `ps` was refused -- a PASS over a case it did not "
                           f"judge: {last[:200]}")
            elif r.returncode == 2 and name in NAMED and NAMED[name][0] != 2:
                bad.append(f"  {name}: exit 2, wanted {NAMED[name][0]} ({NAMED[name][1]}): {last[:200]}")
            elif r.returncode not in (0, 2):
                bad.append(f"  {name}: exit {r.returncode}: {last[:200]}"
                           + "".join(f"\n    {ln}" for ln in r.stdout.strip().splitlines()[:-1][:12]))
            verdicts.append(f"{name} {({0: 'PASS', 2: 'NOT-EVALUABLE'}).get(r.returncode, 'FAIL')}")
    scope = f"{len(derived)} derived ({', '.join(derived)}) + {len(NAMED)} named, TMPDIR {len(str(long_tmp))} characters"
    if bad:
        print("\n".join(bad))
        print(f"test-sandbox FAIL -- {len(bad)} finding(s) under a refused bind and `ps` [{scope}]")
        return 1
    print(f"test-sandbox PASS: under a refused bind and `ps`, each gives its verdict -- {'; '.join(verdicts)} [{scope}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
