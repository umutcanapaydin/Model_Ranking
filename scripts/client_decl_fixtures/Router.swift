// #60 (D-181, the W2 review's M5): the price in pages is the one arithmetic REQ-CMP-002 permits here, in
// `priceInPages` alone. ALLOWED there; a second one in this file is REFUSED.
import Foundation

func priceInPages(_ blendedPerM: Double) -> Double {
    blendedPerM / 1500
}

func fixtureRouterDiscounts(_ pick: Pick) -> Double {
    let price = pick.blendedPerM
    return price * 0.8
}
