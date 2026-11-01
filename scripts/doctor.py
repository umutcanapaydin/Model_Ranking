#!/usr/bin/env python3
"""`make doctor`: the read-only checks a session starts with, in one call.

`/start-session` ran them one by one -- session-check, mode, deploy-check, run-check, ci-liveness, two `gh`
listings -- each a tool call whose whole output stays in the context of every later model call. v7.3 (A23,
the owner's ruling of 2026-10-28): one call, a stable id per check, pass / warn / fail, `--json` for a script.
It writes nothing and runs no gate leg: `make check-fast` stays the session's own step.

  session      scripts/session_check.py: this Claude Code session loaded the settings; core.hooksPath is set
  environment  .agents/rules/environment.md exists (gitignored: your machine, copied from its template)
  mode         the brief's working mode (`make mode`), and `Merges: do not wait` when the brief says it
  run          each open run file (docs/plans/run-*.md, `Ended: open`), graded by scripts/run_check.py
  deploy       scripts/deploy_gate.py --check; before the first release it says so, which is not a defect
  ci           scripts/ci_liveness.py: did the latest CI runs start a step (advisory)
  prs          gh: the open pull requests; a merged one whose branch is still here at its head (`/post-merge` deletes
               it, so this survives GitHub's auto-delete); one whose branch is left only on origin (the owner's)
  settings     the settings-risk line (the owner's trim of a settings scan): an allow rule or a hook wider than
               the permission matrix in .claude/settings.json, .claude/settings.local.json or the user's settings
  claude-code  Claude Code 2.1.295 or later: an older one ignores `"onFailure": "block"`, so a guard hook that
               hangs or cannot start lets the call through -- the guard fails open

A check that cannot read its subject says so as a `warn` (a `fail` for the session and the run, which a
session cannot work past): it never passes on what it could not see. Every git call it and the scripts it runs
make carries GIT_OPTIONAL_LOCKS=0: a read-only check never takes `.git/index.lock` from the session's own git.

    python3 scripts/doctor.py [--json]
Exit: 0 no check failed · 1 a check failed · 2 usage.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IDS = ("session", "environment", "mode", "run", "deploy", "ci", "prs", "settings", "claude-code")
MIN_CLAUDE = (2, 1, 295)
#: Commands an allow rule may not pre-approve without a prompt: a shell or an interpreter, a downloader,
#: a privilege change, a destructive command, or a wrapper that runs any other command. A named list with
#: its reason (AGENTS.md §3.5): it is the vocabulary of ruflo's settings-risk scan, which the owner's trim
#: of 2026-10-28 turned into this one line; the project's own allow list is the matrix (permission-matrix.md §10).
RISKY = {"bash", "sh", "zsh", "dash", "ksh", "fish", "pwsh", "powershell", "python", "python3", "node", "perl",
         "ruby", "curl", "wget", "sudo", "su", "doas", "eval", "exec", "rm", "dd", "mkfs", "chmod", "chown",
         "env", "xargs", "nohup", "timeout", "nice", "command", "busybox"}


def quiet() -> dict:
    """The environment of every git call and script doctor runs: git takes no optional lock (v7.3 review, B2)."""
    return {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}


def git(*args: str, cwd: Path | str = ".") -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, encoding="utf-8", errors="replace",
                           timeout=30, env=quiet())
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def run(args: list[str], timeout: int = 120, env: dict | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(args, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
                           env=quiet() if env is None else env)
    except subprocess.TimeoutExpired:
        return 124, f"did not answer within {timeout}s"
    except OSError as exc:
        return 127, str(exc)
    return r.returncode, (r.stdout + r.stderr).strip()


# ------------------------------------------------------------------ where the work stands (also A22, A25)
def open_runs(root: Path) -> list[Path]:
    out = []
    for f in sorted((root / "docs" / "plans").glob("run-*.md")):
        try:
            if re.search(r"^Ended:\s*open\s*$", f.read_text(encoding="utf-8", errors="replace"), re.M):
                out.append(f)
        except OSError:
            continue
    return out


def running(run_file: Path) -> list[tuple[str, str]]:
    """(wave, branch) of every `running` row in a run file's Waves table."""
    rows, on = [], False
    for line in run_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            on = line[3:].strip().lower().startswith("waves")
            continue
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")] if on and line.lstrip().startswith("|") else []
        if len(cells) >= 5 and cells[4].lower() == "running":
            rows.append((cells[0], cells[1]))
    return rows


