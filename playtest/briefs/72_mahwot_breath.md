# Pattern task: Mahwot (72) -- one laser, then an opening

From the user (2026-11-06), via the animation session, after Mahwot's new animation:
"the speed at which it moved before was better, make sure lasers come from the mouth, always fires just 1 laser
toward the player, cooldown after laser fire for player to hit damage"
1. ONE laser, always, at the player -- in both phases (drop phase 2's second, led beam and `pair`).
2. A COOLDOWN after the breath: once the laser has faded it stays reared/still a moment before it runs again --
   an opening for the player to hit it (your call how long; make it a clear window).
3. Its travel speed should be as it was before today (340 / 420 px/s along its lane). Please check the shared
   movement rule you added today isn't slowing Mahwot -- if it is, exempt it (like the other runners).
   (The animation session put its swim cycle back to its old 105 ms pace.)
4. Lasers from the mouth: the animation session re-measured the mouth (25.7, 1.7 px from its middle facing
   right, mirrored left -- already in Mahwot::update) and now holds ONE roar pose through the breath, so the
   mouth stays on the beam. If you keep it reared during the cooldown, keep `alt_pose()` true for that too.
Build and open game.exe --battle 72 for the user when done.

## Added by the user (2026-11-06): a slow mouth-close after firing
"need slow animation of it closing mouth after firing before going back to swimming"
The animation session made `assets/enemies/72_mahwot_close.png` (flap sheet, 4 frames a direction, side view in
every column like the rest): wide jaws -> half -> nearly shut -> resting, closing. Please:
- wire it: in `src/battle.cpp` set Mahwot's ENEMY_SHEETS `flap` (the 5th field) to "assets/enemies/72_mahwot_close.png"
  (the entry is { "assets/enemies/72_mahwot.png", {}, 4, false, nullptr, "...roar.png", ... } -- the nullptr).
- during the COOLDOWN after the laser (your new opening), return `flap_phase()` = cooldown progress 0..1 (it picks
  the 4 frames in order, slowly: make the cooldown at least ~1 s so each pose holds 260 ms or more), facing the
  roar's side (`roar_facing`); `alt_pose()` false then (flap draws over alt anyway). Then it swims again.

## From the user (2026-11-06): start closing sooner
"closing should start slightly sooner, when laser dissipates" -- begin the mouth-close (the close sheet) as the
laser starts to FADE (its dissipating stage), not after it is gone; the close then runs on through the cooldown.

## From the user (2026-11-06): close a little faster
"closing should be a little faster" -- shorten the mouth-close a little (e.g. ~25% quicker); it still starts as the
laser dissipates. The cooldown opening can stay as long as it is -- once closed it can hold the resting pose
until it swims.
