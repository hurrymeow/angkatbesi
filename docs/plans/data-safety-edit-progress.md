# Data safety, edit past workouts, better exercise progress

Status: approved by Hari 2026-11-13 (items 1, 2 and 3 of the improvements list). Three PRs, run in order.

## Goal

Protect and correct the logged history that the pet, PRs, streak and progression are built on. Then make the By Exercise view show real progress.

## Decisions and why

- **Safety and correctness before more features.** The pet's value grows with history, so losing or corrupting history is the costliest failure.
- **Three PRs, run one after another.** All three touch `app.js` and bump `CACHE_NAME` in `sw.js`, so parallel branches would conflict.
- **No storage migration.** New fields are optional top-level or `ui` keys. `loadState()` spreads over `defaultState()`, so old data picks up the defaults. Rename/merge rewrites `name` strings only, so the shape stays the same.
- **Everything derived stays derived.** PRs, best, progression prefill, pet stage and form all read `state.history`. Editing an entry fixes them with no extra bookkeeping.
- **Google Health: delete then resend on edit.** The sent session's notes hold the sets, and kcal depends on completed sets. Reuse `Health.queueDelete(gh.name)` plus `gh = { state: 'pending' }`, as Delete entry does today (`app.js` near the `delete-history-entry` handler).
- **Backup nudge, not auto-backup.** The app has no server, and `persist()` is weakly honoured on iOS. A nudge to export is the only thing that survives a lost phone.
- **e1RM uses Epley, sets of 1–10 reps only.** Epley is the common default. Above 10 reps it overestimates badly, so those sets are skipped.

## Tasks

### 1. Data safety (PR 1, Sonnet)

Files: `app.js`, `sw.js`.

- On startup, if `navigator.storage?.persist` exists and `persisted()` is false, call `persist()`. Fire and forget. Never block render.
- Add `lastExportAt: null` to `defaultState()`. `exportData()` sets it to now and calls `saveState()` before downloading.
- Add `backupSnoozeUntil: null` to `defaultState().ui`.
- "Unbacked" entries are `state.history` plus `state.activities` with `date` after `lastExportAt` (all of them when null).
- Show a backup card on Train when there is at least 1 unbacked entry and either 10 or more are unbacked or the oldest is 14 or more days old. Hide it during an active workout, on the finish summary, and while `backupSnoozeUntil` is in the future.
- Card copy: "Back up your log" and "N entries since your last backup." Buttons: **Back up** (calls `exportData()`) and **Later** (snoozes 7 days).
- Settings Backup row: add "Last backup: <relative day>" or "Never", and "Storage: kept" or "Storage: may be cleared by the browser" from `navigator.storage.persisted()`.
- Bump `CACHE_NAME`.

Done-check:
- Fresh state with 10 logged entries shows the card. Back up downloads the file and hides the card. Later hides it, and it stays hidden after reload.
- An export with an older `lastExportAt` re-imports without errors.
- "Erase all data" resets `lastExportAt` to null.
- `node --check app.js health.js sw.js` passes and CI is green.

### 2. Edit a past workout (PR 2, Sonnet)

Files: `app.js`, `app.css` if the sheet needs styles, `sw.js`.

- Add an **Edit** button beside Delete entry in an expanded History card. It applies to lifting entries only, because sports already have an edit sheet.
- It opens a sheet (`kind: 'edit-entry'`) on a deep copy of the entry. Each exercise lists its sets as reps, weight and done. Each exercise has Add set and remove set buttons.
- The session name and date stay read-only in this PR.
- **Save** writes the copy back, converting values as `handleFinishWorkout()` does (`''` becomes `null`, numbers become `Number`). **Cancel** discards it. Dismissing the sheet counts as Cancel.
- Health after save:
  - `gh.state === 'done'` with a `name`, and connected: queue a delete of the old name, set `gh = { state: 'pending' }`, call `sendToHealth({ interactive: true })`.
  - `gh` pending or failed: leave it. The next sync sends the edited data.
  - `gh.state === 'done'` with `name: null`: the app can't remove the old copy. Show a note in the sheet: "The Google Health copy won't update." Leave `gh` alone.
- Bump `CACHE_NAME`.

Done-check:
- Log a workout with a typo (100 instead of 10). Edit it to 10. The PR pill goes away, By Exercise best drops, and the next workout prefills from 10.
- Cancel leaves the entry unchanged.
- With Health connected and the entry sent, saving queues one delete and one resend.
- Syntax check passes and CI is green.

### 3. Better exercise progress (PR 3, Sonnet)

Files: `app.js`, `app.css`, `sw.js`.

- **Fix matching.** The By Exercise rows compare `e.name === selected` with no trim or case folding. PRs and best use trim plus lowercase. Use one shared `exerciseKey(name)` helper everywhere.
- **Metric toggle.** Add Top weight, e1RM and Volume as a segmented control above the sparkline. Store the choice in `state.ui.historyMetric` (default `'top'`).
  - e1RM per session: the best of `weight × (1 + reps / 30)` over completed sets with 1–10 reps and weight above 0. Round to 1 decimal.
  - Volume per session: the sum of reps × weight over completed sets of that exercise.
  - The stat row follows the metric: best and latest of the chosen metric, plus the sessions count.
- **Rename or merge.** Add a **Rename** button on the selected exercise in By Exercise. It opens a sheet with a name input.
  - If the new name matches another known exercise by key, the button reads "Merge into <name>".
  - Confirm with a count: "Updates N logged sessions and M routine exercises."
  - Rewrite `name` in `state.history[].exercises[]`, `state.routine.sessions[].exercises[]`, and `state.activeWorkoutDraft` if present. Then set `historyExerciseFilter` to the new name.
- Bump `CACHE_NAME`.

Done-check:
- Rename "Bench" to "Bench Press" when both exist. One exercise remains, with combined rows and correct PRs.
- The e1RM toggle on a 5×5 at 100 shows 116.7. A 15-rep set is ignored.
- The volume toggle matches a hand sum for one session.
- Syntax check passes and CI is green.

## Not in scope

- Editing session name or date on past workouts.
- Auto-backup to Drive or other cloud storage.
- Splitting `app.js` into modules.
- A stronger smoke test (item 4). Each PR's done-check is manual in the browser.

## Open questions

- None blocking. If Hari wants the backup to open the share sheet (save to Files or Drive) instead of a download, that is a follow-up to PR 1.
