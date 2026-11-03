# Target catalog

Generated from `targets/catalog.json` (built by `gen_assets.py`). Every target has a printable artwork PDF/PNG (`targets/<key>-letter.pdf`) and a separate scoring mask (`targets/<key>-mask.pdf`). See [masks.md](masks.md) for the legend.

| Key | Code | Name | Category | Paper | Distance | Features |
|---|---|---|---|---|---|---|
| `bullseye` | LD-001 | Bullseye | tactical | letter | 3-7 yd (pistol) |  |
| `silhouette` | LD-002 | Silhouette + No-Shoot | tactical | letter | 3-7 yd (scaled ~1/3) | no-shoot |
| `five-dot` | LD-003 | 5-Dot Sequence | tactical | letter | 3-5 yd |  |
| `clays` | LD-004 | Shotgun Clays | tactical | letter | 3-5 yd (shotgun cartridge) |  |
| `hostage` | LD-005 | Hostage | tactical | letter | 3-5 yd | hostage, no-shoot |
| `crowd` | LD-301 | Crowd Hunt (Letter) | tactical | letter | 3-5 yd | backstop |
| `crowd-tabloid` | LD-302 | Crowd Hunt (Tabloid) | tactical | tabloid | 3-5 yd | backstop |
| `carnival` | LD-401 | Carnival Shoot | fun | letter | 3-5 yd |  |
| `battle` | LD-402 | Sink-the-Ship (8x8) | fun | letter | 3-7 yd |  |
| `cards` | LD-403 | Card Shoot | fun | letter | 3-5 yd |  |
| `cards-tabloid` | LD-404 | Card Shoot (Tabloid) | fun | tabloid | 3-5 yd |  |
| `maritime` | LD-501 | Maritime Interdiction | tactical | letter | 5-10 yd | no-shoot |
| `maritime-tabloid` | LD-502 | Maritime Interdiction (Tabloid) | tactical | tabloid | 5-10 yd | no-shoot |
| `ct` | LD-503 | Counter-Terror | tactical | letter | 5-7 yd | head-only, no-shoot |
| `ct-tabloid` | LD-504 | Counter-Terror (Tabloid) | tactical | tabloid | 5-7 yd | head-only, no-shoot |
| `fof` | LD-505 | Friend or Foe | tactical | letter | 5-10 yd | hard cover |
| `fof-tabloid` | LD-506 | Friend or Foe (Tabloid) | tactical | tabloid | 5-10 yd | hard cover |
| `ankle` | LD-601 | Ankle Draw: Store | self-defense | letter | 3 yd, shooter kneeling (aim slightly upward) | backstop, hard cover |
| `ankle-tabloid` | LD-602 | Ankle Draw: Store (Tabloid) | self-defense | tabloid | 3 yd, shooter kneeling (aim slightly upward) | backstop, hard cover |
| `idpa-threat` | LD-101 | IDPA-style Threat | tactical | letter | 3 yd = ~13.5 yd sim (1/4.5 scale) |  |
| `idpa-hc-left` | LD-102 | IDPA-style Hard Cover: Left | tactical | letter | 3 yd = ~13.5 yd sim (1/4.5 scale) | hard cover |
| `idpa-hc-lower` | LD-103 | IDPA-style Hard Cover: Lower | tactical | letter | 3 yd = ~13.5 yd sim (1/4.5 scale) | hard cover |
| `idpa-hc-diagonal` | LD-104 | IDPA-style Hard Cover: Diagonal | tactical | letter | 3 yd = ~13.5 yd sim (1/4.5 scale) | hard cover |
| `idpa-nonthreat` | LD-105 | IDPA-style Non-Threat (open hands) | tactical | letter | 3 yd = ~13.5 yd sim (1/4.5 scale) | no-shoot |
| `idpa-practice` | LD-106 | IDPA-style Practice (dark -0) | tactical | letter | 3 yd = ~13.5 yd sim (1/4.5 scale) |  |
| `idpa-nt-pair` | LD-107 | IDPA-style Threat + Non-Threat | tactical | letter | 3 yd = ~15 yd sim (1/5 scale) | no-shoot |
| `idpa-multi` | LD-108 | IDPA-style Multiple Threats | tactical | letter | 3 yd = ~27 yd sim (1/9 scale) |  |
| `idpa-all-tabloid` | LD-110 | IDPA-style All Variations | tactical | tabloid | 3 yd = ~27 yd sim (1/9 scale) | hard cover, no-shoot |
| `idpa-all-letter` | LD-111 | IDPA-style All Variations | tactical | letter | 3 yd = ~42 yd sim (1/14 scale) | hard cover, no-shoot |
| `dh-hans` | LD-201 | Die Hard: Hans (HK P7) | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) | backstop |
| `dh-karl` | LD-202 | Die Hard: Karl (MP5A3, stairwell) | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) | backstop, hard cover |
| `dh-tony` | LD-203 | Die Hard: Tony (MP5A3, cabinet) | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) | backstop, hard cover |
| `dh-franco` | LD-204 | Die Hard: Franco (AUG, desk) | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) | backstop, hard cover |
| `dh-heinrich` | LD-205 | Die Hard: Heinrich (AUG, pillar) | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) | backstop, hard cover |
| `dh-eddie` | LD-206 | Die Hard: Eddie (fake guard) | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) |  |
| `dh-theo` | LD-207 | Die Hard: Theo (vault tech) | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) |  |
| `dh-uli` | LD-212 | Die Hard: Uli (AUG, lobby) | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) | backstop |
| `dh-powell` | LD-213 | Die Hard: Sgt. Powell (FRIENDLY) | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) | backstop, no-shoot |
| `dh-billclay` | LD-208 | Die Hard: "Bill Clay" impostor | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) |  |
| `dh-finale` | LD-209 | Die Hard: Roof Finale | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) | hostage, no-shoot |
| `dh-party` | LD-210 | Die Hard: Christmas Party | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) | no-shoot |
| `dh-lobby` | LD-214 | Die Hard: Lobby (Powell arrives) | themed | letter | 3 yd = ~30 yd sim (figure ~1/10 scale) | no-shoot |
| `dh-nakatomi` | LD-211 | Die Hard: Nakatomi Plaza line-up | themed | tabloid | 3 yd = ~32 yd sim (1/11 scale) | no-shoot |
