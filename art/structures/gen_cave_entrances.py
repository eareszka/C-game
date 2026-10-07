"""The overworld cave entrances, one per Material, stamped into assets/tileset.png.

    python art/structures/gen_cave_entrances.py          # report only
    python art/structures/gen_cave_entrances.py --stamp  # write the sheet
    python tools/palette_pass.py --write                  # always last

cave_entrance.aseprite is drawn through the pixel plugin in the stone tones and
exported beside it as cave_entrance.png (64x32, transparent where the ground or
wall shows through):

    x  0..47, y 0..31   the wall mouth: a ring of boulders round the opening,
                        laid over the foot of a south cliff wall (3x2 cells)
    x 48..63, y 0..15   the pit: the same boulders round a hole, for a cave on
                        flat ground or a storey top (1 cell)

and the ways out of a dungeon seen from inside, drawn by src/dungeon.cpp on
the north wall at each way out: ladder_up.aseprite (ladder_up_design.py), the
pit's ladder on the wall's face, a length of it and its foot, recoloured per
material; and dungeon_doors.aseprite (dungeon_doors_design.py), the built
entrances' doorways, each the size of its overworld one, in their own stone.

Every material is the same drawing in its own rock: each of the four stone tones
(line, shade, base, lit/ore fleck) is swapped for that material's. The layout
on the sheet, which src/tilemap.cpp must agree with (CAVE_ENT_ROW0 there):

    rows ROW0..ROW0+1, cols 3*m .. 3*m+2   material m's wall mouth
    row  ROW0+2,       col  m              material m's pit
    row  ROW0+2, ROW0+3, col LADDER_COL0+m material m's ladder: a length, its foot
    rows ROW0+1..ROW0+3, cols 21..29      the doorways, bottoms on ROW0+3 (DOORS)
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SHEET = os.path.join(ROOT, "assets", "tileset.png")
ART = os.path.join(HERE, "cave_entrance.png")
LADDER_UP = os.path.join(HERE, "ladder_up.png")
LADDER_COL0 = 7           # src/dungeon.cpp's LADDER_COL0
DOORS_ART = os.path.join(HERE, "dungeon_doors.png")
# (x in the export, w, h in cells, sheet col) -- src/dungeon.cpp's DOORS; each
# stands with its foot on row ROW0 + 3
DOORS = [(0, 3, 3, 21),     # ruins
         (48, 2, 2, 24),    # pyramid
         (96, 2, 2, 26),    # tree
         (144, 1, 2, 28),   # graveyards
         (192, 1, 3, 29)]   # catacombs
GPL = os.path.join(ROOT, "art", "direction", "game_palette.gpl")
CELL = 16
KEY = (255, 0, 0)
ROW0 = 12
MAX_COLOURS = 4           # tools/palette_pass.py's rule, per cell, key not counted

# Material enum order (include/entity.h). Line, shade, base, lit -- the first
# entry is the master's own tones, so stone is the drawing unchanged. Shade and
# base are the material's cave-wall tones from tools/gen_cave_tiles.py's
# stamped blocks; lit is its gem, so the flecks read as the ore.
K = (0, 0, 0)
TONES = [
    ("stone",         [K, (71, 71, 81),  (132, 134, 148), (188, 190, 202)]),
    ("bronze",        [K, (52, 30, 16),  (129, 84, 35),   (216, 152, 48)]),
    ("emerald",       [K, (35, 84, 54),  (79, 166, 103),  (168, 240, 188)]),
    ("veyrite",       [K, (48, 27, 90),  (55, 90, 148),   (132, 167, 233)]),
    ("dravium",       [K, (93, 30, 31),  (182, 67, 61),   (236, 132, 118)]),
    ("kharvite",      [K, (104, 80, 24), (201, 164, 51),  (250, 228, 136)]),
    ("reality_shard", [K, (43, 31, 64),  (102, 75, 149),  (182, 156, 238)]),
]
# The cliff islands are painted in the same ramps (src/cliff_paint.cpp): an
# island takes the tones of the ore of the cave inside it, and one with no cave
# this default -- the brown of the Mother 1 cliffs, given a shade and a lit.
DEFAULT = [K, (73, 55, 18), (136, 112, 0), (178, 158, 92)]
TONES_INC = os.path.join(ROOT, "src", "ore_tones.inc")
MOUTH = (0, 0, 48, 32)    # x, y, w, h in the export
PIT = (48, 0, 16, 16)


def palette():
    cols = set()
    for line in open(GPL, encoding="utf-8"):
        p = line.split()
        if len(p) >= 3 and all(v.isdigit() for v in p[:3]):
            cols.add(tuple(int(v) for v in p[:3]))
    return cols


def recolour(art, swap, keep=()):
    """A copy of art with its stone tones swapped for a material's."""
    im = art.copy()
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a and (r, g, b) not in keep:
                if (r, g, b) not in swap:
                    sys.exit("%s at %d,%d is not one of the stone tones" % ((r, g, b), x, y))
                px[x, y] = swap[(r, g, b)] + (255,)
    return im


