#!/usr/bin/env python3
"""`make owner-bundle`: a change the agent may not make, as one patch the owner applies with one command.

    python3 scripts/owner_bundle.py [--src <dir>]           # build; <dir> (default build/owner-bundle/src) holds
                                                             # each proposed file at its path in this project
    python3 scripts/owner_bundle.py apply <patch> <sha256>  # the owner's command: check the sha, apply, re-pin

WHY (v7.3, harvest Q3, the owner's ruling of 2026-10-28). The agent never edits `.github/workflows/**`, and the
guard and its settings are the owner's. In one field project four such changes reached the owner as hand-made
bundles ("prepare me a one-command owner patch", "I must restart the session, the pin changed"), with six
security reviews, and the owner began using a second assistant that edits outside the guard.

THE BUILD writes the proposed files' difference from this tree as a git patch, `build/owner-bundle/<sha12>.patch`,
and prints its sha256, whether it owes a review, and the owner's one command. It never writes a tracked file, and
it refuses a file the patch would carry as a binary hunk: the owner must be able to read what they apply. A
bundle whose every file is DevFlow's own tooling, byte for byte as the installed release ships it (the brief's
`process_version:` tag in this clone), owes no review: that release reviewed those bytes, and the deploy gate
reads them as unchanged (`deploy_gate.shipped_unchanged`). Any other bundle owes the Security-Reviewer's
reading before the owner applies it: the verdict, a `docs/reviews/*-security.md`, names the patch it read as
`**Reviewed patch:** <sha256>`. Build and apply decide "DevFlow's bytes" the same way, from the patch applied to
a scratch index of HEAD -- never from the patch's own header lines.

THE APPLY refuses a patch whose sha256 is not the one the command names -- it changed after it was built, or it
is another bundle -- a binary hunk, one that does not apply cleanly to the index, and one that owes a review
with no PASS or MINOR verdict naming its sha; each leaves the tree as it was. Then it stages the change, runs
the guard-pin step when the guard changed, and says to restart Claude Code when anything under `.claude/`
changed: a session open across a guard or settings change keeps the hooks it started with. It applies from
the repository's top with the project's own prefix: from a subdirectory `git apply` skips every path outside it
and still exits 0.

Exit: 0 built or applied · 1 nothing to bundle, or refused · 2 cannot run here.
"""
from __future__ import annotations

import hashlib
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from deploy_gate import (DEVFLOW_TOOLING, DEVFLOW_TOOLING_FILES, INDEPENDENT, REVIEWED_PATCH, VERDICT,  # noqa: E402
                         _git, devflow_history)

OUT = Path("build/owner-bundle")
GUARD = ".claude/hooks/bash_guard.py"


def git(cwd: Path, *args: str, data: bytes | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, input=data, env=env)


def top_and_prefix(root: Path) -> tuple[Path, str] | None:
    """(the repository's top, this project's path inside it with a trailing `/`, or "")."""
    r = git(root, "rev-parse", "--show-toplevel", "--show-prefix")
    lines = r.stdout.decode().splitlines() if r.returncode == 0 else []
    return (Path(lines[0]), lines[1] if len(lines) > 1 else "") if lines else None


def binary_files(top: Path, patch: bytes) -> list[str]:
    """The files a patch carries as binary -- bytes nobody can read before applying them: git's own judgement (a
    `-\t-\t` row of `git apply --numstat`), and each notice git writes for one (`GIT binary patch`, `Binary files
    ... differ`, `Files ... differ`, which applies a blob already in the object store; Security-Reviewer R2)."""
    numstat = git(top, "apply", "--numstat", "-", data=patch).stdout.decode("utf-8", "replace").splitlines()
    out, current = [ln.split("\t", 2)[2] for ln in numstat if ln.startswith("-\t-\t")], ""
    for line in patch.decode("utf-8", "replace").splitlines():
        if line.startswith("diff --git "):
            current = line.rsplit(" ", 1)[-1].removeprefix("b/")
        elif line == "GIT binary patch" or (line.startswith(("Binary files ", "Files ")) and line.endswith(" differ")):
            out.append(current)
    return sorted(set(out))