def branch(root: Path) -> str:
    name = git("branch", "--show-current", cwd=root)
    if name:
        return name
    head = git("rev-parse", "--short", "HEAD", cwd=root)
    return f"detached HEAD at {head}" if head else ""


def container_issue(root: Path, milestone: str, wave: str) -> str | None:
    plan = root / "docs" / "plans" / f"m{milestone}-plan.md"
    try:
        text = plan.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(rf"^## Wave {wave}\b(.*?)(?=^## |\Z)", text, re.M | re.S)
    found = re.search(r"Container issue:\s*#(\d+)", m.group(1)) if m else None
    return found.group(1) if found else None


def issue_of(root: Path, name: str) -> str | None:
    """The issue a branch works: `issue-<n>` in its name, a heavy wave's container issue from its plan, or the
    open run's `running` row for this branch."""
    m = re.search(r"\bissue-(\d+)", name)
    if m:
        return m.group(1)
    w = re.fullmatch(r"wave/m(\d+)-w(\d+)", name)
    if w:
        return container_issue(root, w.group(1), w.group(2))
    for f in open_runs(root):
        for wave, b in running(f):
            if b != name:
                continue
            light = re.fullmatch(r"issue-(\d+)", wave)
            heavy = re.fullmatch(r"m(\d+)-w(\d+)", wave)
            if light:
                return light.group(1)
            if heavy:
                return container_issue(root, heavy.group(1), heavy.group(2))
    return None


def after_compaction(root: Path) -> str:
    """The SessionStart message's addition after a compaction (A25): the branch and the issue it works."""
    name = branch(root)
    if not name:
        return ""
    issue = issue_of(root, name)
    return f"After the compaction: branch {name}" + (f", issue #{issue}." if issue else ".")


# ------------------------------------------------------------------ the checks
def check_session() -> tuple[str, str]:
    rc, out = run([sys.executable, str(HERE / "session_check.py")])
    if rc != 0:
        # Only a missing pre-push hook is a warn (`make hooks` cures it); settings that did not load, or
        # anything else, is a fail: the session stops there.
        fails = [ln for ln in out.splitlines() if ln.startswith("FAIL")]
        hooks_only = fails and all("core.hooksPath" in ln and "make hooks" in ln for ln in fails)
        return ("warn" if hooks_only else "fail"), out
    if "PASS" in out and "and core.hooksPath (" in out:
        return "pass", "the SessionStart marker for this session, and core.hooksPath (this clone's .githooks)"
    if "PASS" in out:       # beside husky or pre-commit (v7.3): the pre-push hook git runs names ours
        return "pass", ("the SessionStart marker for this session, and the pre-push hook git runs (its first command "
                        "names .githooks/pre-push)")
    return "pass", re.sub(r"^session-check:\s*", "", out)


def check_environment(root: Path) -> tuple[str, str]:
    if (root / ".agents" / "rules" / "environment.md").is_file():
        return "pass", ""
    return "warn", ("no .agents/rules/environment.md: copy .agents/rules/environment.md.template to it and fill "
                    "it (gitignored: your machine, not the project's)")


def check_mode(root: Path) -> tuple[str, str]:
    import brief_fields  # noqa: PLC0415
    mode = brief_fields.mode(root)
    merges = (brief_fields.field("Merges", root) or "").strip().lower()
    return "pass", mode + ("; Merges: do not wait -- the integration lane while the owner is away (AGENTS.md §3)"
                           if merges.startswith("do not wait") else "")


