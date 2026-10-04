---
record_type: design
id: stranger-first-use-protocol
status: draft
process_version: v6.6
date: 2026-10-04
---
# A stranger's first use: the protocol (#91, W-123)

**Why.** Every question the router has been tuned and measured on was written by the project: by
the author, or by an independent seat asked to imagine a reader. W-123 records what that costs. In
M18-W3 the on-device model read many genuine searches as something else, and many inputs that were
not searches as searches (`docs/research/m18-w3-question-reading-probe-2026-10-04.md`). The only
evidence of what people actually ask is people asking. This protocol gets that evidence without
anything they type leaving their device unless they agree (D-126).

**What it produces.** A held-out set of real first questions. The next measure of #66, #73 and
#113 runs on it once, before anyone tunes on it (D-147 clause 5).

## 1. Who

- **Three to five people** who have not seen the app, its screens or this project, and who would
  plausibly want to choose an AI model. They do not need to work in software.
- **Both languages.** At least one person who writes in Turkish and one who writes in English.
- **Not the owner, and not anyone who has read the app's examples** ("which model writes the best
  SQL" and the like). Someone who has read them will write like them.

## 2. How the app reaches them

The engine runs on the owner's Mac. It reaches a phone only on the owner's network, and only once the
owner opts in (D-171). So the session is in person, on the owner's network:

- **On the owner's iPhone** (the simplest). Install a build from `main`. Clear the gap register
  first ("Clear" on the register screen), so it holds only this session.
- **Or on their own iPhone,** with a development build installed by the owner from Xcode. Then the
  register on their phone is theirs, and it is deleted with the app at the end.

Start the engine with `scripts/install_engine_service.sh --lan`, and check that `/health` answers
from the phone before the person arrives.

## 3. What they are told

Read this, and nothing else. Answer no question about what the app can do until the session is over.

> **English.** "This app suggests which AI model to use for something you want to do. Type what you
> would like to use an AI model for, in your own words, as many times as you like. There are no
> right answers. I will note what you type. At the end you choose which of your questions I may
> keep. The ones you let me keep will be published, without your name, in the project's public
> code repository, where anyone can read them, to test the app."
>
> **Türkçe.** "Bu uygulama, yapmak istediğin bir iş için hangi yapay zekâ modelini kullanacağını
> önerir. Bir yapay zekâ modelini ne için kullanmak istediğini kendi cümlelerinle, istediğin kadar
> yaz. Doğru cevap yok. Yazdıklarını not alacağım. Sonunda hangi sorularını saklayabileceğime sen
> karar vereceksin. Saklamama izin verdiklerin, adın olmadan, projenin herkese açık kod deposunda
> yayımlanacak; herkes okuyabilecek. Uygulamayı sınamak için kullanılacaklar."

Do not show them an example question, the surface list or the chooser. If they ask "what should I
write?", answer: "Whatever you would really want an AI model for."

## 4. What is recorded, and where

- **During the session,** the owner writes down, on paper or in a note on the owner's own device,
  each thing typed, exactly as typed. Beside each one, write what the screen did:
  - the surface shown;
  - "not measured";
  - the note;
  - or the question back, and which tap they chose.
- **Nothing else is recorded.** There are no screen recordings or screenshots of their typing, and
  no name in any note. Each person is "P1", "P2" and so on.
- **The app itself sends nothing.** What is typed never reaches the engine (D-126, REQ-RTR-004). The
  gap register keeps unmeasured questions on the phone only (REQ-GAP-001).

## 5. Consent, at the end

- Show the person the notes of what they typed. They strike out anything they do not want kept,
  without giving a reason.
- **Ask for the publication by name.** Say again that what they keep will be public, without their
  name, in the project's code repository, and that anyone can read it. A question that says
  anything about them or someone they know should be struck, whatever they decide (the W6 review's
  M3: free text can carry anything about a person).
- What is left is kept only with their spoken yes to that. Write "P2 agreed to publication, <date>"
  under their list.
- If they say no to all of it, the list is destroyed there and then.
- Clear the gap register on the phone they used, or delete the development build from theirs.
- **Close the home network.** Run `scripts/install_engine_service.sh --no-lan` once the last person
  has gone, so the engine answers this Mac only again (D-171 note 7: `--no-lan` is the one control).

## 6. From notes to a held-out set

The author of the router must never read the questions before they are measured (D-147 clause 5).
So:
1. The owner gives the kept notes to an **independent seat**: a fresh agent session, told to write the
   set and nothing else. It has not worked on the router's wording.
2. That seat writes `scripts/router_probe/stranger_heldout_<YYYY-MM-DD>_questions.json`, one row per
   question: `{"q": "<as typed>", "expected": "<surface id, UNMEASURED, or NOT_A_SEARCH>", "class":
   "<kind>"}`. It labels each by the owner's notes and D-169's line. Where it is unsure, it marks
   the row `ambiguous`.
3. The file name matches `*heldout*_questions.json`, so
   `test_no_held_out_question_is_written_into_the_code_or_its_tests` treats it as live from the
   moment it lands. No question of it may appear in code or tests.
4. The router's author sees only counts until the set has been measured once, twice over, as M18-W3
   did. Then it is spent, and its misses may be read.

## 7. Done when

- At least **40 questions from at least 3 people**, with at least 10 in each language, are kept with
  consent and written as the set above.
- The session notes, without names, are attached to #91 by the owner. The questions themselves are
  not attached, since the issue is public.

## 8. What this protocol does not do

- **It is not a usability study.** It does not time anything, and it asks nothing about the screen.
  A finding about the screen goes to an issue as usual.
- **It does not need TestFlight or a server.** Both would send what is typed somewhere else, or need
  the engine off the Mac (D-116, D-171). Either one is a decision for the owner, with its own ADR.
