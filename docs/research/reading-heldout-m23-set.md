# reading_heldout_m23_questions.json

**Written 2026-10-16** by an independent seat: a subagent dispatched for this set alone, which wrote no
routing code and reviewed none.

## Independence rule

The author did not read the routing code or its examples: not `ios/ModelRanking/Engine/Router.swift`,
`Reading.swift`, `Refinements.swift`, `ScriptedRouting.swift`, nor anything else under `ios/ModelRanking/`
(D-191, D-196). The author read only:
- the served surfaces, from the public `GET https://model-ranking.fly.dev/v1/categories` (14 ids);
- `scripts/router_probe/reading_heldout_m22_questions.json`, for its format only;
- `docs/research/reading-wave-m22-probe.md`, for how such a set is built and scored;
- issues #218, #273 and #66, for the problems the next rules target.

## Format

A JSON list of `[question, label]`, UTF-8. A label is one surface id, several acceptable ids joined by
`|`, or `NOT_A_SEARCH`. A search is labelled by what it asks for. Questions are typed the way people
type: typos, missing punctuation, mixed case, Turkish with and without its letters.

## Uniqueness

No question equals (after case folding, NFC and dropping punctuation) any string in any JSON under
`scripts/router_probe/` or `docs/research/judgement/` (22 files, 1222 strings): 0 collisions. No
question is within a `difflib` ratio of 0.9 of one either (highest 0.875). The check printed counts and
row numbers only, never text from the existing sets.

## Counts

168 rows: 96 searches, 72 `NOT_A_SEARCH`.

| language | searches | not a search | total |
|---|---:|---:|---:|
| English | 36 | 24 | 60 |
| Turkish | 37 | 26 | 63 |
| Spanish | 3 | 3 | 6 |
| German | 3 | 3 | 6 |
| French | 2 | 3 | 5 |
| Portuguese | 2 | 2 | 4 |
| Kurmanji | 3 | 2 | 5 |
| Azerbaijani | 3 | 2 | 5 |
| Russian, Cyrillic | 2 | 2 | 4 |
| Russian, Latin letters | 2 | 2 | 4 |
| Arabic | 3 | 2 | 5 |
| none (keyboard mash) | 0 | 1 | 1 |

Turkish searches: 20 of the 37 are five words or fewer (8 of those with Turkish letters, 12 without);
16 of the 37 hold a Turkish letter. The Azerbaijani rows carry `ə` where the language writes it, except
where a question naturally has none.

| label | rows |
|---|---:|
| `NOT_A_SEARCH` | 72 |
| `coding` | 14 |
| `mathematics` | 11 |
| `assistant` | 8 |
| `vision` | 8 |
| `document` | 8 |
| `expert` | 6 |
| `factuality` | 6 |
| `abstract` | 6 |
| `web-dev` | 5 |
| `search` | 4 |
| `agentic-coding` | 4 |
| `computer-use\|agentic-coding` | 3 |
| `everyday` | 2 |
| `search_factuality` | 2 |
| `computer-use` | 2 |
| `everyday\|assistant` | 2 |
| `coding\|agentic-coding` | 1 |
| `vision\|document` | 1 |
| `search_factuality\|search` | 1 |
| `factuality\|everyday` | 1 |
| `web-dev\|coding` | 1 |

## Non-search categories (72)

| category | rows | what it is |
|---|---:|---|
| brand or knowledge trivia | 19 | a question about a painter, a wind, an animal, a zodiac sign, a pilot, a stock or a match, often one that names an AI brand word (Claude, Gemini, Mistral, Llama, Opus, Copilot, DeepSeek), and plain knowledge questions |
| chit-chat | 17 | greetings, thanks, "I'm bored" small talk |
| task requests | 15 | asking the app to do the work: a poem, a translation, a code fix, an equation, a summary, homework |
| prompt injections | 9 | instructions to drop the rules, reveal a prompt or a key, change persona, or fix a ranking |
| questions about the app | 7 | how it ranks, where the scores come from, who made it, whether it is paid or collects data |
| gibberish | 5 | keyboard mash and repeated letters |

A few searches sit near these lines on purpose: a search that names brands ("kod icin claude mu gpt mi
daha iyi"), and searches that ask for a model to talk to when bored, which are `assistant`, not chit-chat.
