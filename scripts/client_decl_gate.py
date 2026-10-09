"""D-126 checked against what the COMPILER resolves, not against how the source spells it (W-122).

Six rounds of a word list over `ios/ModelRanking` each closed the spellings somebody had thought
of, and each independent seat found more: backticks (`` `URL`(string:) ``), a comment between two
tokens (`URL/**/(`), a `typealias`, `NSMutableURLRequest`, a markdown link, Handoff. A gate over
text cannot see through any of those, because the text is not what compiles.

This gate type-checks the client with the iOS SDK and reads the DECLARATIONS the compiler bound
each reference to. `` `URL`(string:) ``, `Address(string:)` after a typealias and `URL(string:)`
all resolve to `Foundation.(file).URL.init(string:)`, so all three are one entry here.

**Two rules, in this order.**

1. **Module allowlist.** A client file may reference declarations only from the modules below, plus
   the app's own. `Network`, `WebKit`, `CloudKit`, `Photos`, `Contacts` and everything else are
   refused by absence, so an API nobody has thought of yet is refused too. `UIKit` and
   `CoreFoundation` are allowlisted SYMBOL by symbol: both arrive through a re-export, and
   `CoreFoundation` whole carries sockets.
2. **Capability rules inside the allowed modules.** Foundation and SwiftUI carry the ways text
   leaves a phone, so those are named: the network is EngineClient's alone, the file system is the
   gap register's alone, and sharing, hand-off, shared storage and logging belong to nobody.

The text gate in `tests/unit/test_router_hints.py` stays: it runs in every lane, including the ones
with no Xcode, and this one runs where the toolchain is. Neither is the whole check.

**What this gate does NOT do** (M16-W1 review, measured):

- It scopes by FILE, not by data, with two exceptions. A function declared in `EngineClient.swift`
  resolves in `main`, and `main` is not capability-checked, so a relay there that any file can call
  passes (B19); the file system is whole inside `FrontDoor.swift`, so a write to the temporary
  directory from there passes too (B31). What a file does with a capability it owns is for review
  and the tests. The first exception is the two privacy sinks (#85, D-180): neither holds anything
  but a value of a listed type, reads mutable state another file can set, or calls what another file
  declares unless it is listed, and the code a sink runs elsewhere reads no shared mutable state
  (`_SinkReach`); only they build standings, only `EngineClient.swift` builds a client on an address
  of its own and only the store's file builds or saves to a store, a kept type is extended and
  conformed nowhere else, and no file touches memory unsafely (`SINK_FILES`, `SINK_HELD_TYPES`,
  `SINK_CALLS_PERMITTED`, `PROVENANCE`, `KEPT_TYPES`, `UNSAFE`). These are the routes D-180 names, not
  a proof that no other route exists (G-1, #172). The second is a served number (#60, D-181): the
  operators, methods and names it lists are followed (`_Flow`), others are not (#173), and nor is a
  number through `Any` or text; the served facts reach the phone through `Any` (G-2, #171).
- It does not see arguments, and some of the check lives in the text gate for that reason:
  `Text("[report](https://…)")` is a `LocalizedStringKey` literal, not an `AttributedString`, so a
  markdown link written as a literal passes here and dies there (B10); a key built at run time is
  refused here instead. `try!` on an error that carries the reader's words puts them in the crash
  report, and has no declaration for either gate to refuse (re-review, X06).
- `.textSelection(.enabled)` is allowed: the detail screen uses it on model facts, and what it
  hands the pasteboard is what the reader chose to copy (B22).
- One known false positive: `URL.appending…` is file-scoped, so building a path to a bundle
  resource outside the two owning files fails (FP3). `Bundle.main.url(forResource:withExtension:)`
  makes a URL, so since #107 it fails there too (`URL.made`).
"""

from __future__ import annotations

import pathlib
import platform
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLIENT = ROOT / "ios" / "ModelRanking"
#: Every configuration the app ships in. One was not enough: the M16-W1 seat put a `URLSession`
#: exfiltration inside `#if !targetEnvironment(simulator)` and inside `#if DEBUG`, and a gate that
#: type-checks the simulator Release build never saw either branch. Each configuration is dumped
#: and every one must be clean.
CONFIGURATIONS = (
    ("simulator, release", "iphonesimulator", ["-target", "arm64-apple-ios18.0-simulator"]),
    ("simulator, debug", "iphonesimulator",
     ["-target", "arm64-apple-ios18.0-simulator", "-D", "DEBUG"]),
    ("device, release", "iphoneos", ["-target", "arm64-apple-ios18.0"]),
    ("device, debug", "iphoneos", ["-target", "arm64-apple-ios18.0", "-D", "DEBUG"]),
)

#: Modules a client file may resolve a declaration in. `main` is the app's own module.
MODULES = {
    "main",
    "Swift",
    "SwiftUI",
    "SwiftUICore",
    "Foundation",
    "NaturalLanguage",
    "FoundationModels",
    "_Concurrency",
    "ObjectiveC",
    "Observation",
    "Combine",
    "_DarwinFoundation1",  # `pow`, through Foundation's re-export
}
# `Darwin` is NOT here, deliberately (M16-W1 review, B-3): it carries BSD sockets, `getaddrinfo`
# and `dlopen`, so allowlisting the module handed every client file its own way onto the network.
# Measured on the shipping client: the only declaration it resolves in that family is
# `_DarwinFoundation1.pow`, so the removal costs nothing.

#: UIKit arrives through SwiftUI's re-export, so it is allowed one symbol at a time: these are the
#: colour and trait types the design layer reads. `UIPasteboard`, `UIApplication`,
#: `UIActivityViewController`, `UIPrintInteractionController` and `UIDocumentPickerViewController`
#: are all UIKit, and all refused by not being here.
UIKIT_ALLOWED = {"UIColor", "UITraitCollection", "UIUserInterfaceStyle", "UIFont", "UIScreen"}

#: CoreFoundation is allowed the same way, and for B-3's reason: allowlisted whole it handed every
#: client file a TCP socket (`CFSocketCreate` / `CFSocketConnectToAddress` / `CFSocketSendData`,
#: measured delivering the typed text to a listener), Darwin notifications and `CFShow` (M16-W1
#: re-review, R-B1, B11, X14). The shipping client resolves nothing there but `CGFloat`.
COREFOUNDATION_ALLOWED = {"CGFloat"}

#: Declarations that reach the network, or build an address that could. A `URL` MADE FROM A STRING
#: is the network's first step; a `URL` that names a file on this device is the file system's, and
#: the two are told apart here by which initialiser the compiler chose.
NETWORK = ("URLSession", "URLRequest", "URLComponents", "URLQueryItem", "NSURL", "CFURL",
           "NSMutableURLRequest", "NSURLRequest", "NSURLSession", "NSURLConnection",
           "URL.init(string", "URL.init(dataRepresentation", "URL.lines", "URL.resourceBytes",
           # A socket pair to a host. It lived under `Stream` in the file-system list, which gave
           # it to the register's file (M16-W1 re-review, X02).
           "Stream.getStreamsToHost",
           # #58: a URL made by DECODING is neither a spelling nor an initialiser; `references`
           # records it under this name, from the decode's own type substitution.
           "URL.decoded",
           # #107: a link detector finds URLs in text; and any CALL whose result is a URL, whatever
           # it is called (`URL(_:strategy:)`, a decode wrapper in another file), is recorded under
           # `URL.made` by `url_facts`.
           "NSDataDetector", "NSTextCheckingResult.url", "URL.made",
           # #168: initialisers that load a URL, an https one included. The text gate's `contentsOf:`
           # refuses their spelling; these refuse what the compiler binds.
           "String.init(contentsOf", "NSString.init(contentsOf", "NSData.init(contentsOf",
           "NSArray.init(contentsOf", "NSDictionary.init(contentsOf", "XMLParser.init(contentsOf",
           "NSAttributedString.init(url", "NSAttributedString.init(contentsOf")
NETWORK_FILE = "EngineClient.swift"

#: Declarations that touch the file system, including the local-file half of `URL`. Only the files in
#: `FILESYSTEM_FILES` may name them: the two things this app writes.
FILESYSTEM = ("FileManager", "FileHandle", "Data.init(contentsOf", "Data.write", "String.write",
              "StringProtocol.write(toFile", "String.write(toFile", "write(to:",
              "URL.init(fileURLWithPath", "URL.init(filePath",
              "URL.deleting", "URL.setResourceValues", "URL.resourceValues", "URLResourceValues",
              # The Objective-C twins and the stream APIs write a file just as well, and the first
              # version of this list named only the Swift spellings (M16-W1 review, B04/B05/B28).
              "NSString.write", "NSData.write", "NSArray.write", "NSDictionary.write",
              "OutputStream", "InputStream.init(fileAtPath", "InputStream.init(url",
              "NSTemporaryDirectory", "StringProtocol.write(to", "FileWrapper",
              "URL.init(fileURLWithFileSystemRepresentation")
#: Each file allowed the file system, with what it keeps and the ruling that allows it. The gap
#: register (REQ-GAP-001) and, since M17-W4, the standings the engine sent (D-167 clause 4).
FILESYSTEM_FILES = {
    "FrontDoor.swift": "the gap register (REQ-GAP-001)",
    "StandingsStore.swift": "the standings the engine sent (D-167)",
}

#: Appending a path component builds a route inside a URL that already exists, so it belongs to
#: whoever owns that URL: the register's folder in one file, the engine's request path in the other.
#: It cannot turn a local URL into a remote one, which is what the two lists above are about.
PATH_BUILDING = ("URL.appending",)

#: Declarations that carry text off the device or into storage nothing else can see, whoever names
#: them. Matched as a prefix of the symbol path inside its module.
FORBIDDEN = (
    "UserDefaults",
    "NetService",
    # A markdown link renders as a tappable link, so the reader's words leave through the browser
    # with no URL type anywhere in the source (M15-W4 re-review, BLOCKING-1).
    "AttributedString",
    "View.draggable",
    "View.userActivity",
    "View.fileExporter",
    "View.fileMover",
    "View.onDrag",
    "View.shareable",
    "View.exportsItemProviders",
    "View.dropDestination",
    "NSUbiquitousKeyValueStore",
    "NSUserActivity",
    "UIActivityViewController",
    "UIPasteboard",
    "UIApplication",
    "UIPrintInteractionController",
    "UIDocumentPickerViewController",
    "ShareLink",
    "AsyncImage",
    "Link",
    "OpenURLAction",
    "EnvironmentValues.openURL",
    # State restoration writes a scene's storage to disk, so `@SceneStorage` holding what a reader
    # typed is a second store beside the register (M16-W1 review, B23). The client uses none.
    "SceneStorage",
    # An App Group container is shared with other apps and extensions, so not even the register
    # may write there (B08).
    "FileManager.containerURL",
    # iCloud Drive (M16-W1 re-review, X09).
    "FileManager.url(forUbiquityContainerIdentifier",
    # A markdown link built at RUN time: the literal form is checked by the text gate, but a key
    # made from a runtime string is not a literal, and neither gate saw it (re-review, R-M1). The
    # client builds its keys only by interpolation.
    "LocalizedStringKey.init(_:",
    "LocalizedStringKey.init(stringLiteral",
    # Credentials with `.synchronizable` go to iCloud Keychain, and cookies to a store the system
    # writes to disk; refused for the reason `SecItemAdd` and `UserDefaults` are (re-review, R-M2).
    "URLCredentialStorage",
    "URLCredential",
    "URLProtectionSpace",
    "HTTPCookieStorage",
    "HTTPCookie",
    # A crash message lands in the crash report, which leaves the phone. This gate sees the call,
    # not the argument, so it cannot tell `fatalError("\(typed)")` (B09) from a constant one; the
    # client calls none of these, so all of them are refused. The text gate also refuses
    # interpolation into them (W-121).
    "fatalError",
    "precondition",
    "assert",
    "NSException",
    "print",
    "debugPrint",
    "dump",
    "NSLog",
    "Logger",
    "OSLog",
    "SecItemAdd",
    "CFPreferences",
    "NSKeyedArchiver",
)

