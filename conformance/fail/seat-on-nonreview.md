---
record_type: closure
id: fixture-fail-seat-on-nonreview
status: ratified
seat: independent
---
<!-- expect: R6 -->

# R6 fixture — `seat` on a record that is not a review

V4C-35: a field may exist only if a check consumes it. `seat` is consumed for reviews and nowhere
else, so carrying it on a closure record is a field with no reader — the sediment the record
contract was written to stop.
