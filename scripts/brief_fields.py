#!/usr/bin/env python3
"""The owner's setup answers, read from `docs/project-brief.md` -- the one place they live.

`/setup-project` writes the brief; these fields are the ones a script acts on, so they are read
here and nowhere else:

  Working mode:                    light | heavy   (unset or unreadable: heavy -- more checks, not fewer)
  Deploy commands:                 none | a comma-separated list the deploy gate guards
  Paths that make a change HIGH:   none | comma-separated globs (a change touching one needs security)
  QA verification:                 off | on        (unset: off -- a bug closes when its fix merges)

    python3 scripts/brief_fields.py mode          # prints light or heavy
    python3 scripts/brief_fields.py get "<field>" # prints the raw answer, or nothing
Exit 0, always: an absent brief is an answer (the defaults), not an error.

**The policy fields are read at the protected base** (AGENTS.md section 5, base-pinned policy; #283):
`Working mode:`, `Paths that make a change HIGH:` and `Deploy commands:` decide the reviews a change owes and
what the deploy gate guards, so `review_need.py` and `deploy_gate.py` read them from the brief as a base
commit holds it (`root_at`), never from the change under evaluation. A base commit git cannot read is an
error (`RuntimeError`), not the defaults: a policy read from nowhere would answer for the change.
"""
from __future__ import annotations

import atexit
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

BRIEF = Path("docs/project-brief.md")
T = TypeVar("T")
_PLACEHOLDER = re.compile(r"^<[^>]*>$")
#: The fields that decide what a change owes (#283): read at the base, and a change to one is a policy edit.
POLICY_FIELDS = ("Working mode", "Paths that make a change HIGH", "Deploy commands")
#: The branches whose merge-base with HEAD is the protected base, in the order they are tried.
DEFAULT_BRANCHES = ("origin/HEAD", "origin/main", "origin/master", "main", "master")


def field(name: str, root: Path | str = ".") -> str | None:
    """The answer on the first line naming `name:`, stripped of Markdown; None if absent or a placeholder."""
    p = Path(root) / BRIEF
    if not p.is_file():
        return None
    want = name.lower() + ":"
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        low = line.lower()
        at = low.find(want)
        if at < 0:
            continue
        rest = line[at + len(want):]
        # The answer is in code spans when there are any -- the template writes every field that
        # way, one span (`a, b`) or one per item (`a`, `b`); all of them, joined, since reading only
        # the first left a second deploy command unguarded. Else the text before a *(explanation)*,
        # which may run onto later lines. A code span is taken as written: a glob's `**` is kept.
        before = re.split(r"\s\*\(", rest, maxsplit=1)[0]
        spans = re.findall(r"`([^`]*)`", before)
        rest = ", ".join(s.strip() for s in spans) if spans else before.strip().strip("*_ ").strip()
        if not rest or _PLACEHOLDER.match(rest):
            return None
        return rest
    return None


def listing(name: str, root: Path | str = ".") -> list[str]:
    """A comma-separated answer as a list; `none` or absent is the empty list."""
    raw = field(name, root)
    if not raw or raw.strip().lower() in ("none", "no", "-", "—"):
        return []
    return [x.strip().strip("`").strip() for x in raw.split(",") if x.strip().strip("`").strip()]


def mode(root: Path | str = ".") -> str:
    raw = (field("Working mode", root) or "").lower()
    return "light" if raw.startswith("light") else "heavy"


def qa_on(root: Path | str = ".") -> bool:
    return (field("QA verification", root) or "").lower().startswith("on")


