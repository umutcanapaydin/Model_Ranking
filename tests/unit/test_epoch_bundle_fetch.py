"""M16-W4 P1, D-158 -- the refresh fetches the Epoch bundle itself, and unpacks it safely.

Nine of nineteen sources were read from a directory the owner downloaded by hand; without it every
night carried them until they expired (D-156). The bundle is a public CC-BY zip, so the refresh
fetches it. A zip from the internet is untrusted input: a member may name a path outside the
directory (`../`, absolute), be a symlink, or expand far past its compressed size. Each is refused,
and a refused bundle leaves the boards to carry, exactly as a missing one does.

No test here touches the network: the download is injected, as every source client's is.
"""

from __future__ import annotations

import io
import stat
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.clients import epoch_bundle
from app.clients.protocols import SourceError


def _zip(members: dict[str, bytes], *, symlink: str | None = None) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
        if symlink is not None:
            info = zipfile.ZipInfo(symlink)
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "/etc/passwd")
    return buffer.getvalue()


def test_a_bundle_unpacks_into_its_directory(tmp_path: Path) -> None:
    payload = _zip({"gpqa_diamond.csv": b"a,b\n1,2\n", "epoch_capabilities_index/eci_scores.csv": b"x\n"})
    epoch_bundle.unpack(payload, tmp_path)
    assert (tmp_path / "gpqa_diamond.csv").read_bytes() == b"a,b\n1,2\n"
    assert (tmp_path / "epoch_capabilities_index" / "eci_scores.csv").is_file()


@pytest.mark.parametrize("name", ["../escape.csv", "/abs/escape.csv", "a/../../escape.csv",
                                  "..\\escape.csv", "C:/escape.csv"])
def test_a_member_that_names_a_path_outside_is_refused(tmp_path: Path, name: str) -> None:
    dest = tmp_path / "bundle"
    dest.mkdir()
    with pytest.raises(SourceError, match="outside"):
        epoch_bundle.unpack(_zip({"ok.csv": b"1", name: b"2"}), dest)
    assert not (tmp_path / "escape.csv").exists()


def test_a_symlink_member_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SourceError, match="link"):
        epoch_bundle.unpack(_zip({"ok.csv": b"1"}, symlink="gpqa_diamond.csv"), tmp_path)
    assert not (tmp_path / "gpqa_diamond.csv").exists()


