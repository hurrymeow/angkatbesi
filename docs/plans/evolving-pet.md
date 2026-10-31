# Evolving pet on the Train tab

Status: approved by Hari 2026-10-31. Build in one PR, in the task order below.

## Goal

Make the home (Train) tab feel like visible progress. A pixel-art pet sits above the week card. It grows with every logged workout, takes a form based on what you train, and reacts to how recently you trained. Tapping it opens a sheet where it walks around and you can play with it.

## Decisions and why

- **Pet, not tree, house or heat map.** Hari picked it for its emotional pull.
- **Compact row card above the week card (layout A).** It keeps "Next up" and Start near the top. Mockup: `/mnt/project-files/pet-mockups/pet-in-app.png` (middle phone).
- **Tappable.** The card opens a detail sheet with a playground, stats and the evolution path.
- **Colour is allowed for the pet art only.** The rest of the app stays Mono Dark. No new colour tokens outside the pet styles.
- **Art is Gemini pixel art, not code-drawn shapes.** The SVG preview was only for the concept.
- **Never negative.** No sickness, sadness or devolving. Rest makes it sleepy.
- **Form locks at 25 sessions.** It is decided by the first 25 logged sessions, so it feels earned and needs no stored field.
- **No storage change.** Everything is derived from `state.history`. Don't add keys to `gymCompanionData_v1`.
- **Name is the constant `PET_NAME = 'Bebi'`.** It's a placeholder. Renaming would need storage, so it's out of scope.

## Source art

All in `/mnt/project-files/pet-mockups/sprites/` (shared project folder, readable from any thread):

| File | Layout | Use |
|---|---|---|
| `baby.jpg`, `brawler.jpg`, `climber.jpg`, `stomper.jpg` | 1024x1024, 4x4 grid of 256px cells | Rows: 1 idle, 2 happy, 3 sleepy, 4 celebrate. 4 frames per row. |
| `baby-walk.jpg`, `brawler-walk.jpg`, `climber-walk.jpg`, `stomper-walk.jpg` | 2064x512, 1 row of 4 cells (516x512 each) | Walk cycle, three-quarter view facing right. Mirror for left. |
| `baby-alt.jpg`, `baby-walk.png` | | Rejected. Don't use. |

