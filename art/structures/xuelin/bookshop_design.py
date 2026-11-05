"""Xuelin's book shop, the region's: its lot by the gate, fifteen cells
across and seven back (the user, 2026-10-28: "shop + library hall").

    python art/structures/xuelin/bookshop_design.py <design.json>

After PixelLab pixellab-out/xuelin-bookshop/sprites/v1: a wide two-storey
shop on the street -- display windows of stacked books between red posts, a
board over them in the game's own sign (House.sign, BOOKS) framed in gold, a
balcony rail along the upper storey -- then a courtyard, and across the back
of the lot the library, a tall hall. Its door is at the east end, clear of
the gate tower, which stands before the lot's west end.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
sys.path.insert(0, HERE)
from house_shapes import House, brick_tone
from courtyard_design import TILES, timber
from shophouse_design import PAL, MERGE, door, lantern


def size(lot_w):
    return lot_w + 7, 10


def bookfront(width, wall, door_x):
    """The ground storey: red posts at its ends, a plank beam along the top,
    and display windows -- shelves of books, their spines in red and the two
    woods, black shelves between -- framed in black in a plank wall."""
    def tone(rx, ry):
        if rx < 3 or rx > width - 4:
            return 'D'
        if ry < 10:
            return 'v' if ry in (0, 9) else 'w'
        wx = (rx - 6) % 44                              # a window every 44, 34 across, under the sign's beam
        if 18 <= ry <= 35 and 0 <= wx < 34 and rx > 5 and not door_x - 6 <= rx <= door_x + 18:
            if wx in (0, 33) or ry in (18, 35):
                return 'K'
            shelf = (ry - 19) % 6
            return 'K' if shelf == 5 else ('D', 'w', 'v')[((rx - 6) // 2 + (ry - 19) // 6) % 3]
        if ry > wall - 4:
            return 'v'
        return 'K' if rx % 8 == 0 else 'w'
    return tone


def board(h, x0, z0, d0, text):
    """The sign, framed: the game's black board and gold capitals, a gold
    border round it and black round that."""
    B, w, ht = h.B, 4 * len(text) + 3, 9
    y0, y1 = B - d0 - z0 - ht - 2, B - d0 - z0 + 1
    for y in range(y0, y1 + 1):
        for x in range(x0 - 2, x0 + w + 2):
            if x0 <= x < x0 + w and y0 + 2 <= y <= y1 - 2:
                continue                                 # the board's own
            edge = x in (x0 - 2, x0 + w + 1) or y in (y0, y1)
            h.put(x + d0, y, 'K' if edge else 'Y', B - d0)
    h.sign(x0, z0, text, d0=d0, ink='Y')


def rail(h, x0, x1, z, d):
    """A balcony rail along the upper storey's front: a red top rail on black
    posts."""
    B = h.B
    for x in range(x0, x1 + 1):
        for k in range(7):
            c = 'D' if k in (5, 6) else 'K' if (x - x0) % 6 == 0 or k == 0 else None
            if c:
                h.put(x + d, B - z - k - d, c, B - d)


def draw(h, lot_w=15):
    X = lot_w * 16 - 18
    dx = (X - 40) // 16 * 16                                                                   # its door's cell
    h.hall(2, X, 26, 40, 4, d0=2, eave=5, lift=4, ridge=1, snow=0.3, tiles=TILES, ends=False,
           front=bookfront(X - 1, 40, dx - 2))                                                         # the shop
    h.hall(4, X - 2, 18, 20, 12, d0=8, z0=44, eave=5, lift=6, tiles=TILES, front=timber, snow=0.4)  # above
    rail(h, 6, X - 4, 44, 6)
    for x0 in (2, X - 4):                                                                      # the court's walls
        h.hall_d(x0, x0 + 4, 34, 28, 3, d0=29, eave=1, lift=0, ridge=1, snow=0, tiles=TILES, ends=False)
    h.hall(2, X, 26, 38, 16, d0=64, eave=3, lift=6, tiles=TILES, front=timber)               # the library
    at = door(h, dx, 2)
    for x in (10, X - 8):
        lantern(h, x, 31, 1)
    board(h, (2 + X) // 2 - 11, 24, 2, 'BOOKS')
    return at


def design(lot_w=15):
    w, ch = size(lot_w)
    h = House(w + 1, ch, brick_tone)
    h.shift(16, 0)                                         # a whole cell: its cells are the town's
    at = draw(h, lot_w)
    h.shift(0, 0)
    return h.finish('bookshop', PAL, (at[0] + 16, at[1]), merge=MERGE)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
