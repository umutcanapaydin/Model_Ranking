#!/usr/bin/env python3
"""The Bash guard refuses what it claims and stays quiet on the field's false positives, run as Claude Code runs it.

WHY. The guard that shipped before this test was a set of regular expressions over the raw command
text, and two field projects measured it over two weeks: every refusal on a deploy command was wrong
(commit messages, issue comments, heredocs, a self-test that named the command), a commit message
`... on main (#90)` matched the push-main rule, a heredoc with `git checkout -- .` matched the
destructive rule, sixteen refusals were `rm -rf` of the agent's own scratch directory -- and the real
evasions walked through: `FLY DEPLOY`, `fly  deploy`, `a=xcodebuild; $a ...`, `gh -R a/b pr merge`,
a deploy from a subdirectory, a deploy with the gate script missing. Each of those is a case here, in
the polarity it must hold.

HOW. Every case is the hook's JSON on stdin -- `{"tool_input": {"command": ...}, "cwd": ...}` -- fed
to the `Bash` hook command lifted from `.claude/settings.json`, through bash, with
`CLAUDE_PROJECT_DIR` set: exactly what Claude Code does. Blocked means exit 2; allowed means exit 0;
any other exit is a finding. The deploy cases run in a throwaway git repository with a brief, the
gate script and the two verdicts, so the guard resolves the repository from the call's own directory,
worktree included, and never from the main checkout. The `rm -rf` cases run from the home directory,
because a target under the system temp directory is scratch by design.

model_ranking: this project's guard refuses `fly` and `flyctl` but their read-only subcommands whatever
the gate says (D-185), so the gate's fixture declares `vercel deploy` where DevFlow's declares `fly
deploy`; the D-185 cases sit beside them, and `tests/unit/test_bash_guard_bounds.py` holds the rest.

Exit 0 clean · 1 findings · 2 not evaluable here (no bash, or no git to build the fixture).
"""
import concurrent.futures
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, runnable_bash, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
GUARD = ROOT / ".claude" / "hooks" / "bash_guard.py"
TMP = tempfile.gettempdir()


def payload(command: str, cwd: pathlib.Path) -> str:
    return json.dumps({"tool_input": {"command": command}, "cwd": str(cwd)}, ensure_ascii=False)


def git(root: pathlib.Path, *args: str) -> str:
    r = subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", *args], cwd=root,
                       capture_output=True, encoding="utf-8", errors="replace", env=scrubbed_env(), timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def verdict(root: pathlib.Path, rel: str, head: str, text: str = "PASS") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"# verdict\n\n**Independent:** yes\n\n## Verdict\n{text}\n\n**Reviewed head:** {head}\n",
                 encoding="utf-8")


