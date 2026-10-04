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

  - stamp rows: the stamp's cells are the way in ('E'); any other cell with
    art on it is solid ('#'), like the wall of a house
  - rows above: drawn over the player, who walks behind them ('^')

That is worked out here for a building. Art that spreads back along the
ground -- a pool -- gives its own roles instead, one character a cell row by
row, as the eighth field of its ART entry, and may also use '_' for art on the
ground that is walked over. Either way '.' is a cell with no art.

Other overworld sprites drawn the same way -- the gravestones graveyards are
scattered with -- are strips of single cells, listed in SPRITES and packed
after the blocks; their place goes to src/sheet_sprites.inc for whoever draws
them. Blocks and strips are packed left to right on shelves from ROW0, and
the band ROW0..ROW_END is this script's: it is cleared before every stamp, so
a layout that moves leaves nothing stale behind.

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
GPL = os.path.join(ROOT, "art", "direction", "game_palette.gpl")
CELL, KEY, MAX_COLOURS = 16, (255, 0, 0), 4
ROW0 = 20                 # rows 17-19 left for the island library to grow into
ROW_END = 60              # first row past the band this owns
SHEET_COLS = 256
NL = "\n"



def design_roles(name, key):
    """The ROLES a design file gives for one of its blocks, read from the file
    itself so the roles live in one place."""
    import importlib.util
    path = os.path.join(HERE, "entrances", name + "_design.py")
    spec = importlib.util.spec_from_file_location(name + "_design", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ROLES[key]


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
    ("DUNGEON_ENT_OASIS", 0, "-1", "entrances/oasis.png", 0, 0, 80, 32,
     design_roles("oasis", "sand")),
    ("DUNGEON_ENT_OASIS", 0, "TILE_SNOW", "entrances/oasis.png", 80, 0, 80, 32,
     design_roles("oasis", "snow")),
]

# (name, export, cells[, rows, x]) -- a strip of sprites from the export's top
# left, or from x across: cells wide and rows cells tall (one if not given)
SPRITES = [
    ("GRAVESTONE", "entrances/gravestones.png", 6),
    ("STEAM", "entrances/steam.png", 4),
    ("OASIS_WATER", "entrances/oasis_water.png", 1),
    ("YARD_FENCE", "entrances/yard_walls.png", 16, 2, 0),
    ("YARD_WALL", "entrances/yard_walls.png", 16, 2, 256),
]


def palette():
    cols = set()
    for line in open(GPL, encoding="utf-8"):
        p = line.split()
        if len(p) >= 3 and all(v.isdigit() for v in p[:3]):
            cols.add(tuple(int(v) for v in p[:3]))
    return cols


def roles(t, size, im, given):
    """Each cell's role, row by row: worked out for a building, or checked if
    the art gives its own -- every cell with art must have a role, and the
    stamp's cells, and only those, are 'E'."""
    p, cw, ch, sz = im.load(), im.width // CELL, im.height // CELL, size + 1
    fx = (cw - sz) // 2
    out = []
    for cy in range(ch):
        for cx in range(cw):
            ink = any(p[x, y][3] for y in range(cy * CELL, (cy + 1) * CELL)
                      for x in range(cx * CELL, (cx + 1) * CELL))
            stamp = cy >= ch - sz and fx <= cx < fx + sz
            want = 'E' if stamp else ('.' if not ink else '#' if cy >= ch - sz else '^')
            if given is None:
                out.append(want)
                continue
            c = given[cy * cw + cx]
            if c not in "E#^_." or (c == 'E') != stamp or (ink and c == '.'):
                sys.exit("%s %d: cell (%d,%d) has role %r" % (t, size, cx, cy, c))
            out.append(c)
    if given is not None and len(given) != cw * ch:
        sys.exit("%s %d: %d roles for %d cells" % (t, size, len(given), cw * ch))
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

    for t, size, biome, path, x, y, w, h, *given in ART:
        if w % CELL or h % CELL:
            sys.exit("%s %d: %dx%d is not whole cells" % (t, size, w, h))
        cw, ch, sz = w // CELL, h // CELL, size + 1
        if (cw - sz) % 2 or ch < sz:
            sys.exit("%s %d: a %dx%d block cannot centre a %dx%d stamp" % (t, size, cw, ch, sz, sz))
        im = Image.open(os.path.join(HERE, path)).convert("RGBA").crop((x, y, x + w, y + h))
        out.append((t, size, im) + place(cw, ch) + (roles(t, size, im, given[0] if given else None), biome))
    for name, path, n, *more in SPRITES:
        rows, x = more if more else (1, 0)
        im = Image.open(os.path.join(HERE, path)).convert("RGBA").crop((x, 0, x + n * CELL, rows * CELL))
        out.append((name, -1, im) + place(n, rows) + (None, None))
    if row + shelf > ROW_END:
        sys.exit("the art runs past row %d" % ROW_END)
    return out


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
    lines, sprites = [], []
    for t, size, im, col, row, role, biome in blocks():
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
        if size < 0:
            sprites.append("#define %s_SHEET_COL %d%s#define %s_SHEET_ROW %d%s#define %s_COUNT %d%s"
                           % (t, col, NL, t, row, NL, t, cw, NL))
            continue
        lines.append('    { %s, %d, %s, %d, %d, %d, %d, "%s" },' % (t, size, biome, col, row, cw, ch, role))
    changed = sum(1 for q, c in want.items() if sp[q] != c)
    t1 = write_if_changed(INC, NL.join([
        "// Generated by art/structures/gen_entrance_art.py -- do not edit.",
        "// type, size, biome (-1 any), sheet col, sheet row, width and height in cells, and each",
        "// cell's role row by row (E way in, # solid, ^ walked behind, _ floor,",
        "// . no art): worldgen reads this rather than the sheet, so a world",
        "// builds the same with no texture loaded.",
        "static const EntranceArt ENTRANCE_ART[] = {"] + lines + ["};", ""]))
    t2 = write_if_changed(SPRITES_INC, NL.join([
        "// Generated by art/structures/gen_entrance_art.py -- do not edit.",
        "// Where each strip of one-cell overworld sprites sits on the sheet.", ""]) + "".join(sprites))
    print("structure art: %d sheet pixels differ, tables %s" % (changed, "differ" if t1 or t2 else "same"))
    if "--stamp" in sys.argv:
        if changed:
            for q, c in want.items():
                sp[q] = c
            sheet.convert("RGBA").save(SHEET)
        print("written -- now run: python tools/palette_pass.py --write")


if __name__ == "__main__":
    main()
