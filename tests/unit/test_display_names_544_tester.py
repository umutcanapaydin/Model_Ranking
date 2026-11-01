"""The release delta Tester of `integration/fixes-1101` (2026-11-01): #544's mixed-case words, "one way only".

`_mixed_case_words` (`src/app/workflows/registry.py`) takes a word's capitals from the registry's own names (`MiniMax`,
`DeepSeek`) "each where they capitalise it one way only". No word in today's tables is spelled two ways, so fault
F-R9 (the one-way rule dropped: the first spelling in sorted order wins) stayed green: the first table entry that
spells a family two ways would then name every new model of that family by whichever spelling sorts first.
"""

from __future__ import annotations

import pytest

from app.workflows import registry


# covers #544
def test_a_word_the_registry_capitalises_two_ways_takes_no_spelling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry, "DISPLAY_NAMES", {**registry.DISPLAY_NAMES, "zz-a": "ZetaForge A",
                                                    "zz-b": "Zetaforge B", "zz-c": "QuuxLab C"})
    words = registry._mixed_case_words()
    assert "zetaforge" not in words, words.get("zetaforge")
    assert words.get("quuxlab") == "QuuxLab", "the control: a word spelled one way keeps its capitals"
