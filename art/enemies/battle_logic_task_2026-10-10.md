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
