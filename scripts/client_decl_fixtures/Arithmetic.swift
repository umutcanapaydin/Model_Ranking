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

func shapeFilterCount(_ s: Standing) -> Int { [s].filter { $0.position > 0 }.count + 1 } // allowed: filter-count

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
