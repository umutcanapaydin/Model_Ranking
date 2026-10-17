"""#297 (D-206 clause 4): what the phone keeps in `answers.json` is what the engine sent, held by the
compiled gate (`scripts/client_decl_gate.py`, `make client-decls`) as well as by the types.

The #288 security review's MJ1: `StandingsStore.keep` could be called from any file, so a later change could
write the reader's typed words beside the standings and every gate stayed green. #296 narrowed `keep` to the
two decoded types; the re-review's R-m1 (probe P5) then decoded a `[Category]` from typed text in
`ContentView.load()` and kept it, and the gate still passed. So the gate holds both halves:

- `keep` is called only in the load path, `ContentView.load()`;
- a `Recommendation`, a `Category` or a `KeptAnswer`, or a type that holds one, is decoded or built only where
  the engine's answer is decoded (`EngineClient.swift`) or a kept answer is read back (`KeptAnswers.swift`,
  `StandingsStore.swift`).

What the client keeps on the phone is held in part by the compiled gate and the text pins: see INV-67 in
`docs/security-invariants.md`, whose gaps name what is not held.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("client_decl_gate", ROOT / "scripts" / "client_decl_gate.py")
assert _spec is not None and _spec.loader is not None
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

#: The compiled fixture's dump as committed, which the gate's self-test holds equal to its compile.
FLOW_AST = (ROOT / "tests" / "unit" / "data" / "g2_fixture_ast.txt").read_text(encoding="utf-8")  # raw: not Swift, the compiled dump


def _refused(file: str, phrase: str, ast: str = FLOW_AST) -> list[str]:
    return [line for line in gate.problems(gate.references(ast)) if line.startswith(f"{file}:") and phrase in line]


def test_a_kept_answer_is_kept_only_in_the_load_path() -> None:
    """MJ1: a `keep` call anywhere but `ContentView.load()` is refused, in the screen's own file and in
    another; the load path's own calls are not. # covers REQ-RTR-004, INV-67"""
    elsewhere = _refused("ContentView.swift", "outside the load path")
    assert any("`ContentView.keepElsewhere`" in line for line in elsewhere), elsewhere
    assert not [line for line in elsewhere if "in `ContentView.load`" in line], elsewhere
    assert _refused("Detail.swift", "outside the load path")


def test_p5_a_surfaces_list_decoded_from_the_typed_question_is_refused() -> None:
    """R-m1, probe P5: the typed question decoded into a `[Category]` inside the load path, and into a
    `CategoryList`, a type that holds one, is refused at the decode. # covers REQ-RTR-004, INV-67"""
    assert _refused("ContentView.swift", "decodes `Category`")
    assert _refused("ContentView.swift", "decodes `CategoryList`")


def test_a_kept_answers_types_are_built_only_by_a_decode() -> None:
    """R-m1: a surface built by its memberwise initialiser, and a kept answer built outside the store, are
    refused. # covers REQ-RTR-004, INV-67"""
    assert _refused("Detail.swift", "builds Category")
    assert _refused("Detail.swift", "builds KeptAnswer")


def test_the_engine_client_and_the_read_back_decode_a_kept_answer() -> None:
    """The fixture's allowed half: the engine client decodes the engine's answer and its surfaces' list, the
    kept answers' file decodes what the store kept, the store decodes its own file, and the models' file
    declares the types whose synthesised decoders run inside those decodes. None is refused."""
    refused = gate.problems(gate.references(FLOW_AST))
    for name in ("EngineClient.swift", "KeptAnswers.swift", "StandingsStore.swift", "Models.swift"):
        assert not [line for line in refused if line.startswith(f"{name}:") and "#297" in line], (name, refused)


#: What `swiftc -dump-ast` printed for the shipping client's two read-backs and its write (Xcode 26,
#: measured 2026-10-17, `KeptAnswers.swift:52`, `Models.swift`'s synthesised `CategoryList` decoder and
#: `StandingsStore.swift:215`), here under a file name of the test's choosing.
DECODED_LIST = (
    '  (declref_expr type="(JSONDecoder) -> ([Category].Type, Data) throws -> [Category]" '
    'location=/x/{file}:52:51 range=[/x/{file}:52:51 - line:52:51] '
    'decl="Foundation.(file).JSONDecoder.decode(_:from:) [with (substitution_map '
    'generic_signature=<T where T : Decodable> T -> [Category])]" function_ref=double apply)\n'
)
ENCODED_LIST = (
    '  (declref_expr type="(JSONEncoder) -> ([Category]) throws -> Data" location=/x/{file}:215:43 '
    'range=[/x/{file}:215:43 - line:215:43] decl="Foundation.(file).JSONEncoder.encode [with (substitution_map '
    'generic_signature=<T where T : Encodable> T -> [Category])]" function_ref=double apply)\n'
)
FIELD_DECODED = (
    '  (declref_expr type="(KeyedDecodingContainer<Category.CodingKeys>) -> (String.Type, Category.CodingKeys) '
    'throws -> String" location=/x/{file}:41:8 decl="Swift.(file).KeyedDecodingContainer.decode(_:forKey:) '
    '[with (substitution_map generic_signature=<K where K : CodingKey> K -> Category.CodingKeys)]" '
    'function_ref=double apply)\n'
)