def not_devflows(root: Path, top: Path, prefix: str, patch: bytes) -> list[str]:
    """The files this patch leaves that are not DevFlow's own tooling, byte for byte as the installed release ships
    it: the bundle owes a review for them. Read from the patch applied to a scratch copy of the index the apply
    uses, so a header that names other bytes than its hunks write cannot pass; a patch that does not apply there
    owes the review."""
    history = devflow_history(root)
    version = history[0] if history else None
    files = [ln.split("\t")[-1] for ln in git(top, "apply", "--numstat", "-", data=patch).stdout.decode().splitlines()]
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(tmp, "index"))}
        directory = [f"--directory={prefix.rstrip('/')}"] if prefix else []
        index = Path(git(top, "rev-parse", "--git-path", "index").stdout.decode().strip())
        index = index if index.is_absolute() else top / index
        if index.is_file():
            shutil.copyfile(index, Path(tmp, "index"))
        if (not files or (not index.is_file() and git(top, "read-tree", "HEAD", env=env).returncode)
                or git(top, "apply", "--cached", *directory, "-", data=patch, env=env).returncode):
            return files or ["(no file could be read from the patch)"]
        off = []
        for f in files:
            blob = git(top, "rev-parse", "-q", "--verify", f":{prefix}{f}", env=env).stdout.decode().strip()
            shipped = _git(root, "rev-parse", "-q", "--verify",
                           f"refs/tags/{version}:{f}").stdout.decode().strip() if version else ""
            if not (f in DEVFLOW_TOOLING_FILES or f.startswith(DEVFLOW_TOOLING)) or not blob or blob != shipped:
                off.append(f)
        return off


