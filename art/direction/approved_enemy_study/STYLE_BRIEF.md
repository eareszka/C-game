# Approved enemy style study for PixelLab

This is a derived reference pack, not a change to either Art Bible.
Approval comes from `art/enemies/redraw_status.json`: 36 DONE enemies,
four canonical REF enemies, and two explicitly accepted OK enemies, 42 total.
Unapproved drafts and unfinished enemies are excluded.

The study reads the sheets currently loaded by `src/battle.cpp`, respecting
their frame counts and horizontal or per-direction row layouts. It covers
65 enemy sheets, 3,320 stored direction/animation cels, and three attached
parts/log/marks assets. Every sampled view is extracted at native resolution.
All analyzed sheets have binary alpha and zero off-palette opaque pixels.
Source-file hashes are recorded and verified unchanged in `analysis.json`.

## Source of truth

- `art/direction/ART_DIRECTION.md` and `game_palette.gpl`.
- `C:/Users/emery/.herdr/worktrees/C-game/sprites/art/direction/SPRITE_STYLE.md`.
- Canonical style anchors: 00 Skvader, 01 Wolpertinger, 03 Qique, 08 Snawfus.
- Other approved enemies provide scale, anatomy and material examples;
  their individual exceptions do not replace the Bible's general rules.

## Shared drawing rules to include in each generation request

Draw one coherent flat 2D pixel silhouette, composed for its viewing angle.
Use deliberate single-pixel edges and chunky interior clusters, with shared
separation lines between overlapping parts. Avoid stacked cutout pieces,
rendered 3D forms, tubes, soft edges, and antialiasing.

The standard outline is one pixel of black. Use flat fills and one dark/mid/light
ramp per material. Place light by form on viewer/up-facing surfaces, dark
under overhangs and on far surfaces. Never shade by horizontal bands or
smooth gradients. No dithering, hatching, scale lattices, fur noise or
repeated skin textures. Species details belong in the silhouette and a few
outline strokes.

Use the project's exact palette. Standard sprites permit eight colors plus
black; the giant tier permits a larger palette under its separate Bible
budget. Keep accents restrained. The canonical front views use 5, 7, 9 and
8 opaque colors, including black. The accepted medium front views have a
median of six colors, big front views eight; these are observations, not
new limits.

Maintain chibi anatomy, a substantial readable head, rounded body masses,
and tapered limbs. Eyes are tiny marks: no elaborate irises, glints or
rendered eyeballs. Preserve the individual enemy's native dimensions,
proportions, padding, baseline, pose, view and recognizable silhouette.

The canonical front views devote approximately 9.35%-14.49% of their opaque
pixels to interior black separation lines. Their outer-edge black coverage
varies because of deliberately open thin parts and accent tips; do not
mistake this measurement for a rule to thicken every outline.

## Model inputs and limits of the workflow

`approved_style_native.png` contains the front, three-quarter and right-side
first views of all 42 approved enemies, packed without rescaling their pixels.
It is a style reference, not a request to generate a roster or a collage.
`analysis.json` maps every packed view back to its source enemy and sheet.
`approved_42_labeled_overview.png` is the labeled human review image.

The installed CLI has no separate command that reads an Art Bible and
certifies style compliance. PixelLab receives visual style images and the
Bible's drawing constraints in its generation prompt. The reference pack
should accompany future enemy requests. Local review and validation remain
required after generation; receiving a reference is not proof of compliance.

## Current task: 97 RO

The current first-frame reference is
`art/enemies/97_ro_frame0_draft.png`, 130x81 pixels, occupied bounds
(5,2)-(126,81) in exclusive-coordinate notation. Preserve its upright
front-facing roar, broad bat-wing spread, large head/mane, stubby legs,
right-curving tail and grounded baseline. Keep the original sheet and
previous draft intact, and save a separate PixelLab revision.

The user's explicit exception is **black skin**: RO is the game's only black
enemy. Since 2026-10-18 it keeps the black outline like everything else; the
hide is a charcoal ramp and red is only an accent (eyes, mouth, wing veins).
The earlier red outlines were dropped for readability on dark backdrops.
This exception applies to RO only; all other Bible constraints
still apply. Do not recolor the reference roster or modify the Art Bible.

RO was generated through PixelLab CLI after explicit per-call approval. The
initial reference board was rejected by the API because it exceeded 512 pixels;
that rejected submission did not reduce the account balance. The corrected
`approved_42_fronts_native_512.png` packs all 42 approved front views at native
pixel size, with no resampling, and was sent with the RO source and Bible prompt.
The successful request reported 10 generations, verified by a balance change
from 40 to 30. The generated draft was palette-cleaned through the pixel plugin,
validated, and opened in Aseprite. This is model input, not an independent remote
certification of Bible compliance. New paid requests still require approval.