def test_a_bundle_that_expands_past_the_limit_is_refused_by_what_it_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Counted while writing, never from the header: a zip bomb states whatever size it likes."""
    monkeypatch.setattr(epoch_bundle, "MAX_UNPACKED_BYTES", 1000)
    with pytest.raises(SourceError, match="expands past"):
        epoch_bundle.unpack(_zip({"a.csv": b"0" * 800, "b.csv": b"0" * 800}), tmp_path)


def test_too_many_members_are_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(epoch_bundle, "MAX_MEMBERS", 3)
    with pytest.raises(SourceError, match="members"):
        epoch_bundle.unpack(_zip({f"{i}.csv": b"1" for i in range(4)}), tmp_path)


def test_a_body_that_is_not_a_zip_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SourceError, match="not a zip"):
        epoch_bundle.unpack(b"<html>rate limited</html>", tmp_path)


def test_fetch_downloads_the_documented_url_and_unpacks_it(tmp_path: Path) -> None:
    seen: list[str] = []

    def get(url: str) -> bytes:
        seen.append(url)
        return _zip({"gpqa_diamond.csv": b"a\n"})

    epoch_bundle.fetch_bundle(tmp_path, get=get)
    assert seen == [epoch_bundle.EPOCH_BUNDLE_URL]
    assert (tmp_path / "gpqa_diamond.csv").is_file()


# --- through the real cycle --------------------------------------------------------------------

GPQA = (b"Model version,mean_score,Started at\n"
        b"gpt-5,0.85,2026-09-01T00:00:00Z\nclaude-4-5-opus,0.83,2026-09-02T00:00:00Z\n")


def _scratch(live: Path) -> list[Path]:
    return sorted(live.parent.glob(f"{live.name}.*.epoch"))


def test_a_cycle_with_a_fetcher_ingests_the_bundle_it_fetched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.workflows.refresh import EXIT_PUBLISHED, refresh

    from .test_refresh_carry import _first_cycle, _record

    live = _first_cycle(tmp_path, monkeypatch)
    fetched: list[Path] = []

    def fetch(dest: Path) -> None:
        fetched.append(dest)
        epoch_bundle.unpack(_zip({"gpqa_diamond.csv": GPQA}), dest)

    outcome, code = refresh(live, fetch_epoch=fetch)
    assert code == EXIT_PUBLISHED, outcome.reason
    assert "epoch_gpqa" in _record(live)["sources_last_ok"]
    assert fetched and not _scratch(live), "the unpacked bundle is scratch, removed after the cycle"


def test_a_fetch_that_fails_leaves_the_boards_to_carry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.workflows.refresh import refresh

    from .test_refresh_carry import _first_cycle, _record

    live = _first_cycle(tmp_path, monkeypatch)

    def fetch(dest: Path) -> None:
        raise SourceError("epoch bundle: fetch failed: 503")

    refresh(live, fetch_epoch=fetch)
    assert "epoch_gpqa" not in _record(live)["sources_last_ok"]
    assert not _scratch(live)


def test_an_owner_supplied_directory_wins_over_the_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.workflows.refresh import refresh

    from .test_refresh_carry import _first_cycle

    live = _first_cycle(tmp_path, monkeypatch)
    owner = tmp_path / "owner-bundle"
    owner.mkdir()

    def fetch(dest: Path) -> None:
        raise AssertionError("fetched although the owner supplied a bundle")

    refresh(live, build_args=["--epoch-dir", str(owner)], fetch_epoch=fetch)


def test_the_cli_flag_turns_the_fetch_on(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from app.workflows import refresh as refresh_mod

    seen: dict[str, object] = {}

    def fake_refresh(target: Path, **kw: object) -> tuple[object, int]:
        seen.update(kw)
        return SimpleNamespace(as_json=lambda: "{}"), 0

    monkeypatch.setattr(refresh_mod, "refresh", fake_refresh)
    refresh_mod.main(["--db", str(tmp_path / "a.db"), "--fetch-epoch"])
    assert seen["fetch_epoch"] is epoch_bundle.fetch_bundle
    refresh_mod.main(["--db", str(tmp_path / "a.db")])
    assert seen["fetch_epoch"] is None, "off unless asked: tests and hand runs stay off the network"


def test_a_member_whose_resolved_path_escapes_is_refused_even_when_its_name_is_clean(
    tmp_path: Path,
) -> None:
    """The second layer. A clean NAME can still land outside if the directory already holds a link
    (the scratch is fresh in the refresh, so this is defence in depth, and it is tested as such)."""
    outside = tmp_path / "outside"
    outside.mkdir()
    dest = tmp_path / "bundle"
    dest.mkdir()
    (dest / "boards").symlink_to(outside, target_is_directory=True)
    with pytest.raises(SourceError, match="resolves outside"):
        epoch_bundle.unpack(_zip({"boards/gpqa_diamond.csv": b"1"}), dest)
    assert not list(outside.iterdir())


# --- the security pass on P1 (docs/reviews/m16-wave-4-security-p1.md) ---------------------------


def _bad_utf8_name() -> bytes:
    """F1: a member name flagged UTF-8 (bit 0x800) whose bytes are not UTF-8."""
    raw = bytearray(_zip({"AAAA.csv": b"1"}))
    raw[:] = raw.replace(b"AAAA", b"\xff\xfe\xfd\xfc")
    raw[6] |= 0x08  # the local header's flag word, high byte
    central = raw.find(b"PK\x01\x02")
    raw[central + 9] |= 0x08
    return bytes(raw)


def _corrupt_lzma() -> bytes:
    """F1: an LZMA member whose properties are garbage."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_LZMA) as archive:
        archive.writestr("gpqa_diamond.csv", bytes(range(256)) * 64)
    raw = bytearray(buffer.getvalue())
    start = 30 + len("gpqa_diamond.csv")  # the member's data: 4 bytes of version, then properties
    for i in range(start + 4, start + 9):
        raw[i] ^= 0xFF
    return bytes(raw)


HOSTILE = {"a name that is not UTF-8": _bad_utf8_name, "a corrupt LZMA member": _corrupt_lzma}


@pytest.mark.parametrize("make", HOSTILE.values(), ids=HOSTILE.keys())
def test_any_unreadable_archive_is_a_source_error(tmp_path: Path, make) -> None:  # type: ignore[no-untyped-def]
    """F1: an allowlist of exception classes is the shape that failed; the stdlib adds codecs."""
    with pytest.raises(SourceError):
        epoch_bundle.unpack(make(), tmp_path)


@pytest.mark.parametrize("make", HOSTILE.values(), ids=HOSTILE.keys())
def test_an_unreadable_archive_never_stops_the_cycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, make  # type: ignore[no-untyped-def]
) -> None:
    """F1: one upstream's bytes stopped every source for the night. Now the boards carry."""
    from app.workflows.refresh import EXIT_PUBLISHED, refresh

    from .test_refresh_carry import MOVED_PRICING, _first_cycle, _record, _sources, _use

    live = _first_cycle(tmp_path, monkeypatch)
    _use(monkeypatch, _sources(pricing=MOVED_PRICING))
    payload = make()
    outcome, code = refresh(live, fetch_epoch=lambda dest: epoch_bundle.fetch_bundle(
        dest, get=lambda url: payload))
    assert code == EXIT_PUBLISHED, outcome.reason
    assert "epoch_gpqa" not in _record(live)["sources_last_ok"]
    assert not _scratch(live)


