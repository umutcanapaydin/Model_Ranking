import CoreGraphics
import Foundation

// A press-move-release drag. The Simulator translates this into a swipe; scroll-wheel events it
// appears to ignore.
let a = CommandLine.arguments
let x = Double(a[1])!, y0 = Double(a[2])!, y1 = Double(a[3])!
let steps = 30

func post(_ type: CGEventType, _ p: CGPoint) {
    if let e = CGEvent(mouseEventSource: nil, mouseType: type, mouseCursorPosition: p,
                       mouseButton: .left) {
        e.post(tap: .cghidEventTap)
    }
}

CGWarpMouseCursorPosition(CGPoint(x: x, y: y0)); usleep(300_000)
post(.leftMouseDown, CGPoint(x: x, y: y0)); usleep(120_000)
for i in 1...steps {
    let t = Double(i) / Double(steps)
    post(.leftMouseDragged, CGPoint(x: x, y: y0 + (y1 - y0) * t))
    usleep(12_000)
}
usleep(80_000)
post(.leftMouseUp, CGPoint(x: x, y: y1))
