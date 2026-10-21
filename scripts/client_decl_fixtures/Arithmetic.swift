// #173 (D-181, G-2): arithmetic on a served number by the shapes the second M19-W2 review planted. Each
// line marked `shape:` is REFUSED; the line marked `allowed:` is not (the review's M5, an over-refusal).
// The unit tests find each line by its mark.
import Foundation

func shapePrefixMinus(_ s: Standing) -> Int { -s.position } // shape: prefix-minus
func shapeShift(_ s: Standing) -> Int { s.position << 1 } // shape: shift
func shapeShiftAssign(_ s: Standing) -> Int {
    var x = s.position
    x <<= 1 // shape: shift-assign
    return x
}
func shapeReducePlus(_ s: Standing) -> Int { [s.position].reduce(0, +) } // shape: operator-as-value
func shapeMapMinus(_ s: Standing) -> [Int] { [s.position].map(-) } // shape: operator-as-value-map
func shapePow(_ s: Standing) -> Double { pow(Double(s.position), 2) } // shape: pow
func shapeTruncating(_ s: Standing) -> Double { Double(s.position).truncatingRemainder(dividingBy: 2) } // shape: truncating
func shapeQuotient(_ s: Standing) -> Int { s.position.quotientAndRemainder(dividingBy: 2).quotient } // shape: quotient
func shapeOverflow(_ s: Standing) -> Int { s.position.dividedReportingOverflow(by: 2).partialValue } // shape: overflow

struct ShapeBox { let v: Int }
func + (lhs: ShapeBox, rhs: ShapeBox) -> ShapeBox { ShapeBox(v: lhs.v) } // shape: custom-operator

extension Int { // shape: numeric-extension
    func shapeBumped() -> Int { self + 1 }
}

struct ShapeTable {
    subscript(_ i: Int) -> Int { i + 1 } // shape: subscript
}
func shapeSubscript(_ s: Standing) -> Int { ShapeTable()[s.position] }

func shapeLaterLine(_ s: Standing) -> Int {
    for
        p in [s.position] { return p + 1 } // shape: later-line
    return 0
}

struct ShapeDecoded { let points: Int }
extension ShapeDecoded: Decodable {}
func shapeDecodedInExtension(_ d: ShapeDecoded) -> Int { d.points + 1 } // shape: decoded-in-extension

func shapeFilterCount(_ s: Standing) -> Int { [s].filter { $0.position > 0 }.count + 1 } // shape: filter-count

// #171: a served number through `Any` and through text, and a served fact's number. REFUSED.
func shapeThroughAny(_ s: Standing) -> Int {
    var bag: [String: Any] = [:]
    bag["p"] = s.position
    return (bag["p"] as? Int ?? 0) + 1 // shape: through-any
}

func shapeThroughText(_ s: Standing) -> Int {
    let text = "\(s.position)"
    return (Int(text) ?? 0) + 1 // shape: through-text
}

enum ShapeValue: Decodable {
    case number(Double)
    case word(String)
}

struct ShapeFact: Decodable { let fact: ShapeValue }

func shapeServedFact(_ f: ShapeFact) -> Double {
    if case let .number(n) = f.fact { return n + 1 } // shape: served-fact
    return 0
}

func shapeFactThroughAny(_ f: ShapeFact) -> Double {
    var out: [String: Any] = [:]
    if case let .number(n) = f.fact { out["n"] = n }
    return (out["n"] as? Double ?? 0) * 2 // shape: fact-through-any
}

// ALLOWED: a label's length is not a served number.
func shapeLabelLength(_ s: Standing) -> Int { "#\(s.position)".count + 1 } // allowed: label-length

