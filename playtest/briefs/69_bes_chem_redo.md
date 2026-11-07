# Pattern task: Bes Chem (69) redo

From the user (2026-11-06), via the animation session:
"we will redo this enemy. its first phase is its 2nd phase but it should fly to a new spot after each
'burst'. for the first phase it burst and flaps". Confirmed by the user:
- Phase 1: perched in place, BURSTS (the chest-mouth rings, "e... e... e...") and flaps its wings.
- Phase 2: its current phase-1 pattern (the bursts, the falling poison feathers), but after EACH burst
  it FLIES to a new spot, lands, and bursts again.
- The "pok... pok..." orbs are DROPPED (the user).
Bullet details beyond that are yours, within the battle pattern rules (LOW tier, 380 HP).

## Animation (done; class `BesChem` in src/enemies.cpp needs the hooks)
Sheets installed, `ENEMY_SHEETS` entry in src/battle.cpp already points at them (45x39 frame, front view
only -- keep `move_facing()` returning FACE_DOWN; built by art/enemies/anim/69_bes_chem/build.py):
- idle `69_bes_chem.png`, 5 frames at 260 ms: mouth shut, WIDE OPEN (frame 1 = `breath_frame`, the burst
  leaves on it via `breathe()`), opening, rest, clenched -- with the wings beating over it. This is phase 1.
- alt `69_bes_chem_perch.png`: the same 5 mouth frames, wings still. Make `alt_pose()` true while it is
  PERCHED IN PHASE 2 (landed between flights), so the burst still comes on frame 1 there.
- flap `69_bes_chem_fly.png`, 4 frames: wings down, out, up, out. Return a `flap_phase()` while it flies:
  a pose per 260 ms step, e.g. `fmodf(fly_t / 1.04f, 1.0f)`. Start the flight's clock at 0 so it leaves on
  the wings-down pose and lands on whichever comes up.
- The bursts leave from the chest mouth at the frame's middle: (x, y) -- already in `breathe()`.
Preview with `game.exe --battle 69` (put `C:\msys64\mingw64\bin` first on PATH); the user approves there.

## Added (2026-11-06): legs tucked in flight
The user: "when flying legs should be shaking or tucked whichever signals that its flying better". The flight
sheet `69_bes_chem_fly.png` now has the legs tucked (re-installed by the animation session). No code change needed.
