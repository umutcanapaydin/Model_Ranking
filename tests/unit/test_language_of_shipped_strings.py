"""W-019 — the English-only gate detects an ALPHABET, not a language.

`check_records.py`'s `L1` rule fires on the six Turkish-specific letters (dotless-i, s-cedilla,
g-breve, c-cedilla, o-umlaut, u-umlaut -- named rather than written, because writing them here
made this very file fail `L1` on its first run, which is **GPF-005 reproducing itself**: no
record can state what the rule detects). Turkish
written in pure ASCII passes it silently, and that is not hypothetical: after D-118's migration was
declared complete and `make check` was green, **four ASCII Turkish fragments were still shipping in
live user-facing strings**, one of them rendering a single sentence in two languages. The migration
had followed the gate's signal and stopped exactly where the gate stops.

This is the narrow local mitigation, and its scope is stated rather than implied:

* It scans STRING LITERALS in `src/`, which is where user-facing prose is assembled — not prose in
  records, where a translated owner quote is legitimate evidence (V4C-79) and a marker word is
  expected to appear.
* It matches WHOLE WORDS from a conservative list: entries were chosen because they have no English
  meaning at all, so a hit is a hit. Ambiguous high-frequency words (`bir`, `de`, `da`, `ile`) are
  deliberately absent — a guard that cries wolf gets deleted, and a deleted guard detects nothing.
* It cannot detect Turkish that avoids every listed word. It is a tripwire on the likely forms, not
  a language detector, and saying so is the difference between this and the rule it supplements.

The general defect belongs to the pipeline, not to this project, and is handed back as **GPF-006**.
"""

from __future__ import annotations

import ast
import pathlib

SRC = pathlib.Path(__file__).resolve().parents[2] / "src"

#: ASCII spellings of Turkish words with no English meaning. Whole-word matches only.
TURKISH_ASCII = frozenset(
    {
        "icin", "degil", "olarak", "yuksek", "dusuk", "secim", "oneri", "kullanici",
        "guncel", "aciklama", "baglanti", "sunucu", "sorgu", "deger", "gore", "sonuc",
        "ozellik", "gerekli", "yeniden", "calisti", "basarili", "hata", "veri", "onceki",
        "bulunamadi", "gecerli", "yanlis", "dogru", "toplam", "ortalama", "fiyat",
    }
)


def _string_literals(path: pathlib.Path) -> list[tuple[int, str]]:
    """Every string constant in one module, with its line number.

    Parsed rather than grepped: a comment explaining that a word is Turkish is not a shipped
    string, and a guard that cannot tell those apart teaches people to stop writing the
    explanation.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            found.append((node.lineno, node.value))
    return found


def test_no_shipped_string_is_turkish_written_in_ascii() -> None:
    """Fails on a user-facing sentence that the letter-based gate cannot see.

    Reproduce the original defect to check this can fail: put `"Bu model secim icin uygun degil"`
    into any module under `src/` and this goes red where `L1` stays green.
    """
    offenders: list[str] = []
    for module in sorted(SRC.rglob("*.py")):
        for lineno, value in _string_literals(module):
            words = {word.strip(".,:;!?()[]'\"").lower() for word in value.split()}
            hits = sorted(words & TURKISH_ASCII)
            if hits:
                excerpt = value.strip()[:70]
                offenders.append(
                    f"{module.relative_to(SRC.parent.parent)}:{lineno}: {hits} in {excerpt!r}"
                )
    assert not offenders, (
        "these shipped strings contain Turkish written in ASCII, which the English-only rule "
        "cannot see because it detects an alphabet rather than a language (W-019):\n  "
        + "\n  ".join(offenders)
    )


def test_the_word_list_is_ascii_only_so_it_covers_what_the_letter_rule_cannot() -> None:
    """A marker containing a Turkish-specific letter would be caught by `L1` already.

    Such an entry is not wrong, it is INERT — and an inert entry in a guard's list is how the list
    grows until nobody believes it. This keeps the two rules from overlapping.
    """
    non_ascii = sorted(word for word in TURKISH_ASCII if not word.isascii())
    assert not non_ascii, (
        f"{non_ascii} carry Turkish-specific letters, which `L1` already detects; this list exists "
        "for exactly the words it cannot"
    )
    assert len(TURKISH_ASCII) >= 20, "the list has been pruned below usefulness"
