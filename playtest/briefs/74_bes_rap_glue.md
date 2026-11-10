# Bes Rap (74): glue spit + droppings on the player

From the user (2026-11-09): "the stuff it shoots out is a new type of bullets that take 1 damage and make it so you cant
move/move extreamly slowly, like a stunning glue/gel like bullet. this plays well with this fight because the x's that
spawn into blobs should spawn where the players current position is"

The user's answers:
- **Glue = the spit cone only.** The droppings and the phase-2 figs/seeds stay normal.
- **Glue effect:** each hit does 1 damage (not the usual 5) and sets a player glue timer of 1.5 s; another hit restarts
  it. While glued the player moves at ~15% speed and can't dash.
  - Make it readable: the bullet is a gel/glue colour, and the player shows a visible glued tint or drip while it lasts.
  - Build this as a general bullet flag (e.g. `BulletSpawn::glue`) so other enemies can use it later.
- **Droppings:** in each wave the first X goes exactly on the player's current (px, py), clamped into the arena. The
  rest keep their 60-150 px scatter around the player.

## Mouth origin (settled -- placeholder art)
PixelLab is out of credits, so Bes Rap keeps its current 37x43 front-only still: no 4-view redraw, no `four_views()`,
no `facing_toward4`. In `breathe()`, replace the old 98x65 per-facing table with ONE mouth point for every facing:
the middle of its teeth row, art px (17.5, 13.5), drawn 2x = screen offset (-1, -15) -> `mx = x - 1.0f, my = y - 15.0f`.

Then `make game.exe` and launch `game.exe --battle 74` (mingw64 first on PATH).

## From the user (2026-11-09): phase 2 lunges
"during phase 2 it lunges at players potion spits and does the x thing in a ring around the player"

Phase 2 (half HP): Bes Rap stops sitting still and repeats this cycle:
1. **Lunge.** It lunges at the player's position, taken when the lunge starts, so the player can dodge it. It's a quick dash that stops at that spot.
2. **Spit.** It lands and spits the glue cone at the player from its mouth. Use the same mouth offset, (x-1, y-15).
3. **Droppings ring.** At the same time, the X marks go down in a ring around the player. Use a ring at a set radius (your call, around 60-80 px) rather than the random scatter, plus the one X right on the player as before. They land as droppings after HINT_T as usual.
4. **Pause.** A short pause, then the next lunge.

Notes:
- It must never leave the screen.
- Its body hurts to touch, including during the lunge.
- It's a phase-2 movement, so it's exempt from the movement rule (free_movement), like other user-asked dashes.
- Keep the figs if they still fit; drop them if the screen gets too busy.
- Rebuild and open `--battle 74`.

## Note on the glue as built
battle.cpp has `PSPEED = 0` while glued, plus a re-glue lockout (`_glue_cd`). The user picked "crawl ~1.5 s":
- move at about 15% speed while glued, not 0;
- no dash while glued;
- each new glue hit restarts the 1.5 s.

Please match that. If you think the lockout is needed to stop the player being glued forever, keep it but say so in your report.
