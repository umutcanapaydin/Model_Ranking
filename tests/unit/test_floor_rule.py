"""D-148 -- every shipped floor is the one the measurement record derived under the ROWS rule.

One fact in two artefacts: the floor in `categories.py` and the measured D-148 column in
`docs/research/m16-w3-floor-table-2026-09-23.md`. DevFlow AGENTS.md §3.5: generate one from the other
or gate the comparison. The record is the measurement (reproduced by
`scripts/survey_boards.py --floors`), so this compares the code with it, surface by surface, and fails
closed if the record's table cannot be read.
"""

from __future__ import annotations

from pathlib import Path

from app.workflows.categories import CATEGORIES

RECORD = Path(__file__).resolve().parents[2] / "docs" / "research" / "m16-w3-floor-table-2026-09-23.md"


def _d148_column() -> dict[str, float]:
    lines = RECORD.read_text(encoding="utf-8").splitlines()
    header = next(i for i, line in enumerate(lines) if line.startswith("| surface | board rows"))
    columns = [c.strip() for c in lines[header].strip("|").split("|")]
    at = columns.index("D-148 (rows)")
    out: dict[str, float] = {}
    for line in lines[header + 2:]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        out[cells[0]] = float(cells[at])
    return out


def test_the_record_covers_every_surface() -> None:
    """Fails closed: a surface missing from the record is a floor nobody measured."""
    assert set(_d148_column()) == set(CATEGORIES)


def test_every_floor_follows_d148() -> None:
    measured = _d148_column()
    wrong = {s: (spec.min_quality, measured[s]) for s, spec in CATEGORIES.items()
             if spec.min_quality != measured[s]}
    assert not wrong, f"floor in code != D-148 measurement (code, record): {wrong}"
