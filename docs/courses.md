# Courses

Generated from `courses.json` (source: `tools_courses.py`). These are **original laser adaptations** inspired by well-known program formats (NRA-style qualification ranks, Basic/Defensive Pistol-style curricula, Laser-Academy-style drill types, popular benchmark drills). They are not official course materials and confer no certification.

**Laser distances:** Letter bullseye/silhouette stages are shot at half the standard distance; IDPA-style sheets carry their own printed scale (e.g. 3 yd ≈ 13.5 yd sim).

**Pass logic** (`Core.stagePass`): all listed criteria must hold on a single run; `≥N%` = score / max score; `≤T s` = time from beep to last shot; `final` = IDPA-style raw + penalties; required shot count must be fired (dynamic-call drills excepted). Best run counts; a badge is earned when every stage of a course is passed with the same firearm profile. Qualification ranks unlock in order.

### Qualification: Pro-Marksman  
`qual-pro-marksman` · badge **Pro-Marksman** (Lucide `medal`)

Rank 1 of 5 in a progressive marksmanship ladder (inspired by NRA-style qualification ranks; original laser standards). Pass every stage at 60% or better. Repeat stages as often as you like; your best run counts.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | Slow fire, bullseye | `five-shot-par` | 5 yd real / 2.5 yd laser | ≥60% |
| 2 | Timed fire, bullseye | `five-shot-par` | 5 yd / 2.5 yd laser | ≥55%, ≤12.5 s |
| 3 | Rapid fire, silhouette | `five-shot-par` | 7 yd / 3.5 yd laser | ≥50%, ≤7.5 s |
| 4 | Dot sequence | `dot-sequence` | 3 yd / 1.5 yd laser | ≥60%, ≤15.0 s |

### Qualification: Marksman  
`qual-marksman` · badge **Marksman** (Lucide `award`) · requires `qual-pro-marksman`

Rank 2 of 5 in a progressive marksmanship ladder (inspired by NRA-style qualification ranks; original laser standards). Pass every stage at 70% or better. Repeat stages as often as you like; your best run counts.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | Slow fire, bullseye | `five-shot-par` | 5 yd real / 2.5 yd laser | ≥70% |
| 2 | Timed fire, bullseye | `five-shot-par` | 5 yd / 2.5 yd laser | ≥65%, ≤10.0 s |
| 3 | Rapid fire, silhouette | `five-shot-par` | 7 yd / 3.5 yd laser | ≥60%, ≤6.0 s |
| 4 | Dot sequence | `dot-sequence` | 3 yd / 1.5 yd laser | ≥70%, ≤12.0 s |

### Qualification: Sharpshooter  
`qual-sharpshooter` · badge **Sharpshooter** (Lucide `crosshair`) · requires `qual-marksman`

Rank 3 of 5 in a progressive marksmanship ladder (inspired by NRA-style qualification ranks; original laser standards). Pass every stage at 78% or better. Repeat stages as often as you like; your best run counts.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | Slow fire, bullseye | `five-shot-par` | 5 yd real / 2.5 yd laser | ≥78% |
| 2 | Timed fire, bullseye | `five-shot-par` | 5 yd / 2.5 yd laser | ≥73%, ≤8.5 s |
| 3 | Rapid fire, silhouette | `five-shot-par` | 7 yd / 3.5 yd laser | ≥68%, ≤5.1 s |
| 4 | Dot sequence | `dot-sequence` | 3 yd / 1.5 yd laser | ≥78%, ≤10.2 s |

### Qualification: Expert  
`qual-expert` · badge **Expert** (Lucide `trophy`) · requires `qual-sharpshooter`

Rank 4 of 5 in a progressive marksmanship ladder (inspired by NRA-style qualification ranks; original laser standards). Pass every stage at 85% or better. Repeat stages as often as you like; your best run counts.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | Slow fire, bullseye | `five-shot-par` | 5 yd real / 2.5 yd laser | ≥85% |
| 2 | Timed fire, bullseye | `five-shot-par` | 5 yd / 2.5 yd laser | ≥80%, ≤7.2 s |
| 3 | Rapid fire, silhouette | `five-shot-par` | 7 yd / 3.5 yd laser | ≥75%, ≤4.3 s |
| 4 | Dot sequence | `dot-sequence` | 3 yd / 1.5 yd laser | ≥85%, ≤8.6 s |

