"""Tester, #146 (INV-49): the sweep removes only THIS artifact's day-old scratch."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest


def test_the_sweep_leaves_another_artifacts_day_old_scratch_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """INV-49: "the sweep removes only this artifact's day-old scratch". `.writing` is a generic
    suffix, so a sweep that matched any artifact's name would take a neighbour's files too."""
    from app.workflows.refresh import refresh

    from .test_refresh_carry import _first_cycle

    live = _first_cycle(tmp_path, monkeypatch)
    old = time.time() - 2 * 86400
    neighbour = [
        live.parent / "other.db.refresh.json.dead.writing",
        live.parent / "other.db.dead.candidate-journal",
        live.parent / "other.db.dead.candidate",
    ]
    for path in neighbour:
        path.write_text("x", encoding="utf-8")
        os.utime(path, (old, old))

    refresh(live)
    assert all(p.exists() for p in neighbour), "the sweep took another artifact's scratch"
