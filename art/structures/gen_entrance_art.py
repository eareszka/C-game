"""The overworld art of every structure entrance, stamped into assets/tileset.png.

    python art/structures/gen_entrance_art.py          # report only
    python art/structures/gen_entrance_art.py --stamp  # write the sheet and both tables
    python art/structures/gen_entrance_art.py --tables # write the tables, leave the sheet alone
    python art/structures/gen_entrance_art.py --tables --landmarks   # and the landmarks' own cells
    python art/structures/gen_entrance_art.py --tables --villages    # and the villages' sets' own cells
    python art/structures/gen_entrance_art.py --tables --grounds     # and the grounds' blocks' own cells
    python tools/palette_pass.py --write                # always last

Each entrance is drawn through the pixel plugin into art/structures/entrances/
<name>.aseprite (from <name>_design.py) and exported beside it as <name>.png.
A block is a whole number of cells, as wide as the art and as tall as it
stands; its stamp -- the entrance's 1x1 or 2x2 footprint -- is the bottom
size+1 rows of the middle size+1 columns. Read by src/tilemap.cpp through the
table this writes (src/entrance_art.inc):

  - the stamp's cells are the way in ('E')
  - a cell with ground the art stands on is solid to a whole-tile question
    ('#'); any other cell with art on it is not ('^'); '.' has no art

Neither is what the player meets. Each design also gives two layers
(entrance_shapes.depth_layers): for every pixel the row its ground line is on,
and the ground the art stands on. Written per sheet cell to the same table,
they are the feet's collision, pixel by pixel, and what is drawn over the
player: a pixel whose ground line is nearer the viewer than the feet.

Other overworld sprites drawn the same way -- the gravestones graveyards are
scattered with -- are strips of single cells, listed in SPRITES and packed
after the blocks; their place goes to src/sheet_sprites.inc for whoever draws
them. Blocks and strips are packed left to right on shelves from ROW0, and
the band ROW0..ROW_END is this script's: it is cleared before every stamp, so
a layout that moves leaves nothing stale behind.

Building interiors are here too, a whole room a block (INTERIORS, from
interiors/<name>_design.py), with the same layers; their layout -- which sheet
cell each of the room's 20x15 cells draws, and what each cell is to the feet
-- goes to include/interiors.h.

Transparent in an export is the sheet's key colour. Caves are not here -- they
are cut into cliffs and have their own generator (gen_cave_entrances.py).
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SHEET = os.path.join(ROOT, "assets", "tileset.png")
INC = os.path.join(ROOT, "src", "entrance_art.inc")
SPRITES_INC = os.path.join(ROOT, "src", "sheet_sprites.inc")
INTERIORS_H = os.path.join(ROOT, "include", "interiors.h")
HOUSES_INC = os.path.join(ROOT, "src", "town_houses.inc")
LANDMARKS_INC = os.path.join(ROOT, "src", "landmarks.inc")
VILLAGES_INC = os.path.join(ROOT, "src", "village_houses.inc")
GPL = os.path.join(ROOT, "art", "direction", "game_palette.gpl")
CELL, KEY, MAX_COLOURS = 16, (255, 0, 0), 4
ROW0 = 20                 # rows 17-19 left for the island library to grow into
ROW_END = 60              # first row past the band this owns
SHEET_COLS = 256
sys.path.insert(0, os.path.join(ROOT, "tools"))
import overworld_style
NL = "\n"



_designs = {}


def design_of(export):
    """What the design that drew an export says (<dir>/<name>.png from
    <dir>/<name>_design.py)."""
    if export not in _designs:
        import contextlib, importlib.util, io
        name = os.path.splitext(os.path.basename(export))[0]
        path = os.path.join(HERE, os.path.dirname(export), name + "_design.py")
        spec = importlib.util.spec_from_file_location(name + "_design", path)
        mod = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            spec.loader.exec_module(mod)
            _designs[export] = mod.design()
    return _designs[export]


def layers(export):
    """The depth layers of an export, or None if its design gives none."""
    return design_of(export).get("depth")


def crop_layers(export, x, y, w, h):
    """(footy, foot, y, way): the layers over one block, footy still counted
    from the export's top, y."""
    lay = layers(export)
    if lay is None:
        return None
    return ([r[x:x + w] for r in lay["footy"][y:y + h]],
            [r[x:x + w] for r in lay["foot"][y:y + h]], y,
            [r[x:x + w] for r in lay["way"][y:y + h]])


