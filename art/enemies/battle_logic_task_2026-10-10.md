# Task for the Battle Logic agent: fit bullet spawn positions to four redrawn enemies

From the enemy-art session, 2026-10-10, at the user's instruction. Could not be sent directly: no session named "Battle Logic" was reachable.

The user's rule: the art session only does sprites; every time a sprite is updated, the battle logic agent gets the task of fitting that enemy's bullet spawn positions to it. Before the user set that rule, the art session had already edited the fight code for these four in `src/enemies.cpp` and `src/battle.cpp` (uncommitted on main; the game builds). The user chose to keep those edits and have you review them. Change anything you see fit; the patterns are yours.

Sprites are drawn 2x about the frame's middle, so an offset = (art pixel - frame middle) * 2. Sources for every sprite: `art/enemies/NN_name_design.py` (holds the coordinates) and `NN_name.txt`.

## 04 Lili

`assets/enemies/04_lili.png`, frame 28x22, 3 frames, views D / R / U (L mirrored).

- Art session's edits: `Lili::move_facing` (left/right in phase 1, up/down in phase 2), `Lili::anim_frame` (scuttle 0 1 2 1 at 90 ms, frame 1 while pinching), a `run` clock.
- **Not done:** bullets still leave from the sprite's centre. Snout: front view about (13.5, 14) in the frame; side view about (24, 11) facing right.

## 54 Billdad

`54_billdad.png` (3 frames), `54_billdad_jump.png` (alt, 3), `54_billdad_slap.png` (flap, 4); frame 28x27; front view in phase 1, back view all of phase 2.

- Art session's edits: `move_facing` = `FACE_DOWN`; `alt_pose` / `anim_frame` for the leap and landing slam (jump frames 0 air, 1 tail raised, 2 slam); `flap_phase` covers all of phase 2 (0 air, 1 tail raised, 2 slam from `SLAP_T * 0.5`, 3 standing); a `landed` flag; `from_tail()` with `FLICK_X/Y` = (15, -11), `BACK_Y` = 15, `SLAM_Y` = 17, used for the flick, the splash and the shockwave.

## 55 Wapaloosie

`55_wapaloosie.png`, `55_wapaloosie_up.png` (alt); frame 26x26, 3 frames; views D and DR only (DL mirrored).

- Art session's edits: `move_facing` (`FACE_DOWN` when the player is within 50 px in x, else down-right / down-left; while humping to its side, the way it goes), a `look` member; the spike fan in `breathe()` leaves from y - 6 (the top of the hump).
- Spore ring and logs untouched (still centre / top of screen).
- The art has no cocked tail any more. The bullets and logs are still tinted violet though the sprite is now rust.

## 58 Agropelter

`58_agropelter.png`, frame 98x65, 8 frames, one row a direction (`rows = true`), front view only.

- `src/battle.cpp`: new `int step_ms` at the end of `EnemySheet` (0 = `STEP_MS`), used by `idle_frame_now()`; row 58 is 8 frames at 162 ms (the old 1.3 s loop).
- `Agropelter`: lashes start on idle frames 2 (right arm) and 6 (left), scream on 4 (were 1, 3, 2); `move_facing` = `FACE_DOWN`; `cur` = the current idle frame; `HAND[8][2][2]` = per-frame hand offsets (right, left) and `MOUTH_Y` = -5; `from_hand()` puts each lash shot and each branch at a hand, the scream ring at the mouth; `lash_a0` and the branch aim are taken from the hand.
- **Worth checking:** the hands are about 80 px either side of the body, so lashes now start much wider than before. Fairness was not play-tested.

## Useful

- In a debug battle (`game.exe --debug`), R drops the enemy to its next phase.
- `test_enemies` in `src/main.cpp` is currently set to 58.

## 57 Dingbat (added later the same day; no fight code was changed for it)

`57_dingbat.png` (5 frames, flying), `57_dingbat_catch.png` (alt, 5, blocking), `57_dingbat_stare.png` (flap, 4). Frame 98x65, same layout as before, so it already displays. One drawn view, 3/4 facing screen right; the left-facing directions are its mirror, the rest copies. Source: `art/enemies/57_dingbat_design.py`.

Offsets are from the frame's middle, times 2, for the right-facing view; negate x for the mirrored view.

