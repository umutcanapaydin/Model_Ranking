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
   refused by absence, so a declaration of a module nobody has listed is refused too; a class
   reached by name is gap G-12. `UIKit` and
   `CoreFoundation` are allowlisted SYMBOL by symbol: both arrive through a re-export, and
   `CoreFoundation` whole carries sockets.
2. **Capability rules inside the allowed modules.** Foundation and SwiftUI carry the ways text
   leaves a phone, so those are named, as lists of the symbols each refuses: the network outside
   `EngineClient.swift`, the file system outside the two stores, and sharing, hand-off, shared
   storage and logging in any file. A symbol the lists do not name is not refused.

What the client keeps on the phone is held in part by the compiled gate and the text pins: see
INV-62, INV-63, INV-64, INV-66, INV-67, INV-75, INV-76, INV-85 and INV-89 in
`docs/security-invariants.md`, whose gaps name what is not held.

The text gate in `tests/unit/test_router_hints.py` stays: it runs in every lane, including the ones
with no Xcode, and this one runs where the toolchain is. Neither is the whole check.

**What this gate does NOT do** (M16-W1 review, measured):

- It scopes by FILE, not by data, with two exceptions. A function declared in `EngineClient.swift`
  resolves in `main`, and `main` is not capability-checked, so a relay there that any file can call
  passes (B19); the file system is whole inside `FrontDoor.swift`, so a write to the temporary
  directory from there passes too (B31). What a file does with a capability it owns is for review
  and the tests. The first exception is the two privacy sinks (#85, D-180, `_SinkReach`); the second
  is a served number (#60, D-181, `_Flow`). Since #242 (D-214) both are allowlists: a sink file references
  only its own Foundation list, the code a sink runs only `SINK_RUNS_ALLOWED`, and a constant of another
  file only when `SINK_CONSTANT_TYPES` admits its type; a served number meets only what `SERVED_MAY_MEET`
  and its rules admit. What each still does not hold is G-1 and G-2 (INV-66, INV-76 in
  `docs/security-invariants.md`); every refusal the fixture made before #242 is pinned
  (`PINNED_REFUSALS`).
- The two stores' URLs: since #242 a store makes a URL only from the file manager's folders
  (`STORE_FOLDER_MAKERS`) or by a function of its own file not generic over it, reads only its own `url`
  (`STORE_READS`), and takes a URL parameter only in an initialiser `PROVENANCE` keeps to its file; since
  #246 a URL initialiser or decode by name is refused there, and `FrontDoor.swift`'s Foundation
  declarations are listed (`STORE_FOUNDATION_ALLOWED`). What is not held is G-13.
- The kept answers' file (#297, INV-67): `StandingsStore.keep` is refused outside `ContentView.load()`, both
  matched by their full names (#322), and a kept answer's type outside its files when a decode's generic
  substitution gives a `Decodable` parameter that type, read through every `typealias` the dump declares,
  explicit or inferred, by its `type=` (#322), or a type whose synthesised decoder or enum case holds one;
  or when its initialiser, `init(from:)` included, is called. A decode through an existential (`any
  Decodable`) is refused in every file, since its type cannot be read (#322). Not held: a decode through a
  helper whose parameter is constrained only by a protocol of the app's own that refines `Decodable`, which
  prints no `Decodable`, directly or as an existential of that protocol; and an alias of a generic type's
  member (`Box<T>.Item`), which the dump does not print with its `type=`.
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

import hashlib
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterator

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
#: The M21-W3 review's M2: an initialiser whose first label is `contentsOf:` or `url:`, whatever class
#: declares it; another label is not held (G-14).
CONTENTS_OF = re.compile(r"\.init\((?:contentsOf|url):")

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

#: #246 (G-13, the M21-W3 review's round 3; the backlog-gates review round 1's M2): a store reads with
#: `Data(contentsOf:)`, which fetches an `https` address as readily as a file, so the Foundation
#: declarations the gap register's own file may reference are listed, each by the path the compiler
#: resolves (measured on the shipping client, the four configurations, 2026-10-14). Any other one is
#: refused by absence, a URL parse strategy or format style among them, so a new one is a reviewed edit.
#: `StandingsStore.swift` is a privacy sink, held so by `SINK_FOUNDATION_ALLOWED`.
STORE_FOUNDATION_ALLOWED: dict[str, frozenset[str]] = {
    "FrontDoor.swift": frozenset({
        "CharacterSet.newlines", "CharacterSet.whitespaces", "CharacterSet.whitespacesAndNewlines",
        "Data.init(contentsOf:options:", "Data.write(to:options:", "Date.init(",
        "FileManager.SearchPathDirectory.applicationSupportDirectory", "FileManager.SearchPathDomainMask.userDomainMask",
        "FileManager.createDirectory(at:withIntermediateDirectories:attributes:", "FileManager.default",
        "FileManager.temporaryDirectory", "FileManager.urls(for:in:",
        "JSONDecoder.decode(_:from:", "JSONDecoder.init(", "JSONEncoder.encode", "JSONEncoder.init(",
        "Locale.init(identifier:", "NSData.WritingOptions.atomic", "NSData.WritingOptions.completeFileProtection",
        "StringProtocol.components(separatedBy:", "StringProtocol.lowercased(with:", "StringProtocol.trimmingCharacters(in:",
        "URL.appendingPathComponent", "URL.appendingPathComponent(_:isDirectory:", "URL.deletingLastPathComponent(",
        "URL.isFileURL", "URL.made", "URL.setResourceValues", "URLResourceValues.init(",
        "URLResourceValues.isExcludedFromBackup",
    }),
}
#: #242 (G-13; the backlog-gates review rounds 2 and 3, M1; #276): what may make a URL in each store, each by the
#: declaration the compiler resolves (measured on the shipping client, the four configurations, 2026-10-21): the
#: file manager's folders, and a component appended to one or removed. A URL a store makes any other way is
#: refused: an initialiser, a decode, a generic function of its own over the URL it returns (its type given,
#: inferred, or through a `typealias`, which `_aliases` reads), a cast, or a call into another file. A function the
#: store's own file declares, not generic over it, is admitted: its own body is held by this rule. Each entry is
#: seen on the shipping client or reported.
STORE_FOLDER_MAKERS: dict[str, frozenset[str]] = {
    file: frozenset({"Foundation.FileManager.urls(for:in:", "Foundation.URL.appendingPathComponent",
                     "Foundation.URL.appendingPathComponent(_:isDirectory:", "Foundation.URL.deletingLastPathComponent("})
    for file in ("FrontDoor.swift", "StandingsStore.swift")
}
#: #242 (G-13): what each store reads with `Data(contentsOf:)` (or any initialiser `CONTENTS_OF` matches): its own
#: `url`, the one property its initialiser sets, and only that (the #276 shape, a URL bound to `url` between the
#: guard and the read, is another declaration). Each is seen on the shipping client or reported.
STORE_READS: dict[str, str] = {
    "FrontDoor.swift": "GapRegisterStore.url",
    "StandingsStore.swift": "StandingsStore.url",
}
#: A symbol that makes a URL by its own name: an initialiser of a URL type, or a decode of one. Refused in
#: both stores, the privacy sink's list notwithstanding (it lists `URL.init(string:` for the engine client).
URL_MADE_BY_NAME = re.compile(r"^(?:URL|NSURL)\.(?:init\(|decoded\b)")

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
#: The M21-W3 review's K1 (#241): symbols that reach a value, a class or a selector by name, past every
#: declaration rule here. The client uses none, so each listed symbol is refused outright; any other
#: by-name route is not held (G-12; see INV-62).
BY_NAME = (
    "NSExpression",
    "NSPredicate",
    "NSObject.value(forKey",
    "NSObject.value(forKeyPath",
    "NSObject.setValue(",
    "NSObject.perform(",
    "Mirror",
    "objc_",
    "class_",
    "method_",
    "NSClassFromString",
    "NSSelectorFromString",
)
#: #242 (G-12; the M21-W3 review's round 2, B3): a value, a class or a selector reached by name, matched by what
#: the declaration takes rather than by who declares it: an argument labelled for a key or a selector (`forKey:`,
#: `forKeyPath:`, `forKeys:`, `forUndefinedKey:`, `selector:`, `aSelector:`), a base name that takes keys
#: (`setValuesForKeys`), and the class-by-name entry points. `Selector.init` and `responds(to:)` are declared in
#: `ObjectiveC`, which the module rule refuses whole. Each match is refused unless `BY_NAME_ALLOWED` names it.
BY_NAME_LABEL = re.compile(r"[(:](?:forKey|forKeyPath|forKeys|forUndefinedKey|selector|aSelector):|"
                           r"ForKey(?:s|Path)?(?:\(|$)|^Bundle\.(?:classNamed|principalClass)\b")
#: #242, the security review's M3: a key labelled `key:` or `keyPath:` on a Foundation declaration
#: (`NSSortDescriptor(key:ascending:)`), and, read from the reference's type rather than its label, a declaration
#: that takes a `Selector` (`Thread.detachNewThreadSelector(_:toTarget:with:)`, `RunLoop.perform(_:target:…)`).
FOUNDATION_KEY_LABEL = re.compile(r"[(:](?:key|keyPath):")
TAKES_A_SELECTOR = re.compile(r"\bSelector\b")
#: #242 (G-12): the declarations the by-name labels match that the client may reference, matched whole, each with its
#: reason (measured on the shipping client, the four configurations, 2026-10-21); each is seen there or reported.
BY_NAME_ALLOWED: dict[str, str] = {
    "Swift.KeyedDecodingContainer.decode(_:forKey:": "a Codable container's key: a coding key of the app's own type",
    "Swift.KeyedDecodingContainer.decodeIfPresent(_:forKey:": "a Codable container's key: a coding key of the app's own type",
    "Foundation.URL.resourceValues(forKeys:": "#314: the standings store reads its own file's size by a resource key",
}

#: #85 (D-180): the two privacy sinks, into which the file scope above cannot see (the M17 closure's
#: P2). What the rules below refuse is the shapes the fixture holds; see INV-66 (G-1).
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
#: The M21-W3 review's B2: what `PROVENANCE` holds by an initialiser's name alone, whatever its labels:
#: a routed outcome, whose surface is what the recommendation request sends, so no other file builds
#: one; what the router and the answer plan put in its surface is gap G-11 (INV-64).
PROVENANCE_BY_TYPE: dict[str, tuple[set[str], str]] = {
    "RoutingOutcome.init(": (
        {"Router.swift", "AnswerPlan.swift"},
        "only the router and the answer plan build a routed outcome; its surface is what the engine is asked"),
    # #297 (the #288 security re-review's R-m1): what `StandingsStore.keep` writes is built only by a decode
    # (`KEPT_ANSWER_TYPES`), never by an initialiser, so a typed question cannot become one by name.
    "Recommendation.init(": (
        set(), "only a decode builds an answer: the engine's, or the one the store kept (#297)"),
    "Category.init(": (
        set(), "only a decode builds a surface: the engine's list, or the one the store kept (#297)"),
    # #242 (G-13): a register store built on a URL another file chose, the engine's address among them, by any of its
    # initialisers; the app reaches it through `GapRegisterStore.onDevice` only.
    "GapRegisterStore.init(": (
        {"FrontDoor.swift"}, "only the register's own file builds its store, on the one place it keeps the register"),
    "KeptAnswer.init(": (
        {"StandingsStore.swift"}, "only the store builds a kept answer, from what the engine sent (#297)"),
}
KEPT_TYPES = {symbol.split(".")[0] for symbol in (*PROVENANCE, *PROVENANCE_BY_TYPE)}

#: #297 (the #288 security review's MJ1, D-206 clause 4): declarations only one function may call, as
#: `(file, type, function)`, each with why. A kept answer is written to `answers.json` only by the load path,
#: with the answer the engine has just sent; `keep` called anywhere else is refused, in that file or another.
CALLED_ONLY_IN: dict[str, tuple[tuple[str, str, str], str]] = {
    "StandingsStore.keep": (
        ("ContentView.swift", "ContentView", "load()"),
        "only the load path keeps an answer, the one the engine has just sent"),
}
#: #297 (R-m1, probe P5): the types `keep` writes, and the files that may decode one, each with why. A type
#: whose synthesised decoder decodes one of them holds it (`CategoryList`), and is decoded only where it is:
#: the synthesised decoder runs only inside that decode. A decode is a call whose generic substitution gives
#: a `Decodable` parameter a type that names one (`[Category]`, `Recommendation?`), or a reference to the
#: type's `init(from:)`.
KEPT_ANSWER_TYPES: dict[str, tuple[set[str], str]] = {
    "Recommendation": (
        {"EngineClient.swift", "KeptAnswers.swift"},
        "only the engine client decodes the engine's answer, and `KeptAnswers.swift` the one the store kept"),
    "Category": (
        {"EngineClient.swift", "KeptAnswers.swift"},
        "only the engine client decodes the engine's surfaces, and `KeptAnswers.swift` the list the store kept"),
    "KeptAnswer": (
        {"StandingsStore.swift"},
        "only the store reads back the answers it kept"),
}
#: A generic substitution, printed after a declaration's path: its signature, then each parameter's type.
SUBSTITUTION = re.compile(r'\[with \(substitution_map generic_signature=<([^>]*)> ([^"]*?)\)\]')
#: #322 (M1): a `typealias`, explicit or one the compiler inferred for an associated type, by its full name
#: (`ProbeShape.Item`) and the type it names. A substitution prints the alias, not the type.
TYPEALIAS = re.compile(r'^ *\(typealias [^"]*"[^"]*" interface_type="([\w.]+)\.Type"[^\n]*? type="([^"]*)"',
                       re.MULTILINE)
#: #322 (M1): an enum case with a payload: its synthesised decoder is printed untyped, so the payload's types
#: say what the enum holds.
CASE_PAYLOAD = re.compile(r'^ *\(enum_element_decl (?!implicit)[^"]*"[^"]*" interface_type="\([^"]*?\.Type\) -> '
                          r'\((.*)\) -> [^"]*"')
#: #322 (M1): a substitution whose type is an existential, which the gate cannot read.
EXISTENTIAL = re.compile(r"^(?:any|some)\b|@opened\b")
#: The kept-type key a decode through an existential stands under: it may be any of them.
ANY_KEPT = "*"
#: #322 (M3): a reference to an app type's `init(from:)`, its synthesised one included, which has no location.
INIT_FROM = re.compile(r'decl="main\.\(file\)\.([\w.]+?)(?: extension)?\.init\(from:\)(?:@[^"]*)?"')
#: #322 (N1): the declarations that make a type's full path, and a function's full name (`load(later:)`).
OWNER = re.compile(r'^ *\((struct_decl|class_decl|enum_decl|extension_decl|actor_decl|protocol)\b[^"]*"([\w.]+)"')
FULL_FUNCTION = re.compile(r'^ *\((?:func_decl|constructor_decl) [^\[]*range=\[[^\]:]+:\d+:\d+[^"]*"([^"]+)"')


def _provenance(symbol: str) -> tuple[set[str], str] | None:
    """The files allowed to call `symbol`, and why, if `PROVENANCE` or `PROVENANCE_BY_TYPE` holds it."""
    if symbol in PROVENANCE:
        return PROVENANCE[symbol]
    return next((entry for prefix, entry in PROVENANCE_BY_TYPE.items() if symbol.startswith(prefix)), None)

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
#: was given (`select`'s guard on the engine's list is INV-70, a text pin; G-14). The surface itself
#: leaves the phone by design (D-168 note 9, D-126).
REQUEST_SOURCES: dict[str, set[str] | None] = {
    "ContentView.budget": None,
    "ContentView.task": {"RoutingOutcome.categoryID", "ContentView.select(_:).id"},
}
#: The M21-W3 review's B2: each allowed source exactly, as the declarations the assigned expression
#: names: a routed outcome's surface only through `apply`'s own `outcome` parameter (a routed outcome
#: is built only where `PROVENANCE_BY_TYPE` allows), or `select`'s id.
REQUEST_SOURCE_SHAPES: dict[str, list[re.Pattern[str]]] = {
    "ContentView.task": [re.compile(r"^ContentView\.apply\([\w:]*\)\.outcome\|RoutingOutcome\.categoryID$"),
                         re.compile(r"^ContentView\.select\(_:\)\.id$")],
}
#: #244 (the M21-W3 review's round-2 B2; the backlog-gates review round 1's M1): the members of the engine client
#: each file other than its own may reach, each matched whole (measured on the shipping client, the four
#: configurations, 2026-10-14). Anything else on it, an initialiser, a subscript, or a member whose name
#: begins like a listed one, added there or in an extension elsewhere, is a door past `REQUEST_ARGUMENTS`,
#: so it is refused until it is listed here by a reviewed edit.
ENGINE_CLIENT_REACHABLE: dict[str, frozenset[str]] = {
    "ContentView.swift": frozenset({"EngineClient.init(", "EngineClient.baseURL", "EngineClient.boards(",
                                    "EngineClient.categories(", "EngineClient.recommendation(task:budget:"}),
    "Models.swift": frozenset({"EngineClient.maxStandingsBytes"}),
}
#: A declaration's other names: a `@State` property's storage and its binding are the property.
REQUEST_ALIASES = {"ContentView._task": "ContentView.task", "ContentView.$task": "ContentView.task"}

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
    ("Uncertainty.swift", "fact", "anchoredFact"): "D-143: a pick's fact restated out of 100 (#171)",
    ("Uncertainty.swift", "fact", "distanceOutOf100"): "D-143: a fact's distance from the leader, out of 100 (#171)",
    ("Uncertainty.swift", "fact", "scoreOutOf100"): "D-143: a fact's score against the served anchor (#171)",
}
#: #242 (G-2, INV-76): what a served number may meet, by the declaration of another module the compiler resolves
#: and the number's role there (`receiver` or `argument`), each with its reason. `None` admits it in any file; a
#: set admits it only in those `(file, function)` places (measured on the shipping client, the four
#: configurations, 2026-10-21). Anything else a served number meets, outside the places `ARITHMETIC_PERMITTED`
#: names, is refused (`_meets`), so a new operation on one is a reviewed edit; every entry, in every place it
#: names, is seen on the shipping client or reported. The arithmetic rule still judges the operators and numeric
#: methods it names; this rule judges every other declaration. What the app's own code does with a served number
#: is followed by `_Flow` and judged where it meets one of these.
_Places = frozenset[tuple[str, str]] | None
SERVED_MAY_MEET: dict[tuple[str, str], tuple[_Places, str]] = {
    # A test reads a number and changes none (a comparison operator is admitted by rule, `SERVED_MAY_MEET_BY_RULE`).
    ("Swift.ClosedRange.contains", "argument"): (frozenset({("Uncertainty.swift", "evidenceBreadth")}),
                                                 "a comparison: whether a range of the app's own holds a board's age"),
    ("Swift.Double.isFinite", "receiver"): (None, "a test: whether it is a number at all"),
    # Display: the number written as it is.
    ("Swift.DefaultStringInterpolation.appendInterpolation", "argument"): (None, "display: written into text"),
    ("SwiftUICore.LocalizedStringKey.StringInterpolation.appendInterpolation", "argument"): (
        None, "display: written into a localised text"),
    ("Swift.String.init(_:", "argument"): (
        frozenset({("Language.swift", "number"), ("Language.swift", "wholeNumber"), ("Notices.swift", "staleSentence")}),
        "display: the number as text, and the sources' ages listed"),
    # Passed along unchanged: the flow follows what is passed (`_Flow`); a method that hands each element to a
    # closure is admitted by rule (`SERVED_PASSES_ELEMENTS`).
    ("Swift.??", "argument"): (None, "passed along: the served number, or a default of the app's own"),
    ("Swift.Array.subscript(_:", "receiver"): (frozenset({("Notices.swift", "staleSentence")}),
                                               "passed along: the freshest source's age, written into its sentence"),
    ("Swift.Sequence.sorted(", "receiver"): (frozenset({("Notices.swift", "staleSentence")}),
                                             "ordered, which `SORTS_PERMITTED` counts per file: the sources' ages"),
    # Only where the shipping client needs it, each place named.
    ("Swift.Double.init(_:", "argument"): (frozenset({("Language.swift", "number")}),
                                           "display: a whole count checked against the range a sentence may show"),
    ("Swift.Int.init(_:", "argument"): (frozenset({("Language.swift", "wholeNumber")}),
                                        "display: a number `rounded()` has shown to be whole, written without decimals"),
    ("Swift.FloatingPoint.rounded(", "receiver"): (
        frozenset({("Language.swift", "wholeNumber"), ("Router.swift", "money")}),
        "display: whether a number is whole (`wholeNumber`), and a price of a dollar or more shown to the dollar "
        "(`money`, REQ-CMP-002)"),
    ("Foundation.NSNumber.init(value:", "argument"): (frozenset({("Scores.swift", "priceTag")}),
                                                      "display: the price handed to its number formatter"),
    ("Swift.Set.init(_:", "argument"): (frozenset({("AnswerPlan.swift", "disclosures")}),
                                        "counted: whether two rows share a place (a tie notice)"),
}
#: #242 (G-2): what a served number may meet by rule, whatever type declares it, each rule with its reason: a
#: comparison operator of the standard library as an argument, which reads a number and changes none; and as a
#: receiver, a count, an index range or a test for emptiness (`COUNTING`'s members) and `enumerated()`, which the
#: M21-W3 review's M1 rules are not served numbers (how many there are, and a row number beside each). And
#: `SERVED_PASSES_ELEMENTS`, read off the printed declaration as `HANDS_ELEMENTS` reads it.
SERVED_MAY_MEET_BY_RULE: dict[str, tuple[str, re.Pattern[str]]] = {
    # The owner is identifiers joined by single dots, so `Comparable...<`, a range, is no comparison.
    "a comparison": ("argument", re.compile(r"^Swift\.(?:\w+(?:\.\w+)*\.)?(?:<|>|<=|>=|==|!=)$")),
    "a count or a row number": ("receiver", re.compile(r"^Swift\.[\w.]+\.(?:count|indices|isEmpty|underestimatedCount|"
                                                       r"startIndex|endIndex|enumerated\()$")),
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
#: #242 (D-214 clause 1, no loosening): every refusal the fixture made before #242 turned the deny-lists into
#: allowlists, one per line: `all` or `release` (the Release configurations only), then (#375) its key, tab-separated:
#: the file, the planted line (the fixture's source line it is made on, stripped; `-` for a refusal made on no line),
#: which of the file's identical lines that is (0 for none), and the refusal's text after its file and line number. A
#: line moved by an insertion keeps its key. The self-test fails in any configuration that no longer makes one of them,
#: so a rule rewritten as an allowlist cannot refuse less than the list it replaced. Lines are added, never removed.
PINNED_REFUSALS = ROOT / "tests" / "unit" / "data" / "client_decl_refusals_before_242.txt"
#: #375: the pin as it was made before #242, its first `PINNED_COUNT` lines, by their SHA-256. A pin edited, cut,
#: reordered or regenerated fails the self-test unless every one of those lines is still there as it was.
PINNED_COUNT = 183
PINNED_SHA256 = "b05b262f704b6d27af859d063708f5259bc27ef791529b0e5cf43414b80abeef"
#: #375: a refusal's file, its line (none for a refusal made on no line), and its text.
REFUSAL_PLACE = re.compile(r"^(\w+\.swift)(?::(\d+))?: (.+)$", re.DOTALL)
_PinKey = tuple[str, str, int, str]
#: What the fixture must produce, as (file, a phrase the refusal carries).
FIXTURE_REFUSALS = {
    ("ContentView.swift", "URLSession"), ("ContentView.swift", "URL.decoded"),
    # #246 (G-13): a store makes a URL from text and loads it.
    ("FrontDoor.swift", "a store makes a URL only"),
    # #244: round two's twins of the surface.
    ("ContentView.swift", "a key path to `ContentView.task`"), ("ContentView.swift", "EngineClient.subscript"),
    # The backlog-gates review round 1's M1 and M2: an initialiser and a lookalike member of the engine client, and
    # a store's parse strategy.
    ("ContentView.swift", "EngineClient.init(asking:"), ("ContentView.swift", "EngineClient.baseURLSender"),
    ("FrontDoor.swift", "URL.ParseStrategy"), ("Detail.swift", "a member of the engine client off the list"),
    # The relays above reach the engine client's members too, which #244's list refuses as well.
    ("Detail.swift", "EngineClient.localDefault"), ("StandingsStore.swift", "a member of the engine client off the list"),
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
    # The M21-W3 review's B1: Foundation's process-wide state in a sink, and objects another file holds
    # in constants, read by a sink.
    ("EngineClient.swift", "Thread.main"), ("EngineClient.swift", "ProcessInfo.processName"),
    ("EngineClient.swift", "OperationQueue.main"), ("EngineClient.swift", "NSTimeZone.default"),
    ("EngineClient.swift", "reads `fixtureScreenBox`"), ("EngineClient.swift", "reads `box`"),
    ("EngineClient.swift", "Foundation.NSMutableString"),
    # Each plant above meets the sink's Foundation list, and the process-wide state the code a sink
    # runs may not use, more than once.
    ("EngineClient.swift", "not on the list of Foundation declarations"), ("EngineClient.swift", "Foundation's shared state"),
    # B2: the surface's twins: its wrapper's storage, a helper's outcome, the request method as a value.
    ("ContentView.swift", "ContentView._task"), ("ContentView.swift", "used as a value"),
    ("Detail.swift", "builds RoutingOutcome"), ("Detail.swift", "extends `RoutingOutcome`"),
    # M2 and K1 (#241): a mutable class's URL initialiser, and an expression evaluated by name.
    ("ContentView.swift", "NSMutableArray.init(contentsOf"), ("ContentView.swift", "NSExpression"),
    # Past the review's fix: reflection, and the runtime's associated objects carrying the reader's words
    # from the screen to code a sink runs (BY_NAME).
    ("Arithmetic.swift", "Mirror"), ("ContentView.swift", "ObjectiveC.objc_"),
    ("Detail.swift", "objc_getAssociatedObject"),
    # M4: the five rules the fixture lacked (the Release-only hook is in FIXTURE_RELEASE_REFUSALS).
    ("Detail.swift", "UIKit.UIPasteboard"), ("Detail.swift", "CoreFoundation.CFSocketCreate"),
    ("Detail.swift", "builds a path"), ("Detail.swift", "stores something outside the register"),
    # #175 R3: a framework off the allowlist, and text into shared storage (FORBIDDEN).
    ("Imports.swift", "imports `Network`"), ("ContentView.swift", "UserDefaults"),
    # The M21 closure security seat's S6: the runtime, imported and called, off the module allowlist.
    ("Imports.swift", "imports `ObjectiveC`"), ("Imports.swift", "in `ObjectiveC`"),
    # #168: a URL loaded as text, as NSData and by an XML parser is the network too.
    ("ContentView.swift", "String.init(contentsOf"), ("ContentView.swift", "NSData.init(contentsOf"),
    ("ContentView.swift", "XMLParser.init(contentsOf"),
    # #297 (D-206 clause 4): an answer kept outside the load path, from the screen's file and another; probe
    # P5, a surfaces' list decoded from the typed question in the load path, and through a type that holds
    # one; and a surface and a kept answer built by their initialisers.
    ("ContentView.swift", "in `ContentView.keepElsewhere(_:)`, outside the load path"),
    ("Detail.swift", "in `fixtureDetailKeeps(_:)`, outside the load path"),
    ("ContentView.swift", "decodes `Category`,"), ("ContentView.swift", "decodes `CategoryList`, which holds"),
    ("Detail.swift", "builds Category"), ("Detail.swift", "builds KeptAnswer"),
    # #322 (D-209 clause 5; the #297 security review's M1, M3 and N1): P5 behind an inferred associated type, an
    # explicit alias, an enum's payload and an existential; an answer built and decoded outside its files, a kept
    # answer decoded in the screen's file, a surfaces' list decoded by its initialiser's name, a type that holds a
    # type that holds one; and a load path of another name, and in another type of the same simple name.
    ("ContentView.swift", "through the alias `FixtureShape.Item`"),
    ("ContentView.swift", "through the alias `FixtureSurfaces`"),
    ("ContentView.swift", "decodes `FixtureEnvelope`, which holds a `Category`"),
    ("ContentView.swift", "an existential"),
    ("Detail.swift", "builds Recommendation"), ("Detail.swift", "decodes `Recommendation`,"),
    ("ContentView.swift", "decodes `KeptAnswer`,"),
    ("Detail.swift", "decodes `CategoryList`, which holds a `Category`"),
    ("Detail.swift", "decodes `FixtureSurfacesShelf`, which holds a `Category`"),
    ("ContentView.swift", "in `ContentView.load(later:)`, outside the load path"),
    ("ContentView.swift", "in `FixtureElsewhere.ContentView.load()`, outside the load path"),
    # #242 (G-1; the backlog-gates review round 2's K1): constants of an object's type, behind a widened type and of
    # a Swift-module class, read by a sink and by a static `let`'s initialiser it runs; what the code a sink runs
    # references off its list; and a declaration the standings store inherited from the engine client's list.
    ("EngineClient.swift", "reads `fixtureWidened`, a constant"), ("EngineClient.swift", "reads `fixtureWidenedList`, a constant"),
    ("EngineClient.swift", "reads `fixtureHeld`, a constant"), ("EngineClient.swift", "reads `fixtureSharedBuffer`, a constant"),
    ("Detail.swift", "reads `fixtureSharedBuffer`, a constant"), ("Detail.swift", "code a privacy sink runs, references"),
    ("Detail.swift", "references `Swift.ManagedBuffer.header`"), ("Detail.swift", "references `Foundation.Calendar.current`"),
    ("ContentView.swift", "code a privacy sink runs, references"),
    ("StandingsStore.swift", "`Foundation.Bundle.main` is not on the list of Foundation declarations"),
    ("StandingsStore.swift", "`Foundation.Bundle.object(forInfoDictionaryKey:` is not on the list of Foundation declarations"),
    # #242 (G-11): an unlabelled argument, an initialiser's and a subscript's into the engine client, each read; and
    # the unlabelled member the screen may not reach.
    ("ContentView.swift", "the argument 0 (unlabelled) of `EngineClient.ask`"),
    ("ContentView.swift", "the `asking` argument of `EngineClient.init(asking:)`"),
    ("ContentView.swift", "the `asking` argument of `EngineClient.subscript(asking:)`"),
    ("ContentView.swift", "reaches `EngineClient.ask`"),
    # #242 (G-12): by name, matched by the argument's label or as a class-by-name entry point.
    ("ContentView.swift", "reaches a value, a class or a selector by name (an argument labelled"),
    # #242 (G-13): a store's URL made by a generic helper of its own, through an alias, by a cast or by a call into
    # another file; a read of anything but its own `url`; and the register's store built outside its file.
    ("FrontDoor.swift", "makes a URL by `main.fixtureStoreHelper`"), ("FrontDoor.swift", "makes a URL by a cast"),
    ("FrontDoor.swift", "makes a URL by `Foundation.JSONDecoder.decode(_:from:`"),
    ("FrontDoor.swift", "not the store's own `GapRegisterStore.url`"),
    ("StandingsStore.swift", "a store makes a URL only"), ("ContentView.swift", "builds GapRegisterStore"),
    ("FrontDoor.swift", "`GapRegisterStore.fixtureAt(_:)` takes a URL"),
    # #242, the security review's M2: a URL of another file's type, read through a key path.
    ("FrontDoor.swift", "receives a URL, by `FixtureAddressHolder.address`, declared in ContentView.swift"),
    # #242, the security review's round 2: a key path not written in place, in a store and on a served number; and
    # a method referenced on a served number without a call.
    ("FrontDoor.swift", "reads a URL through a key path not written in place"),
    # #374: a URL of another file's type, read through its subscript and through a `@dynamicMemberLookup` wrapper.
    ("FrontDoor.swift", "receives a URL, by `FixtureAddressTable.subscript(_:)`, declared in ContentView.swift"),
    ("FrontDoor.swift", "receives a URL, by `FixtureAddressWrapper.subscript(dynamicMember:)`, declared in ContentView.swift"),
    ("Arithmetic.swift", "`a key path not written in place` on a served position"),
    ("Arithmetic.swift", "`Swift.Int.advanced(by:` on a served position (its receiver) in `shapeMethodHeld`"),
    # #242 (G-12): a selector made from text and asked of an object, both `ObjectiveC`'s (the module rule).
    ("ContentView.swift", "`ObjectiveC.Selector.init(_:` in `ObjectiveC`"),
    # #242, the security review's M3: a selector passed unlabelled, and a key labelled `key:`.
    ("ContentView.swift", "(it takes a `Selector`, whatever its label)"),
    ("ContentView.swift", "(a key labelled `key:` or `keyPath:`)"),
    ("ContentView.swift", "`ObjectiveC.NSObject.responds(to:` in `ObjectiveC`"),
    # #242 (G-2): what a served number meets off its list.
    ("Arithmetic.swift", "`Swift.abs` on a served position"),
    # #242, the security review's B1: met by reference, through a function value and a key path.
    ("Arithmetic.swift", "`a function value` on a served position"),
    ("Arithmetic.swift", "`Swift.Int.magnitude` on a served position (its receiver) in `shapeKeyPathMagnitude`"),
    # #373: a key path walked from a served struct's field, and a method called curried on its type.
    ("Arithmetic.swift", "`Swift.Int.magnitude` on a served position (its receiver) in `shapeStructKeyPath`"),
    ("Arithmetic.swift", "`Swift.Int.magnitude` on a served position (its receiver) in `shapeStructMapMagnitude`"),
    ("Arithmetic.swift", "`Swift.Int.words` on a served position (its receiver) in `shapeStructMapWords`"),
    ("Arithmetic.swift", "`Swift.Int.advanced(by:` on a served position (its receiver) in `shapeCurriedAdvanced`"),
    ("Arithmetic.swift", "`Swift.Int.signum(` on a served position (its receiver) in `shapeCurriedSignum`"),
    # #371: the twins D-218 clause 4 admits include a sort and a `max(by:)`, which the sort rule counts per file.
    ("Arithmetic.swift", "sorts `ranked`"),
    # #371 (D-218 clause 4): a served number handed to a generic over a numeric protocol, and met inside a closure that
    # counts or searches.
    ("Arithmetic.swift", "over the numeric protocol"), ("Arithmetic.swift", "which counts or searches"),
}
#: #175 R3: the rules the fixture holds, each by a phrase a refusal of it carries; these names are what
#: the register's rows cite. Each has at least one
#: refusal the fixture must produce in every configuration, so a change in the compiler's printed
#: layout that silences one of them fails the self-test, wherever the gate runs. Two rules are not
#: here and have no such refusal: the budget's literal `let` (`_literal_let`) and `SINK_SWIFT_REFUSED`.
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
    # The M21-W3 review's M4 and B1, B2, K1.
    "the UIKit symbol list": "UIKit.UIPasteboard",
    "the CoreFoundation symbol list": "CoreFoundation.CFSocketCreate",
    "a path built elsewhere": "builds a path",
    "a second @AppStorage": "stores something outside the register",
    "the Release-only hook": "Debug-only UI test hook",
    "a sink's Foundation list": "not on the list of Foundation declarations",
    "a request method as a value": "used as a value",
    "the router's outcomes": "builds RoutingOutcome",
    "an expression by name": "NSExpression",
    "reflection and the runtime by name": "ObjectiveC.objc_",
    "a URL a store makes from text": "a store makes a URL only",
    "a key path to a request's source": "a key path to `ContentView.task`",
    "the engine client's members": "a member of the engine client off the list",
    # #297 (D-206 clause 4).
    "a kept answer's caller": "outside the load path",
    "a kept answer decoded": "decodes `Category`,",
    # #322 (D-209 clause 5).
    "a kept answer decoded through an alias": "through the alias",
    "a decode through an existential": "an existential",
    # #242 (G-1).
    "a constant a sink reads": "reads `fixtureWidened`, a constant",
    "what the code a sink runs references": "references `Foundation.Calendar.current`",
    "each sink's own Foundation list": "`Foundation.Bundle.main` is not on the list of Foundation declarations",
    # #242 (G-11).
    "every argument into the engine client": "the argument 0 (unlabelled) of `EngineClient.ask`",
    # #242 (G-12).
    "by name, by its label": "reaches a value, a class or a selector by name (an argument labelled",
    "a selector by its type": "(it takes a `Selector`, whatever its label)",
    "a Foundation key by its label": "(a key labelled `key:` or `keyPath:`)",
    # #242 (G-13).
    "what a served number may meet": "`Swift.abs` on a served position",
    "a function value called with a served number": "`a function value` on a served position",
    "a key path on a served number": "`Swift.Int.magnitude` on a served position (its receiver) in `shapeKeyPathMagnitude`",
    "a key path not written in place": "`a key path not written in place` on a served position",
    "a method referenced without a call": "`Swift.Int.advanced(by:` on a served position (its receiver) in `shapeMethodHeld`",
    # #373.
    "a key path walked from a served struct": "`Swift.Int.magnitude` on a served position (its receiver) in `shapeStructKeyPath`",
    "a method called curried on its type": "`Swift.Int.advanced(by:` on a served position (its receiver) in `shapeCurriedAdvanced`",
    "a store's key path not written in place": "reads a URL through a key path not written in place",
    "a store's URL through another file's subscript": "receives a URL, by `FixtureAddressTable.subscript(_:)`",
    "a store's URL makers": "makes a URL by `main.fixtureStoreHelper`",
    "a store's one read": "not the store's own `GapRegisterStore.url`",
    "a store function's URL parameter": "`GapRegisterStore.fixtureAt(_:)` takes a URL",
    # #371 (D-218 clause 4).
    "a served number into a numeric generic": "over the numeric protocol",
    "a served number inside a count or a search": "which counts or searches",
}
#: The M21-W3 review's M4: what the fixture must produce in the Release configurations only.
FIXTURE_RELEASE_REFUSALS = {("ContentView.swift", "Debug-only UI test hook")}
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
OPERATOR = re.compile(r'decl="(?:Swift|Foundation)\.\(file\)\.(\w+)(?: extension)?\.(&?(?:<<|>>|[-+*/%&|^~])=?)(?:"| \[with|@)')
NOT_NUMBERS = {"Bool", "String", "Substring", "StringProtocol", "Character", "Array", "ArraySlice",
               "ContiguousArray", "Set", "Dictionary", "Sequence", "Collection",
               "RangeReplaceableCollection", "Optional"}
#: The end of a resolved function's name. The compiler prints a function whose labels are all `_`
#: by its base name alone (`map [with ...`, `swapAt"`), and any other with its labels. #363: Swift 6.4
#: prints an Objective-C declaration with its header after the name (`sortedArray(comparator:)@<h>:652:1`).
_CALLED = r'(?:\(([^)]*)\))?(?:"| \[with|@)'
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
    # #363: Swift 6.4 expands `@State` in a macro plugin it runs under its own sandbox, and macOS
    # refuses a sandbox inside the test run's offline one (`scripts/offline.sb`): the macro is not
    # expanded and the fixture does not type-check. Only there is the compiler's sandbox dropped;
    # the offline profile still holds the plugin, and `make client-decls` runs with it as before.
    nested = ["-disable-sandbox"] if os.environ.get("MODEL_RANKING_REQUIRE_OFFLINE") == "1" else []
    result = subprocess.run(  # noqa: S603
        [xcrun, "swiftc", "-typecheck", "-dump-ast", *nested, *flags, "-sdk", sdk, *sources],
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
                        *request_facts(ast).items(), *kept_answer_facts(ast).items(), *store_url_facts(ast).items(),
                        *selector_facts(ast).items()):
        found.setdefault(name, set()).update(facts)
    return found


def _app_classes(ast: str) -> set[str]:
    """The classes the app declares, by name."""
    return {m.group(2).split(".")[-1] for line in ast.splitlines()
            if (m := TYPE_DECL.match(line)) and m.group(1) == "class_decl"}


def _holds_an_object(line: str, scope: str, classes: set[str]) -> bool:
    """The M21-W3 review's B1: a constant at file scope or `static` that holds an object (a Foundation
    class, or a class the app declares) is shared state another file can change through it."""
    if " static " not in line and scope != "source_file":
        return False
    typed = TYPE_OF["interface_type"].search(line)
    return typed is not None and (FOUNDATION_OBJECT.match(typed.group(1)) is not None
                                  or typed.group(1).rstrip("?") in classes)


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
    classes = _app_classes(ast)
    for line in ast.splitlines():
        node = NODE.match(line)
        if node:
            depth, kind = len(node.group(1)), node.group(2)
            while stack and stack[-1][0] >= depth:
                stack.pop()
            if kind == "source_file":
                current = pathlib.Path(line.split('"')[1]).name
            elif kind == "var_decl":
                scope = next((k for _, k in reversed(stack) if k in SHARED_SCOPES | LOCAL_SCOPES), "source_file")
                start, named = RANGE_START.search(line), VAR_NAME.match(line)
                if scope in SHARED_SCOPES and start and named and (
                        "writeImpl=stored" in line or _holds_an_object(line, scope, classes)):
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


def selector_facts(ast: str) -> dict[str, set[str]]:
    """#242, the security review's M3: `{file: {"main.<takes a selector>.Module.symbol"}}` for each declaration of an
    allowed module whose reference's type takes a `Selector`, whatever its labels say; a module off the allowlist
    (`ObjectiveC`) is refused whole already."""
    facts: dict[str, set[str]] = {}
    current = ""
    for line in ast.splitlines():
        if line.startswith("(source_file"):
            current = pathlib.Path(line.split('"')[1]).name
        elif (named := DECL.search(line)) and named.group(1) in MODULES - {"main"} \
                and (typed := TYPE_OF["type"].search(line)) and TAKES_A_SELECTOR.search(typed.group(1)):
            facts.setdefault(current, set()).add(f"main.<takes a selector>.{named.group(1)}.{_symbol(named.group(2))}")
    return facts


def _selector_problem(name: str, symbol: str) -> str | None:
    """#242, the security review's M3: a declaration that takes a `Selector`, unless the by-label rule refuses it
    already or `BY_NAME_ALLOWED` names it."""
    fact, _, declared = symbol.partition(">.")
    if fact != "<takes a selector" or declared in BY_NAME_ALLOWED or BY_NAME_LABEL.search(declared.partition(".")[2]):
        return None
    return (f"{name}: `{declared}` reaches a value, a class or a selector by name (it takes a `Selector`, whatever "
            "its label); only the declarations `BY_NAME_ALLOWED` names take one (G-12, #242)")


def store_url_facts(ast: str) -> dict[str, set[str]]:
    """#242 (G-13): in each store, `main.<store url>` for a URL made by anything but `STORE_FOLDER_MAKERS` or a function
    of the store's own file, not generic over it, or received from another file's declaration; and `main.<store
    reads>` for a read of anything but `STORE_READS`' property. Types are read through every `typealias` (#322).
    `main.<store url listed>` and `main.<store reads listed>` record what is admitted, for `unseen_permissions`."""
    aliases = _aliases(ast)
    facts: dict[str, set[str]] = {}
    for root in _tree(ast):
        file = _file_of(root)
        if file not in FILESYSTEM_FILES:
            continue
        for node in root.walk():
            line = _expanded(node.line, aliases)[0] if aliases else node.line
            found = _store_made(file, node, line, aliases) + _store_received(file, node, line) + _store_read(file, node)
            facts.setdefault(file, set()).update(found)
        facts.setdefault(file, set()).update(_store_parameters(file, root, "", aliases))
    return {file: found for file, found in facts.items() if found}


def _store_parameters(file: str, node: _Node, owner: str, aliases: dict[str, str]) -> list[str]:
    """#242 (G-13): a URL-typed parameter of a function or a subscript in a store's file, which lets another file
    choose the address the store's own code builds on. Only an initialiser `PROVENANCE` keeps to this file takes
    one. A closure's parameter is not one another file can pass."""
    if (declared := TYPE_DECL.match(node.line)) is not None:
        owner = declared.group(2).split(".")[-1]
    found: list[str] = []
    if node.kind in ("func_decl", "constructor_decl", "subscript_decl"):
        printed = node.line.split('"')[1] if '"' in node.line else "subscript"
        listed = next((item for item in node.walk() if item.kind == "parameter_list"), None)
        kept = node.kind == "constructor_decl" and (entry := _provenance(f"{owner}.{printed}")) is not None \
            and entry[0] == {file}
        for parameter in (listed.kids if listed and not kept else []):
            typed = TYPE_OF["interface_type"].search(_expanded(parameter.line, aliases)[0] if aliases else parameter.line)
            if (named := PARAMETER.match(parameter.line)) and typed and re.search(r"\bURL\b", typed.group(1)):
                where = ".".join(part for part in (owner, printed) if part)
                found.append(f"main.<store parameter>.{where}|{named.group(1)}@{_line(node) or _range_line(node)}")
    for kid in node.kids:
        if kid.kind != "closure_expr":
            found += _store_parameters(file, kid, owner, aliases)
    return found


def _range_line(node: _Node) -> int:
    found = RANGE_START.search(node.line)
    return int(found.group(2)) if found else 0


def _store_made(file: str, node: _Node, line: str, aliases: dict[str, str]) -> list[str]:
    """#242 (G-13): a call or a cast in a store whose result is or holds a URL, and what made it."""
    if CASTS_URL.match(line):
        return [f"main.<store url>.a cast@{_line(node)}"]
    if not (call := MAKES_URL.match(line)) or not re.search(r"\bURL\b", call.group(1).rsplit("->", 1)[-1]) \
            or node.kind != "call_expr" or not node.kids:
        return []
    callee = _top(node.kids[0])
    head = callee.kids[0] if callee.kind in ("dot_syntax_call_expr", "constructor_ref_call_expr") and callee.kids else callee
    printed = _expanded(head.line, aliases)[0] if aliases else head.line
    if (named := DECL.search(printed)) is None:
        return [f"main.<store url>.an expression the gate cannot name@{_line(node)}"]
    maker = f"{named.group(1)}.{_symbol(named.group(2))}"
    if maker in STORE_FOLDER_MAKERS.get(file, frozenset()):
        return [f"main.<store url listed>.{maker}"]
    own = (place := MAIN_REF.search(printed)) is not None and pathlib.Path(place.group(2)).name == file
    if own and not re.search(r"\[with \(substitution_map[^\n]*\bURL\b", printed):
        return []
    return [f"main.<store url>.`{maker}`@{_line(node)}"]


def _store_received(file: str, node: _Node, line: str) -> list[str]:
    """#242 (G-13): a URL a store reads off a declaration another file declares (not a call, which `_store_made`
    judges): directly, as a member, (the security review's M2) through a key path, whose members it names, or (#374)
    through a subscript, a `@dynamicMemberLookup` one included."""
    if node.kind == "keypath_application_expr" and len(node.kids) >= 2 and (typed := TYPE_OF["type"].search(line)) \
            and re.search(r"\bURL\b", typed.group(1)):
        if _top(node.kids[1]).kind != "keypath_expr":
            # The security review's round 2, M2: a key path bound to a name or handed in, whose members the gate
            # cannot read, is refused (fail closed).
            return [f"main.<store url>.through a key path not written in place@{_line(node)}"]
        return [f"main.<store url>.`{place.group(1)}`, declared in {declared},@{_line(node)}"
                for item in node.kids[1].walk() for place in MAIN_REF.finditer(item.line)
                if (declared := pathlib.Path(place.group(2)).name) != file]
    if node.kind == "subscript_expr" and (typed := TYPE_OF["type"].search(line)) and "->" not in typed.group(1) \
            and re.search(r"\bURL\b", typed.group(1)):
        # #374: a subscript of another file's type, written or (`@dynamicMemberLookup`) implicit, and the members a
        # key path handed to it names.
        named = [node] + [item for kid in node.kids[1:] for item in kid.walk() if item.kind == "member"]
        return [f"main.<store url>.`{place.group(1)}`, declared in {declared},@{_line(node)}"
                for item in named for place in FLOW_REF.finditer(item.line)
                if (declared := pathlib.Path(place.group(2)).name) != file]
    if node.kind not in ("declref_expr", "member_ref_expr") or " implicit " in node.line \
            or (typed := TYPE_OF["type"].search(line)) is None or "->" in typed.group(1) \
            or not re.search(r"\bURL\b", typed.group(1)) or (place := MAIN_REF.search(line)) is None:
        return []
    declared = pathlib.Path(place.group(2)).name
    return [] if declared == file else [f"main.<store url>.`{place.group(1)}`, declared in {declared},@{_line(node)}"]


def _store_read(file: str, node: _Node) -> list[str]:
    """#242 (G-13): a store's `Data(contentsOf:)`, or any initialiser `CONTENTS_OF` matches, on anything but its own
    `url`."""
    if node.kind != "call_expr" or len(node.kids) < 2 or node.kids[1].kind != "argument_list":
        return []
    callee = _top(node.kids[0])
    head = callee.kids[0] if callee.kind == "constructor_ref_call_expr" and callee.kids else callee
    if (named := DECL.search(head.line)) is None or named.group(1) == "main" \
            or not CONTENTS_OF.search(reader := _symbol(named.group(2))):
        return []
    read = ", ".join(sorted(set().union(set(), *(_named(argument) for argument in _operands(node.kids[1])[:1])))) or "a value"
    if read == STORE_READS.get(file):
        return [f"main.<store reads listed>.{read}"]
    return [f"main.<store reads>.{reader}|{read}@{_line(node)}"]


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
#: when a sink calls it, or when a decoder does (a coding witness, called by no name). `_SinkReach`
#: follows each such body through the functions, initialisers and computed properties it reaches and
#: every member a protocol requirement may dispatch to. What it refuses there is the shapes the fixture
#: holds (rule `the code a sink runs`); see INV-66 (G-1).
_LOCAL_KINDS = {"func_decl", "constructor_decl", "destructor_decl", "accessor_decl", "closure_expr"}


#: #172 and the M21-W3 review's B1: process-wide state any file can set that the code a sink runs in
#: another file could read, as a list. Since #242 that code is also held to `SINK_RUNS_ALLOWED`, an allowlist, and
#: this list still runs beside it, so nothing it refused is refused less.
FOUNDATION_SHARED = re.compile(r'decl="(?:Foundation|Swift)\.\(file\)\.((?:Thread|OperationQueue|ProcessInfo|NSTimeZone|'
                               r'TimeZone\.(?:current|autoupdatingCurrent|default)|NSLocale|'
                               r'Locale\.(?:current|autoupdatingCurrent)|CommandLine|NotificationCenter|URLCache|'
                               r'HTTPCookieStorage|URLCredentialStorage|NSUbiquitousKeyValueStore)[\w.]*)')
#: The M21-W3 review's B1 (#242): the Foundation declarations the two privacy sinks' own files may
#: reference, each by the path the compiler resolves. Any other declaration of these modules in a sink
#: file is refused by absence, so a new one is a reviewed edit; an object reached through a listed
#: declaration is not held (G-1). The code a sink runs in another file is checked against `SINK_RUNS_ALLOWED`
#: and `FOUNDATION_SHARED`, and the constants it and the sink read against `SINK_CONSTANT_TYPES` (#242).
#: `ObjectiveC` is on neither list (the M21 closure security seat's S6): it declares the whole runtime
#: (`sel_registerName`, `object_*`, `ivar_*`), and the shipping client resolves nothing in it.
SINK_MODULES = {"Foundation", "CoreFoundation", "Dispatch", "_DarwinFoundation1"}
#: #242 (the backlog-gates review round 2's K1): one list per sink file, each entry seen on the shipping client or
#: reported (`unseen_permissions`), so neither sink inherits what the other needs (measured on the shipping client,
#: the four configurations, 2026-10-21). One shared list gave the standings store `URL.init(string:`, the session
#: and the bundle's settings, which only the engine client uses.
SINK_FOUNDATION_ALLOWED: dict[str, frozenset[str]] = {
    "EngineClient.swift": frozenset({
        "Bundle.main", "Bundle.object(forInfoDictionaryKey:",
        "Code.appTransportSecurityRequiresSecureConnection", "Code.dataNotAllowed", "Code.networkConnectionLost",
        "Code.notConnectedToInternet", "Code.secureConnectionFailed", "Code.timedOut", "_BridgedStoredNSError.code",
        # #363 (owner, 2026-10-20): `EngineClient.read`'s `data.append(byte)` (#56), unchanged; Swift 6.4 binds it
        # to Foundation's `Data.append`, where 6.3 bound the standard library's. A local buffer.
        "Data.append",
        "Data.count", "Data.init(", "Data.reserveCapacity", "Error.localizedDescription",
        "HTTPCookie.AcceptPolicy.never", "HTTPURLResponse.statusCode",
        "JSONDecoder.decode(_:from:", "JSONDecoder.init(",
        "NSURLRequest.CachePolicy.reloadIgnoringLocalCacheData",
        "URL.absoluteString", "URL.appendingPathComponent", "URL.host", "URL.init(string:", "URL.made", "URL.scheme",
        "URLComponents.init(url:resolvingAgainstBaseURL:", "URLComponents.queryItems", "URLComponents.url",
        "URLQueryItem.init(name:value:", "URLRequest.url", "URLResponse.expectedContentLength",
        "URLSession.AsyncBytes.makeAsyncIterator(", "URLSession.AsyncBytes.task", "URLSession.bytes(from:delegate:",
        "URLSession.init(configuration:", "URLSessionConfiguration.ephemeral",
        "URLSessionConfiguration.httpCookieAcceptPolicy", "URLSessionConfiguration.httpCookieStorage",
        "URLSessionConfiguration.httpShouldSetCookies", "URLSessionConfiguration.requestCachePolicy",
        "URLSessionConfiguration.timeoutIntervalForRequest", "URLSessionConfiguration.timeoutIntervalForResource",
        "URLSessionTask.cancel(",
    }),
    "StandingsStore.swift": frozenset({
        "Data.count", "Data.init(contentsOf:options:", "Data.write(to:options:", "NSData.WritingOptions.atomic",
        "Date.init(", "Date.timeIntervalSince",
        "FileManager.SearchPathDirectory.cachesDirectory", "FileManager.SearchPathDomainMask.userDomainMask",
        "FileManager.createDirectory(at:withIntermediateDirectories:attributes:", "FileManager.default",
        "FileManager.temporaryDirectory", "FileManager.urls(for:in:",
        "JSONDecoder.decode(_:from:", "JSONDecoder.init(", "JSONEncoder.encode", "JSONEncoder.init(",
        "URL.appendingPathComponent", "URL.appendingPathComponent(_:isDirectory:", "URL.deletingLastPathComponent(",
        "URL.isFileURL", "URL.made",
        # #314 (D-209 clause 6): the kept answers' file is refused by its size before its bytes are read. A
        # resource value of the store's own file URL; it reads no file content and reaches no network.
        "URL.resourceValues(forKeys:", "URLResourceKey.fileSizeKey", "URLResourceValues.fileSize",
    }),
}
#: #242 (G-1): every declaration of another module the code a privacy sink runs in another file may reference,
#: matched whole, each with the body that needs it (measured on the shipping client, the four configurations,
#: 2026-10-21). Any other, a Foundation object's shared state or a Swift-module class among them, is refused by
#: absence, so a new one is a reviewed edit; each entry is seen on the shipping client or reported. It stands
#: beside `FOUNDATION_SHARED`, which still runs.
SINK_RUNS_ALLOWED: dict[str, str] = {
    "Foundation.Data.count": "`FetchedStandings.init(payload:)` measures the engine's bytes against its ceiling",
    "Foundation.JSONDecoder.decode(_:from:": "`FetchedStandings.init(payload:)` decodes the engine's bytes",
    "Foundation.JSONDecoder.init(": "`FetchedStandings.init(payload:)` decodes the engine's bytes",
    "Foundation.JSONEncoder.OutputFormatting.sortedKeys": "`FetchedStandings.init(payload:)` re-encodes what it decoded",
    "Foundation.JSONEncoder.encode": "`FetchedStandings.init(payload:)` re-encodes what it decoded",
    "Foundation.JSONEncoder.init(": "`FetchedStandings.init(payload:)` re-encodes what it decoded",
    "Foundation.JSONEncoder.outputFormatting": "`FetchedStandings.init(payload:)` re-encodes what it decoded, keys sorted",
    "Swift.Decoder.singleValueContainer(": "`JSONValue.init(from:)`, a served fact's decoding witness",
    "Swift.SingleValueDecodingContainer.decode": "`JSONValue.init(from:)`, a served fact's decoding witness",
    "Swift.SingleValueDecodingContainer.decodeNil(": "`JSONValue.init(from:)`, a served fact's decoding witness",
    "Swift.Encoder.singleValueContainer(": "`JSONValue.encode(to:)`, a served fact's encoding witness",
    "Swift.SingleValueEncodingContainer.encode": "`JSONValue.encode(to:)`, a served fact's encoding witness",
    "Swift.SingleValueEncodingContainer.encodeNil(": "`JSONValue.encode(to:)`, a served fact's encoding witness",
    "Swift.DefaultStringInterpolation.appendInterpolation":
        "`UIText.engineAddress(_:_:)` and `FetchedStandings.init(payload:)` put their own values in text",
    "Swift.DefaultStringInterpolation.appendLiteral":
        "`UIText.engineAddress(_:_:)` and `FetchedStandings.init(payload:)` put their own values in text",
    "Swift.Equatable.==": "`UIText.engineAddress(_:_:)` compares its language argument",
    "Swift.Int.<=": "`FetchedStandings.init(payload:)` compares the payload's size with the ceiling",
}
#: #242 (G-1): the types of a constant (a `let` at file scope, or `static`) another file declares that a privacy
#: sink, or the code it runs, may read. Each holds a value no other file can change; an object, or a value behind
#: a widened type (`Any`, an array of objects, a struct holding one), is refused by absence. Each is seen on the
#: shipping client or reported.
SINK_CONSTANT_TYPES: dict[str, str] = {
    "Int": "`FetchedStandings.init(payload:)` reads the engine client's `maxStandingsBytes`",
    "String": "the standings store reads `KeptAnswers`' two route names",
}
#: A Swift standard-library type that holds process-wide state a sink may not read (B1).
SINK_SWIFT_REFUSED = ("CommandLine",)
#: The M21-W3 review's B1: a constant another file declares, at file scope or `static`, holds shared
#: state when its type is an object's: a Foundation class (its name starts `NS`) or a class the app
#: declares. Read by a sink, it is refused as a `var` is.
FOUNDATION_OBJECT = re.compile(r"^(?:NS\w+|Thread|OperationQueue|ProcessInfo|Bundle|FileManager|NotificationCenter|"
                               r"URLCache|HTTPCookieStorage|URLSession|JSONEncoder|JSONDecoder|NumberFormatter|"
                               r"DateFormatter|Formatter|Scanner)\??$")


class _SinkReach:
    """The second W2 review's B2: the bodies a privacy sink runs, and the shared state they read."""

    def __init__(self, roots: list[_Node]) -> None:
        self.roots = roots
        self.bodies: dict[tuple[object, ...], tuple[str, str, _Node]] = {}
        self.lines: dict[tuple[str, str], list[int]] = {}
        self.members: dict[str, list[tuple[object, ...]]] = {}
        self.mutable: dict[tuple[str, int, int], str] = {}
        #: #242 (G-1): every stored `let` at file scope or `static`, with its type.
        self.constants: dict[tuple[str, int, int], tuple[str, str]] = {}
        self.protocols: set[str] = set()
        self.witnesses: list[tuple[object, ...]] = []
        self.classes = {m.group(2).split(".")[-1] for root in roots for node in root.walk()
                        if (m := TYPE_DECL.match(node.line)) and m.group(1) == "class_decl"}
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
        if shared and ("writeImpl=stored" in node.line or closure or _holds_an_object(node.line, scope, self.classes)):
            self.mutable[key] = named.group(1)
        elif (scope == "source_file" or static) and "readImpl=stored" in node.line and typed is not None:
            self.constants[key] = (named.group(1), typed.group(1))

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
        # #242 (G-1): a constant another file declares, read in a sink itself.
        found += [fact for root in self.roots if _file_of(root) in SINK_FILES
                  for fact in self.constant_reads(_file_of(root), "", root)]
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
            found += self.constant_reads(file, shown, node) + _sink_runs_references(file, shown, node)
            queue += list(self.reached(node))
        return found

    def constant_reads(self, file: str, shown: str, node: _Node) -> list[tuple[str, str]]:
        """#242 (G-1): each constant `node` reads that is not already refused as mutable: its type admitted by
        `SINK_CONSTANT_TYPES` (a fact `unseen_permissions` reads) or refused. A sink's own constants are its own;
        the code a sink runs in another file reads none but an admitted one, its own file's included."""
        found: list[tuple[str, str]] = []
        for item in node.walk():
            for reference in FLOW_REF.finditer(item.line):
                where = (pathlib.Path(reference.group(2)).name, int(reference.group(3)), int(reference.group(4)))
                if where not in self.constants or where in self.mutable or (not shown and where[0] == file):
                    continue
                constant, typed = self.constants[where]
                if typed.rstrip("?") in SINK_CONSTANT_TYPES:
                    found.append((file, f"main.<sink reads constant type>.{typed.rstrip('?')}"))
                else:
                    found.append((file, f"main.<sink reads constant>.{shown}|{constant}|{typed}@{where[0]}"))
        return found


def _symbol(symbol: str) -> str:
    """A resolved symbol as `references` records it: a member added in an extension under its type's name."""
    symbol = re.sub(r"([\w.]+) extension\.", r"\1.", symbol)
    return re.sub(r"(^|\.)extension\.", r"\1", symbol).rstrip(".")


def _sink_runs_references(file: str, shown: str, node: _Node) -> list[tuple[str, str]]:
    """#242 (G-1): each declaration of another module the code a sink runs references: on `SINK_RUNS_ALLOWED` (a
    fact `unseen_permissions` reads), or refused."""
    found: list[tuple[str, str]] = []
    for item in node.walk():
        for module, symbol in DECL.findall(item.line):
            if module == "main":
                continue
            declared = f"{module}.{_symbol(symbol)}"
            found.append((file, f"main.<sink runs uses>.{declared}" if declared in SINK_RUNS_ALLOWED
                          else f"main.<sink runs off list>.{shown}|{declared}"))
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
        if _provenance(symbol) is not None:
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
    """#171: `(enum, case) -> "fact"` for each numeric payload of an enum the client decodes: a kind of
    its own, so only the places that restate a fact may do arithmetic on one (the M21-W3 review's B3)."""
    found: dict[tuple[str, str], str] = {}
    for root in roots:
        for node in root.walk():
            if (named := DECODED_ENUM.match(node.line)) is None or named.group(1) in NOT_SERVED:
                continue
            for element in node.kids:
                if (case := NUMERIC_CASE.match(element.line)) is not None:
                    found[(named.group(1), case.group(1))] = "fact"
                    found[(named.group(1), f"{case.group(1)}(_:)")] = "fact"
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
            found[(decoded, held.group(1))] = "fact"
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
TEXTY_TYPE = re.compile(r"^(?:@lvalue )?(?:inout )?(?:String|Substring|DefaultStringInterpolation|NSString|NSMutableString|"
                        r"Data|AnyHashable|AnyObject|NSNumber|NSValue)\??$|\bAny\b")
#: Text and bytes: the walk enters them only where a number is parsed back out (the M21-W3 review's
#: B3); see INV-76 (G-2).
TEXT_NODE = re.compile(r'\btype="(?:@lvalue )?(?:String|Substring|DefaultStringInterpolation|NSString|NSMutableString|'
                       r'Data)\??"')
#: A number parsed from text or bytes: the numeric types' initialisers from a string, and (the M21-W3
#: review's B3) `NSString`'s number properties, a number formatter, a scanner, `Decimal(string:)` and
#: a JSON decode.
PARSES_NUMBER = re.compile(r'decl="(?:Swift|Foundation)\.\(file\)\.(?:(?:U?Int(?:8|16|32|64)?|Double|Float|Decimal|'
                           r'FixedWidthInteger|BinaryInteger|BinaryFloatingPoint|LosslessStringConvertible)'
                           r'(?: extension)?\.init\((?:_:|string:)|NSString(?: extension)?\.(?:integer|int|double|float|longLong|'
                           r'bool)Value|NumberFormatter(?: extension)?\.number\(from:|Scanner(?: extension)?\.scan|'
                           r'JSONDecoder(?: extension)?\.decode)')
#: A count, an index range or a test for emptiness ends the walk: how many served numbers there are is
#: not one (the M21-W3 review's M1).
COUNTING = re.compile(r'decl="Swift\.\(file\)\.\w+(?: extension)?\.(?:count|indices|isEmpty|underestimatedCount|'
                      r'startIndex|endIndex)[" @]')


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
    if node.kind == "member_ref_expr" and COUNTING.search(node.line):
        # A count is not read as a served number (M1), but for the arguments `_counted` follows (G-2).
        yield from _counted(node)
        return
    if node.kind == "tuple_element_expr" and "field #=0" in node.line and node.kids and (
            '"(offset: Int' in node.kids[0].line or 'type="EnumeratedSequence<' in node.kids[0].line):
        # An `enumerated()` element's offset is a row number, not a served one (M1).
        return
    parses = PARSES_NUMBER.search(node.line) is not None or (node.kind == "call_expr" and bool(node.kids) and any(
        PARSES_NUMBER.search(item.line) for item in node.kids[0].walk()))
    for kid in node.kids:
        if not closures and kid.kind == "closure_expr":
            continue
        if not (text or parses) and TEXT_NODE.search(kid.line):
            continue
        yield from _reach(kid, closures, text or parses)


def _counted(node: _Node) -> Iterator[_Node]:
    """The arguments of the call, operator or subscript a count is taken directly off: a served number
    one of them is given is read. A list bound to a name first is not followed into its count, and nor
    are an element of a list, a closure or a key path mapping one, or text and bytes (#171); see INV-76
    (G-2)."""
    for kid in node.kids:
        if kid.kind in ("closure_expr", "keypath_expr") or TEXT_NODE.search(kid.line):
            continue
        if kid.kind != "argument_list":
            yield from _counted(kid)
            continue
        for argument in kid.kids:
            if not any(item.kind in ("closure_expr", "keypath_expr") for item in argument.walk()):
                yield from _reach(argument, closures=False, text=False)


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
        #: #242, the security review's round 2: every expression called on the spot, so a method referenced and
        #: not called (`let g = x.advanced(by:)`) can be told from one that is.
        self.callees = {id(_top(node.kids[0])) for root in roots for node in root.walk()
                        if node.kind in ("call_expr", "binary_expr", "prefix_unary_expr", "postfix_unary_expr") and node.kids}

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
                found |= self._bound(file, line, int(column), parts[-1])
                if function and (at := self.declared(file, parts[-1], line)) is not None:
                    found |= self.carriers.get(("result", file, at, _base(parts[-1])), set())
                # #173: a subscript's parameter is printed under its getter, `<anonymous>`.
                if len(parts) >= 2 and parts[-2] == "<anonymous>" and (
                        at := self.declared(file, "subscript", line)) is not None:
                    found |= self.carriers.get(("parameter", file, at, "subscript", parts[-1]), set())
                if len(parts) >= 2 and "(" in parts[-2] and (at := self.declared(file, parts[-2], line)) is not None:
                    found |= self.carriers.get(("parameter", file, at, _base(parts[-2]), parts[-1]), set())
        return found

    def _bound(self, file: str, line: int, column: int, name: str) -> set[str]:
        """A name a statement binds: an anonymous closure parameter by its own closure, a condition's or a
        named closure parameter's by its line, and a loop's by the line its `for` starts, up to five lines
        above where the compiler declares it (#173; the M21-W3 review's M1)."""
        if name.startswith("$"):
            return self.carriers.get(("closure", file, line, column, name), set())
        found = set(self.carriers.get(("bound", file, line, name), set()))
        for back in range(6):
            found |= self.carriers.get(("loop", file, line - back, name), set())
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
        return any([_mark(self.carriers, ("loop", file, int(start.group(1)), name), kinds) for name in names])

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
            at = LOCATION.search(closure.line)
            for parameter in listed.kids:
                if (named := PARAMETER.match(parameter.line)) and _numeric(parameter, "interface_type"):
                    # The M21-W3 review's M1: `$0` is keyed by its own closure, where the compiler
                    # declares it, so a served `$0` taints no other closure's.
                    key: tuple[object, ...] = (
                        ("closure", file, int(at.group(2)), int(at.group(3)), named.group(1))
                        if named.group(1).startswith("$") and at else ("bound", file, int(start.group(1)), named.group(1)))
                    changed |= _mark(self.carriers, key, kinds)
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


def _placed(node: _Node, function: str | None = None,
            place: str | None = None) -> Iterator[tuple[_Node, str | None, str | None]]:
    """Every node with the function it is in, as `_scoped` gives it, and (#242, the security review's R1) its place:
    that function, or the computed property whose getter it is in."""
    if named := FUNCTION.match(node.line):
        function = place = named.group(2)
    elif node.kind == "var_decl" and "readImpl=getter" in node.line and (variable := VAR_NAME.match(node.line)):
        place = variable.group(1)
    yield node, function, place
    for kid in node.kids:
        yield from _placed(kid, function, place)


def flow_facts(ast: str) -> dict[str, set[str]]:
    """#60 (G-2): `{file name: {"main.<...>", ...}}`, the arithmetic on served numbers and the sorts
    each file makes, resolved by the compiler and followed to a fixed point, for `problems` to judge."""
    flow = _Flow(_tree(ast))
    flow.run()
    facts: dict[str, set[str]] = {}
    sorts: dict[tuple[str, str, str], int] = {}
    protocols = _numeric_protocols(flow.roots)
    bodies = _predicate_bodies(flow.roots)
    counted: dict[tuple[str, str, str, str, str], set[tuple[int, int]]] = {}
    for root in flow.roots:
        file = _file_of(root)
        for node, function, place in _placed(root):
            arithmetic = _arithmetic(node, flow, function)
            # #242 (G-2): what the arithmetic rule does not judge, the list of what a served number may meet does, in
            # the place it names: a function, or a computed property (the security review's R1).
            for fact in arithmetic or _meets(node, flow, file, function, place):
                facts.setdefault(file, set()).add(fact)
            if (ordering := _ordering(node)) is not None:
                sorts[(file, *ordering)] = sorts.get((file, *ordering), 0) + 1
            # #371 (D-218 clause 4): beside both rules, and whatever they admit.
            where = place or function or "-"
            facts.setdefault(file, set()).update(_numeric_generic(node, flow, protocols, where))
            for method, met, declared, kind in _counts_or_searches(node, flow, bodies):
                counted.setdefault((file, where, method, kind, declared), set()).add((_line(met), _column(met)))
    for (file, method, receiver), count in sorts.items():
        facts.setdefault(file, set()).add(f"main.<sorts>.{method}.{receiver}={count}")
    for (file, where, method, kind, declared), meetings in counted.items():
        allowed, _ = COUNTS_OR_SEARCHES_PERMITTED.get((file, where, method, kind, declared), (0, ""))
        if len(meetings) <= allowed:
            facts.setdefault(file, set()).add(f"main.<counts listed>.{declared}|{method}|{kind}|{where}")
            continue
        facts.setdefault(file, set()).update(f"main.<counts>.{kind}@{line} {declared}|{method}|{allowed} in {where}"
                                             for line, _ in meetings)
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


#: #242 (G-2): what is never a served number's role: a closure, an implicit one, a key path.
_NOT_AN_OPERAND = {"closure_expr", "autoclosure_expr", "keypath_expr"}


#: #242 (G-2): a method that hands each element of a list of served numbers, unchanged, to a closure the flow
#: follows (`HANDS_ELEMENTS`, `_Flow.closure`), or returns one of them as it is; admitted as the receiver. `min`,
#: `max`, `reduce`, `drop`, `prefix` and `sorted` are not here: they choose, combine, cut or order.
SERVED_PASSES_ELEMENTS = re.compile(r'decl="(?:Swift|Foundation)\.\(file\)\.\w+ extension\.(?:map|compactMap|flatMap|'
                                    r'filter|forEach|contains|allSatisfy|first|last|firstIndex|lastIndex)' + _CALLED)


def _operands(listed: _Node | None) -> list[_Node]:
    return [argument.kids[0] for argument in (listed.kids if listed else []) if argument.kind == "argument" and argument.kids]


def _application(node: _Node) -> tuple[_Node, list[_Node], list[_Node]] | None:
    """#242 (G-2): `(the node that names the declaration, its receivers, its arguments)` for a call, a method call,
    an initialiser, an operator, a property read or a subscript; None for any other node."""
    if node.kind == "call_expr" and len(node.kids) >= 2 and node.kids[1].kind == "argument_list":
        callee = _top(node.kids[0])
        if callee.kind == "dot_syntax_call_expr" and callee.kids:
            listed = next((kid for kid in callee.kids[1:] if kid.kind == "argument_list"), None)
            return callee.kids[0], _operands(listed), _operands(node.kids[1])
        if callee.kind == "constructor_ref_call_expr" and callee.kids:
            return callee.kids[0], [], _operands(node.kids[1])
        if callee.kind == "dot_syntax_base_ignored" and (curried := _curried(callee)) is not None:
            return curried, _operands(node.kids[1]), []
        return (callee, [], _operands(node.kids[1])) if callee.kind == "declref_expr" else None
    if node.kind in ("binary_expr", "prefix_unary_expr", "postfix_unary_expr") and len(node.kids) >= 2:
        callee = _top(node.kids[0])
        head = callee.kids[0] if callee.kind == "dot_syntax_call_expr" and callee.kids else callee
        return head, [], _operands(node.kids[1])
    if node.kind in ("member_ref_expr", "subscript_expr") and node.kids:
        return node, [node.kids[0]], _operands(next((kid for kid in node.kids if kid.kind == "argument_list"), None))
    return None


def _curried(callee: _Node) -> _Node | None:
    """#373 (G-2): the method a call names curried on its type, `Int.advanced(by:)(x)`, whose argument is the method's
    receiver: the compiler wraps the method in a thunk whose first parameter is `self`. None for anything else."""
    thunk = next((kid for kid in callee.kids if kid.kind == "autoclosure_expr"), None)
    first = next((m.group(1) for item in thunk.walk() if (m := PARAMETER.match(item.line))), None) if thunk else None
    if first != "self":
        return None
    return next((item for item in thunk.walk() if item.kind == "declref_expr" and " implicit " not in item.line
                 and DECL.search(item.line)), None) if thunk else None


def _walked_from_served(node: _Node, flow: _Flow, file: str, where: str, line: int,
                        permitted: Callable[[str], bool]) -> list[str]:
    """#373 (G-2): a key path walked from the first served number it reaches (`\\Standing.position.magnitude`): each
    later component that names a declaration of another module meets that number as its receiver, whatever the key
    path is applied to."""
    components = next((kid for kid in node.kids if kid.kind == "components"), None)
    kinds: set[str] = set()
    found: list[str] = []
    for component in components.kids if components else []:
        named = DECL.search(component.line)
        if kinds and named is not None and named.group(1) != "main":
            declared = f"{named.group(1)}.{_symbol(named.group(2))}"
            found += [fact for kind in sorted(kinds) if not permitted(kind)
                      if (fact := _meeting(declared, "receiver", kind, file, where, line)) is not None]
        kinds |= _served_operand(flow, component)
    return found


def _served_operand(flow: _Flow, operand: _Node) -> set[str]:
    """#242 (G-2): the served kinds an operand carries, when it is a number (or a list of them) and not a closure."""
    typed = TYPE_OF["type"].search(operand.line)
    if operand.kind in _NOT_AN_OPERAND or typed is None or "->" in typed.group(1) or not NUMERIC_TYPE.search(typed.group(1)):
        return set()
    return flow.carried(operand, closures=False)


def _meeting(declared: str, role: str, kind: str, file: str, where: str, line: int) -> str | None:
    """#242 (G-2): one meeting of a served number with a declaration of another module: None when a rule admits it,
    `main.<meets listed>` when `SERVED_MAY_MEET` does there, and `main.<meets>` to be refused otherwise."""
    if any(role == by and rule.match(declared) for by, rule in SERVED_MAY_MEET_BY_RULE.values()):
        return None
    places, _ = SERVED_MAY_MEET.get((declared, role), (frozenset(), ""))
    if places is None or (file, where) in places:
        return f"main.<meets listed>.{declared}|{role}|{where}"
    return f"main.<meets>.{kind}@{line} {declared}|{role} in {where}"


def _followed(argument: _Node) -> bool:
    """#242, the security review's B1: a closure written in the source, which `_Flow.closure` follows. An implicit
    one (a function or a key path handed by name, `Int.init(truncatingIfNeeded:)`, `\\.magnitude`) is not."""
    top = _top(argument)
    return top.kind == "closure_expr" and " implicit " not in top.line


def _by_reference(argument: _Node, kind: str, file: str, where: str, line: int) -> list[str]:
    """#242, the security review's B1: what a served number meets through a function-typed or key-path argument
    that is not a closure the flow follows: each declaration of another module named in it (a key path's member
    as its receiver), and a function of the app's own handed by name, which the flow does not follow."""
    typed = TYPE_OF["type"].search(_top(argument).line)
    if typed is None or not ("->" in typed.group(1) or "KeyPath<" in typed.group(1)):
        return []
    found: list[str] = []
    for item in argument.walk():
        for module, symbol in DECL.findall(item.line):
            if module == "main":
                item_type = TYPE_OF["type"].search(item.line)
                if item.kind in ("declref_expr", "member_ref_expr") and " implicit " not in item.line \
                        and item_type is not None and "->" in item_type.group(1):
                    found.append(f"main.<meets>.{kind}@{line} main.{_symbol(symbol)}|argument in {where}")
                continue
            role = "receiver" if item.kind == "member" else "argument"
            if (fact := _meeting(f"{module}.{_symbol(symbol)}", role, kind, file, where, line)) is not None:
                found.append(fact)
    return found


def _calls_a_value(node: _Node, flow: _Flow) -> bool:
    """#242, the security review's B1: a call whose callee is a function value, not a function the flow follows: a
    closure written on the spot, or a constant, a variable or a parameter of the app's own holding a function
    (`let f = abs; f(x)`), as `_operator_as_value` treats an operator."""
    callee = _top(node.kids[0])
    if callee.kind in ("closure_expr", "autoclosure_expr"):
        return True
    if callee.kind not in ("declref_expr", "member_ref_expr") or (place := MAIN_REF.search(callee.line)) is None:
        return False
    symbol, path, row = place.group(1), pathlib.Path(place.group(2)).name, int(place.group(3))
    name = _base(re.sub(r"[\w.]+ extension\.", "", symbol).split(".")[-1])
    return not any(row - 3 <= declared <= row for declared in flow.functions.get((path, name), []))


def _met_by_reference(node: _Node, flow: _Flow, file: str, where: str, line: int,
                      permitted: Callable[[str], bool]) -> list[str] | None:
    """#242, the security review's rounds 1 and 2 (B1): a key path applied to a served number (refused when it is not
    written in place, since the gate cannot read it), a method referenced on one without a call (judged as its call
    is: the compiler wraps it in an implicit thunk that calls it), and a function value called with one. None for
    any other node."""
    if node.kind == "keypath_application_expr" and len(node.kids) >= 2:
        applied = [kind for kind in sorted(_served_operand(flow, node.kids[0])) if not permitted(kind)]
        if _top(node.kids[1]).kind != "keypath_expr":
            return [f"main.<meets>.{kind}@{line} a key path not written in place|receiver in {where}" for kind in applied]
        return [fact for kind in applied for fact in _by_reference(node.kids[1], kind, file, where, line)]
    if node.kind == "keypath_expr":
        return _walked_from_served(node, flow, file, where, line, permitted)
    if node.kind == "dot_syntax_call_expr" and id(node) not in flow.callees and node.kids:
        named = next((m for item in node.kids[0].walk() if (m := DECL.search(item.line)) and m.group(1) != "main"), None)
        listed = next((kid for kid in node.kids[1:] if kid.kind == "argument_list"), None)
        kinds = set().union(set(), *(_served_operand(flow, operand) for operand in _operands(listed)))
        if named is None or not kinds:
            return None
        declared = f"{named.group(1)}.{_symbol(named.group(2))}"
        return [fact for kind in sorted(kinds) if not permitted(kind)
                if (fact := _meeting(declared, "receiver", kind, file, where, line)) is not None]
    if node.kind == "call_expr" and len(node.kids) >= 2 and node.kids[1].kind == "argument_list" \
            and _calls_a_value(node, flow):
        kinds = set().union(set(), *(_served_operand(flow, operand) for operand in _operands(node.kids[1])))
        return [f"main.<meets>.{kind}@{line} a function value|argument in {where}" for kind in sorted(kinds)
                if not permitted(kind)]
    return None


def _meets(node: _Node, flow: _Flow, file: str, function: str | None, place: str | None = None) -> list[str]:
    """#242 (G-2, INV-76): a declaration of another module a served number meets, as its receiver or an argument:
    `main.<meets listed>` when `SERVED_MAY_MEET` admits it there (a fact `unseen_permissions` reads), nothing in a
    place `ARITHMETIC_PERMITTED` names or a rule admits, and `main.<meets>` to be refused otherwise. Since the
    security review's B1, by reference too: a key path applied to one, a function or a key path handed to an
    element-passing method in place of a closure the flow follows, and a function value called with one. Since its
    round 2, failing closed: a key path not written in place, which the gate cannot read, is refused, and a method
    referenced on one without a call is judged as its call is. The place is the function or the computed property
    (`_placed`); a ruling's permission is read by the function alone, as the arithmetic rule reads it (R5)."""
    where, line = place or function or "-", _line(node)

    def permitted(kind: str) -> bool:
        return _arithmetic_permitted(file, kind, function or "-")

    if (referenced := _met_by_reference(node, flow, file, where, line, permitted)) is not None:
        return referenced
    if (applied := _application(node)) is None:
        return []
    head, receivers, arguments = applied
    if (named := DECL.search(head.line)) is None or named.group(1) == "main":
        return []
    declared = f"{named.group(1)}.{_symbol(named.group(2))}"
    found: list[str] = []
    for role, operands in (("receiver", receivers), ("argument", arguments)):
        for kind in sorted(set().union(set(), *(_served_operand(flow, operand) for operand in operands))):
            if permitted(kind):
                continue
            if role == "receiver" and SERVED_PASSES_ELEMENTS.search(head.line):
                found += [fact for argument in arguments if not _followed(argument)
                          for fact in _by_reference(argument, kind, file, where, line)]
                continue
            if (fact := _meeting(declared, role, kind, file, where, line)) is not None:
                found.append(fact)
    return found


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


#: #371 (D-218 clause 4, G-2): the numeric protocols of the standard library and SwiftUI, each a way to do arithmetic on
#: a value whose type is a generic parameter, `some` or `any` of it, which no number type the rules read names. A
#: protocol of the app's own that refines one is one too (`_numeric_protocols`).
NUMERIC_PROTOCOLS = frozenset({"Numeric", "SignedNumeric", "AdditiveArithmetic", "BinaryInteger", "FixedWidthInteger",
                               "SignedInteger", "UnsignedInteger", "FloatingPoint", "BinaryFloatingPoint", "Strideable",
                               "VectorArithmetic"})
PROTOCOL_REFINES = re.compile(r'^ *\(protocol [^"]*"(\w+)"[^\n]*?\b(?:requirement_signature|inherits)="([^"]*)"')
#: A generic declaration's substitution, which the compiler prints after its name: `<T where T : Numeric> T -> Int`,
#: and ` some Numeric -> Int` for a `some` parameter.
SUBSTITUTED = re.compile(r"\[with \(substitution_map generic_signature=([^\]]*)\)\]")
#: #371 (D-218 clause 4): the closures that count or search, by the standard library's or Foundation's method they are
#: given to, as the ruling names them. What such a closure returns decides a count, an index, an element or a total, so
#: whatever a served number meets inside one can come back as a new number.
COUNTS_OR_SEARCHES = re.compile(r'decl="(?:Swift|Foundation)\.\(file\)\.\w+(?: extension)?\.(filter|first|firstIndex|'
                                r'lastIndex|last|count|contains|allSatisfy|drop|prefix|reduce)' + _CALLED)
#: #371 (D-218 clause 4): `(file, place, method, kind, declaration met) -> (how many such meetings, the reason)` inside a
#: closure that counts or searches, each in the shipping client (measured, the four configurations, 2026-10-21). Counted
#: per place, so a second meeting there is refused; an entry not seen is reported (`unseen_permissions`). Every other
#: meeting inside such a closure is refused.
COUNTS_OR_SEARCHES_PERMITTED: dict[tuple[str, str, str, str, str], tuple[int, str]] = {
    # The staleness notice (#63 finding 2, D-176): the stale sources' ages it lists, those dated in the future left out,
    # and how many carry no date or a date in the future, counts of sources, never one of their ages.
    ("Notices.swift", "staleSentence", "filter", "number", "Swift.Int.>="): (
        1, "the ages the notice lists: a source dated in the future is left out"),
    ("Notices.swift", "staleSentence", "filter", "number", "Swift.Optional.=="): (
        1, "how many stale sources carry no date"),
    ("Notices.swift", "staleSentence", "filter", "number", "Swift.??"): (
        1, "an undated source read as dated today, so it counts as no future date"),
    ("Notices.swift", "staleSentence", "filter", "number", "Swift.Int.<"): (
        1, "how many stale sources are dated in the future"),
    # D-135's weight: whether any source or row carries a date at all.
    ("Notices.swift", "combinedDisclosure", "contains(where:)", "number", "Swift.Equatable.!="): (
        1, "a stale board is a state when any source is dated, else a property of the board"),
    ("Router.swift", "classifyDisclosures", "contains(where:)", "number", "Swift.Equatable.!="): (
        1, "the staleness notice is the dating note when no row is dated"),
}


def _numeric_protocols(roots: list[_Node]) -> frozenset[str]:
    """#371: `NUMERIC_PROTOCOLS` and every protocol of the app's own that refines one, however many steps away."""
    refines = {m.group(1): set(re.findall(r"\w+", m.group(2))) for root in roots for node in root.walk()
               if (m := PROTOCOL_REFINES.match(node.line))}
    found = set(NUMERIC_PROTOCOLS)
    while grown := {name for name, parents in refines.items() if name not in found and parents & found}:
        found |= grown
    return frozenset(found)


def _numeric_generic(node: _Node, flow: _Flow, protocols: frozenset[str], where: str) -> list[str]:
    """#371 (D-218 clause 4, G-2): a served number handed to a declaration of the app's own that is generic over a
    numeric protocol (a function, a method, an initialiser of a generic type, a `some` parameter), as its receiver or
    an argument, or erased to `any` of one: arithmetic on its `T` is arithmetic no rule can follow."""
    if node.kind == "erasure_expr":
        typed = TYPE_OF["type"].search(node.line)
        over = sorted(set(re.findall(r"\w+", typed.group(1))) & protocols) if typed else []
        kinds = set().union(set(), *(_served_operand(flow, kid) for kid in node.kids)) if over else set()
        return [f"main.<numeric generic>.{kind}@{_line(node)} {over[0]}|`{typed.group(1)}`, an existential in {where}"
                for kind in sorted(kinds) if typed]
    if (applied := _application(node)) is None:
        return []
    head, receivers, arguments = applied
    named, substituted = DECL.search(head.line), SUBSTITUTED.search(head.line)
    if named is None or named.group(1) != "main" or substituted is None:
        return []
    over = sorted(set(re.findall(r"\w+", substituted.group(1))) & protocols)
    if not over:
        return []
    kinds = set().union(set(), *(_served_operand(flow, operand) for operand in (*receivers, *arguments)))
    return [f"main.<numeric generic>.{kind}@{_line(node)} {over[0]}|`main.{_symbol(named.group(2))}` in {where}"
            for kind in sorted(kinds)]


def _column(node: _Node) -> int:
    found = LOCATION.search(node.line)
    return int(found.group(3)) if found else 0


def _predicate_bodies(roots: list[_Node]) -> dict[tuple[object, ...], _Node]:
    """#371: what a predicate handed by name runs: a function by `(file, name, line)`, and a constant's or a variable's
    binding by where the name is declared, `(file, line, column)`."""
    found: dict[tuple[object, ...], _Node] = {}
    for root in roots:
        file = _file_of(root)
        for node in root.walk():
            if function := FUNCTION.match(node.line):
                found[(file, function.group(2), int(function.group(1)))] = node
            for index, kid in enumerate(node.kids):
                if kid.kind != "pattern_binding_decl":
                    continue
                for sibling in node.kids[index + 1:]:
                    if sibling.kind != "var_decl" or not (place := LOCAL_VAR.match(sibling.line)):
                        break
                    found[(pathlib.Path(place.group(1)).name, int(place.group(2)), int(place.group(3)))] = kid
    return found


def _predicate(argument: _Node, flow: _Flow, bodies: dict[tuple[object, ...], _Node]) -> _Node | None:
    """#371: the body a function-typed argument runs: a closure written in place, or the function, the constant or the
    variable of the app's own it names. None for anything else (a parameter, a member), which G-2 names."""
    top = _top(argument)
    if top.kind == "closure_expr":
        return top
    if top.kind != "declref_expr" or (place := MAIN_REF.search(top.line)) is None:
        return None
    symbol, file, row, column = place.group(1), pathlib.Path(place.group(2)).name, int(place.group(3)), int(place.group(4))
    if (held := bodies.get((file, row, column))) is not None:
        return held
    name = _base(symbol.split(".")[-1])
    at = flow.declared(file, name, row)
    return bodies.get((file, name, at)) if at is not None else None


def _counts_or_searches(node: _Node, flow: _Flow,
                        bodies: dict[tuple[object, ...], _Node]) -> list[tuple[str, _Node, str, str]]:
    """#371 (D-218 clause 4, G-2): `(method, meeting, declaration, kind)` for each declaration a served number meets,
    as its receiver or an argument, inside the closure given to a method that counts or searches (`COUNTS_OR_SEARCHES`),
    written in place or handed by name: a comparison, which the rules admit elsewhere, and anything else, a function
    of the app's own among them. A served number rebuilt that way (`(1...100).filter { $0 <= s.position }.count`) is a
    number no board published."""
    if node.kind != "call_expr" or len(node.kids) < 2 or node.kids[1].kind != "argument_list":
        return []
    callee = _top(node.kids[0])
    if callee.kind != "dot_syntax_call_expr" or not callee.kids or (
            method := COUNTS_OR_SEARCHES.search(callee.kids[0].line)) is None:
        return []
    called = method.group(1) + (f"({method.group(2)})" if method.group(2) else "")
    found: list[tuple[str, _Node, str, str]] = []
    for argument in (kid for kid in node.kids[1].kids if kid.kind == "argument" and kid.kids):
        typed = TYPE_OF["type"].search(_top(argument.kids[0]).line)
        if typed is None or "->" not in typed.group(1) or (body := _predicate(argument.kids[0], flow, bodies)) is None:
            continue
        for item in body.walk():
            if (applied := _application(item)) is None or (named := DECL.search(applied[0].line)) is None:
                continue
            kinds = set().union(set(), *(_served_operand(flow, operand) for operand in (*applied[1], *applied[2])))
            found += [(called, item, f"{named.group(1)}.{_symbol(named.group(2))}", kind) for kind in sorted(kinds)]
    return found


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


#: #242 (G-11): a call into the engine client, a member of an extension of it included: a method, printed with its
#: labels or (all `_`) without them, an initialiser or a subscript.
ENGINE_MEMBER = re.compile(r'decl="main\.\(file\)\.(EngineClient(?: extension)?\.\w+(?:\([^)"]*\))?)@')


def _engine_arguments(node: _Node) -> list[str]:
    """#242 (G-11, INV-64; the backlog-gates review's K1): every argument of a call into the engine client, labelled
    or not, an initialiser's and a subscript's included, that `REQUEST_ARGUMENTS` does not name with its declared
    source, keyed by its label or, unlabelled, by its position (`#0`). The labelled arguments of a request method
    `_request_call` reads are left to it."""
    if node.kind == "call_expr" and len(node.kids) >= 2 and node.kids[1].kind == "argument_list":
        callee = _top(node.kids[0])
        head = callee.kids[0] if callee.kind in ("dot_syntax_call_expr", "constructor_ref_call_expr") and callee.kids \
            else callee
        listed: _Node | None = node.kids[1]
        judged = callee.kind == "dot_syntax_call_expr" and REQUEST_CALL.search(head.line) is not None
    elif node.kind == "subscript_expr":
        head, listed, judged = node, next((kid for kid in node.kids if kid.kind == "argument_list"), None), False
    else:
        return []
    if listed is None or " implicit" in listed.line or (member := ENGINE_MEMBER.search(head.line)) is None:
        return []
    method, found = member.group(1).replace(" extension.", "."), []
    for index, argument in enumerate(kid for kid in listed.kids if kid.kind == "argument"):
        label = ARGUMENT_LABEL.match(argument.line)
        # A default the caller did not write is the engine client's own value, not an argument.
        if (label is not None and judged) or (argument.kids and argument.kids[0].kind == "default_argument_expr"):
            continue
        key = label.group(1) if label is not None else f"#{index}"
        allowed, named = REQUEST_ARGUMENTS.get((method, key)), _named(argument)
        if allowed is None or (named and named != {allowed}):
            found.append(f"main.<engine argument>.{method}|{key}|{', '.join(sorted(named)) or 'a value'}@{_line(node)}")
    return found


def _request_value(node: _Node) -> list[str]:
    """The review's B2: an engine request method referred to anywhere but as the direct callee of a call
    (`let ask = client.recommendation`) carries arguments `_request_call` never sees."""
    # The compiler turns a method used as a value into an implicit closure that calls it.
    if node.kind != "autoclosure_expr":
        return []
    call = next((m for item in node.walk() if (m := REQUEST_CALL.search(item.line))), None)
    return [f"main.<request argument>.{call.group(1)}|(all)|the method used as a value@{_line(node)}"] if call else []


def _request_source(node: _Node) -> list[str]:
    """An assignment, an `inout` use or a binding of a declaration a request sends, from anything but
    its declared source."""
    found = []
    if node.kind in {"assign_expr", "inout_expr"} and node.kids:
        for held in _named(_top(node.kids[0])) & set(REQUEST_SOURCES):
            value = _top(node.kids[1]) if node.kind == "assign_expr" and len(node.kids) > 1 else None
            if not _an_allowed_source(held, value):
                found.append(f"main.<request source>.{held}|{node.kind}@{_line(node)}")
    # The review's B2: the property's storage (`_task`) and its binding (`$task`), in any use the
    # compiler did not write itself, are the property assigned from anywhere.
    found += [f"main.<request source>.{path}|{REQUEST_ALIASES[path]} through {path}@{_line(node)}"
              for module, path, *_ in NAMED_DECL.findall(node.line)
              if module == "main" and path in REQUEST_ALIASES and " implicit " not in node.line]
    # #244: a key path to it, whatever is done with the path afterwards. A declaration a request sends,
    # named in a key path, can be written through it from anywhere (bound to a name first, or handed to a
    # generic writer), so no key path may name one.
    if node.kind == "keypath_expr":
        named = {path for item in node.walk() for module, path, *_ in NAMED_DECL.findall(item.line) if module == "main"}
        found += [f"main.<request source>.{REQUEST_ALIASES.get(path, path)}|a key path to "
                  f"`{REQUEST_ALIASES.get(path, path)}`@{_line(node)}"
                  for path in named if path in REQUEST_SOURCES or path in REQUEST_ALIASES]
    return found


def _an_allowed_source(held: str, value: _Node | None) -> bool:
    """Whether `value` is one of `held`'s declared sources, exactly (the review's B2)."""
    if value is None or REQUEST_SOURCES[held] is None:
        return False
    shown = "|".join(sorted(_named(value)))
    return any(shape.match(shown) for shape in REQUEST_SOURCE_SHAPES.get(held, []))


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
            if file != NETWORK_FILE:
                found += _request_value(node) + _engine_arguments(node)
            facts.setdefault(file, set()).update(found)
    for held, sources in REQUEST_SOURCES.items():
        if sources is None and held in declared_at and not _literal_let(roots, declared_at[held]):
            facts.setdefault(declared_at[held].split(":")[0], set()).add(
                f"main.<request source>.{held}|not a literal let@0")
    return {file: found for file, found in facts.items() if found}


def _aliases(ast: str) -> dict[str, str]:
    """#322 (M1): every `typealias` the dump declares, by its full name, to the type it names."""
    return {name: target for name, target in TYPEALIAS.findall(ast) if name != target}


def _expanded(typed: str, aliases: dict[str, str]) -> tuple[str, str]:
    """#322 (M1): `typed` with every alias in it replaced by the type it names, to a fixed point, and the first
    alias it was written through ("" when none)."""
    through = ""
    for _ in range(len(aliases) + 1):
        before = typed
        for alias, target in aliases.items():
            pattern = rf"(?<!\w){re.escape(alias)}(?![\w.])"
            if re.search(pattern, typed):
                through = through or alias
                typed = re.sub(pattern, target.replace("\\", r"\\"), typed)
        if typed == before:
            break
    return typed, through


def _decoded(line: str, kept: set[str], aliases: dict[str, str] | None = None) -> dict[str, str]:
    """#297: the kept types a line decodes, each with the alias it is written through (#322): each type a generic
    substitution gives a `Decodable` parameter, when it names a kept type (`[Category]`, not
    `Category.CodingKeys`), read through `aliases`. An existential stands for every kept type (`ANY_KEPT`)."""
    found: dict[str, str] = {}
    for signature, mapping in SUBSTITUTION.findall(line):
        for parameter in re.findall(r"(\w+) : Decodable\b", signature):
            for typed in re.findall(rf"(?:^|\s){parameter} -> (.*?)(?=\s\w+ -> |$)", mapping):
                typed, through = _expanded(typed.strip(), aliases or {})
                if EXISTENTIAL.search(typed):
                    found.setdefault(ANY_KEPT, through)
                for name in kept:
                    if re.search(rf"\b{name}\b(?![.\w])", typed):
                        found.setdefault(name, through)
    return found


def _owned(node: _Node, owner: str = "", function: str = "",
           synthesised: str = "") -> Iterator[tuple[_Node, str, str, str]]:
    """Every node with the full path of the type and the full name of the function it is in (#322, N1:
    `Elsewhere.ContentView`, `load(later:)`), and the type whose synthesised `init(from:)` it is in, if any
    (#297). A type declared in a function is under that function's name."""
    if (declared := OWNER.match(node.line)) and declared.group(1) != "protocol":
        name = declared.group(2)
        owner = name if declared.group(1) == "extension_decl" else ".".join(p for p in (owner, function, name) if p)
        function = ""
    elif named := FULL_FUNCTION.match(node.line):
        function = named.group(1)
    elif node.kind == "constructor_decl" and " implicit " in node.line and '"init(from:)"' in node.line:
        synthesised = owner.split(".")[-1]
    yield node, owner, function, synthesised
    for kid in node.kids:
        yield from _owned(kid, owner, function, synthesised)


def _held(owned: list[tuple[str, tuple[_Node, str, str, str]]], aliases: dict[str, str]) -> dict[str, str]:
    """#297: each type that is or holds a kept answer's type, to the kept type: a type whose synthesised decoder
    decodes one, or an enum one of whose cases carries one (#322), to a fixed point."""
    held = {name: name for name in KEPT_ANSWER_TYPES}
    grown = True
    while grown:
        grown = False
        for _, (node, owner, _function, synthesised) in owned:
            holder = synthesised
            if synthesised:
                inside = set(_decoded(node.line, set(held), aliases)) - {ANY_KEPT}
            elif payload := CASE_PAYLOAD.match(node.line):
                holder, typed = owner.split(".")[-1], _expanded(payload.group(1), aliases)[0]
                inside = {name for name in held if re.search(rf"\b{name}\b(?![.\w])", typed)}
            else:
                continue
            if holder and holder not in held and inside:
                held[holder] = held[sorted(inside)[0]]
                grown = True
    return held


def kept_answer_facts(ast: str) -> dict[str, set[str]]:
    """#297 (D-206 clause 4): `{file: {"main.<...>", ...}}`, each call to a declaration `CALLED_ONLY_IN`
    holds, with the type and function it is in, and each decode of a kept answer's type, with the kept type
    it is or holds and the alias it is written through. A type whose synthesised decoder decodes a kept type,
    or an enum one of whose cases carries one (#322), holds it, to a fixed point."""
    roots = _tree(ast)
    aliases = _aliases(ast)
    owned = [(_file_of(root), entry) for root in roots for entry in _owned(root)]
    held = _held(owned, aliases)
    facts: dict[str, set[str]] = {}
    for file, (node, owner, function, synthesised) in owned:
        if not synthesised:
            facts.setdefault(file, set()).update(
                f"main.<decodes>.{name}|{held.get(name, ANY_KEPT)}|{through}@{_line(node)}"
                for name, through in _decoded(node.line, set(held), aliases).items())
            for name in INIT_FROM.findall(node.line):
                if (name := name.split(".")[-1]) in held:
                    facts.setdefault(file, set()).add(f"main.<decodes>.{name}|{held[name]}|@{_line(node)}")
        for symbol, *_ in MAIN_REF.findall(node.line):
            symbol = re.sub(r"([\w.]+) extension\.", r"\1.", symbol)
            called = ".".join([*symbol.split(".")[:-1], _base(symbol.split(".")[-1])])
            if called in CALLED_ONLY_IN:
                facts.setdefault(file, set()).add(f"main.<called in>.{called}|{owner}|{function}@{_line(node)}")
    return {file: found for file, found in facts.items() if found}


def _kept_answer_problem(name: str, symbol: str) -> str | None:
    """#297: a kept answer kept outside the load path, or its type decoded outside its files."""
    fact, _, subject = symbol.partition(">.")
    detail, _, line = subject.rpartition("@")
    if fact == "<called in":
        called, owner, function = detail.split("|")
        (file, allowed_owner, allowed_function), why = CALLED_ONLY_IN[called]
        if (name, owner, function) == (file, allowed_owner, allowed_function):
            return None
        where = ".".join(part for part in (owner, function) if part) or "the file's own scope"
        return (f"{name}:{line}: keeps an answer (`{called}`) in `{where}`, outside the load path "
                f"(`{allowed_owner}.{allowed_function}` in {file}); {why} (#297, INV-67)")
    if fact == "<decodes":
        decoded, kept, through = (*detail.split("|"), "")[:3]
        alias = f" through the alias `{through}`" if through else ""
        if kept == ANY_KEPT:
            return (f"{name}:{line}: decodes through an existential{alias}, whose type the gate cannot read, so it may "
                    "be a kept answer's type; no file decodes every kept type (#297, #322, INV-67)")
        files, why = KEPT_ANSWER_TYPES[kept]
        if name in files:
            return None
        holds = f", which holds a `{kept}`" if decoded != kept else ""
        return (f"{name}:{line}: decodes `{decoded}`{alias}{holds}, a kept answer's type; {why} "
                f"({', '.join(sorted(files))}) (#297, INV-67)")
    return None


def _store_problem(name: str, symbol: str) -> str | None:
    """#242 (G-13): a store's URL made or received otherwise than from the file manager's folders, and a read of
    anything but the store's own `url`."""
    fact, _, subject = symbol.partition(">.")
    detail, _, line = subject.rpartition("@")
    if fact == "<store url":
        how = "by a cast" if detail == "a cast" else f"by {detail}" if detail.startswith("`") or detail.startswith("an ") \
            else detail
        verb = "receives a URL," if ", declared in " in detail else "reads a URL" if detail.startswith("through ") \
            else "makes a URL"
        return (f"{name}:{line}: {verb} {how}; a store makes a URL only from the file manager's folders "
                f"(`STORE_FOLDER_MAKERS`) or by a function of its own file that is not generic over it, since its read "
                "fetches an https address as readily as a file (G-13, #242)")
    if fact == "<store parameter":
        function, _, parameter = detail.partition("|")
        return (f"{name}:{line}: `{function}` takes a URL (`{parameter}`) from its caller, so another file chooses the "
                "address the store builds on; only an initialiser `PROVENANCE` keeps to the store's own file takes one "
                "(G-13, #242)")
    if fact == "<store reads":
        reader, _, read = detail.partition("|")
        return (f"{name}:{line}: reads with `{reader}` from {read}, not the store's own `{STORE_READS.get(name, '?')}`; "
                "a store reads only its own file (`STORE_READS`; G-13, #242)")
    return None


def _request_problem(name: str, symbol: str) -> str | None:
    """#174, #188 (INV-64): the reader's text, or anything the screen built, into a request's arguments."""
    fact, _, subject = symbol.partition(">.")
    detail, _, line = subject.rpartition("@")
    if fact == "<request argument":
        method, label, named = detail.split("|")
        return (f"{name}:{line}: the request's `{label}` argument to `{method}` names {named}; a request "
                "carries only its declared sources, never what the screen builds (INV-64, D-126; #174, #188)")
    if fact == "<engine argument":
        method, key, named = detail.split("|", 2)
        which = f"argument {key[1:]} (unlabelled)" if key.startswith("#") else f"`{key}` argument"
        return (f"{name}:{line}: the {which} of `{method}` names {named}; every argument of a call into the engine "
                "client, labelled or not, an initialiser's and a subscript's included, carries only the declared source "
                "`REQUEST_ARGUMENTS` names for it (INV-64, D-126; G-11, #242)")
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
    if fact == "<meets":
        kind, _, where = subject.partition("@")
        line, _, rest = where.partition(" ")
        meeting, _, function = rest.rpartition(" in ")
        declared, _, role = meeting.rpartition("|")
        what = "number" if kind == "number" else kind
        return (f"{name}:{line}: `{declared}` on a served {what} (its {role}) in `{function}`, which is not on the list "
                "of what a served number may meet (`SERVED_MAY_MEET`: a comparison, its display, what passes it along "
                "unchanged, and the places named there); a new one is a reviewed edit (REQ-APP-005, D-181, #242)")
    if fact == "<numeric generic":
        kind, _, where = subject.partition("@")
        line, _, rest = where.partition(" ")
        meeting, _, function = rest.rpartition(" in ")
        protocol, _, shown = meeting.partition("|")
        what = "number" if kind == "number" else kind
        return (f"{name}:{line}: a served {what} is handed to {shown} in `{function}`, over the numeric protocol "
                f"`{protocol}`, whose arithmetic on it no rule can follow; no served number goes to one (D-218 clause 4, "
                "REQ-APP-005, #371)")
    if fact == "<counts":
        kind, _, where = subject.partition("@")
        line, _, rest = where.partition(" ")
        meeting, _, function = rest.rpartition(" in ")
        declared, method, allowed = meeting.split("|")
        what = "number" if kind == "number" else kind
        listed = f"; {allowed} such meeting(s) are permitted there" if allowed != "0" else ""
        return (f"{name}:{line}: `{declared}` meets a served {what} inside the closure given to `{method}` in "
                f"`{function}`, which counts or searches, so its result can be a new number (D-218 clause 4, "
                f"REQ-APP-005, #371){listed}")
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
    # The backlog-gates review round 2's N1: the store's Foundation list and the engine client's members.
    missing += [f"{name}: `{entry}` on the store's Foundation list" for name, allowed in STORE_FOUNDATION_ALLOWED.items()
                for entry in sorted(allowed) if f"Foundation.{entry}" not in found.get(name, set())]
    missing += [f"{name}: `{entry}` on the engine client's list" for name, allowed in ENGINE_CLIENT_REACHABLE.items()
                for entry in sorted(allowed) if f"main.{entry}" not in found.get(name, set())]
    # #242 (the backlog-gates review round 2's K1, G-1): each sink's own Foundation list, what the code a sink runs
    # may reference, and the constant types a sink may read.
    missing += [f"{name}: `{entry}` on the sink's own list of Foundation declarations" for name, allowed in SINK_FOUNDATION_ALLOWED.items()
                for entry in sorted(allowed) if not any(f"{module}.{entry}" in found.get(name, set()) for module in SINK_MODULES)]
    seen_runs = {fact.split(">.", 1)[1] for facts in found.values() for fact in facts
                 if fact.startswith(("main.<sink runs uses>.", "main.<sink reads constant type>."))}
    missing += [f"`{entry}` on the list of what the code a sink runs may reference" for entry in sorted(SINK_RUNS_ALLOWED)
                if entry not in seen_runs]
    missing += [f"`{typed}` on the list of constant types a sink may read" for typed in sorted(SINK_CONSTANT_TYPES)
                if typed not in seen_runs]
    # #242 (G-13): each store's URL makers and its one read.
    missing += [f"{name}: `{entry}` on the store's list of URL makers" for name, allowed in STORE_FOLDER_MAKERS.items()
                for entry in sorted(allowed) if f"main.<store url listed>.{entry}" not in found.get(name, set())]
    missing += [f"{name}: `{read}`, the store's one read" for name, read in STORE_READS.items()
                if f"main.<store reads listed>.{read}" not in found.get(name, set())]
    # #242 (G-12): the by-name labels the client may use.
    referenced = set().union(set(), *found.values())
    missing += [f"`{entry}` on the by-name list" for entry in sorted(BY_NAME_ALLOWED) if entry not in referenced]
    # #242 (G-2): what a served number may meet, in each place an entry names; an entry for any file, anywhere.
    seen_meets = {(name, *fact.split(">.", 1)[1].rsplit("|", 2))
                  for name, facts in found.items() for fact in facts if fact.startswith("main.<meets listed>.")}
    for (declared, role), (places, _) in sorted(SERVED_MAY_MEET.items(), key=str):
        wanted = [(file, function) for file, function in sorted(places)] if places is not None else [None]
        for place in wanted:
            if not any(d == declared and r == role and (place is None or (n, f) == place) for n, d, r, f in seen_meets):
                at = f"{place[0]}: " if place else ""
                missing.append(f"{at}`{declared}` as a {role}{f' in {place[1]}' if place else ''} on the list of what "
                               "a served number may meet")
    # #371 (D-218 clause 4): what a served number meets inside a closure that counts or searches, in each place named.
    seen_counts = {(name, fact.split(">.", 1)[1]) for name, facts in found.items() for fact in facts
                   if fact.startswith("main.<counts listed>.")}
    missing += [f"{file}: `{declared}` inside `{method}` in `{where}` on the list of what a served {kind} meets inside a "
                "closure that counts or searches" for file, where, method, kind, declared in sorted(COUNTS_OR_SEARCHES_PERMITTED)
                if (file, f"{declared}|{method}|{kind}|{where}") not in seen_counts]
    # #322 (M2): the kept answers' allowed sides. Rename `keep`, the load path or a kept type, and its rule
    # matched nothing while the gate passed.
    seen_kept = {(name, fact.split(">.", 1)[1].rpartition("@")[0])
                 for name, facts in found.items() for fact in facts if fact.startswith("main.<called in>.")}
    missing += [f"{file}: `{called}` called in `{owner}.{function}` (#322)"
                for called, ((file, owner, function), _) in CALLED_ONLY_IN.items()
                if (file, f"{called}|{owner}|{function}") not in seen_kept]
    seen_decodes = {(name, fact.split(">.", 1)[1].rpartition("@")[0].split("|")[1])
                    for name, facts in found.items() for fact in facts if fact.startswith("main.<decodes>.")}
    missing += [f"{file}: a decode of `{kept}` (#322)" for kept, (files, _) in KEPT_ANSWER_TYPES.items()
                for file in sorted(files) if (file, kept) not in seen_decodes]
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
    if fact == "<builds" and (entry := _provenance(subject)) is not None and name not in entry[0]:
        verb = f"builds {subject.split('.')[0]}" if ".init(" in subject else "calls"
        return f"{name}: {verb} (`{subject}`); {entry[1]} (D-180)"
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
    if fact == "<sink runs off list":
        body, _, declared = subject.partition("|")
        return (f"{name}: `{body}`, code a privacy sink runs, references `{declared}`, which is not on the list of what "
                "that code may reference (`SINK_RUNS_ALLOWED`); a new one is a reviewed edit (D-180, #242)")
    if fact == "<sink reads constant":
        detail, _, declared = subject.rpartition("@")
        body, constant, typed = detail.split("|", 2)
        who = f"`{body}`, code a privacy sink runs, reads" if body else "reads"
        return (f"{name}: {who} `{constant}`, a constant of type `{typed}` declared in {declared}; a privacy sink and "
                f"the code it runs read only constants of a plain value type ({', '.join(sorted(SINK_CONSTANT_TYPES))}), "
                "since another file can change an object held in one (D-180, #242)")
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


def _network_problem(name: str, symbol: str, head: str, decl: str) -> str | None:
    """The network outside its one door: a declaration on `NETWORK`, or an initialiser `CONTENTS_OF`
    matches (the M21-W3 review's M2), `Data`'s for the two stores aside (`FrontDoor.swift`'s own loads
    are gap G-13, #246)."""
    if name == NETWORK_FILE:
        return None
    if (CONTENTS_OF.search(symbol) and not symbol.startswith("Data.init(contentsOf")
            and not symbol.startswith(("URLComponents.init(url:", "URLRequest.init(url:"))):
        return (f"{name}: `{decl}` loads what a URL names, which can be the network, and {NETWORK_FILE} is the "
                "one door (D-126; the M21-W3 review's M2)")
    if any(symbol.startswith(p) or head == p for p in NETWORK) and symbol != "URL.made":
        return (f"{name}: `{decl}` is the network, and {NETWORK_FILE} is the one door (D-126); "
                "its arguments are pinned in EngineClientTests.swift")
    return None


def _reach_anything_problem(name: str, symbol: str, head: str, decl: str) -> str | None:
    """What reaches any value past the declaration rules: by name (BY_NAME), or through memory."""
    if any(symbol.startswith(p) or head == p for p in BY_NAME):
        return (f"{name}: `{decl}` reaches a value, a class or a selector by name, past every declaration "
                "rule here; the client uses none (the M21-W3 review's K1, #241)")
    if BY_NAME_LABEL.search(symbol) and decl not in BY_NAME_ALLOWED:
        return (f"{name}: `{decl}` reaches a value, a class or a selector by name (an argument labelled for a key or a "
                "selector, or a class-by-name entry point); only the declarations `BY_NAME_ALLOWED` names take one "
                "(G-12, #242)")
    if decl.startswith("Foundation.") and FOUNDATION_KEY_LABEL.search(symbol) and decl not in BY_NAME_ALLOWED:
        return (f"{name}: `{decl}` reaches a value, a class or a selector by name (a key labelled `key:` or "
                "`keyPath:`); only the declarations `BY_NAME_ALLOWED` names take one (G-12, #242)")
    if any(part.startswith(UNSAFE) for part in head.split(".")):
        return (f"{name}: `{decl}` touches memory unsafely, which can rewrite any value, a privacy sink's "
                "own included; the client uses none (D-180, the second W2 review's U9)")
    return None


def _store_url_problem(name: str, symbol: str, decl: str) -> str | None:
    """#246 (G-13): a store makes no URL by an initialiser or a decode."""
    if name in FILESYSTEM_FILES and URL_MADE_BY_NAME.match(symbol):
        return (f"{name}: `{decl}` makes a URL, and a store makes a URL only from the file system's folders: "
                "its read fetches an https address as readily as a file (#246)")
    return None


def _store_module_problem(name: str, module: str, symbol: str) -> str | None:
    """#246 (the backlog-gates review round 1's M2): the gap register's own file references only the Foundation
    declarations on its list."""
    allowed = STORE_FOUNDATION_ALLOWED.get(name)
    if allowed is None or module not in SINK_MODULES or symbol == "<imported>":
        return None
    if symbol in allowed or any(entry.startswith(f"{symbol}.") for entry in allowed):
        return None
    return (f"{name}: `{module}.{symbol}` is not on the list of Foundation declarations a store may reference "
            f"({FILESYSTEM_FILES[name]}); its read fetches an https address as readily as a file, so a store "
            "makes a URL only from the file system's folders, and the list widens only by a reviewed edit (#246)")


def _capability_problem(name: str, symbol: str, decl: str) -> str | None:
    """Network, file system and the ways text leaves a phone, inside the allowed modules."""
    head = symbol.split("(")[0]
    if (name, symbol) in FORBIDDEN_EXCEPT:
        return None
    if any(symbol.startswith(p) or head == p for p in FORBIDDEN):
        return f"{name}: `{decl}` carries text off the device or into shared storage"
    if (reached := _reach_anything_problem(name, symbol, head, decl) or _store_url_problem(name, symbol, decl)) is not None:
        return reached
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
    if (network := _network_problem(name, symbol, head, decl)) is not None:
        return network
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


def _engine_client_problem(name: str, module: str, symbol: str) -> str | None:
    """#244: a member of the engine client off `ENGINE_CLIENT_REACHABLE`, reached from another file."""
    if name == NETWORK_FILE or module != "main" or not symbol.startswith("EngineClient."):
        return None
    allowed = ENGINE_CLIENT_REACHABLE.get(name, frozenset())
    if symbol in allowed:
        return None
    return (f"{name}: reaches `{symbol}`, a member of the engine client off the list this file may reach "
            f"({', '.join(sorted(allowed)) or 'none'}); a new one is a reviewed edit (INV-64, #244)")


def _sink_module_problem(name: str, module: str, symbol: str) -> str | None:
    """The M21-W3 review's B1 (#242): a privacy sink's own file references only the Foundation
    declarations on its list, and none of the standard library's process-wide state."""
    if name not in SINK_FILES or symbol == "<imported>":
        return None
    allowed = SINK_FOUNDATION_ALLOWED.get(name, frozenset())
    listed = symbol in allowed or any(entry.startswith(f"{symbol}.") for entry in allowed)
    if module in SINK_MODULES and not listed:
        return (f"{name}: `{module}.{symbol}` is not on the list of Foundation declarations a privacy sink may "
                f"reference ({SINK_FILES[name]}); what it is built from widens only by a reviewed edit (D-180, "
                "the M21-W3 review's B1, #242)")
    if module == "Swift" and symbol.split(".")[0] in SINK_SWIFT_REFUSED:
        return (f"{name}: `Swift.{symbol}` is process-wide state any file can set; a privacy sink reads none "
                "(D-180, the M21-W3 review's B1)")
    return None


def problems(found: dict[str, set[str]]) -> list[str]:
    bad: list[str] = []
    for name, decls in sorted(found.items()):
        for decl in sorted(decls):
            module, _, symbol = decl.partition(".")
            if module == "main" and symbol.startswith("<"):
                if (problem := _sink_problem(name, symbol) or _flow_problem(name, symbol)
                        or _request_problem(name, symbol) or _kept_answer_problem(name, symbol)
                        or _store_problem(name, symbol) or _selector_problem(name, symbol)) is not None:
                    bad.append(problem)
                continue
            problem = (_module_problem(name, module, symbol, decl) or _sink_module_problem(name, module, symbol)
                       or _store_module_problem(name, module, symbol) or _engine_client_problem(name, module, symbol))
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
    """The second W2 review's K1: the committed dump against the fixture as it compiles, by its
    declarations and (the M21-W3 Tester's M2) by its refusals, line for line, the Release rule's too: a
    shape whose body changed while another still carried its phrase passed the per-phrase check."""
    if not SNAPSHOT.exists():
        return [f"{SNAPSHOT.name} is missing; write it with `--snapshot`"]
    compiled, committed = fixture_dump(ast), SNAPSHOT.read_text(encoding="utf-8")
    now, kept = set(DECLARED.findall(compiled)), set(DECLARED.findall(committed))
    if now != kept:
        return [f"{SNAPSHOT.name} is not the fixture as it compiles ({len(now - kept)} declaration(s) new, "
                f"{len(kept - now)} gone); write it again with `--snapshot`"]
    found_now, found_kept = references(compiled), references(committed)
    refused_now = sorted(problems(found_now)) + sorted(release_problems(found_now))
    refused_kept = sorted(problems(found_kept)) + sorted(release_problems(found_kept))
    if refused_now == refused_kept:
        return []
    return [f"the fixture as it compiles is refused otherwise than {SNAPSHOT.name} "
            f"({len(set(refused_now) - set(refused_kept))} refusal(s) new, "
            f"{len(set(refused_kept) - set(refused_now))} gone); write it again with `--snapshot`"]


def pinned_refusals(release: bool) -> list[_PinKey] | None:
    """#242 (D-214): the refusals `PINNED_REFUSALS` holds for a Release or a Debug configuration, by their keys (#375),
    or None when the file is missing, empty or has a line of another shape, which fails the self-test (fail closed)."""
    try:
        lines = PINNED_REFUSALS.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    pinned: list[_PinKey] = []
    for line in lines:
        fields = line.split("\t")
        if len(fields) != 5:
            return None
        scope, file, planted, occurrence, text = fields
        if scope not in ("all", "release") or not file.endswith(".swift") or not planted.strip() \
                or not occurrence.isdigit() or (planted == "-") != (occurrence == "0") or not text.strip():
            return None
        if scope == "all" or release:
            pinned.append((file, planted, int(occurrence), text))
    return pinned or None


def refusal_keys(refused: list[str]) -> set[_PinKey]:
    """#375: each refusal by its key, its line read in the fixture as `FIXTURES` holds it: the planted line, stripped,
    and which of the file's identical lines it is, so a refusal moved with its line keeps its key."""
    sources: dict[str, list[str]] = {}
    keys: set[_PinKey] = set()
    for refusal in refused:
        if (found := REFUSAL_PLACE.match(refusal)) is None:
            continue
        file, line, text = found.groups()
        if line is None:
            keys.add((file, "-", 0, text))
            continue
        if file not in sources:
            try:
                sources[file] = [row.strip() for row in (FIXTURES / file).read_text(encoding="utf-8").splitlines()]
            except OSError:
                sources[file] = []
        rows, row = sources[file], int(line)
        if 1 <= row <= len(rows):
            keys.add((file, rows[row - 1], rows[:row].count(rows[row - 1]), text))
    return keys


def _pin_intact() -> bool:
    """#375: whether the pin's first `PINNED_COUNT` lines are the ones made before #242, as they were."""
    try:
        lines = PINNED_REFUSALS.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    kept = "\n".join(lines[:PINNED_COUNT]).encode("utf-8")
    return len(lines) >= PINNED_COUNT and hashlib.sha256(kept).hexdigest() == PINNED_SHA256


def pin_shown(key: _PinKey) -> str:
    """#375: a pinned refusal as a reader finds it: its file, its planted line and its text."""
    file, planted, occurrence, text = key
    return f"{file}: {text}" if occurrence == 0 else f"{file}, on `{planted}` (#{occurrence} of that line): {text}"


def _pin_broken(label: str, refused: list[str]) -> list[str]:
    """#242 (D-214 clause 1): each pinned refusal one configuration no longer makes, by its key (#375); and the pin
    itself, when its lines made before #242 are not all there as they were."""
    pinned = pinned_refusals("release" in label)
    if pinned is None:
        return [f"({label}) {PINNED_REFUSALS.name} is missing, empty or malformed, so nothing holds that the gate "
                "refuses what it refused before #242 (D-214)"]
    broken = [] if _pin_intact() else [
        f"({label}) the first {PINNED_COUNT} lines of {PINNED_REFUSALS.name} are not those pinned before #242: one was "
        "edited, removed or moved, or the pin was regenerated; every one must still be there as it was (D-214, #375)"]
    made = refusal_keys(refused)
    return broken + [f"({label}) a refusal the fixture made before #242 is gone (D-214, no loosening): {pin_shown(key)}"
                     for key in pinned if key not in made]


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
        found = references(ast)
        refused = problems(found)
        expected = set(FIXTURE_REFUSALS)
        if "release" in label:
            # The M21-W3 review's M4: the Release configurations' own rule, on the fixture too.
            refused += release_problems(found)
            expected |= FIXTURE_RELEASE_REFUSALS
        if index == 0:
            broken += _snapshot_drift(ast)
        broken += _pin_broken(label, refused)
        broken += [f"({label}) {file}: {phrase} was not refused" for file, phrase in sorted(expected)
                   if not any(line.startswith(f"{file}:") and phrase in line for line in refused)]
        broken += [f"({label}) refused what it must allow: {line}" for line in refused
                   if not any(line.startswith(f"{file}:") and phrase in line for file, phrase in expected)]
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
