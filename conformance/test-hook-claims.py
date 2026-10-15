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
     once exited 0 on everything, silently. The Bash guard needs nothing but an interpreter: with
     only `python3` on PATH it still refuses. The PostToolUse hook must run `make check-fast`, fail
     with exit 2, and say so plainly when `make` is not installed.
  5. The Bash hook runs `.claude/hooks/bash_guard.py` and PINS it: its command carries the file's
     sha256, refuses every call when the file is altered (`not the guard the settings pin`) or
     missing, and the pin written there is the file's current sha256. Every hook entry carries
     `timeout` and `"onFailure": "block"`: a hook that hangs, or cannot start, does not block on its
     own (Claude Code 2.1.295 and later read `onFailure`), so a guard without them is a guard that
     switches itself off under load. And `permissions.allow` grants no `Bash(make <target>:*)`: that
     wildcard let `make lint PY='<anything>'` run with no prompt (a field finding).
  6. model_ranking (the M21 closure, carried into the v7.1 guard): the Write and Edit hook runs the same
     pinned guard with `--write`, so one changed byte blocks every write too; every interpreter the two
     hooks start runs as `python3 -I -S`, so neither a `json.py` where they run nor a `.pth` in the
     site-packages of the `python3` first on PATH changes a verdict; and both refuse a write into any work
     tree's `.claude/` or `.githooks/`, resolved from the payload's `cwd` and each `cd`, `pushd` or `git -C`,
     links followed, case-folded. The project's rules on `fly`/`flyctl` and the hosted engine's deploy
     script (D-185) are cases of the Bash hook's lists below.

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
import contextlib, sys, re, json, os, pathlib, signal, subprocess, shutil, tempfile, time, hashlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, runnable_bash                     # noqa: E402

# The first stderr line of a PreToolUse guard that has no interpreter to read the call with.
NO_INTERPRETER = ("BLOCKED: this guard cannot read the tool call -- no working python3 or python "
                  "on PATH (see INSTALL.md).")
