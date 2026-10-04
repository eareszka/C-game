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

Every material is the same drawing in its own rock: each of the four stone tones
(line, shade, base, lit/ore fleck) is swapped for that material's. The layout
on the sheet, which src/tilemap.cpp must agree with (CAVE_ENT_ROW0 there):

    rows ROW0..ROW0+1, cols 3*m .. 3*m+2   material m's wall mouth
    row  ROW0+2,       col  m              material m's pit
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SHEET = os.path.join(ROOT, "assets", "tileset.png")
ART = os.path.join(HERE, "cave_entrance.png")
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
MOUTH = (0, 0, 48, 32)    # x, y, w, h in the export
PIT = (48, 0, 16, 16)


def palette():
    cols = set()
    for line in open(GPL, encoding="utf-8"):
        p = line.split()
        if len(p) >= 3 and all(v.isdigit() for v in p[:3]):
            cols.add(tuple(int(v) for v in p[:3]))
    return cols


def variants():
    """[(name, mouth RGBA image, pit RGBA image)] in Material order."""
    art = Image.open(ART).convert("RGBA")
    master = TONES[0][1]
    out = []
    for name, tones in TONES:
        swap = dict(zip(master, tones))
        im = art.copy()
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if a:
                    if (r, g, b) not in swap:
                        sys.exit("cave_entrance.png has %s at %d,%d, not one of the stone tones"
                                 % ((r, g, b), x, y))
                    px[x, y] = swap[(r, g, b)] + (255,)
        crop = lambda r: im.crop((r[0], r[1], r[0] + r[2], r[1] + r[3]))
        out.append((name, crop(MOUTH), crop(PIT)))
    return out


def placements():
    """[(image, col, row)] for every block this owns on the sheet."""
    res = []
    for m, (name, mouth, pit) in enumerate(variants()):
        res.append((mouth, 3 * m, ROW0))
        res.append((pit, m, ROW0 + 2))
    return res


def main():
    legal = palette()
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
    print("cave entrances: %d pixels differ from the sheet (rows %d..%d)" % (changed, ROW0, ROW0 + 2))
    if "--stamp" in sys.argv and changed:
        sheet.convert("RGBA").save(SHEET)
        print("stamped into", os.path.relpath(SHEET, ROOT), "-- now run: python tools/palette_pass.py --write")


if __name__ == "__main__":
    main()
