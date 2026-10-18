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


# #322 (D-209 clause 5; the #297 security review's M1, M2, M3 and N1). What `swiftc -dump-ast` printed for P5
# spelled three more ways (Xcode 26.6, measured 2026-10-18 on a probe compiled as the gate compiles the client):
# behind an associated type the compiler inferred, behind an explicit `typealias`, as an enum's payload, and
# through an existential metatype.
INFERRED_ALIAS = ('  (typealias decl_context=0x0 implicit "Item" interface_type="ProbeShape.Item.Type" access=internal '
                  'type="[Category]")\n')
EXPLICIT_ALIAS = ('  (typealias decl_context=0x0 range=[/x/{file}:17:1 - line:17:27] "Cats" interface_type="Cats.Type" '
                  'access=internal type="[Category]")\n')
ENVELOPE = (
    '  (enum_decl decl_context=0x0 range=[/x/{file}:12:1 - line:15:1] "ProbeEnvelope" '
    'interface_type="ProbeEnvelope.Type" access=internal non_resilient inherits="Decodable"\n'
    '    (enum_case_decl decl_context=0x0 range=[/x/{file}:13:5 - line:13:29]\n'
    '      (enum_element_decl decl_context=0x0 range=[/x/{file}:13:10 - line:13:29] "surfaces(_:)" '
    'interface_type="(ProbeEnvelope.Type) -> ([Category]) -> ProbeEnvelope" access=internal))\n'
    '    (constructor_decl decl_context=0x0 implicit "init(from:)" '
    'interface_type="(ProbeEnvelope.Type) -> (any Decoder) throws -> ProbeEnvelope" access=internal designated))\n'
)


def _decode_of(typed: str) -> str:
    """A `JSONDecoder.decode(_:from:)` whose generic substitution gives `T` the type `typed`, as printed."""
    return (f'  (declref_expr type="(JSONDecoder) -> ({typed}.Type, Data) throws -> {typed}" location=/x/{{file}}:32:32 '
            f'range=[/x/{{file}}:32:32 - line:32:32] decl="Foundation.(file).JSONDecoder.decode(_:from:) [with '
            f'(substitution_map generic_signature=<T where T : Decodable> T -> {typed})]" function_ref=single apply)\n')


@pytest.mark.parametrize(("alias", "typed"), [(INFERRED_ALIAS, "ProbeShape.Item"), (EXPLICIT_ALIAS, "Cats")],
                         ids=["inferred", "explicit"])
def test_322_a_kept_type_decoded_through_an_alias_is_refused(alias: str, typed: str) -> None:
    """#322 M1: the substitution prints the alias, not the type; the alias's `type=` names a `[Category]`. An
    alias the compiler inferred for an associated type, and one the source spells, are refused at the decode in
    the screen's file, and allowed where a kept answer is read back. # covers REQ-RTR-004, INV-67"""
    refused = _refused("ContentView.swift", f"through the alias `{typed}`",
                       _in("ContentView.swift", alias, _decode_of(typed)))
    assert refused and all("decodes `Category`" in line and "#297" in line for line in refused), refused
    assert not _refused("KeptAnswers.swift", "#297", _in("KeptAnswers.swift", alias, _decode_of(typed)))


def test_322_an_enum_whose_case_carries_a_kept_type_holds_it() -> None:
    """#322 M1: an enum's synthesised decoder is printed untyped, so its cases' payloads say what it holds. A
    `Decodable` enum with a `[Category]` payload is refused at its decode outside the files that may decode a
    surface. # covers REQ-RTR-004, INV-67"""
    ast = _in("ContentView.swift", ENVELOPE, _decode_of("ProbeEnvelope"))
    refused = _refused("ContentView.swift", "decodes `ProbeEnvelope`, which holds a `Category`", ast)
    assert refused, gate.problems(gate.references(ast))
    assert not _refused("KeptAnswers.swift", "#297", _in("KeptAnswers.swift", ENVELOPE, _decode_of("ProbeEnvelope")))


