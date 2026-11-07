# Bullet task: Rumptifusel (60) -- bullets coloured like its spores

From the user (2026-11-06), via the animation session: "have the bullet colors be like the spores on the enemy".
- Its belly's spores (the light crosses on the purple, art/enemies/nes/60_rumptifusel/sprite.png) are
  (182, 156, 238) -- already an exact game-palette entry (Qique uses it), bright on the black arena.
  The belly round them is (102, 75, 149).
- Change `ENEMY_BULLET_RGB` in src/enemies.cpp, the `{ 60, 148, 112, 61 }` row (fur brown, line ~10459), to
  the spore lavender (182, 156, 238), comment "its belly's spores". If any of its bullets are drawn with their
  own colour elsewhere (sheets, suck ring), make them match too.
Build and open game.exe --battle 60 for the user.

## Refined by the user (2026-11-06)
"the large clusters should be the dark purple, and the other shots should be the light purple and poisonous"
- The large CLUSTERS -- the pore SHEETS (the 24-shot hex lattices from `sheet()`): the dark purple of its belly,
  (102, 75, 149) -- or the nearest exact game-palette entry to it that still stands off the black arena.
- Every OTHER shot (the spray of 7, the phase-2 suck ring): the light spore purple (182, 156, 238), and
  POISONOUS (`BulletSpawn::poison = true` -- see `poisoned()` in src/enemies.cpp).
- Per-shot colour: if bullets can't carry their own colour yet, add a per-spawn colour override (BulletSpawn)
  that the draw uses instead of `enemy_bullet_color` -- keep it general, other enemies will want it.
- Battle pattern rule from memory: poison is a minority threat ("one or two poison sources a pattern, never a
  screen") -- here the spray + ring are the poison and the sheets aren't; flag if that's too much poison.