def _git(repo: Path | str, *args: str) -> subprocess.CompletedProcess[str]:
    """git's answer; no git, or one that hangs, is a failed answer (exit 127), never a crash: the deploy gate
    asks this on every Bash call the guard judges, and a crash there would refuse `ls`."""
    try:
        # #410 round 1's B1: a `refs/replace/` ref would answer for the base this reads; never honour one.
        return subprocess.run(["git", "--no-replace-objects", "-C", str(repo), *args], capture_output=True,  # noqa: S603, S607
                              encoding="utf-8", errors="replace", check=False, timeout=60)
    except (OSError, subprocess.SubprocessError) as error:
        return subprocess.CompletedProcess(["git", *args], 127, "", str(error))


def root_at(rev: str, repo: Path | str = ".") -> Path:
    """A throwaway root holding `docs/project-brief.md` as commit `rev` of the repository at `repo` held it,
    empty when that commit holds no brief (an absent brief is an answer: the defaults). RuntimeError when
    `rev` is not a commit git can read there, or its brief cannot be read (#283: fail closed); `Unverified` when
    an object on the way does not hash to its id (#509: `git show` does not hash a loose blob)."""
    try:
        body = verified_file(repo, rev, BRIEF.as_posix())
    except Unverified as error:
        raise Unverified(f"{BRIEF.as_posix()} at {rev[:12]} cannot be read as that commit holds it: {error}") from error
    except RuntimeError as error:
        raise RuntimeError(f"the commit {rev!r} cannot be read, so the brief's policy fields there cannot be "
                           f"({error})") from error
    tmp = Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, tmp, True)
    (tmp / "docs").mkdir()
    (tmp / BRIEF).write_text((body or b"").decode("utf-8", "replace"), encoding="utf-8")
    return tmp


# --- verified objects (#509, #511) -------------------------------------------------------------------------

class Unverified(RuntimeError):
    """#509: an object on the way to a file at a base commit does not hash to its id, is missing, or is not what git
    writes there, so the bytes read are not that commit's. Every caller fails closed on it."""