@pytest.mark.parametrize("file", ["ContentView.swift", "EngineClient.swift", "KeptAnswers.swift", "StandingsStore.swift"])
def test_322_a_decode_through_an_existential_is_refused_in_every_file(file: str) -> None:
    """#322 M1: `decode(t, …)` with `t: any Decodable.Type` prints `T -> any Decodable`, a type the gate cannot
    read, so it may be any kept answer's type. No file may decode one: no file may decode all three kept types.
    # covers REQ-RTR-004, INV-67"""
    refused = _refused(file, "an existential", _in(file, _decode_of("any Decodable")))
    assert refused and all("#297" in line for line in refused), refused


#: The shipping client's #297 facts in the simulator Release configuration (measured 2026-10-18, Xcode 26.6).
KEPT_SHIPPING = {
    "ContentView.swift": {"main.<called in>.StandingsStore.keep|ContentView|load()@1119",
                          "main.<called in>.StandingsStore.keep|ContentView|load()@1131"},
    "EngineClient.swift": {"main.<decodes>.CategoryList|Category@287", "main.<decodes>.Recommendation|Recommendation@269"},
    "KeptAnswers.swift": {"main.<decodes>.Category|Category@52", "main.<decodes>.Recommendation|Recommendation@42"},
    "StandingsStore.swift": {"main.<decodes>.KeptAnswer|KeptAnswer@199"},
}


def test_322_an_allowed_side_the_client_no_longer_shows_fails_the_gate() -> None:
    """#322 M2 (AGENTS.md §3.5: an empty derived set fails): rename `keep`, or the load path, or a kept type,
    and the rule matched nothing while the gate passed. The load path's `keep` and each allowed decode must be
    SEEN on the shipping client; one that is not is reported as a permission that matches nothing.
    # covers REQ-RTR-004, INV-67"""
    assert not [line for line in gate.unseen_permissions(KEPT_SHIPPING) if "#322" in line]
    renamed = {**KEPT_SHIPPING, "ContentView.swift": {"main.<called in>.StandingsStore.keep|ContentView|load(later:)@1"}}
    missing = [line for line in gate.unseen_permissions(renamed) if "#322" in line]
    assert any(line.startswith("ContentView.swift:") and "`StandingsStore.keep`" in line
               and "`ContentView.load()`" in line for line in missing), missing
    missing = [line for line in gate.unseen_permissions({}) if "#322" in line]
    for kept, (files, _) in gate.KEPT_ANSWER_TYPES.items():
        for file in files:
            assert any(line.startswith(f"{file}:") and f"a decode of `{kept}`" in line for line in missing), (kept, file)
    assert len(missing) == 1 + sum(len(files) for files, _ in gate.KEPT_ANSWER_TYPES.values()), missing


#: #322 M1, M3 and N1: the shapes the review found, planted in the fixture, each with the phrase its refusal
#: carries. The self-test requires each in every configuration (`FIXTURE_REFUSALS`), so a gate mutant that
#: silences one fails `make client-decls`.
PLANTS_322 = [
    # M1: P5 behind an inferred associated type, an explicit alias, an enum's payload and an existential.
    ("ContentView.swift", "through the alias `FixtureShape.Item`"),
    ("ContentView.swift", "through the alias `FixtureSurfaces`"),
    ("ContentView.swift", "decodes `FixtureEnvelope`, which holds a `Category`"),
    ("ContentView.swift", "an existential"),
    # M3: an answer built and decoded outside its files, a kept answer decoded in the screen's file, a surfaces'
    # list decoded by its initialiser's name, and a type that holds a type that holds one.
    ("Detail.swift", "builds Recommendation"),
    ("Detail.swift", "decodes `Recommendation`,"),
    ("ContentView.swift", "decodes `KeptAnswer`,"),
    ("Detail.swift", "decodes `CategoryList`, which holds a `Category`"),
    ("Detail.swift", "decodes `FixtureSurfacesShelf`, which holds a `Category`"),
    # N1: a load path of another name, and one in another type of the same simple name.
    ("ContentView.swift", "in `ContentView.load(later:)`, outside the load path"),
    ("ContentView.swift", "in `FixtureElsewhere.ContentView.load()`, outside the load path"),
]


