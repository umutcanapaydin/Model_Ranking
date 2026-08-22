---
record_type: review
id: m10-router-calibration
status: ratified
date: 2026-08-22
---
# Router calibration — M10-W1, measured rather than written by taste

> **The first version of the router did not work at all, and only a probe showed it.** Every
> question fell through to the fallback. The second scored 3 of 8. The shipped one scores 7 of 8.
> Nothing about the code changed between the second and the third — only the words in the hints.

## Why this record exists

The router's quality is not visible from any gate this repository runs. There is no iOS test target
(W-038), the boundary tests assert STRUCTURE — that the closed set comes from the engine, that no
recommendation can travel in the outcome type — and none of them can say whether "fix a bug in my
python repo" actually reaches `coding`. That is the difference between a router and a text field
that changes the screen at random, and it needed measuring.

The probe is a small Swift program run on macOS, where the same `NaturalLanguage` APIs are
available: nine real questions, one per surface plus one the catalogue does not measure, scored
against the hints. Its runs are below.

## Run 1 — `NLEmbedding.sentenceEmbedding`: 1 of 9, and it was not close

```
fix a bug in my python repo          -> assistant(unmeasured)  sim=-0.07
build me a landing page              -> assistant(unmeasured)  sim=-0.01
solve this competition math problem  -> assistant(unmeasured)  sim=-0.00
help me write an email to my landlord-> assistant(unmeasured)  sim=-0.00
```

Every similarity sat at or below zero: the sentence embedding places these texts essentially
orthogonally, so every question fell past the floor to the unmeasured fallback. **The one "correct"
answer was the question that was supposed to fall through.** This is a control that exists, runs,
and does nothing — and it would have shipped, because it compiles, it returns a surface, and the
screen changes when you use it.

## Run 2 — `NLContextualEmbedding`, raw cosine: 3 of 8, with a pathology

```
build me a landing page               -> agentic-coding  cos=0.799
solve this competition math problem   -> agentic-coding  cos=0.828
click through this website...         -> agentic-coding  cos=0.838
help me write an email to my landlord -> agentic-coding  cos=0.818
```

Better, and wrong in an informative way: **everything collapsed onto one surface**, and the cosines
all sat between 0.80 and 0.90. That is anisotropy — every vector in the space carries a large
component they all share, so the nearest hint is whichever one is longest rather than whichever one
matches, and `agentic-coding` had the longest hint.

## Run 3 — centred cosine: 5 of 8

Subtracting the mean hint vector before comparing removes what the hints have in common and leaves
what tells them apart. Scores dropped into a usable range (0.09–0.39) and four surfaces started
resolving correctly. **One line of arithmetic, two more correct answers.**

## Run 4 — sharpened hints, centred: 7 of 8 (shipped)

```
fix a bug in my python repo               -> coding          0.507  OK
build me a landing page                   -> web-dev         0.239  OK
solve this competition math problem       -> mathematics     0.180  OK
explain quantum entanglement to a chemist -> mathematics     0.256  MISS (expected expert)
an agent that refactors my codebase       -> agentic-coding  0.354  OK
click through this website and fill form  -> computer-use    0.302  OK
a logic puzzle with no examples           -> abstract        0.299  OK
help me write an email to my landlord     -> assistant       0.418  OK
which AI should do my taxes               -> everyday        0.187  (see below)
```

The code did not change between run 3 and run 4. The hints did: several of them had described the
same idea in overlapping words, so `assistant` and `everyday` competed for ordinary questions and
`mathematics` absorbed anything technical. Naming the vocabulary a person would actually use —
"HTML", "a proof", "click buttons", "write an email" — separated them.

**The floor is 0.15, and it is measured too.** Correct answers scored 0.18 to 0.51; the unmeasured
question scored 0.19. So the floor separates "nothing like anything" from "a weak but real match"
and deliberately does not try to separate more than that — a tighter floor would have rejected the
correct maths answer at 0.180.

## The one miss, and the one that is arguably not a miss

**`expert` loses to `mathematics`** on a physics question. Both hints name technical subject matter
and the space cannot tell a chemist's question from a proof. Recorded rather than tuned away: with
nine surfaces and a 512-dimension general embedding, some pairs are genuinely close, and hint
tuning past this point is fitting to the probe rather than to users.

**"Which AI should do my taxes" routes to `everyday` at 0.187**, above the floor, so it is NOT
flagged unmeasured. The probe called that a miss. It is defensible: `everyday` is a measured
surface for broad ordinary usefulness, and a general assistant genuinely is the tool for a question
this catalogue does not measure specifically — which is the owner's own ruling on where unmeasured
questions go. What matters is that the surface it lands on is one the engine ranks, and it is.

## What this record does NOT claim

Nine questions is a probe, not an evaluation. It was written by the same person who wrote the
hints, which is exactly the bias this project has measured elsewhere — a mutant set written by the
author tests the author's model of the code. **The honest reading is that tier 2 is materially
better than nothing and materially worse than the on-device model in tier 1**, which is why its
outcome tells the reader it matched on wording and asks them to check the surface is right.
