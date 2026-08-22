# Simulator gesture helpers

Two dozen lines of Swift that post real mouse events, used to VERIFY a layout rather than assert
one. They exist because of a specific failure: the M11-W3.5 design pass was handed over with half
the screen unseen, recorded as W-066, because there was no way to scroll the Simulator from a
command line — arrow keys do not move a SwiftUI `ScrollView`, and `osascript` cannot post a scroll
wheel.

`sim_drag.swift` does a press-move-release, which the Simulator translates into a swipe. Build and
use it as:

    swiftc -O scripts/simtools/sim_drag.swift -o /tmp/sim_drag
    osascript -e 'tell application "Simulator" to activate'
    /tmp/sim_drag <x> <fromY> <toY>          # screen coordinates, top-left origin

Window geometry comes from:

    osascript -e 'tell application "System Events" to tell process "Simulator" to get position of window 1'
    osascript -e 'tell application "System Events" to tell process "Simulator" to get size of window 1'

**What did NOT work, recorded so the next person does not spend the time again:** scroll-wheel
events (`CGEvent(scrollWheelEvent2Source:)`) are ignored by the Simulator, and synthetic keystrokes
reach the Simulator but do not land in a SwiftUI `TextField` even with Connect Hardware Keyboard
on. Clicks DO land — a probe click selected a category chip. So a layout can be walked from here;
typing into the app cannot, and anything that needs typing is still a person's job.

These are host-side developer tools. They are not part of the app, not in `make check`, and touch
nothing the product ships.