// The M21-W3 review's B3: a served number parsed back from text, boxed, round-tripped through JSON, and
// met by a bitwise operator. REFUSED, each.
func shapeNSStringParse(_ s: Standing) -> Int { let text = "\(s.position)"; return (text as NSString).integerValue + 1 } // shape: nsstring-parse
func shapeFormatterParse(_ s: Standing) -> Int { let text = "\(s.position)"; return (NumberFormatter().number(from: text)?.intValue ?? 0) + 1 } // shape: formatter-parse
func shapeScannerParse(_ s: Standing) -> Int { let text = "\(s.position)"; return (Scanner(string: text).scanInt() ?? 0) + 1 } // shape: scanner-parse
func shapeAnyHashable(_ s: Standing) -> Int { let boxed = AnyHashable(s.position); return (boxed.base as? Int ?? 0) + 1 } // shape: anyhashable
func shapeAnyObject(_ s: Standing) -> Int { let boxed = s.position as AnyObject; return (boxed as? Int ?? 0) + 1 } // shape: anyobject
func shapeNSNumber(_ s: Standing) -> Int { let boxed = NSNumber(value: s.position); return boxed.intValue + 1 } // shape: nsnumber
func shapeJSONRoundTrip(_ s: Standing) -> Int { let bytes = (try? JSONEncoder().encode([s.position])) ?? Data(); let back = (try? JSONDecoder().decode([Int].self, from: bytes)) ?? []; return (back.first ?? 0) + 1 } // shape: json-round-trip
func shapeXor(_ s: Standing) -> Int { s.position ^ 1 } // shape: xor
func shapeBitwiseNot(_ s: Standing) -> Int { ~s.position } // shape: bitwise-not
func shapeBitwiseAnd(_ s: Standing) -> Int { s.position & 0xFF } // shape: bitwise-and
func shapeFactNSNumber(_ f: ShapeFact) -> Double { if case let .number(n) = f.fact { return NSNumber(value: n).doubleValue * 2 }; return 0 } // shape: fact-nsnumber

// The M21-W3 review's M1: counts, row numbers, and a closure's `$0` near a served one. ALLOWED, each;
// the served `$0` itself is REFUSED.
func shapeServedDollar(_ list: [Standing]) -> [Int] { list.map(\.position).map { $0 + 1 } } // shape: served-dollar
func shapeNearbyRowNumbers(_ list: [Standing]) -> [Int] { list.enumerated().map { $0.offset + 1 } } // allowed: nearby-row-numbers
func shapePositionsCount(_ list: [Standing]) -> Int { let positions = list.map(\.position); return positions.count + 1 } // allowed: positions-count
func shapeIndicesCount(_ s: Standing) -> Int { [s.position].indices.count - 1 } // allowed: indices-count
func shapeRowNumbers(_ list: [Standing]) -> [Int] { list.map(\.position).enumerated().map { $0.offset + 1 } } // allowed: row-numbers
func shapeKeyPathCount(_ list: [Standing]) -> Int { list.map(\.position).count + 1 } // allowed: keypath-count

// The M21-W3 review's M1 allowance, laundered: a count of a list a served number BUILDS (its length,
// a range's bound, how many are dropped) is a function of that number. REFUSED, each. A served number
// read by reflection is refused by name (Mirror).
func shapeCountOfBuilt(_ s: Standing) -> Int { Array(repeating: 0, count: s.position).count + 1 } // shape: count-of-built
func shapeRangeCount(_ s: Standing) -> Int { (0..<s.position).count * 2 } // shape: range-count
func shapeDropCount(_ s: Standing) -> Int { [1, 2, 3].dropFirst(s.position).count + 1 } // shape: drop-count
func shapeMirror(_ s: Standing) -> Int { (Mirror(reflecting: s).children.first?.value as? Int ?? 0) + 1 }