# (DungeonEntranceType, size 0/1, biome, export, crop x, y, w, h[, roles]).
# The biome is the TileId the site read as at placement, or -1 for any: the
# game takes the entry for the entrance's own biome first, then the -1 one.
ART = [
    ("DUNGEON_ENT_RUINS", 1, "-1", "entrances/ruins.png", 0, 0, 96, 80),
    ("DUNGEON_ENT_RUINS", 0, "-1", "entrances/ruins.png", 96, 0, 48, 48),
    ("DUNGEON_ENT_GRAVEYARD_LG", 1, "-1", "entrances/mausoleum.png", 0, 0, 64, 64),
    ("DUNGEON_ENT_CATACOMBS", 1, "-1", "entrances/church.png", 0, 0, 160, 160),
    ("DUNGEON_ENT_PYRAMID", 1, "TILE_SAND", "entrances/pyramid.png", 0, 0, 160, 112),
    ("DUNGEON_ENT_PYRAMID", 1, "-1", "entrances/pyramid.png", 160, 0, 160, 112),
    ("DUNGEON_ENT_STONEHENGE", 1, "-1", "entrances/stonehenge.png", 0, 0, 192, 80),
    ("DUNGEON_ENT_LARGE_TREE", 0, "-1", "entrances/large_tree.png", 0, 0, 144, 96),
    ("DUNGEON_ENT_OASIS", 0, "-1", "entrances/oasis.png", 0, 0, 80, 32),
    ("DUNGEON_ENT_OASIS", 0, "TILE_SNOW", "entrances/oasis.png", 80, 0, 80, 32),
]

# (name, export, cells[, rows, x]) -- a strip of sprites from the export's top
# left, or from x across: cells wide and rows cells tall (one if not given).
# Those whose design gives depth layers -- the walls and the gravestones the
# player meets -- carry them, as a block does.
SPRITES = [
    ("GRAVESTONE", "entrances/gravestones.png", 6),
    ("STEAM", "entrances/steam.png", 4),
    ("OASIS_WATER", "entrances/oasis_water.png", 1),
    ("YARD_FENCE", "entrances/yard_walls.png", 16, 2, 0),
    ("YARD_WALL", "entrances/yard_walls.png", 16, 2, 256),
]
# Strips packed after everything else, so one added here moves nothing already
# on the sheet: it goes in by --tables and its own cells written (the band also
# holds the dungeon walls, gen_dungeon_wall_tiles.py, which --stamp would clear).
SPRITES_LAST = [
    ("DESERT", "entrances/desert.png", 10, 2, 0),      # the sand's formations, two cells tall each
]


# (export, sheet col, sheet row) -- art drawn at a fixed cell outside the band,
# whose id the game already uses: the town's signpost (town_0's value 6).
FIXED = [
    ("town/sign.png", 0, 0),
]

# (interior id, export) -- a room, 320x240: the game's interior screen.
INTERIORS = [
    (0, "interiors/house0.png"),
    (1, "interiors/bookshop.png"),
    (2, "interiors/house2.png"),
    (3, "interiors/house3.png"),
    (4, "interiors/house4.png"),
    (5, "interiors/house5.png"),
    (6, "interiors/house6.png"),
]

# (interior id, export, door x, door y) -- the starting town's houses
# (houses/<name>_design.py), each stood so its door's foot is on that cell of
# the town blueprint (include/towns.h town_0), the door opening that room.
# Entrance art to the game -- the feet meet it to the pixel, and what stands in
# front of the player is drawn over them -- placed by stamp_town_blueprint
# from src/town_houses.inc rather than by worldgen.
HOUSES = [
    (0, "houses/house0.png", 75, 30),
    (2, "houses/house2.png", 109, 79),
    (3, "houses/house3.png", 116, 79),
    (1, "houses/bookshop.png", 73, 87),
    (6, "houses/house6.png", 89, 87),
    (4, "houses/house4.png", 68, 96),
    (5, "houses/house5.png", 75, 96),
]

