"""#271 (D-198 clause 1): rule L1 decodes escapes before it reads.

A JSON file written with `ensure_ascii` holds Turkish as `\\u015f`, and a Swift file as `\\u{15F}`; L1 read
the raw characters and saw none of it, so an escaped Turkish line needed no reasoned entry."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]


def _check_records() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_records", ROOT / "scripts" / "check_records.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _flagged(tmp_path: Path, files: dict[str, str]) -> set[str]:
    for name, text in files.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    return {finding.path.name for finding in _check_records().language_rule(tmp_path) if finding.rule == "L1"}


def test_an_escaped_turkish_line_is_read_as_turkish(tmp_path: Path) -> None:
    flagged = _flagged(tmp_path, {
        "set.json": '["bu bir \\u015fey"]\n',
        "upper.json": '["\\u0130stanbul"]\n',
        "pair.json": '["\\ud83d\\ude00 \\u011f"]\n',
        "Probe.swift": 'let line = "bu bir \\u{15F}ey"\n',
        "Wide.swift": 'let line = "\\u{0000011F}"\n',
    })
    assert flagged == {"set.json", "upper.json", "pair.json", "Probe.swift", "Wide.swift"}, flagged


def test_an_escape_that_is_not_turkish_or_not_a_string_escape_stays_quiet(tmp_path: Path) -> None:
    flagged = _flagged(tmp_path, {
        "ascii.json": '["caf\\u00e9 \\u2014 a dash"]\n',
        "literal.json": '["a backslash then u015f: \\\\u015f"]\n',
        "Ascii.swift": 'let dash = "\\u{2014}"\n',
        # Python and Markdown keep their own reading: the escape is decoded only where it is one.
        "note.md": "A JSON escape quoted in prose: \\u015f.\n",
    })
    assert flagged == set(), flagged
