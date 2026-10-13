# Interior style

The rules every interior texture follows: the dungeons' walls and floors and
the house rooms, whatever projection they are drawn in. They are not chosen:
they are measured from the two interiors the user is happy with, and anything
else is held to them. `tools/interior_style.py` holds the measurable half --
the materials, the shared textures and the checker. Read this before touching
`art/structures/dungeon_walls/`, `art/structures/interiors/` or
`tools/interior_room.py`.

The rules of `ART_DIRECTION.md` still hold underneath: one palette, four
colours a 16px cell.

## The reference

**The graveyard and the stonehenge barrow** (the user, 2026-10-12):
`graveyard_design.py` and `barrow_design.py`. When a rule here is unclear, the
answer is whatever these two do. Both draw through `tools/interior_style.py`,
so the rules and the reference cannot drift apart.

This is about textures only. A type's layout, its projection and what it is
built of are its own.

## Across projections

The dungeons are top-down, oblique, isometric, terraced and side-on. The
texture is what stays the same.

- **One texture pixel is one screen pixel.** A texture is never scaled or
  stretched to fit a plane. A plane reads its swatch by where it is in the
  world, so a path or a wall runs on seamless.
- **The isometric floor shows every other row.** Its 2:1 view reads the swatch
  a row in two, so anything 1 px wide can vanish or break up there: a floor's
  shade is 2 px, and it carries no chips (a 3-2-1 corner comes out as a comb).
- **Courses follow their own plane.** Level on a wall seen square on; stepping
  with the edge on a 45-degree or 2:1 wall.
- **Three planes, three steps of the material.** The top takes the base tone.
  The face toward the viewer takes the base and its shade. The side turned
  away (the east) takes the next tones down: the graveyard brick's east face is
  `792727` / `5d1e1f` where its south face is `b6433d` / `792727`; the barrow's
  side is its stone's darkest grey, flat.
- **A floor in its walls' own stone sits a step down**, so the two read apart:
  the catacombs' flags are `9797aa` / `595965` under walls of `c6ccda` /
  `9797aa` (the user, 2026-10-12, over a floor as pale as the walls).
- **Light from the upper left**, as everywhere else in the game.

## Shapes from whole pieces

**A shape is built from whole pieces on the grid, never by bending a texture
to it** (the user, 2026-10-12: "use sprites to make the cave feel more organic
instead of bending flat already existing walls", "each one should be 16x16
and flow organically"). Two tries at the caves were thrown out for this: the
old rock face hung along a smoothed curve, its cobbles sheared on the slopes;
then 8 px columns of heights picked by a rule.

What works, and is how the caves are laid: edges that are level or at 45
degrees and meet the 16 px grid at a cell's corners or its middle. Each of a
cell's four quarters (the triangles its diagonals cut) is then wholly rock or
not, and one 16 x 16 piece serves each way they can fall: a level top, a
rising or falling top or foot, a floor's pointed tip, a valley, a vault, a
peak, a fang. The flutes of the rock stay upright on every slope. A missing
piece shows as a black wedge where two edges meet; `dngshot` counts cells no
piece fits, and the count is 0.

## Materials

A material is named once, in `MATERIALS`, and every design script takes its
colours from there. The same material is the same colours and the same size in
every interior it appears in.

| Material | Lit to dark | Joint |
|---|---|---|
| brick | `b6433d` `792727` `5d1e1f` | `531b1c` |
| stone | `c6ccda` `9797aa` `595965` | black |
| wood | `967448` `785830` `493712` | `493712` |
| grass (moonlit) | `4fa667` `235436` | black |
| bone | `b2966a` `8d6b4f` | `34343e` |
| dark stone | `34343e` `292931` `1e1e24` | black |
| sandstone | `f4ce80` `b29e5c` `967448` | `785830` |
| slate | `474751` `34343e` | black |
| heartwood | `815423` `633e1b` `3c2412` `22140c` | black |
| soil | `2b190e` `22140c` | black |
| fungus | `d7a175` `b2966a` `8d6b4f` | black |
| dirt | `583518` `3c2412` | black |
| bark | `605028` `463422` `2d230c` | black |
| rock (the oasis) | `5c4616` `2d230c` | black |

The ruins' wall faces are dark stone under a rim of the pale (the user,
2026-10-12: "much darker, almost surreal darkness", over the pale stone and
over a single step down). A type's mood may pick a darker material; it does
not change how the material is drawn.

House rooms are the exception (the user, 2026-10-12: left as they are). A room
is in its own house's brick, as its outside wall is -- 10 x 4, pale mortar --
so its colours are its design's, not this table's.

A new material (sandstone, soil, bone) is added to the table when its type is
brought into line, not typed into a design script.

## A unit: base, shade, joint

A brick, a block or a plank is three things and no more:

