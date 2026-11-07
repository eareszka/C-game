# Pattern task: Snawfus (8) redo

From the user (2026-11-06), via the animation session:
"Snawfus first phase gallops across screen either moving fast or slow, second phase volleys out massive
shots before going to next position and doing it again"
- Phase 1: it GALLOPS across the screen, each run at random either fast or slow (fire its phase-1
  bullets as you see fit while it runs -- the petals/blossoms can be reworked).
- Phase 2: it stands and volleys out MASSIVE shots, then gallops to its next position, and does it again.
Bullet design is yours within the battle pattern rules (MEDIUM tier, 520 HP; phase line 0.66 now).

## Animation hooks (the animation session is making the sheets now with PixelLab; it will wire the
## `ENEMY_SHEETS` entry in src/battle.cpp -- you add these to class `Snawfus`)
- `four_views()` -> true. While galloping, `move_facing()` = `facing_toward4(vx, vy)` (the way it runs);
  standing, -1 (it faces the player).
- `flap_phase()` while galloping: the gallop sheet's 4 poses, one per 260 ms on a FAST run and one per
  520 ms on a SLOW run: `fmodf(run_t / (fast ? 1.04f : 2.08f), 1.0f)`; -1 when standing.
- `alt_pose()` true while it volleys in phase 2 (the rearing/throw pose), at least one 260 ms step per
  volley, held through a long volley.
- Standing it plays its idle (4 poses at 260 ms). No `breath_frame` use needed.
Preview `game.exe --battle 8` (`C:\msys64\mingw64\bin` first on PATH); the user approves there.

## Correction from the user (2026-11-06)
"the volleys i meant in the 2nd phase should be the previously existing flower patterns"
- Phase 2's massive volleys = the OLD blossom attack, as it was: `bloom()` -- 40-bullet five-petal rose
  outline + 8-bullet centre, drifting at 85 toward the player while it opens, two a throw either side of
  the player (aim -0.3 and +0.3). The old code is in git: `git show HEAD:src/enemies.cpp`, class Snawfus.
- Keep the rest of phase 2 (stand, volley, gallop to the next spot, repeat). The reared alt pose stays
  as the volley pose.

## From the user (2026-11-06): phase 2 gallops always fast
"for phase 2 no gallops are slow" -- in phase 2 every run to the next spot is a FAST one (only phase 1
picks fast or slow). The animation session is redoing the gallop art and its speed in flap_phase.

## From the user (2026-11-06): longer stand in phase 2
"it stays still for a longer time during 2nd phase before taking off again" -- lengthen phase 2's stand
(the volley stop) before it gallops off to the next spot.
