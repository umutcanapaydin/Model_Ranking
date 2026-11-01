#!/usr/bin/env python3
"""The statusline appends DevFlow's segment to the owner's own statusline, caches git, calls no network tool, and counts the session's tokens once.

WHY (v7.3, A22; the owner's ruling of 2026-10-28). Project settings win over the user's for `statusLine`, so
DevFlow's command must run the owner's own one itself, or the owner loses it in every DevFlow project. Each
claim is a case: with no personal statusline the segment stands alone; with one, it is appended to that line's
last row; a personal statusline that fails or hangs is left out within its time limit, and DevFlow's part still
shows; one that runs this statusline again prints DevFlow's segment once (no recursion). The segment names the
mode, the branch, the open run and its running wave, the gate stamp at HEAD (and not, once the tree changes),
the last check-fast, the context used and the session's tokens in tokens, never USD. Git runs once per CACHE_S
for a session -- a refresh that starts with a fresh cache entry runs none, judged from the cache file the first
refresh wrote, not from wall time -- `gh` never, and a transcript read once is not counted again: a refresh after
one more message adds that message only. Every git call carries `--no-optional-locks`: a status that takes
`.git/index.lock` fails the session's own `git add`, and one stopped mid-way leaves the lock behind (v7.3 review,
B2). When Claude Code stops a refresh in flight (SIGTERM), the owner's own command goes with it, never orphaned
(M1); that case is judged only while the command is alive inside its time limit, and a stop that lands as the
command starts is sent from inside Popen, so it is judged on every run (#87). Once the command has returned,
a stop ends the statusline alone: a background job the owner's command left running survives (M5).

Each case runs .claude/statusline.py on a throwaway repository with a fake `git` wrapper and a fake `gh` that log
their calls, and the user settings in a throwaway CLAUDE_CONFIG_DIR: the real ones are never read.

Where neither /proc nor `ps` can tell a running process from a zombie (a sandbox that refuses `ps`, #72), the two
cases that need it are not judged, every other case is, and the verdict is NOT-EVALUABLE.

Exit: 0 every case behaves - 1 one does not - 2 git not installed, or a case could not be judged here.
"""
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATUSLINE = ROOT / ".claude" / "statusline.py"


def git(cwd: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True,
                          env=scrubbed_env()).stdout.strip()


def usage_line(mid: str, n: int, side: bool = False) -> str:
    return json.dumps({"type": "assistant", "isSidechain": side, "requestId": "r" + mid, "cwd": "/p",
                       "timestamp": "2026-10-28T10:00:00Z", "message": {"id": mid, "role": "assistant",
                       "model": "claude-opus-5-5", "usage": {"input_tokens": n, "output_tokens": 0}}})


