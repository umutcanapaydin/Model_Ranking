# Assumptions — run night-1021

Questions the run met that are reversible and outside a ⛔ zone, each with the most conservative answer taken.


- **m25's set loaded from outside the repository (#355).** `scripts/model_tier.py` knows only golden and m24, and the sealed set must not be committed. The run added it to the script's sets at run time from a scratch wrapper that first checks the set's sha256, and changed no committed file. Reversible: a later judgement can add a `--set-file` option instead.
