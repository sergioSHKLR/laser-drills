# Development

## Run locally
```
python3 -m http.server 8765   # then open http://localhost:8765/
```
The camera needs a secure context, so use localhost or HTTPS.

## Generators
| Script | Notes |
|---|---|
| `gen_assets.py` | Renders every target and mask PDF/PNG plus `targets/catalog.json` from `targets.json` and `art/` |
| `tools_build_specs.py`, `tools_games.py`, `tools_clays.py`, `tools_crowd.py`, `tools_diehard.py`, `tools_ankle.py` | Add target specs and drills for each set |
| `tools_diehard_safe.py` | Laser-safe color pass: no red in scoring zones, red-dominance under about 40, readable grayscale steps |
| `tools_courses.py` | Writes `courses.json` |
| `tools_icons.py` | Builds the Lucide sprite from an extracted `lucide-static` npm tarball (`npm pack lucide-static && tar xzf …` into `/tmp/package`). Writes `vendor/lucide/sprite.svg` and `LICENSE`, and inlines the sprite between `<!--LUCIDE-->` markers in `index.html`. To add an icon, add its name to the list in the script, re-run it, and use `I('name')` in JS or `<svg class=ic><use href="#i-name"/></svg>` in HTML |
| `tools_pwa_assets.py` | Favicons, apple-touch and maskable icons, `og-image.png` |

## Tests
```
node test/run_test.js
node test/game_test.js
python3 test/editor_test.py
```
Manual check before a release: headless Chromium at 390 and 1280 widths, every tab, no console errors, and every `<use href>` resolves. The manifest screenshots in `screenshots/` come from this check, with seeded demo data.

## Release
1. Bump `CACHE` in `sw.js` (`ld-vNN`). If you add a new file the app needs offline, add it to the precache list.
2. Run the tests.
3. Commit and push to `main`. GitHub Pages deploys in about 1 minute.
4. Check the live `sw.js`, `manifest.webmanifest`, and a hard reload of the app.