// #242 (G-2): what a served number may meet is listed: a comparison, its display, the places a ruling names, and
// what the app's own code does with it, followed. Each line marked `shape:` meets something else. REFUSED, each,
// on that line; a list a served number sizes is refused where it is built, so its count, bound to a name first or
// not, is never read.
func shapeAbs(_ s: Standing) -> Int { abs(s.position) } // shape: abs
func shapeMin(_ s: Standing) -> Int { min(s.position, 3) } // shape: min
func shapeMax(_ s: Standing) -> Int { max(s.position, 3) } // shape: max
func shapeMagnitude(_ s: Standing) -> UInt { s.position.magnitude } // shape: magnitude
func shapeRounded(_ s: Standing) -> Double { Double(s.position).rounded(.down) } // shape: rounded
func shapeTable(_ s: Standing) -> Int { [10, 20, 30][s.position] } // shape: table
func shapeBoundCount(_ s: Standing) -> Int {
    let built = Array(repeating: 0, count: s.position) // shape: bound-count
    return built.count + 1
}
func shapeBoundRange(_ s: Standing) -> Int {
    let range = 0..<s.position // shape: bound-range
    return range.count
}
func shapeBoundDrop(_ s: Standing) -> Int {
    let dropped = [1, 2, 3].dropFirst(s.position) // shape: bound-drop
    return dropped.count
}
func shapeStringRepeating(_ s: Standing) -> Int { String(repeating: "x", count: s.position).count } // shape: string-repeating
func shapeDataCount(_ s: Standing) -> Int { Data(count: s.position).count } // shape: data-count
func shapeDataRepeating(_ s: Standing) -> Int { Data(repeating: 0, count: s.position).count } // shape: data-repeating
func shapeRepeatElement(_ s: Standing) -> Int { Array(repeatElement(0, count: s.position)).count } // shape: repeat-element
// ALLOWED, each: a served number compared, and shown.
func shapeCompared(_ s: Standing) -> Bool { s.position > 3 } // allowed: compared
func shapeShown(_ s: Standing) -> String { "#\(s.position)" } // allowed: shown

// #242, the security review's B1: the twins above, met by reference rather than applied: a function handed to an
// element method, held as a value, or named in a key path; and (past the review) an app function handed to `map`,
// which the flow does not follow, and a closure literal called on the spot. REFUSED, each, on its line.
func shapeMapAbs(_ s: Standing) -> Int { [s.position].map(abs).first ?? 0 } // shape: map-abs
func shapeAbsValue(_ s: Standing) -> Int { let f: (Int) -> Int = abs; return f(s.position) } // shape: abs-value
func shapeMaxValue(_ s: Standing) -> Int { let m: (Int, Int) -> Int = max; return m(s.position, 3) } // shape: max-value
func shapeMapMagnitude(_ s: Standing) -> UInt { [s.position].map(\.magnitude).first ?? 0 } // shape: map-magnitude
func shapeKeyPathMagnitude(_ s: Standing) -> UInt { s.position[keyPath: \.magnitude] } // shape: keypath-magnitude
func shapeMapWords(_ s: Standing) -> [Int] { [s.position].map(\.words.count) } // shape: map-words
func shapeMapTruncating(_ s: Standing) -> [Int] { [s.position].map(Int.init(truncatingIfNeeded:)) } // shape: map-truncating
func shapeBumped(_ x: Int) -> Int { x + 1 }
func shapeMapAppFunction(_ s: Standing) -> [Int] { [s.position].map(shapeBumped) } // shape: map-app-function
func shapeCalledLiteral(_ s: Standing) -> Int { { $0 + 1 }(s.position) } // shape: called-literal