- Body middle: about (+9, -1). The body sits right of the frame's middle, so anything fired from x, y leaves from beside it.
- Eyes (the stare's two rings): left eye (+9, -22), right eye (+19, -22). They are small cross shapes now, 5 px apart in art, not two big round eyes.
- Mouth: (+15, -15).
- Near wing (screen left when facing right): root (-6, -3); tip about (-66, -40) wings up, (-64, -18) level, (-58, +30) on the downstroke (flying frame 2). Far wing, shorter: tip about (+60, -30) up, (+62, +16) down.
- Flying frames: 0 up, 1 level, 2 downstroke, 3 down, 4 level; the mouth goes open, shut, open, shut, half over them.
- Blocking pose: both wings wrapped across the front; the curtain spans about x -8..+36, y -34..+26.
- Stare frames: 0 wings up, 1-2 wings lowered with the eyes lit yellow, 3 level.
- Also: the `ENEMY_SHEETS` comment on row 57 in `src/battle.cpp` still says "big, 6 dirs"; it could face only down-right / down-left, since that is all that is drawn.

## 30 Dajna (no fight code was changed for it)

`assets/enemies/30_dajna.png`, same layout as before (8 frames, one row a direction, frame 302x166), so it already displays. One view, 3/4 facing screen right, identical and unmirrored in all 8 directions; the head no longer turns. Source: `art/enemies/30_dajna_design.py`.

Offsets from the frame's middle, times 2, at rest. Everything above the belly sinks 1 art px (2 on screen) on frames 2-5, the neck and head on frames 3-6.

- Mouth: (+214, -18). Eyes: (+230, -52) and (+246, -52). Top of the head: about (+234, -76).
- Pyramid: tip (-26, -166); its doorway about (-56, -14); it spans x -140..+120 at its foot.
- Tail tip: about (-222, +134), swinging up to 16 screen px either way over the 8 frames.
- Feet stand at y +164.
- `Dajna::fire` currently aims and fires from x, y: the frame's middle, in the camel's flank.

## Seen while capturing (not art)

Across several enemies on 2026-10-10, one captured battle frame in about 40 came out with only the HUD: no enemy, player or bullets. It may be the screen capture, but it has recurred (Lili, Dajna).

## 30 Dajna, sitting (the art session redid it; no fight code was changed)

`assets/enemies/30_dajna_sit.png` (4 frames a direction) and `assets/enemies/30_dajna_sat.png` (8 frames a direction) are replaced. Same paths, same layouts, same 302x166 frame, so they already display. Sources: `art/enemies/30_dajna_sit.py`, `art/enemies/30_dajna_sat_user_frame.png` (the seated frame the user finished in Aseprite).

What changed for the spawn points. `Dajna::at()` lowers everything above art row 154 by `SIT_DROP * sit` with `SIT_DROP = 18`. The art no longer moves that way:

- **Seated:** the body (pyramid, doorway) is **32** art px lower; the neck and head (art x 229 and right) are **22** lower; between x 212 and 229 the neck bends from one to the other.
- **On the way down it goes front first, so it tilts.** Art px down at the rump (x 62), at the chest (x 199) and at the head, per sit frame; the body in between is on the straight line from rump to chest:

  | sit frame | rump | chest | head |
  |---|---|---|---|
  | 1 | 0 | 14 | 10 |
  | 2 | 2 | 32 | 22 |
  | 3 | 20 | 32 | 22 |
  | 4 | 32 | 32 | 22 |

- Sit frame 4 is the seated pose itself, the same picture as the seated idle's first frame.

Seated positions, as offsets from the frame's middle times 2 (standing ones are in the Dajna section above):

- Pyramid tip: (-26, -102). Its doorway: about (-56, +50).
- Mouth: (+214, +26). Eyes: (+230, -8) and (+246, -8).
- There are no standing feet when it is down: the legs are folded on its side. The near hind foot lies at about (-114..-78, +164), the near fore foot at about (+92..+132, +164). Stage 3's stomps happen standing, so they are not affected.
- Seated idle: everything above art row 146 sinks 1 art px on frames 2-5 (the neck and head on frames 3-6); the tail's end slides up to 3 art px either way along the ground.

Not checked in the game by the art session: `test_enemies` in `src/main.cpp` was on 06 (set by another session) and was left there.

## 82 Nadubi (no fight code was changed for it)

`82_nadubi.png` (5 frames), `82_nadubi_crawl.png` (flap, 4) and `82_nadubi_scratch.png` (alt, 5) are redrawn. Same paths, frame 98x65 and frame counts, so they already display. Source: `art/enemies/82_nadubi_design.py`.

It now has two drawings only, at the user's choice: from the front (standing, scratching) and from the side (crawling). Every right-facing direction (D DR R UR U) holds the same drawing and the left-facing ones (UL L DL) its mirror, so the per-direction tables in `Nadubi` can collapse to one column (keeping the `97 - x` mirror for left facings).

Claw tips, art px in the 98x65 frame, for the unmirrored drawing:

- Standing, frame 2 (the raised claw the pentagram leaves from): (71, 32). `CX[0]` is already 71; the other four entries should be 71 too.
- Scratching, raised: frame 0 (63, 4), frame 2 (34, 4). `HIGH_X` has 63 and 44.
- Scratching, slashed: frame 1 (57, 47), frame 3 (40, 47). `SLASH_X` has 63 and 47.
- Frames 2 and 3 of the scratch are frames 0 and 1 mirrored, so the left claw's numbers are `97 - x` of the right claw's.

Barb tips on the standing frame, if `tips()` is used again: knees (22, 15) and (75, 15); elbows (32, 18) and (65, 18); spine (42, 24), (48, 20), (55, 24).

The crawl sheet is the side view, shown only while it scuttles. The comment on row 82 of `ENEMY_SHEETS` still says "big, 8 dirs".

`test_enemies` in `src/main.cpp` was set to 82 for this (it was on 30).

## 18 Vatnaormur (no fight code was changed for it)

`assets/enemies/18_vatnaormur.png` is redrawn: same path, frame 114x59, 5 frames, front view only, so it already displays. It is a giant slug now (slate, pink underside, eyes on stalks), at the user's direction. Source: `art/enemies/18_vatnaormur_design.py`; frame 0 is the user's own frame.

**New, and it needs code: the pool.** The user asked for the pool it sits in to "go to the far left and far right and all north of the screen from where the enemy is", and said **the shore should stop the player** (they cannot walk up into the water).

- The picture is `assets/enemies/18_vatnaormur_pool.png`, 320x100 art px. Draw it at 2x with its top left at the screen's top left (0, 0), behind the enemy sprite and under bullets and the player. It then spans the arena's full width from the top down to a wavy shore just below the serpent.
- The shore's lowest water pixel is art row 99 at its deepest, row 96 at its shallowest: screen y 192 to 199. The player's upper limit in this fight should be about there instead of `ARENA_TOP`.
- The sprite carries its own small patch of water in the same blue with no outline, so it disappears into the pool; until the pool is drawn it stands as a small lake, as before.
- The battle has no backdrop draw today (`_draw_enemy` draws marks, the sprite, parts), so this is a new hook.

Positions, art px in the 114x59 frame:

- Mouth: (57, 21) on frame 0. It sways and bobs: frame 1 (60, 20), frame 2 (59, 20), frame 3 (55, 21), frame 4 (54, 22). `mouth()` uses a fixed (56.5, 22); the gold ring leaves on frame 1, where the mouth is about 3 px right and 2 px up of that.
- The mouth is open on frames 0 and 1, closing on 2, shut on 3, opening on 4.
- Coils: still centred on x 30 and x 84 with the water line at y 48, so `HX` and the ripple height are unchanged. Their spikes travel round the arches; white water splashes at their feet (x 18, 42, 72, 96).

## Seen while capturing (not art), again

On the Vatnaormur capture 4 of 40 battle frames came out with nothing below the HUD (shots 1, 2, 12, 13).

## 25 Myrmecoleon (one line of its class was added: it faces front)

`assets/enemies/25_myrmecoleon.png` is redrawn: same path, still 5 frames, but **the frame is 98x79 now (it was 98x69)** and it holds one front view. The frame size is read from the sheet, so it already displays; seen in a debug battle. The user drew frame 0 themselves (ball abdomen, cross eyes); the other frames move their pixels. Source: `art/enemies/25_myrmecoleon_design.py`.

- I added `move_facing()` returning `FACE_DOWN` to `class Myrmecoleon` ("one drawn view"), so the sheet's one view shows wherever the player stands. Nothing else in the class was touched.
- It still fires from `x, y`, the frame's middle (49, 39.5), which is now between its eyes. If the shots should leave from its mouth or its tail, in art px in the 98x79 frame:
  - Mouth: frame 0 (48.5, 52.5), frame 1 (48.5, 53.5), frame 2 (48.5, 53.5), frame 3 (48.5, 51), frame 4 (48.5, 51.5). It is open on frames 0 and 1, half shut on 2, shut on 3, half shut on 4. It drools from x 52.
  - Tail (the ball above its head, which wags): its centre is (48.5, 14.5) on frame 0, (51.5, 15.5) on 1, (50.5, 16.5) on 2, (46.5, 15.5) on 3, (45.5, 14.5) on 4.
- It is 78 px tall where it was 60, and its feet are on row 78 of 79: 5 art px lower against the frame's middle than before.

`test_enemies` in `src/main.cpp` was set to 25 for this (it was on 06).

## Seen while capturing (not art), 25

In the first of two capture runs the game window closed by itself after about 36 of 40 shots, the player still at over half HP; Windows logged no crash for it. The second run held all 40 shots. Shots with nothing drawn under the HUD, as on the Vatnaormur: 2 in the first run, 4 in the second (b03, b19, b35, b36).

## 27 Grootslang (I changed where its shots leave from, at the user's word; no pattern value)

`assets/enemies/27_grootslang.png` is redrawn: same path, frame 98x65, 5 frames, one front view. Typed by hand to the bible; the user took the pose as it was. Source: `art/enemies/27_grootslang_design.py`.

The user asked for this one directly: "implement and make sure the bullets spawning match the new sprite". No session named Battle Logic could be reached, so I made that change myself and it is here for review. In `class Grootslang`:

- Added `SINK`, `SWAY`, `SHAKE` (five numbers each, the same as in the design script) and `cur`, the idle frame showing, set by a new `on_idle_frame` that returns no shots.
- The three `at(...)` calls now use them: tusk tips `(37.5 / 60.5, 34.5 + SINK[cur])`, trunk tip `(49 + SWAY[cur], 47.5 + SINK[cur])`, rattle tip `(81 + SHAKE[cur], 8.5 + SINK[cur])`. The old numbers were (37 / 60, 34), (48.5, 47) and (80, 8); the new ones are the middle of the black tip pixels.
- Nothing else: speeds, angles, counts, clocks, `breathe()` and the gem sweep are as they were.

Checked: on all five frames each of those points is the middle of the tip drawn for it (the check is run against the design script's pixels), and in a debug battle the tusk streams leave the tusk tips, the diamonds the trunk's end, and in phase 2 the spiral the rattle's tip.

`test_enemies` in `src/main.cpp` was set to 27 for this (it was on 25).

## Seen while capturing (not art), 27

Another session was driving its own copy of the game while I captured: its window came up over mine and one of my runs was closed from outside. That is most likely what closed the window during the 25 capture too, not a crash.

## 22 Cactus Cat (art and its sheet row only; nothing in the fight changed)

`assets/enemies/22_cactus_cat.png` is redrawn from the user's own frame: same path, frame now 50x35 (was 46x35), **8 idle frames** (was 3), one 3/4 view (`quarter` class: the game mirrors it when the player is on its left). Source: `art/enemies/22_cactus_cat_design.py`.

What I changed outside the art: its row in `ENEMY_SHEETS` (`src/battle.cpp`) is now `{}, 8, ..., 170` -- 8 frames played straight through at 170 ms (a 1.36 s loop; the old 0 1 0 2 loop was 1.3 s). `class CactusCat` is untouched.

For you to check:
- Its rings and spines still leave from `x, y`, the frame's middle (25, 17.5). The cat's body is drawn on that point: the middle of its coat is (25.3, 18.3) on frame 0, so no art coordinates are needed.
- The cactus tail is behind it, to the left of the frame (columns 1-15, rows 2-21); mirrored, to the right. Nothing fires from it today. If a pattern should ever leave from the tail's flowers, their tips on frame 0 are (6, 3), (2, 10) and (14, 6), and the top two move with the sway: columns +1, +1 on frames 1-2, -1 on 4 and 7, -2 on 5-6.
- The breath moves everything above row 26 up a pixel on frames 2-3 and down a pixel on frames 6-7.
- `breath_frame()` is the default 2 and the class has no `breathe`, so the longer idle fires nothing new.

Seen in the game (2026-10-11): player below it and player to its left (mirrored), rings and spines leaving from its body.

## 70 Trollgadda (art only; nothing in the fight changed)

`assets/enemies/70_trollgadda.png` is redrawn from the user's own frame: same path, frame 98x65, 5 idle frames, but **one side view only** (new bible class `profile`: the right-facing drawing, mirrored when the player is on its left; straight below or above it shows the right-facing one). Source: `art/enemies/70_trollgadda_design.py`.

What I changed outside the art: the comment on its row in `ENEMY_SHEETS` (`src/battle.cpp`). `class Trollgadda` is untouched and still has no art coordinates.

Where the fight's points fall on frame 0 (frame pixels; on screen each is 2 px, from the frame's middle at 49, 32.5; mirror x about 49 when it faces left):
- Scales and bell rings leave from `x, y`: that is on the fish's dark back just right of the gill. The fish's own middle is (43.1, 39.3), about 6 px left and 7 px below.
- Leaves fall from `x +/- 80, y - 20 .. y` on screen = columns 9-89, rows 22.5-32.5. The canopy is columns 36-84, rows 3-22 (it sits over the head and trunk, not over the tail), so today's band starts 27 px left of the canopy and just under it. To have leaves fall out of the canopy: centre about column 60 (x + 22 on screen facing right, x - 22 facing left), half-width about 24 columns (48 on screen), rows 12-22 (y - 41 .. y - 21 on screen).
- The mouth holding the trunk is at columns 59-72, rows 34-42; the trunk's foot is about (66, 38).

What moves, by frame (0..4): the tail fin (columns up to 19) by 0, -1, -2 at its tips, 0, +1 rows; the canopy's top (rows up to 15) by 0, +1, 0, -1, -1 columns; the whole sprite 1 row lower on frames 2 and 3; on frame 2 the lower jaw drops a pixel (`breath_frame()` is still 2: the bells ring on the jaws-widest frame).

Seen in the game (2026-10-11): player below it (faces right) and player on its left (mirrored); the bell ring leaves from its head.

## 60 Rumptifusel (art and its sheet row only; the fight is untouched, but its rhythm changes -- see below)

`assets/enemies/60_rumptifusel.png` is redrawn from the user's own frame, after their reference picture: same path, frame 98x65, **12 idle frames** (was 5), **one 3/4 view** (bible class `quarter`: the sheet holds it facing right, mirrored when the player is on its left; it keeps this view while it lunges, whichever way). Source: `art/enemies/60_rumptifusel_design.py`.

What I changed outside the art: its row in `ENEMY_SHEETS` (`src/battle.cpp`) is now `{}, 12, ..., 162` -- 12 frames at 162 ms. `class Rumptifusel` is not touched.

**For you to decide with the user:** the idle loop is now 1.94 s (it was 1.3 s), at the user's word ("still be the same fps, but it takes longer to close the belly and the eyes"). `breathe()` fires once a loop, when the idle comes to frame 2, so the pore sheets now come every 1.94 s instead of every 1.3 s: about a third fewer. I told the user. If the old rate is wanted, that is a change in the class, not in the art.

The frames (0..11):
- 0 the user's frame, at rest. 1-2 breath in: back and hood up 1 then 2 px, leaning back. **Frame 2 is still "hood reared, belly bared"** (`breath_frame()` 2): its highest frame, the belly fully bare.
- 3-8 the roll of its near edge comes down over the belly (15, 30, 45, 60, 80, 100%); on 8 and 9 no purple shows. Eyes half shut on 5-6, shut on 7-8, half open on 9.
- 10-11 the roll lifts (60%, 30% covered) back to frame 0.
- Its back and hood sink 1, 1, 2, 3, 3, 2, 1 px below rest on frames 5-11 and slump toward its head by up to 3 px.

Where the fight's points fall (frame pixels; on screen each is 2 px from the frame's middle at 49, 32.5):
- Sheets and suck rings leave from `x, y`: on frame 0 that is on its back, in the furrow nearest its head.
- The belly, where the pores are, is columns 35-62, rows 45-59 on frame 0 (the same columns either way it faces): about 20 px below the frame's middle, 40 on screen. If the pore spray should leave from the pores, that is `y + 40` on screen, and only on frames 0-2 is the belly fully bare.

