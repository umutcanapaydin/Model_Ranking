#!/usr/bin/env python3
"""`make cost` counts a project's transcript tokens by the ledger's rules, and `cost-advise` fires each rule only past its line.

WHY (v7.3, A21; the owner's ruling of 2026-10-28: tokens only, never USD, advisory, never a gate leg). A field
release's reviews spent about 216M tokens nobody could attribute. Each counting rule is a way a tracker
double-counts or misses, so each has a case: a message logged once per content block counts once (message
id + request id); a `<synthetic>` message made no call; a subagent's row counts and is tagged; a session started
at the root counts whole, wherever its shell moved; one started in a work tree counts inside the project; a sibling
directory that only shares the slug's start does not; the same at a root whose slug Claude Code cuts at 200
characters and suffixes with a hash (#72: a 199-character temp path made every fixture root one); a window
by date, by ISO time or by git revision; a window that is none of these refuses (exit 2) rather than counting
everything, `--output=<file>` included. Each advice rule is proved on both sides of its line: 30 turns over
400k cached tokens a turn, subagent tokens over 1M on a top-tier model, 1-hour writes over 1M read back
under twice. And `cost` is reachable from neither `make gate` nor `make check`.

The transcripts are fixtures under a throwaway projects directory (`--dir`): no real transcript is read.

Exit: 0 every case behaves - 1 one does not.
"""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "cost_ledger.py"


def slug(p: str) -> str:
    """Claude Code's directory for a session started at `p` (2.1.314): each character but a letter or a digit becomes
    `-`, and a name over 200 characters is cut to 200 with `-<hash of the path>` appended. Claude Code finds such a
    directory by that 200-character start and the cwd its transcripts begin with, never by recomputing the hash, so
    the fixture's hash is its own."""
    s = re.sub(r"[^A-Za-z0-9]", "-", p)
    return s if len(s) <= 200 else f"{s[:200]}-{hashlib.sha256(p.encode()).hexdigest()[:7]}"


def sessions(p: str, projects: pathlib.Path) -> None:
    """The counting fixture for a project at `p`: what the ledger must count is 31,636 tokens, 30,636 since 10-27."""
    a = line("m1", "r1", {"input_tokens": 10, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 1000,
                         "output_tokens": 5, "cache_creation": {"ephemeral_1h_input_tokens": 60,
                                                                "ephemeral_5m_input_tokens": 40}}, p)
    write(projects / slug(p) / "s1.jsonl", [
        a, a,                                                        # one message, two content blocks: once
        line("m2", "r2", {"input_tokens": 1, "cache_read_input_tokens": 2000, "output_tokens": 7}, p),
        line("m0", "r0", {"input_tokens": 999}, p, model="<synthetic>"),     # no model call
        line("m3", "r3", {"input_tokens": 1000}, p, ts="2026-10-20T10:00:00Z"),   # before the window
        line("m4", "r4", {"input_tokens": 20000}, "/elsewhere"),      # started here, then moved: still ours
        "{not json",
    ])
    write(projects / slug(p) / "s1" / "subagents" / "agent-a.jsonl", [
        line("m5", "r5", {"input_tokens": 3, "cache_read_input_tokens": 500, "output_tokens": 2}, p, side=True),
        line("m10", "r10", {"input_tokens": 7000}, "/elsewhere", side=True)])   # its session started here: ours
    write(projects / slug(p + "/.claude/worktrees/w1") / "s2.jsonl", [
        line("m6", "r6", {"input_tokens": 4, "output_tokens": 4}, p + "/.claude/worktrees/w1"),
        line("m8", "r8", {"input_tokens": 66666}, "/elsewhere")])    # started in a work tree, outside it: not ours
    write(projects / slug(p + "-old") / "s3.jsonl", [
        line("m7", "r7", {"input_tokens": 55555}, p + "-old")])   # shares the slug's start, not the place


