# Thirty new NPCs for review

These are additional NPCs based on the existing player and four approved
villagers, not replacements for them. No town placements or game code are
changed by this art pack. Sources: `assets/player_small.png`, the four
`art/npcs/*_walk_3frame.aseprite` files, `art/direction/ART_DIRECTION.md`,
`art/direction/OVERWORLD_STYLE.md`, and `game_palette.gpl`.

Each numbered character has:

- A native `.aseprite` file with twelve 14x20 cels and four directional tags.
- A transparent 42x80 PNG sheet: down, up, left, right as rows; standing,
  step A, step B as columns. Side views include both player stride poses.
- JSON containing frame rectangles, palette, identity, foot origin (7,19),
  and explicit playback sequences.

All pixel painting uses the installed Aseprite pixel MCP. These are flat
four-color sprites with black outlines; hairstyles, hats, facial hair,
glasses, and clothing patterns define the people. Each retains the player's
body masks, hands, foot placement, and head bob. Design layouts are checked
to prevent palette swaps being counted as different people.

## Animation

Walking uses the player's exact cadence: step A, standing, step B, standing,
200 milliseconds per beat (800 milliseconds per cycle). Stopping selects
standing. PNG sheets keep standing in column 0. JSON `playback` specifies
zero-based atlas indices for the four beats in every direction.

The native Aseprite files store **step A, standing, step B** in each
direction and use **pingpong** tags, producing that same four-beat loop
directly in Aseprite. Native standing indices are 1,4,7,10 (zero-based).
The JSON `native_aseprite` block records this distinction explicitly.

## Review

`cast30_labeled_overview.png` identifies all thirty people. The three
`cast30_pageN_review.aseprite` documents each show ten people in a four-beat
animation. Read each page as two groups of five columns: down, up, left,
right vertically for each group. Pages cover IDs 05-14, 15-24, and 25-34.
Matching animated GIFs are enlarged 3x with nearest-neighbor pixels.

`manifest.json` records the full cast, validations, and protected source
hashes. Validation reopens all saved character cels and checks exact pixels,
dimensions, alpha, palette membership, four-color limit, connected
silhouettes, baseline, distinct poses, native tag playback and timing.
Review-page cels are independently checked against their individual sheets.

Reproduction scripts live one directory above: `cast30_design.py` and
`cast30_finalize.py`. The design script preserves existing numbered output
files. Do not rerun the finalizer over reviewed or hand-edited files; it
is the one-time finishing pass from generated frame order to native
pingpong playback.
