# Fold the stat tiles into the pet card

Status: approved by Hari 2026-10-31 (option "B-short"). One small PR.

## Goal

Free vertical space on the Train tab. The three stat tiles (kg this week, sessions this month, PRs this month) become one line inside the pet card. "Next up" moves up about 76px on a 390px-wide phone.

## Decisions and why

- **B-short: one inline line under the pet progress bar.** Text: `3,720 kg · 9 sessions · 18 PRs`. Mockup: `/mnt/project-files/pet-mockups/shots/stats-merge-b-short.png`.
- **Rejected A (footer row under a divider).** It saved only 15px. Comparison: `/mnt/project-files/pet-mockups/shots/stats-merge-compare.png`.
- **Rejected B with period labels ("kg wk", "sess mo").** Too cramped to read.
- **Periods are unchanged.** Weight is this week. Sessions and PRs are this month. The card drops the period words, so the pet sheet spells them out.
- **Hidden with no history.** Same rule as today's tiles.
- **Accessibility fix.** The card's `aria-label="Open Bebi"` replaces its content for screen readers, so the numbers would be silent. Use an accessible name that includes them.
- **No storage change.** Everything is derived from `state.history`.

## Tasks

### 1. Extract the stat numbers (`app.js`)

- Turn the loop in `renderStatTiles()` into `statNumbers()` that returns `{ volume, sessions, prCount }`.
- Delete `renderStatTiles()` and its call in `renderTrainTab()`.
- Don't touch the `stat-grid` on the finish summary.
- Done when: `grep -n renderStatTiles app.js` returns nothing.

### 2. Inline line in the pet card (`app.js`, `app.css`)

- In `renderPetCard()`, after `<p class="pet-next">`, add when `state.history.length`:
  `<p class="pet-stats"><b>{formatVolume(volume)}</b> {unitLabel()} · <b>{sessions}</b> session(s) · <b class="up if prCount">{prCount}</b> PR(s)</p>`.
- Pluralise "session" and "PR" for 1.
- CSS (pet section of `app.css`):
  - `.pet-stats { margin: 6px 0 0; font-size: var(--text-xs); color: var(--text-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }`
  - `.pet-stats b { font-family: var(--font-mono); color: var(--text); font-weight: 600; }`
  - `.pet-stats b.up { color: var(--success); }`
- Use Mono Dark tokens only. No new colours.
- Accessibility: replace the button's `aria-label` with one that includes the line. Example: "Open Bebi. 3,720 kg this week, 9 sessions and 18 PRs this month."
- Done when: the card matches the mockup at 390px. The line doesn't wrap at 320px, and it ellipsises if it must.

### 3. Spell out periods in the pet sheet (`app.js`)

- In `renderPetSheet()`, after the Mood block and before Form, add `<p class="eyebrow mt-3">Training</p>`.
- Under it, add `<div class="stat-grid flat">` with three `.stat` items. Labels: "{unit} this week", "sessions this month", "PRs this month".
- Reuse `statNumbers()`.
- Done when: the sheet shows the three labelled numbers, and nothing shows with no history.

### 4. Ship

- Bump `CACHE_NAME` in `sw.js` from `gym-companion-v26` to v27.
- Run `node --check app.js health.js sw.js` and `node tools/smoke.js`.
- Serve locally. Check the Train tab with history and with no history, then open the pet sheet.
- Check at 320px and 390px.
- Branch, PR, squash-merge, confirm Pages deploy.

## Don't touch

- The week card, Next up card, finish summary stats, pet art and animation, `gymCompanionData_v1`.

## Open questions

- None.