# (export, sheet col, sheet row) -- the coastal town's buildings and the things
# on its green (coast/<name>_design.py). Their art lies on the sheet below the
# band, where it is edited by hand (tools/overworld_style.py COAST), so none of
# it is stamped from here: the sheet is read for what is drawn, the design for
# its layers. Entrance art to the game as the houses are; the town's blueprint
# and its wharves say where each cell goes (tools/town1_layout.py).
COAST = [("coast/%s.png" % n, at[0], at[1]) for n, (at, _) in overworld_style.COAST.items()] + [
    ("coast/park.png", 93, 188),
]


# (name, ground, export, sheet col, sheet row) -- the country's landmarks
# (landmarks/<name>_design.py): a small place with one cache to strike open,
# laid by worldgen on its ground (src/tilemap.cpp "Landmarks"). Entrance art
# to the game as the houses are. An export is the landmark's block: its
# design says how many columns ('stamp_w') and which cell of them the cache
# stands in ('cache') -- left empty, every cache being the one CHEST -- and
# that goes to src/landmarks.inc. Each at fixed cells of its own in the band
# LANDMARK_BAND, below the entrances' and above the coastal town's rows,
# written by --landmarks and by nothing else, so one added here moves
# nothing on the sheet.
LANDMARKS = [
    ("WELL", "LM_GRASS", "landmarks/well.png", 0, 176),
    ("CAMP", "LM_FOREST", "landmarks/camp.png", 4, 176),
    ("STATUE", "LM_SAND", "landmarks/statue.png", 10, 176),
    ("CAIRN", "LM_SNOW", "landmarks/cairn.png", 14, 176),
    ("WAGON", "LM_WASTE", "landmarks/wagon.png", 18, 176),
    ("BOAT", "LM_COAST", "landmarks/boat.png", 23, 176),
]
# (export, sheet col, sheet row) -- the chest, shut and open (landmarks/
# chest_design.py): every landmark's cache and every dungeon's chest (the
# user, 2026-10-14: "one sprite ... and a flag is set once opened").
CHEST = ("landmarks/chest.png", 28, 176)
# (export, sheet col, sheet row) -- the overworld's things to mine (nodes/
# nodes_design.py): the stone rock, and beside it the gold ore vein, plain and
# its three twinkling frames; their feet and depth as the chest's.
NODES = ("nodes/nodes.png", 30, 176)
# (col0, row0, col1, row1), inclusive: the sheet's cells the landmarks own --
# cleared before they are written, so a cell one no longer draws is emptied.
LANDMARK_BAND = (0, 176, 39, 179)

# (set, export, sheet col, sheet row) -- the villages' building sets
# (villages/<set>_design.py, village_shapes.strip): three houses and a well
# in one strip, each on cells of its own, the strip's design saying where
# ('houses', 'well'). Entrance art to the game as the houses are; where each
# house's block and door are, and each well's block, goes to
# src/village_houses.inc, which worldgen lays a village from ("Villages").
# Each at fixed cells of its own, a strip a shelf, in the free rows above the
# coastal town's, written by --villages and by nothing else.
VILLAGES = [
    ("VS_GRASS",  "villages/grass.png",  0, 194),
    ("VS_MEADOW", "villages/meadow.png", 0, 200),     # seven rows: its barn
    ("VS_SAND",   "villages/sand.png",   0, 208),
    ("VS_SNOW",   "villages/snow.png",   0, 214),
    ("VS_WASTE",  "villages/waste.png",  0, 220),
]


def palette():
    cols = set()
    for line in open(GPL, encoding="utf-8"):
        p = line.split()
        if len(p) >= 3 and all(v.isdigit() for v in p[:3]):
            cols.add(tuple(int(v) for v in p[:3]))
    return cols


def roles(t, size, im, foot):
    """Each cell's role, row by row: the stamp's 'E', '#' where the art stands
    on the ground, '^' other art, '.' none."""
    p, cw, ch, sz = im.load(), im.width // CELL, im.height // CELL, size + 1
    fx = (cw - sz) // 2
    out = []
    for cy in range(ch):
        for cx in range(cw):
            cell = [(x, y) for y in range(cy * CELL, (cy + 1) * CELL)
                    for x in range(cx * CELL, (cx + 1) * CELL)]
            if cy >= ch - sz and fx <= cx < fx + sz:
                out.append('E')
            elif any(foot[y][x] == '#' for x, y in cell):
                out.append('#')
            else:
                out.append('^' if any(p[x, y][3] for x, y in cell) else '.')
    return "".join(out)