Not seen in the game: the user said no in-game test was needed for art, and another session was play-testing 27 at the time (it had just set `test_enemies` to 27), so I left the debug encounter alone. The game compiles with the new row.

**60 Rumptifusel, corrected the same day:** the user then said "have the enemys pose always be left facing". The sheet now holds the drawing as it was drawn, head to the left, in all eight directions; nothing is mirrored and it does not turn with the player or with its lunge. This is done in the sheet alone (no `move_facing` change). So the positions above hold whichever side the player is on: belly columns 35-62, rows 45-59; its head is at the left of the frame (columns 6-33), its hood at the upper right.

## 71 Namungumi (I changed four things in its class, each at the user's word; no beam speed, angle, count or timing)

`assets/enemies/71_namungumi.png` is redrawn from the user's own frame: same path, frame 98x65, **12 idle frames** (was 5), **front view only**. New beside it: `assets/enemies/71_namungumi_flash.png`, the same 12 frames with the eye pure white (its `alt` sheet). Source: `art/enemies/71_namungumi_design.py`.

What I changed in `src/battle.cpp`: row 71 of `ENEMY_SHEETS` is 12 frames at 162 ms with the flash sheet as `alt`.

What I changed in `class Namungumi` (`src/enemies.cpp`), and the user's words for each:
- `move_facing()` returns `FACE_DOWN` -- "have it only ever face front".
- `eye()` is now one point, `x + 1, y + 20`: the pupil is frame pixel (49, 42) on every frame -- "make sure the eyes are still subject to lasers shooting from them".
- `alt_pose()` (new): the white-eyed sheet flashes for `FLASH_T` 0.3 s (on/off every 50 ms), then holds for `WHITE_T` 0.2 s before `beam_t` reaches `every()`, and stays on while a beam is shooting out or charged (`b.t < GROW_T + HOLD_T`) -- "eyes flash and turn pure white before turning into lasers as a warning". The timings are mine; the user saw them in a mock-up and said "looks good".
- It shuffles sideways on idle frames 7-11 (`on_idle_frame` keeps the frame; `update` moves `x` at `WALK_SPEED` 14 px/s, the other way each loop, within `WALK_REACH` 16 px of `HOME_X` 320) -- "have it in battle move a little bit during the walking frames".