### Qualification: Distinguished Expert  
`qual-distinguished-expert` · badge **Distinguished Expert** (Lucide `crown`) · requires `qual-expert`

Rank 5 of 5 in a progressive marksmanship ladder (inspired by NRA-style qualification ranks; original laser standards). Pass every stage at 92% or better. Repeat stages as often as you like; your best run counts.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | Slow fire, bullseye | `five-shot-par` | 5 yd real / 2.5 yd laser | ≥92% |
| 2 | Timed fire, bullseye | `five-shot-par` | 5 yd / 2.5 yd laser | ≥87%, ≤6.0 s |
| 3 | Rapid fire, silhouette | `five-shot-par` | 7 yd / 3.5 yd laser | ≥82%, ≤3.6 s |
| 4 | Dot sequence | `dot-sequence` | 3 yd / 1.5 yd laser | ≥92%, ≤7.2 s |

### Pistol Fundamentals (Basic Pistol-style)  
`fund-basic` · badge **Fundamentals** (Lucide `target`)

Grip, sight alignment, trigger press. Group shooting at four scaled distances (inspired by NRA Basic Pistol-style range work; original content). Laser distance = half the standard distance on the Letter bullseye. Slow and clean beats fast.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | Group at 3 yd | `five-shot-par` | 3 yd / 1.5 yd laser | ≥80% |
| 2 | Group at 5 yd | `five-shot-par` | 5 yd / 2.5 yd laser | ≥75% |
| 3 | Group at 7 yd | `five-shot-par` | 7 yd / 3.5 yd laser | ≥70% |
| 4 | Group at 15 yd | `five-shot-par` | 15 yd / 7.5 yd laser | ≥60% |
| 5 | Trigger control: dots | `dot-sequence` | 3 yd / 1.5 yd laser | ≥80% |

### Defensive Pistol (Defensive-course-style)  
`def-pistol` · badge **Defender** (Lucide `shield`)

Draw from concealment, ankle draw from a kneel, movement and decision. Score at end (IDPA-style: raw time + 1 s per point down). Inspired by defensive pistol course themes; original stages. Say “start” to begin each stage.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | Draw to first shot | `single-draw` | 7 yd / 3.5 yd laser | ≥60%, ≤2.0 s |
| 2 | Draw, 2 to body | `single-draw` | 7 yd / 3.5 yd laser | final ≤4.0 s |
| 3 | Ankle draw, kneeling | `ankle-standing` | kneel at 2–3 yd | final ≤6.0 s, no fail |
| 4 | Move off the X | `single-draw` | 5 yd / 2.5 yd laser | final ≤5.0 s |
| 5 | Shoot / don't-shoot | `shoot-dont-shoot-letter` | Letter landscape at 3 yd | final ≤18.0 s, no fail |
| 6 | Multiple threats | `idpa-course:idpa-multi` | 3 yd laser | final ≤10.0 s |

### Reaction · Hunt · Eyes (Laser-Academy-style)  
`la-style` · badge **Quick Eyes** (Lucide `eye`)

Original drills in the spirit of popular laser-trainer apps: reaction to the beep, hunting the called target, and eyes/decision drills. Inspired by Mantis Laser Academy-style drill types; no copied content.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | Reaction: single shot | `five-shot-par` | 3 yd laser | ≥60%, ≤1.2 s |
| 2 | Reaction: double tap | `single-draw` | 3 yd laser | ≥70%, ≤1.6 s |
| 3 | Hunt: one attribute | `crowd-l1` | 3 yd laser | final ≤20.0 s |
| 4 | Hunt: two attributes | `crowd-l2` | 3 yd laser | final ≤28.0 s |
| 5 | Eyes: friend or foe | `fof-tape` | 3 yd laser | complete |
| 6 | Eyes: decision | `mar-decision` | 3 yd laser | complete |

### FBI-style Qualification (laser)  
`bm-fbi` · badge **Qualified** (Lucide `star`)

