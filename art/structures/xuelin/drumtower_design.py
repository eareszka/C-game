"""Xuelin's drum tower, the square's landmark: its lot across the main
street's head, sixteen cells across and six back (the user, 2026-10-28:
"base + 2-storey tower").

    python art/structures/xuelin/drumtower_design.py <design.json>

After PixelLab pixellab-out/xuelin-drum/sprites/v1: a broad grey brick base,
an arched doorway in its front where the main street ends (its sides blank:
the user, 2026-10-30, "door shouldnt be on right side of building"), a red rail round its top; on it the tower, two storeys -- the lower
open between red posts, the great drum showing in the middle, the upper in
lattice -- each under its own roof. The tallest thing in the town, and still
under the street behind its lot: z + d stays under 128 (six rows and the
street's two), so it covers no door of the row behind.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
sys.path.insert(0, HERE)
from house_shapes import House, brick_tone
from courtyard_design import TILES, timber, ROAD_MID
from shophouse_design import PAL, MERGE
from bookshop_design import rail

BASE = 32                     # the base's height


def size(lot_w):
    return lot_w + 7, 9


def arch(w, h, at, tone):
    """A face with an arched doorway `w` wide and `h` high, its middle `at`
    along: dark inside, a ring of pale stones round it, else `tone`."""
    r = w // 2
    def face(a, ry):
        z, ax = BASE - 1 - ry, a - at
        q = ax * ax + max(0, z - (h - r)) ** 2
        if abs(ax) < r and (z < h - r or q < r * r):
            return 'K'
        if abs(ax) < r + 3 and q < (r + 3) ** 2:
            return 'K' if q >= (r + 2) ** 2 else 'M'
        return tone(a, ry)
    return face


def drumfront(width, wall):
    """The open lower storey: red posts every 22, dark between, and in the
    middle the drum -- its pale hide, a red rim studded with gold."""
    cx, cz, r = width // 2, wall // 2, 8
    def tone(rx, ry):
        q = (rx - cx) ** 2 + (ry - cz) ** 2
        if q <= r * r:
            return 'M' if q < (r - 2) ** 2 else 'K' if q >= (r - 0.5) ** 2 else 'Y' if (rx + ry) % 3 == 0 else 'D'
        if rx % 22 < 3 or ry < 3:
            return 'D'
        return 'K'
    return tone


def draw(h, lot_w=16):
    from town_design import box
    X = lot_w * 16 - 18
    mid = (2 + X) // 2 - ROAD_MID                            # on the main street's paving
    x0, x1, d0, d1 = mid - 88, mid + 88, 2, 50
    box(h, x0, x1, d0, d1, 0, BASE, front=arch(26, 24, mid - x0, brick_tone),
        east=brick_tone, foot=True)                                  # the base
    for d, xa, xb in ((d0, x0 + 2, x1 - 2),):
        rail(h, xa, xb, BASE, d + 1)
    h.hall(mid - 64, mid + 64, 32, 20, 8, d0=10, z0=BASE, eave=6, lift=5, ridge=2, tiles=TILES,
           front=drumfront(129, 20), snow=0.3)                                                    # the drum's storey
    h.hall(mid - 42, mid + 42, 20, 14, 14, d0=16, z0=BASE + 26, eave=5, lift=6, tiles=TILES,
           front=timber)                                                                         # the upper storey
    return mid - 8, 16                                       # its door: the arch, at the main street's end


def design(lot_w=16):
    w, ch = size(lot_w)
    h = House(w + 1, ch, brick_tone)
    h.shift(16, 0)
    at = draw(h, lot_w)
    h.shift(0, 0)
    return h.finish('drumtower', PAL, (at[0] + 16, at[1]), merge=MERGE)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