def fixture(base: pathlib.Path) -> tuple[pathlib.Path, str]:
    """A project with a brief naming three deploy commands, the gate, the guard and current verdicts."""
    r = base / "proj"
    for d in ("docs/reviews", "scripts", "src", "sub", ".claude/hooks", ".claude/agents", ".claude/skills/fix-issue"):
        (r / d).mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "deploy_gate.py", r / "scripts")
    shutil.copy(ROOT / "scripts" / "brief_fields.py", r / "scripts")
    shutil.copy(GUARD, r / ".claude" / "hooks")
    (r / "docs" / "project-brief.md").write_text(
        "- **Working mode:** `light`\n"
        "- Deploy commands: `vercel deploy`, `./deploy.sh`, `xcodebuild -scheme App archive`\n", encoding="utf-8")
    (r / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    (r / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (r / ".claude" / "agents" / "Security-Reviewer.md").write_text("# profile\n", encoding="utf-8")
    (r / ".claude" / "skills" / "fix-issue" / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (r / "Makefile").write_text("x:\n\ttrue\n", encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-qm", "base")
    head = git(r, "rev-parse", "HEAD")
    verdict(r, "docs/reviews/release-security.md", head)
    verdict(r, "docs/reviews/release-tester.md", head)
    git(r, "add", "-A")
    git(r, "commit", "-qm", "verdicts")
    return r, head


def main() -> int:
    bash, why = runnable_bash("run the Bash hook in .claude/settings.json")
    if not bash:
        print(f"test-bash-guard NOT-EVALUABLE: {why}")
        return 2
    if (no_git := missing_tool("git", "build the deploy-gate fixture")):
        print(f"test-bash-guard NOT-EVALUABLE: {no_git}")
        return 2
    if not GUARD.is_file():
        print(f"test-bash-guard FAIL: {GUARD.relative_to(ROOT)} does not exist -- the Bash hook has nothing to run")
        return 1
    hooks = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))["hooks"]
    hook = next((h["hooks"][0]["command"] for h in hooks.get("PreToolUse", []) if h.get("matcher") == "Bash"), None)
    if hook is None:
        print("test-bash-guard FAIL: no PreToolUse Bash hook in .claude/settings.json")
        return 1
    home = pathlib.Path.home()
    if str(home.resolve()).startswith(str(pathlib.Path(TMP).resolve())):
        print(f"test-bash-guard NOT-EVALUABLE: the home directory {home} lies under the temp directory, so no "
              "`rm -rf` case can be told from scratch here")
        return 2

    # (label, command, cwd, env extra, want_block, a fragment the refusal must carry or "")
    cases: list[tuple[str, str, pathlib.Path, dict, bool, str]] = []
    # TMPDIR set explicitly: `$TMPDIR` is scratch only where the hook's environment has it, and a CI runner
    # without one must grade the same cases (DevFlow v7.1.1).
    env_pkg = {"CLAUDE_PROJECT_DIR": str(ROOT), "TMPDIR": TMP}
    for c in (
        # the human's steps, with flags anywhere
        "gh pr merge 5", "gh pr ready 5", "gh -R a/b pr merge 5", "gh pr -R a/b merge 5", "gh --repo a/b pr ready 5",
        "gh api repos/a/b/pulls/5/merge -X PUT", "gh api -X PUT repos/a/b/pulls/5/merge", "gh api repos/a/b/pulls/5/merge",
        "cd x && gh pr merge 3", "gh api repos/o/r/rulesets -f name=x",
        "gh api --method DELETE repos/o/r/branches/main/protection",
        "gh api -X PATCH repos/o/r/branches/main/protection/required_status_checks -F strict=false",
        # the protected branch and destructive git
        "git push origin main", "git push origin master", "git push o trunk", "git push origin HEAD:main",
        "git push origin refs/heads/main", "git push --force origin x", "git push -f o x", "git push origin +x",
        "git push --all origin", "git push --mirror o", "git -C sub push origin main", "git reset --hard HEAD~1",
        "git clean -fd", "git checkout -- .", "git checkout .", "git checkout -- src/a.py", "git checkout -f x",
        "git checkout main a.py", "git restore src/a.py", "git restore --worktree --staged a", "git switch -f x",
        "git stash clear",
        # a skipped hook, a moved protected ref, a shell write to a secrets file, find -delete (v7.1)
        "git push --no-verify -u origin fix/x", "git commit -n -m x", "git commit --no-verify -m x",
        "git -c core.hooksPath=/dev/null push -u origin fix/x", "git merge --no-verify fix/x",
        "git update-ref -d refs/heads/main", "git update-ref refs/heads/main HEAD~3",
        "echo X=1 > .env", "echo X=1 >> .env", "cat > .env <<'EOF'\nA=1\nEOF", "cp other .env", "mv tmp .env",
        "tee .env.production < x", "printf 'A=1' > config/.env.local", "echo x > .envrc", "echo x > prod.env",
        "find . -name '*.pyc' -delete", "find src -type f -delete",
        # rm -rf outside scratch
        "rm -rf .", "rm -rf ~/work", "rm -fr /home/u", "rm -r -f build", "rm --recursive --force x",
        "rm -rf $BUILD_DIR", "rm -rf .claude/worktrees", "rm -rf",
        # the same, behind what the shell runs
        "bash -c 'git push origin main'", "sh -c \"git push origin main\"", "eval 'git push origin main'",
        "x=$(git push origin main)", "`git push origin main`", "a=git; $a push origin main",
        "export a=git; $a push origin main", "sudo git push origin main", "env FOO=1 git push origin main",
        "echo hi | xargs git push origin", "find . -name x -exec rm -rf {} +",
        "if true; then git push origin main; fi", "git push origin main # comment", "git   push    origin main",
        "cat <<EOF\n$(git push origin main)\nEOF",
        # what it cannot read
        "gi* push", "bash < script.sh", "cat x.sh | sh", "bash -c", "echo 'unclosed",
    ):
        cases.append((f"`{c}`", c, home, env_pkg, True, ""))
    for c in (
        # the field's false positives: a commit message, a heredoc, an echo
        "git commit -m \"fix: run clean-module and go-fmt on main (#90)\"", "git commit -m 'push to main'",
        "git commit -m 'a' -m 'gh pr merge 1'",
        "cat > t.sh <<'EOF'\ngit checkout -- .\nrm -rf /\nEOF", "cat <<EOF\ngit checkout -- .\nEOF",
        "echo \"git push origin main\"", "echo git push origin main", "printf '%s' 'rm -rf /'",
        "grep -r \"rm -rf\" .", "python3 -c \"print('git push origin main')\"", "echo done # git push origin main",
        "gh issue comment 3 -b \"then gh pr merge it\"",
        # ordinary git and gh
        "git status", "git push", "git push -u origin fix/issue-3", "git push origin fix/main-page", "git push origin main-2",
        "git reset HEAD~1", "git checkout main", "git checkout -b feature/x", "git checkout HEAD~1", "git restore --staged a",
        "git stash", "git log --oneline -5 main", "git diff main..HEAD", "git branch -D main",
        "git commit -am 'x' && git push -u origin feat/x",
        "gh pr view 12", "gh pr create --draft --title t", "gh pr list --state open",
        "gh api repos/o/r/branches/main/protection",
        # rm that is not both recursive and forced, and rm of scratch
        "rm file.txt", "rm -r build", "rm -rf $TMPDIR/x", "rm -rf \"$TMPDIR\"/x", f"rm -rf {TMP}/probe",
        "d=$(mktemp -d) && rm -rf \"$d\"", "d=$(mktemp -d); rm -rf $d/sub", "D=`mktemp -d`; rm -rf $D",
        "rm -rf .claude/worktrees/agent-x", "rm -rf /abs/path/.claude/worktrees/agent-y", "rm -rf -- /tmp/zz",
        "TMPD=/tmp/scratch; rm -rf $TMPD/x",
        # the same shapes, where no gate is skipped and no secrets file is written
        "git push -u origin fix/x", "git commit -m 'no --no-verify here'", "git push -n origin fix/x",
        "git -c user.name=x commit -m y", "git update-ref refs/heads/fix/x HEAD", "echo X > .env.example",
        "echo hi > out.txt", "tee -a .claude/last-check.log", "cp .env.example .env.sample", "echo x > src/config.env.py", f"find {TMP}/x -delete",
        "find . -name '*.pyc'", "cat .env", "grep KEY .env",
        # shell shapes that are not commands
        "ls -la", "make test", "echo \"$(echo hi)\"", "for f in a b; do echo $f; done", "case x in a) echo a;; esac",
        "x=1; y=2; echo $((x+y))", "echo \u2192 done", "$UNSET deploy",
    ):
        cases.append((f"`{c}`", c, home, env_pkg, False, ""))

    bad: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        try:
            proj, head = fixture(base)
        except (RuntimeError, OSError) as error:
            print(f"test-bash-guard NOT-EVALUABLE: the fixture could not be built ({error})")
            return 2
        env_proj = {"CLAUDE_PROJECT_DIR": str(proj)}
        # The deploy gate, everything current: the deploy and the ordinary commands pass.
        for c in ("vercel deploy", "./deploy.sh prod", "vercel status", "echo 'vercel deplo'y", "echo 'vercel deploy'",
                  "git commit -m 'vercel deploy notes'", "x='vercel deploy'; echo $x", "ls"):
            cases.append((f"`{c}` with every verdict current", c, proj, env_proj, False, ""))
        # model_ranking (D-185): the hosted engine is the owner's to deploy or destroy whatever the gate says,
        # so `fly`/`flyctl` but its read-only subcommands, and the deploy script but its dry run, are refused
        # with every verdict current. The gate's own cases above and below therefore name `vercel`.
        for c in ("fly deploy", "flyctl apps destroy model-ranking", "fly launch", "sudo fly deploy",
                  "scripts/deploy_hosted_engine.sh", "bash scripts/deploy_hosted_engine.sh --prod"):
            cases.append((f"`{c}` with every verdict current (D-185)", c, proj, env_proj, True, "D-185"))
        for c in ("fly status", "fly logs -a model-ranking", "scripts/deploy_hosted_engine.sh --dry-run"):
            cases.append((f"`{c}` with every verdict current (D-185)", c, proj, env_proj, False, ""))
        # One code file after the reviewed head: every spelling of the deploy is refused, nothing else is.
        dirty = base / "dirty"
        shutil.copytree(proj, dirty, symlinks=True)
        (dirty / "src" / "b.py").write_text("y = 2\n", encoding="utf-8")
        for c in ("vercel deploy", "VERCEL DEPLOY", "vercel  deploy", "'vercel' deplo'y'", "verc'el' deploy", "/usr/local/bin/vercel deploy",
                  "vercel --verbose deploy -a app", "a=vercel; $a deploy", "sudo vercel deploy", "env FOO=1 vercel deploy",
                  "bash -c 'vercel deploy'", "eval 'vercel deploy'", "x=$(vercel deploy)", "cd sub && vercel deploy",
                  "bash ./deploy.sh prod", "./deploy.sh", "xcodebuild -scheme App archive",
                  "a=xcodebuild; $a -scheme App archive", "if true; then vercel deploy; fi"):
            cases.append((f"`{c}` with code changed after the reviewed head", c, dirty, env_proj, True,
                          "changed since the reviewed head"))
        for c in ("echo 'vercel deplo'y", "echo 'vercel deploy'", "git commit -m 'vercel deploy notes'", "x='vercel deploy'; echo $x",
                  "gh issue comment 3 -b 'run vercel deploy after'", "vercel status", "cat <<'EOF'\nvercel deploy\nEOF", "ls"):
            cases.append((f"`{c}` with code changed (not a deploy)", c, dirty, env_proj, False, ""))
        # S1: from a subdirectory, and with CLAUDE_PROJECT_DIR unset -- the repository is the call's own.
        cases.append(("`vercel deploy` from a subdirectory, CLAUDE_PROJECT_DIR unset", "vercel deploy", dirty / "sub",
                      {"CLAUDE_PROJECT_DIR": ""}, True, "changed since the reviewed head"))
        cases.append(("`vercel deploy` from outside any repository, CLAUDE_PROJECT_DIR the project", "vercel deploy", base,
                      {"CLAUDE_PROJECT_DIR": str(dirty)}, True, "changed since the reviewed head"))
        # S1: a brief with no gate script beside it refuses every call, never skips.
        gone = base / "gone"
        shutil.copytree(proj, gone, symlinks=True)
        (gone / "scripts" / "deploy_gate.py").unlink()
        cases.append(("`ls` in a tree whose brief declares deploys and whose gate script is missing", "ls", gone,
                      {"CLAUDE_PROJECT_DIR": str(gone)}, True, "has no scripts/deploy_gate.py"))
        # S3: a profile, a skill, a hook, the Makefile and a workflow are code whatever their extension.
        for rel in (".claude/agents/Security-Reviewer.md", ".claude/skills/fix-issue/SKILL.md", "Makefile",
                    ".github/workflows/ci.yml", "scripts/notes.md", "conformance/README.md", ".githooks/pre-push"):
            t = base / ("code-" + rel.replace("/", "_"))
            shutil.copytree(proj, t, symlinks=True)
            (t / rel).parent.mkdir(parents=True, exist_ok=True)
            (t / rel).write_text("# edited after the reviewed head\n", encoding="utf-8")
            cases.append((f"`vercel deploy` after `{rel}` changed", "vercel deploy", t, {"CLAUDE_PROJECT_DIR": str(t)}, True,
                          "changed since the reviewed head"))
        for rel in ("docs/notes.md", "README.md", "docs/decisions.md", "docs/cold-start.sh"):
            t = base / ("rec-" + rel.replace("/", "_"))
            shutil.copytree(proj, t, symlinks=True)
            (t / rel).parent.mkdir(parents=True, exist_ok=True)
            (t / rel).write_text("a record\n", encoding="utf-8")
            cases.append((f"`vercel deploy` after `{rel}` changed (a record)", "vercel deploy", t,
                          {"CLAUDE_PROJECT_DIR": str(t)}, False, ""))
        # The verdicts themselves: missing, BLOCKING, unfilled, no head; the Tester's too.
        for rel, text, want in (("docs/reviews/release-security.md", "BLOCKING", "has no PASS or MINOR"),
                                ("docs/reviews/release-security.md", "PASS | MINOR | BLOCKING", "has no PASS or MINOR"),
                                ("docs/reviews/release-tester.md", "BLOCKING", "has no PASS or MINOR")):
            t = base / ("verdict-" + rel.split("/")[-1] + text[:4].strip(" |"))
            shutil.copytree(proj, t, symlinks=True)
            verdict(t, rel, head, text)
            cases.append((f"`vercel deploy` with {rel} saying `{text}`", "vercel deploy", t, {"CLAUDE_PROJECT_DIR": str(t)},
                          True, want))
        for rel in ("docs/reviews/release-security.md", "docs/reviews/release-tester.md"):
            t = base / ("missing-" + rel.split("/")[-1])
            shutil.copytree(proj, t, symlinks=True)
            (t / rel).unlink()
            cases.append((f"`vercel deploy` with {rel} missing", "vercel deploy", t, {"CLAUDE_PROJECT_DIR": str(t)}, True,
                          f"there is no {rel}"))
        # Heavy mode reads the latest milestone Tester verdict, by its commit range's end.
        heavy = base / "heavy"
        shutil.copytree(proj, heavy, symlinks=True)
        (heavy / "docs" / "project-brief.md").write_text("- Deploy commands: `vercel deploy`\n", encoding="utf-8")
        cases.append(("`vercel deploy` in heavy mode with no milestone Tester verdict", "vercel deploy", heavy,
                      {"CLAUDE_PROJECT_DIR": str(heavy)}, True, "there is no milestone Tester verdict"))
        heavy_ok = base / "heavy-ok"
        shutil.copytree(heavy, heavy_ok, symlinks=True)
        (heavy_ok / "docs" / "reviews" / "m3-tester.md").write_text(
            f"# t\n**Independent:** yes\n\n## Verdict\nPASS\n\n**Reviewed head:** {head}\n", encoding="utf-8")
        cases.append(("`vercel deploy` in heavy mode with the milestone Tester at the head", "vercel deploy", heavy_ok,
                      {"CLAUDE_PROJECT_DIR": str(heavy_ok)}, False, ""))
        # A Tester verdict declares its independence, like every review verdict; one that does not is no verdict.
        dependent = base / "dependent"
        shutil.copytree(proj, dependent, symlinks=True)
        (dependent / "docs" / "reviews" / "release-tester.md").write_text(
            f"# t\n\n## Verdict\nPASS\n\n**Reviewed head:** {head}\n", encoding="utf-8")
        cases.append(("`vercel deploy` with a Tester verdict that declares no independence", "vercel deploy", dependent,
                      {"CLAUDE_PROJECT_DIR": str(dependent)}, True, "does not declare `**Independent:** yes`"))
        # S2b: the checkout the command runs in. The main checkout is dirty; the worktree is reviewed.
        wt_base = base / "wt"
        shutil.copytree(proj, wt_base, symlinks=True)
        try:
            w = base / "worktree"
            git(wt_base, "worktree", "add", "-q", str(w), "-b", "work")
            (wt_base / "src" / "a.py").write_text("dirty\n", encoding="utf-8")
            cases.append(("`vercel deploy` from a clean worktree while the main checkout is dirty", "vercel deploy", w,
                          {"CLAUDE_PROJECT_DIR": str(wt_base)}, False, ""))
            cases.append(("`vercel deploy` from the dirty main checkout", "vercel deploy", wt_base,
                          {"CLAUDE_PROJECT_DIR": str(wt_base)}, True, "changed since the reviewed head"))
            w2 = base / "worktree-2"   # its own worktree: the cases run side by side, so no tree serves two
            git(wt_base, "worktree", "add", "-q", str(w2), "-b", "work-2")
            (w2 / "src" / "a.py").write_text("w\n", encoding="utf-8")
            git(w2, "add", "-A")
            git(w2, "commit", "-qm", "w")
            cases.append(("`vercel deploy` from a worktree with a commit after the reviewed head", "vercel deploy", w2,
                          {"CLAUDE_PROJECT_DIR": str(wt_base)}, True, "changed since the reviewed head"))
        except RuntimeError as error:
            bad.append(f"the worktree fixture could not be built ({error})")

        def run(case: tuple[str, str, pathlib.Path, dict, bool, str]) -> str | None:
            label, command, cwd, extra, want_block, fragment = case
            env = scrubbed_env({k: v for k, v in extra.items() if v})
            for k, v in extra.items():
                if not v:
                    env.pop(k, None)
            r = subprocess.run([bash, "-c", hook], input=payload(command, cwd).encode("utf-8"), capture_output=True,
                               env=env, cwd=cwd, timeout=120)
            err = r.stderr.decode("utf-8", errors="replace").strip().splitlines()
            first = err[0] if err else ""
            if r.returncode not in (0, 2) or (r.returncode == 2) != want_block:
                return (f"the Bash guard {'failed to refuse' if want_block else 'wrongly refused'} {label} "
                        f"(exit {r.returncode}; {first[:110] or 'no message'})")
            if want_block and fragment and fragment not in first:
                return f"the Bash guard refused {label} for another reason: `{first[:110]}` (expected `{fragment}`)"
            if want_block and not first.startswith("BLOCKED:"):
                return f"the Bash guard refused {label} without a `BLOCKED:` line"
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as pool:
            bad += [b for b in pool.map(run, cases) if b]

    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-bash-guard {'FAIL' if bad else 'PASS'}: {len(cases)} tool call(s) fed to the Bash hook as Claude Code "
          f"feeds them, {len(bad)} wrong verdict(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