- **The base**: the lightest tone, and most of the unit. **Nothing is lighter
  than the base** -- no lit top row, no highlighted edge. Where a material
  appears in the reference its lightest tone is never under 33% of it.
- **The shade**: along the unit's bottom and right edge, inside the joint.
  1 px on a brick or a plank, 2 px on a 32px block.
- **The joint**: 1 px, the unit's bottom row and right column. Mortared brick
  takes its own dark mortar tone; dry stone blocks take black.

Sizes sit on the 8 px grid: brick and squared block 16 x 8 (the graveyard, the
ruins, the desert pyramid), plank 8 tall, great stone block 32 x 32 (one over
two). Stones that are not squared -- the step pyramid's interlocking masonry
-- keep their shapes and take the same three parts: black joint, shade inside
it along the bottom and right, no lit edge. Bond is offset by half a unit. The one finer course is the
graveyard walkway's 8 px edge, which shows two 4 px courses.

`masonry()` lays all of these (`unit_tone()` is its rule for one pixel, for a
wall drawn as a function of where it is); `planks()` lays boards.

## Lines

Black, 1 px: round a wall's silhouette, down the corner where its front turns
to its side, along its foot. Not round every unit: the joint does that.

## Wear and detail

- **Brick** (the graveyard): a worn brick goes to the shade tone whole, about
  one in four; three in ten have a chipped corner, a black 3-2-1 (`chip()`).
  `bond()` lays this.
- **Stone** (the stonehenge): plain. No block is worn or chipped; one in three
  of its 32px blocks has a crack, one connected black line (`crack()`). Whole
  dark stones on a swatch a few blocks wide repeat as stripes down a wall.
- Small marks are black and few: a nail head, a bolt, an eye socket.
- **Grown things** (the giant tree): the same parts without units. The base
  is the lightest tone and most of the surface; what is drawn on it is darker
  and whole -- grain lines, a ring knot, a root with its black edges, a
  fungus's growth bands, a hollow trodden in the dirt. Nothing is scattered:
  no flecks, clods, pores or pebbles.
- **No noise.** No dither, speckle, dot lattice or hash scatter inside a
  texture. A tone never stands as a lone pixel (the reference's worst swatch
  has 0.6%, the ragged clod under the brick).
- Things laid on a texture -- grass tufts, roots, carvings -- are laid whole,
  never sliced by an edge.

## Drawn decoration

Murals, glyphs, stained glass, constellations, ghosts and the like are
drawings, not textures. The texture rules do not apply to them; `TYPES` in
`tools/interior_style.py` lists which views of each design are texture.

## What is not the style

- A lit top row or a lit edge on a block.
- The same material at two sizes, or in two sets of colours.
- A colour typed into a design script that is not in `MATERIALS`.
- Dither or speckle to suggest roughness.
- A texture stretched or sheared to fit a slanted wall.
- A side wall lighter than the wall it turns from.

## How to check

```
python tools/interior_style.py                  # every type
python tools/interior_style.py catacombs tree   # some
python tools/interior_style.py --board out.png  # the swatches side by side, verdicts under them
```

One row a swatch, a count per rule, non-zero exit on any failure:

| Rule | Fails when |
|---|---|
| `pal` | a colour is off `game_palette.gpl` |
| `col` | a 16px cell holds more than four colours |
| `speck` | lone pixels of a tone are over 0.7% of the swatch |
| `ramp` | a colour belongs to no material in `MATERIALS` |
| `lit` | a material's lightest tone is under 30% of it: a highlight |

A pass is necessary, not sufficient. The checker cannot see unit size, which
side the shade is on, or whether a plane was resampled; those are read off the
board.

Changing a type's textures never changes its layout: its swatch sizes and
piece positions stay, and its `dngshot` map dump is the same before and after.

## Rulings

The cave (the user, 2026-10-12) was rebuilt rather than restyled: terraces, a
floor for every level its mountain's mouths stand on outside, laid from the
16 x 16 pieces of `cave_rock_design.py` in its ore's own tones. See "Shapes
from whole pieces" above; its crystal and gem stay as hand-painted.