For you to check or decide:
- **The ring comes less often.** `breathe()` fires once an idle loop (frame 2), and the loop is now 1.94 s where it was 1.3 s. I told the user. Frame 2 is still its highest frame (the crest up 2 px); the eye no longer glows brighter on it.
- A live beam now follows the eye: `update()` sets `b.ox, b.oy` from `eye()` every frame while the beam is on (the user: "have laser spawner follow the eyes position even when moving"). So the dashed shots also appear along the line where the eye is at that moment.
- The ring and the three aimed shots still leave from `x, y`, the frame's middle, which is on the cloak above the eye; the eye is 20 px lower on screen.
- `px_` and `py_` are no longer read by `eye()`; I left them.

Seen in the game (2026-10-11, one run): the front view, beams passing through the eye, the eye white before and during them. The run was cut short at about 7 s when the game window closed; Windows logged no crash and another session was active at the time.

## 74 Bes Rap (art only; class not touched)

`assets/enemies/74_bes_rap.png` is redrawn from the user's own frame (2026-10-11): same path, frame 98x65, **5 idle frames at the default 260 ms** (1.3 s loop, unchanged), **front view only, always as drawn** -- the same drawing in all eight directions, never mirrored (the head is turned to its right, our right). Source: `art/enemies/74_bes_rap_design.py`. The `ENEMY_SHEETS` row is unchanged but for its comment.