def check_run(root: Path) -> tuple[str, str]:
    runs = open_runs(root)
    if not runs:
        return "pass", "no open run"
    status, said = "pass", []
    for f in runs:
        rel = f.relative_to(root).as_posix()
        rc, out = run([sys.executable, str(HERE / "run_check.py"), rel])
        if rc != 0:
            status = "fail"
            said.append(f"{rel}: " + "; ".join(ln for ln in out.splitlines() if ln.startswith("FAIL")))
            continue
        rows = running(f)
        said.append(f"{rel} is open, resume it: " + (", ".join(f"{w} running on {b}" for w, b in rows)
                                                     if rows else "no wave running"))
    return status, " | ".join(said)


def check_deploy(root: Path) -> tuple[str, str]:
    # model_ranking (D-234, #526): the deploy gate refuses while its caller sets any `GIT_*`, so it is run without
    # `GIT_OPTIONAL_LOCKS`, and sets it to 0 for its own git itself.
    rc, out = run([sys.executable, str(HERE / "deploy_gate.py"), "--check"],
                  env={k: v for k, v in os.environ.items() if k != "GIT_OPTIONAL_LOCKS"})
    if rc == 0:
        return "pass", "the release verdicts are current for this tree"
    if not (root / "docs" / "reviews" / "release-security.md").is_file():
        return "pass", "no release yet -- not a defect"
    fails = [ln.replace("deploy-check ", "", 1) for ln in out.splitlines() if ln.startswith("deploy-check FAIL")]
    return "warn", ("; ".join(fails) or out[-300:]) + " -- a release owes this before it ships"


def check_ci() -> tuple[str, str]:
    import ci_liveness  # noqa: PLC0415
    v = ci_liveness.verdict()
    if v.startswith("WARN"):
        return "warn", v[len("WARN -- "):] + ": tell the owner"
    if v.startswith("CANNOT CHECK"):
        return "warn", v.lower().replace(" -- ", ": ", 1)
    return "pass", re.sub(r"^ok -- ", "", v)


def check_prs(root: Path) -> tuple[str, str]:
    import ci_liveness  # noqa: PLC0415
    if shutil.which("gh") is None:
        return "warn", "cannot check: gh not installed"
    try:
        opened = ci_liveness.gh(["pr", "list", "--state", "open", "--limit", "20", "--json", "number,headRefName,isDraft"])
        merged = ci_liveness.gh(["pr", "list", "--state", "merged", "--author", "@me", "--limit", "20",
                                 "--json", "number,headRefName,headRefOid"])
    except ci_liveness.CannotCheck as exc:
        return "warn", f"cannot check: {exc}"
    opened = [p for p in opened if isinstance(p, dict)] if isinstance(opened, list) else []
    merged = [p for p in merged if isinstance(p, dict)] if isinstance(merged, list) else []
    said = (f"{len(opened)} open: " + ", ".join(f"#{p.get('number')} {p.get('headRefName')}"
                                                 + (" (draft)" if p.get("isDraft") else "") for p in opened[:10])
            if opened else "none open")
    if not merged:
        return "pass", said
    # `/post-merge` deletes local branches only (#50). A merged PR's branch still here at the PR's head is one
    # whose `/post-merge` never ran -- a marker GitHub's auto-delete leaves alone; one a commit moved past the
    # head, or another worktree holds, is not (`/post-merge` keeps it: naming it would loop). A branch left only
    # on origin is the owner's to delete: `/post-merge` never pushes (P5 review, B1).
    heads = git("ls-remote", "--heads", "origin", cwd=root)
    refs = git("for-each-ref", "--format=%(refname:short)%00%(objectname)%00%(worktreepath)", "refs/heads", cwd=root)
    top = git("rev-parse", "--show-toplevel", cwd=root)
    if heads is None or refs is None or top is None:
        return "warn", said + "; cannot tell which merged branch is left (git ls-remote origin, git for-each-ref)"
    alive = {ln.split("refs/heads/", 1)[1] for ln in heads.splitlines() if "refs/heads/" in ln}
    here = {}
    for ln in refs.splitlines():
        name, oid, tree = (ln.split("\0") + ["", ""])[:3]
        if not tree or Path(tree).resolve() == Path(top).resolve():
            here[name] = oid
    busy = {p.get("headRefName") for p in opened}
    mine = [p for p in merged if p.get("headRefOid") and here.get(str(p.get("headRefName"))) == p.get("headRefOid")]
    theirs = [p for p in merged if p.get("headRefName") in alive - busy and p not in mine]
    if not mine and not theirs:
        return "pass", said + "; no merged branch left"
    def name(ps: list[dict]) -> str:
        return ", ".join(f"#{p.get('number')} {p.get('headRefName')}" for p in ps)
    return "warn", said + (f"; merged, not cleaned up here: {name(mine)} -- /post-merge for each" if mine else "") + (
        f"; merged, branch left on origin: {name(theirs)} -- the owner's: `git push origin --delete <branch>`, or "
        "the delete-branch-on-merge row (docs/owner-actions.md)" if theirs else "")