def line(mid: str, rid: str, usage: dict, cwd: str, ts: str = "2026-10-28T10:00:00.000Z",
         model: str = "claude-opus-5-5", side: bool = False) -> str:
    u = {"input_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0, **usage}
    return json.dumps({"type": "assistant", "isSidechain": side, "requestId": rid, "cwd": cwd, "timestamp": ts,
                       "sessionId": "s", "message": {"id": mid, "role": "assistant", "model": model, "usage": u}})


def write(path: pathlib.Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(proj: pathlib.Path, projects: pathlib.Path, *args: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(proj), "--dir", str(projects), *args],
                       cwd=proj, capture_output=True, text=True, env=scrubbed_env())
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    bad: list[str] = []

    def case(name: str, got: tuple[int, str], rc: int, want: tuple[str, ...] = (), absent: tuple[str, ...] = ()):
        code, out = got
        if code != rc or any(w not in out for w in want) or any(a in out for a in absent):
            bad.append(f"  {name}: exit {code} (wanted {rc}); wanted {list(want)}, forbidden {list(absent)}\n"
                       + "\n".join(f"    {ln}" for ln in out.splitlines()))

    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(os.path.realpath(tmp))
        proj, projects = base / "proj", base / "projects"
        proj.mkdir()
        p = str(proj)
        sessions(p, projects)

        case("every row once: duplicates and synthetic out, a sibling's rows and a work tree's outside it too",
             run(proj, projects), 0,
             ("Cost: 31,636 tokens", "input 28,018", "cache write 100 (1h 60)", "cache read 3,500", "output 18",
              "subagents 7,505", "2 session(s)", "tokens only"), ("66,666", "55,555"))
        case("a window by date", run(proj, projects, "--from", "2026-10-27"), 0, ("Cost: 30,636 tokens",))
        # A root whose slug is over 200 characters, wherever the temp directory lives: the directories of its own
        # sessions, its work tree's and its sibling's share one 200-character start and differ only by the hash.
        far = base / ("l" * 120) / ("m" * 120) / "proj"
        far.mkdir(parents=True)
        far_projects = base / "far-projects"
        sessions(str(far), far_projects)
        # Another project whose path differs from the root's only in punctuation: the same shortened slug, its own hash.
        twin = str(far.parent) + "-proj"
        write(far_projects / slug(twin) / "s4.jsonl", [line("m9", "r9", {"input_tokens": 44444}, twin)])
        case("a root past Claude Code's 200-character cut: the same rows, by the cwd each session starts in",
             run(far, far_projects), 0, ("Cost: 31,636 tokens", "input 28,018", "subagents 7,505", "2 session(s)"),
             ("66,666", "55,555", "44,444"))
        case("... and its window by date", run(far, far_projects, "--from", "2026-10-27"), 0, ("Cost: 30,636 tokens",))
        case("a window by ISO time, both edges", run(proj, projects, "--from", "2026-10-20T00:00:00Z",
                                                     "--to", "2026-10-21T00:00:00Z"), 0, ("Cost: 1,000 tokens",))
        env = scrubbed_env({"GIT_COMMITTER_DATE": "2026-10-27T00:00:00Z", "GIT_AUTHOR_DATE": "2026-10-27T00:00:00Z"})
        for cmd in (["git", "init", "-q"], ["git", "-c", "user.name=f", "-c", "user.email=f@x", "commit", "-q",
                                             "--allow-empty", "-m", "base"]):
            subprocess.run(cmd, cwd=proj, capture_output=True, env=env, check=True)
        case("a window by git revision: its committer time", run(proj, projects, "--from", "HEAD"), 0,
             ("Cost: 30,636 tokens",))
        case("a window that is no date, time or revision refuses", run(proj, projects, "--from", "last-tuesday"), 2,
             ("cost CANNOT RUN",), ("Cost:",))
        case("an option-shaped window is a revision name, never an option",
             run(proj, projects, f"--from=--output={base / 'written'}"), 2, ("cost CANNOT RUN",))
        if (base / "written").exists():
            bad.append("  an option-shaped window wrote a file: git read it as an option")

        # The advice: each rule just past its line fires; just short of it, it stays quiet.
        def advice(over: bool) -> tuple[int, str]:
            d = base / ("over" if over else "under")
            q = str(proj)
            turns = 30 if over else 29
            write(d / slug(q) / "bloat.jsonl", [line(f"b{i}", f"rb{i}", {"cache_read_input_tokens": 500_000}, q)
                                                for i in range(turns)])
            write(d / slug(q) / "edge.jsonl", [line(f"e{i}", f"re{i}", {"cache_read_input_tokens": 400_000}, q)
                                               for i in range(30)])           # exactly 400k a turn: not over
            write(d / slug(q) / "b" / "subagents" / "agent-x.jsonl", [
                line("t1", "rt1", {"output_tokens": 1_000_001 if over else 1_000_000}, q, side=True),
                line("t2", "rt2", {"output_tokens": 5_000_000}, q, model="claude-sonnet-5-5", side=True)])
            write(d / slug(q) / "ttl.jsonl", [line("w1", "rw1", {
                "cache_creation_input_tokens": 2_000_000, "cache_read_input_tokens": 3_000_000 if over else 4_000_000,
                "cache_creation": {"ephemeral_1h_input_tokens": 2_000_000, "ephemeral_5m_input_tokens": 0}}, q)])
            return run(proj, d, "--advise")

        case("advice past every line: all three rules", advice(True), 0,
             ("context-bloat: 1 transcript(s)", "bloat", "subagents-top-tier: 1,000,001 subagent tokens ran on "
              "claude-opus-5-5", "ttl-1h: 2,000,000 tokens", "read back 1.5x"), ("sonnet",))
        case("advice short of every line: quiet", advice(False), 0, ("cost-advise: no rule fired",),
             ("context-bloat", "subagents-top-tier", "ttl-1h"))

    # Advisory: no leg of the gate or of check reaches it.
    mk = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("gate", "check"):
        m = re.search(rf"^{target}:([^#\n]*)", mk, re.M)
        if not m or {"cost", "cost-advise"} & set(m.group(1).split()):
            bad.append(f"  `make {target}` must exist and must not run cost or cost-advise")
    for target, flag in (("cost", ""), ("cost-advise", "--advise")):
        m = re.search(rf"^{target}:.*\n(?:#.*\n)*\t(.*)", mk, re.M)
        if not m or "scripts/cost_ledger.py" not in m.group(1) or (flag and flag not in m.group(1)):
            bad.append(f"  `make {target}` does not run scripts/cost_ledger.py {flag}".rstrip())

    print("\n".join(bad))
    print(f"test-cost {'FAIL' if bad else 'PASS'}: the counting rules, the window and the three advice rules"
          + (f" -- {len(bad)} finding(s)" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
