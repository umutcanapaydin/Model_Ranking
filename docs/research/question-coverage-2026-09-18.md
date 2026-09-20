---
record_type: research
id: question-coverage-2026-09-18
status: draft
process_version: v5.0
date: 2026-09-18
---
# Every question a person might ask, and where the answer would come from

**Status: a direction the owner gave, with the parts that are already true separated from the parts
that are not yet work.** Written the same night as D-142 and M14-W1, from the owner's message at
02:36. It is not a plan and nothing here is scheduled.

## What the owner asked for

Translated from Turkish: *"A tax officer could come and ask which one produces the best tax table.
We will rank that too and understand it. A gardener asks what gives the best plant-pruning answer.
All the questions that could come actually have a place in some scientific category, don't they —
and against that, if necessary we intervene in the existing lists with the benchmark data we have,
compare benchmarks well enough to pick our own list and leaderboard, find a logic; using Apple
Intelligence to understand the search bar live, or hooking up a free LLM endpoint if we need live
understanding; or as a last resort we find data on what humans are actually asking models, research
it, then collect the best benchmark lists we can and apply them, and produce say 400 or 500 separate
lists. The job can be this big, that's fine. Nobody is doing this. We will."*

## 1. Part of it is already bought and paid for

`lmarena-ai/leaderboard-dataset` — CC-BY-4.0, already ingested, Stage-0 gate already passed —
carries **22 boards**, and this project reads two of them:

```
agent · agent_bash_recovery_steps · agent_praise_complaint · agent_steerability
agent_task_outcome_explicit · agent_tool_hallucination · document · document_style_control
image_edit · image_to_video · search · search_factuality · search_style_control
text · text_factuality · text_style_control · text_to_image · text_to_video
video_edit · vision · vision_style_control · webdev
```

Several answer questions a person would actually ask in their own words — *which model makes things
up least when it uses a tool*, *which one is most accurate when it searches*, *which one follows
correction best*, *which one is best with documents*. Identical column schema to the `text` board, so
the client shape is already written. **This is the cheapest coverage this product will ever buy**,
and it is a better first move than any new source.

## 2. "What do people actually ask" is a measurable question, not a guess

The owner's last-resort idea is a real research method and it has public data: large open corpora of
genuine user prompts to chat models (the LMSYS-Chat-1M and WildChat families are the widely cited
ones). Mining them gives the **distribution of real questions** rather than a list of categories
somebody imagined — so "tax table" and "plant pruning" stop being intuitions and become frequencies,
each with a measurable answer to *does any public benchmark measure this*.

That is the same instrument as M14-W3's gap register, sourced from outside instead of waiting for our
own readers. The two are complementary: the corpus says what the world asks, the register says what
**our** readers ask, and disagreement between them is itself informative.

**Caveat to carry:** these corpora are what people asked a chat assistant. They are biased toward
what people already believe an assistant can do, so they under-represent exactly the questions this
product wants to serve. Treat them as a floor on demand, never a ceiling.

## 3. The boundary, and it is not a preference

The owner raises hooking up a free LLM endpoint for live understanding. The line D-104 and D-126 draw
is not about which model or how much it costs:

- **An LLM choosing which measured surface a question belongs to is allowed, and already ships.**
  Apple Intelligence does exactly this, constrained by a generation schema to the nine ids the engine
  serves plus a decline sentinel, so it *cannot* express a recommendation. On 2026-09-18 it correctly
  recognised a misspelled `Image enchantment` as something we do not measure and declined.
- **An LLM answering the question — saying a model is good — is not**, at any price. The product's
  only defensible claim is that its answers come from measurement. A reader who wants a language
  model's opinion about language models can already get one for free, from the language model. They
  do not need us for that, and the moment we offer it we are a worse version of a thing that already
  exists.

So the strongest form of the owner's vision is: **let a model understand the question; make the
measurement answer it.** Where nothing measures it, say so and put the gap in the queue. That is the
same shape as the front door already built — the vision extends its reach rather than replacing it.

## 4. What "400–500 lists" honestly means

A list is only worth having if something measures it. 400 lists therefore means 400 measurements, and
the count of real, licensable, non-junk benchmark boards in the world is far below that today. The
honest restatement, which loses nothing the owner asked for:

> **400–500 questions, mapped onto however many measured surfaces exist, with the unmeasured ones
> named and ranked by how often they are asked.**

The question-to-category map can be as large as we like — it costs a routing hint, not a benchmark.
The number of *surfaces* grows at the speed of licensable measurement. Conflating the two is the
Finding 1 error (a coverage gap read as a measurement gap) at a larger scale.

One warning from the literature, since the plan is to ingest widely: a systematic review of 445 LLM
benchmarks found only 16% using uncertainty estimates and 27% using convenience sampling. **A bad
benchmark is worse than no benchmark, because it contaminates every aggregate it enters.** Ingesting
widely and ranking on everything ingested are two different decisions.

## 5. Where this would start, if it were scheduled

1. Unpack the boards we already have rights to (§1). No new licence, no new client shape.
2. Mine a public prompt corpus for the real question distribution (§2), and check it against the gap
   register once M14-W3 has one.
3. Keep the routing layer free to understand anything; keep the answering layer refusing to speak
   without a measurement (§3).