def _rule_risk(rule: object) -> str | None:
    if not isinstance(rule, str):
        return "an allow rule that is not text"
    m = re.fullmatch(r"\s*(Bash|PowerShell)\s*(?:\((.*)\))?\s*", rule, re.I | re.S)
    if not m:
        return None
    inner = (m.group(2) or "").strip()
    first = re.split(r"[\s:]+", inner.strip("\"'"), maxsplit=1)[0] if inner else ""
    if not first or "*" in first:
        return f"allows all of {m.group(1)}"
    word = re.split(r"[\\/]", first.strip("\"'"))[-1].lower().removesuffix(".exe")
    if word in RISKY:
        return f"allows `{word}`"
    # `make` with any arguments runs any recipe: `make lint PY='<anything>'` (test-hook-claims, a field finding)
    return "allows `make` with any arguments" if word == "make" and "*" in inner else None


def _hook_risk(command: object) -> str | None:
    text = command if isinstance(command, str) else ""
    words = set(re.findall(r"[A-Za-z0-9_.-]+", text.lower()))
    if words & {"curl", "wget"} and (words & {"sh", "bash", "zsh", "python", "python3", "node", "eval"}
                                     or re.search(r"\|\s*(sh|bash|zsh)\b", text)):
        return "a hook that downloads and runs"
    if re.search(r"base64\s+(-d|--decode)\b|/dev/tcp/", text):
        return "a hook that decodes or opens a socket"
    return None


def settings_files(root: Path) -> list[tuple[str, Path, bool]]:
    """(label, path, whether its hooks are DevFlow's shipped set) for each settings file the session loads."""
    config = os.environ.get("CLAUDE_CONFIG_DIR")
    user = (Path(config).expanduser() if config else Path.home() / ".claude") / "settings.json"
    label = "$CLAUDE_CONFIG_DIR/settings.json" if config else "~/.claude/settings.json"
    return [(".claude/settings.json", root / ".claude" / "settings.json", True),
            (".claude/settings.local.json", root / ".claude" / "settings.local.json", False),
            (label, user, False)]


def check_settings(root: Path) -> tuple[str, str]:
    found, read = [], 0
    for label, path, shipped in settings_files(root):
        if not path.is_file():
            continue
        read += 1
        try:
            cfg = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(cfg, dict):
                raise ValueError("not an object")
        except (OSError, ValueError):
            found.append(f"{label}: cannot be read as JSON, so nothing in it was checked")
            continue
        why: list[str] = []
        perms = cfg.get("permissions", {})
        allow = perms.get("allow", []) if isinstance(perms, dict) else None
        if not isinstance(allow, list):
            why.append("its permissions cannot be read")
            allow = []
        why += [r for r in map(_rule_risk, allow) if r]
        if isinstance(perms, dict) and perms.get("defaultMode") == "bypassPermissions":
            why.append("defaultMode bypassPermissions (no prompt at all)")
        if cfg.get("disableAllHooks") is True:
            why.append("disableAllHooks (every guard off)")
        hooks = cfg.get("hooks", {})
        if not shipped and isinstance(hooks, dict):
            commands = [h.get("command") for groups in hooks.values() for g in (groups if isinstance(groups, list) else [])
                        if isinstance(g, dict) and isinstance(g.get("hooks"), list) for h in g["hooks"] if isinstance(h, dict)]
            line = cfg.get("statusLine")
            commands += [line.get("command")] if isinstance(line, dict) else []
            why += [r for r in map(_hook_risk, commands) if r]
        if why:
            found.append(f"{label}: " + ", ".join(dict.fromkeys(why)))
    if found:
        return "warn", "wider than the permission matrix -- " + "; ".join(found) + " -- tell the owner"
    return "pass", f"no allow rule or hook wider than the permission matrix ({read} settings file(s) read)"


