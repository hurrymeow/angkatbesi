# CLAUDE.md

Beban Book: vanilla JS gym logbook PWA. No build, no tests, no CI. See README.md for the overview.

## Rules

- Bump `CACHE_NAME` in `sw.js` (`gym-companion-vN`, +1) whenever you change `index.html`, `app.js`, `health.js`, `app.css`, `manifest.json`, `icons/*` or `ALL_ASSETS`. Skipping it strands installed users on the old version.
- Add new cached files to `ALL_ASSETS` in `sw.js`. Add shell files to `CORE_FILES` too if they must load network-first.
- Keep it dependency-free and buildless. Scripts load in order: `health.js`, then `app.js`.
- Storage key `gymCompanionData_v1` is user data. Don't rename it or change its shape without a migration in `app.js`.
- The Gemini key (`ironlog.geminiKey`) must stay out of backups and "Erase all data".
- Style follows Mono Dark. Colour tokens live in `app.css`. Icon and `theme-color` (`#0a0a0a`) must match.

## Ship

- Docs-only or `.claude/`-only: commit to main. If the push is refused, open a PR and squash-merge it.
- Anything else: branch, PR, squash-merge, confirm Pages deploy.
- Past PRs were squash-merged locally, so GitHub lists them as closed, not merged. Check `git log origin/main` for the PR number.
- Old `ccr-*` branches on origin are leftovers, not pending work.

## Check a change

- Serve with `python3 -m http.server`, open in a browser, exercise the tab you changed.
- `node --check app.js health.js sw.js` for syntax.
