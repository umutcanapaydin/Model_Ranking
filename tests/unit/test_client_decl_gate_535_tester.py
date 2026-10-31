"""#535 (the release Tester, delta round 2026-10-31b): the standings sink may compare two dates through Foundation's
`Date.<=`, and the allowance is that one operator in that one sink.

`make client-decls` proves the allowance on this Mac's toolchain, but CI does not run it (#535's impact line), so a
removal or a widening would be seen only on the owner's next local commit. These hold both in the unit suite: the
operator the toolchain now binds passes in `StandingsStore.swift`, and the neighbouring operators, and the same
operator in the other sink, are still refused. The AST fragment is shaped as `swiftc -dump-ast` prints a resolved
operator reference (`decl="Foundation.(file).Date.<=@..."`).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("client_decl_gate_535_tester", ROOT / "scripts" / "client_decl_gate.py")
assert _spec is not None and _spec.loader is not None
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

NOT_LISTED = "is not on the list of Foundation declarations a privacy sink may reference"


def _compare(file: str, operator: str) -> str:
    return (f'(source_file "/x/{file}"\n'
            f'  (binary_expr type="Bool" location=/x/{file}:126:40 nothrow\n'
            f'    (dot_syntax_call_expr implicit type="(Date, Date) -> Bool" location=/x/{file}:126:40 nothrow\n'
            f'      (declref_expr type="(Date.Type) -> (Date, Date) -> Bool" location=/x/{file}:126:40 '
            f'decl="Foundation.(file).Date.{operator}@/SDK/Foundation.swiftmodule:1:1" function_ref=double apply))))\n')


def _refused(file: str, operator: str) -> list[str]:
    refs = gate.references(_compare(file, operator))
    assert refs.get(file) == {f"Foundation.Date.{operator}"}, refs
    return [line for line in gate.problems(refs) if line.startswith(f"{file}:") and NOT_LISTED in line]


def test_the_standings_sink_may_compare_two_dates_with_foundations_le() -> None:
    """# covers #535, D-180: `fetchedAt <= now` (StandingsStore.swift:126, :148) as the toolchain of 2026-10-31
    binds it. Red with the `Date.<=` entry removed from `SINK_FOUNDATION_ALLOWED`."""
    assert not _refused("StandingsStore.swift", "<=")


@pytest.mark.parametrize("operator", ["<", ">", ">=", "=="])
def test_no_other_date_operator_rode_in_with_it(operator: str) -> None:
    """# covers #535, D-180: the reviewed edit added one operator, the one the gate reported; the others the issue
    named as possible stay refused until a toolchain binds them and a review adds them."""
    assert _refused("StandingsStore.swift", operator)


def test_the_engine_client_sink_does_not_gain_the_operator() -> None:
    """# covers #535, D-180: the allowance is the standings sink's own list (#242), not every sink's."""
    assert _refused("EngineClient.swift", "<=")
