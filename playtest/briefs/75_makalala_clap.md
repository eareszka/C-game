# Makalala (75): phase 1 redone around the wing clap

From the user (2026-11-09): "redo this enemeys bullets, 1st phase will be it clapping its wings together pushing the
player completely back against the wall from the angle it claps from, the clap forces a shockwave of bullets as well"

## Phase 1 (planted, it doesn't move)
Replace the spiral and the scream rings with the clap.

**The clap.** On its scream frame (idle frame 2: wings flung out, the breath frame), it claps its wings together.
- **Gust:** the clap shoves the player straight away from Makalala, along the line from its body to the player, all the
  way until they hit the arena wall. It's a strong, fast push (a knockback slide, not a teleport). The player can't
  fight it while it lasts, and it stops at the wall.
  - This is a new player effect. Build it generally (e.g. a push vector and timer in BattleScene, driven by an enemy
    hook or a bullet flag) so other enemies can use it.
  - Make it readable: a short telegraph before the clap so it's fair, and gust lines or dust on the player while
    they're pushed.
- **Shockwave:** at the same moment the clap sends out a shockwave of bullets.
  - It's a wave front travelling the same way as the gust, so the player gets pinned against the wall with bullets
    coming at them: e.g. a wide arc or a dense ring biased toward the player.
  - It needs gaps to slip through once the push ends.
  - Your design, but beak-yellow, matching its colours.
- **Pace:** claps every couple of seconds. Light filler between them is optional; the clap is the pattern.

## Phase 2
Phase 2 is the lasers and the ring of 20, unchanged (the user only asked about phase 1).

## Origin
Fire from the body centre, where the wings meet. The placeholder art is still in use (PixelLab is out), so there's no
new mouth or wing point.

Then `make game.exe` and open `game.exe --battle 75` (mingw64 first on PATH).

## From the user (2026-11-09): the push follows its facing, and it can't be avoided
"push back is innevatable it will be decided by how the sprite is facing"

- **Unavoidable:** every clap pushes the player, wherever they are on screen. Nothing dodges it, not distance, not a
  dash, not i-frames.
- **Direction is set by how Makalala faces, not by the line to the player:**
  - Use its 4 views: down, right, up, left.
  - When the clap's telegraph starts, it turns to the view nearest the player (`facing_toward4`) and locks it.
  - The clap pushes the player straight along that direction to the wall, so facing down pushes them to the bottom
    wall and facing right to the right wall.
  - The player slides straight, keeping their other coordinate.
- The telegraph should show that direction clearly, e.g. an arrow or gust lines across the arena the way the push
  will go.
- The shockwave travels the same way: a wall of bullets moving in the facing direction, with gaps.
- Its art is a placeholder front-only still for now (PixelLab is out), so only the telegraph shows the direction.
  Still give it `four_views()` and the facing logic, so the art drops in when it's drawn.

## From the user (2026-11-09): no line
"no line for the flap": drop the telegraph line (and any arrow or gust lines across the arena) before the clap. Show
no warning graphic for the push. The clap itself and the gust on the player while being pushed are fine.
