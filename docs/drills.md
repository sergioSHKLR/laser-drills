# Drill catalog

Generated from `drills.json`. `dyn` = shot count set at run time by calls/scenarios. See [data-formats.md](data-formats.md) for fields.

| ID | Name | Category | Target | Shots | Par (s) | Scoring |
|---|---|---|---|---|---|---|
| `five-shot-par` | 5 shots on the beep (par 5.0s) | training | any | 5 | 5.0 | points |
| `single-draw` | Draw + 1 shot (par 1.8s) | training | silhouette | 1 | 1.8 | points |
| `dot-sequence` | 5-dot sequence (par 8s) | training | five-dot | 5 | 8.0 | points |
| `clay-trio` | Clay trio, shotgun (par 4s) | training | clays | 3 | 4.0 | points |
| `hostage-head` | Hostage: 2 head shots (par 3s) | training | hostage | 2 | 3.0 | points |
| `idpa-course` | IDPA-style familiarization course (8 stages) | course | idpa-hc-diagonal, idpa-hc-left, idpa-hc-lower, idpa-multi, idpa-nt-pair, idpa-practice, idpa-threat | 8 | — | idpa |
| `idpa-all-calls-letter` | IDPA-style random calls (letter landscape) | training | idpa-all-letter | dyn | 15.0 | idpa |
| `idpa-all-calls` | IDPA-style random calls (tabloid 11x17) | training | idpa-all-tabloid | dyn | 15.0 | idpa |
| `shoot-dont-shoot` | Shoot / don't-shoot: threat vs compliant (tabloid 11x17) | training | idpa-all-tabloid | dyn | 10.0 | idpa |
| `shoot-dont-shoot-letter` | Shoot / don't-shoot: threat vs compliant (letter landscape) | training | idpa-all-letter | dyn | 10.0 | idpa |
| `dh-hans-mozambique` | Die Hard: Hans Mozambique | fun | dh-hans | dyn | 4.0 | idpa |
| `dh-stairwell` | Die Hard: Stairwell (Karl) | fun | dh-karl | 2 | 3.0 | idpa |
| `dh-tony` | Die Hard: 31st floor (Tony) | fun | dh-tony | 2 | 2.5 | idpa |
| `dh-franco` | Die Hard: Lobby desk (Franco) | fun | dh-franco | 2 | 3.0 | idpa |
| `dh-heinrich` | Die Hard: Pillar (Heinrich) | fun | dh-heinrich | 2 | 3.0 | idpa |
| `dh-eddie` | Die Hard: The guard (Eddie) shoot/don't-shoot | fun | dh-eddie | dyn | 3.0 | idpa |
| `dh-theo` | Die Hard: Vault tech (Theo) shoot/don't-shoot | fun | dh-theo | dyn | 3.0 | idpa |
| `dh-billclay` | Die Hard: "Bill Clay" impostor | fun | dh-billclay | dyn | 4.0 | idpa |
| `dh-finale` | Die Hard: Roof Finale | fun | dh-finale | 2 | 3.0 | idpa |
| `dh-party` | Die Hard: Christmas party | fun | dh-party | 2 | 3.0 | idpa |
| `dh-uli` | Die Hard: Lobby (Uli) | fun | dh-uli | 2 | 2.5 | idpa |
| `dh-powell` | Die Hard: Friendly ID (Sgt. Powell) | fun | dh-powell | 0 | 4.0 | idpa |
| `dh-lobby` | Die Hard: Lobby, Powell arrives | fun | dh-lobby | 2 | 3.0 | idpa |
| `dh-nakatomi-calls` | Die Hard: Nakatomi random calls (tabloid) | fun | dh-nakatomi | dyn | 12.0 | idpa |
| `dh-nakatomi-sds` | Die Hard: Nakatomi shoot/don't-shoot (tabloid) | fun | dh-nakatomi | dyn | 10.0 | idpa |
| `dh-course` | Die Hard: Nakatomi Plaza story course (7 stages) | course | dh-finale, dh-franco, dh-hans, dh-heinrich, dh-karl, dh-lobby, dh-tony | 7 | — | idpa |
| `crowd-l1` | Crowd Hunt L1 (one attribute) | training | crowd | dyn | 4.0 | idpa |
| `crowd-l2` | Crowd Hunt L2 (two attributes) | training | crowd | dyn | 6.0 | idpa |
| `crowd-l3` | Crowd Hunt L3 (three+ / relative position) | training | crowd | dyn | 9.0 | idpa |
| `carnival-free` | Carnival Shoot: free fire (60 s) | fun | carnival | 20 | 30 | points |
| `carnival-calls` | Carnival Shoot: called shots | fun | carnival | 40 | 60 | game |
| `battle-classic` | Sink-the-Ship: sink the fleet | fun | battle | 64 | 600 | game |
| `battle-timed` | Sink-the-Ship: timed (3 min) | fun | battle | 64 | 180 | game |
| `cards-poker` | Card Shoot: poker hand | fun | cards | 5 | 30 | game |
| `cards-callout` | Card Shoot: call-out | fun | cards | 40 | 60 | game |
| `cards-poker-tab` | Card Shoot: poker hand (Tabloid) | fun | cards-tabloid | 5 | 30 | game |
| `cards-callout-tab` | Card Shoot: call-out (Tabloid) | fun | cards-tabloid | 40 | 60 | game |
| `mar-easy` | Maritime: easy (named target) | training | maritime | 20 | 30 | game |
| `mar-med` | Maritime: medium (by type) | training | maritime | 20 | 30 | game |
| `mar-decision` | Maritime: decision (smuggler or civilian?) | training | maritime | 20 | 20 | game |
| `mar-easy-tab` | Maritime: easy (named target) (Tabloid) | training | maritime-tabloid | 20 | 30 | game |
| `mar-med-tab` | Maritime: medium (by type) (Tabloid) | training | maritime-tabloid | 20 | 30 | game |
| `mar-decision-tab` | Maritime: decision (smuggler or civilian?) (Tabloid) | training | maritime-tabloid | 20 | 20 | game |
| `ct-kit` | Counter-Terror: call by kit | training | ct | 20 | 30 | game |
| `ct-vest` | Counter-Terror: vest! | training | ct | 10 | 10 | game |
| `ct-clear` | Counter-Terror: clear the street | training | ct | 30 | 30 | game |
| `ct-kit-tab` | Counter-Terror: call by kit (Tabloid) | training | ct-tabloid | 20 | 30 | game |
| `ct-vest-tab` | Counter-Terror: vest! (Tabloid) | training | ct-tabloid | 10 | 10 | game |
| `ct-clear-tab` | Counter-Terror: clear the street (Tabloid) | training | ct-tabloid | 30 | 30 | game |
| `fof-sides` | Friend or Foe: sides | training | fof | 30 | 30 | game |
| `fof-tape` | Friend or Foe: single tape | training | fof | 30 | 20 | game |
| `fof-sides-tab` | Friend or Foe: sides (Tabloid) | training | fof-tabloid | 30 | 30 | game |
| `fof-tape-tab` | Friend or Foe: single tape (Tabloid) | training | fof-tabloid | 30 | 20 | game |
| `fof-drones` | Friend or Foe: counter-drone | training | fof | 30 | 20 | game |
| `fof-drones-tab` | Friend or Foe: counter-drone (Tabloid) | training | fof-tabloid | 30 | 20 | game |
| `ankle-standing` | Ankle Draw L1: Standing | training | ankle | dyn | 4.0 | idpa |
| `ankle-seated` | Ankle Draw L2: Seated | training | ankle | dyn | 3.5 | idpa |
| `ankle-walking` | Ankle Draw L3: Walking | training | ankle | dyn | 3.0 | idpa |
| `ankle-any` | Ankle Draw L4: Random start | training | ankle | dyn | 5.2 | idpa |
| `ankle-all` | Ankle Draw: all threats | training | ankle | dyn | 5.5 | idpa |
| `ankle-standing-tab` | Ankle Draw L1: Standing (Tabloid) | training | ankle-tabloid | dyn | 4.0 | idpa |
| `ankle-seated-tab` | Ankle Draw L2: Seated (Tabloid) | training | ankle-tabloid | dyn | 3.5 | idpa |
| `ankle-walking-tab` | Ankle Draw L3: Walking (Tabloid) | training | ankle-tabloid | dyn | 3.0 | idpa |
| `ankle-any-tab` | Ankle Draw L4: Random start (Tabloid) | training | ankle-tabloid | dyn | 7.8 | idpa |
| `ankle-all-tab` | Ankle Draw: all threats (Tabloid) | training | ankle-tabloid | dyn | 7.5 | idpa |
