-- Connect Hardware Keyboard: ON, idempotently.
--
-- The owner asked for BOTH keyboards — typing from the Mac (which he found pleasant) and the app's
-- own keyboard on tap, because that is what the app looks like on a phone. Only half of that can be
-- automated, and the reason is worth writing down rather than discovering twice:
--
--   `Connect Hardware Keyboard`  => carries a check mark, so its state can be READ. Safe to ensure.
--   `Toggle Software Keyboard`   => no mark char at all. It is a pure toggle with no readable
--                                   state, so a script cannot ensure it — it can only FLIP it.
--
-- An earlier version of this file clicked both. Run twice, it turned the software keyboard back
-- off, which is worse than not touching it: a helper that leaves a setting in a state nobody chose
-- is a helper you have to check after, and then it is not helping. So it ensures the half it can
-- read and prints the shortcut for the half it cannot.
--
-- Needs Accessibility permission for whatever runs it.

tell application "Simulator" to activate
delay 1

tell application "System Events" to tell process "Simulator"
	tell menu bar 1 to tell menu bar item "I/O" to tell menu 1 to tell menu item "Keyboard" to tell menu 1
		set theMark to missing value
		try
			set theMark to value of attribute "AXMenuItemMarkChar" of menu item "Connect Hardware Keyboard"
		end try
		if theMark is missing value or theMark is "" then
			click menu item "Connect Hardware Keyboard"
			return "hardware keyboard: turned on"
		end if
		return "hardware keyboard: already on"
	end tell
end tell
