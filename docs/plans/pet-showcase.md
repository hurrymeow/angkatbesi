# Plan: show the pet on the finish screen and in the rest banner

## Goal

Put Bebi where effort and reward happen. Today it shows only on the Train card, its sheet, and the finish screen when it evolves.

- **B. Finish-screen hero:** the pet replaces the check badge after every session.
- **A. Rest-timer buddy:** a small pet sits in the rest banner and celebrates after a PB set.

Picked by Hari on 2026-11-09 from options A–F. Deferred: history milestones (C), empty states (D), roaming pet (E), share card (F).

## Decisions and why

- **No new art.** Existing sheet rows cover it: 1 happy, 2 sleepy, 3 celebrate. `petSprite()` already renders any row.
- **Finish hero mood:** celebrate (row 3) if the session has a PB, else happy (row 1). The reward should match the result.
- **Finish hero line:** `Bebi ate <volume> <unit>.` under the session title. It ties the stats to the pet.
- **No double pet when it evolves.** `renderPetEvolution()` keeps its title and sub text but drops its own sprite tile. The hero already shows the pet celebrating, and on an evolution it always uses row 3.
- **Rest pet is static by default.** It shows the sleepy frame (row 2) with no animation. Motion on the workout screen is the main clutter risk.
- **PB set triggers celebrate.** When a ticked set's weight beats the best completed weight for that exercise name in `state.history`, the banner pet plays the celebrate row until that rest ends. It's a live check only. The saved PB logic in `prsByEntry()` is unchanged.
- **Toggle to hide the rest pet.** It's a new top-level `petInRest: true` in `defaultState()`. `loadState()` spreads defaults under parsed data, so old saves pick it up with no migration. It's an additive field, so the shape of existing data is unchanged.
- **Reduced motion:** the existing `prefers-reduced-motion` rule on `.pet-sprite` already stops the animation. Nothing new is needed.

## Tasks

### 1. Finish-screen hero (B)

Files: `app.js` (`renderFinishSummary`, `renderPetEvolution`), `app.css` (`.summary-badge` area).

- In `renderFinishSummary`, replace `<div class="summary-badge">${icon('check')}</div>` with a pet tile. Use `petSprite(petForm(), row, 96, mood)`, with row and mood as decided above, wrapped in the pet colour (`--pet`) and stage scale like `renderPetCard`.
- Add a `<p class="muted">Bebi ate …</p>` line using `formatVolume(entryVolume(entry))` and `unitLabel()`. Use `PET_NAME`, not the literal.
- In `renderPetEvolution`, remove the `.pet-tile` block and keep the text card.
- Add CSS for the hero tile, sized and centred where the badge was. Remove `.summary-badge` rules if nothing else uses them (grep first).

Done-check: finish a session with no PB and see the happy pet. Finish one with a PB and see it celebrate. Finish one that crosses a stage (e.g. the 10th session) and see one pet, not two, plus the evolution text.

### 2. Rest-banner pet (A)

Files: `app.js` (`renderRestBanner`, `toggle-set-done` handler, `startRestTimer`/rest reset, `defaultState`, `renderSettingsTab` and its field handler), `app.css` (`.rest-banner`).

- Add `petInRest: true` to `defaultState()`.
- Add a helper `bestDoneWeight(name)`: the max completed-set weight for that exercise name (trimmed, lowercased) across `state.history`. Reuse `topWeight()`.
- In the `toggle-set-done` handler, when a set becomes done and its weight beats `bestDoneWeight(ex.name)`, set `restState.pb = true` after `startRestTimer()`. `startRestTimer()` and the rest reset leave `pb` false.
- In `renderRestBanner`, if `state.petInRest`, add a ~40px pet on the left of the banner. Use `petSprite(form, 3, 40, 'celebrate')` when `restState.pb`, else the static sleepy frame. Static means add a `still` class that sets `animation: none`.
- Settings: add a "Show Bebi during rest" checkbox next to the rest seconds field. Wire it like the other settings fields and save it.
- The banner text updates by id each second (`rest-remaining`), so the sprite isn't re-rendered per tick. Keep it that way.

Done-check: tick a normal set and see a still, sleepy pet in the banner. Tick a set heavier than any past set of that exercise and see the pet celebrate until the rest ends. Turn the toggle off and see no pet. Reload, and the toggle state persists.

### 3. Ship

- Bump `CACHE_NAME` in `sw.js` by +1.
- `node --check app.js health.js sw.js`.
- Serve with `python3 -m http.server`. Screenshot the finish screen (PB and no-PB) and the rest banner (still and celebrate) for Hari before merge.
- One PR for tasks 1–3.

## Don't touch

- `prsByEntry()`, pet stage and form logic, `PET_STAGES`, sprite files.
- Storage key `gymCompanionData_v1` and existing fields.
- The Train card and pet sheet.

## Open questions (defaults in place)

1. **First set of a new exercise.** With no history, any weight "beats" nothing. Default: no celebrate when there's no prior best. That matches `prsByEntry()`.
2. **Bodyweight or zero-weight sets.** Default: no celebrate if the weight is empty or 0.
3. **Sports finishes.** The sports sheet has no finish screen. Default: out of scope.
