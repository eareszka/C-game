# Bullet task: Mice That Eat Iron (65) -- a shot on every bite

From the user (2026-11-06), via the animation session: "for mice that eats iron every bite taken in the
animation shoots a fast gray/steel colored ricochetting or regular bullet in players direction".

## What exists now (animation just installed, approved pending)
- Class `MiceThatEatIron` in `src/enemies.cpp` (subclass of the `Unfinished` placeholder; `case 65`).
  It still fires the placeholder 2-shot volley every 0.9 s, and flashes its alt sheet (all three heads up)
  for 0.26 s on each volley.
- Sheet `assets/enemies/redraws/65_mice_that_eat_iron.png`, entry in `ENEMY_SHEETS` (`src/battle.cpp`):
  4 idle frames at 260 ms (STEP_MS), front only, 28x23 frame drawn 2x about the enemy's (x, y).
  - frame 0: all three at rest
  - frame 1: LEFT mouse bites (head dipped onto the beam)
  - frame 2: MIDDLE mouse bites
  - frame 3: RIGHT mouse bites
  Built by `art/enemies/anim/65_mice_that_eat_iron/build.py` -- don't change the art; ask the animation
  session if you need a frame changed.
- Mouths, roughly, in frame px (0,0 = top-left of the 28x23 frame): left (5, 14), middle (14, 12),
  right (22, 13). Screen = enemy x + (fx + 0.5 - 14) * 2, enemy y + (fy + 0.5 - 11.5) * 2.

## The task
- On idle frames 1, 2 and 3 (each bite), one fast steel-grey bullet leaves that mouse's mouth toward the
  player. Use `on_idle_frame(frame, ...)` (as Moskitto does) so the shot lands on the frame shown.
  The user said "ricochetting or regular": your call per volley/phase, following the battle pattern
  rules (2+ distinct patterns; bullet types for difficulty; LOW tier, 300 HP).
- Steel/grey colour for these bullets.
- Drop the placeholder `fire()` volley. The heads-up alt flash was tied to it: remove the alt flash too
  (the bite poses are now the attack), or reuse it for a bigger second-phase volley if you add one.
- Build with `make`; preview with `game.exe --battle 65` (put `C:\msys64\mingw64\bin` first on PATH).
  The user approves in the battle.

Standing note from the user: all bullet/pattern tasks go to this session; the animation session only
does poses and timing.

## Added by the user (2026-11-06): movement
"this enemys moves very slowly left or right while chewing not in a straight line tho"
- It drifts very slowly left or right across the arena the whole time it chews -- a meandering path
  (wobbling up and down, easing, changing pace or turning back), never a straight line.
- The animation needs no change for it: the gnaw cycle keeps playing while it drifts, front view only
  (`move_facing` stays FACE_DOWN).

## Added by the user (2026-11-06): phase 2
"for phase two it will remain stationary for a second chewing really fast shooting a spray of bullets off"
- Phase 2: every so often it STOPS its drift for about a second and chews really fast, spraying bullets
  off the beam while it does; then drifts on.
- The fast chew (animation side, agreed with the animation session): during that second return 2.0 from
  `anim_speed()` (enemy.h: "How fast its idle animation runs") so the same 4 gnaw poses step at 130 ms
  instead of 260 -- the user asked for it fast, so this is a deliberate exception to the 260 ms rule.
  Don't speed up any other time. The bites still land on frames 1-3 (`on_idle_frame` runs at that speed
  too), so you can hang the spray on them or run it on its own clock -- your call.

## Added (2026-11-06): walking feet -- animation done, needs one hook from you
The user: "if moving have the mice feet walking". The animation session made it and pointed the sheet's
alt at it: `65_mice_that_eat_iron_walk.png` is the same 4 gnaw frames with the feet stepping, laid out
like the idle, so the bites stay on frames 1-3 while it walks.
- In `MiceThatEatIron`, make `alt_pose()` return true while it is drifting/moving, false while it stands
  (the phase-2 fast-chew second). That replaces the old heads-up volley flash: remove that
  (`atk_t` and the alt in `fire`).
- The heads-up pose is still on disk as `65_mice_that_eat_iron_up_unused.png` if you ever want it.

## Added by the user (2026-11-06): one speed
"should move the same speed for this entire fight. mice that eat iron never slows down"
- The drift keeps ONE pace the whole fight (both phases): no easing, no slow-downs, no random stops.
  It can still turn back and wander up and down (not a straight line), just never changes speed.
- The only stop is the phase-2 fast-chew second, as before (the user asked for that one).
- Animation: the walking-feet alt shows while it moves, so it will simply always walk except in the frenzy.
