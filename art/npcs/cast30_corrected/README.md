# Corrected 30-NPC cast

Use this version for review instead of `../cast30/`. The earlier pack is
preserved unchanged.

Side-view corrections requested by the user:

- Clear the old player-eye pixels that looked like an accidental beard.
- Place the NPC vertical eye at the approved profile height.
- Make all four glasses characters' profile lenses solid black, with no
  skin-colored center pixel. This was explicitly confirmed by the user.
- Keep intentional moustaches, stubble and full beards below the eyes.

Each NPC retains its twelve 14x20 cels, transparent 42x80 sheet, four-color
palette and four directions. Front/back cels are pixel-identical to the
original saved source files. Outside the side-face correction rectangle,
every side pixel is unchanged; alpha masks are unchanged throughout.

PNG columns are standing, step A, step B; rows down, up, left, right.
Native Aseprite tags store step A, standing, step B with pingpong playback,
matching the player's step/standing/other-step/standing loop at 200 ms per
beat. JSON documents both layouts.

`side_face_corrections.png` compares selected profiles before and after.
`cast30_corrected_page1_review.aseprite` covers IDs 05-14, page 2 IDs 15-24,
and page 3 IDs 25-34. Each page has two groups of five people; each group
shows down, up, left, right vertically. `validation.json` records the saved
pixel comparisons and original-file hashes.

The corrections were painted through the Aseprite pixel plugin by
`../cast30_fix_profiles.py`; `../cast30_design.py` contains the corrected
profile eye and glasses rules for future generation.