Original laser adaptation of a law-enforcement-style qualification: close, fast strings then longer, slower strings. Pass ≥ 80% on every stage.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | 3 yd: 3 rounds | `five-shot-par` | 3 yd / 1.5 yd laser | ≥80%, ≤3.0 s |
| 2 | 5 yd: 4 rounds | `five-shot-par` | 5 yd / 2.5 yd laser | ≥80%, ≤4.0 s |
| 3 | 7 yd: 6 rounds | `five-shot-par` | 7 yd / 3.5 yd laser | ≥80%, ≤6.0 s |
| 4 | 15 yd: 5 rounds | `five-shot-par` | 15 yd / 7.5 yd laser | ≥80%, ≤10.0 s |

### Bill Drill  
`bm-bill` · badge **Bill Drill** (Lucide `zap`)

6 shots to the center-mass rings (8 ring or better) from the draw as fast as you can keep them in. Benchmark par 2.5 s.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | Bill Drill | `single-draw` | 7 yd / 3.5 yd laser | ≥80%, ≤2.5 s |

### El Presidente (laser)  
`bm-elprez` · badge **El Presidente** (Lucide `users`)

Original laser adaptation: turn from facing uprange, 2 each on three threats, simulated reload (rack/reset), 2 each again. Uses the 3-threat sheet.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | El Prez | `idpa-course:idpa-multi` | 3 yd laser (≈27 yd sim) | final ≤16.0 s |

### Dot Torture (laser)  
`bm-dot` · badge **Dot Torture** (Lucide `circle-dot`)

Original precision drill on the 5-dot sheet: repeated slow and fast sequences. Every shot must hit its dot in order.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | Slow sequence | `dot-sequence` | 3 yd / 1.5 yd laser | ≥100%, ≤20 s |
| 2 | Draw sequence | `dot-sequence` | 3 yd / 1.5 yd laser | ≥100%, ≤12 s |
| 3 | Fast sequence | `dot-sequence` | 3 yd / 1.5 yd laser | ≥100%, ≤8 s |
| 4 | Speed sequence | `dot-sequence` | 3 yd / 1.5 yd laser | ≥100%, ≤6 s |

### 3-Seconds-or-Less (laser)  
`bm-3sec` · badge **Under 3** (Lucide `timer`)

Original adaptation of the classic 'three seconds or less' idea: every string must finish in 3 s or less with hits.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | Draw, 1 shot | `single-draw` | 3 yd laser | ≥60%, ≤3.0 s |
| 2 | Draw, 2 shots | `single-draw` | 3 yd laser | ≥60%, ≤3.0 s |
| 3 | Ready, 3 shots | `single-draw` | 3 yd laser | ≥60%, ≤3.0 s |
| 4 | Head shot | `single-draw` | 3 yd laser | ≥100%, ≤3.0 s |
| 5 | Ankle draw, 1 shot | `ankle-standing` | kneel 2–3 yd | ≤3.0 s, no fail |

### Core Skills (laser)  
`bm-core` · badge **Core Skills** (Lucide `puzzle`)

Original skills test in the spirit of instructor 'core skills' assessments: draw, accuracy, pairs, head shot, and a multi-threat string. Pass every stage.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | Draw, 1 | `single-draw` | 5 yd / 2.5 yd laser | ≥80%, ≤1.8 s |
| 2 | Pair | `single-draw` | 5 yd / 2.5 yd laser | ≥80%, ≤2.3 s |
| 3 | Precision | `five-shot-par` | 7 yd / 3.5 yd laser | ≥80%, ≤8.0 s |
| 4 | Head | `hostage-head` | 5 yd / 2.5 yd laser | ≥80%, ≤3.0 s |
| 5 | Multi-threat | `idpa-course:idpa-multi` | 3 yd laser | final ≤8.0 s |

### 5×5 (laser)  
`bm-5x5` · badge **5×5** (Lucide `hand`)

Original take on the 5×5 idea: 5 shots, 5 seconds, one small circle. Use the center ring of the bullseye; anything not 5 pts is a miss.

| # | Stage | Base drill | Distance | Pass |
|---|---|---|---|---|
| 1 | 5×5 | `five-shot-par` | 5 yd / 2.5 yd laser | ≥100%, ≤5.0 s |
