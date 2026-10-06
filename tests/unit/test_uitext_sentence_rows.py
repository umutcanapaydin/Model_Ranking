"""#127: every screen sentence has a row in `UITextLanguageTests`, which composes it in both languages.

The test's table is a hand-kept list beside the functions it covers, so these gates read the
functions from the app's sources and fail on one without a row (AGENTS.md section 3.5). They were
in `test_ios_client_contract.py`; they have a file of their own so that tests added to that file by
other changes do not collide with them.
"""

from __future__ import annotations

import pathlib
import re

CLIENT = pathlib.Path(__file__).resolve().parents[2] / "ios/ModelRanking"


def test_every_screen_sentence_has_a_row_in_the_language_test() -> None:
    """#127: `UITextLanguageTests` composes every `UIText` sentence in both languages and fails on
    one that is empty or the same in Turkish as in English. Its table is a hand-kept list beside the
    functions it covers, so the functions are read here from `Language.swift`, and a sentence added
    without a row, or a row naming no sentence, fails (AGENTS.md section 3.5)."""
    language = (CLIENT / "Engine/Language.swift").read_text(encoding="utf-8")
    declared: set[str] = set()
    for opening in re.finditer(r"^(?:public )?(?:enum|extension) UIText \{$", language, re.M):
        body = language[opening.end():]
        body = body[: re.search(r"^\}$", body, re.M).end()] if re.search(r"^\}$", body, re.M) else ""
        declared |= set(re.findall(r"\bstatic func (\w+)\(", body))
    assert len(declared) >= 40, f"read {len(declared)} UIText functions; was Language.swift read?"
    test = CLIENT.parent / "EngineTests/UITextLanguageTests.swift"
    rows = set(re.findall(r'\("(\w+)", \{', test.read_text(encoding="utf-8"))) if test.exists() else set()
    assert not declared - rows, f"sentences no test composes in both languages: {sorted(declared - rows)}"
    assert not rows - declared, f"rows naming no UIText function: {sorted(rows - declared)}"


def test_every_uitext_sentence_anywhere_in_the_app_has_a_row() -> None:
    """#127 (the fix Tester's T2): the sentence gate above reads `Language.swift` alone, and a
    function only as `static func name(`. A sentence declared in an `extension UIText` in another
    app file, or a generic one (`static func name<T>(`), passed it with no row. Here every `UIText`
    body in the app's sources is read, and every function declared in it."""
    declared: dict[str, str] = {}
    for path in sorted(CLIENT.rglob("*.swift")):
        if ".build" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for opening in re.finditer(r"^(?:\w+ )*(?:enum|extension) UIText\b[^{\n]*\{$", text, re.M):
            body = text[opening.end():]
            closing = re.search(r"^\}$", body, re.M)
            assert closing, f"{path.name}: a UIText body never closes"
            for name in re.findall(r"\bfunc\s+(\w+)\s*[<(]", body[: closing.end()]):
                declared[name] = path.name
    assert len(declared) >= 40, f"read {len(declared)} UIText functions; were the sources read?"
    table = CLIENT.parent / "EngineTests/UITextLanguageTests.swift"
    rows = set(re.findall(r'\("(\w+)", \{', table.read_text(encoding="utf-8")))
    missing = sorted(f"{name} ({where})" for name, where in declared.items() if name not in rows)
    assert not missing, f"sentences no test composes in both languages: {missing}"
