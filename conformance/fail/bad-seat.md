---
record_type: review
id: fixture-fail-seat
status: ratified
seat: mostly-independent
---
<!-- expect: R6 -->

# R6 fixture — a seat value the enum does not have

D-133 makes a wave close GREEN or not on what this field says, so a value outside
`{author, independent}` is not a typo, it is an unreadable answer to the one question the record
exists to answer. Shipped because V4C-32 says a validator with no fixture for a rule is a no-op
for that rule, and the independent seat measured exactly that: `--self-test` passed without
exercising R6 at all.
