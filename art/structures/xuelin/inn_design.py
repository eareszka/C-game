"""Xuelin's inn: its lot by the gate, west of the main street, fifteen cells
across and seven back (the user, 2026-10-28: "inn + guest courtyard").

    python art/structures/xuelin/inn_design.py <design.json>

After PixelLab pixellab-out/xuelin-inn/sprites/v1: a two-storey front hall
in pale plaster between red posts, paper lattice windows, a row of red
lanterns along its eave, the upper storey raised higher in the middle; its
door at the west end under the game's own sign (INN), clear
of the gate tower before the lot's east end. Behind it a courtyard with a
guest wing either side, and a stable shed across the back.
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


def plaster(width, wall, door_x):
    """The ground storey: red posts every 36, a lacquered beam along the top,
    pale plaster between, paper lattice windows -- black on white -- and a
    red dado along the foot; round the door, red lacquer."""
    def tone(rx, ry):
        if rx % 36 < 3 or rx > width - 4 or door_x - 2 <= rx <= door_x + 13:
            return 'D'                                   # the posts, and the door's cell in lacquer
        if ry < 4:
            return 'd'
        if ry > wall - 7:
            return 'K' if ry == wall - 6 else 'D'
        wx = rx % 36
        if 12 <= ry <= 26 and 8 <= wx <= 28:
            return 'K' if wx in (8, 28) or ry in (12, 26) or wx % 4 == 0 or ry % 4 == 0 else 'W'
        return 'M'
    return tone


def stable(rx, ry):
    """The stable's front: planks, black between, and its stalls' dark
    openings."""
    if 8 <= ry and 6 <= rx % 40 < 30:
        return 'K' if ry == 8 or rx % 40 in (6, 29) else 'v'
    return 'K' if rx % 4 == 0 else 'w'


def draw(h, lot_w=15):
    X = lot_w * 16 - 18
    mid, dx = (2 + X) // 2, 32                                                                  # its door: the west end
    h.hall(2, X, 26, 38, 4, d0=2, eave=5, lift=4, ridge=1, snow=0.3, tiles=TILES, ends=False,
           front=plaster(X - 1, 38, dx - 2))                                                    # the front hall
    h.hall(4, X - 2, 18, 18, 10, d0=8, z0=42, eave=4, lift=5, tiles=TILES, front=timber, snow=0.4)
    h.hall(mid - 44, mid + 44, 14, 28, 14, d0=9, z0=42, eave=5, lift=6, tiles=TILES, front=timber)   # raised
    h.hall_d(2, 34, 36, 24, 10, d0=29, tiles=TILES, face=timber)                                # the guest wings
    h.hall_d(X - 32, X, 36, 24, 10, d0=29, tiles=TILES)
    h.hall(2, X, 22, 26, 10, d0=68, eave=3, lift=4, tiles=TILES, front=stable)                  # the stable
    at = door(h, dx, 2)
    for x in range(12, X - 4, 26):
        if not dx - 6 <= x <= dx + 22:                                                          # clear of the sign
            lantern(h, x, 31, 1)
    h.sign(dx, 24, 'INN', d0=2, ink='Y')                                                      # in the door's cell
    return at


def design(lot_w=15):
    w, ch = size(lot_w)
    h = House(w + 1, ch, brick_tone)
    h.shift(16, 0)                                         # a whole cell: its cells are the town's
    at = draw(h, lot_w)
    h.shift(0, 0)
    return h.finish('inn', PAL, (at[0] + 16, at[1]), merge=MERGE)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