Every background is near-black (#0A0A0A) JPG, not transparent. The characters have a dark outline, so a global "make dark pixels transparent" key would also eat the outline.

## Mechanics

**Stage** comes from `n = state.history.length`.

| n | Stage | Art | Scale in card |
|---|---|---|---|
| 0 | Sleeping | baby, sleepy row | 0.7 |
| 1–9 | Hatchling | baby | 0.75 |
| 10–24 | Cub | baby | 0.9 |
| 25–49 | Junior | form sheet | 0.9 |
| 50–99 | Adult | form sheet | 1.0 |
| 100+ | Legend | form sheet plus a soft glow (CSS `drop-shadow` in the form colour) | 1.0 |

Next thresholds for the progress bar: 1, 10, 25, 50, 100. At 100+ show "Fully evolved".

**Form** (only from n ≥ 25):

- Take the oldest 25 entries (`state.history.slice(-25)`, because history is newest-first).
- Classify each completed set by exercise name (lowercase, keyword `includes`). Check in this order and stop at the first match:
  - **legs:** squat, lunge, leg press, leg curl, leg extension, calf, rdl, romanian, hip thrust, glute, split squat, step-up
  - **pull:** row, pull-up, pullup, chin, pulldown, curl, deadlift, face pull, shrug, rear delt
  - **push:** bench, press, dip, push-up, pushup, fly, flye, triceps, tricep, skullcrusher, lateral raise, raise
- Legs goes first, so "leg press", "leg curl" and "Romanian deadlift" count as legs.
- Unmatched sets are ignored.
- The form with the most sets wins. Tie-break: legs, then push, then pull. If nothing matched at all, use push.
- Forms: push = **Brawler** (`#FF7A59`), pull = **Climber** (`#3EC7C2`), legs = **Stomper** (`#A58BFF`). The baby is `#FFD166`.

**Mood** comes from `daysAgo(state.history[0].date)` and today's PRs (`prsByEntry()` for entries dated today).

| Condition | Mood | Sprite row | Line on card |
|---|---|---|---|
| A PR today | celebrate | 4 | "New PB today. {name} is losing it." |
| Trained today | happy | 2 | "Fed today. Bouncing around." |
| 1–2 days | content | 1 | "Trained {n} day(s) ago. Happy and resting." |
| 3–6 days | sleepy | 3 | "{n} days since your last session. Getting sleepy." |
| 7+ days | hibernating | 3, at 50% opacity, slower | "Hibernating. Log a workout to wake it up." |
| No history | sleepy | 3 | "Log your first workout to wake {name}." |

## Tasks

Do them in order. Each ends with its own done-check.

### 1. Process the sprites into the repo

- **Add** `tools/make-pet-sprites.py` (Pillow, like `tools/make-icons.py`). Args: a source dir and an output dir (default `pet/`).
- **Background removal:** for each cell, flood-fill from the cell's border pixels and make transparent every connected pixel within about 30 of #0A0A0A (RGB distance). Interior outline pixels aren't connected to the border, so they survive. Then clear the remaining JPG speckle: pixels under 24 luminance that touch transparency.
- **Mood sheets:** resize each 256px cell to 128px (LANCZOS) and reassemble. Output `pet/{baby,brawler,climber,stomper}.png` at 512x512.
- **Walk strips:** centre-crop each 516x512 cell to 512x512, resize to 128px, and reassemble. Output `pet/{form}-walk.png` at 512x128.
- Save optimised PNGs (`optimize=True`).
- **Done when:**
  - all 8 PNGs exist and each is under 120 KB;
  - a 4x zoom of one cell on a white background shows no black halo and an intact dark outline;
  - re-running the script gives identical output.
- **Don't touch:** `icons/`, `make-icons.py`.

### 2. Pet model (pure functions in `app.js`)

Add a `// ---------- Pet ----------` section after the "Progress & stats" helpers (around `weekStreak()`):

- `PET_NAME`, `PET_FORMS` (key, name, colour, sheet, walk), `PET_STAGES` (name, at, scale).
- `petStage(n)` returns the stage object, its index, and the next stage (or null).
- `petForm()` returns a form key, or `'baby'` when history has fewer than 25 entries. Rules as above.
- `petMood()` returns `{ key, row, line, daysAgo }`. Reuse `daysAgo`, `prsByEntry`, `startOfDay`.
- `petSetCounts(entries)` returns `{ push, pull, legs }` for the sheet. Use the oldest 25 when n ≥ 25, otherwise all entries, so the sheet can say "leaning legs".
- **Done when:**
  - `node --check app.js` passes;
  - in the browser console with seeded data (see "Seeding test data"), the 0, 5, 18, 30-legs, 60-push and 120-pull cases return the expected stage, form and mood.
- **Don't touch:** the storage shape, `loadState`, `defaultState`.

### 3. Compact card on the Train tab

- `renderPetCard()` returns a `.card.pet-card` row, built as a `<button>` so it's tappable and keyboard-focusable. `data-action="open-pet"`, `aria-label="Open {name}"`.
  - Left: an 84x84 tile with a radial-gradient background tinted by the form colour (about 20% mix over `--surface-2`) and the animated sprite.
  - Right: the name with the stage label right-aligned (for example "Cub", or "Stomper · Junior"), the mood line, a 6px progress bar in the form colour, and "N sessions to {next}".
- Insert `${renderPetCard()}` directly above `${renderWeekCard()}` in `renderTrainTab()`, in the branch that has a next session. Also show it on the "no sessions yet" and "Pick a program" screens, so a new user sees the sleeping baby.
- **Sprite rendering:** a `<div class="pet-sprite">` with CSS variables `--sheet` (url), `--row` (0–3), `--size` (px) and `--scale`.
  - `background-image: var(--sheet); background-size: calc(var(--size) * 4) calc(var(--size) * 4);`
  - Animate `background-position` from `0 calc(var(--size) * var(--row) * -1)` to `calc(var(--size) * -4) calc(var(--size) * var(--row) * -1)` with `steps(4)`. Use about 0.8s for idle and happy, 1.6s for sleepy and 2.4s for hibernating.
  - `image-rendering: pixelated` only if it looks better at 84px. Check both.
  - Add a gentle bob (`translateY`) on top for happy.
- Add `case 'open-pet': openSheet({ kind: 'pet' }); break;` to the click switch.
- Styles go in `app.css` under a `/* Pet */` block. Pet colours are literals there; that's the agreed exception.
- **Done when:**
  - screenshots at 390px width with 0, 5, 18, 30-legs and 120 sessions look like the mockup's middle phone;
  - the card doesn't push "Next up" further down than the mockup;
  - Tab focuses the card and Enter opens the sheet.
- **Don't touch:** `renderWeekCard`, `renderStatTiles`, `renderNextUpCard`, colour tokens in `:root`.

### 4. Pet sheet (detail and play)

- Add `case 'pet': body = renderPetSheet(); break;` to `renderSheet()`.
- **Sheet contents:**
  1. **Playground:** full width, 180px tall, a faint floor line, sprite at 112px. The pet wanders: pick a random x, walk there using the walk strip (mirror with `scaleX(-1)` when going left), pause 1.5–4s on the mood row, repeat. Climber walks 10px above the floor with a small ellipse shadow. Stomper adds a small squash on each step.
  2. **Tap the pet:** play the celebrate row once (about 1s), float a small heart, call `navigator.vibrate?.(20)`, then resume. It's local fun only, with no state change.
  3. **Header:** name, stage label, progress bar, "N of M sessions to {next}".
  4. **Mood:** the mood line plus "Last trained {relativeDay}".
  5. **Form:** before 25, "Leaning {top} · push {a} · pull {b} · legs {c} sets" with "Form is set at 25 sessions". After 25, "{Form}, set by your first 25 sessions".
  6. **Evolution path:** five thumbnails (baby, Brawler, Climber, Stomper, Legend glow) with thresholds. Unreached forms show as a silhouette (`filter: brightness(0) opacity(.35)`) with "?".
- **Animation loop:** one `requestAnimationFrame` loop that looks up `.pet-playground` on each tick, because `render()` rebuilds `#app.innerHTML` and replaces the element. Keep the pet's x and direction in a module-level object. Stop the loop when the element is gone, and start it from `openSheet` when `kind === 'pet'`.
- **Reduced motion:** with `prefers-reduced-motion: reduce`, there's no wandering and no frame stepping. Show a static first frame and keep the tap reaction as a single frame swap.
- **Done when:**
  - the sheet opens and closes, and Android back closes it (via the existing `history.pushState`);
  - the pet walks, turns and taps for 30 seconds with no console errors;
  - closing the sheet stops the loop (no rAF callbacks running afterwards);
  - it works with reduced motion emulated.

### 5. Evolution moment on the finish screen

- In `renderFinishSummary()`, compare `petStage(n - 1)` with `petStage(n)` and the form at 24 versus 25 sessions.
- If the stage changed, show a card above the stats: the new sprite on the celebrate row at 96px, "{name} evolved into {Form}!" (or "{name} grew into a {Stage}"), and one line on what's next.
- **Done when:** finishing the 1st, 10th, 25th, 50th and 100th session (seed n−1, then finish one) shows the card, and other sessions don't.
- **Don't touch:** the existing summary stats, PR list and Health sending.

### 6. Service worker and docs

- `sw.js`: add the 8 `./pet/*.png` files to `ALL_ASSETS` (not `CORE_FILES`). Bump `CACHE_NAME` from `gym-companion-v25` to `gym-companion-v26` (or +1 from whatever main has).
- `README.md`: add one feature bullet: "An evolving pet on the Train tab that grows with your logged workouts."
- **Done when:** CI's cache-bump check passes, and the installed app shows the update banner and then the pet offline.
- **Don't touch:** `CORE_FILES`, the fetch strategy, `manifest.json`, `icons/`.

## Seeding test data

Paste this into a Playwright `addInitScript`, or into the console then reload. Change `N` and the exercise list per case.

```js
const N = 30, ex = ['Squat', 'Leg Press', 'Calf Raises']; // legs case
const day = 864e5, now = Date.now();
const history = Array.from({ length: N }, (_, i) => ({
  id: 'h' + i, date: new Date(now - i * 2 * day).toISOString(), sessionId: 's', sessionName: 'Legs',
  exercises: ex.map((name, j) => ({ exerciseId: 'e' + j, name,
    sets: [1, 2, 3].map(() => ({ weight: 100 - i, reps: 8, completed: true })) }))
}));
localStorage.setItem('gymCompanionData_v1', JSON.stringify({ version: 1, unit: 'kg', restSeconds: 90, bodyweight: '',
  routine: { name: 'R', sessions: [{ id: 's', name: 'Legs', exercises: ex.map((name, j) => ({ id: 'e' + j, name, sets: 3, reps: '8' })) }] },
  history, activeWorkoutDraft: null,
  ui: { activeTab: 'train', expandedSessionIds: [], expandedHistoryIds: [], historyViewMode: 'sessions', historyExerciseFilter: '' } }));
```

Weights descend with age, so the newest entry is a PR. That gives the celebrate mood. Use a flat weight to test the other moods.

## Checks before the PR

- `node --check app.js health.js sw.js`
- `python3 -m http.server 8080` and `node tools/smoke.js http://localhost:8080/`
- One screenshot each, at 390px: the Train tab at 0, 18 and 30-legs sessions; the pet sheet; an evolution summary. Attach them to the PR and the thread.

## Ship

- Branch from the latest `origin/main`. Open one PR titled "Add evolving pet to Train tab". Wait for CI, squash-merge, then confirm the Pages deploy (per CLAUDE.md).
- Show Hari the screenshots in the thread when the PR is up.

## Open questions (defaults are in place, so they don't block the build)

1. **Name.** "Bebi" is a placeholder. Renaming in-app would need a stored field and a migration.
2. **Egg stage.** There's no egg art. 0 sessions shows the sleeping baby. Generate an egg later if wanted.
3. **Brawler roll.** Dropped. The Brawler walks like the others.
