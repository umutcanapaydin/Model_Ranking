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
