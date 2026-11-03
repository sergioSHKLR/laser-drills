# Laser Drills (test version)
Static PWA. Serve over HTTPS (camera requirement) or http://localhost.
- Print targets/bullseye-letter.pdf at 100% on US Letter.
- Run tests: python3 test/make_frames.py && node test/run_test.js
- Quick host options: GitHub Pages / Netlify Drop (drag folder), or on ChromeOS Linux: `python3 -m http.server 8000` then open http://localhost:8000 (localhost counts as secure).
- Phone via USB: `adb reverse tcp:8000 tcp:8000` then open http://localhost:8000 in Chrome on the phone.
- Shotgun mode: zones grow by `shotgunSpread` inches (default 1.5). Idea for next step: score a pattern circle and allow multiple-pellet "hit" credit.
