//  probe.swift — the wording tier's calibration probe (docs/reviews/m15-router-recalibration.md).
//
//  A standalone replica of `SimilarityRouter.route`'s arithmetic that PRINTS every score, because
//  `swift test` only says pass or fail and the margins are what a hint change moves. Run from this
//  folder (`build/` at the repository root is gitignored):
//
//      python3 extract_examples.py ../../build/examples.json
//      swiftc -O probe.swift -o ../../build/probe
//      ../../build/probe ../../build/examples.json probe_questions.json      # add a 3rd argument: misses only
//      ../../build/probe ../../build/examples.json heldout_questions.json
//
//  MODE=max|top2|mean picks how a group of examples scores (the router ships top2). FLOOR defaults
//  to SimilarityRouter.defaultFloor. An expected id ending in `~` passes when it is the answer OR
//  the first one-tap alternative of a decline; `a|b~` accepts either. `DECLINE` expects unmeasured.
//  If this and Router.swift ever disagree, Router.swift is right and this file is the defect.
import Foundation
import NaturalLanguage
struct Config: Decodable { let examples: [String: [String]]; let declines: [[String]] }
let args = CommandLine.arguments
let cfg = try! JSONDecoder().decode(Config.self, from: Data(contentsOf: URL(fileURLWithPath: args[1])))
let raw = try! JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: args[2]))) as! [[String]]
let cases = raw.map { ($0[0], $0[1]) }
let mode = ProcessInfo.processInfo.environment["MODE"] ?? "top2"
let served = ["coding","agentic-coding","assistant","everyday","expert","mathematics","computer-use",
              "abstract","web-dev","document","factuality","vision","search","search_factuality"]
let emb = NLContextualEmbedding(language: .english)!; try! emb.load()
func vector(_ s: String) -> [Double] {
  let r = try! emb.embeddingResult(for: s, language: .english)
  var t = [Double](repeating: 0, count: emb.dimension); var n = 0
  r.enumerateTokenVectors(in: s.startIndex..<s.endIndex) { tok, _ in
    for i in 0..<min(tok.count, t.count) { t[i] += tok[i] }; n += 1; return true }
  return t.map { $0 / Double(n) }
}
let ex = served.map { id in (id, cfg.examples[id]!.map(vector)) }
let d = emb.dimension
var mean = [Double](repeating: 0, count: d); var cnt = 0.0
for (_, vs) in ex { for v in vs { for i in 0..<d { mean[i] += v[i] }; cnt += 1 } }
mean = mean.map { $0 / cnt }
func c(_ v: [Double]) -> [Double] { (0..<d).map { v[$0] - mean[$0] } }
func cos(_ a: [Double], _ b: [Double]) -> Double {
  var dot = 0.0, na = 0.0, nb = 0.0
  for i in 0..<d { dot += a[i]*b[i]; na += a[i]*a[i]; nb += b[i]*b[i] }
  return dot / (na.squareRoot()*nb.squareRoot() + 1e-9)
}
let exC = ex.map { ($0.0, $0.1.map(c)) }
let decC = cfg.declines.map { $0.map { c(vector($0)) } }
func agg(_ s: [Double]) -> Double {
  let t = s.sorted(by: >)
  if mode == "max" { return t[0] }
  if mode == "top2" { return (t[0] + t[1]) / 2 }
  return s.reduce(0,+) / Double(s.count)
}
let floor = Double(ProcessInfo.processInfo.environment["FLOOR"] ?? "0.15")!
var pass = 0
for (q, want) in cases {
  let qv = c(vector(q))
  let scored = exC.map { ($0.0, agg($0.1.map { cos(qv, $0) })) }.sorted { $0.1 > $1.1 }
  let dec = decC.map { agg($0.map { cos(qv, $0) }) }.max()!
  let best = scored[0]
  let declined = dec > best.1 || best.1 < floor
  let alts = declined ? scored.map(\.0).filter { $0 != "assistant" }.prefix(2).map { $0 } : scored.dropFirst().prefix(2).map(\.0)
  var ok: Bool
  if want == "DECLINE" { ok = declined }
  else if want.hasSuffix("~") {
    let set = Set(want.dropLast().split(separator: "|").map(String.init))
    ok = declined ? (set.contains(alts.first ?? "") || (set.count > 1 && !set.isDisjoint(with: alts))) : set.contains(best.0)
  } else { ok = !declined && best.0 == want }
  if ok { pass += 1 }
  if args.count < 4 || !ok {
    print(String(format: "%@ %-52@ -> %-17@ best=%.3f dec=%.3f", ok ? "OK  " : "MISS", q as NSString, (declined ? "DECLINE" : best.0) as NSString, best.1, dec),
      "| want \(want) | top3", scored.prefix(3).map { "\($0.0) \(String(format: "%.3f", $0.1))" }.joined(separator: ", "), declined ? "| alts \(alts)" : "")
  }
}
print("\(pass)/\(cases.count)")
