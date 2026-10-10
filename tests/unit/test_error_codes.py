"""#223 (M21-W3): the phone says every error code the engine can send in both languages, keyed on
`error.code`; the engine's English `message` is the fallback only for a code the app does not know.
Held from the source: every `_error(status, "code", ...)` in the engine has a case in the phone's
`EngineError.refusalSentence`, and the phone names no code the engine never sends."""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENGINE = ROOT / "src" / "app" / "adapter" / "main.py"
LANGUAGE = ROOT / "ios" / "ModelRanking" / "Engine" / "Language.swift"
CLIENT = ROOT / "ios" / "ModelRanking" / "Engine" / "EngineClient.swift"


def _engine_codes() -> set[str]:
    source = ENGINE.read_text(encoding="utf-8")
    codes = set(re.findall(r'_error\(\s*\d+\s*,\s*"([a-z_]+)"', source))
    assert len(codes) >= 6, f"the engine's error codes were not read: {sorted(codes)}"
    return codes


def _phone_codes() -> set[str]:
    source = LANGUAGE.read_text(encoding="utf-8")
    match = re.search(r"static func refusalSentence\(.*?\n    \}\n", source, re.S)
    assert match, "the phone has no refusalSentence"
    return set(re.findall(r'case "([a-z_]+)"', match.group(0)))


def _own_codes() -> set[str]:
    """The codes the phone gives a refusal itself (`code: "unexpected"`, the M21 repo review's M4)."""
    codes = set(re.findall(r'code:\s*"([a-z_]+)"', CLIENT.read_text(encoding="utf-8")))
    assert "unexpected" in codes, f"the phone's own refusal codes were not read: {sorted(codes)}"
    return codes


def test_every_code_the_engine_sends_has_a_sentence_on_the_phone() -> None:
    assert _engine_codes() - _phone_codes() == set(), (
        "codes the phone shows only in the engine's English"
    )


def test_every_code_the_phone_names_itself_has_a_sentence_too() -> None:
    """A Fly 502 or 503 becomes `unexpected`; a Turkish reader saw its English (the M21 repo review's M4)."""
    assert _own_codes() - _phone_codes() == set(), "a refusal the phone names itself, said only in English"


def test_the_phone_names_no_code_the_engine_never_sends() -> None:
    assert _phone_codes() - _engine_codes() - _own_codes() == set(), "a sentence for a code no engine sends"