@pytest.mark.parametrize(("file", "phrase"), PLANTS_322)
def test_322_each_shape_the_review_found_is_planted_and_refused(file: str, phrase: str) -> None:
    """#322 M3: five gate mutants survived because no plant held their rule; M1's and N1's shapes had none
    either. Each is refused on the compiled fixture's dump, and the self-test requires it.
    # covers REQ-RTR-004, INV-67"""
    assert _refused(file, phrase), (file, phrase)
    assert (file, phrase) in gate.FIXTURE_REFUSALS


def test_322_the_fixtures_load_path_is_allowed() -> None:
    """#322 N1: the fixture's load path is `ContentView.load()` by its full name, and its own `keep` calls are not
    refused."""
    assert not [line for line in _refused("ContentView.swift", "outside the load path") if "`ContentView.load()`," in line]


#: #322: the review's shapes compiled as the gate compiles the client, beside PROBE's allowed half.
PROBE_322 = {
    **PROBE,
    "ContentView.swift": (
        "import Foundation\n\n"
        "protocol ProbeShaped {\n    associatedtype Item: Decodable\n    func sample() -> Item?\n}\n\n"
        "struct ProbeShape: ProbeShaped {\n    func sample() -> [Category]? { nil }\n}\n\n"
        "enum ProbeEnvelope: Decodable {\n    case surfaces([Category])\n}\n\n"
        "typealias Cats = [Category]\n\n"
        "enum Elsewhere {\n    struct ContentView {\n"
        "        func load() { StandingsStore.onDevice.keep([Category]()) }\n    }\n}\n\n"
        "struct ContentView {\n"
        "    let client = EngineClient()\n    let asked = \"\"\n\n"
        "    func load() {\n"
        "        StandingsStore.onDevice.keep(client.categories(Data()))\n"
        "        let data = Data(asked.utf8)\n"
        "        if let one = try? JSONDecoder().decode(ProbeShape.Item.self, from: data) {\n"
        "            StandingsStore.onDevice.keep(one)\n        }\n"
        "        if case .surfaces(let two)? = try? JSONDecoder().decode(ProbeEnvelope.self, from: data) {\n"
        "            StandingsStore.onDevice.keep(two)\n        }\n"
        "        let erased: any Decodable.Type = [Category].self\n"
        "        if let three = try? JSONDecoder().decode(erased, from: data) as? [Category] {\n"
        "            StandingsStore.onDevice.keep(three)\n        }\n"
        "        if let four = try? JSONDecoder().decode(Cats.self, from: data) {\n"
        "            StandingsStore.onDevice.keep(four)\n        }\n    }\n\n"
        "    func load(later: Int) {\n        StandingsStore.onDevice.keep([Category]())\n    }\n}\n\n"
        "func probeDecodesByName(_ decoder: any Decoder) throws -> CategoryList {\n"
        "    try CategoryList(from: decoder)\n}\n"),
}


@pytest.mark.needs("xcode")  # the probe is compiled
def test_322_the_reviews_shapes_are_refused_on_a_compiled_client(tmp_path: Path) -> None:
    """#322, the real entry point: the review's M1 and N1 shapes and a decoder called by name, type-checked with
    the iOS SDK and judged as `make client-decls` judges the client. Each is refused, and nothing else: the load
    path's own `keep`, the engine client's decode and the store's kept answer are allowed.
    # covers REQ-RTR-004, INV-67"""
    for name, source in PROBE_322.items():
        (tmp_path / name).write_text(source, encoding="utf-8")
    _, sdk_name, flags = gate.CONFIGURATIONS[0]
    dumped = gate.dump_ast(sdk_name, flags, tmp_path)
    assert dumped is not None and dumped[1] == 0, dumped and dumped[0][-800:]
    refused = [line for line in gate.problems(gate.references(dumped[0])) if "#297" in line]
    for phrase in ("through the alias `ProbeShape.Item`", "through the alias `Cats`",
                   "decodes `ProbeEnvelope`, which holds a `Category`", "an existential",
                   "decodes `CategoryList`, which holds a `Category`",
                   "in `ContentView.load(later:)`, outside the load path",
                   "in `Elsewhere.ContentView.load()`, outside the load path"):
        assert [line for line in refused if line.startswith("ContentView.swift:") and phrase in line], (phrase, refused)
    assert len(refused) == 7, refused
