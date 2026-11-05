"""The elder's house, closing the east lane under the back wall: thirteen
cells across, six back (the user, 2026-10-28: "grand compound"). The town's
elder lives here, who knows of the one that stares (boss 52).

    python art/structures/xuelin/elder_design.py <design.json>

A richer courtyard house than the street's (courtyard_design.py), after
PixelLab pixellab-out/xuelin-elder/sprites/v1: its gatehouse where the lane
ends, taller and red-lacquered, the courtyard's red double gate in it, a
stone lion each side on a plinth; behind the lane wall a screen wall with a
round moon gate; and across the back the main hall, two storeys -- pulled
forward enough that its upper roof stays under the street behind (z + d
under 128).
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
sys.path.insert(0, HERE)
from house_shapes import House, brick_tone
from courtyard_design import TILES, timber, gate, ROAD_MID
from shophouse_design import PAL, MERGE

DOOR_CELL = 6                 # the lane's middle, k 176, across the lot from its k0 (170)


def size(lot_w):
    return lot_w + 7, 9


def lacquer(rx, ry):
    """The gatehouse's front: red lacquer, a beam along its top."""
    return 'd' if ry < 3 or rx < 2 else 'D'


def moon(width, wall, r=11):
    """A screen wall, brick, a round moon gate open through its middle."""
    def tone(rx, ry):
        q = (rx - width // 2) ** 2 + (ry - wall // 2 - 2) ** 2
        if q < r * r:
            return None
        if q < (r + 2) ** 2:
            return 'K' if q >= (r + 1) ** 2 else 'M'
        return brick_tone(rx, ry)
    return tone


def lion(h, x, d):
    """A stone lion on its plinth, seated, facing the lane: a pale grey
    body, its mane and haunch in the shade, black round it."""
    B = h.B
    pts = {}
    for i in range(-4, 5):                                   # the plinth
        for j in range(0, 4):
            pts[(i, j)] = 'S' if j == 3 else 'B'
    for i in range(-3, 4):                                   # the body
        for j in range(-6, 0):
            pts[(i, j)] = 'B' if i > 1 else 'M'
    for i in range(-3, 3):                                   # the head and mane
        for j in range(-11, -6):
            pts[(i, j)] = 'B' if abs(i) == 3 or j == -11 else 'M'
    pts[(-1, -9)] = pts[(1, -9)] = 'K'                       # its eyes
    for (i, j), c in pts.items():
        edge = any((i + a, j + b) not in pts for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        h.put(x + d + i, B - d - 4 + j, 'K' if edge else c, B - d)


def draw(h, lot_w=13):
    X = lot_w * 16 - 18
    dx = DOOR_CELL * 16 - ROAD_MID                           # on the lane's paving
    h.hall(4, X, 24, 26, 5, d0=46, eave=5, lift=4, ridge=1, snow=0.3, tiles=TILES, ends=False,
           front=timber)                                                                       # the main hall
    h.hall(12, X - 8, 14, 16, 12, d0=51, z0=31, eave=5, lift=6, tiles=TILES, front=timber)    # its upper storey
    h.hall(16, X - 16, 3, 26, 3, d0=30, eave=1, lift=1, ridge=1, snow=0, tiles=TILES, ends=False,
           front=moon(X - 31, 26))                                                            # the moon gate's wall
    for x0 in (4, X - 4):                                                                     # the side walls
        h.hall_d(x0, x0 + 4, 38, 28, 3, d0=8, eave=1, lift=0, ridge=1, snow=0, tiles=TILES, ends=False)
    h.hall(4, X, 6, 30, 4, d0=2, eave=2, lift=1, ridge=1, snow=0, tiles=TILES, ends=False)    # the lane wall
    h.hall(dx - 16, dx + 31, 14, 46, 12, d0=0, eave=4, lift=5, tiles=TILES, front=lacquer)    # the gatehouse
    at = gate(h, dx, h.B - 31)
    B = h.B
    for y in range(B - 41, B - 33):                                                           # a plaque over the gate
        for x in range(dx - 2, dx + 18):
            edge = x in (dx - 2, dx + 17) or y in (B - 41, B - 34)
            h.put(x, y, 'Y' if edge else 'K', B)
    for x in (dx - 23, dx + 38):                                                              # the lions, either side
        lion(h, x, 0)
    return at


def design(lot_w=13):
    w, ch = size(lot_w)
    h = House(w + 1, ch, brick_tone)
    h.shift(16, 0)
    at = draw(h, lot_w)
    h.shift(0, 0)
    return h.finish('elder', PAL, (at[0] + 16, at[1]), merge=MERGE)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
