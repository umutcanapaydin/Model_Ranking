# The iOS client (M8)

The app renders answers the engine computes. **It holds no ranking logic of its own** — no sorting,
no budget arithmetic, no derived "best" flag. If a screen needs a value `/v1` does not serve, that
is a finding against the API (D-124), not a licence to compute it here.

## Running it

Two processes. The engine first, on the Mac:

    make run

Then open `ios/ModelRanking.xcodeproj` in Xcode and run on any iPhone simulator. The simulator
shares the Mac's loopback, so `EngineClient.localDefault` (`http://127.0.0.1:8080`) reaches it.

If the engine is not running the app says so and names the command — it does not show a spinner
forever, and it does not show stale or invented data. There is no mock payload anywhere in the
target; a screen with numbers on it is a screen that reached the engine.

## Why `Models.swift` looks mechanical

Every field mirrors `PUBLIC_ANSWER_FIELDS` / `PUBLIC_PICK_FIELDS` in `src/app/adapter/main.py`, and
the shape was read off a live response rather than written from memory. A Swift struct authored
from an imagined payload is precisely the "typed-out enumeration" this project has been caught by
five times, and it would fail silently: a `Decodable` with an optional it should not have decodes a
broken payload happily.

The decoder is verified against real captured responses — both the two-surface `coding` case and
the zero-pick `assistant` case — rather than against a fixture someone wrote to match the struct.

## What is deliberately plain

W1 is one screen. It exists to prove the seam: Swift's decoder, the simulator's network stack, a
running engine. **Design is W2's**, and W2 opens with a decision only the owner can make — how do
you show two EQUAL answers on a phone, when a list has a first item and tabs have a selected one?
There is no neutral presentation. Until he rules, this screen makes the least-committal choice
available: both answers laid out identically, under the engine's own sentence saying the order
carries no meaning.
