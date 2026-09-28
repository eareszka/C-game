# Art direction

The game draws on one palette, `game_palette.gpl`: the colours it drew at
commit `3a4b41d`, before the FC World recolour (`830f1e1`, since undone),
with near-duplicates merged so that sprites meaning the same colour use one.
It is mostly the NES palette Mother 1 uses (mint meadow `#a8f0bc`, sky water
`#5c94fc`, `#fcfcfc` snow, `#00a800`, `#887000` rock, `#fc74b4` flowers),
plus the wasteland's dark browns and the cave and trail ramps. 102 colours.

![the original game on the left, the game now on the right](fc_compare.png)

Left: the game as it first looked. Right: the same seeds and places, rendered
by the current build (`build_compare.py`).

## Two rules

1. **One palette.** Every colour drawn, art and UI alike, is one of
   `game_palette.gpl`.
2. **Four colours a tile.** No 16px cell holds more than four colours: the
   NES's own limit.

No effect blends, because a blend makes colours no palette has. Where the game
washes or dims, it dithers instead: a Bayer pattern picks which pixels take a
palette colour, so every pixel is still exactly one of the palette.

| Effect | How |
|---|---|
| Plateau storeys | a quarter of the pixels per storey in the biome's tint: 25%, 50%, 75%. Grass toward mint, meadow and sand toward white, snow toward a cool blue, waste toward ash |
| Cave rock out of view | 11 of every 16 pixels black |
| Water's shore | a pale blue rim, `#dcf0ff` |

## Keeping sprites consistent

A colour that is off the palette goes where `fcremap.py` sends it:

- **Merged near-duplicates** go to the colour they merged into, the more-used
  of the pair: two nearly identical wasteland browns, water's `#ffffff` foam
  and the snow's `#fcfcfc`, and so on.
- **Leftover FC World colours** go to the old colour playing the same part:
  foliage greens to the old trees' greens, grounds back to their grounds.
- Anything else goes to its nearest palette colour (CIELAB).

Sprites that mean the same thing share exact colours. Every tree, the ASCII
ones in the build script and the plugin-drawn ones in `trees/`, uses the same
three greens: `#235436`, `#058f3a` and `#05c43a`. The houses use the colours
they had originally. The stone house has white brick `#fcfcfc`, grey mortar
and side `#9797aa`, and a brown roof and door `#94703d`. The white house has
white siding, grey trim and a dark roof `#282828`.

## How it is applied

`tools/palette_pass.py --write` puts the sheet and the player sprite on the
palette and enforces four colours a tile. **Run it last**, after any
`tools/gen_*.py` or anything else that paints into the sheet. It is idempotent.
It leaves alone the tint masks, which must stay pure white, and the
generators' hand-painted masters, which are never drawn. It also writes
`src/fc_palette_lut.inc` from the palette.

The code's own colours go through the same table. `fc_draw_color()` and
`fc_snap()` (`include/fc_palette.h`) replace `SDL_SetRenderDrawColor`, so a
colour typed into the source lands where the art's colours land.

To check a frame: `python tools/palette_check.py some.png`. Renders from
`shot.exe` and `dngshot.exe` report 0 pixels off the palette.

The few translucent draws (weapon swing trails, the door prompt box, debug
grids) have their colour on the palette but still alpha-blend.

## Unused art

`tools/prune_sheet.py` blanked 59 cells nothing draws. `make sheetcensus`
compiles the game's own drawing code with every `SDL_RenderCopy` reporting its
source cell, then draws whole worlds, every dungeon type in every material, and
every interior. The prune list is chosen by hand. The census can veto it but
not extend it, because it cannot see art that is drawn but not wired in yet,
like the pyramid in the sheet's bottom-right corner.

## Painting new art

Draw through the pixel plugin (the Aseprite MCP tools). Open
`fc_palette.aseprite` or load `game_palette.gpl` as the palette, and paint four
colours to a tile. Then run `tools/palette_pass.py` to confirm the tiles pass.

## Trees and buildings

`art/structures/build_fc_structures.py` builds the trees and houses and stamps
them into `assets/tileset.png` (`--stamp`). Ordinary ground has two tree kinds,
both two tiles tall, drawn through the plugin with sources in
`art/structures/trees/`. One is the three-lobe column, and the other is the
stacked-clumps tree. The renderer picks between them half and half
(`tree_col()` in `src/tilemap.cpp`). Snow has two conifers. The houses keep
every line and their exact footprint, so town collision and the door cells are
untouched.

## Files

| File | What it is |
|---|---|
| `game_palette.gpl` | The palette. Edit this to change it |
| `fcremap.py` | Reads the palette; where off-palette colours go |
| `fc_palette.aseprite` | The palette as swatches, built through the plugin |
| `fc_compare.aseprite` / `.png` | Before and after, built through the plugin |
| `before/` | The original game's three views, frozen |
| `fc_world_reference.png` | FC World's tileset, the reference for the trees |
| `build_compare.py`, `mcpc.py` | Rebuild the board: `make shot`, then `python art/direction/build_compare.py` |
| `tools/palette_pass.py` | Puts the art on the palette; writes the game's lookup table |
| `tools/palette_check.py` | Is a rendered frame on the palette? |
| `tools/prune_sheet.py`, `make sheetcensus` | Which cells are drawn; blank the ones chosen to go |