def claude_version() -> tuple[tuple[int, ...] | None, str]:
    m = re.match(r"claude-code_(\d+)-(\d+)-(\d+)", os.environ.get("AI_AGENT", ""))
    if m:
        return tuple(int(x) for x in m.groups()), "this session"
    m = re.search(r"(?:^|[/\\])versions[/\\](\d+)\.(\d+)\.(\d+)(?:$|[/\\])", os.environ.get("CLAUDE_CODE_EXECPATH", ""))
    if m:
        return tuple(int(x) for x in m.groups()), "this session"
    exe = shutil.which("claude")
    if exe:
        rc, out = run([exe, "--version"], timeout=20)
        m = re.match(r"\s*(\d+)\.(\d+)\.(\d+)", out) if rc == 0 else None
        if m:
            return tuple(int(x) for x in m.groups()), "`claude --version`"
    return None, ""


def check_claude() -> tuple[str, str]:
    version, source = claude_version()
    least = ".".join(map(str, MIN_CLAUDE))
    if version is None:
        return "warn", (f"cannot read the Claude Code version (`claude --version`) -- Claude Code older than {least}: "
                        "the guard fails open -- tell the owner")
    shown = ".".join(map(str, version))
    if version < MIN_CLAUDE:
        return "warn", (f"{shown} ({source}): Claude Code older than {least}: the guard fails open -- a guard hook "
                        "that hangs or cannot start lets the call through; tell the owner (INSTALL.md)")
    return "pass", f"{shown} ({source})"


def doctor(root: Path) -> list[dict]:
    from concurrent.futures import ThreadPoolExecutor  # noqa: PLC0415
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))         # brief_fields, ci_liveness: imported once, before the threads
    jobs = {"session": check_session, "environment": lambda: check_environment(root),
            "mode": lambda: check_mode(root), "run": lambda: check_run(root), "deploy": lambda: check_deploy(root),
            "ci": check_ci, "prs": lambda: check_prs(root), "settings": lambda: check_settings(root),
            "claude-code": check_claude}

    def safe(name: str) -> tuple[str, str]:
        try:
            return jobs[name]()
        except Exception as exc:  # noqa: BLE001 -- a check that crashed read nothing: never a pass
            return ("fail" if name in ("session", "run") else "warn"), f"the check could not run: {exc!r}"[:300]

    with ThreadPoolExecutor(max_workers=len(IDS)) as pool:
        results = dict(zip(IDS, pool.map(safe, IDS)))
    return [{"id": i, "status": results[i][0], "detail": results[i][1]} for i in IDS]


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")
    if argv not in ([], ["--json"]):
        print("usage: doctor.py [--json]")
        return 2
    checks = doctor(Path.cwd())
    worst = "fail" if any(c["status"] == "fail" for c in checks) else (
        "warn" if any(c["status"] == "warn" for c in checks) else "pass")
    if argv:
        print(json.dumps({"checks": checks, "status": worst}))
    else:
        for c in checks:
            print(f"{c['id']}: {c['status']}" + (f" -- {c['detail']}".replace("\n", "\n  ") if c["detail"] else ""))
        n = {s: sum(c["status"] == s for c in checks) for s in ("warn", "fail")}
        print(f"doctor: {worst.upper()} -- {len(checks)} checks, {n['warn']} warn, {n['fail']} fail")
    return 1 if worst == "fail" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
