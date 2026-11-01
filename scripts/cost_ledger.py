#!/usr/bin/env python3
"""`make cost` and `make cost-advise`: what this project's Claude Code sessions spent, in TOKENS only.

ADVISORY, never a gate leg (owner ruling, 2026-10-28): tokens, never USD. It reads the transcripts Claude
Code already keeps on this machine and sends nothing anywhere. `Cost:` is the line the close-wave checklist,
the run file and the closure report carry.

WHAT IT READS. Claude Code writes one transcript per session, `<config>/projects/<slug>/<session>.jsonl`, and
one per subagent below `<session>/subagents/`. `<config>` is `$CLAUDE_CONFIG_DIR`, else `~/.claude`; `<slug>`
is the directory the session started in, every character but a letter or a digit replaced by `-`; past 200
characters Claude Code cuts it to 200 and appends `-<hash>`, a hash this script does not recompute: such a
directory is the root's when its session's transcript starts in the root, the test Claude Code applies itself.
A session started at the project's root is the project's, every row of it, wherever its shell moved later. A session
started inside the project (a work tree under `.claude/worktrees/`) has a longer slug with the same start; so
does a sibling, `/a/proj-old` beside `/a/proj`. In such a directory a row counts only when its `cwd` is the
project or a directory inside it.

THE COUNTING RULES (from ruflo's cost ledger, each a way a tracker double-counts):
  * one assistant message is logged once per content block: rows are de-duplicated by message id + request id;
  * input, cache writes (5-minute and 1-hour apart), cache reads and output stay apart, and the total is their
    sum (the v7.3 run's measurement plan); a write with no TTL split counts as a 5-minute write;
  * a subagent's row (`isSidechain`) counts, and is tagged; a `<synthetic>` message made no model call.
THE WINDOW: `--from` / `--to` take a date (YYYY-MM-DD, UTC), an ISO time, or a git revision (its committer
time). One that is none of these refuses (exit 2): a window nobody can read must not count everything.

THE ADVICE (`--advise`), three rules, each in tokens, each fired only past its line:
  context-bloat       a transcript of 30 or more turns that re-read over 400k cached tokens a turn on average
  subagents-top-tier  over 1M subagent tokens on a top-tier model (TOP_TIER)
  ttl-1h              over 1M tokens written to the 1-hour cache and read back less than twice: a 1-hour write
                      costs twice the input price, a 5-minute one 1.25 times, so it pays back only when re-read

    python3 scripts/cost_ledger.py [--advise] [--from X] [--to Y] [--dir <projects dir>] [--root <project>]
Exit: 0 (advisory) · 2 a window that cannot be read.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

#: The model families above Sonnet in Anthropic's line-up (2026-10): a subagent on one of these is "top tier".
#: A named list with its reason (AGENTS.md §3.5): the families cannot be derived from a transcript; a new
#: top-tier family is added here.
TOP_TIER = ("fable", "opus")
#: Claude Code's longest slug before it cuts one and appends a hash of the path (2.1.314).
CUT = 200
BLOAT_TURNS, BLOAT_PER_TURN = 30, 400_000
TOP_TIER_FLOOR = 1_000_000
TTL_FLOOR, TTL_PAYBACK = 1_000_000, 2.0
BUCKETS = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")


def slug(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def row(line: str) -> tuple[str, dict] | None:
    """(the de-duplication key, the row) for one transcript line that records a model call, else None."""
    if '"usage"' not in line:
        return None
    try:
        d = json.loads(line)
    except ValueError:
        return None
    m = d.get("message") if isinstance(d, dict) else None
    u = m.get("usage") if isinstance(m, dict) else None
    if not isinstance(u, dict) or m.get("role") != "assistant" or not m.get("model") or m.get("model") == "<synthetic>":
        return None

    def n(v: object) -> int:
        return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else 0

    split = u.get("cache_creation")
    written = n(u.get("cache_creation_input_tokens"))
    w1 = n(split.get("ephemeral_1h_input_tokens")) if isinstance(split, dict) else 0
    w5 = n(split.get("ephemeral_5m_input_tokens")) if isinstance(split, dict) else written
    r = {"input": n(u.get("input_tokens")), "cache_write_5m": w5, "cache_write_1h": w1,
         "cache_read": n(u.get("cache_read_input_tokens")), "output": n(u.get("output_tokens")),
         "model": str(m.get("model")), "sidechain": d.get("isSidechain") is True,
         "cwd": d.get("cwd") if isinstance(d.get("cwd"), str) else None, "ts": stamp(d.get("timestamp"))}
    return f"{m.get('id') or d.get('uuid')}|{d.get('requestId') or ''}", r


def total(r: dict) -> int:
    return sum(r[b] for b in BUCKETS)


def stamp(value: object) -> float | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def when(text: str, root: Path) -> float:
    """A window edge: a date, an ISO time, or a git revision. ValueError when it is none of these."""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return dt.datetime.fromisoformat(text).replace(tzinfo=dt.timezone.utc).timestamp()
    t = stamp(text) if re.match(r"\d{4}-\d{2}-\d{2}T", text) else None
    if t is not None:
        return t
    # Only `rev-parse --verify` reads the text, suffixed `^{commit}`: `--output=<file>` names no commit, and is
    # never an option (`git log <text>` would have written the file); `git show` gets the 40-digit answer.
    try:
        sha = subprocess.run(["git", "rev-parse", "--verify", "-q", f"{text}^{{commit}}"],
                             cwd=root, capture_output=True, text=True).stdout.strip()
        r = subprocess.run(["git", "show", "-s", "--format=%ct", sha], cwd=root, capture_output=True,
                           text=True) if re.fullmatch(r"[0-9a-f]{40,64}", sha) else None
    except OSError:                                # no git: only a date or a time can be read
        r = None
    if r is not None and r.returncode == 0 and r.stdout.strip().isdigit():
        return float(r.stdout.strip())
    raise ValueError(f"`{text}` is not a date (YYYY-MM-DD), an ISO time or a git revision here")


def files(projects: Path, root: Path, since: float | None) -> list[Path]:
    """Every transcript under a directory whose name starts with the project's slug, newest change >= since."""
    starts = {slug(str(root))[:CUT], slug(os.path.realpath(root))[:CUT]}
    out: list[Path] = []
    try:
        dirs = [d for d in projects.iterdir() if d.is_dir() and any(d.name.startswith(s) for s in starts)]
    except OSError:
        return out
    for d in sorted(dirs):
        for f in sorted(d.rglob("*.jsonl")):
            try:
                if len(f.relative_to(d).parts) <= 3 and (since is None or f.stat().st_mtime >= since):
                    out.append(f)
            except OSError:
                continue
    return out