// #242, the security review's round 2, B1: a key path not written in place (bound to a name, or a parameter), and a
// method of a served number referenced without a call. REFUSED, each, on its line: the gate refuses what it cannot
// read, and judges a method reference as it judges the call.
func shapeKeyPathHeld(_ s: Standing) -> UInt { let kp = \Int.magnitude; return s.position[keyPath: kp] } // shape: keypath-held
func shapeKeyPathHeldInClosure(_ s: Standing) -> [UInt] { let kp = \Int.magnitude; return [s.position].map { $0[keyPath: kp] } } // shape: keypath-held-closure
func shapeKeyPathParameter(_ s: Standing, _ kp: KeyPath<Int, UInt>) -> UInt { s.position[keyPath: kp] } // shape: keypath-parameter
func shapeKeyPathParameterUse(_ s: Standing) -> UInt { shapeKeyPathParameter(s, \.magnitude) }
func shapeMethodHeld(_ s: Standing) -> Int { let g = s.position.advanced(by:); return g(1) } // shape: method-held
func shapeDistanceHeld(_ s: Standing) -> Int { let g = s.position.distance(to:); return g(10) } // shape: distance-held
func shapeSignumHeld(_ s: Standing) -> Int { let sg = s.position.signum; return sg() } // shape: signum-held

// #373 (G-2): a served number reached through a key path walked from its struct, and a method of a served number
// called curried on its type. REFUSED, each, on its line.
func shapeStructKeyPath(_ s: Standing) -> UInt { s[keyPath: \Standing.position.magnitude] } // shape: struct-keypath
func shapeStructMapMagnitude(_ s: Standing) -> [UInt] { [s].map(\.position.magnitude) } // shape: struct-map-magnitude
func shapeStructMapWords(_ s: Standing) -> [Int] { [s].map(\.position.words.count) } // shape: struct-map-words
func shapeCurriedAdvanced(_ s: Standing) -> Int { Int.advanced(by:)(s.position)(1) } // shape: curried-advanced
func shapeCurriedSignum(_ s: Standing) -> Int { Int.signum(s.position)() } // shape: curried-signum

// #371 (D-218 clause 4, G-2): a served number handed to a generic of the app's own whose parameter is constrained to a
// numeric protocol, directly, by a `where` clause, through a protocol of the app's own that refines one, as `some`, as
// an existential, and into a generic type and a generic method. The gate cannot follow arithmetic on `T`. REFUSED,
// each, on the line marked.
func shapeGenericTwice<T: Numeric>(_ x: T) -> T { x + x }
func shapeGenericWhere<T>(_ x: T) -> T where T: BinaryInteger { x * 2 }
protocol ShapeBumpable: AdditiveArithmetic {}
extension Int: ShapeBumpable {}
func shapeGenericOwn<T: ShapeBumpable>(_ x: T) -> T { x + x }
func shapeGenericSome(_ x: some BinaryInteger) -> Int { Int(x) + 1 }
func shapeGenericAny(_ x: any Numeric) -> Int { (x as? Int ?? 0) + 1 }
struct ShapeGenericBox<T: Numeric> { let v: T; func doubled() -> T { v + v } }
struct ShapeGenericHelper { func twice<T: FixedWidthInteger>(_ x: T) -> T { x &* 2 } }
func shapeGeneric(_ s: Standing) -> Int { shapeGenericTwice(s.position) } // shape: generic-numeric
func shapeGenericByWhere(_ s: Standing) -> Int { shapeGenericWhere(s.position) } // shape: generic-where
func shapeGenericByOwn(_ s: Standing) -> Int { shapeGenericOwn(s.position) } // shape: generic-own-protocol
func shapeGenericBySome(_ s: Standing) -> Int { shapeGenericSome(s.position) } // shape: generic-some
func shapeGenericByAny(_ s: Standing) -> Int { shapeGenericAny(s.position) } // shape: generic-any
func shapeGenericType(_ s: Standing) -> Int { ShapeGenericBox(v: s.position).doubled() } // shape: generic-type
func shapeGenericMethod(_ s: Standing) -> Int { ShapeGenericHelper().twice(s.position) } // shape: generic-method