# What the Bash hook says when the guard file is not the one the settings pin, or is gone.
PIN_ALTERED = "is not the guard the settings pin"
PIN_MISSING = "is missing"
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
      python-only      a real `python3` and nothing else -- the Bash guard must still judge
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
    d = tmp / "python-only"
    d.mkdir()
    _script(d / "python3", f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    out["python-only"] = str(d)
    for rc in (0, 7):
        d = tmp / f"make-{rc}"
        d.mkdir()
        _script(d / "make", f'#!/bin/sh\necho "fake-make-args: $*"\nexit {rc}\n')
        out[f"make-{rc}"] = os.pathsep.join((str(d), str(tools)))
    return out


def run_hook(bash: str, command: str, payload: str, path: str | None = None,
             extra: dict | None = None, cwd: pathlib.Path | None = None,
             timeout: float = 120) -> subprocess.CompletedProcess:
    # The guard resolves the repository from the call's directory and `CLAUDE_PROJECT_DIR`: both name
    # THIS package unless a case says otherwise, so a session's own project cannot leak in.
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(pathlib.Path(__file__).resolve().parent.parent)
    if path is not None:
        env["PATH"] = path
    env.update(extra or {})
    # The M21-W4 Tester's M5: the hook runs in a session of its own; one that does not answer within its limit
    # has its whole group killed (the guard's interpreter included) and comes back as a failure, exit -9.
    proc = subprocess.Popen([bash, "-c", command], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=env, start_new_session=hasattr(os, "killpg"), cwd=cwd)
    try:
        out, err = proc.communicate(payload.encode("utf-8"), timeout=timeout)
        return subprocess.CompletedProcess(proc.args, proc.returncode, out, err)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            if hasattr(os, "killpg"):
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
        out, err = proc.communicate()
        said = f"the hook did not answer within {timeout:g} s; its process group was killed\n".encode()
        return subprocess.CompletedProcess(proc.args, -9, out, said + err)


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
                  "git clean -fd",
                  # v6.7: merging, readying and branch protection are the human's. In the field the
                  # rule held only because the agent obeyed it; nothing refused `gh pr merge`.
                  "gh pr merge 12 --squash", "gh pr ready 12", "cd x && gh pr merge 3",
                  "gh api -X PATCH repos/o/r/branches/main/protection/required_status_checks -F strict=false",
                  "gh api repos/o/r/rulesets -f name=x", "gh api --method DELETE repos/o/r/branches/main/protection",
                  # the flags-anywhere forms the field probes walked through
                  "gh -R a/b pr merge 5", "gh pr -R a/b merge 5", "gh api repos/a/b/pulls/5/merge -X PUT",
                  # #142 (the M18 closure's S6): a short-option cluster holding `f`, and a mirror push.
                  "git push -uf origin x", "git push -fu origin x", "git push --mirror origin",
                  # The M19-W5 review's M1 and K1, the M19 security review's S5 and S6: a cluster with a
                  # digit, an abbreviated --mirror, a quoted -f or +refspec, a continued line, main
                  # named by its full ref, and the hosted engine deployed or destroyed by an agent.
                  "git push -4f origin x", "git push -f4 origin x", "git push --mi origin", "git push --mirr origin",
                  "git push origin '+x'", "git push '-f' origin x", "git push \\\n--force origin x",
                  "git push origin HEAD:refs/heads/main", "fly deploy --remote-only",
                  "flyctl apps destroy model-ranking", "scripts/deploy_hosted_engine.sh",
                  # The W5 Tester's M1: a dry run first, then the deploy, on one line.
                  "scripts/deploy_hosted_engine.sh --dry-run && scripts/deploy_hosted_engine.sh",
                  "scripts/deploy_hosted_engine.sh --dry-run | scripts/deploy_hosted_engine.sh",
                  # #189 (the second M19-W5 review's M1, M2 and K1): a command the text guard missed,
                  # spelled through an assignment, a wrapper, a subshell, a substitution or quotes, or
                  # another fly subcommand; read by `.claude/hooks/bash_guard.py`, which splits it.
                  "FLY_API_TOKEN=x fly deploy", "env fly deploy", "command fly deploy", "time fly deploy",
                  "(fly deploy)", "$(fly deploy)", "fly launch", "fly secrets set A=b", "fly scale count 0",
                  "fly machine stop x", "fly machine run img", "fly machine update x", "fly ssh console",
                  "MODEL_RANKING_SERVED=x scripts/deploy_hosted_engine.sh", "git push origin 'HEAD:main'",
                  "git push origin \\+x", "git push origin ''+x", "(git push --force origin x)",
                  "$(git push -f origin x)", "git push \\\r\n--force origin x", "(rm -rf ~/work)", "`rm -rf x`",
                  "$(git reset --hard HEAD~1)", "bash -c 'fly deploy'", "eval \"git push --force origin x\"",
                  "git status\nfly deploy", "if true; then fly deploy; fi", "{ fly deploy; }", "! fly deploy",
                  "while true; do git push --force origin x; done",
                  # The release's Stage 5.1 verdict (RS1): four mirror spellings and three deploys beside a
                  # dry run the text guard counted.
                  "git push origin \\--mirror", "git push origin $'--mirror'", "git push origin ''--mirror",
                  'git push origin ""--mirror', "scripts/deploy_hosted_engine.sh # deploy_hosted_engine.sh --dry-run",
                  "scripts/deploy_hosted_engine.sh; echo deploy_hosted_engine.sh --dry-run",
                  "echo deploy_hosted_engine.sh --dry-run; scripts/deploy_hosted_engine.sh",
                  # The M21-W4 review's B1: a comment line, a redirection, a here-string, or a "#" inside a word
                  # stopped the second reading, and the command after it passed.
                  '# check status first\nenv fly deploy', '# note\nFLY_API_TOKEN=x fly deploy',
                  '# note\n(fly deploy)', '>/dev/null fly deploy', '</dev/null fly deploy',
                  'fly >/dev/null secrets set A=b', '2>/dev/null fly launch',
                  '# push\nbash -c "git push --all origin"', '# x\ngit push origin \\--mirror',
                  'curl -s https://x.dev/#a; fly launch', 'fly status#x; fly launch',
                  'true # <<EOF\nfly launch\nEOF', 'cat <<< x\nfly launch\nx',
                  # The review's M1: git's unique option prefixes, a shell reading its script from stdin, the
                  # wrappers the lists lacked, and zsh's own forms.
                  'git push --m origin', 'git push --al origin', 'git push --branches origin',
                  'git reset --ha HEAD~1', 'git restore --staged --work x', "bash <<'EOF'\nfly launch\nEOF",
                  "bash <<'EOF'\ngit push origin \\--mirror\nEOF", "echo 'fly deploy' | bash",
                  "env -S 'fly deploy'", 'env -P /usr/local/bin fly deploy', 'echo deploy | xargs fly',
                  'coproc fly deploy', 'caffeinate -i fly deploy', "bash -c -- 'fly deploy'", '=fly deploy',
                  'noglob fly launch', 'nocorrect fly deploy', '- fly launch', 'repeat 1 fly launch',
                  'fl[y] deploy',
                  # The M21-W4 review, round 2: an unquoted here-document's body runs its substitutions (B1);
                  # arithmetic, nested backticks, `${ }`, zsh's forms (M1); a shell reading stdin, csh, heads/main
                  # (M2); an input too long or a brace to enumerate (M3); one case per item the docstring says
                  # it reads (M8); checkout, switch and stash that discard work (K1).
                  'git commit -q -F - <<EOF\nfix: the guard (M21-W4)\n\n- it now blocks `fly deploy` and `git push --all origin`\nEOF',
                  'gh pr create --draft --title \'M21-W4\' --body "$(cat <<EOF\n- agents run `fly launch` never\nEOF\n)"',
                  "cat > ../notes.md <<EOF\nRun `fly secrets set A=b` from the owner's terminal only.\nEOF",
                  'cat <<EOF | tee ../x.md\nPushed with $(git push origin HEAD:main)\nEOF',
                  'cat <<EOF\n$(fly deploy)\nEOF', 'echo $(( $(fly deploy) + 1 ))', '(( $(fly deploy) ))',
                  '$((fly deploy) )', 'echo `echo \\`fly deploy\\``',
                  "bash -c 'echo ${x:-{} ; fly launch ; echo }'", '{ true } always { fly deploy }',
                  'if true { fly deploy; }', "ls /etc/hosts(e:'fly deploy':)", "echo ${(e):-'$(fly deploy)'}",
                  "echo 'fly launch' | bash -", "bash /dev/stdin <<< 'fly launch'",
                  "bash /dev/stdin <<'EOF'\ngit push --all origin\nEOF",
                  "echo 'fly launch' | bash --rcfile /dev/null", "printf 'fly launch' | xargs -0 bash -c",
                  "source /dev/stdin <<< 'fly launch'", "tcsh -c 'fly launch'", "csh -c 'fly deploy'",
                  'git push origin heads/main', 'git push origin HEAD:heads/main',
                  '{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}{a,b}; fly launch',
                  'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                  'echo ${x:-$(fly deploy)}', 'echo x |& bash', 'bash < /tmp/script.sh',
                  'find . -name x -exec fly deploy \\;', 'source scripts/deploy_hosted_engine.sh',
                  'echo "`fly deploy`"', 'cat <(fly deploy)', 'echo origin | xargs git push',
                  # A pipe or a file wins over a here-string in this guard's reading (the round-2 review's M8).
                  "echo 'fly launch' |& bash <<< 'echo hi'", "bash < /tmp/script.sh <<< 'echo hi'",
                  'git checkout HEAD src/x.py', 'git checkout -f', 'git switch --discard-changes main',
                  'git stash clear',
                  # The M21-W4 Tester: what the docstring says it reads and no case held -- `rm`'s split and long
                  # options, `rm` behind a wrapper, and a shell given `-s` (each plant stayed green without them).
                  'rm -r -f build', 'rm --recursive --force build', 'sudo rm -r -f build',
                  'cat setup.sh | bash -s -- --quiet',
                  # It blocks what it cannot read: an unclosed quote, substitution or backtick (no case held these).
                  "echo 'not closed", 'echo "not closed', 'echo $(date', 'echo `date', 'echo ${HOME']
    MUST_ALLOW = ["git push -u origin fix/issue-3", "git push origin enhancement/x", "git push",
                  "git push --follow-tags origin x", "git push -4 origin x", "fly status", "fly logs",
                  # Named, not run: a message or a search that mentions them is no deploy.
                  "git commit -m 'fly deploy docs'", "grep -n deploy_hosted_engine.sh docs/release-testflight.md",
                  # The second W5 review's M2: an option or a branch that only starts like --mirror.
                  "git log --grep push --min-parents=2", "git push origin wave/m19--minor", "git push origin fix--mi",
                  "git status", "rm file.txt", "rm -r build",
                  "git reset HEAD~1", "npm run format",
                  "gh pr create --draft --title t", "gh pr view 12", "gh pr list --state open",
                  "gh api repos/o/r/branches/main/protection",
                  # the field's false positives: a commit message and a heredoc are data
                  "git commit -m 'fix: clean-module and go-fmt on main (#90)'",
                  "cat > t.sh <<'EOF'\ngit checkout -- .\nEOF",
                  # #189: the read-only fly subcommands, and a here-document whose body is data.
                  "fly auth whoami", "fly apps list", "fly version", "fly logs -a model-ranking",
                  "python3 - <<'EOF'\nprint(\"don't\")\nEOF", "git commit -m \"$(cat <<'EOF'\nIt's done\nEOF\n)\"",
                  # The review's M2: text inside quotes is not a command, and the commands this session runs.
                  "gh issue comment 189 --body 'the guard reads `fly deploy` and git push --all'",
                  'gh pr create --draft --title \'x\' --body "$(cat <<\'EOF\'\n- blocks `git push --all`\nEOF\n)"',
                  "cat <<< 'hello'", 'echo $((1<<2))',
                  'git commit -q -m "$(cat <<\'EOF\'\nfix: the guard\'s second reading -- #189 (M21-W4)\n\n- it blocks `fly deploy` and `git push --all`\nEOF\n)"',
                  "gh issue create --title 'a title' --body-file ../w4-122.md",
                  "gh pr create --draft --base main --title 'M21-W4' --body-file ../body.md",
                  'make check-fast > ../w4-cf.log 2>&1 && git add a.py b.md && git commit -q -m "fix: a\'s b (M21-W4)" -m "GP-Task: M21-W4" && git push -q origin wave/m21-w4',
                  'python3 - <<\'EOF\'\nfrom pathlib import Path\ns = "fly deploy" if 1 << 2 else \'x\'\nprint(s, "it\'s")\nEOF',
                  'for f in a b; do echo $f; done', 'git log --oneline 2ac522c..HEAD | cat',
                  # Round 2: a quoted delimiter's body is data; an unquoted one may hold harmless substitutions.
                  'cat > f <<EOF\nbuilt $(date)\nEOF',
                  "git commit -F - <<'EOF'\nfix: the guard no longer lets `fly deploy` through\nEOF",
                  'git checkout -b feature origin/main', 'git checkout wave/m21-w4', 'git switch -c x',
                  'x=(a b c); echo ${x[0]}', 'f() { echo hi; }; f', 'echo ${HOME:-/tmp}', 'echo $(( 2 + 3 ))',
                  # The M21-W4 Tester: a shell's `-c` string and here-document that read as harmless, and a `case`.
                  "bash -c 'echo hi'", "bash <<'EOF'\necho hi\nEOF", 'case $1 in a) echo a;; *) echo other;; esac',
                  ]
    # Run from the project itself (its `.claude/` and `.githooks/` are the owner's): the lists above run from
    # the home directory, where `rm -rf` of the temp directory's tree is scratch by design and no `.git` sits.
    MUST_BLOCK_HERE = [
                  # The M21 closure security seat's S3: the guard and the hooks are the owner's, so a write to
                  # `.claude/` or `.githooks/` through Bash is blocked; reading them is not.
                  'echo x > .claude/hooks/bash_guard.py', "sed -i '' 's/a/b/' .claude/settings.json",
                  'cp /tmp/x .githooks/pre-commit', 'rm .claude/hooks/bash_guard.py',
                  'printf x | tee .claude/settings.json', 'mv /tmp/g "$CLAUDE_PROJECT_DIR/.claude/hooks/bash_guard.py"',
                  'echo x >> .githooks/pre-push', "perl -pi -e 's/a/b/' .claude/hooks/bash_guard.py",
                  # The M21 closure fixes review's M6: a destination given as an option, and another case.
                  'cp -t .claude/hooks x.py', 'cp --target-directory=.githooks x', 'install -t .githooks x',
                  'dd if=x of=.claude/settings.json', 'cp x .CLAUDE/settings.json',
                  # Round 3, M2 and M7: `-t` ending a cluster, a value holding a `t`, and `install -d`'s every path.
                  'install -vt .githooks x', 'install -ostaff x .githooks/commit-msg', 'install -d .githooks/x build']
    # D-185 lets an agent run the deploy script's dry run. The brief may also declare the script a deploy
    # (`Deploy commands:`), and then the deploy gate refuses even the dry run until the release verdicts are
    # current: these run where no brief governs, so they grade the guard's own rule, not today's verdicts.
    MUST_ALLOW_NO_GATE = ["scripts/deploy_hosted_engine.sh --dry-run", "bash scripts/deploy_hosted_engine.sh --dry-run",
                          "sh scripts/deploy_hosted_engine.sh --dry-run", "fly status"]
    MUST_ALLOW_HERE = [
                  # S3: reading the guard, staging it and hashing it stay allowed.
                  'cat .claude/settings.json', 'git add .claude/hooks/bash_guard.py',
                  'shasum -a 256 .claude/hooks/bash_guard.py', 'grep -n onFailure .claude/settings.json',
                  # The M21 closure fixes review, round 2, M6: `-t` is a destination for cp, mv, ln and install only,
                  # and with one the last word is a source; rsync's `-t` keeps times.
                  'rsync -t .claude/settings.json /tmp/out', 'cp -t /tmp/out .claude/settings.json',
                  # Round 3, M2: an option that takes a value is no `-t`, though its value holds a `t`.
                  'install -o root .claude/settings.json /tmp/out']
    # Scratch under `$TMPDIR` counts only where the hook's environment sets it, so the case sets it: a CI
    # runner with no TMPDIR must grade the same rule, not a different one (DevFlow v7.1.1).
    SCRATCH_ALLOW = "rm -rf \"$TMPDIR\"/scratch"
    bash_hook = next((h["hooks"][0]["command"] for h in hooks.get("PreToolUse", [])
                      if h.get("matcher") == "Bash"), None)
    # Every hook entry carries `timeout` and `"onFailure": "block"`: without them a hook that
    # hangs or cannot start does not block, and the guard is off exactly when it is slow.
    for event, entries in hooks.items():
        for entry in entries:
            for h in entry.get("hooks", []):
                where = f"{event} hook `{entry.get('matcher', '*')}`"
                if not isinstance(h.get("timeout"), int) or h["timeout"] <= 0:
                    bad.append(f"{where} carries no positive `timeout` -- a hook that hangs never blocks")
                if h.get("onFailure") != "block":
                    bad.append(f"{where} does not set `\"onFailure\": \"block\"` -- a hook that cannot start "
                               "lets the call through (Claude Code 2.1.295 and later read this field)")
    # The Bash hook pins the guard file by its sha256: the pin must be the file's current digest.
    guard = root / ".claude" / "hooks" / "bash_guard.py"
    if bash_hook is not None:
        pins = set(re.findall(r'\[ "\$h" = "([0-9a-f]{64})" \]', bash_hook))
        if "bash_guard.py" not in bash_hook or not pins:
            bad.append("the PreToolUse Bash hook does not run `.claude/hooks/bash_guard.py` under a sha256 pin -- "
                       "an agent could edit the guard that judges its own commands")
        elif not guard.is_file():
            bad.append("the PreToolUse Bash hook pins `.claude/hooks/bash_guard.py` and the file does not exist")
        else:
            have = hashlib.sha256(guard.read_bytes()).hexdigest()
            if pins != {have}:
                bad.append(f"the sha256 pin in .claude/settings.json ({', '.join(p[:12] for p in sorted(pins))}) is "
                           f"not .claude/hooks/bash_guard.py's ({have[:12]}) -- every Bash call is refused until "
                           "`make guard-pin` rewrites it")
    # `permissions.allow`: a `make <target>:*` wildcard lets an argument run anything.
    allow = json.loads(st.read_text(encoding="utf-8")).get("permissions", {}).get("allow", [])
    for rule in allow:
        if re.match(r"^(Bash|PowerShell)\(make\s+\S+:\*\)$", rule):
            bad.append(f"permissions.allow carries `{rule}` -- `make <target> VAR='<anything>'` then runs with no "
                       "prompt; allow the exact target instead")
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
        # The payload's `cwd` is the home directory: relative `rm -rf` targets resolve from it, and a
        # target under the temp directory would be scratch by design.
        home = str(pathlib.Path.home())

        # A case that names its own directory sends it as `cwd`, as Claude Code sends the session's.
        def cmd(c: str, cwd: pathlib.Path | str | None = None) -> str:
            return json.dumps({"tool_input": {"command": c}, "cwd": str(cwd or home)}, ensure_ascii=False)

        def fpath(f: str, cwd: pathlib.Path | None = None) -> str:
            return json.dumps({"tool_input": {"file_path": f}, **({"cwd": str(cwd)} if cwd else {})}, ensure_ascii=False)

        # (hook, label, payload, want_block, PATH or None for this machine's, extra env)
        cases: list[tuple[str, str, str, bool, str | None, dict]] = []
        with tempfile.TemporaryDirectory() as tmp:
            paths = hook_paths(pathlib.Path(tmp))
            if bash_hook is not None:
                cases += [("Bash", f"`{c}`", cmd(c), True, None, {}) for c in MUST_BLOCK]
                cases += [("Bash", f"`{c}`", cmd(c), False, None, {}) for c in MUST_ALLOW]
                cases.append(("Bash", f"`{SCRATCH_ALLOW}` with TMPDIR set", cmd(SCRATCH_ALLOW), False, None,
                              {"TMPDIR": tempfile.gettempdir()}))
                cases += [("Bash", f"`{c}` from the project", cmd(c, root), True, None, {}) for c in MUST_BLOCK_HERE]
                ungated = pathlib.Path(tmp) / "ungated"
                (ungated / ".claude" / "hooks").mkdir(parents=True)
                shutil.copy(root / ".claude" / "hooks" / "bash_guard.py", ungated / ".claude" / "hooks")
                cases += [("Bash", f"`{c}` where no brief declares a deploy", cmd(c), False, None,
                           {"CLAUDE_PROJECT_DIR": str(ungated)}) for c in MUST_ALLOW_NO_GATE]
                cases += [("Bash", f"`{c}` from the project", cmd(c, root), False, None, {}) for c in MUST_ALLOW_HERE]
                # v7.1's scratch and the owner's directories together: `rm -rf` of a worktree under
                # `.claude/worktrees/` passes, of anything else in `.claude/` it does not.
                cases += [("Bash", f"`{c}` from the project", cmd(c, root), want, None, {})
                          for c, want in (("rm -rf .claude/worktrees/agent-x", False), ("rm -rf .claude/hooks", True),
                                          ("rm -rf .claude", True), ("rm -rf .claude/worktrees", True),
                                          ("find .claude -delete", True))]
                # S3: the hook pins the guard's sha256; one changed byte blocks every command.
                changed = pathlib.Path(tmp) / "changed"
                (changed / ".claude" / "hooks").mkdir(parents=True)
                guard = (root / ".claude" / "hooks" / "bash_guard.py").read_bytes()
                (changed / ".claude" / "hooks" / "bash_guard.py").write_bytes(guard + b"\n")
                cases.append(("Bash", "`git status` with the guard changed by one byte", cmd("git status"), True,
                              None, {"CLAUDE_PROJECT_DIR": str(changed)}))
                # The fixes review, round 2, M8: after a pull the pin is already right and only a new session helps,
                # so the line says to restart one, and where the owner's re-pin is written.
                said = _err(run_hook(bash, bash_hook, cmd("git status"), None, {"CLAUDE_PROJECT_DIR": str(changed)}))
                if PIN_ALTERED not in said or "restart" not in said or "INSTALL.md" not in said:
                    bad.append(f"the pin's BLOCKED line names neither the restart nor INSTALL.md: `{said[:120]}`")
                # M6: the pin holds the guard's bytes, and `python3 -I` keeps a module beside it from changing
                # what it imports: a `json.py` there that allows everything changes nothing.
                shadow = pathlib.Path(tmp) / "shadow"
                (shadow / ".claude" / "hooks").mkdir(parents=True)
                (shadow / ".claude" / "hooks" / "bash_guard.py").write_bytes(guard)
                (shadow / ".claude" / "hooks" / "json.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
                cases.append(("Bash", "`env fly deploy` with a json.py beside the guard", cmd("env fly deploy"), True,
                              None, {"CLAUDE_PROJECT_DIR": str(shadow)}))
            if env_hook:
                # M6: a link into the project's .githooks/ is the project's .githooks/.
                (pathlib.Path(tmp) / "hooks-link").symlink_to(root / ".githooks")
                cases += [("Write", f"a write to `{f}`", fpath(f), want, None, {})
                          for f, want in ((".env", True), ("cfg/.env.prod", True), ("prod.env", True),
                                          ("src/app.py", False), ("README.md", False),
                                          # v7.1: a secrets file by its name, and only by its name.
                                          (".envrc", True), (".env.example", False), ("src/config.env.py", False),
                                          # S3: the hooks and settings are the owner's, by the Edit tool too.
                                          (".claude/settings.json", True), (".githooks/pre-commit", True),
                                          (str(root / ".claude" / "hooks" / "bash_guard.py"), True),
                                          (str(root / ".CLAUDE" / "settings.json"), True),
                                          (str(pathlib.Path(tmp) / "hooks-link" / "pre-push"), True),
                                          ("docs/claude.md", False))]
            # The M21 closure fixes review, round 2, B1 and M6: the hooks and settings of EVERY work tree are the
            # owner's -- a linked worktree's (a `.git` file) and a clone's (a `.git` directory) as much as the
            # project's -- each path resolved from the payload's `cwd`, through a `cd` or `git -C` in the command and
            # through a link, and case-folded. A `.claude/` whose parent holds no `.git` (Claude Code's own
            # `~/.claude`) is not; neither is a read, nor a `-t` that is not a destination.
            trees = pathlib.Path(tmp) / "trees"
            worktree, clone, plain, fake_home = (trees / name for name in ("worktree", "clone", "plain", "home"))
            for d in (worktree / ".githooks", worktree / ".claude", worktree / "ios", clone / ".git", clone / ".githooks",
                      plain / ".claude", plain / ".githooks", fake_home / ".claude" / "projects"):
                d.mkdir(parents=True)
            (worktree / ".git").write_text("gitdir: /nowhere/.git/worktrees/worktree\n", encoding="utf-8")
            (trees / "worktree-hooks").symlink_to(worktree / ".githooks")
            at_home = {"HOME": str(fake_home)}
            # Round 3, M1: Claude Code makes worktrees inside a repository's `.claude/` (`claude --worktree`, a
            # subagent's `isolation: "worktree"`). Such a worktree is its own work tree: its files are writable,
            # its own `.claude/` and `.githooks/` are not.
            inner = clone / ".claude" / "worktrees" / "x"
            for d in (inner / "src", inner / ".claude", inner / ".githooks"):
                d.mkdir(parents=True)
            (inner / ".git").write_text("gitdir: /nowhere/.git/worktrees/x\n", encoding="utf-8")
            if bash_hook is not None:
                cases += [("Bash", f"`{c}` from {cwd.relative_to(trees)}", cmd(c, cwd), want, None, extra)
                          for c, cwd, want, extra in (
                              ("cp notes.md .githooks/commit-msg", worktree, True, {}),
                              (f"cp notes.md {worktree / '.githooks' / 'commit-msg'}", plain, True, {}),
                              ("cd ios && cp x ../.githooks/y", worktree, True, {}),
                              ("pushd ios && cp x ../.claude/settings.json", worktree, True, {}),
                              ("cp x ../.githooks/y", worktree / "ios", True, {}),
                              ("cp x worktree-hooks/y", trees, True, {}),
                              ("cp x .GITHOOKS/y", worktree, True, {}),
                              ("echo x > .Claude/settings.json", clone, True, {}),
                              (f"git -C {worktree} rm .githooks/commit-msg", plain, True, {}),
                              ("cp -t .githooks x", worktree, True, {}),
                              ("cp notes.md .claude/settings.json", plain, False, {}),
                              ("cat .githooks/commit-msg", worktree, False, {}),
                              ("mkdir -p ~/.claude/plans", plain, False, at_home),
                              ('cp notes.md "$HOME/.claude/CLAUDE.md"', plain, False, at_home),
                              # Round 3, M1: a worktree inside the clone's `.claude/` is a work tree of its own.
                              ("echo x > src/f.py", inner, False, {}),
                              ("touch src/new.py", inner, False, {}),
                              ("echo x > .githooks/commit-msg", inner, True, {}),
                              ("cp x .claude/settings.json", inner, True, {}),
                              # M1: in commands joined by `;`, `&&`, `||` and pipes, a `cd` that leaves a directory
                              # leaves it; a `cd` that may fail keeps the directory before it.
                              ("cd .claude && ls && cd .. && echo x > notes.txt", clone, False, {}),
                              ("cd .claude && ls | head -3 && cd .. && echo x > notes.txt", clone, False, {}),
                              ("cd ~ && mkdir -p .claude/plans", clone, False, at_home),
                              ("cd a1 && cd a2 && cd a3 && cd a4 && cd a5 && cd a6 && cd a7 && cd a8 && touch f", plain,
                               False, {}),
                              ("cd .claude; echo x > notes.txt", clone, True, {}),
                              ("cd ios && cd .. && touch .githooks/x", worktree, True, {}),
                              ("cd ios || echo no; touch .githooks/x", worktree, True, {}),
                              ("cd .claude || echo x > notes.txt", clone, False, {}),
                              # `time` runs its `cd` in the shell, as `builtin` and `command` do; a subshell's `cd`
                              # moves nothing after it, and an `eval`'s moves everything after it.
                              ("time cd .githooks; touch commit-msg", worktree, True, {}),
                              ("(cd ios) && touch .githooks/x", worktree, True, {}),
                              ('eval "cd .githooks" && touch commit-msg', worktree, True, {}),
                              # Round 3, M7: elsewhere every directory a `cd` reached is kept, and each `cd` is taken
                              # from each of them -- after one made in a subshell, too (G13) -- up to MAX_DIRS (G14).
                              ("(cd ios); cd .githooks && touch x", worktree, True, {}),
                              ("(cd a1; cd a2; cd a3; cd a4; cd a5; cd a6; cd a7; cd a8)", plain, True, {}))]
            if env_hook:
                cases += [("Write", f"a write to `{f}`" + (f" from {cwd.relative_to(trees)}" if cwd else ""),
                           fpath(f, cwd), want, None, extra)
                          for f, cwd, want, extra in (
                              (str(worktree / ".githooks" / "commit-msg"), None, True, {}),
                              (str(worktree / ".claude" / "settings.json"), None, True, {}),
                              (str(clone / ".githooks" / "pre-push"), None, True, {}),
                              (".githooks/commit-msg", worktree, True, {}),
                              ("../.githooks/x", worktree / "ios", True, {}),
                              (str(worktree / ".Claude" / "settings.json"), None, True, {}),
                              (str(trees / "worktree-hooks" / "pre-push"), None, True, {}),
                              (str(plain / ".claude" / "settings.json"), None, False, {}),
                              (".claude/x", plain, False, {}),
                              (str(fake_home / ".claude" / "projects" / "x" / "MEMORY.md"), None, False, at_home),
                              # Round 3, M1: a worktree inside the clone's `.claude/`.
                              (str(inner / "src" / "f.py"), None, False, {}),
                              ("src/f.py", inner, False, {}),
                              (str(inner / ".claude" / "settings.json"), None, True, {}),
                              (str(clone / ".claude" / "settings.json"), None, True, {}))]
                # One refusal for both hooks: the Write hook runs the pinned guard, so a changed guard blocks it too.
                cases.append(("Write", "a write with the guard changed by one byte", fpath("README.md"), True, None,
                              {"CLAUDE_PROJECT_DIR": str(changed)}))
            # M6: every interpreter the hooks start runs with -I, so a module in the directory a hook runs in (the
            # project, which an agent writes) changes nothing. With a json.py there that exits 0, the guard still
            # refuses with its own message, and the Write hook still refuses.
            for kind, entry in (("Bash", bash_hook), ("Write", env_hook)):
                for unisolated in re.findall(r'"\$py"\s+(?!-I -S\b|\])[^;|]{0,40}', entry or ""):
                    bad.append(f"the PreToolUse {kind} hook starts an interpreter without -I -S: `{unisolated}`")
            # Round 3, R1: `-S` too, so the site-packages of the interpreter found on PATH change nothing: a `.venv`
            # first on PATH whose site-packages holds a `.pth` that ends the guard with exit 0 changes no verdict.
            venv = pathlib.Path(tmp) / "venv"
            made = subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], capture_output=True,
                                  timeout=120, check=False)
            site = next(iter(sorted((venv / "lib").glob("python*/site-packages"))), None) if made.returncode == 0 else None
            if site is None:
                unevaluable.append("no virtual environment could be made here, so the -S case was not graded")
            else:
                (site / "zz_guard.pth").write_text('import os, sys; sys.argv[:1] and sys.argv[0].endswith("bash_guard.py")'
                                                   ' and os._exit(0)\n', encoding="utf-8")
                first = os.pathsep.join((str(venv / "bin"), os.environ.get("PATH", "")))
                for kind, entry, payload in (("Bash", bash_hook, cmd("echo x > .githooks/commit-msg", root)),
                                             ("Write", env_hook, fpath(".githooks/commit-msg"))):
                    if entry and run_hook(bash, entry, payload, first).returncode != 2:
                        bad.append(f"the PreToolUse {kind} hook let a write into .githooks/ through with a .pth in the "
                                   "site-packages of the python3 first on PATH")
            planted = pathlib.Path(tmp) / "planted"
            planted.mkdir()
            (planted / "json.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
            if bash_hook is not None:
                r = run_hook(bash, bash_hook, cmd("git push origin main"), None, {}, cwd=planted)
                if r.returncode != 2 or "never pushes the protected branch" not in _err(r):
                    bad.append(f"the guard did not refuse `git push origin main` for its reason with a json.py where the hook runs "
                               f"(exit {r.returncode}; {_err(r)[:90] or 'no message'})")
            if env_hook:
                r = run_hook(bash, env_hook, fpath("cfg/.env"), None, {}, cwd=planted)
                if r.returncode != 2:
                    bad.append(f"the Write hook did not block a .env write with a json.py where it runs (exit {r.returncode})")
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
            # The Bash guard needs nothing but an interpreter: with only `python3` on PATH (no git,
            # no grep) it still refuses the push to the protected branch for ITS reason, and allows
            # `git status`.
            if bash_hook is not None:
                r = run_hook(bash, bash_hook, cmd("git push origin main"), paths["python-only"])
                if r.returncode != 2 or "never pushes the protected branch" not in _err(r):
                    bad.append(f"PreToolUse Bash guard with only python3 on PATH: exit {r.returncode}, "
                               f"first stderr line `{_err(r)[:90]}` -- it must refuse the push to the "
                               "protected branch with its own reason, needing no other tool")
                r = run_hook(bash, bash_hook, cmd("git status"), paths["python-only"])
                if r.returncode != 0:
                    bad.append(f"PreToolUse Bash guard with only python3 on PATH wrongly refused `git status` "
                               f"(exit {r.returncode}; {_err(r)[:90]})")
                # The pin: an altered guard, and a missing one, refuse every call -- even `git status`.
                scratch = pathlib.Path(tmp) / "pinned"
                (scratch / ".claude" / "hooks").mkdir(parents=True)
                guard_src = root / ".claude" / "hooks" / "bash_guard.py"
                (scratch / ".claude" / "hooks" / "bash_guard.py").write_text(
                    guard_src.read_text(encoding="utf-8") + "\n# altered\n", encoding="utf-8")
                r = run_hook(bash, bash_hook, cmd("git status"), None, {"CLAUDE_PROJECT_DIR": str(scratch)})
                if r.returncode != 2 or PIN_ALTERED not in _err(r):
                    bad.append(f"PreToolUse Bash guard ran an ALTERED .claude/hooks/bash_guard.py (exit "
                               f"{r.returncode}; `{_err(r)[:90]}`) -- the pin in .claude/settings.json does not hold")
                (scratch / ".claude" / "hooks" / "bash_guard.py").unlink()
                r = run_hook(bash, bash_hook, cmd("git status"), None, {"CLAUDE_PROJECT_DIR": str(scratch)})
                if r.returncode != 2 or PIN_MISSING not in _err(r):
                    bad.append(f"PreToolUse Bash guard with .claude/hooks/bash_guard.py MISSING: exit "
                               f"{r.returncode}, `{_err(r)[:90]}` -- it must refuse every call, never skip")
                # The M21-W4 Tester's M5: a hook that does not answer is a failure with its label, never a
                # traceback that hides the run's other findings, and nothing it started outlives it.
                r = run_hook(bash, "sleep 30", "{}", None, timeout=1)
                if r.returncode in (0, 2):
                    bad.append(f"run_hook returned {r.returncode} for a hook that did not answer within its limit")
                # The M21-W4 review, round 2, M3: a hook that times out does not block (Claude Code proceeds
                # with the call), so the guard answers within its own bound, and the hook blocks on failure.
                started = time.monotonic()
                r = run_hook(bash, bash_hook, cmd("{a,b}" * 30 + "; fly launch"), None)
                if r.returncode != 2 or time.monotonic() - started > 20:
                    bad.append(f"PreToolUse Bash guard took {time.monotonic() - started:.1f} s (exit {r.returncode}) on a "
                               "brace word it would have to enumerate -- it must block within its own bound")
                entry = next(h for h in hooks.get("PreToolUse", []) if h.get("matcher") == "Bash")["hooks"][0]

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