Its rock is the user's own hand-drawn cobble wall (the sheet's master block,
column 28) brought to this bible's tones: base, shade, black joints, no lone
pixels ("have them look like the stone sprite i handrew on tileset but fitting
thr games pallete and sprite bible"; of two versions, "B is correct"). Three
earlier textures of Claude's own invention (flutes, stones, stripes) were
thrown out. A level run of wall faces you and is the strip as drawn; a sloped
run and the pieces on a turn are turned away, a tone down, with a black line
where the two meet ("make it obvious which is a corner tile and whats a
straight up and down tile"). About one face cell in ten carries one of the
strip's round stones as a gem in its ore's lit tone: the one thing in the rock
lighter than its base. A way out is inside what its entrance is outside: an
arch for a mouth walked into, a ladder up to a hatch for a hole in a plateau.

The catacombs' sections (the user, 2026-10-12): bone walls of whole pieces on
the dark between them -- long bones laid in courses, skulls 14 px. The old
8 px skulls were sheared to mush by the slanted walls. A skull is never
sheared and never sliced: the game lays as many as fit whole along each
straight run of a face, either side of a ladder, and stands each upright on a
slanted wall while the bone courses lean with it (`cat_bake`). Two walls, taken
in turn "so the player doesnt get confused what catacombs theyre in": odd
sections a row of skulls over three courses of long bones, even ones skulls all
the way down. Their floor is the graveyard's brick less its chips, shade 2 px;
a wall's top is the plain base.

Torches (the user, 2026-10-12): caves and ruins have them; the catacombs none
for now, the nave included. One drawing, `torch_design.py`: a bronze cup on a
wooden handle, six flame frames. Nothing in it is a wall's tone -- a first
version in each dungeon's own wall tones was thrown out ("too close to the
original hue ... should match the theme of the dungeon but not look exactly
like the stone or walls"). The flame is drawn as fire and a dungeon may show
it in a colour of its own (`cave_flame`): fire in the ruins and in stone and
bronze caves, white in emerald and veyrite, black fire in dravium and
kharvite, a rainbow in reality shard -- each flame striped in the rainbow's
six colours ("the individual flame is rainbow colored"), the stripes slanted,
2 px wide and moving along a stripe a frame ("alternating", "sideways ...
instead of purly vertical or horizontal"), and its glow striped with them
("the circle should reflect that its rainbow"), in stripes twice as wide so
the rock's texture does not chop them to specks. Kept soft ("more sutle maybe
mixxing some white"): a stripe is its hue's pale tone and the flame's heart is
white, as the white flame's is.
Round the flame a small glow on the wall, its circle growing
and shrinking with the flame's frame (10, 12, 14 px): the wall's own pixels
pulled toward the flame's colour and put back on the palette. They hang on
wall that faces you, in the middle of its height, about one in eight cells of a
straight run; never on a cave's turned rock or a gem, a cracked or holed ruins
face or the face beside one, and a cell clear of a doorway, mouth or ladder.

Floors (the user, 2026-10-12): the ruins and the two pyramids had one flat
colour and now have tiles, laid by where a tile is in the world
(`floor_tile` in `tools/gen_dungeon_wall_tiles.py`, `WALL_FLOOR` in the game).
- The ruins: 16 x 8 brick in herringbone, in dark slate (`474751` / `34343e`,
  black joints) -- over flagstones, great blocks, basket weave and three
  other colours.
- The desert pyramid: its walls' own brick, in sandstone a step down
  (`b29e5c` / `967448`, joint `785830`): "the pyramid bricks should match the
  wall textures bricks".
- The step pyramid: its walls' own interlocking stones in slate, quiet -- no
  shade, the joint one tone under the stone ("more sutle").
- **A pyramid's floor is oblique** ("pyramid and cave floors should be oblique
  projected"): its swatch is read at (x + y, y), as the graveyard's walkways
  read theirs, so courses stay level and the joints across them climb 45
  degrees. No pixel is resampled. The ruins' floor is seen from above.
- The caves: the wall's own hand-drawn cobble lying flat ("have the cave floor
  be somewhat similar to the cave wall texture"), quiet -- its stones the
  floor's colour, the lines between them a tone under it. Ten textures of
  Claude's were turned down first. Of the versions shown the user took the
  cobble as it is drawn on the wall, over the same slanted, so the cave's
  floor is not oblique after all. A colour an ore, the user's: grey, olive
  brown, green, indigo, dark red, a darker olive gold (`MATERIALS` in
  `src/dungeon.cpp`: `ground`, `ground_line`). The minimap keeps its own
  floor colours.
- Reality shard's cave is the exception: large rounded cobbles
  (`ground_cobbles` in `cave_rock_design.py`), black, their lines light
  purple, read in the oblique view ("reality shard should be oblique
  projection stone", then "the other stone texture": of four shown, the third).
  A brick floor and the wall's cobble slanted were each built first and taken
  back out.
- **Where a quiet floor meets the walls' black, a shadow** ("find a way to make
  the transitions between the pure black of the walls and the more sutle
  floors work"; of three ways, the user's pick): within 3 px of anything that
  is not floor, the floor is a tone down -- its stones the line colour, its
  lines black. Not on a black floor, which has no tone to fall to.

The oasis rock is the overworld's cliff texture with every stone one
flat tone -- its shade if it was mostly dithered dark, else its base; no
dither, no lit tone (the user, 2026-10-12). Its water keeps the reference's
dot lattice.

The giant tree keeps its knots (drawn detail) and loses its flecks,
clods, pores and pebbles (the user, 2026-10-12).
