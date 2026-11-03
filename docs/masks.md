# Scoring masks and legend

Each target has two printable sheets:
- **Target sheet** (`targets/<key>.pdf` / `.png`): the one you shoot. Full-color art with no zone outlines.
- **Mask sheet** (`targets/<key>-mask.pdf` / `.png`): the same layout and markers, with the scoring zones filled in the legend colors. It's for reference and for checking zones. Don't shoot at it.

The app scores hits against the zone polygons, circles and rectangles in `targets.json` (or your custom zones from the Zone editor). It doesn't read the printed colors.

| Zone type | Color | Meaning |
|---|---|---|
| Hit | navy `#1F4E9A` | Scoring zone. Tiers have their own points, and the top tier is innermost |
| No-hit / no-shoot | white with black hatching | Hostage, bystander or non-threat. A hit is a penalty (HNT +5 s) or a fail |
| Hard cover | black | Hits don't count, and they may count as a miss or penalty |
| Two-hit | green `#2E8B57` | Needs two hits to neutralize |
| Conditional | purple `#7B4FA0` | Hit only when called or when conditions are met |
| Head-only | teal `#00A3B4` | Only head hits count (partial exposure) |
| Backstop | gray `#8C8C8C` | Bystander behind the threat. A hit adds +10 s |

Blank mask templates (Letter and Tabloid) are linked from Home for drawing your own targets. The footer of every target sheet repeats the scoring map using circle swatches.
