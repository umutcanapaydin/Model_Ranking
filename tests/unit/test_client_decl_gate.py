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
    while it has stopped refusing (#51). Nothing held that: with the call unwired, every test here and
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
    A sink file's mutable stored state, and its reads of any other file's, are refused."""
    refused = gate.problems(gate.references(SINK_AST))
    assert any(line.startswith("EngineClient.swift:") and "`tag`" in line and "mutable stored state" in line
               for line in refused), refused
    assert any(line.startswith("EngineClient.swift:") and "`screenRelay`" in line
               and "mutable state declared in ContentView.swift" in line for line in refused), refused


def test_standings_built_outside_the_two_sinks_are_refused() -> None:
    """#85 (D-180 clause 2): P3 made the typed question into `FetchedStandings` on the screen and saved
    it into the device's caches. Only the engine's answer and the store's own file build standings."""
    refused = gate.problems(gate.references(SINK_AST))
    assert any(line.startswith("ContentView.swift:") and "builds FetchedStandings" in line for line in refused), refused


def test_what_the_sinks_may_hold_and_others_may_read_passes() -> None:
    """#85 (D-180): a `let`, a computed property and a function's local are not shared state; a file
    that is not a sink may read a global; the standings initialiser's own parameter is not a call."""
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
    tripwire, which matches the words around the operator. The compiler follows the value."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("ContentView.swift:") and "served position" in line for line in refused), refused


def test_a_second_sort_under_a_permitted_name_is_refused() -> None:
    """#60 (the M17-W4 Tester's M7): a second `common.sorted()` in `Combine.swift` passed, because the
    permission was keyed by the receiver's name. Each permitted sort is counted."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("Combine.swift:") and "sorts `common`" in line for line in refused), refused
    once = gate.problems(gate.references(_without(FLOW_AST, "fixtureCombinesTwice(_:)")))
    assert not [line for line in once if "sorts `common`" in line], once


def test_permitted_arithmetic_passes_where_its_ruling_names_the_file() -> None:
    """#60: D-167 lets `Combine.swift` rank positions; the gate refuses nothing there for it."""
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
    the two stores, whatever it is called; reading a URL that exists is not making one."""
    refused = gate.problems(gate.references(MADE_URL_AST))
    assert any(line.startswith("ContentView.swift:") and "makes a URL" in line for line in refused), refused
    assert not [line for line in refused if line.startswith("EngineClient.swift:")], refused
    assert len([line for line in refused if "makes a URL" in line]) == 1, refused


def test_a_link_detector_is_the_network() -> None:
    """#107: `NSDataDetector` with the `.link` type finds URLs in text, so it is the network's first
    step, as a URL made from a string is."""
    refused = gate.problems({"ContentView.swift": {"Foundation.NSDataDetector"}})
    assert any("NSDataDetector" in line and "network" in line for line in refused), refused


def test_turning_cookies_off_is_the_one_cookie_symbol_allowed_and_only_in_the_door() -> None:
    """#144: the session sets `HTTPCookie.AcceptPolicy.never`, a member of a family the gate refuses
    (cookies go to a store the system writes). That one value is allowed in the network door only."""
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
    which matched `URL`, `URL?` and `[URL]` only, never saw."""
    refused = gate.problems(gate.references(CLIENT_AST))
    assert any(line.startswith("Detail.swift:") and "makes a URL" in line for line in refused), refused


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
])
def test_arithmetic_on_a_served_number_is_refused_whatever_carries_it(file: str, declaration: str) -> None:
    """The W2 review's B1 (D-181, INV-76, REQ-APP-005): the review got arithmetic on a served number past
    the gate through each of these. Each is refused, on a line of its own declaration."""
    span = _lines_of(file, declaration)
    refused = gate.problems(gate.references(FLOW_AST))
    hits = [line for line in refused if line.startswith(f"{file}:") and "served" in line
            and int(line.split(":")[1]) in span]
    assert hits, (declaration, [line for line in refused if line.startswith(f"{file}:")])


def test_foundations_sort_is_counted_as_a_sort() -> None:
    """The W2 review's M4: `sorted(using:)` (Foundation) passed the compiled sort rule, which read the
    standard library's sorts only."""
    refused = gate.problems(gate.references(FLOW_AST))
    assert any(line.startswith("ContentView.swift:") and "sorts `standings`" in line for line in refused), refused


def test_the_price_in_pages_is_permitted_where_it_is_computed() -> None:
    """The W2 review's M5: the price permission is `priceInPages`'s, not the whole file's."""
    refused = gate.problems(gate.references(FLOW_AST))
    span = _lines_of("Router.swift", "func priceInPages")
    assert not [line for line in refused if line.startswith("Router.swift:") and int(line.split(":")[1]) in span], refused