The frames (0..4):
- 0 at rest (the user's frame). 1 winds up: upper body a row higher, head a pixel back.
- **2 the spit** (`breath_frame()` 2, as before): head lunged 2 px right and 1 down, jaw dropped 3 rows, foam at the lip.
- 3 jaw coming up, spit hanging off the chin. 4 breathes out, upper body a row lower.

**For you: where the spit leaves.** On frame 2 the open mouth is columns 56-67, rows 22-24, its middle at frame pixel **(62, 23)**; the lip at its front is column 68. On screen that is `x + 26, y - 19` from the frame's middle (49, 32.5) at 2x. `breathe()` still picks a point per facing (`fx`/`fy` table; D = (58, 20), i.e. `x + 18, y - 25`), but every facing now shows this one drawing, so the table should become the one point. `move_facing` can stay as it is -- nothing turns.

Not seen in the game yet; the game compiles. `test_enemies` in `src/main.cpp` is set to 74.

## 48 Bjarndyrakongur (art only, plus FACE_DOWN)

`assets/enemies/48_bjarndyrakongur.png` is the user's own drawing (2026-10-11): a standing polar bear king, horn with a star, orange-and-red tufts round the head. It is now **giant** (was medium): frame **64x142** (drawn 57x136, 272 px tall on screen at 2x), **12 idle frames at 162 ms** (1.94 s loop), **one row per direction**, **front view only**. Source: `art/enemies/48_bjarndyrakongur_design.py`.

What I changed: row 48 of `ENEMY_SHEETS` in `src/battle.cpp` (`{}, 12, true, ..., 162`), and `move_facing()` returning `FACE_DOWN` in `class Bjarndyrakongur` (the sheet's left rows are mirrors; the bear is drawn to be seen from the front only). The fight itself is untouched: it still fires everything from `x, y`.

The frames: 1-7 a breath (all above the trunk up 1-2 px, highest on 3-5); hands sway a pixel right on 2-4, left on 7-9; tufts flare on 3-4 and 8-9; star twinkles; **a cold-breath puff from the mouth on 5-9**, drifting to our left and thinning.

**For you: its parts, in frame pixels at rest (frame 0), and from the frame's middle (32, 71) at 2x:**
- the star on its horn (the obvious place for anything magic): (32, 8) -> `x + 0, y - 126`
- the mouth (where the puff leaves): (33, 44) -> `x + 2, y - 54`
- the paw on its belly: (37, 85) -> `x + 10, y + 28`; the hanging paw's tips: (52, 97) -> `x + 40, y + 52`
Breath frames lift the star and mouth 1-2 px higher (2-4 on screen). `x, y` now sits in the middle of its chest, and the hitbox radius is 0.4 x 2 x 64 = 51 px (from the frame's narrow side) -- small against 272 px of height; you may want to set it yourself.

Not seen in the game yet. `test_enemies` was left at 74 (another session set it minutes before).

## 28 Opimachus (art, plus the two frame hooks and the crest points)

`assets/enemies/28_opimachus.png` is redrawn (2026-10-12) after the user's reference: a crested, sitting cat-griffin in the old sheet's sand and gold, no wings and no rabbit ears. Same path, frame **50x39** (unchanged, so `at()` is unchanged), **10 idle frames at 130 ms** (1.3 s, the old `0 1 0 2` loop's length), **one view, always as drawn**: the same drawing in all eight directions, never mirrored (tail to our left, haunch to our right). Sources: `art/enemies/28_opimachus_pose_first.py` (frame 0), `28_opimachus_design.py` (the frames), `28_opimachus_install.py`.

The user asked for "the animation speed match its bullet spawn rate" and then "confirmed for battle", so I made the smallest fight edits that keep the spawn rate where it was. No speed, count, angle or gap is changed.

What I changed in `class Opimachus` (`src/enemies.cpp`) and `ENEMY_SHEETS` (`src/battle.cpp`):
- row 28: `{}, 10, false, ..., 130`.
- `on_idle_frame`: the peck fired on frame 2, now `PECK_FRAME` 8 (shown from 1040 ms; the old frame 2 began at 1050 ms). The ear rings fired on frame 1, now `CREST_FRAME` 3 (shown from 390 ms; old frame 1 began at 400 ms). Both still fire once a loop.
- the two ear-tip points `at(20, 5)` and `at(29, 5)` are now the tops of the two outer crest plumes as drawn on frame 3: `at(22, 4.5)` and `at(36, 4.5)`. **They are 14 art px apart where the ears were 9** (28 against 18 on screen), so the two rings start further apart. Say if you want the two tall middle plumes instead: `at(27, 2.5)` and `at(32, 2.5)` on frame 3, 5 art px apart.
- the peck rings still leave from `x, y`, the frame's middle (25, 19.5): that is now the beak's tip over the hood.

The frames (0..9): tail as drawn on 0 and 5, curled up on 2-3, stretched out low to our left on 7-8; upper body a pixel up on 2-4 and a pixel down on 8-9; crest blown to our right most on 3, back a pixel to our left on 7-8.

Plume tops per frame, frame pixels (left, right): 0 (20, 5.5) (34, 5.5) / 1 (21, 5.5) (35, 5.5) / 2 (21, 4.5) (35, 4.5) / 3 (22, 4.5) (36, 4.5) / 4 (21, 4.5) (35, 4.5) / 5 (21, 5.5) (35, 5.5) / 6 (20, 5.5) (34, 5.5) / 7 (19, 5.5) (33, 5.5) / 8 (19, 6.5) (33, 6.5) / 9 (20, 6.5) (34, 6.5).

The game compiles. Not seen in a battle yet. `test_enemies` in `src/main.cpp` is set to 28 (it was 74).

## 24 Zoureg (art, and how the fight shows it; the three heads are gone)

Redrawn 2026-10-12 to its old design. The user's words: "it should have 4 directions for the first phase", "it must be dashing frames since it moves fast during 1st phase", "phase 2 it keeps only 1 head but stays idle", then "looks good implement it". Frame **44x29** as before. Three sheets, each with front, side and back drawn (the left is the side mirrored; a diagonal below it takes the front, one above it the side):

- `assets/enemies/24_zoureg.png` -- the idle, **6 frames at 170 ms** (1.02 s; it was `0 1 0 2`, 1.3 s). Shown resting in phase 1 and all through phase 2.
- `assets/enemies/24_zoureg_windup.png` -- its `alt`, same layout: head drawn back, the whole snake a tone hotter, flickering. Shown while it aims.
- `assets/enemies/24_zoureg_dash.png` -- its `flap`, 4 frames a direction at 70 ms: uncoiled and thrown like a knife, blade first. Shown while it thrusts.

`assets/enemies/24_zoureg_three.png` is no longer loaded (the files are still there). Sources: `art/enemies/24_zoureg_pose_first.py`, `24_zoureg_design.py`, `24_zoureg_install.py`.

What I changed in `class Zoureg` and row 24 of `ENEMY_SHEETS`. No speed, time, count, angle or gap is changed:
- `anim_frame()` is gone (it picked frames 1 and 2 of the old sheet, and the three-headed sheet's bob). `alt_pose()` is now `state == AIM`; new `flap_phase()` runs the dash sheet through `THRUST` (`DASH_LOOP` 0.28 s).
- `move_facing()`: aiming and thrusting it faces the nearer of the four axes of its thrust (was the nearest of eight); `HOME` and `SHEARS` are `FACE_DOWN`; resting it faces the player as before.
- **Phase 2's three lasers all leave one point now**, the blade's point on the idle's front view: `heads()` returns `x, y + 2 * (row + 0.5 - 14.5)` for all three, the row by idle frame `{2, 1, 1, 2, 3, 3}` (`on_idle_frame` keeps the frame). They used to leave three points 26 px either side and 8 px below the middle one. **The user has not ruled on this**: I asked whether all three should leave the one point or the pattern should change, and the answer was "implement it". The shears' geometry is worked out from the heads' positions, so the gap they close to is the same width; what is different is that the three beams now fan from a single spot. `shear_origin()` (the aim, and where the spit leaves) is untouched at `x, y - 12`.
- `BELLY` (where the cut line runs under it) was art row 26, the old coil's underside, 23 px below its middle. The dash is drawn about the frame's middle, so it is now art row 17, 5 px below: the cut forms along the dashing body. The cooling cut and its embers are latched from the same value, so they sit 18 px higher than they did.

For you to check: the rest between thrusts now shows the 6-frame idle at 170 ms; nothing fires on idle frames. The idle's breath moves the blade's point by a row either way (2 px on screen), which the lasers follow.

The game compiles. Not seen in a battle yet. `test_enemies` in `src/main.cpp` is set to 24.

## 78 Zankallala (art, and where the fight reads its staff and hat)

Redrawn 2026-10-12 after the user's reference: a hairy rider in a beehive hat, red eyes, on a jerboa, a snake in its hand for a staff. The user's words: "only need 4 directions", "when its idle it raises its staff which matches bullet spawner for the battle. it also needs dashing animation for 4 directions", then "ok put it into fight please". Frame **58x53** as before, so `at()` is unchanged. Front, side and back are drawn; the left is the side mirrored; a diagonal below it shows the front (the lower left one mirrored), one above it the side.

- `assets/enemies/78_zankallala.png` -- the idle, **10 frames at 130 ms** (1.3 s, the old `0 1 0 2` loop's length; `anim_speed()` still stretches it to its stop). The staff is up 2 px on frames 2 and 5 and 5 px on frames 3 and 4.
- `assets/enemies/78_zankallala_run.png` -- the `flap`, 4 frames a direction: the jerboa bounding 0 / 4 / 7 / 2 px off the ground, the staff levelled ahead like a lance from the side.

Sources: `art/enemies/78_zankallala_pose_first.py`, `78_zankallala_design.py`, `78_zankallala_install.py`.

What I changed in `class Zankallala` and row 78 of `ENEMY_SHEETS`. No speed, time, count, angle or gap is changed:
- `breath_frame()` 1 -> `BOAST_FRAME` 3: the idle frame the staff is first full up, shown from 390 ms where the old frame 1 began at 400. The boast still fires once a loop.
- `staff()`: the tip as drawn. Standing: column 44 (front), 36 (side), 14 (back), 22 and 14 for the mirrored cells; row 13.5, less what the idle frame shown has it raised (`on_idle_frame` keeps the frame) -- so the boast's sun leaves **10 px higher on screen** than the resting tip. Running: column 48 and row 19.5 from the side (10 mirrored), 44 / 14 and row 13.5 from front and back, less `hop()`, the dash frame's height. The old table was one row (13) for every facing and state.
- **The run's laser now starts at the lance's tip and rides the bounds**: its root moves up to 14 px on screen with the dash frames while its far end stays where it was latched. Before, it started at a fixed point. Say if you would rather it stayed steady.
- `hat()` (new): the bees leave the middle of the hat as drawn -- column 29.5 (front, back), 26.5 (side), 31.5 / 28.5 mirrored, row 15.5 less `hop()`. They left `at(27, 21)` whichever way it faced.
- `run_face` is the nearer of the four axes of its run (`axis_facing`), where it was the nearest of eight. Standing it still faces the player.
- The spurs still leave `at(29, 50)`, its feet.

The game compiles. Not seen in a battle yet. `test_enemies` in `src/main.cpp` is set to 78.

## 07 Alber (art, and its fire now leaves the mouth)

Redrawn 2026-10-12, larger. The user's words: "make it larger than it is now but just have the sheet of it flying around" (answered: big tier, about 1.6x; 4 directions), then they edited the front's first frame themselves and asked to "have all other frames match and have it flapping its wings and flying while its legs and tail sway", then "looks good confirm. implement please".

- `assets/enemies/07_alber.png` -- its only sheet: **frame 72x64** (was 40x41), **6 frames at 120 ms** (0.72 s, one wingbeat; it was `0 1 0 2`). Drawn about 60 x 52 where it was 39 x 33. Front, side and back are drawn; the left is the side mirrored; a diagonal below it shows the front, one above it the side.
- Tier: now **big** (the user). Its hitbox follows the frame, so it is larger too.

Sources: `art/enemies/07_alber_pose_first.py` (the first frames; the front's head, body and feet are the user's pixels), `07_alber_design.py` (the wingbeat), `07_alber_install.py`.

What I changed in `class Alber` (`src/enemies.cpp`) and row 7 of `ENEMY_SHEETS` (`src/battle.cpp`). No speed, time, count, sweep width or gap is changed:
- row 7: `{}, 6, false, ..., 120`.
- new `at()` (72x64) and `mouth(facing)`: the mouth as drawn -- frame pixel (36, 20.5) from the front, (63, 18.5) from the side (9 mirrored), and from behind the top of its head (36, 8), since the mouth is past it. The body rides the wingbeat, so the row is that plus 3, 2, 1, 0, 1, 2 by the frame shown (`on_idle_frame` keeps the frame).
- `fire()`: the flame stream and phase 2's ember **leave the mouth** (`from`, `ox`, `oy`) where they left `x, y`, the middle of the sprite. On screen that is 17 to 23 px above the middle from the front and 54 px to the side and 21 to 27 px up from the side.
- **The aim is taken from the mouth too** (`aim_at(mx, my, ...)`, it was from `x, y`), so the sweep still crosses where the player stood when it drew breath. The locked angle is as before: latched at the start of each breath. If it turns to another view mid-breath the stream's root jumps to that view's mouth while the locked angle stays. Say if you would rather the root stayed put for the whole breath.

Nothing fires on a frame of the wingbeat; the frames are: wings raised, level, lowered, lowered, level, raised.

The game compiles. Not seen in a battle yet. `test_enemies` in `src/main.cpp` is set to 7 (it was 78).

## 39 Ajaju (art, four directions, and the frames its volleys fire on)

Redrawn 2026-10-12. The user's words: "ajaju next please", "front looks good, have it be 4 directions as well as idleing breathing and tongue and tail flipping animation", on the idle "looks fine. just make it less created from just shapes especially in the side profiles", then "confirmed". Frame **62x47** as before. Front, side and back are drawn; the left is the side mirrored; a diagonal below it shows the front (the lower left one mirrored), one above it the side.

- `assets/enemies/39_ajaju.png` -- its idle, **10 frames at 130 ms** (1.3 s, the old `0 1 0 2` loop's length). Head and body a row up on frames 2-4 (the breath, stilts planted); tongues fanning on 2-3-4, widest on 3, and a smaller flick on 8; the tail opens on 5, is flipped out on 6-7 and curls back through 8.
- No call frame (mouth open) and no walking frames were asked for: it stalks to the middle on its idle.

Sources: `art/enemies/39_ajaju_pose_first.py`, `39_ajaju_design.py`, `39_ajaju_install.py`.

What I changed in `class Ajaju` (`src/enemies.cpp`) and row 39 of `ENEMY_SHEETS` (`src/battle.cpp`). No speed, count, angle or gap is changed:
- row 39: `{}, 10, false, ..., 130`.
- the tongue sickles fire on idle frame **3** (it was 1): 390 ms into the loop where it was 400.
- the "wa-o" rings fire on idle frame **8** (it was 2): 1040 ms where it was 1050. There is no mouth-open frame now; they leave on the tongues' second flick.
- `mouth(facing)`: the mouth as drawn -- frame pixel (31.5, 16.5) from the front, (52, 16.5) the tip of the snout from the side (10 mirrored, 30.5 for the mirrored front), and that spot on its head from behind. The sickles leave a row higher (frame 3 is in the breath). It was (31.5, 16) for the one view.
- **`move_facing()`: phase 1 it now turns to face the player** (it was the front always), so the sickles and rings leave the snout, 42 px to the side on screen, when the player is beside it. **This was my choice: the user asked for four directions and did not say how it turns.**
- **Phase 2 it still shows its front**, walking down to the middle and for the lasers: six hot beams share the mouth as their root, and a turn to the side would jump all six 42 px sideways under the player. Their root is 1 px lower on screen than before (16.5, the drawn mouth line) and does not ride the breath. Say if it should turn in phase 2 too; the beams would then need a root that does not move.

The game compiles. Not seen in a battle yet. `test_enemies` in `src/main.cpp` is set to 39 (it was 7).

## 86 Leucrocotta (art, four directions, a run sheet, and the idle tied to its call)

Redrawn 2026-10-12. The user's words: "Leucrocotta next please" (answered: 4 directions), then "the front and back was too wide. i fixed the front now do the back and animate all poses running for the sprite sheet and idle" (they redrew the front themselves; it is kept pixel for pixel), then "only have it run using sideways sprites not up and down. for up and down just have idle", then "ok implement please". Frame **98x65** as before, big tier. Front, side and back are drawn; the left is the side mirrored; a diagonal below it shows the front (the lower left one mirrored), one above it the side. It had eight drawn views.

- `assets/enemies/86_leucrocotta.png` -- the idle, **5 frames at 170 ms** (0.85 s, `CALL_EVERY`): head and body a row up on frames 1-2, the mouth gaping on its two ridges of bone on frames 2-3, the tail swinging.
- `assets/enemies/86_leucrocotta_run.png` -- new, its `flap`: a 4-frame gallop **drawn from the side only**. Its front and back cells hold the idle's first four frames; the fight only runs it sideways, so they are not shown.

Sources: `art/enemies/86_leucrocotta_pose_first.py` (the front is the user's pixels), `86_leucrocotta_design.py`, `86_leucrocotta_install.py`.

What I changed in `class Leucrocotta` (`src/enemies.cpp`) and row 86 of `ENEMY_SHEETS` (`src/battle.cpp`). No speed, time, count, angle or gap is changed, and the call is still on its own clock:
- row 86: `{}, 5, false, "assets/enemies/86_leucrocotta_run.png", ..., 170`.
- new `anim_frame()`: `((int)(call_t / 0.17) + 2) % 5`. **The sprite follows the fight's call clock, not the other way round**: frame 2 (mouth open) shows the moment each call leaves, in both phases, and on arrival in phase 2. The user was asked whether to move the call onto an idle frame and did not answer; this keeps the fight's timing exactly as it was. One side effect: when it holds a call because the player is right by it, the mouth still opens.
- new `flap_phase()`: the gallop while `LEAVING` or `ENTERING`, **a stride every 0.32 s (my pick)** -- about 200 px of ground a stride at `DASH`. Before, it slid on its idle.
- `mouth()`: the open mouth as drawn on frame 2 -- frame pixel (51, 21) from the front (47 mirrored), (80, 18.5) its front end from the side (18 mirrored), and from behind its crown (50.5, 8). It was (59.2, 21.8) front and (75.9, 20.6) side, with their own diagonals. On screen the front point moves 16 px left (the head is now in the middle of the frame, it was turned to one side) and the side point 8 px forward and 4 px up.
- `move_facing()` is unchanged: standing it faces the player, running it faces the way it runs (always left or right).

The game compiles. Not seen in a battle yet. `test_enemies` in `src/main.cpp` is set to 86 (it was 39).

## 72 Mahwot (art, left and right only, and where its beam leaves)

Redrawn 2026-10-12. The user's words: "mahwot next please. left and right swimming. and firring from its mouth idle" (answered: the firing pose is left and right only too); they then edited both first frames themselves ("im going for the enemy looking forward with their body turned and their eyes lit up from shooting laser"), asked for the shooting frame's head to be redrawn ("the head area to fix the enemys design more"), then "when swimming have its arms and legs move . when it fires have it breath and idle still", then "ok looks good implement please". Frame **98x65** as before, big tier. **One view is drawn, the side; the left is its mirror.** It had eight drawn views. The sheets still hold eight direction slots; the front and back ones hold the side view and are never shown.

- `assets/enemies/72_mahwot.png` -- swimming, **6 frames at 105 ms** (0.63 s, half of its weave; it was 5 frames): a wave down its body, its limbs paddling. The swim frame is the user's drawing.
- `assets/enemies/72_mahwot_roar.png` -- its `alt`, shown while it breathes its beam, the same 6 frames at 105 ms: stopped and reared, its head turned to face the viewer, eyes and plates lit blue, mouth open; it breathes (chest and head a row up on frames 2-4) and is otherwise still. The body is the user's drawing, the head mine.

Sources: `art/enemies/72_mahwot_pose_first.py`, `72_mahwot_design.py`, `72_mahwot_install.py`. The user's own two frames: `art/_backup/72_user_frames_20261012/`.

What I changed in `class Mahwot` (`src/enemies.cpp`) and row 72 of `ENEMY_SHEETS` (`src/battle.cpp`). No speed, time, count, angle or gap is changed:
- row 72: `{}, 6, false, nullptr, "assets/enemies/72_mahwot_roar.png", nullptr, 1, 1, nullptr, 105`.
- **To breathe it turns left or right, to the side the player is on** (`px < x`); it turned any of eight ways. At the right end of its lane it will nearly always face left, at the left end right.
- **The beam's root is the glow drawn in its open mouth**: frame pixel (75, 30) facing right, (23, 30) facing left. It was (83, 27) / (14, 27) from the side, (72 / 25, 27) on a diagonal and (64, 27) from the front or back. With the player below it -- the usual case, when it used to face down -- the root is now **22 px to the right or 82 px to the left on screen** of where it was, and 6 px lower. The aim is still taken from the root at the player, so the beam still crosses where they stand; its angle differs a little.
- The root is latched once, as before, at the rest position: the beam does not ride the breath (the drawn mouth is 2 px higher on screen for three of the six frames).
- The wake still leaves `x - dir * 30, y`, behind its middle. Not touched; the tail's end is about 88 px behind the middle on screen if the wake should leave there.

The game compiles. Not seen in a battle yet. `test_enemies` in `src/main.cpp` is set to 72 (it was 86).

## 75 Makalala (art: the idle from the front, flying from the side)

Redrawn 2026-10-12. The user's words: "makalala. front idle. left and right flying", then "yes that looks good now animate please" (yes: keep the scream frame), then "good confirm in game". Frame **98x65** as before, big tier. It had eight drawn views for both sheets; now **one view each**: the idle is the front, the flying is the side with the left its mirror. Every slot of both sheets holds that one view.

- `assets/enemies/75_makalala.png` -- the idle, **5 frames at the game's own 260 ms** (unchanged: 1.3 s): it breathes (a row up on frames 1-3), **screams on frame 2** (beak gaping in the middle of its face, wings flung out -- 41 px wide for that frame, 23 at rest), and blinks on frame 4.
- `assets/enemies/75_makalala_fly.png` -- its `flap`, 4 frames: wings raised, level, lowered, level; the club glowing, its middle on frame pixel (49, 15) in every frame.

Sources: `art/enemies/75_makalala_pose_first.py`, `75_makalala_design.py`, `75_makalala_install.py`.

What I changed in `class Makalala` (`src/enemies.cpp`); row 75 of `ENEMY_SHEETS` keeps its values (only its comment changed). No speed, time, count, angle or gap is changed:
- new `move_facing()`: **planted (phase 1) it always shows its front** (it turned to face the player, any of eight ways); **flying (phase 2) it faces left or right, to the side the player is on** (`fly_face`, set each `update`). It turns over when the player crosses under it.
- `beak()`: one view now. The spiral leaves the closed beak's tip, frame pixel (49.5, 21.5); the scream's rings leave the middle of the gape, (49.5, 16.5). From the front it was (49, 18) and (49, 17): the spiral's origin is **7 px lower on screen**, the scream's 1 px higher. The side and diagonal entries of the old table are gone with those views. The spiral does not ride the breath (the tip is 2 px higher on screen on frames 1-3), and through the scream frame it still leaves the closed-tip point, as it did.
- `club()` is untouched: (49, 15), which mirrors onto itself, so the lasers and the ring leave the same screen point whichever way it faces. The drawn club's middle is within 1 px of it.

The game compiles (the first link was refused while the user had `game.exe` open; it went through once the game was closed). Not seen in a battle yet. `test_enemies` in `src/main.cpp` is set to 75 (it was 72).

## 21 Asp (art, four directions, and the frame its hiss leaves on)

Redrawn 2026-10-12. The user's words: "Asp next please" (answered: 4 directions), "looks good confirm" on the first frames, then on the idle "have tail and body bounce and breath", then "good confirm". Frame **42x35** as before, so `at()` is unchanged. Front, side and back are drawn; the left is the side mirrored; a diagonal below it shows the front (the lower left one mirrored), one above it the side. It had eight drawn views. The old greens were not palette colours; they are now.

- `assets/enemies/21_asp.png` -- its idle, **10 frames at 130 ms** (1.3 s, the old `0 1 0 2` loop's length): the head sways a pixel either way, the body dips a pixel on frames 1 and 6 with the tail springing out, the coils swell a pixel at each end on frames 3-5, the tail's tip is in its ear on frames 3-5, and the forked tongue is out on frames 8-9.

Sources: `art/enemies/21_asp_pose_first.py`, `21_asp_design.py`, `21_asp_install.py`.

What I changed in `class Asp` (`src/enemies.cpp`) and row 21 of `ENEMY_SHEETS` (`src/battle.cpp`). No speed, time, count, angle or gap is changed:
- row 21: `{}, 10, false, ..., 130`.
- `breath_frame()` 2 -> **8**: the hiss still starts as the tongue flicks out, 1040 ms into the loop where it was 1050.
- `tongue()`: the tip as drawn on frame 8, the middle of the fork's two ends -- frame pixel (21.5, 14.5) from the front (20.5 for the mirrored lower-left diagonal), (37.5, 9.5) from the side (4.5 mirrored), and from behind the top of its head (21.5, 4.5). The old table had its own diagonals: (32, 15.5) and (9, 15.5) below, (28, 7) and (14, 7) above. So **on a lower diagonal the hiss now leaves the front view's tongue** (21 px nearer the middle on screen than before), and **on an upper diagonal the side view's** (19 px further out and 5 px lower). Front, side and back move by 2 px or less, except the back, 5 px higher.
- On frame 8 the head neither sways nor dips, so the latched point is the drawn tip.
- The fang rings still leave `at(21, 28)`, the middle of its coils. Not touched.
- `move_facing()` is unchanged: it faces the player, and holds its facing through a hiss.

The game compiles. Not seen in a battle yet. `test_enemies` in `src/main.cpp` is set to 21 (it was 75).
