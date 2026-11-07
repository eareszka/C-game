# Movement task: Questing Beast (9) -- gallop over the whole screen

From the user (2026-11-06), via the animation session: "have the galloping be the whole screen not just the
top area".
- Phase 1 now gallops side to side along one line at the top (`QuestingBeast::update`, x 120..520 at
  y 140, 220 px/s). Make its runs cover the WHOLE arena -- up and down as well as across -- while keeping
  the hoofprint barrage working (prints left along its track, each flying at the player after its wait).
  Keep it fair (contact? it has none now -- your call) within the battle pattern rules (MEDIUM, 560 HP).
- Animation is done and already handles any direction: keep `four_views()`; set `move_facing()` to
  `facing_toward4(vx, vy)` of its run (it is FACE_RIGHT/LEFT now, from `dir`), and keep advancing `run`
  while it gallops so `flap_phase()` (130 ms a pose) keeps stepping. Phase 2 (trot home, stand, spots)
  stays as it is.
Preview `game.exe --battle 9` (`C:\msys64\mingw64\bin` first on PATH); the user approves there.

## From the user (2026-11-06): switch the phases; a slow walk that throws spots
"switch phase 1 and 2, during phase 2 when it walks slow it shoots phase 1 volleys instead of trail"
Read as:
- NEW PHASE 1 = the old phase 2: it goes to the middle, stands, and throws its coat's spots (the
  leopard-print volleys).
- NEW PHASE 2 = the galloping over the whole screen, leaving the hoofprint trail. Some runs it WALKS
  SLOWLY instead; while walking slowly it throws the spot volleys (the new phase 1's) and leaves NO
  hoofprint trail. Galloping runs keep the trail.
Animation hooks (the animation session is adding a walk cycle to the same flap sheet):
- `09_questing_beast_gallop.png` will have 8 frames a direction: 0-3 the gallop, 4-7 the walk.
  `flap_phase()` returns (frame + 0.5) / 8:
    galloping: frame = (int)(run / 0.13f) % 4          (130 ms a pose)
    walking:   frame = 4 + (int)(run / 0.26f) % 4      (260 ms a pose)
    standing:  -1 (idle; the braced-shake alt pose a step per spot volley -- also while walking? no:
               walking, keep the walk; only standing throws flash the alt)
- `move_facing()`: `facing_toward4` of its way while galloping or walking; -1 standing.

## From the user (2026-11-06): dashes go at the player
"when dashing it should go towards player and be on all 4's"
- Its gallops/dashes in phase 2 run TOWARD THE PLAYER (aimed at them, not random lines). The animation
  session is redrawing the gallop frames (sheet frames 0-3) as a low dash on all four legs; no hook change.

## From the user (2026-11-06): the walk's line is clusters
"when walking the line of bullets are the clusters instead of single"
Read as: while it WALKS (the slow runs), the line of bullets it leaves/throws is made of the coat-spot
CLUSTERS (the 5-bullet spots/rosettes) instead of single bullets. If what's there now doesn't map onto
that cleanly, keep the user's words as the rule: walk = a line of clusters; dash = as it is.

## CORRECTION from the user (2026-11-06) -- replaces the section above
"my mistake. the clusters are the only bullet type in both phases, when walking they spray out, when
sprinting the line is of clusters"
- The coat-spot CLUSTERS (5-bullet spots / rosettes) are its ONLY bullet, in both phases. No single bullets.
- Phase 1 (standing): the cluster volleys, as now.
- Phase 2 WALKING: clusters SPRAY OUT from it (the spread volleys).
- Phase 2 SPRINTING (the dash at the player): the line it leaves along its track (the old hoofprint
  trail) is made of CLUSTERS instead of single bullets.

## From the user (2026-11-06): homing clusters from the run
"the clusters in the 2nd half from running should be homing similar to snawfus"
- In phase 2, the clusters it leaves while RUNNING (the sprint's line of clusters) home in on the player,
  like Snawfus's petals did (homing for a while, then flying straight -- see `mkh` in Snawfus's old
  petals). Keep each cluster's shape as it homes if you can. The animation session is making the
  walk/sprint more chaotic -- art only, no hook change.

## From the user (2026-11-06): the walk's spray all the way round
"during 2nd phase the spraying clusters should be in a full 360 around the enemy instead of just towards
the player" -- phase 2's walking spray of clusters goes out in a full circle, not an arc at the player.

## From the user (2026-11-06): a burst at every stop / change of pace
"everytime the enemy stops running/changes speed this burst shoots out as well" -- in phase 2, every time it
STOPS running or CHANGES SPEED (sprint -> walk, walk -> sprint, a run ending), the full-360 cluster burst
fires too.
