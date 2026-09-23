#!/usr/bin/env python3
"""Every control the documentation claims is enforced must be reachable from `make gate`.

WHY. A document once listed four controls on the commit hook -- make check, gitleaks, pip-audit,
slopsquat -- while the hook ran `make check` and `make check` ran lint, typecheck and test. It also
listed a PreToolUse block on destructive git commands that `.claude/settings.json` never had.
**Four of six advertised controls were absent, on the page a reviewer reads to learn what is
enforced**, and nothing compared prose with configuration.

What this compares, exactly:
  1. EVERY leg reachable from `make gate` must be able to fail: no `-` prefix, no `|| true`, no
     `exit 0`, no recipe that only echoes, and no tool named in a recipe that the recipe does not run.
  2. A RULE MAY NOT OUTLIVE ITS GATE. A document that asserts its own enforcement declares an
     `enforced-by:` line naming a path in backticks (optionally `@` a location), and this test
     resolves it against what actually runs -- `make -n gate`, the workflows, the hooks, or the named
     home. No list to update; the claim and its check live in the same sentence. Prose that asserts
     enforcement WITHOUT an `enforced-by:` line is not read -- declare it, or it is unchecked.
  3. `make -n gate` must expand the conformance suite, the governance validator and the slopsquat
     check, and every target that collides with a real path must be in `.PHONY`.
  4. The hooks are RUN, not grepped: the Bash and `.env` guards must block exactly what they claim
     (exit 2) and allow the rest (exit 0) -- with a real interpreter, and with a `python3` that
     fails in front of a real `python` (the Windows Store alias). With NO working interpreter, or a
     payload that does not parse, they must block, never allow: a guard that cannot read the call
     once exited 0 on everything, silently. The Bash guard matches with `grep`, so with no `grep`
     on PATH it must block too. The PostToolUse hook must run `make check-fast`, fail with exit 2,
     and say so plainly when `make` is not installed.

FAILS CLOSED: finding zero `enforced-by:` declarations is a FAILURE, not a pass. A parser that
silently matches nothing is the defect this rule exists to name, one level up.

NOT-EVALUABLE (exit 2) when bash cannot run the hooks or make cannot expand the gate here, and
nothing else failed: those halves were not graded, and the line says which.

Field evidence, three projects: a rulebook asserting five rules as enforced while the same commit
deleted three of their gates; a data-erasure register claiming "read by <gate> on every push" that,
run by hand, failed on eight columns; and a restart commit claiming to restore `mypy` in a tree
where `grep mypy` returns nothing.

Exit 0 clean, 1 findings, 2 not evaluable here.
"""
import sys, re, json, os, pathlib, subprocess, shutil, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, runnable_bash                     # noqa: E402

# The first stderr line of a PreToolUse guard that has no interpreter to read the call with.
NO_INTERPRETER = ("BLOCKED: this guard cannot read the tool call -- no working python3 or python "
                  "on PATH (see INSTALL.md).")
# The first stderr line of the Bash guard when it has an interpreter and no `grep` to match with.
NO_GREP = "BLOCKED: this guard cannot run -- grep is not on PATH (see INSTALL.md)."
UNREADABLE = "BLOCKED: this guard cannot read the tool call"
POST_GREEN = "POST-EDIT CHECK: make check-fast GREEN"
POST_FAILED = "POST-EDIT CHECK: make check-fast FAILED (exit 7) -- fix before the next edit"
POST_NO_MAKE = "POST-EDIT CHECK CANNOT RUN: make is not installed (see INSTALL.md)"
# What the Windows Store alias does when Python is not installed: prints, and exits non-zero.
BROKEN_PYTHON = ("#!/bin/sh\necho 'Python was not found; run without arguments to install from "
                 "the Microsoft Store' >&2\nexit 9\n")

