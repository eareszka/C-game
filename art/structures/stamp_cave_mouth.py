"""The cave mouth, stamped into assets/tileset.png.

    python art/structures/stamp_cave_mouth.py          # report only
    python art/structures/stamp_cave_mouth.py --stamp  # write the sheet
    python tools/palette_pass.py --write                # always last

The mouth is drawn in cave_mouth.aseprite through the pixel plugin and exported
beside it as cave_mouth.png (48x32, transparent where the wall shows through).
That export is what this stamps, at CELL (21, 6) of the sheet, three cells wide
and two tall -- the block src/tilemap.cpp lays over the foot of a south wall
(CAVE_MOUTH_COL/ROW there must agree with COL/ROW here). Transparent in the
export is the sheet's key colour. The stamp refuses to paint over art it does
not own: anything in the block that is neither key nor the previous mouth.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SHEET = os.path.join(ROOT, "assets", "tileset.png")
ART = os.path.join(HERE, "cave_mouth.png")
COL, ROW = 21, 6          # the block's top-left cell on the sheet
W, H = 48, 32             # three cells by two
KEY = (255, 0, 0)
CELL = 16
MAX_COLOURS = 4           # tools/palette_pass.py's rule, per cell, key not counted


def main():
    art = Image.open(ART).convert("RGBA")
    if art.size != (W, H):
        sys.exit("cave_mouth.png is %dx%d, expected %dx%d" % (art.size + (W, H)))
    ap = art.load()
    pixels = [[ap[x, y][:3] if ap[x, y][3] else KEY for x in range(W)] for y in range(H)]
    for cy in range(H // CELL):
        for cx in range(W // CELL):
            cols = {pixels[y][x] for y in range(cy * CELL, (cy + 1) * CELL)
                    for x in range(cx * CELL, (cx + 1) * CELL)} - {KEY}
            if len(cols) > MAX_COLOURS:
                sys.exit("cell (%d,%d) of the mouth has %d colours; the sheet allows %d"
                         % (COL + cx, ROW + cy, len(cols), MAX_COLOURS))
    sheet = Image.open(SHEET).convert("RGB")
    sp = sheet.load()
    x0, y0 = COL * CELL, ROW * CELL
    changed = 0
    for y in range(H):
        for x in range(W):
            if sp[x0 + x, y0 + y] != pixels[y][x]:
                changed += 1
    print("cave mouth: %d of %d pixels differ from the sheet at cells (%d..%d, %d..%d)"
          % (changed, W * H, COL, COL + W // CELL - 1, ROW, ROW + H // CELL - 1))
    if "--stamp" not in sys.argv:
        return
    for y in range(H):
        for x in range(W):
            sp[x0 + x, y0 + y] = pixels[y][x]
    sheet.convert("RGBA").save(SHEET)
    print("stamped into", os.path.relpath(SHEET, ROOT), "-- now run: python tools/palette_pass.py --write")


if __name__ == "__main__":
    main()
