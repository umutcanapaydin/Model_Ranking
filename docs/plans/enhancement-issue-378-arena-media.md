# Enhancement plan: LMArena's five image and video boards, ranked on quality only (#378)

**Golden Rules served:** 3 (the most correct list for every question): a request to make an image or a video today has no board, and declines.

## Goal

Five new surfaces answer image and video questions from LMArena's own boards: `image_edit`, `text_to_image`, `image_to_video`, `text_to_video`, `video_edit`. They rank on quality only (the owner's ruling of 2026-10-21, option 1, on #378).

## Scope

**In:**
- the five `ArenaBoard` entries in `src/app/clients/arena.py`, each with a parser test on a recorded fixture and a contract test;
- five surfaces in `src/app/workflows/categories.py`, each with a `score_anchor`, a D-148 calibration note, a router hint and a Turkish title;
- `/v1` answering them with no price column, no value window and no `budget` filter, and the app's detail screen saying the price is not measured;
- the router: a request to make an image or a video routes to its surface, which reverses #113's and #192's decline hint;
- the router probe set, with at least one probe per surface.

**Out:**
- a price in each surface's own unit (per image, per second), which becomes its own issue;
- the four `*_style_control` configs, skipped as duplicates;
- any new publisher: LMArena is already credited.

## Decisions

1. **The price basis:** quality only (the owner's ruling, recorded as an ADR in its own commit before the code).
2. **The decline hint is reversed** for making images and videos. Editing a user's own photo routes to `image_edit`.

## Phases

1. **The ADR**, alone: the ruling, the reversed decline, and the surfaces' price rule.
   *Acceptance:* `make check-records` green.
2. **The boards:** five `ArenaBoard` entries, with recorded fixtures, parser tests (red first) and contract tests.
   *Acceptance:* each board's rows parse, and the build reads them.
3. **The surfaces:** five surfaces calibrated on their boards (D-148), whose `/v1` answers carry no price, value window or budget.
   *Acceptance:* a red test per rule, then the engine serves each surface with a ranked list.
4. **The app:** the router hints, the narrowed decline hint, the Turkish titles, the detail screen's price note, and the probes.
   *Acceptance:* `swift test` green, and each new probe routes to its surface.
