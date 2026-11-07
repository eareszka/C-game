# Pattern + movement task: Trollgadda (70) redo

From the user (2026-11-06), via the animation session: "it simply swims around near the top shaking its tree
more and more aggressively as its hp depletes releasing more and more". Asked about its other attacks:
"Leaves only" -- REMOVE the bell rings (breathe) and the roof-tile scale fans.
- Movement: it swims around near the TOP of the arena (no longer still) -- a wandering swim, your design;
  keep the whole sprite on screen (its frame is 52x40, drawn 2x).
- Fire: only the leaves from its tree, released MORE AND MORE as its HP drops -- rate (and spread/speed if you
  like) ramping continuously with damage taken, from a light shedding at full HP to a storm near death.
  MEDIUM tier, 500 HP, battle pattern rules.
- Animation hooks (the animation session is making the sheet with PixelLab, side view only, 3 shake levels):
  `assets/enemies/70_trollgadda_shake.png` (flap sheet), 12 frames a direction:
     0-3  swimming, the tree swaying gently        (HP above 2/3)  -- 260 ms a pose
     4-7  swimming, the tree shaken hard            (2/3 .. 1/3)    -- 200 ms a pose
     8-11 thrashing, the tree whipped violently     (below 1/3)     -- 130 ms a pose
  `flap_phase()` always on: band = hp > 2/3 max ? 0 : hp > 1/3 max ? 1 : 2; frame = band * 4 + (int)(t / step) % 4;
  return (frame + 0.5f) / 12. `move_facing()`: FACE_RIGHT / FACE_LEFT by its horizontal motion (side view only,
  the left mirrored). Drop `breath_frame` (no bells).
Build and open game.exe --battle 70 for the user when done.

## Sheet READY (animation session)
`assets/enemies/70_trollgadda_shake.png` installed: 12 frames of 52x40 a direction, as above; the battle.cpp entry
already points at it (flap). The idle sheet is shake level 1 (5 frames). You add the hooks in class Trollgadda.