#: #85 (D-180): the two privacy sinks. Each sends or keeps only what its parameters, its immutable
#: configuration and the engine's answer give it, so nothing derived from the question can reach
#: them through state another file sets. The file scope above cannot see that (the M17 closure's P2).
SINK_FILES = {
    "EngineClient.swift": "every request to the engine, the boards request among them (INV-66)",
    "StandingsStore.swift": "the standings file on this device (INV-66)",
}
#: Declarations only the listed files may call, each with why. Standings come from the engine's answer
#: or the store's own file, never from what the screen builds (the M17 closure's P3); a client on an
#: address, and an address made from text, come from the engine client alone, or a file could point the
#: requests wherever the question says (the W2 review's B2).
PROVENANCE: dict[str, tuple[set[str], str]] = {
    "FetchedStandings.init(payload:)": (
        {"EngineClient.swift", "StandingsStore.swift"},
        "only the engine's answer and the store's own file become standings"),
    "EngineClient.init(baseURL:session:)": (
        {"EngineClient.swift"},
        "only the engine client builds a client on an address; the app builds `EngineClient()`"),
    "EngineClient.engineURL(from:)": (
        {"EngineClient.swift"},
        "only the engine client makes its address from text, the build's own setting"),
    # The second W2 review's U10 and P3w: a store on a path made from the question, and standings
    # saved from another file. The app reaches the store through `onDevice.currentKept` only.
    "StandingsStore.init(url:)": (
        {"StandingsStore.swift"},
        "only the store's own file builds a store, on the one place it keeps standings"),
    "StandingsStore.save(_:at:)": (
        {"StandingsStore.swift"},
        "only the store's own file saves standings, the ones it fetched"),
    # #170: a date is a 64-bit channel into the standings file, so only the store's own file dates
    # what it keeps; the app calls `currentKept(fetch:)`, which reads the store's clock.
    "StandingsStore.currentKept(now:fetch:)": (
        {"StandingsStore.swift"},
        "only the store's own file dates the standings it keeps, by its own clock"),
    "StandingsStore.current(now:fetch:)": (
        {"StandingsStore.swift"},
        "only the store's own file dates the standings it keeps, by its own clock"),
}
#: The second W2 review's B1: the types `PROVENANCE` guards. A protocol requirement their initialiser
#: satisfies is another name for it, and an initialiser added in an extension is another initialiser,
#: so each is extended only in the file that declares it, and conforms to no protocol the app declares.
KEPT_TYPES = {symbol.split(".")[0] for symbol in PROVENANCE}

#: #174, #188 (INV-64 on the compiled module): what each argument of a request the engine client
#: sends may name. Outside the engine client, an argument names exactly its declaration here, or is a
#: literal; any other value, whatever the screen built it from, is refused at the call. An argument
#: of a request method not listed here is refused too, so a new parameter is a reviewed change.
REQUEST_ARGUMENTS: dict[tuple[str, str], str] = {
    ("EngineClient.recommendation(task:budget:)", "task"): "ContentView.task",
    ("EngineClient.recommendation(task:budget:)", "budget"): "ContentView.budget",
}
#: What each of those declarations may hold. `None`: a `let` given a literal. Otherwise the one
#: expression each assignment to it may be: a routed outcome's surface, or the surface `select(_:)`
#: was given (the screen's sheet and alternatives offer only the engine's own list, and `select`
#: refuses anything else). The surface itself leaves the phone by design (D-168 note 9, D-126).
REQUEST_SOURCES: dict[str, set[str] | None] = {
    "ContentView.budget": None,
    "ContentView.task": {"RoutingOutcome.categoryID", "ContentView.select(_:).id"},
}

#: The second W2 review's U9: memory touched unsafely can rewrite any value, a sink's own included,
#: whatever the rules above say. The client uses none, so a symbol any part of whose path starts so is
#: refused everywhere.
UNSAFE = ("Unsafe", "withUnsafe", "unsafe", "Unmanaged", "OpaquePointer", "withMemoryRebound",
          "assumingMemoryBound", "bindMemory")

#: The W2 review's M1 (D-180 clause 2): what a sink may hold at a type's or the file's scope, by its
#: compiled type. A value is copied, so no other file can change the sink's; `URLSession` is built in
#: `EngineClient.init(baseURL:session:)`, which only `EngineClient.swift` calls (`PROVENANCE`). Any
#: other type, a `let` of `NSMutableString` or a `@TaskLocal`'s storage among them, is refused.
SINK_HELD_TYPES = {"String", "Int", "Double", "Bool", "TimeInterval", "Date", "Data", "URL", "Standings",
                   "URLSession"}
#: The W2 review's M1: what a sink may call that another file declares, each with its reason. A body
#: another file owns can read the screen's state, so any other call is refused.
SINK_CALLS_PERMITTED = {
    ("EngineClient.swift", "UIText.engineAddress"): "the failure line naming the address, made from its two arguments",
    ("EngineClient.swift", "FetchedStandings.init"): "PROVENANCE: the engine's answer becomes standings",
    ("StandingsStore.swift", "FetchedStandings.init"): "PROVENANCE: the store's own file becomes standings",
}

#: #60 (G-2), D-181 as the W2 review's B1 widened it: a served number is any numeric value a type the
#: client decodes (`Decodable` or `Codable`) stores, found on the compiled module, never typed out by
#: hand. Arithmetic on one, however it travels (see `_Flow`), is a second scoring implementation
#: unless a ruling names the place (REQ-APP-005). These fields have a kind a ruling can name; any
#: other served number is a "served number", which no ruling names.
FIELD_KINDS = {
    "score": "score", "secondaryScore": "score", "higherEffortScore": "score",
    "position": "position",
    "blendedPerM": "price", "inputPerM": "price", "outputPerM": "price",
    "minQuality": "score", "behindBy": "score", "closeCallMargin": "margin", "scoreAnchor": "anchor",
}
#: (file, kind, the function it is in, or None for the whole file) -> the ruling that permits it.
ARITHMETIC_PERMITTED: dict[tuple[str, str, str | None], str] = {
    ("Uncertainty.swift", "score", None): "D-138: a rank range compares served scores against the engine's margin",
    ("Uncertainty.swift", "margin", None): "D-138: the engine's margin, against which a rank range compares scores",
    ("Uncertainty.swift", "anchor", "scoreOutOf100"): "D-143: the Elo expectation against the served anchor",
    ("Combine.swift", "position", None): "D-167: the combination ranks served positions",
    ("Router.swift", "price", "priceInPages"): "REQ-CMP-002: the price in pages, beside the exact figure",
    ("Language.swift", "price", "priceInPages"): "REQ-CMP-002: the price in pages, in its Turkish sentence",
    ("Uncertainty.swift", "anchor", "distanceOutOf100"): "D-143: a distance from the leader, out of 100",
    ("Uncertainty.swift", "anchor", "anchoredFact"): "D-143: a pick's fact restated out of 100 (review M-1)",
    # #171: a served fact's number (`JSONValue.number`, read through `Any`) is a served number since
    # M21-W3, and these are the places D-143 restates one out of 100: the same three functions.
    ("Uncertainty.swift", "number", "anchoredFact"): "D-143: a pick's fact restated out of 100 (#171)",
    ("Uncertainty.swift", "number", "distanceOutOf100"): "D-143: a fact's distance from the leader, out of 100 (#171)",
    ("Uncertainty.swift", "number", "scoreOutOf100"): "D-143: a fact's score against the served anchor (#171)",
}
#: A type the client decodes that the engine never sends: the phone's own record, kept on the phone.
#: Every other decoded type is served, so a new one counts until it is named here, with its reason.
NOT_SERVED = {
    "GapEntry": "REQ-GAP-001: the phone's own count of a question it could not answer, saved on the phone",
}
#: (file, call, the receiver the compiler resolved) -> how many such sorts the file may make (Ruling
#: A, REQ-APP-002). Counted, so a second sort under a permitted name fails (the M17-W4 Tester's M7).
SORTS_PERMITTED = {
    ("Combine.swift", "sorted", "common"): 1,
    ("Combine.swift", "sorted", "placed"): 1,
    # D-188 clause 3 (M20-W2): a family's models ordered by their mean percentile positions.
    ("Combine.swift", "sorted", "means"): 1,
    ("FrontDoor.swift", "sorted", "entries"): 1,
    ("FrontDoor.swift", "min", "entries"): 1,
    ("Notices.swift", "sorted", "ages"): 1,
    ("Notices.swift", "sorted", "distinct"): 1,
    ("Reading.swift", "reversed", "row"): 1,
}

#: (file, symbol) a forbidden family's member is allowed as, each with its reason. Exact, never a
#: prefix: the family stays refused everywhere else.
FORBIDDEN_EXCEPT = {
    ("EngineClient.swift", "HTTPCookie.AcceptPolicy.never"): "#144: the session refuses every cookie",
}

#: `@AppStorage("language")` is the one piece of app storage the client keeps, and it holds a
#: `Language`, never text a reader typed. The text gate pins its declaration; here the SwiftUI
#: property wrapper itself is allowed only in the file that declares it.
APPSTORAGE_FILE = "ContentView.swift"

#: `decl="Module.(file).Symbol"`. A member declared in an extension prints as
#: `Module.(file).Type extension.member`, with a SPACE, which hid `.draggable` and
#: `String.write(toFile:)` from the first version of this gate: the space ended the match.
DECL = re.compile(r'decl="?([A-Za-z_][\w]*)\.\(file\)\.((?:[\w.]+ extension\.)?[^ )"@]*)')
IMPORT = re.compile(r'\(import_decl[^)]*module="([^"]+)"')
#: #58: a `decode` whose generic substitution produces a `URL` (`JSONDecoder.decode([URL].self, ...)`,
#: or a container's `decode(URL.self, forKey:)` inside a synthesised `Decodable`). The substitution
#: is printed after the declaration's path, which `DECL` stops before.
DECODES_URL = re.compile(r'decl="[^"]*\.decode(?:IfPresent)?\([^"]*\[with \(substitution_map[^"]*->[^"]*\bURL\b')
#: The fixture `self_test` compiles: files the gate must refuse and files it must allow (#51).
FIXTURES = ROOT / "scripts" / "client_decl_fixtures"
#: The fixture's dump as committed, which the flow tests read where there is no Xcode. The self-test
#: compares it with the fixture's compile (the second W2 review's K1); `--snapshot` writes it again.
SNAPSHOT = ROOT / "tests" / "unit" / "data" / "g2_fixture_ast.txt"
#: What the fixture must produce, as (file, a phrase the refusal carries).
FIXTURE_REFUSALS = {
    ("ContentView.swift", "URLSession"), ("ContentView.swift", "URL.decoded"),
    ("Detail.swift", "FileManager"), ("Detail.swift", "URL.decoded"),
    # #85 (D-180): the M17 relay through shared state, both halves, and P3's standings.
    ("EngineClient.swift", "mutable stored state"),
    ("EngineClient.swift", "mutable state declared in ContentView.swift"),
    ("ContentView.swift", "builds FetchedStandings"),
    # #60 (G-2): arithmetic on a served position through another name, and a second sort under a
    # permitted receiver's name.
    ("ContentView.swift", "served position"),
    ("Combine.swift", "sorts `common`"),
    # #107: a URL made by the parse strategy, by a decode wrapper and by a link detector.
    ("ContentView.swift", "makes a URL"),
    ("ContentView.swift", "NSDataDetector"), ("ContentView.swift", "NSTextCheckingResult.url"),
    # The W2 review's B2: a client built on an address of a file's own, the address made from text,
    # and a URL hidden in a dictionary.
    ("Detail.swift", "makes a URL"), ("Detail.swift", "EngineClient.init(baseURL:session:)"),
    ("StandingsStore.swift", "EngineClient.init(baseURL:session:)"),
    ("StandingsStore.swift", "EngineClient.engineURL(from:)"),
    # The W2 review's B1, M4 and M5: arithmetic through every shape it named, Foundation's sort, and a
    # price arithmetic outside `priceInPages`.
    ("ContentView.swift", "served number"), ("ContentView.swift", "sorts `standings`"),
    ("Router.swift", "served price"),
    # The W2 review's M1: a sink holding a mutable object as a constant, and calling a function
    # another file declares.
    ("EngineClient.swift", "holds `relay`"), ("EngineClient.swift", "calls `fixtureRelayed`"),
    # The second W2 review's B1 and B2: standings built through a protocol requirement, a store built
    # and saved to outside its file, memory rewritten, and the code a sink runs reading the screen's
    # global (through a call, and through a decoding witness). M4: an `NSArray` sort.
    ("Detail.swift", "conforms to `FixtureMadeFromBytes`"), ("Detail.swift", "extends `FetchedStandings`"),
    ("Detail.swift", "StandingsStore.init(url:)"), ("Detail.swift", "StandingsStore.save(_:at:)"),
    ("Detail.swift", "withUnsafeMutablePointer"),
    ("Models.swift", "a privacy sink runs"),
    ("ContentView.swift", "with `sortedArray`"),
    # #170: a date of another file's choosing into the standings file.
    ("Detail.swift", "StandingsStore.currentKept(now:fetch:)"),
    # #174, #188: the reader's text as a request's budget, and kept as the surface it sends.
    ("ContentView.swift", "the request's `budget` argument"), ("ContentView.swift", "assigns `ContentView.task`"),
    # #173: arithmetic on a served number by every shape the second M19-W2 review planted.
    ("Arithmetic.swift", "on a served"), ("Arithmetic.swift", "declares the operator `+`"),
    ("Arithmetic.swift", "extends `Int`"),
    # #172: a default value, a static initialiser and a kept closure the sink runs, and Foundation's
    # shared state a sink reads.
    ("EngineClient.swift", "FixtureDefaulted.init"), ("Detail.swift", "FixtureStatics.tag"),
    ("EngineClient.swift", "holds `make`"), ("EngineClient.swift", "threadDictionary"),
    ("EngineClient.swift", "NotificationCenter"),
    # #175 R3: a framework off the allowlist, and text into shared storage (FORBIDDEN).
    ("Imports.swift", "imports `Network`"), ("ContentView.swift", "UserDefaults"),
    # #168: a URL loaded as text, as NSData and by an XML parser is the network too.
    ("ContentView.swift", "String.init(contentsOf"), ("ContentView.swift", "NSData.init(contentsOf"),
    ("ContentView.swift", "XMLParser.init(contentsOf"),
}
#: #175 R3: each rule the gate applies, by a phrase a refusal of it carries. Every rule has at least one
#: refusal the fixture must produce in every configuration, so a change in the compiler's printed
#: layout that silences one rule fails the self-test, wherever the gate runs.
FIXTURE_RULES: dict[str, str] = {
    "the module allowlist": "imports `Network`",
    "the network door": "URLSession",
    "a URL decoded from text": "URL.decoded",
    "a URL made from text": "makes a URL",
    "the file system": "FileManager",
    "text off the device (FORBIDDEN)": "UserDefaults",
    "unsafe memory": "withUnsafeMutablePointer",
    "a sink's own shared state": "mutable stored state",
    "a sink reading another file's state": "mutable state declared in",
    "a sink holding a reference": "holds `relay`",
    "a sink calling another file": "calls `fixtureRelayed`",
    "the code a sink runs": "a privacy sink runs",
    "provenance": "StandingsStore.save(_:at:)",
    "a kept type extended": "extends `FetchedStandings`",
    "arithmetic on a served number": "served number",
    "a sort past its count": "sorts `standings`",
    "a request's arguments": "the request's `budget` argument",
}
SOURCE = re.compile(r'^\(source_file "([^"]+)"', re.MULTILINE)
#: One node of the dump: its indentation (the tree's depth) and its kind.
NODE = re.compile(r"^( *)\((\w+)")
VAR_NAME = re.compile(r'^ *\(var_decl [^"]*"([^"]+)"')
RANGE_START = re.compile(r"range=\[([^\]:]+):(\d+):(\d+)")
#: A reference into the app's own module, with the place its declaration starts.
MAIN_REF = re.compile(r'decl="main\.\(file\)\.([^"@]+)@([^":]+):(\d+):(\d+)"')
#: The scopes a declaration can live in: shared (a type or the file) or a body's own (a local).
#: #60: a node with an optional label (`processed_init=binary_expr`); an `original_init` subtree is the
#: unresolved copy of a binding's expression, so it is skipped.
LABELLED_NODE = re.compile(r"^( *)\((?:(\w+)=)?(\w+)")
DECODED_TYPE = re.compile(r'^ *\((?:struct_decl|class_decl) [^"]*"(\w+)"[^\n]*\binherits="[^"]*\b(?:Decodable|Codable)\b')
NUMERIC_FIELD = re.compile(r'^ *\(var_decl [^"]*"(\w+)" interface_type="(?:U?Int(?:8|16|32|64)?|Double|Float|'
                           r'CGFloat|Decimal)\??"[^\n]*readImpl=stored')
