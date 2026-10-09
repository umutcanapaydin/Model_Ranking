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
