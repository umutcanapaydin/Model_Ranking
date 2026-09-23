"""Fetch the Epoch AI benchmark bundle and unpack it safely (M16-W4, D-158).

Until M16 the bundle was downloaded by the owner and handed to the build as a directory, because the
sandbox the project started in got HTTP 403 from epoch.ai. The engine runs on the owner's machine
now, and a directory nobody refreshes meant nine sources carried every night until they expired
(D-156). So the refresh fetches it -- and a zip from the internet is untrusted input:

- a member may NAME a path outside the directory (`../`, an absolute path, a Windows drive);
- a member may BE a symlink, which the board readers would then follow (reproduced against
  /etc/shadow at M5; `EpochBoardClient.fetch_raw` still checks the resolved path as well);
- a member may expand far past what its header says, so the size limit is counted while WRITING,
  never read from the header.

Any of these refuses the WHOLE bundle: a half-trusted bundle is not a thing the build can reason
about, and a refused bundle simply leaves the boards to carry, as a missing one does.
"""

from __future__ import annotations

import io
import stat
import zipfile
import zlib
from collections.abc import Callable
from pathlib import Path, PurePosixPath

from app.clients.epoch import EPOCH_BUNDLE_URL
from app.clients.protocols import SourceError, fetch_bounded_bytes

__all__ = ["EPOCH_BUNDLE_URL", "fetch_bundle", "unpack"]

NAME = "epoch bundle"
#: The download. The 2026-09-23 bundle is 2.3 MB; thirty times that is a bundle that changed shape.
MAX_BUNDLE_BYTES = 64 * 1024 * 1024
#: What it may expand to, counted while writing. The 2026-09-23 bundle unpacks to about 20 MB.
MAX_UNPACKED_BYTES = 256 * 1024 * 1024
#: The 2026-09-23 bundle has 88 members.
MAX_MEMBERS = 2000
TIMEOUT_SECONDS = 60.0
_CHUNK = 64 * 1024


def _safe_relative(name: str) -> PurePosixPath:
    """The member's path inside the bundle, or a refusal if it could land anywhere else."""
    path = PurePosixPath(name)
    if (not name or "\\" in name or path.is_absolute() or ".." in path.parts
            or (path.parts and ":" in path.parts[0])):
        msg = f"{NAME}: refused a member that names a path outside the bundle: {name!r}"
        raise SourceError(msg)
    return path


def _plan(members: list[zipfile.ZipInfo], root: Path) -> list[tuple[zipfile.ZipInfo, Path]]:
    """Every member's destination, judged before anything is written: a name refusal writes
    nothing."""
    if len(members) > MAX_MEMBERS:
        msg = f"{NAME}: {len(members)} members, over the limit of {MAX_MEMBERS}"
        raise SourceError(msg)
    plan: list[tuple[zipfile.ZipInfo, Path]] = []
    for info in members:
        relative = _safe_relative(info.filename)
        if stat.S_ISLNK(info.external_attr >> 16):
            msg = f"{NAME}: refused a symbolic link member: {info.filename!r}"
            raise SourceError(msg)
        if info.is_dir():
            continue
        target = root / relative
        if not target.resolve().is_relative_to(root):
            msg = f"{NAME}: refused a member that resolves outside the bundle: {info.filename!r}"
            raise SourceError(msg)
        plan.append((info, target))
    return plan


def _write(archive: zipfile.ZipFile, info: zipfile.ZipInfo, target: Path, budget: int) -> int:
    """Write one member, counting what it actually expands to. Returns the budget left."""
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with archive.open(info) as source, target.open("wb") as sink:
            while chunk := source.read(_CHUNK):
                budget -= len(chunk)
                if budget < 0:
                    msg = f"{NAME}: the bundle expands past {MAX_UNPACKED_BYTES} bytes"
                    raise SourceError(msg)
                sink.write(chunk)
    except (zipfile.BadZipFile, zlib.error, EOFError, RuntimeError, NotImplementedError) as exc:
        # A corrupt, truncated, encrypted or oddly compressed member is a bundle this cannot
        # read, which is a source failure, not a crash of the cycle.
        msg = f"{NAME}: member {info.filename!r} is unreadable: {exc}"
        raise SourceError(msg) from exc
    return budget


def unpack(payload: bytes, dest: Path) -> int:
    """Unpack `payload` into `dest`. Returns the files written.

    Every NAME is judged before anything is written, so a path or link refusal writes nothing. A
    size refusal happens mid-write and can leave partial files: `dest` is scratch the caller
    removes either way, and the refusal means the build never reads it."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        msg = f"{NAME}: the download is not a zip ({len(payload)} bytes)"
        raise SourceError(msg) from exc
    budget = MAX_UNPACKED_BYTES
    with archive:
        plan = _plan(archive.infolist(), dest.resolve())
        for info, target in plan:
            budget = _write(archive, info, target, budget)
    return len(plan)


def _download(url: str) -> bytes:
    return fetch_bounded_bytes(url, NAME, TIMEOUT_SECONDS, limit=MAX_BUNDLE_BYTES)


def fetch_bundle(dest: Path, *, get: Callable[[str], bytes] | None = None) -> Path:
    """Download the documented bundle and unpack it into `dest` (which must exist).

    `get` is resolved HERE, not in the signature, so a test that injects one never reaches the
    network (the defect `refresh.refresh` documents, found four times in this project).
    """
    download = _download if get is None else get
    unpack(download(EPOCH_BUNDLE_URL), dest)
    return dest
