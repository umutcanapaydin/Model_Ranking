# App Store listing — Model Ranking 1.1.0

The text and answers App Store Connect asks for the first submission (D-252). The owner pastes each field
in App Store Connect → the app → the 1.1.0 version, and its App Information and App Privacy pages. The Turkish
localisation of the same fields is `docs/app-store-listing.tr.md`. Character limits are App Store Connect's;
each field below is within its limit.

## App Information

| Field | Value |
|---|---|
| Name (30) | `Model Ranking` |
| Subtitle (30) | `AI models, ranked by evidence` |
| Primary category | Developer Tools |
| Secondary category | Productivity |
| Content rights | Does not contain, show or access third-party content it lacks the rights to: every number is a published measurement shown with its publisher's credit, under an open licence or terms that do not forbid it (D-215, D-252 clause 2) |
| Age rating | 4+ (every questionnaire answer: None / No) |
| Price | Free, every territory |

**Age rating questionnaire:** every content descriptor is **None**. Unrestricted web access: **No** (the app opens no web page; the Credits screen shows each publisher's link as text). Gambling, contests, user-generated content, messaging: **No**.

## Version 1.1.0

**Promotional text (170):**

```
Ask which AI model fits a job and your budget, and get a ranked list built only from published benchmark results, each with its source.
```

**Description (4,000):**

```
Which AI model is best for writing code? For reading a document? For math, search or images, and which of them fits your budget?

Model Ranking answers with evidence, not opinion. Type your question in your own words. The app works out which task you mean and shows a ranked list for it, built only from published benchmark results and published prices.

WHAT YOU GET
• A ranked list for the task you asked about: coding, agentic coding, operating a computer, mathematics, expert questions, everyday chat, documents, factual answers, search, vision, image and video generation, web development, and puzzles.
• A budget filter: see which models fit what you are willing to spend, priced per million tokens.
• Honest uncertainty: when two models are within the margin of error, the app says so. When the evidence is old, missing or mixed, it says that too, instead of hiding it.
• The source of every number: each list names the benchmark it comes from, and the Credits screen lists every publisher.

HOW IT WORKS
• Your question is understood on your device. On iPhones with Apple Intelligence, the on-device model reads it; elsewhere, the app reads it by its words.
• The rankings come from public leaderboards and price lists, refreshed every night: LMArena, SWE-bench, Terminal-Bench, OSWorld-Verified, ARC-AGI, LiveBench, Epoch AI, SimpleBench, Aider, DeepSWE and others, credited in the app.
• Every number on a list is a published measurement. No number is made up or estimated by an AI.

PRIVACY
No account, no sign-in, no tracking, no ads. Your questions stay on your device: the app only downloads the public rankings. The privacy policy is at https://model-ranking.fly.dev/privacy.

Model Ranking is an independent app. It is not affiliated with any model provider or benchmark publisher.
```

**Keywords (100, comma-separated, no spaces):**

```
AI,LLM,benchmark,leaderboard,ranking,compare,model,coding,chatbot,price,budget,evaluation,agent
```

**Support URL:** `https://github.com/umutcanapaydin/Model_Ranking/issues`

**Marketing URL:** leave empty.

**Copyright:** `2026 Umut Can Apaydın`

**What's New:** not shown for a first version.

## App Privacy

- **Privacy Policy URL:** `https://model-ranking.fly.dev/privacy`
- **Data collection:** "No, we do not collect data from this app" → **Data Not Collected** (D-248; the app's
  `PrivacyInfo.xcprivacy` declares no tracking and no collected data).

## Export compliance

The app uses only the encryption built into iOS (HTTPS through `URLSession`). Its Info plist
(`ios/Config/Info.plist`) sets `ITSAppUsesNonExemptEncryption` to `NO`, so App Store Connect does not ask; if
it does, the answer is **No** (only exempt, operating-system encryption).

## App Review information

- **Sign-in required:** No.
- **Contact:** the owner's name, phone and email, entered in App Store Connect (not committed here).
- **Notes:**

```
Model Ranking shows ranked lists of AI models for a task the user types, built from public benchmark leaderboards and price lists. No account or sign-in is needed.

To try it: type "which AI is best for coding" or "cheapest model for reading PDFs" in the box and tap the answer. "Change" picks another task; the Credits screen lists every data source.

Data sources: every number is a published measurement, shown with its publisher's name and link (Credits screen). Each source is used under an open licence (for example Apache-2.0, MIT, CC BY) or under terms that do not forbid showing attributed results in a free app; a source whose page reserves all rights was removed before this submission.

On-device AI: on iPhones with Apple Intelligence (iOS 26), the question is understood by Apple's on-device Foundation Models framework; on other devices the app reads it by its words. No question leaves the device; the app only downloads public ranking data from its own server (model-ranking.fly.dev).
```

## The build

Build **9** of version **1.1.0** (`MARKETING_VERSION`, `CURRENT_PROJECT_VERSION`), archived and uploaded by
`docs/release-testflight.md` §2. Select it under the version's **Build** section before **Submit for Review**.
