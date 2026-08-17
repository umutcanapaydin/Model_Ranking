"""M6-W3: the alias-expansion guard on curated YAML (W-005).

W-005 was raised at M4's security review and ACCEPTED with a stated trigger: *"both YAML inputs are
repo-committed data with no untrusted producer today. Owning milestone: M6 — the API surface is what
changes this boundary."* M6 is that milestone.

The guard is proved against the attack the review actually measured, not against a description of
it: a document of a few hundred bytes that expands to gigabytes through nested aliases.
"""

from __future__ import annotations

import pytest

from app.workflows.yaml_guard import (
    MAX_YAML_BYTES,
    YamlGuardError,
    safe_load_bounded,
)

#: The billion-laughs shape, as M4 measured it: each level aliases the one below it nine times, so
#: eight levels is 9^8 nodes from a document you can read in one screen.
BILLION_LAUGHS = """
a: &a ["x","x","x","x","x","x","x","x","x"]
b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]
c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]
d: &d [*c,*c,*c,*c,*c,*c,*c,*c,*c]
e: &e [*d,*d,*d,*d,*d,*d,*d,*d,*d]
f: &f [*e,*e,*e,*e,*e,*e,*e,*e,*e]
g: &g [*f,*f,*f,*f,*f,*f,*f,*f,*f]
h: [*g,*g,*g,*g,*g,*g,*g,*g,*g]
"""


def test_the_expansion_attack_is_refused_before_it_is_parsed() -> None:
    """The measured attack, refused — and refused WITHOUT parsing it.

    If this test ever hangs or dies instead of raising, the guard has been moved to after the
    parser, which is the one place it cannot work.
    """
    with pytest.raises(YamlGuardError, match="expands to"):
        safe_load_bounded(BILLION_LAUGHS, what="test input")


def test_the_real_curated_files_pass_the_guard() -> None:
    """A guard that refuses the project's own data is a broken guard, not a strict one."""
    from pathlib import Path

    for name in ("data/plans.yaml", "data/rosters.yaml"):
        raw = Path(name).read_text()
        assert safe_load_bounded(raw, what=name) is not None


def test_an_oversized_document_is_refused_by_size() -> None:
    """The cheap half of the bound, and the error names the artefact."""
    with pytest.raises(YamlGuardError, match="curated-input limit"):
        safe_load_bounded("a: " + "x" * (MAX_YAML_BYTES + 1), what="oversized input")


def test_the_guard_refuses_non_text_rather_than_guessing() -> None:
    """Fail loud on a caller that hands over an already-parsed document."""
    with pytest.raises(YamlGuardError, match="expected raw YAML text"):
        safe_load_bounded({"already": "parsed"}, what="wrong type")


def test_a_legitimate_flat_anchor_still_loads() -> None:
    """The guard bounds EXPANSION, not anchors. Curated data may reuse a value.

    This is the half a stricter guard would have broken: refusing anchors outright would refuse a
    reasonable curated file, which is how a security control becomes something people route around.
    """
    flat = "a: &a 1\nb: [" + ",".join(["*a"] * 500) + "]\n"
    assert safe_load_bounded(flat, what="flat anchors")["b"] == [1] * 500


def test_the_bound_is_on_the_expanded_size_not_the_alias_count() -> None:
    """The property, asserted directly — because the first version had the wrong instrument.

    It capped the NUMBER of aliases. The measured attack uses only 63 of them and expands to tens
    of millions of nodes, because growth is multiplicative in depth. The document below has fewer
    aliases than the flat one above and must be refused, while that one loads.
    """
    nested = "a: &a [1,1,1,1,1,1,1,1,1,1]\n"
    prev = "a"
    for level in "bcdefgh":
        nested += f"{level}: &{level} [" + ",".join([f"*{prev}"] * 10) + "]\n"
        prev = level
    assert nested.count("*") < 500  # fewer aliases than the flat document that loads fine
    with pytest.raises(YamlGuardError, match="expands to"):
        safe_load_bounded(nested, what="nested")


def test_every_yaml_entry_point_goes_through_the_guard() -> None:
    """Built is not wired (V3C-73). Three inputs, three guarded call sites, asserted from source.

    A guard installed on two of three inputs is a guard on none of them, and the third is always
    the one nobody remembered.
    """
    from pathlib import Path

    unguarded = []
    for name in ("plans", "rosters", "epoch"):
        source = Path(f"src/app/workflows/{name}.py").read_text()
        if "yaml.safe_load(" in source:
            unguarded.append(name)
    assert unguarded == [], f"these still call yaml.safe_load directly: {unguarded}"
