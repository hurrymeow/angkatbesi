# Beban Book

Gym logbook PWA. Log sets, build routines, review history. All data stays in the browser.

## Features

- Train, Routine and History tabs.
- Rest timer that counts to a fixed end time and notifies on finish.
- Optional AI routine builder. Uses your own Gemini key, called straight from the browser.
- Optional send of finished workouts to Google Health (`health.js`).
- An evolving pet on the Train tab that grows with your logged workouts.
- Backup export and import as JSON.
- Installable, works offline, shows an update banner when a new version is ready.

## Stack

- Vanilla JS, HTML and CSS. No build step, no dependencies.
- `app.js` holds the UI and state. `health.js` holds the Google Health sync.
- `sw.js` is the service worker. `manifest.json` and `icons/` make it installable.
- Data lives in `localStorage` under `gymCompanionData_v1`. The Gemini key has its own entry and is excluded from backups and "Erase all data".

## Run locally

```
python3 -m http.server 8000
```

Open `http://localhost:8000`. Service workers need localhost or HTTPS.

## Deploy

- Hosted on GitHub Pages, served from `main`. Merging to `main` is the deploy.
- Pages sends `max-age=600`. The service worker fetches core files network-first to get around that.
- The Google OAuth client only works from origins registered in its GCP project.

## Service worker cache bump

`sw.js` has a manual `CACHE_NAME` (`gym-companion-vN`). Bump it in any change that touches a cached asset:

- `index.html`, `app.js`, `health.js`, `app.css`, `manifest.json`
- anything in `icons/`
- the `ALL_ASSETS` list itself

Without the bump, installed copies keep the old cache and never show the update banner.

## Icons

`python3 tools/make-icons.py` redraws the icons from the colour tokens in `app.css`. Needs Pillow.
