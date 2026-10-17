// #297 (D-206 clause 4): the kept answers' read-back, which the gate must ALLOW: a kept surfaces' list
// decoded in its own file.
import Foundation

enum KeptAnswers {
    static func categories(_ entry: KeptAnswer) -> [Category]? {
        try? JSONDecoder().decode([Category].self, from: entry.payload)
    }
}