def open_batch(repo: Path | str) -> subprocess.Popen[bytes]:
    """#511: the one reader of git objects; each object it serves is checked by `batch_read`."""
    return subprocess.Popen(["git", "--no-replace-objects", "-C", str(repo), "cat-file", "--batch"],  # noqa: S603, S607
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def close_batch(batch: subprocess.Popen[bytes]) -> None:
    if batch.stdin is not None:
        batch.stdin.close()
    batch.kill()
    batch.wait()


def batch_read(batch: subprocess.Popen[bytes], oid: str, kind: str) -> bytes | str:
    """One object's bytes from a running `git cat-file --batch`, or why it is not a `kind` that hashes to `oid`."""
    assert batch.stdin is not None and batch.stdout is not None
    batch.stdin.write(oid.encode() + b"\n")
    batch.stdin.flush()
    header = batch.stdout.readline().split()
    if len(header) != 3 or header[1].decode() != kind:
        return f"object {oid} cannot be read as a {kind}"
    body = batch.stdout.read(int(header[2]) + 1)[:-1]
    digest = hashlib.sha256 if len(oid) == 64 else hashlib.sha1
    # The hash git names its objects by: this checks the bytes against the name, nothing more.
    if digest(b"%s %d\0" % (kind.encode(), len(body)) + body).hexdigest() != oid:
        return f"object {oid} ({kind}) does not hash to its id"
    return body


def tree_entries(body: bytes, size: int) -> list[tuple[bytes, bytes, str]]:
    """#511: a tree's entries as (mode as written, name, id), ids `size` bytes long; the one tree parser."""
    out, at = [], 0
    while at < len(body):
        space, nul = body.index(b" ", at), body.index(b"\0", at)
        out.append((body[at:space], body[space + 1:nul], body[nul + 1:nul + 1 + size].hex()))
        at = nul + 1 + size
    return out


#: The tree-entry modes a verified read accepts, only as git writes them: a directory on the way, a regular file.
DIRECTORY, FILES = b"40000", (b"100644", b"100755")


def _commit(repo: Path | str, rev: str) -> str:
    """The commit `rev` names. RuntimeError when git cannot run; `Unverified` when it names no commit git can read."""
    resolved = _git(repo, "rev-parse", "--verify", "--quiet", "--end-of-options", f"{rev}^{{commit}}")
    if resolved.returncode == 127:
        raise RuntimeError(resolved.stderr.strip() or "git cannot run")
    commit = resolved.stdout.strip()
    if resolved.returncode != 0 or not commit:
        raise Unverified(f"the commit {rev[:12]} cannot be read")
    return commit


def _root_tree(batch: subprocess.Popen[bytes], commit: str) -> str:
    """The root tree the verified commit `commit` names; `Unverified` when the commit does not hash or names none."""
    body = batch_read(batch, commit, "commit")
    m = re.match(rb"tree ([0-9a-f]{40,64})\n", body) if isinstance(body, bytes) else None
    if m is None:
        raise Unverified(body if isinstance(body, str) else f"commit {commit[:12]} names no tree")
    return m.group(1).decode()


def _verified_read(repo: Path | str, rev: str, rel: str, read: Callable[[subprocess.Popen[bytes], bytes, str], T]) -> T | None:
    """`read(batch, mode, id)` of the entry `rel` names at commit `rev`, the commit and each tree on the way hashed
    against its id; None when `rel` names nothing there (every object read hashing). RuntimeError when git cannot
    run; `Unverified` for an object that does not hash, is missing, or an entry on the way that is not a directory."""
    commit = _commit(repo, rev)
    try:
        batch = open_batch(repo)
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(f"objects cannot be read by git ({error})") from error
    try:
        oid, parts = _root_tree(batch, commit), [p for p in rel.split("/") if p]
        for depth, part in enumerate(parts):
            tree = batch_read(batch, oid, "tree")
            if isinstance(tree, str):
                raise Unverified(tree)
            found = next(((mode, entry) for mode, name, entry in tree_entries(tree, len(oid) // 2)
                          if name == part.encode()), None)
            if found is None:
                return None
            if depth == len(parts) - 1:
                return read(batch, found[0], found[1])
            if found[0] != DIRECTORY:
                raise Unverified(f"{'/'.join(parts[:depth + 1])} at {commit[:12]} is not a directory as git writes one")
            oid = found[1]
        return None
    except ValueError as error:
        raise Unverified(f"an object on the way to {rel} at {commit[:12]} does not parse ({error})") from error
    except OSError as error:
        raise RuntimeError(f"objects cannot be read by git ({error})") from error
    finally:
        close_batch(batch)


def _blob(batch: subprocess.Popen[bytes], mode: bytes, oid: str) -> bytes:
    if mode not in FILES:
        raise Unverified(f"{oid[:12]} is not a regular file as git writes one (mode {mode.decode()})")
    body = batch_read(batch, oid, "blob")
    if isinstance(body, str):
        raise Unverified(body)
    return body


def verified_file(repo: Path | str, rev: str, rel: str) -> bytes | None:
    """The bytes of the regular file `rel` at commit `rev`, every object on the way -- the commit, each tree, the
    blob -- hashed against its id (#444 R2, #509: git serves a loose object without hashing it); None when `rel`
    names nothing there. RuntimeError when git cannot run; `Unverified` when an object does not hash or is missing,
    or `rel` is not a regular file (a link, a submodule, a mode git does not write)."""
    return _verified_read(repo, rev, rel, _blob)


def verified_tree(repo: Path | str, rev: str) -> dict[str, tuple[bytes, str]]:
    """#505: every entry of commit `rev`'s tree that is not a directory, by its path: (mode as written, id), the
    commit and every tree hashed against its id. RuntimeError when git cannot run; `Unverified` as `verified_file`."""
    commit = _commit(repo, rev)
    try:
        batch = open_batch(repo)
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(f"objects cannot be read by git ({error})") from error
    try:
        out: dict[str, tuple[bytes, str]] = {}
        todo = [("", _root_tree(batch, commit))]
        while todo:
            at, tree_oid = todo.pop()
            tree = batch_read(batch, tree_oid, "tree")
            if isinstance(tree, str):
                raise Unverified(tree)
            for mode, name, entry in tree_entries(tree, len(tree_oid) // 2):
                path = f"{at}{name.decode('utf-8', 'surrogateescape')}"
                if int(mode, 8) & 0o170000 == 0o040000:
                    todo.append((f"{path}/", entry))
                else:
                    out[path] = (mode, entry)
        return out
    except ValueError as error:
        raise Unverified(f"a tree under {commit[:12]} does not parse ({error})") from error
    except OSError as error:
        raise RuntimeError(f"objects cannot be read by git ({error})") from error
    finally:
        close_batch(batch)


def verified_blobs(repo: Path | str, oids: list[str]) -> dict[str, bytes]:
    """#505: each blob's bytes by its id, hashed against it. RuntimeError when git cannot run; `Unverified` when
    one does not hash or is missing."""
    try:
        batch = open_batch(repo)
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(f"objects cannot be read by git ({error})") from error
    try:
        out: dict[str, bytes] = {}
        for oid in oids:
            body = batch_read(batch, oid, "blob")
            if isinstance(body, str):
                raise Unverified(body)
            out[oid] = body
        return out
    except (OSError, ValueError) as error:
        raise RuntimeError(f"objects cannot be read by git ({error})") from error
    finally:
        close_batch(batch)


def verified_files(repo: Path | str, rev: str, folder: str) -> tuple[dict[str, bytes], list[str]]:
    """(every regular file under `folder` at commit `rev` by its path, each read as `verified_file` reads one; the
    paths that could not be read so) -- ({}, []) when `folder` names nothing there. A file that fails is named, not
    skipped quietly, and the rest are still read (the deploy gate's round 1 N1). A tree on the way that fails, or an
    entry that is neither a directory nor a regular file, is `Unverified` for the whole folder."""
    def walk(batch: subprocess.Popen[bytes], mode: bytes, oid: str) -> tuple[dict[str, bytes], list[str]]:
        if mode != DIRECTORY:
            raise Unverified(f"{folder} at {rev[:12]} is not a directory as git writes one")
        out: dict[str, bytes] = {}
        failed: list[str] = []
        todo = [(folder.strip("/"), oid)]
        while todo:
            at, tree_oid = todo.pop()
            tree = batch_read(batch, tree_oid, "tree")
            if isinstance(tree, str):
                raise Unverified(tree)
            for entry_mode, name, entry in tree_entries(tree, len(tree_oid) // 2):
                path = f"{at}/{name.decode('utf-8', 'replace')}"
                if entry_mode == DIRECTORY:
                    todo.append((path, entry))
                    continue
                try:
                    out[path] = _blob(batch, entry_mode, entry)
                except Unverified:
                    failed.append(path)
        return out, failed
    return _verified_read(repo, rev, folder, walk) or ({}, [])


def protected_base(repo: Path | str = ".", head: str = "HEAD") -> str | None:
    """The merge-base of `head` with the first of DEFAULT_BRANCHES git knows in `repo`, or None."""
    for ref in DEFAULT_BRANCHES:
        found = _git(repo, "merge-base", ref, head)
        if found.returncode == 0 and found.stdout.strip():
            return found.stdout.strip()
    return None


def policy(root: Path | str = ".") -> dict[str, str | None]:
    """Each policy field's raw answer in the brief under `root` (None: absent or a placeholder)."""
    return {name: field(name, root) for name in POLICY_FIELDS}


def main(argv: list[str]) -> int:
    if argv[:1] == ["mode"]:
        print(mode())
    elif argv[:1] == ["get"] and len(argv) == 2:
        print(field(argv[1]) or "")
    else:
        print("usage: brief_fields.py mode | get \"<field>\"")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