def blocks():
    """[(name, size, image, col, row)] -- entrance blocks in ART order, then the
    sprite strips (size -1), shelf-packed."""
    out, col, row, shelf = [], 0, ROW0, 0

    def place(cw, ch):
        nonlocal col, row, shelf
        if col + cw > SHEET_COLS:
            col, row, shelf = 0, row + shelf, 0
        at = (col, row)
        col += cw
        shelf = max(shelf, ch)
        return at

    for t, size, biome, path, x, y, w, h in ART:
        if w % CELL or h % CELL:
            sys.exit("%s %d: %dx%d is not whole cells" % (t, size, w, h))
        cw, ch, sz = w // CELL, h // CELL, size + 1
        if (cw - sz) % 2 or ch < sz:
            sys.exit("%s %d: a %dx%d block cannot centre a %dx%d stamp" % (t, size, cw, ch, sz, sz))
        im = Image.open(os.path.join(HERE, path)).convert("RGBA").crop((x, y, x + w, y + h))
        lay = crop_layers(path, x, y, w, h)
        out.append((t, size, im) + place(cw, ch) + (roles(t, size, im, lay[1]), biome, lay))
    def strips(table):
        for name, path, n, *more in table:
            rows, x = more if more else (1, 0)
            im = Image.open(os.path.join(HERE, path)).convert("RGBA").crop((x, 0, x + n * CELL, rows * CELL))
            lay = crop_layers(path, x, 0, n * CELL, rows * CELL)
            out.append((name, -1, im) + place(n, rows) + (None, None, lay))
    strips(SPRITES)
    for n, path in INTERIORS:
        # the room, and beside it in the export the furniture's layer: the
        # room a block, the furniture only its cells that have any, a block
        # each (interior_<n>_furn says where each is drawn over the room)
        full = Image.open(os.path.join(HERE, path)).convert("RGBA")
        rw, rh = full.width // 2, full.height
        im = full.crop((0, 0, rw, rh))
        out.append((n, -2, im) + place(rw // CELL, rh // CELL) + (path, None, crop_layers(path, 0, 0, rw, rh)))
        for cy in range(rh // CELL):
            for cx in range(rw // CELL):
                x, y = rw + cx * CELL, cy * CELL
                cell = full.crop((x, y, x + CELL, y + CELL))
                if cell.getchannel("A").getbbox():
                    out.append(((n, cx, cy), -3, cell) + place(1, 1) + (None, None, crop_layers(path, x, y, CELL, CELL)))
    for n, path, dx, dy in HOUSES:
        im = Image.open(os.path.join(HERE, path)).convert("RGBA")
        lay = crop_layers(path, 0, 0, im.width, im.height)
        out.append(("TOWN_HOUSE", 0, im) + place(im.width // CELL, im.height // CELL)
                   + (roles("TOWN_HOUSE", -1, im, lay[1]), "-1", lay))
    strips(SPRITES_LAST)
    if row + shelf > ROW_END:
        sys.exit("the art runs past row %d" % ROW_END)
    sheet = Image.open(SHEET).convert("RGBA")
    for path, col, row in COAST:
        w, h = Image.open(os.path.join(HERE, path)).size
        im = sheet.crop((col * CELL, row * CELL, col * CELL + w, row * CELL + h))
        p = im.load()
        for y in range(h):
            for x in range(w):
                if p[x, y][:3] == KEY:
                    p[x, y] = (0, 0, 0, 0)
        lay = crop_layers(path, 0, 0, w, h)
        out.append(("TOWN_HOUSE", 0, im, col, row, roles("TOWN_HOUSE", -1, im, lay[1]), "-1", lay))
    for path, col, row in [(p, c, r) for _, _, p, c, r in LANDMARKS] + [CHEST, NODES]:
        im = Image.open(os.path.join(HERE, path)).convert("RGBA")
        lay = crop_layers(path, 0, 0, im.width, im.height)
        out.append(("TOWN_HOUSE", 0, im, col, row, roles("TOWN_HOUSE", -1, im, lay[1]), "-1", lay))
    for vset, path, col, row in VILLAGES:
        im = Image.open(os.path.join(HERE, path)).convert("RGBA")
        lay = crop_layers(path, 0, 0, im.width, im.height)
        out.append(("TOWN_HOUSE", 0, im, col, row, roles("TOWN_HOUSE", -1, im, lay[1]), "-1", lay))
    return out


def landmarks(legal):
    """(src/landmarks.inc's text, {sheet pixel: colour} of the landmarks' cells)."""
    rows, px = [], {}
    c0, r0, c1, r1 = LANDMARK_BAND
    for y in range(r0 * CELL, (r1 + 1) * CELL):
        for x in range(c0 * CELL, (c1 + 1) * CELL):
            px[(x, y)] = KEY
    for name, ground, path, col, row in LANDMARKS + [("CHEST", None) + CHEST, ("NODES", None) + NODES]:
        im = Image.open(os.path.join(HERE, path)).convert("RGBA")
        p, d = im.load(), design_of(path)
        for cy in range(im.height // CELL):
            for cx in range(im.width // CELL):
                cols = {p[x, y][:3] for y in range(cy * CELL, (cy + 1) * CELL)
                        for x in range(cx * CELL, (cx + 1) * CELL) if p[x, y][3]}
                if len(cols) > MAX_COLOURS:
                    sys.exit("%s cell (%d,%d): %d colours" % (name, cx, cy, len(cols)))
                if cols - legal:
                    sys.exit("%s cell (%d,%d) is off the palette: %s" % (name, cx, cy, cols - legal))
        for y in range(im.height):
            for x in range(im.width):
                px[(col * CELL + x, row * CELL + y)] = p[x, y][:3] if p[x, y][3] else KEY
        if ground is None:
            continue
        cx, cy = d["cache"]
        rows.append("    { %s, %d, %d, %d, %d, %d, %d },   // %s"
                    % (ground, col, row, d["stamp_w"], im.height // CELL, cx, cy, name))
    return NL.join([
        "// Generated by art/structures/gen_entrance_art.py -- do not edit.",
        "// The country's landmarks (LANDMARKS): the ground a kind stands on, its block",
        "// on the sheet (col, row), how many of its columns are stamped and how many",
        "// rows, and the cell of the block the cache stands in: the chest, laid there",
        "// shut, or open once struck (CHEST_COL, CHEST_ROW: shut, and open beside it).",
        "enum LandmarkGround { LM_GRASS, LM_FOREST, LM_SAND, LM_SNOW, LM_WASTE, LM_COAST };",
        "struct LandmarkKind { int ground, col, row, w, h, cache_x, cache_y; };",
        "enum { CHEST_COL = %d, CHEST_ROW = %d };" % CHEST[1:],
        "// The overworld's stone rock, and the gold ore vein beside it (NODE_COL + 1, then its",
        "// three twinkling frames).",
        "enum { NODE_COL = %d, NODE_ROW = %d };" % NODES[1:],
        "static const LandmarkKind LANDMARK_KINDS[] = {"] + rows + ["};", ""]), px


# (export, sheet col, sheet row) -- a ground's block drawn from a design
# (art/ground/<ground>_design.py; the user, 2026-10-14: the wasteland redrawn
# as cracked earth), written by --grounds and by nothing else; the game reads
# it by its cells (src/tilemap.cpp COVER_WASTE).
GROUNDS = [
    ("../ground/wasteland.png", 27, 4),
]


def block_pixels(name, im, col, row, legal, px):
    """Adds an export's pixels to px as {sheet pixel: colour} at cell (col, row),
    its cells checked: four colours at most, all on the palette."""
    p = im.load()
    for cy in range(im.height // CELL):
        for cx in range(im.width // CELL):
            cols = {p[x, y][:3] for y in range(cy * CELL, (cy + 1) * CELL)
                    for x in range(cx * CELL, (cx + 1) * CELL) if p[x, y][3]}
            if len(cols) > MAX_COLOURS:
                sys.exit("%s cell (%d,%d): %d colours" % (name, cx, cy, len(cols)))
            if cols - legal:
                sys.exit("%s cell (%d,%d) is off the palette: %s" % (name, cx, cy, cols - legal))
    for y in range(im.height):
        for x in range(im.width):
            px[(col * CELL + x, row * CELL + y)] = p[x, y][:3] if p[x, y][3] else KEY


def grounds(legal):
    """{sheet pixel: colour} of the grounds' blocks (GROUNDS)."""
    px = {}
    for path, col, row in GROUNDS:
        block_pixels(path, Image.open(os.path.join(HERE, path)).convert("RGBA"), col, row, legal, px)
    return px


def villages(legal):
    """(src/village_houses.inc's text, {sheet pixel: colour} of the villages' cells)."""
    houses, wells, fields, px = [], [], [], {}
    for vset, path, col, row in VILLAGES:
        im = Image.open(os.path.join(HERE, path)).convert("RGBA")
        d = design_of(path)
        block_pixels(vset, im, col, row, legal, px)
        rows = im.height // CELL
        for h in d["houses"]:
            dx, dy, dw = h["door"]
            houses.append("    { %s, %d, %d, %d, %d, %d, %d, %d },   // %s" % (
                vset, col + h["cell"], row + rows - h["h"], h["w"], h["h"], dx, dy, dw, os.path.basename(path)[:-4]))
        w = d["well"]
        wells.append("    { %s, %d, %d, %d, %d }," % (vset, col + w["cell"], row + rows - w["h"], w["w"], w["h"]))
        for e in d.get("fields", []):
            fields.append("    { %s, %d, %d, %d, %d },   // %s" % (vset, col + e["cell"], row + rows - e["h"], e["w"], e["h"], e["name"]))
    return NL.join([
        "// Generated by art/structures/gen_entrance_art.py -- do not edit.",
        "// The villages' building sets (VILLAGES): each house's block on the sheet",
        "// (col, row, w, h) and its door's foot in the block (cell across, cell down,",
        "// cells wide; a barn's door is 0 wide, it opens no room); each set's well.",
        "// A village is laid from its ground's set.",
        "enum VillageSet { VS_GRASS, VS_MEADOW, VS_SAND, VS_SNOW, VS_WASTE };",
        "struct VillageHouse { int set, col, row, w, h, door_x, door_y, door_w; };",
        "static const VillageHouse VILLAGE_HOUSES[] = {"] + houses + ["};",
        "struct VillageWell { int set, col, row, w, h; };",
        "static const VillageWell VILLAGE_WELLS[] = {"] + wells + ["};",
        "// a set's field cell (the meadow's farms), laid in fenced rectangles; none for most sets",
        "static const VillageWell VILLAGE_FIELDS[] = {"] + fields + ["};", ""]), px


def town_houses(placed):
    """src/town_houses.inc: each house's block on the sheet and where it
    stands in the town, its door and the room it opens."""
    rows = []
    for (n, path, dx, dy), (col, row, cw, ch) in zip(HOUSES, placed):
        cx, cy, w = design_of(path)["door"]
        rows.append("    { %d, %d, %d, %d,  %d, %d,  %d, %d, %d,  %d }," % (col, row, cw, ch, dx - cx, dy - cy, dx, dy, w, n))
    return NL.join([
        "// Generated by art/structures/gen_entrance_art.py -- do not edit.",
        "// The starting town's houses (HOUSES): the block on the sheet (col, row,",
        "// w, h), its top left cell in the town blueprint, the door's foot there and",
        "// how many cells wide, and the interior it opens.",
        "struct TownHouse { int col, row, w, h, x, y, door_x, door_y, door_w, interior; };",
        "static const TownHouse TOWN_HOUSES[] = {"] + rows + ["};", ""])


def room_layout(n, im, col, row, foot, exits):
    """interior_<n>_tiles and interior_<n>_coll, for include/interiors.h."""
    p = im.load()
    cw, ch = im.width // CELL, im.height // CELL
    tiles, coll = [], []
    for cy in range(ch):
        trow, crow = [], ""
        for cx in range(cw):
            cell = [(x, y) for y in range(cy * CELL, (cy + 1) * CELL) for x in range(cx * CELL, (cx + 1) * CELL)]
            ink = any(p[x, y][3] for x, y in cell)
            trow.append(str((row + cy) * SHEET_COLS + col + cx + 6) if ink else "0")
            crow += (" " if not ink else "E" if [cx, cy] in exits or (cx, cy) in exits
                     else "." if any(foot[y][x] != '#' for x, y in cell) else "#")
        tiles.append("    {" + ",".join(trow) + "},")
        coll.append('    "%s",' % crow)
    return NL.join(["static const int interior_%d_tiles[IMAP_H][IMAP_W] = {" % n] + tiles + ["};",
                    "static const char* interior_%d_coll[IMAP_H] = {" % n] + coll + ["};", ""])


def furniture_layout(n, furn):
    """interior_<n>_furn: the sheet cell (plus 6, 0 for none) of the
    furniture drawn over each of the room's cells."""
    rows = ["    {" + ",".join(str(furn.get((n, cx, cy), 0)) for cx in range(20)) + "},"
            for cy in range(15)]
    return NL.join(["// what of the furniture's layer is drawn over each cell",
                    "static const int interior_%d_furn[IMAP_H][IMAP_W] = {" % n] + rows + ["};", ""])


def write_if_changed(path, text):
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    if old != text and ("--stamp" in sys.argv or "--tables" in sys.argv):
        open(path, "w", encoding="utf-8", newline=NL).write(text)
    return old != text


def main():
    legal = palette()
    sheet = Image.open(SHEET).convert("RGB")
    sp = sheet.load()
    # the band as it should be: key everywhere, then the art
    want = {(x, y): KEY for y in range(ROW0 * CELL, ROW_END * CELL) for x in range(SHEET_COLS * CELL)}
    lines, sprites, depth, at, rooms, houses, furn = [], [], [], {}, [], [], {}
    for t, size, im, col, row, role, biome, lay in blocks():
        p = im.load()
        cw, ch = im.width // CELL, im.height // CELL
        mine = row < ROW_END                    # in the band: checked and stamped (COAST's is the sheet's own)
        for cy in range(ch if mine else 0):
            for cx in range(cw):
                cols = {p[x, y][:3] for y in range(cy * CELL, (cy + 1) * CELL)
                        for x in range(cx * CELL, (cx + 1) * CELL) if p[x, y][3]}
                if len(cols) > MAX_COLOURS:
                    sys.exit("%s cell (%d,%d): %d colours" % (t, cx, cy, len(cols)))
                if cols - legal:
                    sys.exit("%s cell (%d,%d) is off the palette: %s" % (t, cx, cy, cols - legal))
        for y in range(im.height if mine else 0):
            for x in range(im.width):
                if p[x, y][3]:
                    want[(col * CELL + x, row * CELL + y)] = p[x, y][:3]
        if lay:
            footy, foot, y0, way = lay
            for cy in range(ch):
                for cx in range(cw):
                    xs, ys = range(cx * CELL, (cx + 1) * CELL), range(cy * CELL, (cy + 1) * CELL)
                    bits = [sum(1 << (x - cx * CELL) for x in xs if foot[y][x] == '#') for y in ys]
                    ways = [sum(1 << (x - cx * CELL) for x in xs if way[y][x] == '#') for y in ys]
                    drop = [255 if not p[x, y][3] or footy[y][x] < 0 else min(254, max(0, footy[y][x] - y0 - y))
                            for y in ys for x in xs]
                    if not any(bits) and all(v == 255 for v in drop):
                        continue
                    at[(row + cy) * SHEET_COLS + col + cx] = len(depth) + 1
                    depth.append("    { {%s}, {%s}, {%s} }," % (",".join(map(str, bits)), ",".join(map(str, drop)),
                                                            ",".join(map(str, ways))))
        if size == -3:
            furn[t] = row * SHEET_COLS + col + 6
            continue
        if size == -2:
            rooms.append(room_layout(t, im, col, row, lay[1], design_of(role).get("exit", [])))
            continue
        if size < 0:
            sprites.append("#define %s_SHEET_COL %d%s#define %s_SHEET_ROW %d%s#define %s_COUNT %d%s"
                           % (t, col, NL, t, row, NL, t, cw, NL))
            continue
        if t == "TOWN_HOUSE" and mine:
            houses.append((col, row, cw, ch))
        lines.append('    { %s, %d, %s, %d, %d, %d, %d, "%s" },' % (t, size, biome, col, row, cw, ch, role))
    for path, col, row in FIXED:
        im = Image.open(os.path.join(HERE, path)).convert("RGBA")
        p = im.load()
        for y in range(im.height):
            for x in range(im.width):
                c = p[x, y][:3] if p[x, y][3] else KEY
                if c != KEY and c not in legal:
                    sys.exit("%s is off the palette at %d,%d" % (path, x, y))
                want[(col * CELL + x, row * CELL + y)] = c
    changed = sum(1 for q, c in want.items() if sp[q] != c)
    t1 = write_if_changed(INC, NL.join([
        "// Generated by art/structures/gen_entrance_art.py -- do not edit.",
        "// type, size, biome (-1 any), sheet col, sheet row, width and height in cells, and each",
        "// cell's role row by row (E way in, # stands on some of its ground, ^ only",
        "// drawn, . no art): worldgen reads this rather than the sheet, so a world",
        "// builds the same with no texture loaded.",
        "static const EntranceArt ENTRANCE_ART[] = {"] + lines + ["};", "",
        "// Every cell above with art on it, the yard walls' and the gravestones': the",
        "// ground it stands on (a bit a pixel, row by row), how far below each pixel its",
        "// ground line is, in art pixels (255: nothing drawn), and the ground of its way",
        "// in, a bit a pixel. ART_CELL_AT gives each sheet cell of",
        "// the band from row ART_BAND_ROW0 its entry plus one, 0 where it has none.",
        "#define ART_BAND_ROW0 %d" % ROW0,
        "#define ART_BAND_ROWS %d" % (max(at) // SHEET_COLS + 1 - ROW0),
        "static const ArtCellDepth ART_CELL_DEPTH[] = {"] + depth + ["};",
        "static const uint16_t ART_CELL_AT[ART_BAND_ROWS * %d] = {" % SHEET_COLS]
        + ["    " + ",".join(str(at.get(r * SHEET_COLS + c, 0)) for c in range(SHEET_COLS)) + ","
           for r in range(ROW0, max(at) // SHEET_COLS + 1)] + ["};", ""]))
    t2 = write_if_changed(SPRITES_INC, NL.join([
        "// Generated by art/structures/gen_entrance_art.py -- do not edit.",
        "// Where each strip of one-cell overworld sprites sits on the sheet.", ""]) + "".join(sprites))
    t3 = write_if_changed(INTERIORS_H, NL.join([
        "// Generated by art/structures/gen_entrance_art.py -- do not edit.",
        "#ifndef INTERIORS_H",
        "#define INTERIORS_H",
        "",
        '#include "interior.h"',
        "",
        "// Each room's 20x15 cells: the sheet cell it draws, plus 6 (0 for none -- the",
        "// dark outside the room), and what it is to the feet: ' ' outside, '#' all",
        "// solid, '.' some floor (the feet meet the art to the pixel, ArtCellDepth),",
        "// 'E' the doormat, the way out.",
        ""] + rooms + [furniture_layout(n, furn) for n, _ in INTERIORS] + ["#endif", ""]))
    t4 = write_if_changed(HOUSES_INC, town_houses(houses))
    lm_text, lm_px = landmarks(legal)
    t5 = write_if_changed(LANDMARKS_INC, lm_text)
    lm_changed = sum(1 for q, c in lm_px.items() if sp[q] != c)
    vg_text, vg_px = villages(legal)
    t6 = write_if_changed(VILLAGES_INC, vg_text)
    vg_changed = sum(1 for q, c in vg_px.items() if sp[q] != c)
    gd_px = grounds(legal)
    gd_changed = sum(1 for q, c in gd_px.items() if sp[q] != c)
    print("structure art: %d sheet pixels differ, %d of the landmarks' own, %d of the villages' own, %d of the grounds' own, tables %s"
          % (changed, lm_changed, vg_changed, gd_changed, "differ" if t1 or t2 or t3 or t4 or t5 or t6 else "same"))
    if "--landmarks" in sys.argv and lm_changed:
        for q, c in lm_px.items():
            sp[q] = c
        sheet.convert("RGBA").save(SHEET)
        print("the landmarks' cells written")
    if "--villages" in sys.argv and vg_changed:
        for q, c in vg_px.items():
            sp[q] = c
        sheet.convert("RGBA").save(SHEET)
        print("the villages' cells written")
    if "--grounds" in sys.argv and gd_changed:
        for q, c in gd_px.items():
            sp[q] = c
        sheet.convert("RGBA").save(SHEET)
        print("the grounds' cells written")
    if "--stamp" in sys.argv:
        if changed:
            for q, c in want.items():
                sp[q] = c
            sheet.convert("RGBA").save(SHEET)
        print("written -- now run: python tools/palette_pass.py --write")


if __name__ == "__main__":
    main()
