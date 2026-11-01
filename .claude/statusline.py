#!/usr/bin/env python3
"""DevFlow's statusline segment, appended to the owner's personal statusline (v7.3, A22, owner ruling 2026-10-28).

Claude Code runs one `statusLine` command, and project settings win over the user's. So DevFlow's command runs
the personal one itself -- `statusLine.command` in `$CLAUDE_CONFIG_DIR/settings.json`, else
`~/.claude/settings.json` -- with the same JSON on stdin, and appends its segment to that line's last row:

    <personal> · DevFlow light · fix/issue-12-x · run-demo: issue-12 · gate at HEAD · check-fast PASS 3m ago · ctx 42% · 1.2M tok

the working mode, the branch, the open run and its running wave (or a wave branch's wave), whether the gate stamp
is at HEAD, the last post-edit check-fast and its age, the context window used, and the session's tokens: its
transcript and its subagents', by scripts/cost_ledger.py's rules -- tokens, never USD.

It reads files and makes no network call. Git runs at most once every CACHE_S seconds for a session (its answers
are cached in the temp directory: an uncached statusline left orphan git processes in ruflo), always with
`--no-optional-locks`, so it never holds `.git/index.lock` against the session's own git; transcripts are read
from where the last refresh stopped. A personal statusline that fails, or runs past PERSONAL_S seconds, is left
out, and when Claude Code stops a refresh in flight the personal command is stopped with it; a DevFlow part that
cannot be read is left out: nothing here blanks the line. Run by a personal statusline that is this one, it
prints nothing.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_S = 5
PERSONAL_S = 3
CHUNK = 32 << 20        # transcript bytes read per file and refresh: a resumed long session catches up over refreshes
SEP = " · "


def personal(payload: bytes) -> str:
    config = os.environ.get("CLAUDE_CONFIG_DIR")
    path = (Path(config).expanduser() if config else Path.home() / ".claude") / "settings.json"
    try:
        line = json.loads(path.read_text(encoding="utf-8")).get("statusLine")
    except (OSError, ValueError, AttributeError):
        return ""
    command = line.get("command") if isinstance(line, dict) and line.get("type", "command") == "command" else None
    shell = shutil.which("bash") or shutil.which("sh")
    if not isinstance(command, str) or not command.strip() or not shell:
        return ""
    p, asked = None, []

    def kill() -> None:
        try:
            os.killpg(p.pid, signal.SIGKILL)       # the whole group: a script's own children too
        except (AttributeError, OSError):
            p.kill()

    def stopped(*_: object) -> None:               # Claude Code stops a refresh in flight: the owner's command goes too
        if p is None:                              # Popen has not returned it yet: acted on the moment it does
            asked.append(1)
            return
        kill()
        # Reaped here, not left to PID 1: in a container whose PID 1 reaps nothing (CI's `tail -f /dev/null`),
        # an unreaped child stays a zombie for the container's life -- one per stopped refresh.
        end = time.monotonic() + 5               # SIGKILL ends it; a loaded machine may take its time
        while time.monotonic() < end:
            try:
                if os.waitpid(p.pid, os.WNOHANG)[0]:
                    break
            except (AttributeError, OSError):          # reaped already, or no waitpid (Windows): nothing to collect
                break
            time.sleep(0.01)
        os._exit(0)

    # From before the command starts, or a stop as it starts kills this statusline and orphans the command, in its
    # own session (#87); only while it runs: once it is reaped, a stop ends this statusline alone, and a background
    # job the command left running (a cache refresher) lives on (v7.3 review, M5).
    before = {getattr(signal, n): signal.signal(getattr(signal, n), stopped)
              for n in ("SIGTERM", "SIGHUP", "SIGINT") if hasattr(signal, n)}
    try:
        try:
            p = subprocess.Popen([shell, "-c", command], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, env=dict(os.environ, DEVFLOW_STATUSLINE="1"),
                                 start_new_session=True)
        except OSError:                            # nothing started, nothing to orphan
            if asked:                              # but stopped all the same: no refresh printed
                os._exit(0)
            return ""
        if asked:
            stopped()
        out, _ = p.communicate(payload, timeout=PERSONAL_S)
    except subprocess.TimeoutExpired:
        kill()
        p.communicate()
        return ""
    finally:
        for sig, handler in before.items():
            signal.signal(sig, handler)
    return out.decode("utf-8", "replace").rstrip("\r\n") if p.returncode == 0 else ""


def cache_file(sid: str) -> Path | None:
    return Path(tempfile.gettempdir()) / f"devflow-statusline-{sid}.json" \
        if re.fullmatch(r"[A-Za-z0-9-]{8,64}", sid) else None


def load(path: Path | None) -> dict:
    try:
        if path is None or (hasattr(os, "getuid") and path.stat().st_uid != os.getuid()):
            return {}                              # another user's file in a shared temp directory: not ours
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save(path: Path | None, data: dict) -> None:
    if path is None:
        return
    try:
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".devflow-statusline-")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        os.replace(tmp, path)
    except OSError:
        pass


def git_state(cwd: str, cache: dict) -> dict:
    """The work tree, git dir, branch, HEAD and whether anything is uncommitted: from the cache while fresh."""
    g = cache.get("git")
    if isinstance(g, dict) and g.get("cwd") == cwd and 0 <= time.time() - g.get("t", 0) < CACHE_S:
        return g

    # `--no-optional-locks`: a status that took `.git/index.lock` failed the session's own `git add`, and one
    # stopped by the timeout left the lock behind (v7.3 review, B2); Claude Code's own background git does the same.
    def git(*args: str) -> str | None:
        try:
            r = subprocess.run(["git", "--no-optional-locks", *args], cwd=cwd, capture_output=True, encoding="utf-8",
                               errors="replace", timeout=5)
        except (OSError, subprocess.SubprocessError):
            return None
        return r.stdout if r.returncode == 0 else None

    g = {"t": time.time(), "cwd": cwd}
    where = git("rev-parse", "--show-toplevel", "--git-dir")
    status = git("status", "--porcelain=v2", "--branch", "--untracked-files=normal") if where else None
    if where and status is not None and len(where.splitlines()) == 2:
        top, gitdir = where.splitlines()
        g.update(top=top, gitdir=str(Path(cwd, gitdir)), dirty=sum(not ln.startswith("#") for ln in status.splitlines()))
        for ln in status.splitlines():
            if ln.startswith("# branch.oid "):
                g["oid"] = ln.split()[-1]
            elif ln.startswith("# branch.head "):
                g["branch"] = ln.split(" ", 2)[-1]
    cache["git"] = g
    return g


def helpers():
    sys.path.insert(0, str(ROOT / "scripts"))
    import brief_fields, cost_ledger, doctor  # noqa: E401, PLC0415
    return brief_fields, cost_ledger, doctor


def tokens(transcript: object, cache: dict, cost_ledger) -> tuple[int, bool] | None:
    """(the session's tokens so far, whether every transcript is read to its end)."""
    if not isinstance(transcript, str) or not transcript.endswith(".jsonl") or not os.path.isfile(transcript):
        return None
    main = Path(transcript)
    paths = [main] + sorted(main.with_suffix("").glob("subagents/*.jsonl"))
    seen = cache.setdefault("tokens", {})
    total, done = 0, True
    for p in paths:
        offset, count, keys = seen.get(str(p), [0, 0, []])
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size < offset:                          # rewritten: count it again
            offset, count, keys = 0, 0, []
        done = done and size - offset <= CHUNK     # this read reaches the end (bar one unfinished line)
        offset, more, keys = cost_ledger.scan(p, offset, keys, CHUNK)
        seen[str(p)] = [offset, count + more, keys]
        total += count + more
    return total, done


def compact(n: int) -> str:
    return f"{n / 1e6:.1f}M" if n >= 1e6 else f"{n / 1e3:.0f}k" if n >= 1e3 else str(n)


def check_fast(tree: Path) -> str | None:
    log = tree / ".claude" / "last-check.log"
    try:
        with open(log, "rb") as fh:
            fh.seek(max(0, log.stat().st_size - 4096))
            tail = fh.read().decode("utf-8", "replace")
        age = time.time() - log.stat().st_mtime
    except OSError:
        return None
    found = re.findall(r"^check-fast (PASS|FAIL|CANNOT RUN)", tail, re.M)
    if not found:
        return None
    ago = f"{int(age // 86400)}d" if age >= 86400 else f"{int(age // 3600)}h" if age >= 3600 else f"{int(age // 60)}m"
    return f"check-fast {found[-1]} {ago} ago"


def project(cwd: str, top: object) -> Path:
    """The DevFlow tree the session works in: the nearest directory from `cwd` up to its work tree's top that
    holds `.claude/settings.json` (a project in a subdirectory, a work tree under .claude/worktrees/), else ROOT.
    Never above the top: the home directory holds a `.claude/settings.json` too."""
    if isinstance(top, str) and top:
        here, stop = Path(cwd).resolve(), Path(top).resolve()
        for d in (here, *here.parents):
            if (d / ".claude" / "settings.json").is_file():
                return d
            if d == stop:
                break
    return ROOT


def segment(data: dict, cache: dict) -> str:
    ws = data.get("workspace") if isinstance(data.get("workspace"), dict) else {}
    cwd = str(ws.get("current_dir") or data.get("cwd") or os.getcwd())
    g = git_state(cwd, cache)
    tree = project(cwd, g.get("top"))
    parts = ["DevFlow"]
    try:
        brief_fields, cost_ledger, doctor = helpers()
    except ImportError:                            # a tree without DevFlow's scripts: the workshop root
        brief_fields = cost_ledger = doctor = None
    if brief_fields:
        parts[0] += " " + brief_fields.mode(tree)
    branch = g.get("branch")
    if branch:
        parts.append(branch)
    runs = doctor.open_runs(tree) if doctor else []
    if runs:
        waves = [w for w, _ in doctor.running(runs[0])]
        parts.append(runs[0].stem + (": " + ", ".join(waves) if waves else ""))
    elif branch and re.fullmatch(r"wave/m\d+-w\d+", branch):
        parts.append("wave " + branch[len("wave/"):])
    if g.get("oid") and (tree / "scripts" / "gate_stamp.py").is_file():
        stamp = Path(g["gitdir"]) / f"devflow-gate-ok-{g['oid']}"
        parts.append("gate at HEAD" if stamp.is_file() and not g.get("dirty") else "gate not at HEAD")
    fast = check_fast(tree)
    if fast:
        parts.append(fast)
    ctx = data.get("context_window") if isinstance(data.get("context_window"), dict) else {}
    pct = ctx.get("used_percentage")
    if isinstance(pct, (int, float)) and not isinstance(pct, bool):
        parts.append(f"ctx {round(pct)}%")
    got = tokens(data.get("transcript_path"), cache, cost_ledger) if cost_ledger else None
    if got is not None:
        parts.append(f"{compact(got[0])}{'' if got[1] else '+'} tok")
    return SEP.join(parts)


def main() -> int:
    if os.environ.get("DEVFLOW_STATUSLINE"):
        return 0                                   # run by a personal statusline that is this one
    payload = sys.stdin.buffer.read()
    try:
        data = json.loads(payload or b"{}")
        data = data if isinstance(data, dict) else {}
    except ValueError:
        data = {}
    mine = personal(payload)
    try:
        path = cache_file(str(data.get("session_id") or ""))
        cache = load(path)
        seg = segment(data, cache)
        save(path, cache)
    except Exception:  # noqa: BLE001 -- the owner's own line is shown whatever DevFlow's part does
        seg = ""
    rows = mine.split("\n") if mine else []
    if seg:
        rows[-1:] = [rows[-1] + SEP + seg] if rows else [seg]
    sys.stdout.buffer.write(("\n".join(rows) + "\n").encode("utf-8") if rows else b"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
