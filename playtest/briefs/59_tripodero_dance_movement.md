# Movement task: Tripodero (59) -- phase-2 movement must match its dance

From the user (2026-11-06), via the animation session: "its actual movement needs to match the way its
sprite moves during phase 2".

The dance sheet (assets/enemies/redraws/59_tripodero_dance.png, made by art/enemies/anim/59_tripodero/build.py;
4 poses, one per STEP_T = 0.26 s, Tripodero::flap_phase) -- in the FRONT view, which the dance now always uses
(the animation session set move_facing() = FACE_DOWN while DANCING):
  frame 0  standing on its RIGHT stilt, the LEFT stilt swung out to the screen's left, foot about knee height
  frame 1  PLANTED: both stilts down, wide apart (an A stance), jolted a pixel down -- the foot has landed
  frame 2  the mirror: on its left stilt, the RIGHT stilt swung out to the screen's right
  frame 3  PLANTED again, wide
What the code does now (Tripodero::update, DANCING): during frames 0 and 2 the whole body glides 120 px
sideways (home+60 -> home-60, and back) and rises 18 px in an arc, then holds still on 1 and 3 -- so it slides
across the floor on one leg and bobs up, which the art doesn't show.
Make the movement follow the art: on a step (frame 0 / 2) the body stays on its standing leg (no glide, no
arc); when the foot PLANTS (the start of frame 1 / 3) the body shifts toward the planted foot -- a stride's
worth, about the swung foot's reach (~25-30 px on screen; measure from the frames if you like), in one or two
quick NES steps, not a smooth slide -- so it walks across by stepping. Keep the slug + ring on each plant, the
drift round the top of the arena (via the strides), and fairness. Then build and open game.exe --battle 59.