# Where a project may assert enforcement. Documents, not code -- code is checked by being run.
CLAIM_ROOTS = ("docs", ".agents", "AGENTS.md", "README.md", "permission-matrix.md")
# `enforced-by: `path`` with an optional `@ `location``
CLAIM_RE = re.compile(r"enforced-by:\s*`([^`]+)`(?:\s*@\s*`([^`]+)`)?")


def enforcement_claims(root: pathlib.Path) -> list[tuple[pathlib.Path, str, str | None]]:
    """Every `enforced-by:` declaration in the documentation tree. DERIVED, never enumerated."""
    out = []
    for base in CLAIM_ROOTS:
        target = root / base
        files = [target] if target.is_file() else (
            sorted(target.rglob("*.md")) if target.is_dir() else [])
        for f in files:
            for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():
                m = CLAIM_RE.search(ln)
                if m:
                    out.append((f.relative_to(root), m.group(1).strip(), m.group(2)))
    return out


def targets(mk: str) -> dict[str, str]:
    out, cur = {}, None
    for line in mk.splitlines():
        m = re.match(r"^([A-Za-z0-9_.-]+):(.*)$", line)
        if m:
            cur = m.group(1); out[cur] = m.group(2) + "\n"
        elif cur and (line.startswith("\t") or line.startswith("    ")):
            out[cur] += line + "\n"
        elif line.strip() == "":
            cur = None
    return out


def _script(path: pathlib.Path, body: str) -> None:
    """An executable shell script. A wrapper, not a symlink: Windows may not allow symlinks."""
    path.write_text(body, encoding="utf-8", newline="\n")
    path.chmod(0o755)


