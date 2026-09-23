# model_ranking's own check-fast settings (DevFlow v6.5+, INSTALL.md "binding another stack").
# The stack is `python`, so lint, typecheck, test and deps need no binding here; these two lines only
# tell `make check-fast` how to run the project's own gates, which the Makefile's `check:` lists.
#
# client-decls type-checks the iOS client against the SDK (~20 s) and swift-test runs the Engine
# layer's Swift suite (~35 s in parallel): each is as long as the Python leg, so each gets its own.
CHECK_FAST_OWN_LEGS = client-decls swift-test
# `swift test --parallel` prints no count line, so check-fast judges its xUnit report instead
# (scripts/swift_xunit_gate.py); `make check` keeps the serial run and its count floor.
CHECK_FAST_FORMS = swift-test=swift-test-parallel
