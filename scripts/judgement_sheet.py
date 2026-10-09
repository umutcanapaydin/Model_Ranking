"""The owner's judgement sheet (#226, M21-W2): a stub in the red commit."""

from __future__ import annotations

import pathlib


def make(probe: pathlib.Path, out: pathlib.Path, key: pathlib.Path, seed: int = 0) -> None:
    """Write the blinded sheet and its key (a stub)."""


def score(sheet: pathlib.Path, key: pathlib.Path) -> dict[str, object]:
    """Count the owner's choices (a stub)."""
    return {}