def alive(pid: int) -> bool:
    """Present at all, a zombie included: the stopped command must be gone, reaped by the statusline itself."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def running(pid: int) -> bool | None:
    """Present and not a zombie: a process killed and never reaped (a container whose PID 1 reaps nothing) has ended.
    None when neither /proc nor `ps` can say (a sandbox that refuses `ps`): the caller does not judge that case."""
    if not alive(pid):
        return False
    try:
        return pathlib.Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        pass
    try:
        r = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True)
    except OSError:
        return None
    return r.returncode == 0 and not r.stdout.strip().startswith("Z")


def main() -> int:
    real_git = shutil.which("git")
    no_git = missing_tool("git", "build the repository the statusline reads")
    if no_git or not real_git:
        print(f"test-statusline NOT-EVALUABLE: {no_git}")
        return 2
    bad: list[str] = []
    slow = False
    no_ps = "no /proc, and `ps` cannot run here, so a zombie cannot be told from a running process: the two cases " \
            "that need it (a job left running survives a stop; a zombie reads as ended) were not judged here -- " \
            "CI's required `install-and-governance` job judges them on Linux, where /proc works"
    unjudged: set[str] = set()
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(os.path.realpath(tmp))
        proj, user, fake, log = base / "proj", base / "user", base / "bin", base / "calls.log"
        for d in (proj, user, fake):
            d.mkdir()
        slowgit = base / "slow-git"                                  # present: git takes 2 s, so a refresh is caught in it
        (fake / "git").write_text(f'#!/bin/sh\necho "git $*" >> "{log}"\n[ -f "{slowgit}" ] && sleep 2\n'
                                  f'exec "{real_git}" "$@"\n', encoding="utf-8")
        (fake / "gh").write_text(f'#!/bin/sh\necho "gh $*" >> "{log}"\nexit 1\n', encoding="utf-8")
        for f in fake.iterdir():
            f.chmod(0o755)
        git(proj, "init", "-q", "-b", "main")
        (proj / ".claude").mkdir()
        (proj / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")   # the fixture's own, never the project's
        (proj / "scripts").mkdir()
        shutil.copy(ROOT / "scripts" / "gate_stamp.py", proj / "scripts" / "gate_stamp.py")
        (proj / "docs" / "plans").mkdir(parents=True)
        (proj / "docs" / "project-brief.md").write_text("- **Working mode:** `light`\n", encoding="utf-8")
        (proj / "docs" / "plans" / "run-demo.md").write_text(
            "Mode: light\nStarted: 2026-10-28\nEnded: open\n\n## Waves\n\n| Wave | Branch | PR | Close record | Status |\n"
            "|---|---|---|---|---|\n| issue-7 | fix/issue-7-x | none | none | running |\n", encoding="utf-8")
        (proj / ".gitignore").write_text(".claude/last-check.log\n", encoding="utf-8")
        git(proj, "add", "-A")
        git(proj, "-c", "user.name=f", "-c", "user.email=f@x", "commit", "-qm", "base")
        git(proj, "switch", "-q", "-c", "fix/issue-7-x")
        head = git(proj, "rev-parse", "HEAD")
        gitdir = pathlib.Path(proj, git(proj, "rev-parse", "--git-dir"))
        (gitdir / f"devflow-gate-ok-{head}").write_text(head + "\n", encoding="utf-8")
        (proj / ".claude" / "last-check.log").write_text("check-fast: 2 leg(s)\n\ncheck-fast PASS in 3.0s -- x\n",
                                                          encoding="utf-8")
        transcript = base / "session.jsonl"
        transcript.write_text("\n".join([usage_line("m1", 12000), usage_line("m1", 12000)]) + "\n", encoding="utf-8")
        (base / "session" / "subagents").mkdir(parents=True)
        (base / "session" / "subagents" / "agent-a.jsonl").write_text(usage_line("m2", 345, True) + "\n", encoding="utf-8")

        counter = iter(range(1000))
        env = scrubbed_env({"CLAUDE_CONFIG_DIR": str(user), "HOME": str(base), "TMPDIR": str(base),
                            "PATH": os.pathsep.join([str(fake), os.environ.get("PATH", "")])})
        env.pop("DEVFLOW_STATUSLINE", None)

        def setup(personal: str | None, sid: str | None, payload: object) -> str:
            os.utime(proj / ".claude" / "last-check.log")           # "0m ago" holds on a slow, loaded run too
            settings = user / "settings.json"
            if personal is None:
                settings.unlink(missing_ok=True)
            else:
                settings.write_text(json.dumps({"statusLine": {"type": "command", "command": personal}}), encoding="utf-8")
            return payload if payload is not None else json.dumps({
                "session_id": sid or f"probe{next(counter):04d}-statusline", "transcript_path": str(transcript),
                "workspace": {"current_dir": str(proj), "project_dir": str(proj)},
                "context_window": {"used_percentage": 42.4}})

        def statusline(personal: str | None = None, sid: str | None = None, payload: object = None) -> tuple[float, str]:
            body = setup(personal, sid, payload)
            t0 = time.monotonic()
            r = subprocess.run([sys.executable, "-I", "-S", str(STATUSLINE)], input=body, capture_output=True,
                               text=True, env=env, cwd=proj, timeout=60)
            return time.monotonic() - t0, r.stdout if r.returncode == 0 else f"<exit {r.returncode}> {r.stderr}"

        def calls() -> list[str]:
            return log.read_text(encoding="utf-8").splitlines() if log.exists() else []

        seg = ("DevFlow light · fix/issue-7-x · run-demo: issue-7 · gate at HEAD · check-fast PASS 0m ago · ctx 42% "
               "· 12k tok")
        _, out = statusline()
        if out != seg + "\n":
            bad.append(f"  no personal statusline: wanted the segment alone\n    {seg}\n    got {out!r}")
        _, out = statusline("printf MINE")
        if out != f"MINE · {seg}\n":
            bad.append(f"  a personal statusline: wanted `MINE · <segment>`, got {out!r}")
        _, out = statusline("printf 'TOP\\nLAST'")
        if out != f"TOP\nLAST · {seg}\n":
            bad.append(f"  a two-row personal statusline: the segment belongs on its last row, got {out!r}")
        _, out = statusline("echo broken; exit 3")
        if out != seg + "\n":
            bad.append(f"  a personal statusline that fails is left out (as Claude Code shows nothing for it), got {out!r}")
        took, out = statusline("sleep 60")                      # left out at 3 s, never waited for: 30 s tells them apart
        if took > 30 or out != seg + "\n":
            bad.append(f"  a personal statusline that hangs: left out within its limit; took {took:.1f}s, got {out!r}")
        _, out = statusline(f"{sys.executable} -I -S {STATUSLINE}")
        if out.count("DevFlow") != 1:
            bad.append(f"  a personal statusline that is this one: DevFlow's segment once, got {out!r}")
        _, out = statusline(payload="{not json")
        if not out.startswith("DevFlow light · fix/issue-7-x"):
            bad.append(f"  a payload that is not JSON still shows DevFlow's segment, got {out!r}")

        # Git once per CACHE_S for a session, judged from the cache file the first refresh wrote: its entry is made
        # as fresh as can be, and a second refresh that ends within CACHE_S of that runs no git. Wall time between
        # the two refreshes decides nothing (a loaded machine once made the pair's time the verdict).
        cache_s = float(re.search(r"^CACHE_S = (\d+)", STATUSLINE.read_text(encoding="utf-8"), re.M).group(1))
        n0 = len(calls())
        statusline(sid="cache000-statusline")
        first = calls()[n0:]
        entry = base / "devflow-statusline-cache000-statusline.json"
        with transcript.open("a", encoding="utf-8") as fh:          # one more message, logged twice: counted once
            fh.write(usage_line("n0", 1000) + "\n" + usage_line("n0", 1000) + "\n")
        try:
            data = json.loads(entry.read_text(encoding="utf-8"))
            data["git"]["t"] = time.time()
            entry.write_text(json.dumps(data), encoding="utf-8")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            bad.append(f"  the first refresh left no git entry in its cache file {entry.name}: {exc!r}")
        t0 = time.monotonic()
        _, out = statusline(sid="cache000-statusline")
        took = time.monotonic() - t0
        second = calls()[n0 + len(first):]
        if not first:
            bad.append("  the first refresh of a session ran no git")
        elif second and took < cache_s - 0.5:
            bad.append(f"  a refresh with a fresh cache entry ran git anyway ({took:.1f}s): {second}")
        elif second:
            slow = True                                              # the refresh alone outran the cache time
        if "· 13k tok" not in out:
            bad.append(f"  one more message, logged twice, counts once: wanted `· 13k tok`, got {out!r}")

        # Claude Code stops a refresh in flight with SIGTERM: the owner's own command must go with it. Judged when
        # that command is seen alive just before the signal (its time limit has not killed it), whatever the load.
        pidfile, judged = base / "personal.pid", False
        for _ in range(3):
            pidfile.unlink(missing_ok=True)
            body = setup(f"echo $$ > '{pidfile}'; exec sleep 47", None, None)
            p = subprocess.Popen([sys.executable, "-I", "-S", str(STATUSLINE)], stdin=subprocess.PIPE,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, cwd=proj, text=True)
            p.stdin.write(body)
            p.stdin.close()
            t0, pid = time.monotonic(), None
            while pid is None and time.monotonic() - t0 < 20:
                try:
                    pid = int(pidfile.read_text(encoding="utf-8").strip())
                except (OSError, ValueError):
                    time.sleep(0.02)
            if pid is not None and alive(pid):
                p.send_signal(signal.SIGTERM)
                p.wait(timeout=30)
                gone = time.monotonic()
                # Gone, not a zombie: in CI's container PID 1 reaps nothing, so only the statusline reaping its own
                # child makes this pass there (here launchd or init reaps an orphan too).
                while alive(pid) and time.monotonic() - gone < 3:
                    time.sleep(0.05)
                if alive(pid):
                    os.kill(pid, signal.SIGKILL)
                    bad.append("  a refresh stopped with SIGTERM left the owner's statusline command running")
                judged = True
                break
            p.kill()
            p.wait(timeout=30)
            if pid is not None and alive(pid):
                os.kill(pid, signal.SIGKILL)
        slow = slow or not judged

        # The same stop, landing as the owner's command starts (#87): sent from inside Popen, before the statusline
        # holds its handle, so the window is hit on every run, never by the scheduler's luck. The command must go,
        # and the refresh must stop there (print nothing), not run on to its time limit. `sleep 48` is a start that
        # fails (OSError) after the stop: nothing to orphan, and the refresh still stops.
        racefile, wrapper = base / "race.pid", base / "stop-in-popen.py"
        wrapper.write_text(
            "import os, pathlib, runpy, signal, subprocess\n"
            "class Popen(subprocess.Popen):\n"
            "    def __init__(self, *a, **k):\n"
            "        cmd = list(a[0] if a else k.get('args') or [])[-1:]\n"
            "        if cmd == ['exec sleep 48']:\n"
            "            os.kill(os.getpid(), signal.SIGTERM)\n"
            f"            pathlib.Path({str(racefile)!r}).write_text('failed')\n"
            "            raise OSError('no shell')\n"
            "        super().__init__(*a, **k)\n"
            "        if cmd == ['exec sleep 47']:\n"
            f"            pathlib.Path({str(racefile)!r}).write_text(str(self.pid))\n"
            "            os.kill(os.getpid(), signal.SIGTERM)\n"
            "subprocess.Popen = Popen\n"
            f"runpy.run_path({str(STATUSLINE)!r}, run_name='__main__')\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "-I", "-S", str(wrapper)], input=setup("exec sleep 47", None, None),
                           capture_output=True, text=True, env=env, cwd=proj, timeout=60)
        try:
            pid = int(racefile.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pid = None
            bad.append(f"  the stop sent inside Popen never ran: the owner's command no longer starts there {r.stderr[-160:]!r}")
        gone = time.monotonic()
        while pid is not None and alive(pid) and time.monotonic() - gone < 3:   # the statusline reaps it: CI's PID 1
            time.sleep(0.05)                                                     # reaps nothing, launchd here does
        if pid is not None and alive(pid):
            os.kill(pid, signal.SIGKILL)
            bad.append("  a stop that landed as the owner's command started left that command running (#87)")
        elif pid is not None and r.stdout:
            bad.append(f"  a stop that landed as the owner's command started was lost: the refresh printed {r.stdout!r} (#87)")
        racefile.unlink(missing_ok=True)
        r = subprocess.run([sys.executable, "-I", "-S", str(wrapper)], input=setup("exec sleep 48", None, None),
                           capture_output=True, text=True, env=env, cwd=proj, timeout=60)
        if not racefile.is_file():
            bad.append(f"  the stop sent from a failing Popen never ran {r.stderr[-160:]!r}")
        elif r.stdout:
            bad.append(f"  a stop that landed as the owner's command failed to start was lost: the refresh printed {r.stdout!r}")

        # Stopped after the owner's command returned: what it left running in the background survives. The refresh
        # is caught in its segment (git takes 2 s here); judged when it was still running at the signal.
        childfile, judged = base / "child.pid", False
        slowgit.touch()
        for _ in range(3):
            childfile.unlink(missing_ok=True)
            body = setup(f"sleep 47 >/dev/null 2>&1 & echo $! > '{childfile}'; printf MINE", None, None)
            n = len(calls())
            p = subprocess.Popen([sys.executable, "-I", "-S", str(STATUSLINE)], stdin=subprocess.PIPE,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, cwd=proj, text=True)
            p.stdin.write(body)
            p.stdin.close()
            t0 = time.monotonic()
            while len(calls()) == n and p.poll() is None and time.monotonic() - t0 < 20:
                time.sleep(0.02)                                     # the segment's first git call: the command returned
            try:
                child = int(childfile.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                child = None
            if child is not None and len(calls()) > n and p.poll() is None:
                p.send_signal(signal.SIGTERM)
                p.wait(timeout=30)
                time.sleep(0.3)
                state = running(child)
                if state is None:
                    unjudged.add(no_ps)
                elif not state:
                    bad.append("  a refresh stopped after the owner's command returned killed the job it left running")
                if state is not False and alive(child):
                    os.kill(child, signal.SIGKILL)
                judged = True
                break
            p.kill()
            p.wait(timeout=30)
            if child is not None and alive(child):
                os.kill(child, signal.SIGKILL)
        slowgit.unlink()
        slow = slow or not judged

        # That probe reads a zombie as ended: in CI's container PID 1 reaps nothing, and a job the stop killed stays a
        # zombie that `kill -0` still finds -- it read as a job that survived (Linux CI, run 40866973552).
        z = subprocess.Popen(["true"])
        if hasattr(os, "waitid"):
            os.waitid(os.P_PID, z.pid, os.WEXITED | os.WNOWAIT)     # exited, not reaped: a zombie of ours
        else:
            time.sleep(0.5)
        state = running(z.pid)
        if state is None:
            unjudged.add(no_ps)
        elif state:
            bad.append("  a zombie reads as running: a job the stop killed and nobody reaped passes as one that survived")
        z.wait()

        everything = calls()
        if any(c.startswith("gh") for c in everything):
            bad.append(f"  gh is never called: {[c for c in everything if c.startswith('gh')]}")
        locking = [c for c in everything if c.startswith("git ") and not c.startswith("git --no-optional-locks ")]
        if not everything or locking:
            bad.append(f"  every git call carries --no-optional-locks; without it: {locking[:4]}")

        # The gate stamp is at HEAD only while the tree is that commit.
        (proj / "scratch.txt").write_text("x\n", encoding="utf-8")
        _, out = statusline()
        if "gate not at HEAD" not in out:
            bad.append(f"  an uncommitted file: the gate stamp is no longer at HEAD, got {out!r}")

    print("\n".join(bad))
    if slow:
        unjudged.add("on this loaded machine a refresh outran the git cache time, or the owner's command never ran "
                     "inside its time limit, so that case was not judged")
    if unjudged and not bad:
        print(f"test-statusline NOT-EVALUABLE: {'; '.join(sorted(unjudged))}; every other case passed")
        return 2
    # A failing run names its first finding on the last line: a nested run (test-delivered-tree) shows only that.
    print(f"test-statusline FAIL -- {len(bad)} finding(s), first: {bad[0].strip()[:150]}" if bad else
          "test-statusline PASS: appended to the owner's own statusline, git cached, no gh, tokens counted once")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