// #371 (D-218 clause 4, G-2): a served number rebuilt from comparisons inside a closure that counts or searches, one
// shape for each method the ruling names; a test inside such a closure by `if`, by `contains(_:)` and by a function
// of the app's own; and a predicate handed by name and held in a constant. REFUSED, each, on the line marked.
func shapeRebuiltFilter(_ s: Standing) -> Int { (1...100).filter { $0 <= s.position }.count + 1 } // shape: rebuilt-filter
func shapeRebuiltFirst(_ s: Standing) -> Int? { (0..<100).first { $0 == s.position } } // shape: rebuilt-first
func shapeRebuiltFirstIndex(_ s: Standing) -> Int? { Array(0..<100).firstIndex { $0 == s.position } } // shape: rebuilt-first-index
func shapeRebuiltLastIndex(_ s: Standing) -> Int? { Array(0..<100).lastIndex { $0 == s.position } } // shape: rebuilt-last-index
func shapeRebuiltLast(_ s: Standing) -> Int? { Array(0..<100).last { $0 == s.position } } // shape: rebuilt-last
func shapeRebuiltCountWhere(_ s: Standing) -> Int { (1...100).count { $0 <= s.position } } // shape: rebuilt-count-where
func shapeRebuiltContains(_ s: Standing) -> Bool { (1...100).contains { $0 == s.position } } // shape: rebuilt-contains
func shapeRebuiltAllSatisfy(_ s: Standing) -> Bool { (1...100).allSatisfy { $0 != s.position } } // shape: rebuilt-all-satisfy
func shapeRebuiltDropWhile(_ s: Standing) -> Int { (1...100).drop { $0 < s.position }.count } // shape: rebuilt-drop-while
func shapeRebuiltPrefixWhile(_ s: Standing) -> Int { (1...100).prefix { $0 <= s.position }.count } // shape: rebuilt-prefix-while
func shapeRebuiltReduce(_ s: Standing) -> Int { (1...100).reduce(0) { $1 <= s.position ? $0 + 1 : $0 } } // shape: rebuilt-reduce
func shapeRebuiltInIf(_ s: Standing) -> Int { (1...100).filter { if $0 <= s.position { return true }; return false }.count } // shape: rebuilt-in-if
func shapeRebuiltByContains(_ s: Standing) -> Int { (1...100).filter { [s.position, 0].contains($0) }.count } // shape: rebuilt-by-contains
func shapeAtMost(_ x: Int, _ limit: Int) -> Bool { x <= limit }
func shapeRebuiltByHelper(_ s: Standing) -> Int { (1...100).filter { shapeAtMost($0, s.position) }.count } // shape: rebuilt-by-helper
func shapeRebuiltByName(_ s: Standing) -> Int {
    func below(_ x: Int) -> Bool { x <= s.position } // shape: rebuilt-by-name
    return (1...100).filter(below).count
}
func shapeRebuiltHeld(_ s: Standing) -> Int {
    let below = { (x: Int) -> Bool in x <= s.position } // shape: rebuilt-held
    return (1...100).filter(below).count
}
func shapeRebuiltTwice(_ s: Standing) -> Int { (1...100).filter { $0 <= s.position && $0 * 2 <= s.position }.count } // shape: rebuilt-twice

// #371 (D-218 clause 4): a comparison with a served number in `if`, in a closure that neither counts nor searches, in
// a sort and in `max(by:)` stays ADMITTED, each line (a sort is counted per file by `SORTS_PERMITTED` all the same).
func shapeComparedInIf(_ s: Standing) -> Int { if s.position > 3 { return 1 }; return 0 } // allowed: compared-in-if
func shapeComparedInMap(_ s: Standing) -> [Int] { [s].map { if $0.position > 3 { return 1 }; return 0 } } // allowed: compared-in-map
func shapeComparedInSort(_ ranked: [Standing]) -> [Standing] { ranked.sorted { $0.position < $1.position } } // allowed: compared-in-sort
func shapeComparedInMax(_ ranked: [Standing]) -> Standing? { ranked.max { $0.position < $1.position } } // allowed: compared-in-max
