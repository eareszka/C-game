"""The overworld art of every structure entrance, stamped into assets/tileset.png.

    python art/structures/gen_entrance_art.py          # report only
    python art/structures/gen_entrance_art.py --stamp  # write the sheet and both tables
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
GPL = os.path.join(ROOT, "art", "direction", "game_palette.gpl")
CELL, KEY, MAX_COLOURS = 16, (255, 0, 0), 4
ROW0 = 20                 # rows 17-19 left for the island library to grow into
ROW_END = 60              # first row past the band this owns
SHEET_COLS = 256
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
    for name, path, n, *more in SPRITES:
        rows, x = more if more else (1, 0)
        im = Image.open(os.path.join(HERE, path)).convert("RGBA").crop((x, 0, x + n * CELL, rows * CELL))
        lay = crop_layers(path, x, 0, n * CELL, rows * CELL)
        out.append((name, -1, im) + place(n, rows) + (None, None, lay))
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
    if row + shelf > ROW_END:
        sys.exit("the art runs past row %d" % ROW_END)
    return out


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
    if old != text and "--stamp" in sys.argv:
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
        for cy in range(ch):
            for cx in range(cw):
                cols = {p[x, y][:3] for y in range(cy * CELL, (cy + 1) * CELL)
                        for x in range(cx * CELL, (cx + 1) * CELL) if p[x, y][3]}
                if len(cols) > MAX_COLOURS:
                    sys.exit("%s cell (%d,%d): %d colours" % (t, cx, cy, len(cols)))
                if cols - legal:
                    sys.exit("%s cell (%d,%d) is off the palette: %s" % (t, cx, cy, cols - legal))
        for y in range(im.height):
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
        if t == "TOWN_HOUSE":
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
    print("structure art: %d sheet pixels differ, tables %s"
          % (changed, "differ" if t1 or t2 or t3 or t4 else "same"))
    if "--stamp" in sys.argv:
        if changed:
            for q, c in want.items():
                sp[q] = c
            sheet.convert("RGBA").save(SHEET)
        print("written -- now run: python tools/palette_pass.py --write")


if __name__ == "__main__":
    main()