def _in(file: str, *lines: str) -> str:
    return f'(source_file "/x/{file}"\n' + "".join(line.replace("{file}", file) for line in lines)


@pytest.mark.parametrize("file", ["ContentView.swift", "Detail.swift", "Router.swift"])
def test_the_measured_decode_of_a_surfaces_list_is_refused_outside_its_files(file: str) -> None:
    """The rule on what the compiler printed, so it runs where there is no Xcode: the shipping client's own
    decode of a `[Category]`, moved to another file, is refused there. # covers INV-67"""
    refused = _refused(file, "decodes `Category`", _in(file, DECODED_LIST))
    assert refused and all("#297" in line for line in refused), refused


def test_the_measured_decode_is_allowed_where_a_kept_answer_is_read_back() -> None:
    """The same decode in `KeptAnswers.swift` and in the engine client is allowed; an encode, and a field's
    decode inside a surface's own decoder, are not a decode of a kept answer's type."""
    for file in ("KeptAnswers.swift", "EngineClient.swift"):
        assert not _refused(file, "#297", _in(file, DECODED_LIST))
    for line in (ENCODED_LIST, FIELD_DECODED):
        assert not _refused("ContentView.swift", "#297", _in("ContentView.swift", line))


#: P5 and the load path, compiled as the gate compiles the client: the kept answers' types as the app
#: declares them, the store's two `keep`s, the engine client's decode, and a screen whose load path keeps
#: the engine's answer and, in P5, a surfaces' list decoded from the typed question.
PROBE = {
    "Models.swift": (
        "import Foundation\n\n"
        "struct Query: Codable {\n    let task: String\n}\n\n"
        "struct Recommendation: Codable {\n    let query: Query\n}\n\n"
        "struct Category: Codable {\n    let id: String\n}\n\n"
        "struct CategoryList: Codable {\n    let categories: [Category]\n}\n"),
    "EngineClient.swift": (
        "import Foundation\n\n"
        "struct EngineClient {\n"
        "    func categories(_ data: Data) -> [Category] {\n"
        "        (try? JSONDecoder().decode(CategoryList.self, from: data))?.categories ?? []\n    }\n}\n"),
    "StandingsStore.swift": (
        "import Foundation\n\n"
        "struct StandingsStore {\n    static var onDevice: StandingsStore { StandingsStore() }\n}\n\n"
        "struct KeptAnswer: Codable {\n    let task: String\n    let payload: Data\n}\n\n"
        "extension StandingsStore {\n"
        "    func keep(_ recommendation: Recommendation) {\n"
        "        _ = KeptAnswer(task: recommendation.query.task, payload: Data())\n    }\n\n"
        "    func keep(_ categories: [Category]) {\n        _ = categories\n    }\n}\n"),
    "ContentView.swift": (
        "import Foundation\n\n"
        "struct ContentView {\n"
        "    let client = EngineClient()\n\n"
        "    func load(_ data: Data, asked: String) {\n"
        "        StandingsStore.onDevice.keep(client.categories(data))\n"
        "        if let forged = try? JSONDecoder().decode([Category].self, from: Data(asked.utf8)) {\n"
        "            StandingsStore.onDevice.keep(forged)\n        }\n    }\n\n"
        "    func keepLater(_ data: Data) {\n"
        "        StandingsStore.onDevice.keep(client.categories(data))\n    }\n}\n"),
}


@pytest.mark.needs("xcode")  # the probe is compiled
def test_p5_and_a_keep_outside_the_load_path_are_refused_on_a_compiled_client(tmp_path: Path) -> None:
    """The real entry point: the probe is type-checked with the iOS SDK and judged as `make client-decls`
    judges the client. P5's decode and the second function's `keep` are refused, and nothing else is: the
    load path's own `keep`, the engine client's decode, the store's kept answer and the synthesised
    decoders are allowed. # covers REQ-RTR-004, INV-67"""
    for name, source in PROBE.items():
        (tmp_path / name).write_text(source, encoding="utf-8")
    _, sdk_name, flags = gate.CONFIGURATIONS[0]
    dumped = gate.dump_ast(sdk_name, flags, tmp_path)
    assert dumped is not None and dumped[1] == 0, dumped and dumped[0][-800:]
    refused = [line for line in gate.problems(gate.references(dumped[0])) if "#297" in line]
    assert any(line.startswith("ContentView.swift:") and "decodes `Category`" in line for line in refused), refused
    assert any(line.startswith("ContentView.swift:") and "`ContentView.keepLater`" in line
               and "outside the load path" in line for line in refused), refused
    assert len(refused) == 2, refused
