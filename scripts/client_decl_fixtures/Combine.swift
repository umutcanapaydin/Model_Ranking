// #60 (G-2): the one file D-167 lets rank positions. Its permitted arithmetic and its one permitted
// sort the gate must ALLOW; the second sort on the same name, the M17-W4 Tester's M7, it must REFUSE.
import Foundation

func fixtureCombinedRank(_ standing: Standing) -> Int {
    1 + standing.position
}

func fixtureCombines(_ standings: [Standing]) -> [String] {
    let common = standings.map(\.model)
    return common.sorted()
}

func fixtureCombinesTwice(_ standings: [Standing]) -> [String] {
    let common = standings.map(\.model)
    return common.sorted()
}
