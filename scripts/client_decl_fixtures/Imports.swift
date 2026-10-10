// #175 R3: a framework off the module allowlist, imported and never used. REFUSED: reaching a
// framework at all is a reviewed change.
import Foundation
import Network
import ObjectiveC

func fixtureImportsOnly() -> Int { 0 }

// The M21 closure security seat's S6: a selector made from text by the runtime's own C function, which no
// by-name rule refuses. REFUSED: `ObjectiveC` is off the module allowlist.
func fixtureRuntimeSelector() -> Selector { sel_registerName("fixtureSelector") }