#: Any operator on a type that is not text or a collection: `+`, `-=`, `&+`, on `Int`, `Int32`,
#: `FixedWidthInteger`, `Decimal`... (the review's A5, A7).
OPERATOR = re.compile(r'decl="(?:Swift|Foundation)\.\(file\)\.(\w+)(?: extension)?\.(&?(?:<<|>>|[-+*/%])=?)(?:"| \[with)')
NOT_NUMBERS = {"String", "Substring", "StringProtocol", "Character", "Array", "ArraySlice",
               "ContiguousArray", "Set", "Dictionary", "Sequence", "Collection",
               "RangeReplaceableCollection", "Optional"}
#: The end of a resolved function's name. The compiler prints a function whose labels are all `_`
#: by its base name alone (`map [with ...`, `swapAt"`), and any other with its labels.
_CALLED = r'(?:\(([^)]*)\))?(?:"| \[with)'
#: A numeric method, which is arithmetic by another spelling (the review's A6).
NUMERIC_METHOD = re.compile(r'decl="(?:Swift|Foundation)\.\(file\)\.\w+(?: extension)?\.(advanced|distance|adding\w*|'
                            r'subtracting\w*|multiplied\w*|divided\w*|remainder\w*|squareRoot|negate|addProduct|'
                            # #173: the remainder, quotient and overflow forms the second W2 review planted.
                            r'truncatingRemainder|quotientAndRemainder|form\w+|\w+ReportingOverflow)'
                            + _CALLED)
#: #173: a free numeric function, the C library's through Foundation's re-export among them.
FREE_NUMERIC = re.compile(r'decl="(?:Swift|Foundation|_DarwinFoundation\d*)\.\(file\)\.(pow|sqrt|exp2?|log(?:2|10)?|fmod|'
                          r'remainder|fabs|abs|cbrt|hypot)[(@"]')
#: #173: an arithmetic operator the app declares for a type of its own, and an extension of a number.
OPERATOR_DECL = re.compile(r'^ *\(func_decl [^"]*"(&?(?:<<|>>|[-+*/%])=?)(?:\([_:]*\))?"')
NUMERIC_EXTENSION = re.compile(r'^ *\(extension_decl [^"]*"(U?Int(?:8|16|32|64)?|Double|Float|CGFloat|Decimal|BinaryInteger|'
                               r'FixedWidthInteger|SignedInteger|UnsignedInteger|FloatingPoint|BinaryFloatingPoint|'
                               r'Numeric|SignedNumeric|AdditiveArithmetic)"')
#: #171: a decoded enum, a case of it whose payload is a number, and a stored field typed as one.
DECODED_ENUM = re.compile(r'^ *\(enum_decl [^"]*"(\w+)"[^\n]*\binherits="[^"]*\b(?:Decodable|Codable)\b')
NUMERIC_CASE = re.compile(r'^ *\(enum_element_decl (?!implicit)[^"]*"(\w+)\(_:\)" interface_type="[^"]*-> \('
                          r'(?:U?Int(?:8|16|32|64)?|Double|Float|CGFloat|Decimal)\) ->')
FACT_FIELD = re.compile(r'^ *\(var_decl [^"]*"(\w+)" interface_type="(\w+)\??"[^\n]*readImpl=stored')
#: #173: a type that conforms to `Decodable` in an extension stores served numbers too.
DECODED_EXTENSION = re.compile(r'^ *\(extension_decl [^"]*"(\w+)"[^\n]*\binherits="[^"]*\b(?:Decodable|Codable)\b')
#: A function that hands each element of its receiver to a closure.
HANDS_ELEMENTS = re.compile(r'decl="(?:Swift|Foundation)\.\(file\)\.\w+ extension\.(?:map|compactMap|flatMap|filter|'
                            r'forEach|reduce|first|last|contains|allSatisfy|drop|prefix|min|max|sorted|firstIndex|'
                            r'lastIndex|partition|count)' + _CALLED)
ORDERING_CALL = re.compile(r'decl="(?:Swift|Foundation)\.\(file\)\.\w+(?: extension)?\.(sorted|sort|sortedArray|max|'
                           r'min|reversed|shuffled|swapAt)' + _CALLED)
LOCAL_VAR = re.compile(r'^ *\(var_decl [^\[]*range=\[([^\]:]+):(\d+):(\d+)')
#: A bound name: the quoted string that is no attribute's value (`type="Int" "place"`).
PATTERN_NAME = re.compile(r'^ *\(pattern_named (?:[^"=]*="[^"]*")*[^"=]*"([^"]+)"')
PARAMETER = re.compile(r'^ *\(parameter "([^"]+)"')
FUNCTION = re.compile(r'^ *\((?:func_decl|constructor_decl) [^\[]*range=\[[^\]:]+:(\d+):\d+[^"]*"(\w+)')
#: A reference into the app's module as the flow reads it: a generic one ends `[with ...]`.
FLOW_REF = re.compile(r'decl="main\.\(file\)\.([^"@]+)@([^":]+):(\d+):(\d+)(?:"| \[with)')
CALLEE = re.compile(r'decl="main\.\(file\)\.((?:[\w.]+\.)?)(\w+)(?:\([^)"]*\))?@([^":]+):(\d+):\d+(?:"| \[with)'
                    r'.*? function_ref=\w+ apply')
#: A type's declaration. A protocol's node is `protocol`, not `protocol_decl`.
TYPE_DECL = re.compile(r'^ *\((struct_decl|class_decl|enum_decl|extension_decl|protocol)\b[^"]*"([\w.]+)"')
LOCATION = re.compile(r"location=[^ ]*?(\w+\.swift):(\d+):(\d+)")
APPLIED = re.compile(r" function_ref=\w+ apply")
#: A type that can hold a number: `Int`, `Double?`, `[Int]`, `(offset: Int, element: Int)`. A model,
#: a row or a list of them is no served number, though its fields are; only these carry one.
NUMERIC_TYPE = re.compile(r"\b(?:U?Int(?:8|16|32|64)?|Double|Float|CGFloat|Decimal)\b")
TYPE_OF = {name: re.compile(rf'\b{name}="([^"]*)"') for name in ("type", "interface_type", "result")}
#: The line a node's range starts on.
LOCAL_VAR_RANGE = re.compile(r"range=\[[^\]:]+:(\d+):\d+")
SHARED_SCOPES = {"source_file", "struct_decl", "class_decl", "enum_decl", "extension_decl",
                 "protocol_decl", "actor_decl"}
LOCAL_SCOPES = {"func_decl", "constructor_decl", "destructor_decl", "accessor_decl", "closure_expr"}


