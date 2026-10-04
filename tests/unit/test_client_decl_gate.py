"""#51, #58 -- the compiler-level half of D-126 (`scripts/client_decl_gate.py`, `make client-decls`)
refuses what it is for, and that is held by tests rather than by hand-run review probes.

- The rules, on what the compiler printed: these run everywhere, including CI, which has no Xcode.
- The whole gate on a compiled fixture (`scripts/client_decl_fixtures/`): runs where Xcode is, and
  `make client-decls` runs the same fixture before it checks the app, so the gate cannot pass the
  app while it has stopped refusing.
"""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("client_decl_gate", ROOT / "scripts" / "client_decl_gate.py")
assert _spec is not None and _spec.loader is not None
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

#: What `swiftc -dump-ast` printed for `JSONDecoder().decode([URL].self, from:)` (Xcode 26, measured).
DECODED_URL = (
    '(source_file "/x/ContentView.swift"\n'
    '  (declref_expr type="(JSONDecoder) -> ([URL].Type, Data) throws -> [URL]" '
    'decl="Foundation.(file).JSONDecoder.decode(_:from:) [with (substitution_map '
    'generic_signature=<T where T : Decodable> T -> [URL])]" function_ref=single apply)\n'
)


def test_the_network_and_the_file_system_are_refused_outside_their_files() -> None:
    """#51: `URLSession` outside `EngineClient.swift`, `FileManager` outside `FILESYSTEM_FILES`."""
    found = {
        "ContentView.swift": {"Foundation.URLSession"},
        "Detail.swift": {"Foundation.FileManager"},
        "EngineClient.swift": {"Foundation.URLSession"},
        "StandingsStore.swift": {"Foundation.FileManager"},
    }
    refused = gate.problems(found)
    assert len(refused) == 2, refused
    assert any(line.startswith("ContentView.swift:") and "network" in line for line in refused)
    assert any(line.startswith("Detail.swift:") and "file system" in line for line in refused)


def test_a_url_decoded_outside_the_engine_client_is_the_network() -> None:
    """#58: a URL made by decoding was neither a spelling nor an initialiser, so both gates missed it."""
    found = gate.references(DECODED_URL)
    assert "Foundation.URL.decoded" in found["ContentView.swift"], found
    refused = gate.problems(found)
    assert any("ContentView.swift" in line and "network" in line for line in refused), refused
    assert gate.problems({"EngineClient.swift": found["ContentView.swift"]}) == []


@pytest.mark.skipif(shutil.which("xcrun") is None, reason="needs Xcode's compiler: the fixture is compiled")
def test_the_gate_refuses_its_compiled_fixture() -> None:
    """#51: the whole gate, compiled, on files that must be refused and files that must be allowed."""
    assert gate.self_test() == []
