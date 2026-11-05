# Kusa Kap battle review

Status: first-frame design approved by the user ("good confirmed", 2026-11-02).
Eight-direction battle animation ready for review; no animation approval or installation.

Difficulty: Severe, full-roster rank 71/101. Order comes from `ENEMY_TIERS`
in `include/enemy.h`, ascending IDs within each tier, with tier difficulty
order from `tools/playtest_report.py` (tier-1 bosses before Elite). The
art chart and ready-only F4 run are not the full difficulty roster.

Battle status: absent from reference/fine/done in `redraw_status.json`.
Mini status: absent from `minis/confirmed.json`, no installed individual mini.
Earlier uninstalled still-only draft in `art/enemies/claude/45_kusa_kap/`
is preserved. This work does not change it or any installed asset.

Identity and lore: giant Torres Strait sea eagle, white head/breast/tail,
broad brown wings, yellow hooked beak/talons, carrying a grey dugong.
Source: `art/enemies/45_kusa_kap_gen.py` and the earlier draft's design record.

Runtime: `ENEMY_SHEETS[45]`, native 78x59, eight directions in horizontal
groups, three poses each. `idle_frame_now` plays 0/1/0/2 at 400/250/400/250
ms (1.3 seconds). The 260ms STEP_MS applies to sheets with other frame counts.
KusaKap uses the ordinary Enemy animation hooks and no special attack sheet;
preserve fire cadence and aiming behavior. Do not change gameplay readiness.

Generation uses `tools/pixellab_enemy.py` and this folder's job/prompt.
Raw provider files, manifest and cost ledger: `pixellab-out/45-kusa-kap/`.
The initial edit dry run estimates 30 generations. The source and style
reference are sent at native resolution. Originals remain untouched.

Required stops: first-frame design review before rotation/animation (existing
PixelLab workflow); completed battle animation review before mini; completed
mini review before the next enemy. Only approved, installed work updates
the completion tracker and visible graph.

The external SPRITE_STYLE.md and style_check.py referenced by the repository
are unavailable on this machine. Apply the local ART_DIRECTION.md and derived
STYLE_BRIEF.md, and report local checks separately from visual review.

First-frame result: provider reported 10 generations. Raw output and the
initial palette-only draft exceeded the color budget. `cleanup.lua` applies
the restricted material palette, closes exposed outlines and enforces three
material colors plus black per 16px cell in Aseprite. It preserves the raw
output. The current review is `idle_frame0_review_v3.aseprite`, made from
`idle_frame0_clean_v3.png`; the single tag is `D_design_review`, 400ms.
This is a still design checkpoint, not the completed battle animation.

`frame0_validation.json`: native 78x59, six opaque colors including black,
zero off-palette pixels, binary transparency, zero 16px-cell color violations,
closed outlines, 10.9% interior black, exact Aseprite export, recorded original
hashes unchanged. The user approved this first-frame design before rotation
and animation. No mini or installation yet.

## Battle animation checkpoint

Open `battle/45_kusa_kap_playback_review.aseprite`: all eight direction tags,
four playback frames each, 0/1/0/2 at 400/250/400/250ms. Timing and tags were
read back from Aseprite and verified (`battle/playback_metadata.json`).
`battle/45_kusa_kap.aseprite` is the editable three-pose runtime source;
`battle/45_kusa_kap.png` is its 1872x59 export (78x59 cells). Both export
round trips match exactly. Per-direction GIFs and `all_directions.png` show
every animation pose for visual review.

PixelLab made five directional references and five wingbeat cycles; left
views use the corresponding mirrored right view with separate palette/outline
cleanup. Cost including the first frame: 16 reported generations (10 edit,
1 rotation, 5 animations). The first front animation result was recovered
from its saved result after a native-canvas fit error; it was never resubmitted.

`generate_battle.py` collects raw frames onto a slightly roomier working
canvas without scaling. `pack_battle.py` invokes Aseprite `cleanup.lua` to
restore the carried dugong's original directional silhouettes where generation
made it too small, stabilize its placement, close outlines and enforce color
limits. A 16px temporary border keeps palette-cell alignment; the few extreme
wingtip pixels are redrawn inward before exporting the original 78x59 cell.
No opaque pixels are lost when the working border is removed. The user's
approved front pose is retained pixel for pixel.

`battle/validation.json`: all 24 stored poses pass palette, binary alpha,
color budget, per-16px-cell colors, closed outlines and canvas-margin checks.
Visual inspection covered all directional pose sequences, carried prey,
wingtip clearance and runtime rendering. The external full Bible checker
remains unavailable; these are local checks and visual review, not a claim
of external certification.

`verify_runtime.py` runs the existing battlecensus binary against disposable
copies of the original and draft assets. Both 12-second tests (seed 3872026)
exited successfully with identical gameplay stdout. Three screenshots each
and verification records are in `build_tmp/kusa_kap_battle_review/`.
The final native dimensions preserve the renderer's existing hit radius;
no gameplay source or installed assets were changed. The animation and
installation remain unapproved, and the completion tracker is unchanged.
