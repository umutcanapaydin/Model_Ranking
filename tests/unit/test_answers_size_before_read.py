"""#314 (D-209 clause 6): the kept answers' file is refused by its size before its bytes are read.

`StandingsStore.keptAnswers()` checked `maxAnswersBytes` after `contents()` had read the whole file with
`Data(contentsOf:)`: the ceiling bounded the decode, not the read. The store's one read stays one exact
expression (the pins in `test_router_hints.py`); the size is read from the file's attributes before it, and the
kept answers pass their ceiling to it.
"""

from __future__ import annotations

import re
from pathlib import Path

from .test_router_hints import _code

STORE = Path(__file__).resolve().parents[2] / "ios" / "ModelRanking" / "Engine" / "StandingsStore.swift"


def _body(text: str, signature: str) -> str:
    start = text.index(signature)
    depth, end = 0, len(text)
    for position in range(text.index("{", start), len(text)):
        depth += {"{": 1, "}": -1}.get(text[position], 0)
        if depth == 0:
            end = position
            break
    return text[start:end]


def test_the_store_reads_the_size_before_the_bytes() -> None:
    text = _code(STORE.read_text(encoding="utf-8"))
    body = _body(text, "private func contents(")
    assert "fileSizeKey" in body, "contents() reads no size"
    assert body.index("fileSizeKey") < body.index("Data(contentsOf: url)"), "the size is read after the bytes"


def test_the_kept_answers_pass_their_ceiling_to_the_read() -> None:
    body = _body(_code(STORE.read_text(encoding="utf-8")), "func keptAnswers(")
    assert re.search(r"answersFile\.contents\(atMost:\s*Self\.maxAnswersBytes\)", body), body
