# Overworld style

The rules everything drawn on the overworld follows: its ground, the things
standing on it and the buildings, whatever projection each is drawn in. They
are not chosen: they are measured from the pieces the user is happy with, and
anything else is held to them. `tools/overworld_style.py` holds the measurable
half -- the materials, the list of pieces and the checker. Read this before
touching `art/structures/entrances/`, `art/structures/houses/`,
`art/structures/coast/`, `art/structures/trees/`, `art/cliffs/` or the overworld's cells of
`assets/tileset.png`.

The rules of `ART_DIRECTION.md` still hold underneath: one palette, four
colours a 16px cell. Interiors have their own bible, `INTERIOR_STYLE.md`;
where the two meet, this one says so.

![every piece and what it breaks](overworld_board.png)

## The reference

(The user, 2026-10-12.)

- **Ground**: the grass, meadow, snow and sand cells and the water cell. (The sand cells
  were redrawn 2026-10-27 to the wasteland's sparse clods in sand, at the user's word:
  "have the ground speckle pattern be the same for the desert"; `art/ground/sand_design.py`.)
- **Objects**: the two ordinary trees, `art/structures/trees/`.
- **Built**: the seven town houses, `art/structures/houses/`, and the stone
  entrances -- ruins, mausoleum, stonehenge, church.

When a rule here is unclear, the answer is whatever these do. The cliffs are
not reference: they are held to the rest.

## Three kinds

Every piece is one of three kinds, and a kind has its own rules.

- **Ground** lies flat and is walked on: a biome's cells, water, lava, a trail.
- **An object** is one thing standing on the ground, drawn as a sprite: a
  tree, a sign, the player.
- **Built** is a thing made of a material laid in units, or of rock: a house,
  an entrance, a wall, a cliff.

Built pieces follow the interiors' way of drawing a material, objects the
enemy sprites' way of drawing a creature (the user, 2026-10-12), so a brick
outside is a brick inside and a tree is drawn as a Skvader is.

## Across projections

The overworld mixes three views. The texture is what stays the same.

- **Ground is seen from straight above.** No near edge, no far edge.
- **Buildings are oblique**: the front face square on, depth going up and to
  the right at 45 degrees. A point x across, d back and z up lands at
  (x + d, base - z - d) (`entrance_shapes.oblique`, measured off the houses).
  Something lying flat on the ground -- the stonehenge's opening -- is drawn
  as ground is.
- **A cliff is its top from above and its south face square on**; its west and
  east faces are thin and its back is a line.
- **One texture pixel is one screen pixel.** Nothing is scaled, sheared or
  resampled to fit a plane.
- **Three planes, three steps.** The top is the material's lightest tone,
  flat. The front carries the texture. The side turned away (the east) is
  flat and a step darker than the front reads: stone's darkest grey, a house's
  brick without its mortar.
- **Light from the upper left**, as everywhere else in the game.
- **What stands is walked behind.** A piece overflows north of its footprint,
  and each of its pixels is drawn over the player when its ground line is
  nearer the viewer than the feet.

## Materials

A material is named once, in `MATERIALS`, and a piece names the ones it is
made of. The same material is the same colours wherever it appears, outside
and in.

Shared with the interiors (`interior_style.MATERIALS`, lit to dark):

| Material | Tones | Joint |
|---|---|---|
| stone | `c6ccda` `9797aa` `595965` | black |
| sandstone | `f4ce80` `b29e5c` | `785830` |
| wood | `967448` `785830` `493712` | `493712` |
| bark | `605028` `463422` `2d230c` | black |

The overworld's own, from the reference:

| Material | Tones |
|---|---|
| grass | `4edc4a`, tufts `00881b` |
| meadow | `a8f0bc`, flowers `fc74b4`, stems `00a800` |
| snow | `fcfcfc`, tufts `f0bc3c` |
| sand | `f0e880`, clods `d0c078` (the dunes' `e8e0c0` gone from the ground, 2026-10-27) |
| water | `5c94fc`, foam `fcfcfc` |
| foliage | `05c43a` `058f3a` `235436` |
| glass | `5c94fc` `b70000` |
| a house's brick | its own brick, shade and mortar; its roof one tone (`PAL` in its `*_design.py`) |

A house is in its own brick, and its room inside is in the same.

The coastal town's, which is painted wood, not a material laid in units:

| Material | Tones |
|---|---|
| white paint | `fcfcfc` `c6ccda` `9797aa` |
| red paint | `b70000` `7c0a1b` |
| green, navy, black paint | `235436`, `2850a0`, `34343e` |
| slate (roofs, ironwork) | `595965` `474751` |
| lantern glass, lamplight | `5c94fc`, `fae488` |

A coastal house's chimney is the interiors' brick.

The rest -- wasteland, lava, the town's pads, the sign, the player, the dead
tree -- are not in the reference, so each has its own tones in the table
until it is brought into line.

**A road is the town's street carried out into the country** (the user,
2026-10-13: "we need a new approach to overworld trails. they dont match the
current artstyle and they dont connect to town trails well", then, of a first
version 8 px wider than the street: "it needs to be thin enough to transition
seemlessly"). It has no cells on the sheet. The game draws it
(`draw_track` in `src/tilemap.cpp`) as the street's own band -- two tones,
24 px deep across: three rows of edge, twenty of paving, one of edge --
winding with the route and rounded at every bend, and it runs into a street's
end with no join to see. So it keeps the ground rule without art: a flat fill,
no speckle, no black. A wasteland trail is the same band.

**A track is in the trail tones of the ground it lies on** (the user,
2026-10-13: "trail colors need to match the biome they belong to"). Each
ground names its two, paving and edge (`GroundBiome::track` in
`src/tilemap.cpp`, cited here as materials); a road, a trail and a town's
street are all the same band in them. Grass's are the start town's street,
read off the sheet; the coastal town stands on meadow, so its streets are in
meadow's. Where a track crosses from one ground to the next it changes tone
with the grounds' own stippled fringe, pixel for pixel ("smooth trail
transitions between biomes similar to how biome transitions currently are"),
so there is no straight line across it anywhere.

| Ground | Trail paving, edge |
|---|---|
| grass (`town pad`) | `d7a175` `8d6b4f` |
| meadow | `b2966a` `967448` |
| sand | `cebe82` `b29e5c` |
| wasteland | `2b190e` `110000` |
| snow | `c6ccda` `a4aaba` |

**The desert's formations were retired** (2026-10-27): the strip of ten
(saguaros, boulders, a spire, a shrub, bones) gave way to the desert props
(`art/structures/props/desert/`), placed and broken in their themed groups.

**A village is its ground's building set** (the user, 2026-10-13: "the
buildings in the village and the architecture and 'vibe' must match the
biome the village is in"). Five sets, `art/structures/villages/`, each three
houses and a well in the houses' projection and parts (`tools/house_shapes.py`),
every wall a material laid in units: grass, timber frames in bark with
plaster panels in white paint under thatch (`c9a433`, eave shade `876a1f`),
a brick chimney; meadow, a farm (the user, 2026-10-13: "meadow towns should
be like farms", with "different house colors since the current approach
looks like the lake town"): clapboard in yellow paint (`fae488`, `f0bc3c`)
with white trim, the farmhouse under red paint and the cottage under green,
a shed in red paint under slate, and a barn after the user's reference
(2026-10-14): red boards, its gable end to the front, white corner boards
and trim, X-braced double doors under a four-pane hayloft window, a gambrel
roof running back in wood's `785830` lined black, its side in the red's
shade under the eave as every house's is; sand, round houses (the
user, 2026-10-14: "oblique projected but circular with the dome on top") in
the pyramid's sandstone courses (`pyramid_tone`), the side turned away in
its shade, under a dome on the rim -- the rim is an ellipse, so the dome
shares the wall's cells and is the wall's own brick, a beehive -- and no
windows (the user: "remove them"); snow, logs of wood, each lit along its top
and dark beneath, under snow lying on the roof (white paint), a stone
chimney; wasteland, ruined stone (the user: a "barracks settlement from Yume
Nikki"): dark stone in the brick's courses weathered as the entrances are,
under slate sheets, with a stovepipe of rust (`764c20`, `3e1c0e`). The wells
are the landmark well itself -- the round drum (the user, 2026-10-14: "make
sure wells are all round") -- in the set's stone, snow on its lit edges in
snow.
Thatch, rust and yellow paint are named here for the first time.

**The wasteland is overhauled after the user's Yume Nikki references**
(2026-10-27; the mock-ups and their reasoning are `art/concept/wasteland/`).
Stage 1 is the ground, the void, the volcanoes and the causeways; the
hamlets, mazes, a lone-gate landmark and the rubble come in a second stage.

- **Ground.** A flat red-brown, `3e1c0e`, with a rare clod of dirt's `583518`
  and no cracks (the cracked earth of 2026-10-14 is gone; the maroon tried in
  the mock-ups "read purple"). Broad blocks of a lighter `583518`, laid a tile
  at a time, were tried and taken out the same day (the user: "get rid of the
  light brown 'tan' streaks/blobs"). `art/ground/wasteland_design.py`, sheet
  cols 27-29 rows 4-5, written by `gen_entrance_art.py --grounds`. The track
  is a dark worn `2b190e` edged in the near-black `110000`, no longer tan.
- **Island rock.** An island with no ore cave, in every biome, is ash taupe:
  `b2966a` `8d6b4f` `583518` (the user, 2026-10-27: the Mother 1 cliffs'
  olive "to match the reference more without it being confused with other
  ores"), greyer and duller than bronze's orange, apart from every other ore.
  `DEFAULT` in `art/structures/gen_cave_entrances.py` -> `src/ore_tones.inc`.
  The desert's boulders and spire keep the old cliff rock, and so does the
  oasis's rock (`tools/oasis_blocks.py`).
- **The void** is the wasteland's liquid where lava was: TILE_LAVA, the same
  id with a new look. `2c0c47` with the water cell's whole marks in `301b5a`
  and `3b2a58` (`art/ground/void_design.py`, sheet (15,0)), and a 1px `110000`
  rim on the land side as water's shallows are. It comes only as pools (the
  user: "lava should be pools"), one to three of the ponds' radius-2 brushes,
  about one to every 600 tiles of wasteland; the citadel's moat ring stays.
  A natural river or pond running through the wasteland is void too (the
  user: "natural rivers ... in the wasteland should be the purple color"),
  turning back to water where it leaves, the two liquids meeting along the
  edge field. The change is a cut straight across the river, bank to bank,
  never down its middle (the user: "it should go from one side to the
  other"): the river is cut into slabs across its channel, and each slab goes
  whole, by its tiles' vote and its neighbours' along the river. Roads bridge a void river outside the citadel's ring, on a
  causeway. A raft floats on the void while the lava charm is held (the user:
  "both should be crossed by raft"), so the ring waits on the charm.
- **Mini volcanoes** stand where the dead trees did (the user: "red stands
  should be like mini volcanos", "larger/denser"): props of the wasteland's
  own, theme TH_VOLCANO, in four sizes in red rock (`ec8476` `b70000`
  `7c0a1b` and black), laid in dense groves (`props/wasteland/`). A waste
  village's trees are little volcanoes.
- **Causeways.** A bridge over the void is the bridges' deck in waste stone
  (`9797aa` `595965` `34343e`): `tools/stone_deck.py` copies the deck's row
  of the sheet into the row below in stone, and the game draws that row for a
  deck in the wasteland (`stone_deck_at`).

Stage 2 (the same day): the built stone, the hamlets, the mazes, the gate and
the rubble.

- **Waste stone.** Everything built in the wasteland is a step darker than
  stone elsewhere, `9797aa` `595965` `34343e`, sitting in the gloom as the
  references' blocks do. The barracks huts and their well are recoloured in
  `villages/waste.png` itself (they stand nowhere else), under slate in the
  void's `3b2a58`. The stone yard walls and the ruins stand in other biomes
  too, so `tools/waste_stone.py` copies their cells, recoloured, to empty rows
  (194-200, from col 24), and the game draws the copy for a cell standing in
  the wasteland (`art_src`, `WASTE_COPIES` in `src/tilemap.cpp`).
- **The hamlet's compound.** A waste village stands in one row (never a back
  row) inside a wall of the stone yard walls: a parallelogram in the houses'
  projection round the row and its street (`lay_yard`), broken wherever a
  street or road runs and wherever anything already stands.
- **The ruin maze.** The wasteland's ruins stand at the heart of a maze of
  broken walls (`stamp_dungeon_surround`): runs across and back at 45 degrees,
  the only ways the yard walls join, the doorway's columns open in front,
  dead ends to either side. The walls break like rocks.
- **The lone gate** is the wasteland's landmark, where the burnt wagon stood:
  a doorway of waste stone standing alone, the ground seen through it, its
  chest before it (`landmarks/gate_design.py`, sheet 18,176).
- **Rubble** lies round the void: a second prop theme of the wasteland,
  TH_RUBBLE, chosen for a group within 7 tiles of a pool -- grey rocks in
  waste stone's base and dark with a crack and no lit tone (the bible's rock),
  a fallen stub of wall in its courses, a bone (`props/wasteland/rubble_design.py`).

**A town's ground is a biome**: its open ground, and what lies under its
woods, its buildings and its streets. The starting town is grass; the coastal
town is meadow (the user, 2026-10-13: "town 1's grass is meadow"), and its
footprint fringes against the country round it as any two grounds do.

**Rock that holds ore is in its ore's ramp** (`gen_cave_entrances.py`
`TONES`): a cave's mouth, and a cliff with a cave in it. Stone's ramp there is
`bcbeca` `848694` `474751`, a second grey beside built stone's; a cliff with
no cave takes `b29e5c` `887000` `493712`.

## Ground

- **A ground is its fill.** One flat colour over at least 85% of it (the
  water's 85.9%; grass, snow and sand 91%, meadow 95%).
- **What is laid on it is whole and few**: a tuft, a flower, a dune's rim,
  foam. One or two colours a ground besides its fill.
- **Grains are sparse.** Lone pixels are at most 3% of it (the sand's 2.9%).
- **No outline.** Black is only the dots under a tuft, at most 1.2% (grass
  and snow 1.1%).
- **A biome is its own cells, never a tint** of another's. Where two meet, the
  edge is cut in the neighbour's fill colour.

## Built

A wall is laid in courses, 4 px high: a brick or a stone block 6 px long
(`house_shapes.BRICK_W`, `entrance_shapes.courses`), offset by half a unit
from the course above.

- **A brick** (the houses): its base tone, its shade along its bottom row and
  right edge, pale mortar atop each course and between the bricks. The base is
  the lightest tone of the brick and most of it (42% to 69% of the brick's
  pixels across the seven).
- **A stone block** (the entrances): its top row lit, the rest its base, the
  bed and head joints in the stone's dark tone. This is the one place the
  overworld parts from the interiors, where nothing is lighter than the base:
  at 6 x 4 a block is too small for base, shade and joint, so outside it takes
  a lit row instead (the user, 2026-10-12, over the same wall without the row
  and with the interiors' block).
- **A round pillar** is lit down its left edge and in shade down its right,
  with a ring of shade where its drums meet.
- **A clapboard wall** (the coastal town) is the brick's courses without the
  bricks: each board 4 px high in white paint, the shadow under it along its
  bottom row, no joints. Its side face is the shadow tone, flat. Shutters,
  casing and panes are one paint a house; a painted round tower has no
  lighter stripe, only its paint, shade down its right and a deeper edge.
- **A house's roof** is one tone in rows of shingles, black between them.
- **Rock** (the cliffs) has no units and follows the interiors' rule whole:
  a base that is its lightest tone and most of it, a shade, black cracks. No
  lit tone, no dither. The cliffs are painted so, from the very rows the
  oasis cave's rock is (the user, 2026-10-13: "have cliff islands use the same
  rock textures used in oasis caves so it fits the games artstyle more"):
  every stone one flat tone, the mountain's base or its shade
  (`art/cliffs/gen_cliff_texture.py` packs the drawing that way; the lit tone
  of a mountain's ramp is not used on its rock).
- **No noise.** Lone pixels are at most 1.4% of a piece (the church's 1.36%;
  the houses' are under 0.3%).

## Objects

- **A 1-px black outline round the whole silhouette**, and between its parts.
- **Three colours and black** (the trees: three greens).
- **One ramp, placed by form**: the mid tone is most of its colour, the dark is massed
  low and on the right, the light is sparse and high on the left (2% to 3% of
  a tree).
- **Flat fills.** No hatching, no lattice, no dither between tones.

## Lines

Black, 1 px. Round the whole of a built piece or an object: every reference
piece's silhouette edge is black all the way round. Where a nearer part
stands in front of a farther one, on the far one's side. Faces of one block
meet without a line; they differ by tone. Ground has none.

## What is not the style

- A colour typed into a design script that is not in `MATERIALS`.
- The same material in two sets of colours: bark browner outside than in, a
  palm's leaves in another green than a tree's.
- A lit tone or dither in rock.
- A ground speckled all over, or outlined.
- An object without its outline, or in more than three colours.
- A texture stretched or sheared to fit a slanted face.
- A side face lighter than the front it turns from.

## Props

The scenery each biome is laid with, every one of them breakable. The table is
`art/structures/props/props.py`, one row a prop: its biome, the groups it comes
in, its cells, how it stands, what breaks it, what it drops. It is the only place
any of that is written. `gen_entrance_art.py --tables --props` packs every prop
into the sheet's rows 226-245 and writes `src/props.inc`; then
`tools/palette_pass.py --write`. The checker reads every prop from the same table.

- **Standing.** A prop is entrance art, laid whole. A column's lowest pixel is its
  ground line, so the player is drawn behind it above that line. Its feet meet
  the prop on the bottom few rows of each column (`stand` in pixels), on all of
  it if the prop is low (a log), or not at all if it lies flat (tufts, skulls,
  pebbles). A column whose lowest pixel stands well above the prop's own is open
  beneath, as the arch is.
- **Groups, never mixed.** Worldgen ("Props", `lay_props`) lays them as small
  groups of one theme each, about every 30-40 tiles:
  - desert: cactus stand, rock country, old trail
  - forest: deadfall, woodcutter's camp, undergrowth
  - plains (the meadow ground): farmstead, Mayan ruins
  - snow: ice field, abandoned expedition camp, mammoth graveyard

  The theme's anchor stands at a group's middle, with 2-7 fillers thrown round it
  a tile apart, thinning toward the edge. A group holds at most two of a small
  thing and one of a bigger one. A neutral few stray alone between the groups.
- **The two plains countries.** Ruins ring every step pyramid, 12-60 tiles out,
  in the woods as on the meadow. Elsewhere a ruin field stands only where a slow
  noise runs high. Farms keep 70 tiles from a pyramid and 50 from any ruin
  group, so hay and statues never stand together.
- **Breaking.** A prop takes each blow at its block's top left, and it shakes
  whole. A blade crossing several of its cells deals one blow. When it breaks,
  every cell goes and stays gone (`persist.h`), and it pays its drops through
  `item_slot`. `make propcheck` proves this on one prop of each kind of blow.

## How to check

```
python tools/overworld_style.py                   # every piece
python tools/overworld_style.py grass ruins       # some
python tools/overworld_style.py --measure         # the figures the thresholds are set from
python tools/overworld_style.py --board art/direction/overworld_board.png
```

One row a piece, a count per rule, non-zero exit on any failure:

| Rule | Kinds | Fails when |
|---|---|---|
| `pal` | all | a colour is off `game_palette.gpl` |
| `col` | all | a 16px cell holds more than four colours |
| `ramp` | all | a colour belongs to none of the piece's materials |
| `speck` | ground, built | lone pixels of a tone are over 3% of a ground, 1.4% of a built piece |
| `lit` | built | a tiling texture's lightest tone is under 30% of its material: a highlight |
| `flat` | ground | its fill covers under 85% of it |
| `line` | ground | over 1.2% of it is black |
| `out` | object, built | under 99% of its silhouette's edge is black |
| `tones` | object | it has more than three colours besides black |

The first five are `interior_style.check()`, read against the piece's own
materials.

A pass is necessary, not sufficient. The checker cannot see a unit's size,
where its lit row or its shade sits, which tone a plane takes, the projection,
or whether an object is shaded by form. Those are read off the board. Where a
piece has a source drawing it reads that, not the copy stamped into the sheet,
and it reads the cliffs' rock as the game paints it (the packed texture, in
the plain ramp rather than each island's own). A new
piece is checked once it is added to `PIECES`.

## Not covered

Effects (steam, a weapon's swing). The menu's icons and a craftable placed in
the world have their own bible, `ITEM_STYLE.md`. What has no art yet
and still draws as a placeholder -- flower and oilbloom nodes -- is drawn
to this bible when it is drawn.

## Rulings

The reference is the ground cells, the water, the two trees, the seven houses
and the four stone entrances; the cliffs are held to them (the user,
2026-10-12).

Built pieces and rock take the interiors' rule and its materials; living
things and small objects take the enemy sprites' (the user, 2026-10-12).

Stonework outside keeps the lit top row on each block (the user, 2026-10-12).
See "Built".

No piece was changed when this was written. What fails is brought into line
one piece at a time, an image before each install.

The large tree is in the bark of its inside, the plate tone over most of each
limb and its shade down the right (the user, 2026-10-12, over the same tones
with the old shading, and over keeping its paler brown as a material of its
own). Its limbs are placed by hand: four, heavy and bent, a short branch or
two each, spread apart. The tree grown from a seed, forking down to a thicket
of black twigs, was thrown out though it passed every rule ("too clustered up
top and doesnt match the games pixel art"; of two drafts, four bent limbs over
five fanned). A shape is drawn, few parts and bold, not generated: the checker
cannot see this.

The coastal town (town 1, on the ocean) is New England seaport building:
"new england coastal architecture similar to a historic fishing and seaport
town. with a lighthouse and wooden nantucket style houses" (the user,
2026-10-12). Its houses are white clapboard with dark shutters, over grey and
over cedar shingle; its lighthouse the tall white tower with a red band, over
a short harbour light and a tower with a keeper's house, and a landmark, not
a way in. The shop's sign reads STORE. There is a town centre: a town hall, a
bandstand and a green's things ("need more building variety/ maybe like a
town center/park"). All of it lies on the sheet at rows 180-190 for the user
to edit by hand; the sheet is the drawing, and the design files are how it
was first laid out.

The town is laid out (`tools/town1_layout.py`, then by hand in the tile
editor): the green in the middle with the town hall behind it, streets out
from it in the start town's road pieces. Its waterfront is not fixed in
place: "their is a road going towards the water. once over the water it turns
into boardwalk like the one used in graveyards. on this boardwalk is the
lighthouse and finishing huts", and "make sure the boardwalk goes toward the
direction of the world border that is water" (the user, 2026-10-12). The
planks are the graveyard dungeon's own boardwalk, and the deck is drawn as
the dungeon draws it: "the pier needs to be oblique projected shape" (the
user, 2026-10-12, of a first deck laid square to the tiles). Its sides run up
and to the right at 45 degrees as the houses' depth does, a black line round
the floor, the planks' face under every edge -- lit where it looks south,
shaded where it looks east -- and the posts under that, standing in the sea.
To a north or south sea the road goes back at 45 degrees, which in this
projection is straight away from the viewer, and the wharf carries on along
the same line; the wharf is one long deck, the lighthouse at its seaward tip
(over a platform, and over a spur for the lighthouse).

**A bridge is a boardwalk** (the user, 2026-10-13: "bridges should be like
boardwalks. completely straight and using the oblique projection. the
transition between trail and bridge should be seemless as well"). It is the
wharf's deck, baked by the same script (`tools/town1_layout.py`
`bridge_across`, `bridge_back`) into the same cells, a piece for every length
of gap, and laid by the game (`lay_bridge` in `src/tilemap.cpp`). Over water
or lava alike. One crossing east or west lies level, its ends slanted; one
crossing north or south runs back at 45 degrees, up and to the right, as the
north and south wharves do. Its floor is the track's own band -- 24 px, on
the band's pixels -- so a track runs into it edge to edge. The posts stand in
the gap only; a slanted deck's side face runs the whole way down to its lower
corner (the user, 2026-10-13, of one that stopped at the bank's line). The
feet cross on the floor's own pixels.

**A trail comes to a bridge in line with it** (the user, 2026-10-13: "when a
trail goes towards a bridge it must be the classic oblique projection style
for a decent ammount of distance before joining with the bridge to make the
transition not jnarring"; asked, they chose a slanted track in line and 6
tiles). Six tiles of straight track on each bank (`BRIDGE_RUN`): level for a
level bridge, and for a slanted one the band itself drawn slanted -- 24 px
across, a pixel over for every row, three of edge on the far side and one on
the near, the going-back street's make -- so trail and deck are one straight
line and the bend into the winding trail is well away from the bridge. Where
a place could not be reached with that much room, 2 tiles.

**Landmarks** (the user, 2026-10-13: "we need something so whereever the
player goes its fun and something new"): small places laid across the
country, one kind to a ground, each with one cache that is struck open once
and stays open. The place keeps its own kind's rules (the old well is built:
stone in the entrances' courses and projection, its windlass in wood's mid
tone). Every cache, a landmark's and a dungeon's alike, is one drawing, the
chest (the user, 2026-10-14: "one sprite that more detailed and a flag is set
once opened"): an object in wood's base and shade with iron (stone's base)
for its bands, corner plates and lock strap, one black line round it, drawn
shut and open (its lid thrown back, the inside dark). Drawn through the
plugin from `art/structures/landmarks/<name>_design.py` (shared parts in
`landmark_shapes.py`; the chest `chest_design.py`), laid at cells of its own
on the sheet (`gen_entrance_art.py` `LANDMARKS`, `CHEST`, `--landmarks`), and
listed in `PIECES`; a landmark's export leaves its cache's cell empty for
the chest. The six places (2026-10-14): grass, the old well; forest, a
woodshed of the snow villages' logs under bark, its open front stacked with
log ends, and a ring of stones round a cold fire; sand, a stone head sunk to
its lip (a flat bottom line is the sand closing over it); snow, a cairn of
stones in base and shade with snow on what nothing sits on; wasteland, a cart
burnt to its frame in the dead trees' bark; shore (sand or grass within five
tiles of sea, river or pond), a rowing boat with planks stove in. Each cell
keeps four colours; where a shed's lit log tops would make a fifth under the
roof, they go first.

The yard fence is in the interiors' wood, its shape as it was: two posts a
cell, two rails (the user, 2026-10-12, over a stouter post a cell). Its tops
take the lightest tone, its fronts the next, its sides the darkest.

Trails take the tones of their ground, and change tone across a ground's
edge with the same stipple the grounds do; the coastal town's ground is
meadow, so its streets are in meadow's trail tones (the user, 2026-10-13).
See "Materials". The four trail tones that are not grass's began as the
user's earlier per-ground trail cells (since replaced by the drawn band) and
are held to the image: a crossing shows two grounds and two bands, six
colours in a cell, which is more than a sheet cell may hold; if that reads
busy, the edge tone is shared between the two grounds.

The desert is scattered with its formations (the user, 2026-10-13: "we need
many natural forming things in the desert since its pretty barren"; see
"Materials"). Worldgen's "Desert formations" lays them on bare sand after the
entrances and before the roads, in stands -- cactus country and rock country,
each a slow noise of its own -- with bones anywhere: about a tile in ten
inside a stand and under one in fifty outside (the constants at the top of
that pass). Never on a cliff, a trail, a bank, the oasis pond or the
pyramid's court, and never two to a tile. The ten drawings were shown at 6x
on sand beside the player before the install; which stay is the user's.

The sprite board of 2026-10-13 -- every placeable thing but the houses, the
cliffs and the roads -- brought these rulings (the user). Every dungeon
entrance stays but the oasis and the cave. **The cave mouth is the interior's
arch** ("have the cave entrance match the interior cave entrance ... the rim
entrance"): the round-topped opening with its two-pixel rim cut in the
cave's cobble, a ring of that cobble round it and the mountain's painted rock
beyond (`cave_entrance_design.py`). **The oasis is redrawn whole**: new
palms; the way in stays the cave's ladder hole and the pool is a circle
("the oasis ladder should still be the default ladder sprite but the oasis
water should be circular and correct"). **The green's furniture is built**
("bench needs to be oblique projection, street lamp needs to be taller,
fountain needs to be bigger"): the bench in the houses' projection, the lamp
a cell taller, the fountain three cells wide. **The palm and the dead tree
are redrawn with new shapes** to the trees' rule, three colours and black --
so the palm's trunk is black with the dark green along its lit side, as the
forest trees' trunks are, and the dead tree is in bark. The saguaro updated,
the prickly pear larger, two large boulders for three small. **The desert's
bones are its enemies'** ("the skull and bones should match random enemies
sprites using the bible"): the Grootslang's skull, and one coil of the
Olgoi-Khorkhoi's spine rising from the sand as the living worm's does; bone
is three tones now, the roster's bone white over the catacombs' two.

Villages are laid afresh for every seed, unlike the towns (the user,
2026-10-13: "every layout of the villages are procgenerated for every seed
unlike towns"; asked, they chose rural sets a biome, doors into the start
town's rooms, a small hamlet, scenery only this round). A village is its
ground's own ground made through its footprint, the towns' oblique street
cells across it (the user, 2026-10-13: "villages should use the oblique
projection road system for towns") in the ground's trail tones, flat to the
gate's edge and capped at the other end, running on out of its gate to the
road network, its ground's set of houses along the street's north side
facing it, a well at the middle, a sign inside the gate, a fence at each end
of the row where the set has wood, the ground's own trees on what is left,
and now and then a second row behind a back street joined at the gate's far
end (`stamp_village`). A farm always has its back row, and the barn stands
first in it; its front row begins with the farmhouse; south of the street
two fields side by side with a lane between, rows of earth with sprouts --
ground, laid in the base as the streets are, never overlay art, or the
fence takes the field for a building in its line and picks the wrong
pieces -- each fenced as the graveyard's yard is (the user, 2026-10-14: "the oblique
projection fence similar to the picture" -- `lay_yard`, one parallelogram
for both), its two-tile gate opening on the street where the graveyard's
opens south. The wasteland's huts stand shoulder to shoulder. Nothing else of the country is laid inside a footprint, and no dungeon entrance's surround reaches into one (the user, 2026-10-14: a catacombs' yard walled across a hamlet). Each door
opens one of the start town's rooms, and the way out is the door walked in
by.

**The things to mine are objects in rock's ore ramp** (the user, 2026-10-15,
over two veins and a cave crystal: "vein B, have cave rocks be the same shape
but instead of gold vein its whatever material the cave offers").
`art/structures/nodes/nodes_design.py`, two cells: the stone rock -- a broken
boulder in stone's ore ramp, its top lit, a crack down its front -- and the
vein, the same rock one flat grey cut by black cracks with nuggets of ore in
it, lit and base. On the overworld the rock is `TILE_ROCK` and the vein, in
gold (kharvite's tones, the gold icon's), `TILE_GOLD_ORE`, at sheet cells
30-31 row 176 (`gen_entrance_art.py` `NODES`, `--landmarks`). In a cave the
node is the vein with the cave's own ore in it (`tools/gen_cave_tiles.py`
`lay_node`, cell 4 of row 0 of each ore's block); a stone cave's is the
plain rock, stone in stone being no vein. The hand-painted crystal is gone.
A vein twinkles (the user, 2026-10-15: "the specs or veins should twinkle
similar to the parallax background used in cave systems"): one nugget at a
time flares into a cross of its lit tone, as the cave's glints do, a step
every 0.7 s, plain and then each of three nuggets, every vein on a clock of
its own (`vein_frame`); the stone rock is still. A node is stood as the
desert's things are -- solid on its bottom three rows, walked behind above
them -- and shakes when struck, as everything farmable does.

**A tuft of dry grass is drawn as the ground draws a tuft** (the user,
2026-10-26, over the same tufts outlined as objects, where the line round
blades a pixel wide was most of the drawing): the desert's grass
(`art/structures/props/desert/grass_design.py`) is the villages' thatch, two
tones, blades a pixel wide fanned by hand, no line round it, black dots in the
sand under its root as under the grass cells' tufts. It is walked over. The
checker reads it as an object and counts its `out`; that one is expected.