def test_any_error_a_fetcher_raises_is_a_failed_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.workflows.refresh import EXIT_PUBLISHED, refresh

    from .test_refresh_carry import MOVED_PRICING, _first_cycle, _sources, _use

    live = _first_cycle(tmp_path, monkeypatch)
    _use(monkeypatch, _sources(pricing=MOVED_PRICING))

    def fetch(dest: Path) -> None:
        raise ValueError("a codec this code has never heard of")

    assert refresh(live, fetch_epoch=fetch)[1] == EXIT_PUBLISHED
    assert not _scratch(live)


def test_an_interrupt_during_the_fetch_propagates_and_leaves_no_scratch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F2: only `SourceError`/`OSError` used to clean up."""
    from app.workflows.refresh import refresh

    from .test_refresh_carry import _first_cycle

    live = _first_cycle(tmp_path, monkeypatch)

    def fetch(dest: Path) -> None:
        (dest / "gpqa_diamond.csv").write_text(GPQA.decode(), encoding="utf-8")
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        refresh(live, fetch_epoch=fetch)
    assert not _scratch(live)


def test_scratch_a_killed_cycle_left_is_swept_by_the_next(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F2 and W-124: a killed cycle's candidate, reports and bundle; a live sibling's are kept."""
    import os
    import time

    from app.workflows.refresh import refresh

    from .test_refresh_carry import _first_cycle

    live = _first_cycle(tmp_path, monkeypatch)
    old = time.time() - 2 * 86400
    stale = [live.parent / f"{live.name}.dead.{s}" for s in ("candidate", "sources", "last-ok")]
    for path in stale:
        path.write_text("x", encoding="utf-8")
        os.utime(path, (old, old))
    bundle = live.parent / f"{live.name}.dead.epoch"
    bundle.mkdir()
    (bundle / "gpqa_diamond.csv").write_text("x", encoding="utf-8")
    os.utime(bundle, (old, old))
    fresh = live.parent / f"{live.name}.sibling.sources"
    fresh.write_text("x", encoding="utf-8")

    refresh(live)
    assert not [p for p in [*stale, bundle] if p.exists()]
    assert fresh.exists(), "a sibling's scratch minutes old is never touched"


def test_a_size_refusal_says_so(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """F6: it used to read as "member ... is unreadable"."""
    monkeypatch.setattr(epoch_bundle, "MAX_UNPACKED_BYTES", 1000)
    with pytest.raises(SourceError) as caught:
        epoch_bundle.unpack(_zip({"a.csv": b"0" * 800, "b.csv": b"0" * 800}), tmp_path)
    assert str(caught.value).startswith("epoch bundle: the bundle expands past")


def test_the_bundle_download_is_bounded_small_follows_no_redirect_and_has_a_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F3, F4, F5: 16 MB (seven times the real bundle), no redirect, and a total deadline."""
    seen: dict[str, object] = {}

    def fake(url: str, name: str, timeout: float, params: object = None, **kw: object) -> bytes:
        seen.update(kw)
        return _zip({"a.csv": b"1"})

    monkeypatch.setattr(epoch_bundle, "fetch_bounded_bytes", fake)
    epoch_bundle._download(epoch_bundle.EPOCH_BUNDLE_URL)
    assert seen["limit"] == 16 * 1024 * 1024
    assert seen["follow_redirects"] is False
    assert isinstance(seen["deadline"], float) and seen["deadline"] <= 300


def test_a_download_past_its_deadline_is_a_source_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """F4: httpx's timeout is per read; a drip-fed body used to hold the cycle for half an hour."""
    import contextlib

    import httpx

    from app.clients import protocols

    ticks = iter(range(0, 1000, 10))

    class Drip:
        def raise_for_status(self) -> None:
            return None

        def iter_bytes(self):  # type: ignore[no-untyped-def]
            while True:
                yield b"x"

    @contextlib.contextmanager
    def stream(*args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        yield Drip()

    monkeypatch.setattr(httpx, "stream", stream)
    monkeypatch.setattr(protocols.time, "monotonic", lambda: float(next(ticks)))
    with pytest.raises(SourceError, match="deadline"):
        protocols.fetch_bounded_bytes("https://x", "x", 1.0, deadline=100.0)


def test_an_unreadable_member_is_named_in_the_refusal(tmp_path: Path) -> None:
    """The log line is the operator's only clue to WHICH board broke."""
    with pytest.raises(SourceError, match=r"gpqa_diamond\.csv.*LZMAError"):
        epoch_bundle.unpack(_corrupt_lzma(), tmp_path)
