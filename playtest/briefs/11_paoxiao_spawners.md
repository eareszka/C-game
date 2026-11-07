# Battle task: SPAWNERS (new) + Paoxiao (11) phase 2 redo

From the user (2026-11-06), via the animation session:
"new approach to this enemy. no dashing during 2nd phase, have two eye balls come from the body and to the
left and right of the monster both of which are a new class of bullet/battle functionality called
'spawners' they behave like most shmups. the player cant target them"
The user's answers to follow-up questions:
- Movement: HOVER beside it (left and right of Paoxiao, bobbing a little) -- turrets locked to the boss.
- Their fire: YOURS to design -- shmup-style emitters (aimed streams, spirals, rings...), battle pattern
  rules, MEDIUM tier, 640 HP.
- Lifetime: ALL OF PHASE 2 (gone when Paoxiao dies). Touching one HURTS (a bar, like the body's
  contact damage). Player shots pass straight through them (untargetable).
- The body: STANDS, KEEPS CRYING (its eye-of-bullets cry and eye shot, as now).

## 1. A generic spawner system (reusable by later enemies)
In the battle engine (src/battle.cpp, include/enemy.h): a spawner = position, age, a sprite sheet, its own
fire. Player shots ignore them; touching one costs a bar (as `contact_damage`); drawn above the enemy and
below the bullets; cleared when the enemy dies. Suggested: `Enemy::spawners(Spawner out[], int max)` read
each frame, like `Enemy::parts` -- your call.

## 2. Paoxiao phase 2
- Remove WAIT/AIM/LUNGE (no dash). It stands where it is, keeps the cry + eye shot.
- Entering phase 2: two eyeballs come out of the flank eye (start at the eye opening's spot) and settle to
  its LEFT and RIGHT, hovering/bobbing, for the rest of the fight.
- Keep this fight's earlier rules: no fading bullets; the cry from the flank eye opening (table in
  playtest/briefs/11_paoxiao_eye_origin.md).

## 3. Animation (the animation session makes the art; you apply these)
- Phase 2 body: the eye-shut alt sheet ALL phase (`alt_pose()` = ENRAGED) -- its eyes have left it.
  `flap_phase()` -> -1 (no sprint/warning any more).
- Spawner sheet: `assets/enemies/11_paoxiao_spawner.png`, one row, 7 frames (frame size = height x height,
  square; the animation session will confirm the size in a reply), same in every direction, drawn 2x:
    0-1 emerge (squeezing out, popping round), one 260 ms step each, from age 0
    2-5 hover loop: frame = 2 + (int)((age - 0.52f) / 0.26f) % 4
    6   firing flash: show it for one 260 ms step each time that eyeball fires a volley
Preview `game.exe --battle 11` (`C:\msys64\mingw64\bin` first on PATH); the user approves there.

## Spawner sheet READY (animation session)
`assets/enemies/11_paoxiao_spawner.png` is installed: one row, 7 frames of 32x32 (224x32), drawn 2x about the
spawner's position (so ~42x42 px of eyeball on screen; its hurt circle ~18 px). Frames as above:
0-1 emerge, 2-5 hover (pupil jerks left, right, up, middle), 6 firing flash (swollen, pinprick pupil).

## From the user (2026-11-06): the eye pattern comes from the two eyes
"during this phase no eye pattern spawns from the enemy but spawns from the two eyes"
- In PHASE 2 the body's eye-of-bullets cry NO LONGER spawns from Paoxiao's flank: it spawns from the two
  eyeball spawners instead (each eye throws it, grown out from that eyeball's middle, same no-drift /
  fast-expand / no-fading rules). Phase 1 keeps the cry from the flank eye.
- The animation session is redrawing the eyeballs smaller to pass the style checker; the sheet layout
  (7 frames, 0-1 emerge, 2-5 hover, 6 flash) stays, the frame size will be confirmed in a reply.

## Eyeballs redrawn (animation session)
Installed: same file, same layout (7 frames of 32x32, art centred). The eyeball is now 18 px across (19-20 in
the flash), NES palette, passes tools/enemy_style.py -- about 36 px on screen; its touch radius ~16 px.

## Animation session (2026-11-06): consistent flank eye, phase 2 faces forward
- The flank eye is now ONE drawn eye stamped at one spot a view (same on every idle frame). The table in
  `Paoxiao::EYE_IDLE` was updated by the animation session to: down (38.0,26.5); right/left/up (27.5,27.0).
- Phase 2: `move_facing()` = FACE_DOWN (always forward); its alt sheet is the front view with no flank eye.
  The body's phase-2 single eye shot still uses eye() (by player angle) though no eye is drawn on the body in
  phase 2 -- waiting on the user (asked whether that shot should go).

## Animation session (2026-11-06): squinting eyes, rump cleaned
The user: "have the eyeballs be the squinting shape instead of a full circle" + clean the side view's rump.
Spawner eyeballs are now squinting almonds (18x10 art px, ~36x20 on screen; same 7x32x32 layout) -- the
animation session set EYEBALL_R to 12. The flank eye stamp is an almond too (same spots).
