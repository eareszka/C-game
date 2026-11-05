"""Xuelin's shrine, closing the west lane under the back wall: fourteen
cells across, six back (the user, 2026-10-28: "temple hall").

    python art/structures/xuelin/shrine_design.py <design.json>

After PixelLab pixellab-out/xuelin-shrine/sprites/v1: a grey stone terrace,
steps up its front where the lane ends, and on it the hall -- red posts and
pale plaster -- under a double eave, the lower a skirt round it, the upper
roof steep and high; a bronze incense burner on the terrace before it.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
sys.path.insert(0, HERE)
from house_shapes import House, brick_tone
from courtyard_design import TILES, timber, ROAD_MID
from shophouse_design import PAL, MERGE

TERRACE = 10                  # the terrace's height
DOOR_CELL = 6                 # the lane's middle, k 138, across the lot from its k0 (132)


def size(lot_w):
    return lot_w + 7, 9


def stone(rx, ry):
    """The terrace's dressed stone: long blocks in courses five high."""
    return 'K' if ry % 5 == 4 or (rx + (ry // 5) % 2 * 8) % 16 == 0 else 'B'


def hallfront(width):
    """The hall's front: red posts every 20, pale plaster between, a dark
    open door in the middle bay."""
    mid = width // 2
    def tone(rx, ry):
        if rx % 20 < 3 or rx > width - 4 or ry < 3:
            return 'D'
        if abs(rx - mid) < 8 and ry > 4:
            return 'K'
        return 'M'
    return tone


def burner(h, x, d, z):
    """A bronze incense burner: a round pot on three legs, a lid with a knob,
    smoke-dark in its mouth -- in the woods' tones, black round it."""
    B = h.B
    pts = {}
    for j in range(-5, 6):
        for i in range(-5, 6):
            if (i / 5.5) ** 2 + (j / 4.5) ** 2 <= 1:
                pts[(i, j)] = 'v' if i > 1 else 'w'
    for i in (-4, 0, 4):
        pts[(i, 5)] = pts[(i, 6)] = 'K'
    for i in range(-3, 4):
        pts[(i, -6)] = 'v'
    pts[(0, -7)] = pts[(0, -8)] = 'w'
    for (i, j), c in pts.items():
        edge = any((i + a, j + b) not in pts for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        h.put(x + d + i, B - z - d - 6 + j, 'K' if edge else c, B - d)


def draw(h, lot_w=14):
    from town_design import box
    X = lot_w * 16 - 18 - ROAD_MID                           # all of it on the lane's paving
    dx = DOOR_CELL * 16 - ROAD_MID
    box(h, 14 - ROAD_MID, X - 14, 12, 80, 0, TERRACE, front=stone, east=stone, top='M', foot=True)       # the terrace
    for i in range(5):                                                                          # its steps
        box(h, dx - 4, dx + 19, 2 + 2 * i, 12, 0, 2 * (i + 1), front=stone, east=stone, top='M')
    h.hall(30 - ROAD_MID, X - 30, 44, 18, 5, d0=24, z0=TERRACE, eave=7, lift=5, ridge=1, tiles=TILES, snow=0.3,
           ends=False, front=hallfront(X - 59 + ROAD_MID))                                                 # the hall, its skirt
    h.hall(42 - ROAD_MID, X - 42, 30, 14, 18, d0=31, z0=TERRACE + 23, eave=6, lift=8, tiles=TILES,
           front=timber, snow=0.45)                                                            # the upper roof
    burner(h, X - 52, 16, TERRACE)
    return dx, 16


def design(lot_w=14):
    w, ch = size(lot_w)
    h = House(w + 1, ch, brick_tone)
    h.shift(16, 0)
    at = draw(h, lot_w)
    h.shift(0, 0)
    return h.finish('shrine', PAL, (at[0] + 16, at[1]), merge=MERGE)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