def variants():
    """[(name, mouth, pit, ladder up)] RGBA images in Material order."""
    art = Image.open(ART).convert("RGBA")
    up = Image.open(LADDER_UP).convert("RGBA")
    master = TONES[0][1]
    out = []
    for name, tones in TONES:
        swap = dict(zip(master, tones))
        im = recolour(art, swap)
        crop = lambda r: im.crop((r[0], r[1], r[0] + r[2], r[1] + r[3]))
        out.append((name, crop(MOUTH), crop(PIT), recolour(up, swap)))
    return out


def placements():
    """[(image, col, row)] for every block this owns on the sheet."""
    res = []
    for m, (name, mouth, pit, up) in enumerate(variants()):
        res.append((mouth, 3 * m, ROW0))
        res.append((pit, m, ROW0 + 2))
        res.append((up.crop((0, 0, CELL, CELL)), LADDER_COL0 + m, ROW0 + 2))          # a length
        res.append((up.crop((CELL, 0, 2 * CELL, CELL)), LADDER_COL0 + m, ROW0 + 3))   # its foot
    doors = Image.open(DOORS_ART).convert("RGBA")
    for x, w, h, col in DOORS:
        res.append((doors.crop((x, 0, x + w * CELL, h * CELL)), col, ROW0 + 4 - h))
    return res


def write_tones(legal):
    """src/ore_tones.inc: the ramps as C, row 0 the default, row 1 + m material m."""
    rows = [("default", DEFAULT)] + TONES
    for name, tones in rows:
        if set(tones) - legal:
            sys.exit("%s ramp is off the palette: %s" % (name, set(tones) - legal))
    lines = ["// Generated by art/structures/gen_cave_entrances.py -- do not edit.",
             "// Cliff/cave rock ramps: line, shade, base, lit. Row 0 the default (no ore),",
             "// row 1 + m Material m (include/entity.h order).",
             "static const unsigned char ORE_TONES[%d][4][3] = {" % len(rows)]
    for name, tones in rows:
        lines.append("    { %s },   // %s" % (", ".join("{%d, %d, %d}" % c for c in tones), name))
    lines.append("};")
    text = "\n".join(lines) + "\n"
    old = open(TONES_INC, encoding="utf-8").read() if os.path.exists(TONES_INC) else None
    if old != text:
        open(TONES_INC, "w", encoding="utf-8", newline="\n").write(text)
        print("wrote", os.path.relpath(TONES_INC, ROOT))


def main():
    legal = palette()
    write_tones(legal)
    sheet = Image.open(SHEET).convert("RGB")
    sp = sheet.load()
    changed = 0
    for im, col, row in placements():
        p = im.load()
        for cy in range(im.height // CELL):
            for cx in range(im.width // CELL):
                cols = {p[x, y][:3] for y in range(cy * CELL, (cy + 1) * CELL)
                        for x in range(cx * CELL, (cx + 1) * CELL) if p[x, y][3]}
                if len(cols) > MAX_COLOURS:
                    sys.exit("cell (%d,%d) has %d colours" % (col + cx, row + cy, len(cols)))
                if cols - legal:
                    sys.exit("cell (%d,%d) is off the palette: %s" % (col + cx, row + cy, cols - legal))
        for y in range(im.height):
            for x in range(im.width):
                c = p[x, y][:3] if p[x, y][3] else KEY
                if sp[col * CELL + x, row * CELL + y] != c:
                    changed += 1
                    sp[col * CELL + x, row * CELL + y] = c
    print("cave entrances: %d pixels differ from the sheet (rows %d..%d)" % (changed, ROW0, ROW0 + 3))
    if "--stamp" in sys.argv and changed:
        sheet.convert("RGBA").save(SHEET)
        print("stamped into", os.path.relpath(SHEET, ROOT), "-- now run: python tools/palette_pass.py --write")


if __name__ == "__main__":
    main()
