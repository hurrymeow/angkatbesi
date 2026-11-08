# Log sports sessions with estimated calories

Status: approved by Hari 2026-11-08 (option A, generic sports, counts for "last trained"). One PR.

## Goal

Log pickleball, padel and other sports in Beban Book, so it is the only tracker. Each entry takes sport, minutes and intensity. The app estimates active kcal the same way it does for lifting, and sends the session to Google Health.

## Decisions and why

- **Option A: a separate `state.activities` array.** Every `state.history` loop (37 references) assumes exercises and sets. A separate list means volume, PRs, pet form and By Exercise need no guards. Rejected B (`kind` flag inside `history`): one missed guard breaks stats. Rejected C (read from Google Health): needs a new read scope and a watch on court.
- **Generic sport picker, pickleball first.** Hari also plays padel.
- **Pet: counts for "last trained" only.** It updates the pet mood (sleepy/idle), the "Last trained" lines and the week dots and week streak. It does not count toward session count, evolution, push/pull/legs form, volume or PRs. Hari confirmed week dots and streak count (2026-11-08).
- **Active kcal = (MET − 1) × kg × hours.** Same formula and bodyweight as `Health.estimate`. Resting burn stays out because Google counts it separately. No bodyweight means no kcal, same as today.
- **Two intensity tiers per sport: Casual and Match.** Enough for a rough number. A fixed MET can miss by 30% or more, and the lifting estimate is already that rough.
- **No storage migration needed.** `clearAllData()` resets to `defaultState()`, so it clears activities too. `loadState()` and import spread over `defaultState()`, so old data gets `activities: []`. Backup export already dumps the whole state.

### MET table

The 2024 Adult Compendium has no pickleball or padel row. Both use tennis doubles as the analog.

| Sport | Casual | Match | Basis |
|---|---|---|---|
| Pickleball | 4.5 | 6.0 | Compendium tennis doubles 15685 (4.5) and 15680 (6.0). ACE study about 350 kcal/h in adults aged 40–85, roughly 4.5–5 METs. Navalta 2024 singles VO2 21–27 mL/kg/min, about 6–7.7 METs. |
| Padel | 4.5 | 6.0 | Always doubles. Tennis doubles analog. Mellado-Arbelo 2022 review: moderate physiological load. |
| Tennis | 6.8 | 8.0 | Compendium 15675, 15676. |
| Badminton | 5.5 | 7.0 | Compendium 15030, 15020. |
| Other (custom name) | 4.5 | 6.0 | Generic moderate / vigorous. |

Worked example: 70 kg, 90 min casual pickleball → 3.5 × 70 × 1.5 = **368 kcal**.

Sources: [Compendium sports](https://pacompendium.com/sports/) · [ACE pickleball](https://www.acefitness.org/continuing-education/certified/august-2018/7053/ace-sponsored-research-can-pickleball-help-middle-aged-and-older-adults-get-fit/) · [Navalta et al. 2024](https://mdpi.com/2075-4663/12/9/234) · [Mellado-Arbelo & Baiget 2022](https://ojs.srce.hr/kinesiology/article/view/9871)

### Entry shape

```js
{ id, sport: 'pickleball' | 'padel' | 'tennis' | 'badminton' | 'other',
  name,        // display name; custom text for 'other'
  minutes,     // number > 0
  intensity: 'casual' | 'match',
  startedAt,   // ISO
  date,        // ISO end time = startedAt + minutes. Same field name as history, so sorting and relativeDay() work
  gh }         // same Google Health sync field as history entries
```

## Tasks

### 1. Data and estimate (`app.js`, `health.js`)

- Add `activities: []` to `defaultState()`. Keep newest first, like `history`.
- In `health.js`, add a `SPORTS` table (key, label, casual MET, match MET) and `estimateActivity(entry, weight, unit)` returning `{ kcal, met, minutes }`. Reuse `bodyweightKg`. Export both.
- `entryEstimate(entry)` in `app.js` routes to `estimateActivity` when `entry.sport` is set.
- Done when: in the console, `Health.estimateActivity({ sport: 'pickleball', intensity: 'casual', minutes: 90 }, 70, 'kg').kcal === 368`.

### 2. Log sheet (`app.js`, `app.css`)

- Train tab: a "Log a sport" button below the session list. It opens a sheet like the existing sheets.
- Sheet fields: sport chips (Pickleball, Padel, Tennis, Badminton, Other with a name input), minutes (number, default 60), Casual/Match toggle, and date/start time (default now minus minutes).
- Live line: `~368 kcal active`, or "Add bodyweight in Settings to estimate calories".
- Remember the last sport, intensity and minutes in `state.ui` as defaults.
- Save prepends to `state.activities`, marks `gh: { state: 'pending' }` when Health is connected, then calls `sendToHealth()`.
- Done when: logging a 90 min casual pickleball session at 70 kg shows 368 kcal and survives a reload.

### 3. History (`app.js`, `app.css`)

- By Session view merges `history` and `activities` sorted by `date`. A sport card shows icon or label, sport name, minutes, intensity and kcal. It expands to show edit and delete.
- Delete removes the entry and, if `gh.name` exists, queues a Google Health delete the same way workouts do.
- By Exercise view ignores activities.
- The empty state counts both lists.
- Done when: a sport entry shows in date order between workouts, edits and deletes work, and By Exercise is unchanged.

### 4. "Last trained" signals (`app.js`)

- Add `lastTrainedDate()`, the newest `date` across both lists.
- Use it in `petMood()` (the `last` check only), the two "Last trained" lines (`renderPetCard`, `renderWeekCard`), the `renderWeekCard()` dots and `weekStreak()`.
- Do not touch `statNumbers()`, session counts, `petFormOf()`, evolution or PRs.
- Done when: with only a sport logged today, the pet is not sleepy, today's dot is on, and the session count is unchanged.

### 5. Google Health (`health.js`, `app.js`)

- `toDataPoint` branches on `entry.sport`. It sets `exerciseType` from the sport, `displayName` to the name, the interval from `startedAt`/`date`, `caloriesKcal`, and notes like "Pickleball · casual · 90 min".
- `sendToHealth()`, `unsent()` and `waitingCount()` callers (`app.js` lines ~2356, 2357, 2688, 2895) and "Send past workouts" pass `[...state.history, ...state.activities]`. Entries are mutated in place, so `gh` writes back to the right list.
- Done when: a logged sport appears in Google Health with the right type, time and kcal, and deleting it removes it there.

### 6. Ship (`sw.js`)

- Bump `CACHE_NAME` by 1.
- Run `node --check app.js health.js sw.js`. Exercise the Train and History tabs on `python3 -m http.server` at 390px width. Take one screenshot of the sheet and one of History for Hari before merging.

## Open questions

1. **Google Health exercise types.** Check the v4 `exerciseType` enum for pickleball, padel, tennis and badminton values. Use the closest racquet type, or `OTHER`, where one is missing. Report which mapping was used.