def dump_ast(sdk_name: str, flags: list[str], folder: pathlib.Path = CLIENT) -> tuple[str, int] | None:
    """`(AST, exit code)` for one configuration, or None where there is no toolchain."""
    xcrun = shutil.which("xcrun")
    if xcrun is None:
        return None
    try:
        # S603: the executable is resolved from PATH above and every argument is a literal or a
        # path inside this repository; nothing here comes from outside the tree.
        sdk = subprocess.run(  # noqa: S603
            [xcrun, "--sdk", sdk_name, "--show-sdk-path"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    sources = sorted(str(path) for path in folder.rglob("*.swift"))
    result = subprocess.run(  # noqa: S603
        [xcrun, "swiftc", "-typecheck", "-dump-ast", *flags, "-sdk", sdk, *sources],
        capture_output=True, text=True, cwd=ROOT,
    )
    # `-dump-ast` writes the tree to stderr and type errors land there too. A type error STOPS the
    # dump, so every later file silently leaves the check -- the M16-W1 seat shipped a pasteboard
    # write that way and this gate said PASS on 8 of 11 files. The exit code comes back with the
    # tree and `main` refuses anything but 0.
    return result.stderr, result.returncode


def references(ast: str) -> dict[str, set[str]]:
    """`{file name: {"Module.symbol", ...}}` for every declaration the compiler resolved."""
    marks = [(m.start(), pathlib.Path(m.group(1)).name) for m in SOURCE.finditer(ast)]
    found: dict[str, set[str]] = {name: set() for _, name in marks}
    for index, (start, name) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(ast)
        # `import \`Network\`` and `import/**/WebKit` are one thing to the compiler, and this is
        # where the compiler says so. An import of a module nothing uses still fails the gate: the
        # point of the allowlist is that reaching the framework at all is a reviewed change.
        for module in IMPORT.findall(ast[start:end]):
            found[name].add(f"{module}.<imported>")
        if DECODES_URL.search(ast[start:end]):
            found[name].add("Foundation.URL.decoded")
        for module, symbol in DECL.findall(ast[start:end]):
            # A member added in an extension prints as `Module.(file).extension.name`, which hid
            # `.draggable` and `String.write(toFile:)` from the first version of this gate.
            symbol = re.sub(r"([\w.]+) extension\.", r"\1.", symbol)
            symbol = re.sub(r"(^|\.)extension\.", r"\1", symbol)
            found[name].add(f"{module}.{symbol.rstrip('.')}")
    for name, facts in (*sink_facts(ast).items(), *flow_facts(ast).items(), *url_facts(ast).items(),
                        *request_facts(ast).items()):
        found.setdefault(name, set()).update(facts)
    return found


def _shared_state(ast: str) -> tuple[dict[tuple[str, int, int], str], list[tuple[str, str, tuple[str, int, int]]]]:
    """Every `var` the client shares, by where its declaration starts, and every reference into the
    app's own module, as `(file, symbol, where its declaration starts)`.

    Shared state is a `var` whose storage the compiler marks `writeImpl=stored`, declared in a type or
    at file scope: a `let`, a computed property and a function's local are not shared.
    """
    shared: dict[tuple[str, int, int], str] = {}
    refs: list[tuple[str, str, tuple[str, int, int]]] = []
    stack: list[tuple[int, str]] = []
    current = ""
    for line in ast.splitlines():
        node = NODE.match(line)
        if node:
            depth, kind = len(node.group(1)), node.group(2)
            while stack and stack[-1][0] >= depth:
                stack.pop()
            if kind == "source_file":
                current = pathlib.Path(line.split('"')[1]).name
            elif kind == "var_decl" and "writeImpl=stored" in line:
                scope = next((k for _, k in reversed(stack) if k in SHARED_SCOPES | LOCAL_SCOPES), "source_file")
                start, named = RANGE_START.search(line), VAR_NAME.match(line)
                if scope in SHARED_SCOPES and start and named:
                    shared[(pathlib.Path(start.group(1)).name, int(start.group(2)), int(start.group(3)))] = named.group(1)
            stack.append((depth, kind))
        refs += [(current, symbol, (pathlib.Path(path).name, int(row), int(column)))
                 for symbol, path, row, column in MAIN_REF.findall(line)]
    return shared, refs


#: #107: a call, or a constructor's, whose result is or holds a URL: `URL`, `URL?`, `[URL]`, and since
#: the W2 review's B2 any type that names one (`[String : URL]?`, `Set<URL>`, a tuple). A
#: constructor's type is a function's, so what it makes is after its last arrow: `(URL) ->
#: XMLParser?` takes a URL and makes none.
MAKES_URL = re.compile(r'^ *\((?:\w+=)?(?:call_expr|constructor_ref_call_expr) [^\n]*?\btype="([^"]*)"')
#: The second W2 review's U11 and M6: a cast makes a URL no call returns, `value as? URL` or a
#: `case let u as URL` pattern, out of `Any`.
CASTS_URL = re.compile(r'^ *\((?:\w+=)?(?:(?:conditional|forced)_checked_cast_expr [^\n]*?\b(?:written_)?type|'
                       r'pattern_is [^\n]*?\bcast_to)="[^"]*\bURL\b')


def url_facts(ast: str) -> dict[str, set[str]]:
    """#107: `{file name: {"Foundation.URL.made", ...}}` for every call that makes a URL, so the
    network rule judges it as it judges `URL.init(string:)`, whatever the call is named."""
    facts: dict[str, set[str]] = {}
    current = ""
    for line in ast.splitlines():
        if line.startswith("(source_file"):
            current = pathlib.Path(line.split('"')[1]).name
        elif (((call := MAKES_URL.match(line)) and re.search(r"\bURL\b", call.group(1).rsplit("->", 1)[-1]))
              or CASTS_URL.match(line)):
            facts.setdefault(current, set()).add("Foundation.URL.made")
    return facts


def _sink_holds(ast: str) -> list[tuple[str, str]]:
    """The W2 review's M1: `(sink file, fact)` for what a sink holds at a type's or the file's scope,
    with its compiled type."""
    found: list[tuple[str, str]] = []
    stack: list[tuple[int, str]] = []
    current = ""
    for line in ast.splitlines():
        if not (node := NODE.match(line)):
            continue
        depth, kind = len(node.group(1)), node.group(2)
        while stack and stack[-1][0] >= depth:
            stack.pop()
        if kind == "source_file":
            current = pathlib.Path(line.split('"')[1]).name
        elif kind == "var_decl" and current in SINK_FILES and "readImpl=stored" in line:
            scope = next((k for _, k in reversed(stack) if k in SHARED_SCOPES | LOCAL_SCOPES), "source_file")
            named, typed = VAR_NAME.match(line), TYPE_OF["interface_type"].search(line)
            if scope in SHARED_SCOPES and named and typed:
                found.append((current, f"main.<holds>.{named.group(1)}:{typed.group(1)}"))
        stack.append((depth, kind))
    return found


def _sink_calls(ast: str) -> list[tuple[str, str]]:
    """The W2 review's M1: `(sink file, fact)` for each function, initialiser or computed property a
    sink reaches that another file declares. A call is known by its labels, by `function_ref=...
    apply` after it, or by a function type: the compiler prints one whose labels are all `_` without
    them."""
    getters = {(pathlib.Path(start.group(1)).name, int(start.group(2)), int(start.group(3)))
               for line in ast.splitlines()
               if line.lstrip().startswith("(var_decl") and "readImpl=getter" in line
               and (start := RANGE_START.search(line))}
    found: list[tuple[str, str]] = []
    current = ""
    for line in ast.splitlines():
        if line.startswith("(source_file"):
            current = pathlib.Path(line.split('"')[1]).name
        if current not in SINK_FILES:
            continue
        for reference in FLOW_REF.finditer(line):
            symbol, path, row, column = reference.groups()
            declared, last, typed = pathlib.Path(path).name, symbol.split(".")[-1], TYPE_OF["type"].search(line)
            called = "(" in last or APPLIED.match(line, reference.end()) is not None or (
                typed is not None and "->" in typed.group(1) and "enum_element" not in line)
            if declared not in SINK_FILES and (called or (declared, int(row), int(column)) in getters):
                found.append((current, f"main.<calls>.{'.'.join([*symbol.split('.')[:-1], _base(last)])}@{declared}"))
    return found


def _kept_types(ast: str) -> list[tuple[str, str]]:
    """The second W2 review's B1: `(file, fact)` for an extension of a kept type outside the file that
    declares it, and for a kept type's conformance to a protocol the app declares."""
    declared: dict[str, str] = {}
    protocols: set[str] = set()
    conformances: list[tuple[str, str, str, bool]] = []  # (file, type, what it inherits, an extension)
    current = ""
    for line in ast.splitlines():
        if line.startswith("(source_file"):
            current = pathlib.Path(line.split('"')[1]).name
        elif named := TYPE_DECL.match(line):
            kind, type_name = named.group(1), named.group(2).split(".")[-1]
            if kind == "protocol":
                protocols.add(type_name)
            elif type_name in KEPT_TYPES:
                if kind != "extension_decl":
                    declared[type_name] = current
                inheriting = re.search(r'\binherits="([^"]*)"', line)
                conformances.append((current, type_name, inheriting.group(1) if inheriting else "",
                                     kind == "extension_decl"))
    found: list[tuple[str, str]] = []
    for file, type_name, inherits, extension in conformances:
        if extension and file != declared.get(type_name):
            found.append((file, f"main.<extends>.{type_name}@{declared.get(type_name, '?')}"))
        found += [(file, f"main.<conforms>.{type_name}:{protocol}")
                  for protocol in (part.strip() for part in inherits.split(",")) if protocol in protocols]
    return found


#: The second W2 review's B2: what a sink runs is not its file alone. A body another file owns runs
#: when a sink calls it, or when a decoder does (a coding witness, called by no name). Each such body,
#: followed through the functions, initialisers and computed properties it reaches and every member a
#: protocol requirement may dispatch to, reads no shared `var` (a global, a `static` or a class's) and
#: no closure kept in a global or a `static`. What it does not follow: a stored property's default, a
#: global or `static` `let`'s initialiser, a closure kept in a value, and what Foundation holds.
_LOCAL_KINDS = {"func_decl", "constructor_decl", "destructor_decl", "accessor_decl", "closure_expr"}


#: #172: Foundation's shared state, which any file can set and a sink could read: the main thread's
#: dictionary, the notification centre, the shared caches and credential stores.
FOUNDATION_SHARED = re.compile(r'decl="Foundation\.\(file\)\.((?:Thread\.threadDictionary|NotificationCenter|URLCache|'
                               r'HTTPCookieStorage|URLCredentialStorage|NSUbiquitousKeyValueStore)[\w.]*)')


class _SinkReach:
    """The second W2 review's B2: the bodies a privacy sink runs, and the shared state they read."""

    def __init__(self, roots: list[_Node]) -> None:
        self.roots = roots
        self.bodies: dict[tuple[object, ...], tuple[str, str, _Node]] = {}
        self.lines: dict[tuple[str, str], list[int]] = {}
        self.members: dict[str, list[tuple[object, ...]]] = {}
        self.mutable: dict[tuple[str, int, int], str] = {}
        self.protocols: set[str] = set()
        self.witnesses: list[tuple[object, ...]] = []
        for root in roots:
            self.index(root, _file_of(root), "", "source_file")

    def index(self, node: _Node, file: str, owner: str, scope: str) -> None:
        if declared := TYPE_DECL.match(node.line):
            owner, scope = declared.group(2).split(".")[-1], declared.group(1)
            if scope == "protocol":
                self.protocols.add(owner)
        elif function := FUNCTION.match(node.line):
            self.function(node, file, owner, function)
        elif node.kind == "var_decl":
            self.variable(node, owner, scope)
        for index, kid in enumerate(node.kids):
            self.initialiser(node.kids, index, owner, scope)
            self.index(kid, file, owner, node.kind if node.kind in _LOCAL_KINDS else scope)

    def initialiser(self, kids: list[_Node], index: int, owner: str, scope: str) -> None:
        """#172: a global or `static` `let`'s initialiser runs on first use, so it is a body the code
        that reads the constant runs."""
        if kids[index].kind != "pattern_binding_decl" or index + 1 >= len(kids):
            return
        declared = kids[index + 1]
        if declared.kind != "var_decl" or not (place := LOCAL_VAR.match(declared.line)) \
                or not (named := VAR_NAME.match(declared.line)):
            return
        if scope in _LOCAL_KINDS or not (scope == "source_file" or " static " in declared.line):
            return
        key = (pathlib.Path(place.group(1)).name, int(place.group(2)), int(place.group(3)))
        self.bodies.setdefault(key, (key[0], f"{owner}.{named.group(1)}" if owner else named.group(1), kids[index]))

    def function(self, node: _Node, file: str, owner: str, function: re.Match[str]) -> None:
        key: tuple[object, ...] = ("fn", file, int(function.group(1)), function.group(2))
        printed = node.line.split('"')[1] if '"' in node.line else function.group(2)
        self.bodies[key] = (file, f"{owner}.{printed}" if owner else printed, node)
        self.lines.setdefault((file, function.group(2)), []).append(int(function.group(1)))
        self.members.setdefault(function.group(2), []).append(key)
        if printed in ("init(from:)", "encode(to:)"):
            self.witnesses.append(key)

    def variable(self, node: _Node, owner: str, scope: str) -> None:
        if not (place := LOCAL_VAR.match(node.line)) or not (named := VAR_NAME.match(node.line)):
            return
        key = (pathlib.Path(place.group(1)).name, int(place.group(2)), int(place.group(3)))
        if "readImpl=getter" in node.line:
            self.bodies[key] = (key[0], f"{owner}.{named.group(1)}" if owner else named.group(1), node)
            self.members.setdefault(named.group(1), []).append(key)
        static = " static " in node.line and scope not in _LOCAL_KINDS
        typed = TYPE_OF["interface_type"].search(node.line)
        closure = typed is not None and "->" in typed.group(1) and (scope == "source_file" or static)
        shared = scope in ("source_file", "class_decl") or static
        if shared and ("writeImpl=stored" in node.line or closure):
            self.mutable[key] = named.group(1)

    def reached(self, node: _Node) -> Iterator[tuple[object, ...]]:
        """The bodies `node` calls or reads: by location, by the function's name and line, and every
        member a protocol requirement may dispatch to."""
        for item in node.walk():
            for reference in FLOW_REF.finditer(item.line):
                symbol, path, row, column = reference.groups()
                file, parts, line = pathlib.Path(path).name, symbol.split("."), int(row)
                typed = TYPE_OF["type"].search(item.line)
                called = "(" in parts[-1] or APPLIED.match(item.line, reference.end()) is not None or (
                    typed is not None and "->" in typed.group(1))
                if (file, line, int(column)) in self.bodies:
                    yield (file, line, int(column))
                candidates = [n for n in self.lines.get((file, _base(parts[-1])), []) if n <= line]
                if called and candidates:
                    yield ("fn", file, max(candidates), _base(parts[-1]))
                if len(parts) >= 2 and _base(parts[-2]) in self.protocols:
                    yield from self.members.get(_base(parts[-1]), [])

    def facts(self) -> list[tuple[str, str]]:
        queue = [key for root in self.roots if _file_of(root) in SINK_FILES for key in self.reached(root)]
        queue += self.witnesses
        seen: set[tuple[object, ...]] = set()
        # #172: Foundation's shared state, read in a sink itself.
        found: list[tuple[str, str]] = [
            (_file_of(root), f"main.<sink runs>.{_file_of(root)} uses {used.group(1)}@Foundation")
            for root in self.roots if _file_of(root) in SINK_FILES
            for item in root.walk() for used in FOUNDATION_SHARED.finditer(item.line)]
        while queue:
            key = queue.pop()
            if key in seen or key not in self.bodies:
                continue
            seen.add(key)
            file, shown, node = self.bodies[key]
            if file in SINK_FILES:
                continue
            found += [(file, f"main.<sink runs>.{shown} reads {self.mutable[where]}@{where[0]}")
                      for item in node.walk() for reference in FLOW_REF.finditer(item.line)
                      if (where := (pathlib.Path(reference.group(2)).name, int(reference.group(3)),
                                    int(reference.group(4)))) in self.mutable]
            found += [(file, f"main.<sink runs>.{shown} uses {used.group(1)}@Foundation")
                      for item in node.walk() for used in FOUNDATION_SHARED.finditer(item.line)]
            queue += list(self.reached(node))
        return found


def sink_facts(ast: str) -> dict[str, set[str]]:
    """#85 (D-180): `{file name: {"main.<...>", ...}}`, the facts `problems` judges about the sinks: a
    sink's own shared state, its reads of another file's, and who calls a `PROVENANCE` declaration."""
    shared, refs = _shared_state(ast)
    facts: dict[str, set[str]] = {}
    for (file, _, _), name in shared.items():
        if file in SINK_FILES:
            facts.setdefault(file, set()).add(f"main.<mutable stored state>.{name}")
    for file, fact in (*_sink_holds(ast), *_sink_calls(ast), *_kept_types(ast), *_SinkReach(_tree(ast)).facts()):
        facts.setdefault(file, set()).add(fact)
    for file, symbol, declared in refs:
        if file in SINK_FILES and declared in shared and declared[0] != file:
            facts.setdefault(file, set()).add(f"main.<reads mutable state>.{shared[declared]}@{declared[0]}")
        if symbol in PROVENANCE:
            facts.setdefault(file, set()).add(f"main.<builds>.{symbol}")
    return facts


class _Node:
    """One node of the dump: its depth, label, kind, first line, and children."""

    __slots__ = ("depth", "kids", "kind", "label", "line")

    def __init__(self, depth: int, label: str, kind: str, line: str) -> None:
        self.depth, self.label, self.kind, self.line = depth, label, kind, line
        self.kids: list[_Node] = []

    def walk(self) -> Iterator[_Node]:
        yield self
        for kid in self.kids:
            yield from kid.walk()


def _tree(ast: str) -> list[_Node]:
    """The dump as a tree, one root per source file, without the unresolved `original_init` copies."""
    roots: list[_Node] = []
    stack: list[_Node] = []
    skip: int | None = None
    for line in ast.splitlines():
        match = LABELLED_NODE.match(line)
        if not match:
            continue
        depth, label, kind = len(match.group(1)), match.group(2) or "", match.group(3)
        if skip is not None and depth > skip:
            continue
        skip = depth if label == "original_init" else None
        if skip is not None:
            continue
        while stack and stack[-1].depth >= depth:
            stack.pop()
        node = _Node(depth, label, kind, line)
        (stack[-1].kids if stack else roots).append(node)
        stack.append(node)
    return roots


def _file_of(root: _Node) -> str:
    return pathlib.Path(root.line.split('"')[1]).name


def _served_cases(roots: list[_Node]) -> dict[tuple[str, str], str]:
    """#171: `(enum, case) -> "number"` for each numeric payload of an enum the client decodes."""
    found: dict[tuple[str, str], str] = {}
    for root in roots:
        for node in root.walk():
            if (named := DECODED_ENUM.match(node.line)) is None or named.group(1) in NOT_SERVED:
                continue
            for element in node.kids:
                if (case := NUMERIC_CASE.match(element.line)) is not None:
                    found[(named.group(1), case.group(1))] = "number"
                    found[(named.group(1), f"{case.group(1)}(_:)")] = "number"
    return found


def served_fields(roots: list[_Node]) -> dict[tuple[str, str], str]:
    """`(type, field) -> kind` for every numeric value a decoded type stores (the review's A8)."""
    found: dict[tuple[str, str], str] = {}
    # #173: a type that conforms in an extension is decoded too.
    extended = {m.group(1) for root in roots for node in root.walk() if (m := DECODED_EXTENSION.match(node.line))}
    # #171: a decoded enum's numeric payload is a served number (`JSONValue.number`), and so is a field
    # of a decoded type that holds such an enum (`Pick.whyFact`).
    cases = _served_cases(roots)
    found.update(cases)
    fact_types = {enum for enum, _ in cases}

    def visit(node: _Node, decoded: str | None) -> None:
        if node.kind in ("func_decl", "constructor_decl", "accessor_decl", "closure_expr"):
            return
        named = DECODED_TYPE.match(node.line) or (
            (m := TYPE_DECL.match(node.line)) and m.group(1) in ("struct_decl", "class_decl")
            and m.group(2) in extended and m)
        if named:
            name = named.group(1) if named.re is DECODED_TYPE else named.group(2)
            decoded = None if name in NOT_SERVED else name
        elif node.kind in ("struct_decl", "class_decl", "enum_decl"):
            decoded = None
        # A static is the type's own constant, never decoded.
        if decoded and (field := NUMERIC_FIELD.match(node.line)) and " static " not in node.line:
            found[(decoded, field.group(1))] = FIELD_KINDS.get(field.group(1), "number")
        elif decoded and (held := FACT_FIELD.match(node.line)) and held.group(2) in fact_types \
                and " static " not in node.line:
            found[(decoded, held.group(1))] = "number"
        for kid in node.kids:
            visit(kid, decoded)

    for root in roots:
        visit(root, None)
    return found


#: What carries a served number, by where the compiler says it is declared: a declaration's
#: `(file, line, column)`; `("bound", file, line, name)` for a loop's or a closure's name, bound on the
#: line its `for` or `{` starts; `("parameter", file, line, function, name)` and `("result", file,
#: line, function)` for a function declared at that line. Never a bare name, which every `row` and
#: `index` in a file would share.
_Carriers = dict[tuple[object, ...], set[str]]


def _base(name: str) -> str:
    return name.split("(")[0]


def _numeric(node: _Node, attribute: str) -> bool:
    """Whether what a node declares or computes can hold a number, by its compiled type."""
    typed = TYPE_OF[attribute].search(node.line)
    return typed is not None and NUMERIC_TYPE.search(typed.group(1)) is not None


#: #171: text, and a value of `Any`, can carry a served number too: written into text and parsed back,
#: or put in a container of `Any` and cast back out.
TEXTY_TYPE = re.compile(r"^(?:@lvalue )?(?:inout )?(?:String|Substring|DefaultStringInterpolation)\??$|\bAny\b")
TEXT_NODE = re.compile(r'\btype="(?:@lvalue )?(?:String|Substring|DefaultStringInterpolation)\??"')
#: A number parsed from text: the numeric types' initialisers from a string.
PARSES_NUMBER = re.compile(r'decl="(?:Swift|Foundation)\.\(file\)\.(?:U?Int(?:8|16|32|64)?|Double|Float|Decimal|'
                           r'FixedWidthInteger|BinaryInteger|BinaryFloatingPoint|LosslessStringConvertible)'
                           r'(?: extension)?\.init\(_:')


def _texty(node: _Node, attribute: str) -> bool:
    """#171: whether a node declares or computes text, or a value of `Any` (a container of it among them)."""
    typed = TYPE_OF[attribute].search(node.line)
    return typed is not None and TEXTY_TYPE.search(typed.group(1)) is not None


def _carries(node: _Node, attribute: str) -> bool:
    """A number, text, or `Any`: what can carry a served number (#171)."""
    return _numeric(node, attribute) or _texty(node, attribute)


def _reach(node: _Node, closures: bool = True, text: bool = True) -> Iterator[_Node]:
    """A node and what it is computed from. Without `closures`, a closure's body is left out (#173, the
    review's M5: a count of served things is not a served number). Without `text`, text is left out
    unless a number is parsed from it (#171: a label's length is not a served number; `Int(text)` is)."""
    yield node
    parses = node.kind == "call_expr" and bool(node.kids) and any(
        PARSES_NUMBER.search(item.line) for item in node.kids[0].walk())
    for kid in node.kids:
        if not closures and kid.kind == "closure_expr":
            continue
        if not (text or parses) and TEXT_NODE.search(kid.line):
            continue
        yield from _reach(kid, closures, text or parses)


def _mark(carriers: _Carriers, key: tuple[object, ...], kinds: set[str]) -> bool:
    if not kinds or kinds <= carriers.get(key, set()):
        return False
    carriers.setdefault(key, set()).update(kinds)
    return True


def _parameters(roots: list[_Node]) -> dict[tuple[str, str, int], list[tuple[str, bool, bool]]]:
    """`(file, function or initialiser name, line) -> its parameters`, in order: each name, whether it
    can carry a number (a number, text or `Any`, #171), and whether it is text or `Any`."""
    found: dict[tuple[str, str, int], list[tuple[str, bool, bool]]] = {}
    for root in roots:
        for node in root.walk():
            if function := FUNCTION.match(node.line):
                listed = next((kid for kid in node.kids if kid.kind == "parameter_list"), None)
                names = [(m.group(1), _carries(kid, "interface_type"), _texty(kid, "interface_type"))
                         for kid in (listed.kids if listed else []) if (m := PARAMETER.match(kid.line))]
                found[(_file_of(root), function.group(2), int(function.group(1)))] = names
            elif node.kind == "subscript_decl" and (start := RANGE_START.search(node.line)):
                # #173: a subscript's parameters, which its getter lists, keyed as a function `subscript`.
                listed = next((item for item in node.walk() if item.kind == "parameter_list"), None)
                names = [(m.group(1), _carries(kid, "interface_type"), _texty(kid, "interface_type"))
                         for kid in (listed.kids if listed else []) if (m := PARAMETER.match(kid.line))]
                found[(_file_of(root), "subscript", int(start.group(2)))] = names
    return found


def _members(roots: list[_Node]) -> tuple[dict[tuple[str, str], tuple[object, ...]],
                                          list[tuple[str, tuple[object, ...]]],
                                          dict[str, list[tuple[object, ...]]]]:
    """What the types declare: each struct's or class's stored properties by `(type, name)`, for its
    memberwise initialiser; each protocol requirement; and every other member, by name, as a witness
    a requirement may dispatch to. Properties by location, functions by their result."""
    stored: dict[tuple[str, str], tuple[object, ...]] = {}
    requirements: list[tuple[str, tuple[object, ...]]] = []
    witnesses: dict[str, list[tuple[object, ...]]] = {}

    def visit(node: _Node, file: str, container: tuple[str, str] | None) -> None:
        declared = TYPE_DECL.match(node.line)
        member: tuple[str, tuple[object, ...]] | None = None
        if container and (place := LOCAL_VAR.match(node.line)) and (named := VAR_NAME.match(node.line)):
            member = named.group(1), (pathlib.Path(place.group(1)).name, int(place.group(2)), int(place.group(3)))
            if container[0] in ("struct_decl", "class_decl") and "readImpl=stored" in node.line:
                stored[(container[1], member[0])] = member[1]
        elif container and node.kind == "func_decl" and (function := FUNCTION.match(node.line)):
            member = function.group(2), ("result", file, int(function.group(1)), function.group(2))
        if member is not None:
            if container and container[0] == "protocol":
                requirements.append(member)
            else:
                witnesses.setdefault(member[0], []).append(member[1])
        if node.kind in ("func_decl", "constructor_decl", "accessor_decl", "closure_expr", "var_decl"):
            return
        inner = (declared.group(1), declared.group(2).split(".")[-1]) if declared else container
        for kid in node.kids:
            visit(kid, file, inner)

    for root in roots:
        visit(root, _file_of(root), None)
    return stored, requirements, witnesses


class _Flow:
    """The flow of served numbers through one compiled module, to a fixed point (D-181)."""

    def __init__(self, roots: list[_Node]) -> None:
        self.roots = roots
        self.served = served_fields(roots)
        self.parameters = _parameters(roots)
        self.functions: dict[tuple[str, str], list[int]] = {}
        for file, name, line in self.parameters:
            self.functions.setdefault((file, name), []).append(line)
        self.stored, self.requirements, self.witnesses = _members(roots)
        self.carriers: _Carriers = {}

    def declared(self, file: str, name: str, row: int) -> int | None:
        """The line of the function `name` a reference at `row` names: the nearest one at or above it,
        since a function's range starts at its attributes, and a reference at its name."""
        return max((line for line in self.functions.get((file, _base(name)), []) if line <= row), default=None)

    def carried(self, node: _Node, closures: bool = True, text: bool = False) -> set[str]:
        """What served numbers an expression reaches: a served field, or anything they flowed into.
        `_reach` says which parts of it are read: closures, and text a number is not parsed from."""
        found: set[str] = set()
        for item in _reach(node, closures, text):
            for reference in FLOW_REF.finditer(item.line):
                symbol, path, row, column = reference.groups()
                file, parts, line = pathlib.Path(path).name, symbol.split("."), int(row)
                # A function, called or used as a value. The compiler prints one whose labels are all
                # `_` without them, so its type says it is one.
                typed = TYPE_OF["type"].search(item.line)
                function = "(" in parts[-1] or APPLIED.match(item.line, reference.end()) is not None or (
                    typed is not None and "->" in typed.group(1))
                if len(parts) >= 2 and (kind := self.served.get((parts[-2], parts[-1]))):
                    found.add(kind)
                found |= self.carriers.get((file, line, int(column)), set())
                # #173: a name bound a few lines below where its statement starts (`for` alone on its
                # line) is keyed by the statement's line.
                for back in range(6):
                    found |= self.carriers.get(("bound", file, line - back, parts[-1]), set())
                if function and (at := self.declared(file, parts[-1], line)) is not None:
                    found |= self.carriers.get(("result", file, at, _base(parts[-1])), set())
                # #173: a subscript's parameter is printed under its getter, `<anonymous>`.
                if len(parts) >= 2 and parts[-2] == "<anonymous>" and (
                        at := self.declared(file, "subscript", line)) is not None:
                    found |= self.carriers.get(("parameter", file, at, "subscript", parts[-1]), set())
                if len(parts) >= 2 and "(" in parts[-2] and (at := self.declared(file, parts[-2], line)) is not None:
                    found |= self.carriers.get(("parameter", file, at, _base(parts[-2]), parts[-1]), set())
        return found

    def run(self) -> None:
        changed = True
        while changed:
            changed = False
            for root in self.roots:
                file = _file_of(root)
                for node in root.walk():
                    changed |= self.binding(node) | self.assignment(node) | self.loop(node, file)
                    changed |= self.condition(node, file) | self.cases(node)
                    changed |= self.call(node) | self.inout(node) | self.result(node, file) | self.closure(node, file)
                    changed |= self.subscript(node)
            changed |= self.dispatch()

    def binding(self, node: _Node) -> bool:
        """`let x = served`: into the locals the binding declares."""
        changed = False
        for index, kid in enumerate(node.kids):
            if kid.kind == "pattern_binding_decl":
                for sibling in node.kids[index + 1:]:
                    if sibling.kind != "var_decl" or not (place := LOCAL_VAR.match(sibling.line)):
                        break
                    kinds = self.carried(kid, text=_texty(sibling, "interface_type"))
                    if kinds and _carries(sibling, "interface_type"):
                        key = (pathlib.Path(place.group(1)).name, int(place.group(2)), int(place.group(3)))
                        changed |= _mark(self.carriers, key, kinds)
        return changed

    def _target(self, node: _Node) -> tuple[object, ...] | None:
        """Where an assigned or `inout` place is declared."""
        found = next((m for item in node.walk() if (m := FLOW_REF.search(item.line))), None)
        return None if found is None else (pathlib.Path(found.group(2)).name, int(found.group(3)), int(found.group(4)))

    def assignment(self, node: _Node) -> bool:
        """`x = served`, `self.x = served` (the review's A1), and `x += served`: into what is assigned."""
        if node.kind == "assign_expr" and len(node.kids) >= 2:
            place, value = node.kids[0], node.kids[1]
        elif (node.kind == "binary_expr" and len(node.kids) >= 2 and node.kids[0].kids
              and (operator := OPERATOR.search(node.kids[0].kids[0].line)) and operator.group(2).endswith("=")
              and len(arguments := [kid for kid in node.kids[1].kids if kid.kind == "argument"]) == 2):
            place, value = arguments
        else:
            return False
        inner = place.kids[0] if place.kids else place
        if not _carries(place, "type") and not _carries(inner, "type"):
            return False
        text = _texty(place, "type") or _texty(inner, "type")
        if not (kinds := self.carried(value, text=text)) or (target := self._target(place)) is None:
            return False
        return _mark(self.carriers, target, kinds)

    def loop(self, node: _Node, file: str) -> bool:
        """`for x in served`, `for (i, x) in ...`: into every name the pattern binds (the review's A10, A11)."""
        if node.kind != "for_each_stmt" or not (start := LOCAL_VAR_RANGE.search(node.line)):
            return False
        patterns = [kid for kid in node.kids if kid.kind.startswith("pattern_") and kid.kind != "pattern_binding_decl"]
        sequence = [kid for kid in node.kids
                    if not kid.kind.startswith("pattern_") and kid.kind != "brace_stmt" and kid.label != "where"]
        kinds = set().union(*(self.carried(kid) for kid in sequence)) if sequence else set()
        names = {m.group(1) for kid in patterns for item in kid.walk()
                 if (m := PATTERN_NAME.match(item.line)) and _carries(item, "type")}
        return any([_mark(self.carriers, ("bound", file, int(start.group(1)), name), kinds) for name in names])

    def condition(self, node: _Node, file: str) -> bool:
        """`if let x = served`, `guard let`, `while let`, `if case let`: into the names a condition binds,
        on the line its value starts."""
        if node.kind != "pattern" or len(node.kids) < 2 or not (start := LOCAL_VAR_RANGE.search(node.kids[1].line)):
            return False
        kinds = set().union(*(self.carried(kid, text=True) for kid in node.kids))
        names = {m.group(1) for item in node.kids[0].walk()
                 if (m := PATTERN_NAME.match(item.line)) and _carries(item, "type")}
        return any([_mark(self.carriers, ("bound", file, int(start.group(1)), name), kinds) for name in names])

    def cases(self, node: _Node) -> bool:
        """`switch served { case let x: ... }`: into the names each case binds."""
        if node.kind != "switch_stmt" or not node.kids or node.kids[0].kind == "case_stmt":
            return False
        subject = self.carried(node.kids[0], text=True)
        changed = False
        for case in (kid for kid in node.kids if kid.kind == "case_stmt"):
            # #171: a case that binds a served enum's numeric payload binds a served number, whatever
            # the subject (`case let .number(double)` on a served fact).
            labels = set().union(*(self.carried(kid) for kid in case.kids
                                   if kid.label != "case_body_variables" and kid.kind != "brace_stmt"))
            if not (kinds := subject | labels):
                continue
            changed |= any([_mark(self.carriers, (pathlib.Path(place.group(1)).name, int(place.group(2)),
                                                  int(place.group(3))), kinds)
                            for kid in case.kids if kid.label == "case_body_variables" for variable in kid.kids
                            if _carries(variable, "interface_type") and (place := LOCAL_VAR.match(variable.line))])
        return changed

    def call(self, node: _Node) -> bool:
        """A function's, a method's or an initialiser's parameters, from its arguments (the review's A12);
        and a memberwise initialiser's stored properties."""
        if node.kind != "call_expr" or len(node.kids) < 2 or node.kids[1].kind != "argument_list":
            return False
        callee = next((m for item in node.kids[0].walk() if (m := CALLEE.search(item.line))), None)
        if callee is None:
            return False
        owner, name, target = callee.group(1).rstrip(".").split(".")[-1], callee.group(2), pathlib.Path(callee.group(3)).name
        if (at := self.declared(target, name, int(callee.group(4)))) is None:
            return False
        arguments = [kid for kid in node.kids[1].kids if kid.kind == "argument"]
        changed = False
        # Not strict: a parameter with a default takes no argument.
        for (parameter, numeric, text), argument in zip(self.parameters[(target, name, at)], arguments, strict=False):
            if numeric and (kinds := self.carried(argument, text=text)):
                changed |= _mark(self.carriers, ("parameter", target, at, name, parameter), kinds)
                if name == "init" and (owner, parameter) in self.stored:
                    changed |= _mark(self.carriers, self.stored[(owner, parameter)], kinds)
        return changed

    def subscript(self, node: _Node) -> bool:
        """#173: a subscript's parameters, from the arguments it is read with."""
        if node.kind != "subscript_expr" or not (reference := FLOW_REF.search(node.line)):
            return False
        target, row = pathlib.Path(reference.group(2)).name, int(reference.group(3))
        if (at := self.declared(target, "subscript", row)) is None:
            return False
        listed = next((kid for kid in node.kids if kid.kind == "argument_list"), None)
        arguments = [kid for kid in (listed.kids if listed else []) if kid.kind == "argument"]
        changed = False
        for (parameter, numeric, text), argument in zip(self.parameters.get((target, "subscript", at), []),
                                                        arguments, strict=False):
            if numeric and (kinds := self.carried(argument, text=text)):
                changed |= _mark(self.carriers, ("parameter", target, at, "subscript", parameter), kinds)
        return changed

    def inout(self, node: _Node) -> bool:
        """`places.append(served)`, `fill(&total, served)`: into a place a call is handed `inout`,
        a mutating method's receiver among them."""
        if node.kind != "call_expr" or len(node.kids) < 2 or node.kids[1].kind != "argument_list":
            return False
        handed = [kid for kid in node.kids[1].kids if kid.kind == "argument"]
        if node.kids[0].kind == "dot_syntax_call_expr":
            handed += [kid for listed in node.kids[0].kids if listed.kind == "argument_list"
                       for kid in listed.kids if kid.kind == "argument"]
        places = [kid for kid in handed if kid.line.lstrip().startswith("(argument inout") and kid.kids]
        values = [kid for kid in node.kids[1].kids if kid.kind == "argument" and kid not in places]
        if not places or not (kinds := set().union(*(self.carried(kid) for kid in values))):
            return False
        return any([_mark(self.carriers, target, kinds) for place in places
                    if _numeric(place.kids[0], "type") and (target := self._target(place)) is not None])

    def result(self, node: _Node, file: str) -> bool:
        """What a function returns, to every call of it (the review's A2); what a computed property
        returns, to every reading of it."""
        if node.kind == "func_decl" and (function := FUNCTION.match(node.line)) and _carries(node, "result"):
            key: tuple[object, ...] = ("result", file, int(function.group(1)), function.group(2))
            text = _texty(node, "result")
        elif (node.kind == "var_decl" and "readImpl=getter" in node.line and _carries(node, "interface_type")
              and (place := LOCAL_VAR.match(node.line))):
            key = (pathlib.Path(place.group(1)).name, int(place.group(2)), int(place.group(3)))
            text = _texty(node, "interface_type")
        else:
            return False
        kinds = set().union(*(self.carried(item, text=text) for item in node.walk() if item.kind == "return_stmt"))
        return _mark(self.carriers, key, kinds)

    def closure(self, node: _Node, file: str) -> bool:
        """`served.map { $0 - 1 }`, `served.map { s in s - 1 }`: into the parameters of a closure handed
        each element."""
        if node.kind != "call_expr" or len(node.kids) < 2 or not node.kids[0].kids:
            return False
        if not HANDS_ELEMENTS.search(node.kids[0].kids[0].line) or not (kinds := self.carried(node.kids[0])):
            return False
        changed = False
        for closure in (item for item in node.kids[1].walk() if item.kind == "closure_expr"):
            listed = next((kid for kid in closure.kids if kid.kind == "parameter_list"), None)
            if listed is None or not (start := LOCAL_VAR_RANGE.search(closure.line)):
                continue
            for parameter in listed.kids:
                if (named := PARAMETER.match(parameter.line)) and _numeric(parameter, "interface_type"):
                    changed |= _mark(self.carriers, ("bound", file, int(start.group(1)), named.group(1)), kinds)
        return changed

    def dispatch(self) -> bool:
        """`item.placed` on `any FixturePlaced`: a protocol requirement carries what any member of that
        name carries, since the compiler cannot say which type answers."""
        changed = False
        for name, key in self.requirements:
            kinds = set().union(*(self.carriers.get(witness, set()) for witness in self.witnesses.get(name, [])))
            changed |= _mark(self.carriers, key, kinds)
        return changed


def _scoped(node: _Node, function: str | None = None) -> Iterator[tuple[_Node, str | None]]:
    """Every node with the name of the function it is in, for permissions scoped to one (M5)."""
    if named := FUNCTION.match(node.line):
        function = named.group(2)
    yield node, function
    for kid in node.kids:
        yield from _scoped(kid, function)


def flow_facts(ast: str) -> dict[str, set[str]]:
    """#60 (G-2): `{file name: {"main.<...>", ...}}`, the arithmetic on served numbers and the sorts
    each file makes, resolved by the compiler and followed to a fixed point, for `problems` to judge."""
    flow = _Flow(_tree(ast))
    flow.run()
    facts: dict[str, set[str]] = {}
    sorts: dict[tuple[str, str, str], int] = {}
    for root in flow.roots:
        file = _file_of(root)
        for node, function in _scoped(root):
            for fact in _arithmetic(node, flow, function):
                facts.setdefault(file, set()).add(fact)
            if (ordering := _ordering(node)) is not None:
                sorts[(file, *ordering)] = sorts.get((file, *ordering), 0) + 1
    for (file, method, receiver), count in sorts.items():
        facts.setdefault(file, set()).add(f"main.<sorts>.{method}.{receiver}={count}")
    for root in flow.roots:
        facts.setdefault(_file_of(root), set()).update(_declaration_facts(root))
    return {file: found for file, found in facts.items() if found}


def _declaration_facts(root: _Node) -> set[str]:
    """A decoded type the engine never sends; and (#173) an arithmetic operator of the app's own or a
    member added to a number, arithmetic no rule can follow, so neither is in the client."""
    found: set[str] = set()
    for node in root.walk():
        if (named := DECODED_TYPE.match(node.line)) and named.group(1) in NOT_SERVED:
            found.add(f"main.<unserved>.{named.group(1)}")
        place = RANGE_START.search(node.line)
        row = place.group(2) if place else "?"
        if (declared := OPERATOR_DECL.match(node.line)) is not None:
            found.add(f"main.<declares operator>.{declared.group(1)}@{row}")
        if (extended := NUMERIC_EXTENSION.match(node.line)) is not None:
            found.add(f"main.<extends number>.{extended.group(1)}@{row}")
    return found


def _arithmetic(node: _Node, flow: _Flow, function: str | None) -> list[str]:
    """`main.<arithmetic>.<kind>@<line> <operator> in <function>` for arithmetic on a served number:
    an operator on a number, or a numeric method."""
    operands: _Node | None = None
    operator = ""
    if node.kind in ("binary_expr", "prefix_unary_expr", "postfix_unary_expr") and node.kids:
        found = next((m for item in node.kids[0].walk() if (m := OPERATOR.search(item.line))), None)
        if found is not None and found.group(1) not in NOT_NUMBERS:
            operands, operator = node, found.group(2)
    elif node.kind == "call_expr" and node.kids and node.kids[0].kids and (
            method := NUMERIC_METHOD.search(node.kids[0].kids[0].line)):
        operands, operator = node, f".{method.group(1)}"
    elif node.kind == "call_expr" and node.kids and (free := FREE_NUMERIC.search(node.kids[0].line)):
        operands, operator = node, free.group(1)
    elif node.kind == "call_expr" and (value := _operator_as_value(node)) is not None:
        operands, operator = node, f"{value} (as a value)"
    if operands is None:
        return []
    place = LOCATION.search(node.line)
    line = place.group(2) if place else "?"
    return [f"main.<arithmetic>.{kind}@{line} {operator} in {function or '-'}"
            for kind in sorted(flow.carried(operands, closures=False))]


def _operator_as_value(node: _Node) -> str | None:
    """#173: a numeric operator handed to a call as a function (`reduce(0, +)`, `.map(-)`)."""
    for listed in node.kids[1:]:
        if listed.kind != "argument_list":
            continue
        # The compiler wraps an operator passed as a function in an implicit closure that applies it.
        for wrapped in (item for argument in listed.kids for item in argument.walk() if item.kind == "autoclosure_expr"):
            found = next((m for item in wrapped.walk() if (m := OPERATOR.search(item.line))), None)
            if found is not None and found.group(1) not in NOT_NUMBERS:
                return found.group(2)
    return None


def _ordering(node: _Node) -> tuple[str, str] | None:
    """`(call, receiver)` for a sort, a reversal, a shuffle or a `max(by:)`/`min(by:)` on a resolved
    receiver, the standard library's or Foundation's (the review's M4)."""
    if node.kind != "dot_syntax_call_expr" or len(node.kids) < 2:
        return None
    call = ORDERING_CALL.search(node.kids[0].line)
    if call is None or (call.group(1) in ("max", "min") and call.group(2) != "by:"):
        return None
    receiver = next((m for item in node.kids[1].walk() if (m := MAIN_REF.search(item.line))), None)
    return call.group(1), receiver.group(1).split(".")[-1] if receiver else "?"


def _arithmetic_permitted(name: str, kind: str, function: str) -> bool:
    return (name, kind, None) in ARITHMETIC_PERMITTED or (name, kind, function) in ARITHMETIC_PERMITTED


REQUEST_CALL = re.compile(r'decl="main\.\(file\)\.(EngineClient\.\w+\([^)"]*\))@')
NAMED_DECL = re.compile(r'\bdecl="(\w+)\.\(file\)\.([^"@]+)@([^":]+):(\d+):(\d+)')
ARGUMENT_LABEL = re.compile(r'^ *\(argument label="(\w+)"')


def _named(node: _Node) -> set[str]:
    """The declarations an expression names, by path, the implicit ones (`self`, a wrapper's storage)
    left out; a declaration of another module keeps its module's name."""
    named: set[str] = set()
    for item in node.walk():
        if " implicit " in item.line:
            continue
        for module, path, *_ in NAMED_DECL.findall(item.line):
            named.add(path if module == "main" else f"{module}.{path}")
    return named


def _top(node: _Node) -> _Node:
    """An expression past the loads, conversions and parentheses the compiler wraps it in."""
    while node.kind in {"load_expr", "paren_expr", "function_conversion_expr", "inject_into_optional"} and node.kids:
        node = node.kids[0]
    return node


def _line(node: _Node) -> int:
    found = LOCATION.search(node.line)
    return int(found.group(2)) if found else 0


def _declared(roots: list[_Node]) -> dict[str, _Node]:
    """`{"path:line:col": var_decl node}` for every stored property, by where it is declared."""
    out: dict[str, _Node] = {}
    for root in roots:
        for node in root.walk():
            if node.kind == "var_decl" and (start := RANGE_START.search(node.line)):
                out[f"{pathlib.Path(start.group(1)).name}:{start.group(2)}:{start.group(3)}"] = node
    return out


def _literal_let(roots: list[_Node], where: str) -> bool:
    """Whether the property declared at `where` is a `let` its binding gives a literal."""
    for root in roots:
        for parent in root.walk():
            kids = parent.kids
            for index, kid in enumerate(kids):
                start = RANGE_START.search(kid.line) if kid.kind == "var_decl" else None
                if not start or f"{pathlib.Path(start.group(1)).name}:{start.group(2)}:{start.group(3)}" != where:
                    continue
                binding = kids[index - 1] if index else None
                literal = binding is not None and binding.kind == "pattern_binding_decl" and any(
                    item.kind.endswith("literal_expr") for item in binding.walk()) and not _named(binding)
                return " let " in kid.line and "immutable" in kid.line and literal
    return False


def _request_call(node: _Node) -> list[str]:
    """The arguments of one call to an engine request that name anything but their declaration."""
    if node.kind != "call_expr" or not node.kids or node.kids[0].kind != "dot_syntax_call_expr" \
            or not node.kids[0].kids or not (call := REQUEST_CALL.search(node.kids[0].kids[0].line)):
        return []
    method, found = call.group(1), []
    for arguments in node.kids[1:]:
        if arguments.kind != "argument_list" or " implicit" in arguments.line:
            continue
        for argument in arguments.kids:
            if (label := ARGUMENT_LABEL.match(argument.line)) is None:
                continue
            allowed = REQUEST_ARGUMENTS.get((method, label.group(1)))
            named = _named(argument)
            if allowed is None or (named and named != {allowed}):
                shown = ", ".join(sorted(named)) or "a value"
                found.append(f"main.<request argument>.{method}|{label.group(1)}|{shown}@{_line(node)}")
    return found


def _request_source(node: _Node) -> list[str]:
    """An assignment, an `inout` use or a binding of a declaration a request sends, from anything but
    its declared source."""
    found = []
    if node.kind in {"assign_expr", "inout_expr"} and node.kids:
        for held in _named(_top(node.kids[0])) & set(REQUEST_SOURCES):
            sources = REQUEST_SOURCES[held]
            value = _top(node.kids[1]) if node.kind == "assign_expr" and len(node.kids) > 1 else None
            top_named = {path for _, path, *_ in NAMED_DECL.findall(value.line)} if value else set()
            if sources is None or not (top_named & sources):
                found.append(f"main.<request source>.{held}|{node.kind}@{_line(node)}")
    bindings = {f"{held.rpartition('.')[0]}.${held.rpartition('.')[2]}" for held in REQUEST_SOURCES}
    found += [f"main.<request source>.{path}|binding@{_line(node)}"
              for module, path, *_ in NAMED_DECL.findall(node.line) if module == "main" and path in bindings]
    return found


def request_facts(ast: str) -> dict[str, set[str]]:
    """#174, #188 (INV-64): `{file: {"main.<request ...>", ...}}`, each argument of an engine request
    that names anything but its one declaration in `REQUEST_ARGUMENTS`, and each source of those
    declarations `REQUEST_SOURCES` does not allow."""
    roots = _tree(ast)
    facts: dict[str, set[str]] = {}
    declared_at: dict[str, str] = {}
    for root in roots:
        file = _file_of(root)
        for node in root.walk():
            for module, path, decl_file, decl_line, decl_col in NAMED_DECL.findall(node.line):
                if module == "main" and path in REQUEST_SOURCES:
                    declared_at[path] = f"{pathlib.Path(decl_file).name}:{decl_line}:{decl_col}"
            found = _request_source(node) + ([] if file == NETWORK_FILE else _request_call(node))
            facts.setdefault(file, set()).update(found)
    for held, sources in REQUEST_SOURCES.items():
        if sources is None and held in declared_at and not _literal_let(roots, declared_at[held]):
            facts.setdefault(declared_at[held].split(":")[0], set()).add(
                f"main.<request source>.{held}|not a literal let@0")
    return {file: found for file, found in facts.items() if found}


def _request_problem(name: str, symbol: str) -> str | None:
    """#174, #188 (INV-64): the reader's text, or anything the screen built, into a request's arguments."""
    fact, _, subject = symbol.partition(">.")
    detail, _, line = subject.rpartition("@")
    if fact == "<request argument":
        method, label, named = detail.split("|")
        return (f"{name}:{line}: the request's `{label}` argument to `{method}` names {named}; a request "
                "carries only its declared sources, never what the screen builds (INV-64, D-126; #174, #188)")
    if fact == "<request source":
        held, how = detail.split("|")
        return (f"{name}:{line}: assigns `{held}` ({how}) from something other than its declared source; it "
                "is sent to the engine, so what it holds is held too (INV-64, D-126; #174, #188)")
    return None


def _flow_problem(name: str, symbol: str) -> str | None:
    """#60 (G-2): arithmetic on a served number outside its ruling's place, or a sort past its count."""
    fact, _, subject = symbol.partition(">.")
    if fact == "<arithmetic":
        kind, _, where = subject.partition("@")
        line, _, rest = where.partition(" ")
        operator, _, function = rest.partition(" in ")
        if _arithmetic_permitted(name, kind, function):
            return None
        what = "number" if kind == "number" else kind
        return (f"{name}:{line}: `{operator}` on a served {what}, a second scoring implementation; only the "
                f"places a ruling names do arithmetic on one (REQ-APP-005; D-138, D-167, REQ-CMP-002)")
    if fact == "<declares operator":
        operator, _, line = subject.partition("@")
        return (f"{name}:{line}: declares the operator `{operator}`, arithmetic no rule can follow; the client "
                "computes no ranking value of its own (REQ-APP-005, D-181; #173)")
    if fact == "<extends number":
        number, _, line = subject.partition("@")
        return (f"{name}:{line}: extends `{number}`; a member of a number does arithmetic on whatever calls "
                "it, served numbers included (REQ-APP-005, D-181; #173)")
    if fact == "<sorts":
        call_receiver, _, count = subject.rpartition("=")
        call, _, receiver = call_receiver.partition(".")
        allowed = SORTS_PERMITTED.get((name, call, receiver), 0)
        if int(count) > allowed:
            return (f"{name}: sorts `{receiver}` with `{call}` {count} time(s), and {allowed} is permitted; the "
                    "client orders nothing itself but where a ruling says why (Ruling A, REQ-APP-002)")
    return None


def unseen_permissions(found: dict[str, set[str]]) -> list[str]:
    """The W2 review's R3: every permitted arithmetic and sort must be SEEN on the shipping client. One
    that is not is stale, or the compiler's printed layout moved and a rule went quiet."""
    seen_arithmetic = {(name, fact.split(">.")[1].split("@")[0], fact.rpartition(" in ")[2])
                       for name, facts in found.items() for fact in facts if fact.startswith("main.<arithmetic>.")}
    seen_sorts = {(name, *fact.split(">.")[1].rpartition("=")[0].split(".", 1))
                  for name, facts in found.items() for fact in facts if fact.startswith("main.<sorts>.")}
    missing = [f"{name}: {kind} arithmetic{f' in {function}' if function else ''}"
               for name, kind, function in ARITHMETIC_PERMITTED
               if not any(n == name and k == kind and (function is None or f == function) for n, k, f in seen_arithmetic)]
    missing += [f"{name}: `{call}` on `{receiver}`" for name, call, receiver in SORTS_PERMITTED
                if (name, call, receiver) not in seen_sorts]
    seen_calls = {(name, fact.split(">.")[1].split("@")[0])
                  for name, facts in found.items() for fact in facts if fact.startswith("main.<calls>.")}
    missing += [f"{name}: a call to `{called}`" for name, called in SINK_CALLS_PERMITTED
                if (name, called) not in seen_calls]
    seen_types = {fact.split(">.")[1] for facts in found.values() for fact in facts if fact.startswith("main.<unserved>.")}
    missing += [f"`{name}`, which no type decodes" for name in NOT_SERVED if name not in seen_types]
    return missing


def _sink_problem(name: str, symbol: str) -> str | None:
    """#85 (D-180): a sink's shared state, a sink reading another file's, standings built elsewhere."""
    fact, _, subject = symbol.partition(">.")
    if fact == "<mutable stored state":
        return (f"{name}: `{subject}` is mutable stored state in a privacy sink ({SINK_FILES[name]}); "
                "any file can set it, so it can relay the question (D-180)")
    if fact == "<reads mutable state":
        variable, _, declared = subject.partition("@")
        return (f"{name}: reads `{variable}`, mutable state declared in {declared}, so whatever sets it "
                f"reaches {SINK_FILES[name]} (D-180)")
    if fact == "<holds":
        held, _, typed = subject.partition(":")
        if typed.rstrip("?") not in SINK_HELD_TYPES:
            return (f"{name}: holds `{held}`, a `{typed}`, which another file can change through a reference; "
                    f"a sink holds only values and what its own initialiser builds (D-180, the W2 review's M1)")
        return None
    if fact == "<calls":
        called, _, declared = subject.partition("@")
        if (name, called) not in SINK_CALLS_PERMITTED:
            return (f"{name}: calls `{called.split('.')[-1]}` (`{called}`, {declared}), which another file "
                    "declares; a body another file owns can read the screen's state, so a sink calls only "
                    "what is listed for it (D-180, the W2 review's M1)")
        return None
    if fact == "<builds" and subject in PROVENANCE and name not in PROVENANCE[subject][0]:
        verb = f"builds {subject.split('.')[0]}" if ".init(" in subject else "calls"
        return f"{name}: {verb} (`{subject}`); {PROVENANCE[subject][1]} (D-180)"
    return _kept_problem(name, fact, subject)


def _kept_problem(name: str, fact: str, subject: str) -> str | None:
    """The second W2 review's B1 and B2: a kept type extended or conforming, and code a sink runs."""
    if fact == "<extends":
        kept, _, declared = subject.partition("@")
        return (f"{name}: extends `{kept}` outside its own file ({declared}); a kept type gains no "
                "initialiser and no conformance elsewhere (D-180, the second W2 review's B1)")
    if fact == "<conforms":
        kept, _, protocol = subject.partition(":")
        return (f"{name}: `{kept}` conforms to `{protocol}`, a protocol the app declares, so its "
                "initialiser can be called by another name; a kept type conforms to none (D-180, the "
                "second W2 review's B1)")
    if fact == "<sink runs" and " uses " in subject:
        body, _, used = subject.partition(" uses ")
        return (f"{name}: `{body}`, code a privacy sink runs, uses `{used.partition('@')[0]}`, Foundation's shared "
                "state any file can set, so whatever sets it reaches the sink (D-180, #172)")
    if fact == "<sink runs":
        body, _, read = subject.partition(" reads ")
        variable, _, declared = read.partition("@")
        return (f"{name}: `{body}`, code a privacy sink runs, reads `{variable}` ({declared}), shared "
                "mutable state another file can set, so whatever sets it reaches the sink (D-180, the "
                "second W2 review's B2)")
    return None


def _module_problem(name: str, module: str, symbol: str, decl: str) -> str | None:
    """The module allowlist, including `import` lines, and UIKit's per-symbol exception."""
    if symbol == "<imported>":
        if module not in MODULES | {"UIKit", "CoreFoundation"}:
            return (f"{name}: imports `{module}`, which is not on the client's module allowlist; "
                    "a new framework is a reviewed edit, not an import")
        return None
    if module == "UIKit":
        if symbol.split(".")[0] not in UIKIT_ALLOWED:
            return (f"{name}: UIKit.{symbol} is not one of the re-exported types the design layer "
                    f"may use ({', '.join(sorted(UIKIT_ALLOWED))})")
        return None
    if module == "CoreFoundation":
        if symbol.split(".")[0] not in COREFOUNDATION_ALLOWED:
            return (f"{name}: CoreFoundation.{symbol} is not one the client may use "
                    f"({', '.join(sorted(COREFOUNDATION_ALLOWED))}); the module carries sockets")
        return None
    if module not in MODULES:
        return (f"{name}: resolves `{decl}` in `{module}`, which is not a module the client may "
                "reach; the reader's words pass through every client file")
    return None


def _capability_problem(name: str, symbol: str, decl: str) -> str | None:
    """Network, file system and the ways text leaves a phone, inside the allowed modules."""
    head = symbol.split("(")[0]
    if (name, symbol) in FORBIDDEN_EXCEPT:
        return None
    if any(symbol.startswith(p) or head == p for p in FORBIDDEN):
        return f"{name}: `{decl}` carries text off the device or into shared storage"
    if any(part.startswith(UNSAFE) for part in head.split(".")):
        return (f"{name}: `{decl}` touches memory unsafely, which can rewrite any value, a privacy sink's "
                "own included; the client uses none (D-180, the second W2 review's U9)")
    if any(symbol.startswith(p) for p in PATH_BUILDING):
        if name in {*FILESYSTEM_FILES, NETWORK_FILE}:
            return None
        return (f"{name}: `{decl}` builds a path, and the only paths here are the two stores' "
                "folders and the engine's request")
    if any(symbol.startswith(p) for p in FILESYSTEM) and name not in FILESYSTEM_FILES:
        allowed = "; ".join(f"{file}: {what}" for file, what in FILESYSTEM_FILES.items())
        return (f"{name}: `{decl}` reaches the file system, and only these files write one: {allowed}")
    if symbol == "URL.made" and name not in {NETWORK_FILE, *FILESYSTEM_FILES}:
        return (f"{name}: makes a URL (a call whose result is a URL, whatever it is named), and only "
                f"{NETWORK_FILE} and the two stores make one (D-126, #107)")
    if any(symbol.startswith(p) or head == p for p in NETWORK) and symbol != "URL.made" and name != NETWORK_FILE:
        return (f"{name}: `{decl}` is the network, and {NETWORK_FILE} is the one door (D-126); "
                "its arguments are pinned in EngineClientTests.swift")
    if head.split(".")[0] == "AppStorage" and name != APPSTORAGE_FILE:
        return (f"{name}: `{decl}` stores something outside the register; the one @AppStorage "
                "holds the language choice")
    return None


#: D-175 clause 3: the UI tests' hook exists in Debug builds only. A Release build that reads its
#: launch arguments ships a way to steer the app from outside it. (The scripted router itself is in
#: the Engine, which is never compiled on DEBUG, and is inert unless handed the arguments.) The launch
#: environment is the same door (M18-W2 review M5); `getenv` is refused already, by the module list.
DEBUG_ONLY = ("ProcessInfo.arguments", "ProcessInfo.environment", "CommandLine.arguments",
              "CommandLine.unsafeArgv")


def release_problems(found: dict[str, set[str]]) -> list[str]:
    """What a RELEASE configuration must not contain: the Debug-only UI test hooks (D-175)."""
    return [f"{name}: `{decl}` is a Debug-only UI test hook (D-175), compiled into a Release build"
            for name, decls in sorted(found.items()) for decl in sorted(decls)
            if any(hook in decl for hook in DEBUG_ONLY)]


def problems(found: dict[str, set[str]]) -> list[str]:
    bad: list[str] = []
    for name, decls in sorted(found.items()):
        for decl in sorted(decls):
            module, _, symbol = decl.partition(".")
            if module == "main" and symbol.startswith("<"):
                if (problem := _sink_problem(name, symbol) or _flow_problem(name, symbol)
                        or _request_problem(name, symbol)) is not None:
                    bad.append(problem)
                continue
            problem = _module_problem(name, module, symbol, decl)
            if problem is None and symbol != "<imported>" and module not in {"main", "UIKit", "CoreFoundation"}:
                problem = _capability_problem(name, symbol, decl)
            if problem is not None:
                bad.append(problem)
    return bad


def fixture_dump(ast: str) -> str:
    """The fixture's dump as committed: its folder as `/x/`, no `decl_context`, and every memory
    address as `0x0`, so writing it twice writes the same bytes."""
    text = re.sub(r" ?decl_context=0x[0-9a-f]+", "", ast.replace(f"{FIXTURES.resolve()}/", "/x/"))
    text = re.sub(r"\b0x[0-9a-f]{6,}\b", "0x0", text)
    return text if text.endswith("\n") else text + "\n"


#: A declaration in the dump, by kind, name and line: what the snapshot must agree on with the
#: fixture. Addresses and the compiler's layout of an expression may differ between Xcode versions.
DECLARED = re.compile(r'^ *\((func_decl|constructor_decl|var_decl|struct_decl|class_decl|enum_decl|extension_decl|'
                      r'protocol)\b[^\n]*?range=\[/x/(\w+\.swift):(\d+):\d+[^"]*"([^"]+)"', re.MULTILINE)


def _snapshot_drift(ast: str) -> list[str]:
    """The second W2 review's K1: the committed dump against the fixture as it compiles."""
    if not SNAPSHOT.exists():
        return [f"{SNAPSHOT.name} is missing; write it with `--snapshot`"]
    now = set(DECLARED.findall(fixture_dump(ast)))
    kept = set(DECLARED.findall(SNAPSHOT.read_text(encoding="utf-8")))
    if now == kept:
        return []
    return [f"{SNAPSHOT.name} is not the fixture as it compiles ({len(now - kept)} declaration(s) new, "
            f"{len(kept - now)} gone); write it again with `--snapshot`"]


def self_test() -> list[str] | None:
    """#51: the gate on its compiled fixture, in every configuration it reads (#175 R3). What it failed
    to refuse, or allowed wrongly; empty when it behaves; None where there is no toolchain."""
    broken: list[str] = []
    for index, (label, sdk_name, flags) in enumerate(CONFIGURATIONS):
        dumped = dump_ast(sdk_name, flags, FIXTURES)
        if dumped is None:
            return None
        ast, code = dumped
        if code != 0:
            return [f"({label}) the fixture does not type-check: {ast[-500:]}"]
        refused = problems(references(ast))
        if index == 0:
            broken += _snapshot_drift(ast)
        broken += [f"({label}) {file}: {phrase} was not refused" for file, phrase in sorted(FIXTURE_REFUSALS)
                   if not any(line.startswith(f"{file}:") and phrase in line for line in refused)]
        broken += [f"({label}) refused what it must allow: {line}" for line in refused
                   if not any(line.startswith(f"{file}:") and phrase in line for file, phrase in FIXTURE_REFUSALS)]
    return broken


def _host() -> str:
    """The operating system the gate runs on. A Mac is the gate's authoritative host (#175 R1)."""
    return platform.system()


def write_snapshot() -> int:
    """`--snapshot`: write the fixture's dump where the flow tests read it."""
    _, sdk_name, flags = CONFIGURATIONS[0]
    dumped = dump_ast(sdk_name, flags, FIXTURES)
    if dumped is None or dumped[1] != 0:
        print("client-decls: the fixture does not compile here, so no snapshot was written")
        return 1
    SNAPSHOT.write_text(fixture_dump(dumped[0]), encoding="utf-8")
    print(f"client-decls: wrote {SNAPSHOT.relative_to(ROOT)}")
    return 0


def _no_toolchain() -> int:
    """No Xcode toolchain. A Mac is where this gate is authoritative (#175 R1, gap G-10): the text pins
    cannot see the routes D-180 and D-181 moved onto the compiled module, so a skip there would pass
    them unread, and it fails instead. Any other host says it skipped."""
    if _host() == "Darwin":
        print("client-decls FAIL: no Xcode toolchain (xcrun) on this Mac, the gate's authoritative host; it "
              "does not skip here (#175)")
        return 1
    print("client-decls SKIPPED NO-ENVIRONMENT: no Xcode toolchain (xcrun) on PATH")
    return 0


def main() -> int:
    expected = {path.name for path in CLIENT.rglob("*.swift")}
    broken = self_test()
    if broken:
        for line in broken:
            print(f"client-decls FAIL (self-test, scripts/client_decl_fixtures): {line}")
        print("  The gate no longer refuses what it exists to refuse (#51); its PASS below would mean nothing.")
        return 1
    bad: list[str] = []
    totals: list[str] = []
    for label, sdk_name, flags in CONFIGURATIONS:
        dumped = dump_ast(sdk_name, flags)
        if dumped is None:
            return _no_toolchain()
        ast, code = dumped
        if code != 0:
            print(f"client-decls FAIL: the client does not type-check ({label}), so this gate "
                  "cannot see what it would compile to")
            print(ast[-2000:])
            return 1
        found = references(ast)
        missing = expected - set(found)
        if missing:
            print(f"client-decls FAIL ({label}): {sorted(missing)} produced no tree. A dump that "
                  "stops early leaves files unchecked while everything else still passes")
            return 1
        bad += [f"({label}) {line}" for line in problems(found)]
        bad += [f"({label}) a permission no longer matches anything, so its rule may have gone quiet "
                f"(the W2 review's R3): {line}" for line in unseen_permissions(found)]
        if "release" in label:
            bad += [f"({label}) {line}" for line in release_problems(found)]
        totals.append(f"{label}: {sum(len(v) for v in found.values())}")
    for line in bad:
        print(f"client-decls FAIL: {line}")
    if bad:
        print("  D-126: what the compiler binds, not what the source spells (W-122).")
        return 1
    print(f"client-decls PASS: {len(expected)} client file(s) in {len(CONFIGURATIONS)} "
          f"configuration(s) -- {'; '.join(totals)}")
    return 0


if __name__ == "__main__":
    sys.exit(write_snapshot() if sys.argv[1:] == ["--snapshot"] else main())
