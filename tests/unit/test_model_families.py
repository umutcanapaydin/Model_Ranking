"""#206 (M21-W2): the phone's family words are the registry's, so a comparison of any ranked families'
names is a general question. (#194's use of them in the fact doubt was taken out after three verdicts,
D-191.) `ios/ModelRanking/Engine/ModelFamilies.swift` is
written by `scripts/model_family_words.py`; this holds it equal to the registry."""

from __future__ import annotations

import pathlib
import re

from app.workflows import registry

SWIFT = pathlib.Path(__file__).resolve().parents[2] / "ios/ModelRanking/Engine/ModelFamilies.swift"


def _swift_set(name: str) -> set[str]:
    text = SWIFT.read_text(encoding="utf-8")
    match = re.search(rf"static let {name}: Set<String> = \[(.*?)\]", text, re.S)
    assert match, f"ModelFamilies.{name} not found"
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def test_the_phones_family_words_are_the_registrys() -> None:
    words = registry.family_words()
    assert {"qwen", "kimi", "mixtral", "o3", "claude", "gpt", "gemini", "phi"} <= words
    assert _swift_set("words") == set(words), "ModelFamilies.swift is stale: run scripts/model_family_words.py"


def test_every_family_word_is_a_word_the_phone_can_read() -> None:
    """Lower case letters and digits only, so the phone's tokens can equal it."""
    assert all(re.fullmatch(r"[a-z][a-z0-9]*", word) for word in registry.family_words())


# --- The M21-W2 review's M1 to M3 ---------------------------------------------------------------------------


def test_the_written_file_is_the_generators_byte_for_byte() -> None:
    """M2: the file is what `render()` writes, not only the same words."""
    from scripts.model_family_words import render

    assert SWIFT.read_text(encoding="utf-8") == render(), "ModelFamilies.swift is stale: run scripts/model_family_words.py"
