"""#51, #58 -- the compiler-level half of D-126 (`scripts/client_decl_gate.py`, `make client-decls`)
refuses the forms its lists name, and that is held by tests rather than by hand-run review probes.
What the client keeps on the phone is held in part by the compiled gate and the text pins: see
INV-62, INV-63, INV-64, INV-66, INV-67, INV-75, INV-76, INV-85 and INV-89 in
`docs/security-invariants.md`, whose gaps name what is not held.

- The rules, on what the compiler printed: these run everywhere, including CI, which has no Xcode.
- The whole gate on a compiled fixture (`scripts/client_decl_fixtures/`): runs where Xcode is, and
  `make client-decls` runs the same fixture before it checks the app, so the gate cannot pass the
  app while a rule `FIXTURE_RULES` names has stopped refusing (G-10).
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


@pytest.mark.needs("xcode")  # the fixture is compiled
def test_the_gate_refuses_its_compiled_fixture() -> None:
    """#51: the whole gate, compiled, on files that must be refused and files that must be allowed.

    The M21-W3 Tester (#175 R3, G-10): the self-test asks for one refusal per (file, phrase) and compares the
    committed dump with the compile by its declarations only. So a fixture shape whose body changed, while
    another shape still carried its phrase, left every test green: `keepAsked`'s `task = typed` (#188) made
    `_ = typed` passed the self-test, and the tests that count shapes read the stale dump. The compiled
    fixture is refused line for line as the committed dump is. # covers REQ-GAP-001, REQ-APP-005"""
    assert gate.self_test() == []
    _, sdk_name, flags = gate.CONFIGURATIONS[0]
    dumped = gate.dump_ast(sdk_name, flags, gate.FIXTURES)
    assert dumped is not None and dumped[1] == 0, dumped and dumped[0][-800:]
    compiled = gate.references(gate.fixture_dump(dumped[0]))
    committed = gate.references(FLOW_AST)
    assert sorted(gate.problems(compiled)) == sorted(gate.problems(committed)), (
        "the fixture as it compiles is not refused as the committed dump is; write it again with `--snapshot`")
    assert sorted(gate.release_problems(compiled)) == sorted(gate.release_problems(committed))


#: What `swiftc -dump-ast` prints for a synthesised `Decodable` with an `Optional<URL>` property.
DECODED_OPTIONAL_URL = (
    '(source_file "/x/ContentView.swift"\n'
    '  (declref_expr decl="Swift.(file).KeyedDecodingContainer.decodeIfPresent(_:forKey:) [with '
    '(substitution_map generic_signature=<T where T : Decodable> T -> URL)]" function_ref=single apply)\n'
)


def test_a_url_decoded_if_present_is_the_network_too() -> None:
    """W5 review B1 (#58): `decodeIfPresent`, which Swift generates for every optional property, was
    not matched; `struct B: Decodable { let u: URL? }` passed the gate in all four configurations."""
    assert "Foundation.URL.decoded" in gate.references(DECODED_OPTIONAL_URL)["ContentView.swift"]


def test_make_client_decls_fails_when_its_self_test_does(monkeypatch: pytest.MonkeyPatch) -> None:
    """W5 Tester: `main()` runs the self-test before it checks the app, so the gate cannot pass the app
    while a rule `FIXTURE_RULES` names has stopped refusing (#51, G-10). Nothing held that: with the call unwired, every test here and
    `make client-decls` passed. A failed self-test returns before anything compiles, so this runs
    where there is no Xcode too."""
    monkeypatch.setattr(gate, "self_test", lambda: ["ContentView.swift: URL.decoded was not refused"])
    assert gate.main() == 1


def test_a_release_build_carries_no_ui_test_hook() -> None:
    """D-175 clause 3: the launch arguments the scripted router is handed are read in Debug only."""
    found = {"LaunchRouting.swift": {"Foundation.ProcessInfo.arguments", "Swift.CommandLine.arguments"}}
    assert len(gate.release_problems(found)) == 2
    # Review M5: the launch environment is as easy to set from a UI test as the arguments.
    assert len(gate.release_problems({"LaunchRouting.swift": {"Foundation.ProcessInfo.environment"}})) == 1
    inert = {"LaunchRouting.swift": {"Foundation.ProcessInfo.processInfo", "main.ScriptedModelRouter"}}
    assert gate.release_problems(inert) == []


def test_main_refuses_a_release_dump_that_carries_a_ui_test_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    """W2 Tester (D-175 clause 3, review M5): the test above holds `release_problems`; nothing held
    that `main()` calls it, or calls it on the Release configurations. With the call removed, every
    test and `make client-decls` passed. Canned dumps stand in for the compiler, so this runs on CI."""
    names = {path.name for path in gate.CLIENT.rglob("*.swift")}

    def dumps(hooked: str, decl: str) -> None:
        monkeypatch.setattr(gate, "dump_ast", lambda sdk_name, flags, folder=gate.CLIENT: (
            "debug" if "DEBUG" in flags else "release", 0))
        monkeypatch.setattr(gate, "references", lambda ast: {
            name: ({decl} if name == "LaunchRouting.swift" and ast == hooked else set()) for name in names})

    monkeypatch.setattr(gate, "self_test", lambda: [])
    monkeypatch.setattr(gate, "problems", lambda found: [])
    monkeypatch.setattr(gate, "unseen_permissions", lambda found: [])
    dumps("release", "Foundation.ProcessInfo.environment")
    assert gate.main() == 1, "a Release build that reads its launch environment passed"
    dumps("debug", "Foundation.ProcessInfo.arguments")
    assert gate.main() == 0, "the Debug-only hook was refused in a Debug build"


#: #85 (D-180): what `swiftc -dump-ast` prints for the M17 relays and P3, trimmed from the compiled
#: fixture (`scripts/client_decl_fixtures/`, Xcode 26). A sink file's static `var`, a global `var` the
#: screen sets and the sink reads, and standings built from typed text; beside them, what the gate
#: must allow: a `let`, a computed property, a function's local, a non-sink reading the global, and
#: the standings initialiser's own parameter.
SINK_AST = (
    '(source_file "/x/EngineClient.swift"\n'
    '  (struct_decl range=[/x/EngineClient.swift:1:1 - line:9:1] "Relay" interface_type="Relay.Type" access=internal\n'
    '    (var_decl decl_context=0x1 range=[/x/EngineClient.swift:2:36 - line:2:36] "tag" interface_type="String" '
    'access=internal static readImpl=stored writeImpl=stored readWriteImpl=stored nonisolated(unsafe)\n'
    '    (var_decl decl_context=0x1 range=[/x/EngineClient.swift:3:16 - line:3:16] "limit" interface_type="Int" '
    'access=internal let static readImpl=stored immutable\n'
    '    (var_decl decl_context=0x1 range=[/x/EngineClient.swift:4:16 - line:4:16] "computed" interface_type="Int" '
    'access=internal static readImpl=getter immutable\n'
    '    (func_decl range=[/x/EngineClient.swift:5:5 - line:8:5] "build()" interface_type="(Relay) -> () -> String" access=internal\n'
    '      (brace_stmt range=[/x/EngineClient.swift:5:20 - line:8:5]\n'
    '        (var_decl decl_context=0x2 range=[/x/EngineClient.swift:6:13 - line:6:13] "parts" interface_type="[String]" '
    'access=private readImpl=stored writeImpl=stored readWriteImpl=stored\n'
    '        (member_ref_expr type="@lvalue String" location=/x/EngineClient.swift:7:20 '
    'decl="main.(file).Relay.tag@/x/EngineClient.swift:2:36")\n'
    '        (declref_expr type="@lvalue String" location=/x/EngineClient.swift:7:30 '
    'decl="main.(file).screenRelay@/x/ContentView.swift:3:25" function_ref=unapplied)))))\n'
    '(source_file "/x/ContentView.swift"\n'
    '  (var_decl decl_context=0x3 range=[/x/ContentView.swift:3:25 - line:3:25] "screenRelay" interface_type="String" '
    'access=internal readImpl=stored writeImpl=stored readWriteImpl=stored nonisolated(unsafe)\n'
    '  (func_decl range=[/x/ContentView.swift:5:1 - line:7:1] "keep(_:)" interface_type="(String) -> FetchedStandings?" access=internal\n'
    '    (brace_stmt range=[/x/ContentView.swift:5:40 - line:7:1]\n'
    '      (declref_expr implicit type="(FetchedStandings.Type) -> (Data) throws -> FetchedStandings" '
    'location=/x/ContentView.swift:6:10 decl="main.(file).FetchedStandings.init(payload:)@/x/Models.swift:9:5" '
    'function_ref=single apply))))\n'
    '(source_file "/x/Detail.swift"\n'
    '  (declref_expr type="String" location=/x/Detail.swift:2:5 decl="main.(file).screenRelay@/x/ContentView.swift:3:25" '
    'function_ref=unapplied)\n'
    '(source_file "/x/Models.swift"\n'
    '  (declref_expr type="Data" location=/x/Models.swift:9:15 '
    'decl="main.(file).FetchedStandings.init(payload:).data@/x/Models.swift:9:15" function_ref=unapplied)\n'
)


def test_a_sink_holding_or_reading_shared_mutable_state_is_refused() -> None:
    """#85 (D-180 clause 2): the M17 relay P2 kept a refinement in a `static var` on `EngineClient`, and
    a variant kept it in a global `var` the screen sets; both passed every gate, which scoped by file.
    A sink file's mutable stored state, and its reads of any other file's, are refused. REQ-GAP-001."""
    refused = gate.problems(gate.references(SINK_AST))
    assert any(line.startswith("EngineClient.swift:") and "`tag`" in line and "mutable stored state" in line
               for line in refused), refused
    assert any(line.startswith("EngineClient.swift:") and "`screenRelay`" in line
               and "mutable state declared in ContentView.swift" in line for line in refused), refused


def test_standings_built_outside_the_two_sinks_are_refused() -> None:
    """#85 (D-180 clause 2): P3 made the typed question into `FetchedStandings` on the screen and saved
    it into the device's caches. Only the engine's answer and the store's own file build standings. REQ-GAP-001."""
    refused = gate.problems(gate.references(SINK_AST))
    assert any(line.startswith("ContentView.swift:") and "builds FetchedStandings" in line for line in refused), refused


def test_what_the_sinks_may_hold_and_others_may_read_passes() -> None:
    """#85 (D-180): a `let`, a computed property and a function's local are not shared state; a file
    that is not a sink may read a global; the standings initialiser's own parameter is not a call. REQ-GAP-001."""
    refused = gate.problems(gate.references(SINK_AST))
    allowed = ("`limit`", "`computed`", "`parts`")
    assert not [line for line in refused if any(name in line for name in allowed)], refused
    assert not [line for line in refused if line.startswith(("Detail.swift:", "Models.swift:"))], refused


#: #60 (G-2): what `swiftc -dump-ast` printed for the whole compiled fixture (Xcode 26), paths made
#: `/x/`: `Combine.swift`'s permitted position arithmetic and its two sorts of a list named `common`,
#: `ContentView.swift` adding to a served position through another name, and since the W2 review's B1
#: every shape that review got past the gate.
FLOW_AST = (ROOT / "tests" / "unit" / "data" / "g2_fixture_ast.txt").read_text(encoding="utf-8")


def _without(ast: str, function: str) -> str:
    """`ast` with one top-level function's subtree removed."""
    out, skipping = [], False
    for line in ast.splitlines():
        if line.startswith("  (func_decl"):
            skipping = f'"{function}"' in line
        elif line.startswith("(source_file"):
            skipping = False
        if not skipping:
            out.append(line)
    return "\n".join(out) + "\n"


def test_arithmetic_on_a_served_position_through_another_name_is_refused() -> None:
    """#60 (the M17-W4 review's R4): `let place = standing.position; place + 1` passed the text
    tripwire, which matches the words around the operator. The compiler follows the value. REQ-APP-005."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("ContentView.swift:") and "served position" in line for line in refused), refused
    # M19-W2 Tester: the fixture's other shapes refuse a served position in this file too, so the line
    # above held nothing of R4's own; with the binding rule off it stayed green. The refusal must be on
    # R4's own lines. # covers REQ-APP-005, D-181 clause 2 (a binding)
    span = _lines_of("ContentView.swift", "func fixtureViewRanksByHand")
    own = [line for line in refused if line.startswith("ContentView.swift:") and "served position" in line
           and int(line.split(":")[1]) in span]
    assert own, ("R4's own `let place = standing.position; place + 1` is not refused", refused)


def test_a_second_sort_under_a_permitted_name_is_refused() -> None:
    """#60 (the M17-W4 Tester's M7): a second `common.sorted()` in `Combine.swift` passed, because the
    permission was keyed by the receiver's name. Each permitted sort is counted. REQ-APP-002."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("Combine.swift:") and "sorts `common`" in line for line in refused), refused
    once = gate.problems(gate.references(_without(FLOW_AST, "fixtureCombinesTwice(_:)")))
    assert not [line for line in once if "sorts `common`" in line], once


def test_permitted_arithmetic_passes_where_its_ruling_names_the_file() -> None:
    """#60: D-167 lets `Combine.swift` rank positions; the gate refuses nothing there for it. REQ-APP-005."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert not [line for line in refused if line.startswith("Combine.swift:") and "served position" in line], refused


#: #107: what `swiftc -dump-ast` prints for a URL made by a call whose name is no initialiser: a
#: generic decode wrapper declared in another file and called with `URL`. Beside it, what must pass:
#: the screen reading the engine's address, and the one door making its URL.
MADE_URL_AST = (
    '(source_file "/x/ContentView.swift"\n'
    '  (call_expr type="URL?" location=/x/ContentView.swift:3:5 nothrow isolation_crossing="none"\n'
    '    (declref_expr type="(URL.Type, Data) -> URL?" location=/x/ContentView.swift:3:5 '
    'decl="main.(file).fixtureDecode(_:from:)@/x/Detail.swift:3:6 [with (substitution_map '
    'generic_signature=<T where T : Decodable> T -> URL)]" function_ref=single apply))\n'
    '  (member_ref_expr type="URL" location=/x/ContentView.swift:5:20 '
    'decl="main.(file).EngineClient.baseURL@/x/EngineClient.swift:2:9")\n'
    '(source_file "/x/EngineClient.swift"\n'
    '  (call_expr type="URL?" location=/x/EngineClient.swift:4:10 nothrow isolation_crossing="none"\n'
    '    (declref_expr type="(String) -> URL?" location=/x/EngineClient.swift:4:10 '
    'decl="Foundation.(file).URL.init(string:)" function_ref=single apply))\n'
)


def test_a_url_made_by_any_call_outside_its_files_is_refused() -> None:
    """#107: `URL(_:strategy:)` and a generic decode wrapper make a URL from text with no initialiser
    or decode the gate listed. A call whose result is a URL is refused outside the network door and
    the two stores, whatever it is called; reading a URL that exists is not making one. REQ-GAP-001."""
    refused = gate.problems(gate.references(MADE_URL_AST))
    assert any(line.startswith("ContentView.swift:") and "makes a URL" in line for line in refused), refused
    assert not [line for line in refused if line.startswith("EngineClient.swift:")], refused
    assert len([line for line in refused if "makes a URL" in line]) == 1, refused


def test_a_link_detector_is_the_network() -> None:
    """#107: `NSDataDetector` with the `.link` type finds URLs in text, so it is the network's first
    step, as a URL made from a string is. REQ-GAP-001."""
    refused = gate.problems({"ContentView.swift": {"Foundation.NSDataDetector"}})
    assert any("NSDataDetector" in line and "network" in line for line in refused), refused


def test_turning_cookies_off_is_the_one_cookie_symbol_allowed_and_only_in_the_door() -> None:
    """#144: the session sets `HTTPCookie.AcceptPolicy.never`, a member of a family the gate refuses
    (cookies go to a store the system writes). That one value is allowed in the network door only. REQ-GAP-001."""
    assert gate.problems({"EngineClient.swift": {"Foundation.HTTPCookie.AcceptPolicy.never"}}) == []
    assert gate.problems({"ContentView.swift": {"Foundation.HTTPCookie.AcceptPolicy.never"}})
    assert gate.problems({"EngineClient.swift": {"Foundation.HTTPCookieStorage.shared"}})


#: The W2 review's B2: what `swiftc -dump-ast` prints for its two routes onto the boards request. A
#: client built on an address of a file's own (U5, U3b), an address made from text by the engine
#: client's helper (U3b), and a URL inside a dictionary (U5). Beside them, what must pass: the app's
#: `EngineClient()` and the engine client building itself.
CLIENT_AST = (
    '(source_file "/x/Detail.swift"\n'
    '  (call_expr type="[String : URL]?" location=/x/Detail.swift:9:21 nothrow isolation_crossing="none"\n'
    '    (declref_expr type="(URL, Data) -> [String : URL]?" location=/x/Detail.swift:9:21 '
    'decl="main.(file).fixtureReadLike(_:from:)@/x/Detail.swift:3:6 [with (substitution_map '
    'generic_signature=<T where T : Decodable> T -> URL)]" function_ref=single apply))\n'
    '  (declref_expr type="(EngineClient.Type) -> (URL, URLSession?) -> EngineClient" location=/x/Detail.swift:10:12 '
    'decl="main.(file).EngineClient.init(baseURL:session:)@/x/EngineClient.swift:30:5" function_ref=single apply)\n'
    '(source_file "/x/StandingsStore.swift"\n'
    '  (declref_expr type="(String) -> URL" location=/x/StandingsStore.swift:20:40 '
    'decl="main.(file).EngineClient.engineURL(from:)@/x/EngineClient.swift:36:17" function_ref=single apply)\n'
    '(source_file "/x/ContentView.swift"\n'
    '  (declref_expr type="(EngineClient.Type) -> () -> EngineClient" location=/x/ContentView.swift:85:30 '
    'decl="main.(file).EngineClient.init()@/x/EngineClient.swift:26:5" function_ref=single apply)\n'
    '(source_file "/x/EngineClient.swift"\n'
    '  (declref_expr type="(EngineClient.Type) -> (URL, URLSession?) -> EngineClient" location=/x/EngineClient.swift:27:9 '
    'decl="main.(file).EngineClient.init(baseURL:session:)@/x/EngineClient.swift:30:5" function_ref=single apply)\n'
)


def test_only_the_engine_client_builds_a_client_on_an_address_of_its_own() -> None:
    """The W2 review's B2 (D-180, INV-66, REQ-GAP-001): the typed question reached the boards request
    with every gate green, through a client another file built on its own address (U5 from
    `Detail.swift`, U3b from `FrontDoor.swift`). Only `EngineClient.swift` builds a client with an
    address, or makes one from text; the app builds `EngineClient()`."""
    refused = gate.problems(gate.references(CLIENT_AST))
    assert any(line.startswith("Detail.swift:") and "EngineClient.init(baseURL:session:)" in line
               for line in refused), refused
    assert any(line.startswith("StandingsStore.swift:") and "EngineClient.engineURL(from:)" in line
               for line in refused), refused
    assert not [line for line in refused if line.startswith(("ContentView.swift:", "EngineClient.swift:"))], refused


def test_a_url_inside_another_type_is_made_all_the_same() -> None:
    """The W2 review's B2 (INV-63): a generic decode returning `[String: URL]` made a URL the rule,
    which matched `URL`, `URL?` and `[URL]` only, never saw. REQ-GAP-001."""
    refused = gate.problems(gate.references(CLIENT_AST))
    assert any(line.startswith("Detail.swift:") and "makes a URL" in line for line in refused), refused


def _constructed(type_: str) -> str:
    return ('(source_file "/x/ContentView.swift"\n'
            f'  (constructor_ref_call_expr type="{type_}" location=/x/ContentView.swift:3:5 '
            'range=[/x/ContentView.swift:3:5 - line:3:5] nothrow isolation_crossing="none"\n')


def test_a_call_that_takes_a_url_is_not_one_that_makes_one() -> None:
    """Found replaying the review's K1 on the B2 fix: `XMLParser(contentsOf:)` was refused as making
    a URL, because the rule read the constructor's whole type, `(URL) -> XMLParser?`. What a call
    makes is what it returns, after its last arrow. REQ-GAP-001."""
    assert gate.url_facts(_constructed("(URL) -> XMLParser?")) == {}
    assert gate.url_facts(_constructed("(__shared String) -> URL?")) == {"ContentView.swift": {"Foundation.URL.made"}}
    assert gate.url_facts(_constructed("(Data) -> [String : URL]?")) == {"ContentView.swift": {"Foundation.URL.made"}}


FIXTURES = ROOT / "scripts" / "client_decl_fixtures"


def _lines_of(file: str, declaration: str) -> range:
    """The lines a fixture declaration spans: from its line to the next `}` in column one."""
    lines = (FIXTURES / file).read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines, start=1) if declaration in line)
    end = next(i for i, line in enumerate(lines, start=1) if i > start and line.startswith("}"))
    return range(start, end + 1)


@pytest.mark.parametrize(("file", "declaration"), [
    ("ContentView.swift", "func fixtureA1Reassigned"),       # a reassigned local
    ("ContentView.swift", "func fixtureA2Returned"),         # a function's return value
    ("ContentView.swift", "var fixtureA3Next"),              # a computed property on a decoded type
    ("ContentView.swift", "func fixtureA5Wrapping"),         # `&+`
    ("ContentView.swift", "func fixtureA6Advanced"),         # `.advanced(by:)`
    ("ContentView.swift", "func fixtureA7Converted"),        # `Int32(...)`, then `+`
    ("ContentView.swift", "func fixtureA8Unlisted"),         # a decoded field no table listed
    ("ContentView.swift", "func fixtureA10Literal"),         # a loop over a literal
    ("ContentView.swift", "func fixtureA11Tuple"),           # a loop's tuple pattern
    ("ContentView.swift", "struct FixtureRanker"),           # a method's parameter
    ("ContentView.swift", "func fixtureClosure"),            # a closure's `$0`
    ("Router.swift", "func fixtureRouterDiscounts"),         # the review's M5: outside `priceInPages`
    ("ContentView.swift", "func fixtureIfLet"),              # a condition's binding
    ("ContentView.swift", "func fixtureGuardLet"),           # `guard let`
    ("ContentView.swift", "func fixtureCase"),               # a case's binding
    ("ContentView.swift", "func fixtureThroughABox"),        # a memberwise initialiser, then the field
    ("ContentView.swift", "func fixtureAsAValue"),           # a function as a value
    ("ContentView.swift", "func fixtureAppended"),           # a mutating method's argument
    ("ContentView.swift", "func fixtureByProtocol"),         # a protocol requirement's witness
    ("ContentView.swift", "func fixtureCompound"),           # `-=`
])
def test_arithmetic_on_a_served_number_is_refused_in_the_forms_the_fixture_holds(file: str, declaration: str) -> None:
    """The W2 review's B1 (D-181, INV-76, REQ-APP-005): the review got arithmetic on a served number past
    the gate through each of these. Each is refused, on a line of its own declaration; any other form
    is not held (G-2; see INV-76)."""
    span = _lines_of(file, declaration)
    refused = gate.problems(gate.references(FLOW_AST))
    hits = [line for line in refused if line.startswith(f"{file}:") and "served" in line
            and int(line.split(":")[1]) in span]
    assert hits, (declaration, [line for line in refused if line.startswith(f"{file}:")])


def test_foundations_sort_is_counted_as_a_sort() -> None:
    """The W2 review's M4: `sorted(using:)` (Foundation) passed the compiled sort rule, which read the
    standard library's sorts only. REQ-APP-002."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("ContentView.swift:") and "sorts `standings`" in line for line in refused), refused


def test_the_price_in_pages_is_permitted_where_it_is_computed() -> None:
    """The W2 review's M5: the price permission is `priceInPages`'s, not the whole file's. REQ-APP-005."""
    refused = gate.problems(gate.references(FLOW_AST))
    span = _lines_of("Router.swift", "func priceInPages")
    assert not [line for line in refused if line.startswith("Router.swift:") and int(line.split(":")[1]) in span], refused


def test_a_sink_holds_nothing_another_file_can_change() -> None:
    """The W2 review's M1, S3 (D-180 clause 2, INV-66, REQ-GAP-001): `static let probeRelay =
    NSMutableString()` on the client, set by the screen and read by the request, passed: the rule
    refused a `var`, and a `let` holding a mutable object is as shared. What a sink holds is a
    listed type; nothing else in the fixture's sinks is refused for it."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("EngineClient.swift:") and "holds `relay`" in line for line in refused), refused
    # #172 adds the fixture's kept closure (`holds `make``), refused for the same reason.
    assert not [line for line in refused if "holds `" in line and "holds `relay`" not in line
                and "holds `make`" not in line], refused


def test_a_sink_calls_nothing_another_file_declares_but_what_is_listed() -> None:
    """The W2 review's M1, S2b (D-180 clause 2, INV-66, REQ-GAP-001): a sink calling a function that
    `Detail.swift` declares reads whatever that function reads, and the screen can set it. A sink
    calls only the functions listed for it, each with its reason."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("EngineClient.swift:") and "calls `fixtureRelayed`" in line for line in refused), refused
    # #172 adds the fixture's stored default, reached by the sink's call to `FixtureDefaulted.init`.
    assert not [line for line in refused if "calls `" in line and "fixtureRelayed" not in line
                and "FixtureDefaulted.init" not in line], refused


def _refused_in(file: str, phrase: str) -> list[str]:
    return [line for line in gate.problems(gate.references(FLOW_AST)) if line.startswith(f"{file}:") and phrase in line]


def test_a_kept_type_is_extended_only_in_its_own_file_and_conforms_to_no_protocol_the_app_declares() -> None:
    """The second W2 review's B1, P3w (D-180, INV-66, REQ-GAP-001): the M17 mutant P3 again, through a
    protocol requirement `FetchedStandings.init(payload:)` satisfies, passed `make check-fast`: the
    provenance rule reads references to the initialiser by name, and a requirement is another name."""
    assert _refused_in("Detail.swift", "conforms to `FixtureMadeFromBytes`")
    assert _refused_in("Detail.swift", "extends `FetchedStandings`")


def test_only_the_store_builds_a_store_or_saves_to_one() -> None:
    """The second W2 review's U10 and P3w (D-180, INV-66, REQ-GAP-001): a store built on a path made
    from the question, and standings saved from another file, each passed every compiled check."""
    assert _refused_in("Detail.swift", "StandingsStore.init(url:)")
    assert _refused_in("Detail.swift", "StandingsStore.save(_:at:)")
    assert not _refused_in("StandingsStore.swift", "`StandingsStore.")


def test_no_file_touches_memory_unsafely() -> None:
    """The second W2 review's U9 (INV-66, REQ-GAP-001): the client's address rewritten in place through
    `withUnsafeMutablePointer` passed. The client uses no unsafe memory, so all of it is refused."""
    assert _refused_in("Detail.swift", "withUnsafeMutablePointer")


def test_a_url_out_of_any_by_a_cast_is_made() -> None:
    """The second W2 review's U11 and M6 (INV-63, REQ-GAP-001): `value as? URL` makes a URL no call
    returns, so `url_facts` never saw it; nor a `case let u as URL` pattern."""
    cast = ('(source_file "/x/Detail.swift"\n'
            '  (conditional_checked_cast_expr type="URL?" location=/x/Detail.swift:3:5 '
            'range=[/x/Detail.swift:3:5 - line:3:9] value_cast written_type="URL"\n')
    pattern = ('(source_file "/x/Detail.swift"\n'
               '  (pattern_is type="Any" cast_kind=value_cast cast_to="URL"\n')
    assert gate.url_facts(cast) == {"Detail.swift": {"Foundation.URL.made"}}
    assert gate.url_facts(pattern) == {"Detail.swift": {"Foundation.URL.made"}}


def test_the_code_a_sink_runs_is_refused_the_shared_state_the_fixture_holds() -> None:
    """The second W2 review's B2, S5 and S5b (D-180, INV-66, INV-67, REQ-GAP-001): the body of
    `FetchedStandings.init(payload:)`, a call the sinks may make, and a decoding witness it reaches,
    each wrote the screen's global into the standings file, and no rule read them. These shapes of
    what a sink runs are refused; any other form is not held (G-1; see INV-66)."""
    refused = _refused_in("Models.swift", "a privacy sink runs")
    assert any("fixtureStamped" in line for line in refused), refused
    assert any("FixtureNoted" in line for line in refused), refused


def test_foundations_nsarray_sort_is_counted_as_a_sort() -> None:
    """The second W2 review's M4 (REQ-APP-002): `NSArray.sortedArray(comparator:)` was no sort to the
    compiled rule."""
    assert _refused_in("ContentView.swift", "with `sortedArray`")


def test_the_committed_dump_is_the_fixture_as_it_compiles(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The second W2 review's K1: `g2_fixture_ast.txt` is a second copy of the fixture's compile, and
    nothing compared the two where Xcode runs. The self-test now does, and fails when they differ. The
    committed dump stands in for the compile, so this runs where there is no Xcode too."""
    monkeypatch.setattr(gate, "dump_ast", lambda sdk_name, flags, folder=gate.CLIENT: (FLOW_AST, 0))
    assert gate.self_test() == [], "the committed dump is not the fixture as the gate reads it"
    stale = tmp_path / "g2_fixture_ast.txt"
    stale.write_text(FLOW_AST.replace("fixtureStamped", "fixtureStampedLongAgo"), encoding="utf-8")
    monkeypatch.setattr(gate, "SNAPSHOT", stale)
    broken = gate.self_test() or []
    assert any("g2_fixture_ast.txt" in line for line in broken), broken


def test_a_permission_the_client_no_longer_uses_fails_the_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    """M19-W2 Tester (D-181 clause 5; D-180 clause 2's listed calls; the W2 review's R3): "a permission
    the shipping client no longer uses fails the gate, so a ruling cannot outlive its code and a change
    in the compiler's printed layout cannot silence a rule unnoticed". Nothing held it: with
    `unseen_permissions` returning nothing, or `main()` not calling it, every test passed. Here each
    kind of permission is judged on the compiled fixture's own facts (seen where the fixture uses it,
    reported where it does not), and `main()` fails a client that shows none of them.
    # covers REQ-APP-005, REQ-GAP-001, D-180, D-181"""
    missing = gate.unseen_permissions(gate.references(FLOW_AST))
    for seen in ("Combine.swift: position arithmetic", "Combine.swift: `sorted` on `common`",
                 "StandingsStore.swift: a call to `FetchedStandings.init`"):
        assert seen not in missing, ("the fixture uses this permission", seen, missing)
    for unseen in ("Uncertainty.swift: score arithmetic", "Router.swift: price arithmetic in priceInPages",
                   "FrontDoor.swift: `sorted` on `entries`", "EngineClient.swift: a call to `UIText.engineAddress`",
                   "`GapEntry`, which no type decodes"):
        assert unseen in missing, ("the fixture does not use this permission", unseen, missing)

    names = {path.name for path in gate.CLIENT.rglob("*.swift")}
    monkeypatch.setattr(gate, "self_test", lambda: [])
    monkeypatch.setattr(gate, "dump_ast", lambda sdk_name, flags, folder=gate.CLIENT: ("", 0))
    monkeypatch.setattr(gate, "problems", lambda found: [])
    monkeypatch.setattr(gate, "references", lambda ast: {name: set() for name in names})
    assert gate.main() == 1, "a client that uses none of the permissions passed the gate"
    # The control: with no permission granted, the same client passes, so the failure above is theirs.
    for table in ("ARITHMETIC_PERMITTED", "SORTS_PERMITTED", "SINK_CALLS_PERMITTED", "NOT_SERVED"):
        monkeypatch.setattr(gate, table, {})
    assert gate.main() == 0


#: M19-W2 Tester: two routes D-180 clause 2 names for the code a sink runs elsewhere, which no fixture
#: planted: a computed property (here read inside `FetchedStandings.init`, a call the sink may make),
#: and a protocol requirement the sink's own file declares, answered by a conformance in another file.
#: Each body reads the screen's global. The sink calls nothing it may not, so only `_SinkReach` sees them.
SINK_REACH_PROBE = {
    "EngineClient.swift": (
        "import Foundation\n\n"
        "protocol ProbeTagging {\n    func tag() -> String\n}\n\n"
        "struct ProbeClient {\n"
        "    func tagged(_ tagger: any ProbeTagging) -> String { tagger.tag() }\n"
        "    func kept(_ data: Data) -> FetchedStandings? { try? FetchedStandings(payload: data) }\n"
        "}\n"),
    "Models.swift": (
        "import Foundation\n\n"
        "nonisolated(unsafe) var probeNote = \"\"\n\n"
        "struct FetchedStandings {\n    let payload: Data\n\n"
        "    init(payload: Data) throws {\n        self.payload = payload + Data(ProbeHolder.suffix.utf8)\n    }\n}\n"),
    "Detail.swift": (
        "import Foundation\n\n"
        "struct ProbeHolder {\n    static var suffix: String { probeNote }\n}\n\n"
        "struct ProbeTagger: ProbeTagging {\n    func tag() -> String { probeNote }\n}\n"),
}


@pytest.mark.needs("xcode")  # the probe is compiled
def test_the_code_a_sink_runs_is_followed_into_computed_properties_and_protocol_witnesses(tmp_path: Path) -> None:
    """M19-W2 Tester (D-180 clause 2, INV-66): `_SinkReach` follows "the functions, initialisers and
    computed properties it calls ... every member a protocol requirement may dispatch to". Only the
    function route was planted (the fixture's `fixtureStamped`), so with the computed-property or the
    protocol branch of `_SinkReach.reached` removed every test passed. Compiled, as the gate compiles.
    # covers REQ-GAP-001, D-180"""
    for name, source in SINK_REACH_PROBE.items():
        (tmp_path / name).write_text(source, encoding="utf-8")
    _, sdk_name, flags = gate.CONFIGURATIONS[0]
    dumped = gate.dump_ast(sdk_name, flags, tmp_path)
    assert dumped is not None and dumped[1] == 0, dumped and dumped[0][-800:]
    refused = gate.problems(gate.references(dumped[0]))
    runs = [line for line in refused if line.startswith("Detail.swift:") and "code a privacy sink runs" in line]
    assert any("`ProbeHolder.suffix`" in line and "`probeNote`" in line for line in runs), refused
    assert any("`ProbeTagger.tag()`" in line and "`probeNote`" in line for line in runs), refused
    assert len(refused) == 2, ("the probe's sink calls nothing it may not; only the two bodies are refused", refused)


def test_the_fixtures_six_request_shapes_are_refused_and_its_own_request_is_not() -> None:
    """#174, #188 (INV-64's listed forms on the compiled module): the M19 closure seat's S2 line (the
    typed question sent as the budget) and the typed question kept as the surface are refused at their
    call and their assignment, with the review's four round-1 twins; the screen's own request, its
    routed surface and its chosen one are allowed. Other forms are gap G-11."""
    assert _refused_in("ContentView.swift", "the request's `budget` argument")
    assert _refused_in("ContentView.swift", "assigns `ContentView.task`")
    refused = _refused_in("ContentView.swift", "#174, #188")
    # The two lines above, and the M21-W3 review's four twins (B2): six, and the screen's own request,
    # `apply`'s routed surface and `select`'s chosen one are not among them.
    assert len(refused) == 6, refused


def test_a_request_argument_the_gate_does_not_know_is_refused() -> None:
    """#174: a new request parameter is a reviewed change, so an argument not in REQUEST_ARGUMENTS is
    refused whatever it names."""
    assert ("EngineClient.recommendation(task:budget:)", "task") in gate.REQUEST_ARGUMENTS
    assert gate._request_problem("ContentView.swift", "<request argument>.EngineClient.search(text:)|text|a value@9")


def test_a_mac_without_the_toolchain_fails_the_gate_rather_than_skipping(monkeypatch: pytest.MonkeyPatch) -> None:
    """#175 R1: a Mac with Xcode is the gate's authoritative host (`docs/security-invariants.md`, gap
    G-10); a skip there would pass the routes D-180 and D-181 moved onto the compiled module unread. On
    another host the gate still says it skipped."""
    monkeypatch.setattr(gate, "dump_ast", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(gate, "_host", lambda: "Darwin")
    assert gate.main() == 1
    monkeypatch.setattr(gate, "_host", lambda: "Linux")
    assert gate.main() == 0


def test_the_self_test_compiles_the_fixture_in_every_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """#175 R3: the fixture carries a refused shape for each rule `FIXTURE_RULES` names, in each
    configuration the gate reads, so a layout change in any of them fails the self-test. The fixture is compiled once per configuration."""
    seen: list[list[str]] = []

    def dump(_sdk: str, flags: list[str], *_rest: object) -> tuple[str, int]:
        seen.append(list(flags))
        return "", 0

    monkeypatch.setattr(gate, "dump_ast", dump)
    gate.self_test()
    assert [flags for _, _, flags in gate.CONFIGURATIONS] == seen


def test_each_rule_fixture_rules_names_has_a_refused_shape() -> None:
    """#175 R3: each rule `FIXTURE_RULES` names has at least one refusal the fixture must produce, so a
    layout change that silences one of them fails the self-test. Two rules are not named there and have
    no such refusal: the budget's literal `let` and `SINK_SWIFT_REFUSED` (G-10)."""
    phrases = {phrase for _, phrase in gate.FIXTURE_REFUSALS | gate.FIXTURE_RELEASE_REFUSALS}
    assert len(gate.FIXTURE_RULES) >= 8, "the rules are not named"
    for rule, phrase in gate.FIXTURE_RULES.items():
        assert any(phrase in carried for carried in phrases), f"no fixture refusal carries the {rule} rule"


def _marked(mark: str) -> int:
    """The line of `Arithmetic.swift` in the fixture that carries `mark`."""
    lines = (ROOT / "scripts" / "client_decl_fixtures" / "Arithmetic.swift").read_text(encoding="utf-8").splitlines()
    found = [number for number, line in enumerate(lines, start=1) if line.rstrip().endswith(mark)]
    assert len(found) == 1, f"{mark} marks {len(found)} lines"
    return found[0]


@pytest.mark.parametrize(
    "shape",
    ["prefix-minus", "shift", "shift-assign", "operator-as-value", "operator-as-value-map", "pow", "truncating",
     "quotient", "overflow", "custom-operator", "numeric-extension", "subscript", "later-line",
     "decoded-in-extension", "through-any", "through-text", "served-fact", "fact-through-any",
     # The M21-W3 review's B3 and M1.
     "nsstring-parse", "formatter-parse", "scanner-parse", "anyhashable", "anyobject", "nsnumber",
     "json-round-trip", "xor", "bitwise-not", "bitwise-and", "fact-nsnumber", "served-dollar",
     # A count of a list a served number builds (the review's M1 allowance, laundered).
     "count-of-built", "range-count", "drop-count"],
)
def test_each_shape_the_second_review_planted_is_refused(shape: str) -> None:
    """#173 (D-181, G-2): every operator, method and name the second M19-W2 review planted past the
    arithmetic rule is refused at its own line."""
    line = _marked(f"// shape: {shape}")
    refused = [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]
    assert refused, f"{shape} (Arithmetic.swift:{line}) is not refused"


def test_a_count_of_served_things_is_not_arithmetic_on_a_served_number() -> None:
    """#173, the review's M5: `filter { $0.position > 0 }.count + 1` counts things; the walk read the
    closure inside the operand and refused it as `+` on a served position."""
    line = _marked("// allowed: filter-count")
    assert not [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]


def test_a_labels_length_is_not_a_served_number() -> None:
    """#171: following a served number through text must not make a label's length one."""
    line = _marked("// allowed: label-length")
    assert not [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]


def test_every_route_172_names_into_a_sink_is_refused() -> None:
    """#172 (D-180, INV-66, gap G-1): a stored default (the sink's call to another file's initialiser), a
    closure the sink keeps (a sink holds only values), a static `let`'s initialiser reading the screen's
    state, and Foundation's shared state read in a sink: each refused on the fixture."""
    assert _refused_in("EngineClient.swift", "FixtureDefaulted.init")
    assert _refused_in("EngineClient.swift", "holds `make`")
    assert _refused_in("Detail.swift", "`FixtureStatics.tag`, code a privacy sink runs")
    assert _refused_in("EngineClient.swift", "uses `Thread.threadDictionary`")
    assert _refused_in("EngineClient.swift", "uses `NotificationCenter")



# --- The M21-W3 review (docs/reviews/m21-wave-3-review.md) ------------------------------------------------


@pytest.mark.parametrize("mark", ["nearby-row-numbers", "positions-count", "indices-count", "row-numbers",
                                  "keypath-count"])
def test_counts_and_row_numbers_are_not_served_numbers(mark: str) -> None:
    """The review's M1: a count of served numbers, a row number, and a closure's `$0` a few lines below a
    served one are not served numbers; the served `$0` itself still is (`served-dollar`)."""
    line = _marked(f"// allowed: {mark}")
    assert not [found for found in gate.problems(gate.references(FLOW_AST)) if found.startswith(f"Arithmetic.swift:{line}:")]


def test_a_served_fact_is_a_kind_of_its_own_and_d143_permits_only_it() -> None:
    """The review's B3: the three D-143 places restate a served fact's number out of 100; a served count
    or any other number there is arithmetic no ruling names."""
    assert gate._flow_problem("Uncertainty.swift", "<arithmetic>.fact@5 * in scoreOutOf100") is None
    assert gate._flow_problem("Uncertainty.swift", "<arithmetic>.number@5 * in scoreOutOf100") is not None
    assert gate._flow_problem("Uncertainty.swift", "<arithmetic>.number@5 * in anchoredFact") is not None
    assert gate._served_cases(gate._tree(FLOW_AST))[("ShapeValue", "number")] == "fact"


def test_round_one_process_state_and_object_constants_in_a_sink_are_refused() -> None:
    """The review's round-1 B1 (INV-66's listed forms): Foundation's process-wide state in a sink (the
    main thread's and the main queue's names, the process name, the default time zone), and a constant
    or a static another file holds whose declared type is a mutable container class `FOUNDATION_OBJECT`
    lists, are refused where the sink reads them. Behind a widened type it is not held (gap G-1)."""
    for phrase in ("Thread.main", "ProcessInfo.processName", "OperationQueue.main", "NSTimeZone.default"):
        assert _refused_in("EngineClient.swift", phrase), phrase
    assert _refused_in("EngineClient.swift", "reads `fixtureScreenBox`")
    assert _refused_in("EngineClient.swift", "reads `box`")


def test_round_one_twins_of_the_surface_are_refused() -> None:
    """The review's round-1 B2 (INV-64's listed forms): the surface set through the wrapper's storage or
    its binding, from an outcome a helper in another file builds, and the request method held as a
    value: each refused. Round 2's twins are not (gap G-11)."""
    assert _refused_in("ContentView.swift", "ContentView._task")
    assert _refused_in("ContentView.swift", "used as a value")
    assert _refused_in("Detail.swift", "builds RoutingOutcome")
    assert _refused_in("Detail.swift", "extends `RoutingOutcome`")
    assert len(_refused_in("ContentView.swift", "assigns `ContentView.task`")) >= 2


def test_the_mutable_classes_url_initialisers_and_an_expression_by_name_are_refused() -> None:
    """The review's M2 (#168's twins) and K1 (#241)."""
    assert _refused_in("ContentView.swift", "NSMutableArray.init(contentsOf")
    assert _refused_in("ContentView.swift", "NSExpression")


def test_the_fixture_carries_the_five_rules_it_lacked() -> None:
    """The review's M4 (#175 R3): the UIKit and CoreFoundation symbol lists, a path built outside its
    files, a second @AppStorage, and the Release-only hook, each refused on the fixture, and each a rule
    the self-test names."""
    assert _refused_in("Detail.swift", "UIKit.UIPasteboard")
    assert _refused_in("Detail.swift", "CoreFoundation.CFSocketCreate")
    assert _refused_in("Detail.swift", "builds a path")
    assert _refused_in("Detail.swift", "stores something outside the register")
    released = gate.release_problems(gate.references(FLOW_AST))
    assert any(line.startswith("ContentView.swift:") and "Debug-only UI test hook" in line for line in released)
    assert {"the UIKit symbol list", "the CoreFoundation symbol list", "a path built elsewhere",
            "a second @AppStorage", "the Release-only hook"} <= set(gate.FIXTURE_RULES)


def test_the_text_tripwire_names_the_compiled_served_fields_on_the_fixture() -> None:
    """The review's M3 (#169): the text derivation (`_served_numbers`, for the lanes with no Xcode) and the
    compiled gate's `served_fields` name the same fields on the fixture, a served fact's enum payload and
    a field typed as one included; and on the shipping client the text list holds the served facts."""
    from .test_ios_client_contract import _served_numbers, _swift

    compiled = {field for _, field in gate.served_fields(gate._tree(FLOW_AST))}
    fixture = {p.name: _swift(p) for p in (ROOT / "scripts" / "client_decl_fixtures").glob("*.swift")}
    text = _served_numbers(fixture)
    assert text == compiled, (sorted(compiled - text), sorted(text - compiled))
    assert {"whyFact", "tradeOffFact", "number", "number(_:)"} <= _served_numbers()


def test_reflection_and_the_runtime_by_name_are_refused() -> None:
    """Past the review's K1 (#241): `Mirror` reads any stored field by name, past the served-field flow
    (G-2); the ObjectiveC runtime's associated objects carry the reader's words from the screen to code
    a sink runs (G-1); and the runtime's class, method and selector functions reach code by name. The
    client uses none of them, so each is refused outright."""
    assert _refused_in("Arithmetic.swift", "Mirror")
    assert _refused_in("ContentView.swift", "objc_setAssociatedObject")
    assert _refused_in("Detail.swift", "objc_getAssociatedObject")
    for symbol in ("NSClassFromString(_:", "NSSelectorFromString(_:", "class_getInstanceMethod(_:_:",
                   "method_exchangeImplementations(_:_:", "Mirror.init(reflecting:"):
        problem = gate._capability_problem("ContentView.swift", symbol, symbol)
        assert problem is not None and "by name" in problem, (symbol, problem)


# --- The M21-W3 Tester (docs/reviews/m21-wave-3-tester.md) ------------------------------------------------


def test_the_self_test_requires_the_release_rule_in_each_release_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """The M21-W3 Tester (the review's M4, G-10: "the Release configurations run their own rule on it"): with
    the self-test's Release branch removed whole, its call and its expectation, every test and the self-test
    passed, since nothing else asks for the Release-only hook's refusal. Here the rule is silenced, and the
    self-test must say so in the two Release configurations and in no other. The committed dump stands in for
    the compile, so this runs where there is no Xcode too. # covers REQ-GAP-001"""
    monkeypatch.setattr(gate, "dump_ast", lambda sdk_name, flags, folder=gate.CLIENT: (FLOW_AST, 0))
    assert gate.self_test() == []
    monkeypatch.setattr(gate, "release_problems", lambda found: [])
    broken = gate.self_test() or []
    missed = sorted(line.split(")")[0] + ")" for line in broken if "Debug-only UI test hook was not refused" in line)
    assert missed == ["(device, release)", "(simulator, release)"], broken


def test_a_mac_without_the_toolchain_fails_by_the_name_its_platform_gives(monkeypatch: pytest.MonkeyPatch) -> None:
    """The M21-W3 Tester (#175 R1, G-10): the test above replaces `_host` itself, so a `_host` that misnames
    the Mac (`platform.system().lower()`, which is "darwin") skipped the gate on the owner's Mac with every
    test green. Here only the platform's own answer is replaced. # covers REQ-GAP-001"""
    monkeypatch.setattr(gate, "dump_ast", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(gate.platform, "system", lambda: "Darwin")
    assert gate.main() == 1, "the gate skipped on a Mac without its toolchain"
    monkeypatch.setattr(gate.platform, "system", lambda: "Linux")
    assert gate.main() == 0


def test_a_sink_is_refused_the_command_lines_two_members() -> None:
    """The M21-W3 Tester (D-180, the review's B1): `SINK_SWIFT_REFUSED` has no shape in the fixture (G-10), so
    with it emptied every test passed. `CommandLine`'s arguments are process-wide state; a privacy sink reads
    none, and a file that is no sink is not refused for them. # covers REQ-GAP-001"""
    for sink in gate.SINK_FILES:
        for symbol in ("CommandLine.arguments", "CommandLine.unsafeArgv"):
            assert gate.problems({sink: {f"Swift.{symbol}"}}), (sink, symbol)
    assert gate._sink_module_problem("ContentView.swift", "Swift", "CommandLine.arguments") is None


def test_make_client_decls_runs_the_gate_and_keeps_its_status() -> None:
    """The M21-W3 Tester (#175 R1, G-10): `main()` fails on a Mac without its toolchain, and `make
    client-decls` is how `make check-fast` and `make check` reach it. With the recipe's line made
    `-$(PY) ...`, make printed "Error 1 (ignored)" and passed, and every test stayed green. The recipe runs
    the gate and nothing that could drop its status. # covers REQ-GAP-001"""
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith("client-decls:"))
    recipe: list[str] = []
    for line in lines[start + 1:]:
        if not line.startswith("\t"):
            break
        recipe.append(line.strip())
    assert [line for line in recipe if not line.startswith("@#")] == ["$(PY) -B scripts/client_decl_gate.py"], recipe
