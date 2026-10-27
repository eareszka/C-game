"""The void: the wasteland's liquid, where lava was (the user, 2026-10-27, the
overhaul after the Yume Nikki references; art/concept/wasteland/).

    python art/ground/void_design.py [--stamp]

One cell, sheet (15,0), drawn as the water's cell is drawn -- a flat fill with
whole marks laid on it, the water's own ripple pattern -- in the void's
purples: fill 2c0c47, the marks 301b5a, a few of them 3b2a58. The lone dots
of the water's pattern are dropped, so only whole marks remain. Writes
art/ground/void.png; --stamp also writes the cell into assets/tileset.png
(then run tools/palette_pass.py --write). Its 1px rim on the land side is
the game's shore band (src/tilemap.cpp, lava's GroundBiome row, 110000).
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHEET = os.path.join(HERE, '..', '..', 'assets', 'tileset.png')
FILL, MARK, MARK_HI = (0x2c, 0x0c, 0x47, 255), (0x30, 0x1b, 0x5a, 255), (0x3b, 0x2a, 0x58, 255)
# the water cell's marks (sheet 14,0), 'B' a mark
WATER = """
.......B........
............B...
.B.........B.B..
.........B......
.....B..........
....BBB.........
.B.B..BBB....B..
...........BB...
..............B.
B....B.........B
...BB.B....B....
..........BBB...
.........B..BB..
..B...B.........
.B.B............
................"""


def cell():
    rows = WATER.strip('\n').split('\n')
    im = Image.new('RGBA', (16, 16), FILL)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != 'B':
                continue
            n = sum(0 <= x + dx < 16 and 0 <= y + dy < 16 and rows[y + dy][x + dx] == 'B'
                    for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
            if n == 0:
                continue                                  # a lone dot: not a whole mark
            im.putpixel((x, y), MARK_HI if (x + y) % 5 == 0 else MARK)
    return im


if __name__ == '__main__':
    im = cell()
    im.save(os.path.join(HERE, 'void.png'))
    if '--stamp' in sys.argv:
        sheet = Image.open(SHEET).convert('RGBA')
        sheet.paste(im, (15 * 16, 0))
        sheet.save(SHEET)
        print('stamped sheet (15,0)')
    print('wrote', os.path.join(HERE, 'void.png'))