def hook_paths(tmp: pathlib.Path) -> dict[str, str]:
    """PATHs to run the hooks under, each built in `tmp` and holding only what it names.

    Every one but `no-grep` carries the non-Python tools a hook calls (`grep`, `tee`, `cat`), and
    none carries `make`:
      broken-python3   a `python3` that fails, then a real `python` -- the guard must still work
      no-interpreter   `python3` and `python` both failing -- the guard must block everything
      no-python        neither on PATH at all -- the same
      no-grep          a real `python3` and nothing else -- the Bash guard must block everything
      make-0, make-7   a `make` that exits 0 / 7 and prints its arguments
      no-make          the tools alone
    """
    tools = tmp / "tools"
    tools.mkdir()
    for t in ("grep", "tee", "cat"):
        src = shutil.which(t)
        if src:
            _script(tools / t, f'#!/bin/sh\nexec "{src}" "$@"\n')
    out = {"no-python": str(tools), "no-make": str(tools)}
    for name, py3, py in (("broken-python3", BROKEN_PYTHON, f'#!/bin/sh\nexec "{sys.executable}" "$@"\n'),
                          ("no-interpreter", BROKEN_PYTHON, BROKEN_PYTHON)):
        d = tmp / name
        d.mkdir()
        _script(d / "python3", py3)
        _script(d / "python", py)
        out[name] = os.pathsep.join((str(d), str(tools)))
    d = tmp / "no-grep"
    d.mkdir()
    _script(d / "python3", f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    out["no-grep"] = str(d)
    for rc in (0, 7):
        d = tmp / f"make-{rc}"
        d.mkdir()
        _script(d / "make", f'#!/bin/sh\necho "fake-make-args: $*"\nexit {rc}\n')
        out[f"make-{rc}"] = os.pathsep.join((str(d), str(tools)))
    return out


def run_hook(bash: str, command: str, payload: str, path: str | None = None,
             extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if path is not None:
        env["PATH"] = path
    env.update(extra or {})
    return subprocess.run([bash, "-c", command], input=payload.encode("utf-8"),
                          capture_output=True, env=env, timeout=60)


def _err(r: subprocess.CompletedProcess) -> str:
    lines = r.stderr.decode("utf-8", errors="replace").strip().splitlines()
    return lines[0] if lines else ""


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    mk = (root / "Makefile").read_text(encoding="utf-8")
    tg = targets(mk)
    bad = []

    if "gate" not in tg:
        print("  FAIL no `gate` target -- there is no single name meaning 'everything we claim'")
        return 1
    def prereqs(target: str) -> set[str]:
        # A target line may carry a `## help` comment, which `split()` happily turned into
        # forty-odd "prerequisites" with names like `the` and `a`. Stop at the comment.
        return set(tg[target].splitlines()[0].split("#")[0].split()) if target in tg else set()

    gate_deps = prereqs("gate")
    # transitively expand one level (gate: check secrets ... ; check: lint typecheck ...)
    reachable = set(gate_deps)
    for d in list(gate_deps):
        reachable |= prereqs(d)

    # Token presence is defeated by keeping the token and disabling the command:
    # `-$(PY) -m ruff check src tests || true` still contains "ruff", and `make secrets` gutted to
    # `echo skipping; exit 0` still has a recipe. **A recipe that cannot fail is not a control,
    # whatever words are in it.** This runs over EVERY target reachable from `make gate` -- derived
    # from the Makefile, never a hand-kept list of the targets that matter.
    for target in sorted(reachable):
        if target not in tg:
            bad.append(f"`{target}` is a prerequisite of `make gate` but has no target")
            continue
        for line in tg[target].splitlines():
            ln = line.strip()
            if not ln or ln.startswith("#"):
                continue
            if ln.startswith("-") or re.search(r"\|\|\s*true\b|;\s*exit\s+0\b|\|\|\s*exit\s+0\b", ln):
                bad.append(f"`{target}` swallows its own failure (`{ln[:46]}`) -- the token is there "
                           "and the control cannot fail")
        # A leg whose whole recipe is echoes and no-ops runs nothing, whatever it is named.
        real = [ln.strip().lstrip("@-") for ln in tg[target].splitlines()[1:]
                if ln.strip() and not ln.strip().startswith("#")]
        if real and all(re.match(r"(echo|true|:)\b", c) for c in real):
            bad.append(f"`{target}` is a gate leg whose recipe only echoes -- it runs nothing, and "
                       f"a target that cannot fail is not a control")
        # The substitution half: `lint` neutered to `$(PY) -c "import sys; sys.exit(0)"` is a real
        # command that checks nothing, and passes the echo test above. If a leg names a tool or a
        # script -- the same tokens `run-all.py` extracts for caller-liveness -- its recipe must
        # still invoke it.
        if target in reachable and tg[target].splitlines()[1:]:
            declared = set(re.findall(r"(?:scripts|conformance)/[\w.-]+\.py", tg[target]))
            declared |= set(re.findall(r"\b(gitleaks|pip_audit|pip-audit|ruff|mypy|pytest)\b",
                                       "\n".join(l for l in tg[target].splitlines()
                                                 if not l.strip().startswith("#"))))
            body_code = "\n".join(l for l in tg[target].splitlines()[1:]
                                   if l.strip() and not l.strip().startswith("#"))
            for tool in sorted(declared):
                if tool not in body_code:
                    bad.append(f"`{target}` names `{tool}` but its recipe does not invoke it")

    # ---- a rule may not outlive its gate -----------------------------------------------------
    # A tool that is not here is an environment, not a finding: without `make`, the claims only the
    # gate runs would read as "nothing runs it" -- the report accusing controls it could not see.
    unevaluable: list[str] = []
    no_make = missing_tool("make", "expand `make -n gate`, so the gate-only claims and the gate's "
                                   "expansion are not graded here")
    if no_make:
        unevaluable.append(no_make)
    claims = enforcement_claims(root)
    if not claims:
        bad.append("no `enforced-by:` declaration found anywhere in the documentation tree. This "
                   "check FAILS CLOSED: a parser that matches nothing is not evidence that nothing "
                   "is claimed, and the package asserts enforcement in at least one shipped document")
    dry_gate = ""
    if not no_make:
        dry_gate = subprocess.run(["make", "-n", "gate"], cwd=root, capture_output=True,
                                  encoding="utf-8", errors="replace").stdout
    ci_text = "\n".join(f.read_text(encoding="utf-8", errors="replace")
                        for f in sorted((root / ".github" / "workflows").glob("*.yml"))) \
        if (root / ".github" / "workflows").is_dir() else ""
    hooks_text = (root / ".claude" / "settings.json").read_text(encoding="utf-8", errors="replace") \
        if (root / ".claude" / "settings.json").is_file() else ""

    for where, path_claim, at in claims:
        name = pathlib.PurePosixPath(path_claim).name
        if not (root / path_claim).is_file():
            bad.append(f"{where} declares `enforced-by: {path_claim}` and that file does not exist")
            continue
        if at:
            # An explicit home: the control runs from a named place rather than from `make gate`.
            # `bootstrap-check` is the shipped example -- it belongs at Stage 0 close, because it
            # fails on unfilled placeholders and would make every fresh export red on day one.
            home = root / at.split("#")[0].strip()
            if not home.is_file():
                bad.append(f"{where} declares `enforced-by: {path_claim} @ {at}` -- that home "
                           f"does not exist")
            elif not any(tok in home.read_text(encoding="utf-8", errors="replace")
                         for tok in (path_claim, name, pathlib.PurePosixPath(name).stem)):
                bad.append(f"{where} claims `{path_claim}` is enforced at `{at}`, and `{at}` never "
                           f"mentions it -- the claim names a home that does not hold it")
        elif not any(name in blob for blob in (dry_gate, ci_text, hooks_text)) and not no_make:
            bad.append(f"{where} claims `{path_claim}` enforces something, and nothing runs it: "
                       f"absent from `make -n gate`, from every workflow, and from the hooks. "
                       f"**A rule that outlives its gate is worse than one that never had a gate, "
                       f"because the sentence claiming enforcement is still there to be believed**")

    # Reading a build file is not the same as running it: `make gate` once skipped the whole
    # conformance suite silently, because `conformance` is also a directory and was missing from
    # `.PHONY`, and a check that read the Makefile TEXT reported nothing. Ask make itself.
    if not no_make:
        for must, why in (("run-all.py", "the conformance suite"),
                          ("check_records.py", "the governance validator"),
                          ("slopsquat_check.py", "the slopsquat check")):
            if must not in dry_gate:
                bad.append(f"`make -n gate` never expands `{must}` -- {why} does not execute through "
                           "the documented command, whatever the Makefile appears to say")
    phony = re.search(r"^\.PHONY:(.*(?:\\\n.*)*)$", mk, re.M)
    declared = set((phony.group(1) if phony else "").replace("\\", " ").split())
    for t in tg:
        if (root / t).exists() and t not in declared:
            bad.append(f"target `{t}` collides with a real path and is not in .PHONY -- make will "
                       "call it up to date and never run its recipe")

    # The destructive-command PreToolUse hook that permission-matrix.md S5 names.
    st = root / ".claude" / "settings.json"
    hooks = json.loads(st.read_text(encoding="utf-8"))["hooks"]
    # **Grepping a hook tells you what it looks like; only running it tells you what it does.** A
    # grep for "rm" is satisfied by the word "pe-rm-ission", and a narrower regex over the config
    # text fails a correctly widened hook. So run it.
    # Pushing the protected branch is BLOCKED: a rule that says the agent never pushes it is only as
    # real as the hook that refuses. Pushing the agent's OWN branch stays allowed -- it is how the
    # draft PR gets opened, and a rule that blocked it would be unwired within a day.
    MUST_BLOCK = ["git push origin main --force", "git push --force origin main", "git push -f o x",
                  "git push origin main", "git push origin master", "git push origin HEAD:main",
                  "git reset --hard HEAD~1", "rm -rf .", "rm -rf ~/work", "rm -fr /home/u",
                  "git clean -fd"]
    MUST_ALLOW = ["git push -u origin fix/issue-3", "git push origin enhancement/x", "git push",
                  "git status", "rm file.txt", "rm -r build",
                  "git reset HEAD~1", "npm run format"]
    bash_hook = next((h["hooks"][0]["command"] for h in hooks.get("PreToolUse", [])
                      if h.get("matcher") == "Bash"), None)
    env_hook = next((h["hooks"][0]["command"] for h in hooks.get("PreToolUse", [])
                     if h.get("matcher", "").startswith("Write")), None)
    post = [h["hooks"][0]["command"] for h in hooks.get("PostToolUse", [])]
    if bash_hook is None:
        bad.append("no PreToolUse Bash hook at all, and permission-matrix.md S5 says one blocks "
                   "destructive commands")
    if not all(re.search(r"exit 2\b", c) for c in post):
        bad.append("a PostToolUse hook fails with a code other than 2 -- Claude never sees it")

    # Claude Code blocks a PreToolUse call ONLY on exit 2; exit 1 is a non-blocking error and the
    # tool runs anyway. Grading `!= 0` as "blocked" once passed guards that blocked nothing -- a
    # `.env` write went through live. Blocked means exactly 2; allowed means exactly 0.
    bash, why = runnable_bash("run the hooks in .claude/settings.json, so no hook was graded here")
    if not bash:
        unevaluable.append(why)
    else:
        def cmd(c: str) -> str:
            return json.dumps({"tool_input": {"command": c}}, ensure_ascii=False)

        def fpath(f: str) -> str:
            return json.dumps({"tool_input": {"file_path": f}}, ensure_ascii=False)

        # (hook, label, payload, want_block, PATH or None for this machine's, extra env)
        cases: list[tuple[str, str, str, bool, str | None, dict]] = []
        with tempfile.TemporaryDirectory() as tmp:
            paths = hook_paths(pathlib.Path(tmp))
            if bash_hook is not None:
                cases += [("Bash", f"`{c}`", cmd(c), True, None, {}) for c in MUST_BLOCK]
                cases += [("Bash", f"`{c}`", cmd(c), False, None, {}) for c in MUST_ALLOW]
            if env_hook:
                cases += [("Write", f"a write to `{f}`", fpath(f), want, None, {})
                          for f, want in ((".env", True), ("cfg/.env.prod", True), ("prod.env", True),
                                          ("src/app.py", False), ("README.md", False))]
            for kind in [k for k, h in (("Bash", bash_hook), ("Write", env_hook)) if h]:
                ok_payload, bad_payload = ((cmd("git status"), cmd("git push origin main"))
                                           if kind == "Bash" else
                                           (fpath("README.md"), fpath("cfg/.env")))
                cases += [
                    # "The field is empty" is a call the guard has nothing to object to; "the call
                    # could not be read" is one it cannot vouch for. The first allows, the second
                    # blocks -- they were once the same empty string, and both allowed.
                    (kind, "an empty tool_input", '{"tool_input": {}}', False, None, {}),
                    (kind, "a payload that is not JSON", "not json {", True, None, {}),
                    # The Windows Store alias: `python3` prints an error and exits non-zero. With
                    # a real `python` behind it the guard must work exactly as with python3.
                    (kind, "the blocked call, python3 broken", bad_payload, True,
                     paths["broken-python3"], {}),
                    (kind, "the allowed call, python3 broken", ok_payload, False,
                     paths["broken-python3"], {}),
                    # A non-UTF-8 console (cp1254) must not crash the parse into a verdict.
                    (kind, "a non-ASCII call on a cp1254 console",
                     cmd("echo \u2192 done") if kind == "Bash" else fpath("docs/\u2192.md"), False,
                     None, {"PYTHONIOENCODING": "cp1254"}),
                ]
            hook_of = {"Bash": bash_hook, "Write": env_hook}
            for kind, label, payload, want_block, path, extra in cases:
                r = run_hook(bash, hook_of[kind], payload, path, extra)
                if (r.returncode == 2) != want_block or r.returncode not in (0, 2):
                    bad.append(f"PreToolUse {kind} guard {'failed to block' if want_block else 'wrongly blocked'} "
                               f"{label} (exit {r.returncode}; only 2 blocks; {_err(r)[:90] or 'no message'}) "
                               "-- permission-matrix.md S5 describes this hook, and a claim nobody "
                               "executes is a claim nobody has checked")
                elif label == "a payload that is not JSON" and not _err(r).startswith(UNREADABLE):
                    bad.append(f"PreToolUse {kind} guard blocked {label} without saying it could not "
                               f"read the call (`{_err(r)[:90]}`)")
            # No interpreter at all, and one that is only the Store alias: the guard cannot read
            # the call, so it must refuse it -- and say why, in the line INSTALL.md points at.
            for kind in [k for k, h in (("Bash", bash_hook), ("Write", env_hook)) if h]:
                for setup in ("no-interpreter", "no-python"):
                    payload = cmd("git status") if kind == "Bash" else fpath("README.md")
                    r = run_hook(bash, hook_of[kind], payload, paths[setup])
                    if r.returncode != 2 or _err(r) != NO_INTERPRETER:
                        bad.append(f"PreToolUse {kind} guard with {setup.replace('-', ' ')} on PATH: "
                                   f"exit {r.returncode}, first stderr line `{_err(r)[:90]}` -- it "
                                   f"must exit 2 with `{NO_INTERPRETER}`. A guard that cannot read "
                                   "the call and allows it has switched itself off")
            # The Bash guard reads the call and then matches it with `grep`. Without one, every
            # pattern test fails, nothing matches, and the guard allowed everything -- so it must
            # refuse, even `git status`, with the line INSTALL.md points at.
            if bash_hook is not None:
                r = run_hook(bash, bash_hook, cmd("git status"), paths["no-grep"])
                if r.returncode != 2 or _err(r) != NO_GREP:
                    bad.append(f"PreToolUse Bash guard with no grep on PATH: exit {r.returncode}, "
                               f"first stderr line `{_err(r)[:90]}` -- it must exit 2 with "
                               f"`{NO_GREP}`. A guard that cannot match allows every command")

            # Per edit: `make check-fast` -- the offline `make check` legs side by side, seconds.
            # The full `make gate` (network: pip-audit, slopsquat) runs at pre-push and `/pre-merge`.
            proj = pathlib.Path(tmp) / "proj"
            (proj / ".claude").mkdir(parents=True)
            if not post:
                bad.append("no PostToolUse hook -- nothing checks the tree after an edit")
            for c in post:
                env = {"CLAUDE_PROJECT_DIR": str(proj)}
                for setup, want_rc, stream, line in (("make-0", 0, "stdout", POST_GREEN),
                                                     ("make-7", 2, "stderr", POST_FAILED),
                                                     ("no-make", 2, "stderr", POST_NO_MAKE)):
                    r = run_hook(bash, c, "{}", paths[setup], env)
                    text = getattr(r, stream).decode("utf-8", errors="replace")
                    if r.returncode != want_rc or line not in text:
                        bad.append(f"the PostToolUse hook with {setup}: exit {r.returncode}, "
                                   f"expected {want_rc} and `{line}` on {stream}")
                    if setup != "no-make" and "fake-make-args: check-fast" not in \
                            r.stdout.decode("utf-8", errors="replace"):
                        bad.append("the PostToolUse hook does not call `make check-fast` after an edit")

    for b in bad:
        print(f"  FAIL {b}")
    for u in unevaluable:
        print(f"  NOT-EVALUABLE {u}")
    verdict = "FAIL" if bad else ("NOT-EVALUABLE" if unevaluable else "PASS")
    print(f"test-hook-claims {verdict}: {len(claims)} enforcement claim(s) derived, "
          f"{len(reachable)} gate leg(s), {len(bad)} unbacked"
          + (f", {len(unevaluable)} half(s) not graded here" if unevaluable else ""))
    return 1 if bad else (2 if unevaluable else 0)


if __name__ == "__main__":
    sys.exit(main())