def first_cwd(path: Path) -> str | None:
    """The `cwd` of a transcript's first row that has one: where its session started."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"cwd"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict) and isinstance(d.get("cwd"), str):
                    return d["cwd"]
    except OSError:
        pass
    return None


def at_root(p: Path, projects: Path | None, roots: set[str], memo: dict[Path, bool]) -> bool:
    """Whether the session a transcript belongs to started at the root. A directory named by the whole slug is the
    root's; one named by a shortened slug is the root's when its session's own transcript starts in the root. Anything
    else, an unreadable transcript included, is not: its rows then count only where they ran inside the project."""
    if projects is None or not p.is_relative_to(projects):
        return False
    parts = p.relative_to(projects).parts
    names = {slug(r) for r in roots}
    if parts[0] in names:
        return True
    if not any(len(n) > CUT and parts[0].startswith(n[:CUT] + "-") for n in names):
        return False
    session = projects / parts[0] / (parts[1] if len(parts) == 2 else parts[1] + ".jsonl")
    if session not in memo:
        cwd = first_cwd(session)
        memo[session] = cwd is not None and os.path.normpath(cwd) in roots   # exact: a slug conflates punctuation
    return memo[session]


def inside(cwd: str | None, roots: set[str]) -> bool:
    return cwd is not None and any(cwd == r or cwd.startswith(r.rstrip("/") + "/") for r in roots)


def ledger(paths: list[Path], root: Path, since: float | None, until: float | None,
           projects: Path | None = None) -> list[tuple[Path, dict]]:
    roots = {str(root), os.path.realpath(root)}
    # A session started at the root: all of it. Started elsewhere under the slug's start: the rows inside the project.
    memo: dict[Path, bool] = {}
    seen: set[str] = set()
    out: list[tuple[Path, dict]] = []
    for p in paths:
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        home = at_root(p, projects, roots, memo)
        for line in lines:
            got = row(line)
            if got is None or got[0] in seen:
                continue
            key, r = got
            if not home and not inside(r["cwd"], roots):
                continue
            if r["ts"] is None and (since is not None or until is not None):
                continue
            if (since is not None and r["ts"] < since) or (until is not None and r["ts"] > until):
                continue
            seen.add(key)
            out.append((p, r))
    return out


def scan(path: Path, offset: int, recent: list[str], limit: int = -1) -> tuple[int, int, list[str]]:
    """The statusline's incremental read: (new offset, tokens in the complete lines after `offset`, the last
    keys seen). Only whole lines are read, at most `limit` bytes; a message split across two reads counts once."""
    try:
        with open(path, "rb") as fh:
            fh.seek(offset)
            data = fh.read(limit)
    except OSError:
        return offset, 0, recent
    end = data.rfind(b"\n") + 1
    tokens, keys = 0, list(recent)
    for line in data[:end].decode("utf-8", "replace").splitlines():
        got = row(line)
        if got is None or got[0] in keys:
            continue
        keys.append(got[0])
        tokens += total(got[1])
    return offset + end, tokens, keys[-64:]


def fmt(n: int) -> str:
    return f"{n:,}"


def report(rows: list[tuple[Path, dict]]) -> str:
    sums = {b: sum(r[b] for _, r in rows) for b in BUCKETS}
    side = sum(total(r) for _, r in rows if r["sidechain"])
    sessions = len({p for p, r in rows if not r["sidechain"] and "subagents" not in p.parts})
    return (f"Cost: {fmt(sum(sums.values()))} tokens -- input {fmt(sums['input'])}, cache write "
            f"{fmt(sums['cache_write_5m'] + sums['cache_write_1h'])} (1h {fmt(sums['cache_write_1h'])}), cache read "
            f"{fmt(sums['cache_read'])}, output {fmt(sums['output'])}; subagents {fmt(side)}; {sessions} session(s)")


def advise(rows: list[tuple[Path, dict]]) -> list[str]:
    out: list[str] = []
    per: dict[Path, list[int]] = {}
    for p, r in rows:
        per.setdefault(p, []).append(r["cache_read"])
    bloated = sorted(((sum(v) // len(v), len(v), p) for p, v in per.items()
                      if len(v) >= BLOAT_TURNS and sum(v) / len(v) > BLOAT_PER_TURN), reverse=True)
    if bloated:
        shown = "; ".join(f"{p.stem[:14]} {avg // 1000}k a turn over {n} turns" for avg, n, p in bloated[:3])
        out.append(f"- context-bloat: {len(bloated)} transcript(s) re-read over {BLOAT_PER_TURN // 1000}k cached "
                   f"tokens a turn across {BLOAT_TURNS}+ turns ({shown}) -- /compact at a wave boundary, or start a "
                   "fresh session for the next task (AGENTS.md §4)")
    top: dict[str, int] = {}
    for _, r in rows:
        if r["sidechain"] and any(t in r["model"].lower() for t in TOP_TIER):
            top[r["model"]] = top.get(r["model"], 0) + total(r)
    for model, n in sorted(top.items()):
        if n > TOP_TIER_FLOOR:
            name = re.sub(r"[^A-Za-z0-9._:-]", "?", model)[:40]
            out.append(f"- subagents-top-tier: {fmt(n)} subagent tokens ran on {name} -- a reviewer may run on a "
                       "smaller model (`model:` in .claude/agents/*.md; setup question 12)")
    w1 = sum(r["cache_write_1h"] for _, r in rows)
    back = sum(r["cache_read"] for _, r in rows if r["cache_write_1h"])
    if w1 > TTL_FLOOR and back / w1 < TTL_PAYBACK:
        out.append(f"- ttl-1h: {fmt(w1)} tokens written to the 1-hour cache were read back {back / w1:.1f}x, under "
                   f"the {TTL_PAYBACK:.0f}x a 1-hour write needs -- `\"5m\"` in subagentPromptCacheTtl or "
                   "promptCacheTtl (settings) suits short sessions")
    return out


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")
    ap = argparse.ArgumentParser(prog="cost_ledger", description="tokens this project's sessions spent")
    ap.add_argument("--advise", action="store_true")
    ap.add_argument("--from", dest="since")
    ap.add_argument("--to", dest="until")
    ap.add_argument("--dir")
    ap.add_argument("--root", default=".")
    a = ap.parse_args(argv)
    root = Path(a.root).absolute()
    projects = Path(a.dir).expanduser() if a.dir else \
        Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude").expanduser() / "projects"
    try:
        since = when(a.since, root) if a.since else None
        until = when(a.until, root) if a.until else None
    except ValueError as exc:
        print(f"cost CANNOT RUN: {exc}")
        return 2
    paths = files(projects, root, since)
    rows = ledger(paths, root, since, until, projects)
    span = (f"{a.since or 'the first row'} .. {a.until or 'now'}")
    print(f"cost: {len(paths)} transcript file(s) for {root} under {projects}, {span} (tokens only, advisory)")
    if a.advise:
        found = advise(rows)
        print("\n".join(found) if found else "cost-advise: no rule fired")
    else:
        print(report(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
