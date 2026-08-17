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
    """Built is not wired (V3C-73) — and the LIST OF INPUTS is derived, not written down.

    **This test previously hard-coded three module names, and that is how the wave shipped its worst
    defect.** It was written to prove "a guard on two of three inputs is a guard on none", and it
    was itself a guard on three of four: `src/app/clients/aider.py` parses a third-party HTTP body
    and was not in the literal, so the one input with a real untrusted producer was the one nobody
    checked. Both review seats found it independently.

    So the enumeration walks the whole source tree. A fifth YAML entry point added tomorrow fails
    here whether or not anyone remembers this file exists — which is the only version of
    "enumerated from code" that means anything.
    """
    import ast
    from pathlib import Path

    unguarded: list[str] = []
    for path in sorted(Path("src").rglob("*.py")):
        if path.name == "yaml_guard.py":
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if (
                node.func.attr in {"safe_load", "load", "full_load", "unsafe_load"}
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "yaml"
            ):
                unguarded.append(f"{path}:{node.lineno}")
    assert unguarded == [], f"these parse YAML without the bound: {unguarded}"


def test_the_guard_runs_before_the_parser_not_after() -> None:
    """Placement is the control. After the parse, the bound is a report on damage already done.

    The Tester moved the guard below `safe_load` and every test stayed green, while this file's own
    docstring claimed that was impossible. Asserted from source: the refusal must precede the load.
    """
    import ast
    from pathlib import Path

    source = Path("src/app/workflows/yaml_guard.py").read_text()
    fn = next(
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name == "safe_load_bounded"
    )
    lines = {"compose": None, "raise": None, "safe_load": None}
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "compose" and lines["compose"] is None:
                lines["compose"] = node.lineno
            if node.func.attr == "safe_load":
                lines["safe_load"] = node.lineno
        if isinstance(node, ast.Raise) and lines["raise"] is None:
            lines["raise"] = node.lineno
    assert lines["compose"] < lines["safe_load"], "the graph is composed after the document loads"
    assert lines["raise"] < lines["safe_load"], "the refusal happens after the document loads"


def test_a_recursive_anchor_is_refused_rather_than_undercounted() -> None:
    """Security MINOR-1: a cycle expands without bound, so it cannot be scored as small.

    The first cycle guard seeded the memo with 1 and let the recursion unwind, which scored
    `a: &a [*a,*a,...]` at 12 and let it through. Explicitly not ledgered: it is a one-line fix, and
    ledgering it would recreate exactly the W-005 pattern that produced this wave's worst finding.
    """
    with pytest.raises(YamlGuardError, match="recursive"):
        safe_load_bounded("a: &a [*a,*a,*a]\n", what="recursive anchor")


def test_the_guard_error_is_catchable_as_a_yaml_error() -> None:
    """K.8: CLI exit codes are a frozen contract, and the exception type is what preserves them.

    `YamlGuardError` subclassed `ValueError` alone, so every caller's `except yaml.YAMLError` was
    bypassed: malformed roster YAML went from a clean exit 2 to an uncaught traceback and exit 1 —
    and exit 1 in that CLI means "stale rosters found", so a CI cadence job would have read a parse
    failure as a staleness result.
    """
    import yaml as _yaml

    assert issubclass(YamlGuardError, _yaml.YAMLError)
    with pytest.raises(_yaml.YAMLError):
        safe_load_bounded("a: " + "x" * (MAX_YAML_BYTES + 1), what="caught as a YAML error")