def reviewed(root: Path, sha: str) -> bool:
    """Whether a `docs/reviews/*-security.md` names this patch as `**Reviewed patch:**`, PASS or MINOR, independent."""
    for p in sorted((root / "docs" / "reviews").glob("*-security.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        m, v = REVIEWED_PATCH.search(text), VERDICT.search(text)
        if m and m.group(1) == sha and v and v.group(1) != "BLOCKING" and "|" not in v.group(2) \
                and INDEPENDENT.search(text):
            return True
    return False


def build(root: Path, src: Path) -> int:
    files = sorted(p for p in src.rglob("*") if p.is_file() or p.is_symlink()) if src.is_dir() else []
    links = [p for p in files if p.is_symlink() or not p.resolve().is_relative_to(src.resolve())]
    if links:
        print(f"owner-bundle CANNOT RUN: {links[0]} is, or sits in, a symbolic link -- a bundle carries file contents only")
        return 2
    rels = [p.relative_to(src).as_posix() for p in files]
    if any(r == ".git" or r.startswith(".git/") for r in rels):
        print("owner-bundle CANNOT RUN: a bundle never carries `.git/`")
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        a, b = Path(tmp, "a"), Path(tmp, "b")
        a.mkdir()
        b.mkdir()
        for rel in rels:
            old, new = root / rel, src / rel
            (b / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(new, b / rel)
            mode = (old if old.is_file() else new).stat().st_mode & 0o777
            if old.is_file():  # the file's own mode on both sides: a bundle changes content, not modes
                (a / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(old, a / rel)
                os.chmod(a / rel, mode)
            os.chmod(b / rel, mode)
        r = subprocess.run(["git", "-c", "core.quotePath=false", "diff", "--no-index", "--no-prefix", "--binary",
                            "--no-color", "--no-ext-diff", "--no-textconv", "a", "b"], cwd=tmp, capture_output=True)
    if r.returncode not in (0, 1):
        print(f"owner-bundle CANNOT RUN: git diff failed: {r.stderr.decode(errors='replace').strip()[:200]}")
        return 2
    if not r.stdout:
        print(f"owner-bundle: nothing to bundle -- no file under {src} differs from this tree. Write each proposed "
              f"file there at its path in this project ({OUT}/src/.github/workflows/ci.yml), then run this again")
        return 1
    top, prefix = top_and_prefix(root) or (root, "")
    if binary := binary_files(top, r.stdout):
        print(f"owner-bundle REFUSED: {', '.join(binary[:4])} would go in as a binary hunk -- a bundle carries only "
              "text the owner can read")
        return 1
    sha = hashlib.sha256(r.stdout).hexdigest()
    patch = OUT / f"{sha[:12]}.patch"
    (root / patch).parent.mkdir(parents=True, exist_ok=True)
    (root / patch).write_bytes(r.stdout)
    changed = [rel for rel in rels if not (root / rel).is_file() or (root / rel).read_bytes() != (src / rel).read_bytes()]
    history = devflow_history(root)
    version = history[0] if history else None
    off = not_devflows(root, top, prefix, r.stdout)
    print(f"owner-bundle: {len(changed)} file(s): {', '.join(changed[:6])}{' ...' if len(changed) > 6 else ''}")
    print(f"owner-bundle: {patch.as_posix()}, sha256 {sha}")
    if off:
        whose = f"DevFlow {version}'s own tooling" if version else "DevFlow's (the brief names no `process_version:`)"
        print(f"owner-bundle: review: owed -- not {whose}, byte for byte: {', '.join(off[:4])}"
              f"{' ...' if len(off) > 4 else ''}; the Security-Reviewer reads the patch and its verdict "
              f"(docs/reviews/*-security.md) names `**Reviewed patch:** {sha}` -- the apply refuses it without that")
    else:
        print(f"owner-bundle: review: none -- every file is DevFlow {version}'s, byte for byte (refs/tags/{version})")
    print("owner-bundle: the owner's one command, a row in docs/owner-actions.md:\n"
          f"  cd {shlex.quote(str(root))} && python3 scripts/owner_bundle.py apply {patch.as_posix()} {sha}")
    if any(rel.startswith(".claude/") for rel in changed):
        print("owner-bundle: it changes .claude/: the apply re-pins the guard if it changed, and ends asking the owner "
              "to restart Claude Code")
    if git(root, "check-ignore", "-q", patch.as_posix()).returncode:
        print(f"owner-bundle: note -- {OUT.parent}/ is not gitignored here: add it to .gitignore, or these untracked "
              "files read as code changed to the deploy gate")
    return 0


def apply(root: Path, name: str, want: str) -> int:
    found = top_and_prefix(root)
    if found is None:
        print(f"owner-bundle CANNOT RUN: {root} is not inside a git work tree")
        return 2
    top, prefix = found
    patch = Path(name) if Path(name).is_absolute() else root / name
    if not patch.is_file():
        print(f"owner-bundle REFUSED: {name} does not exist -- nothing was applied")
        return 1
    data = patch.read_bytes()  # checked once and applied from memory: what git applies is what was checked
    got = hashlib.sha256(data).hexdigest()
    if got != want.strip().lower():
        print(f"owner-bundle REFUSED: {name} is not the patch that was built -- its sha256 is {got}, the command "
              f"names {want}. Nothing was applied: build the bundle again")
        return 1
    if binary := binary_files(top, data):
        print(f"owner-bundle REFUSED: {name} carries {', '.join(binary[:4])} as a binary hunk, which nobody can read "
              "before applying it. Nothing was applied")
        return 1
    args = ["apply", "--index"] + ([f"--directory={prefix.rstrip('/')}"] if prefix else []) + ["-"]
    check = git(top, *args[:1], "--check", *args[1:], data=data)
    if check.returncode:
        print(f"owner-bundle REFUSED: {name} does not apply to this tree -- "
              f"{check.stderr.decode(errors='replace').strip()[:300]}. Nothing was applied")
        return 1
    if (off := not_devflows(root, top, prefix, data)) and not reviewed(root, got):
        print(f"owner-bundle REFUSED: {name} owes a review -- not DevFlow's own release bytes: {', '.join(off[:4])} -- "
              f"and no docs/reviews/*-security.md names `**Reviewed patch:** {got}` with a PASS or MINOR verdict and "
              "`**Independent:** yes`. Nothing was applied")
        return 1
    files = [ln.split("\t")[-1] for ln in git(top, "apply", "--numstat", "-", data=data).stdout.decode().splitlines()]
    if git(top, *args, data=data).returncode:
        print(f"owner-bundle FAIL: git {' '.join(args[:2])} failed after its check passed -- read `git status`")
        return 1
    print(f"owner-bundle APPLIED and staged: {', '.join(files)} -- commit it")
    rc = 0
    if GUARD in files:
        pin = subprocess.run([sys.executable, str(root / ".claude/hooks/guard_pin.py")], cwd=root, capture_output=True,
                             text=True)
        print(f"owner-bundle: the guard-pin step: {(pin.stdout + pin.stderr).strip()}")
        # guard_pin rewrites Codex's pin too, where the project has one (run v73 M2).
        pinned = [f for f in (".claude/settings.json", ".codex/hooks.json") if (root / f).is_file()]
        rc = 0 if pin.returncode == 0 and git(root, "add", "--", *pinned).returncode == 0 else 1
    if any(f.startswith(".claude/") for f in files):
        print("owner-bundle: restart Claude Code now -- a session open across a change under .claude/ keeps the hooks "
              "it started with")
    return rc


def main(argv: list[str]) -> int:
    root = Path.cwd()
    if shutil.which("git") is None:
        print("owner-bundle CANNOT RUN: git is not installed")
        return 2
    if argv[:1] == ["apply"]:
        if len(argv) != 3:
            print("usage: owner_bundle.py apply <patch> <sha256>")
            return 2
        return apply(root, argv[1], argv[2])
    if argv and (len(argv) != 2 or argv[0] != "--src"):
        print("usage: owner_bundle.py [--src <dir>] | apply <patch> <sha256>")
        return 2
    if top_and_prefix(root) is None:
        print(f"owner-bundle CANNOT RUN: {root} is not inside a git work tree")
        return 2
    return build(root, root / (argv[1] if argv else OUT / "src"))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
