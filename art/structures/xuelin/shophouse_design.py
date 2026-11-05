"""Xuelin's shophouses: the ordinary lots, six to nine cells across and seven
back, each filled (the user, 2026-10-28: "mix of both").

    python art/structures/xuelin/shophouse_design.py <design.json> [lot width] [kind] [sign]

Two kinds, after PixelLab pixellab-out/xuelin-shop/sprites/v1 (and v2's
massing):
  'shop'  -- a two-storey shop on the street, a tiled pent roof between its
             storeys, its front open on shutters and a counter between red
             posts, a lantern each side, a board over the door; behind it a
             walled yard and a one-storey house across the back of the lot.
  'block' -- one deep two-storey block filling the lot, its ridge running
             back, its gable end on the street: the shop front under a pent
             eave there, lattice windows down its long side.
A sign is the game's own (House.sign): a black board, the words in the 3x5
capitals, in gold -- or none, a house that sells nothing.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
sys.path.insert(0, HERE)
from house_shapes import House, brick_tone, DOOR_H
from overworld_style import MATERIALS
from courtyard_design import PAL as _PAL, TILES, timber

WOOD = MATERIALS['wood']['tones']
PAL = dict(_PAL, w=WOOD[0], v=WOOD[1], G=MATERIALS['foliage']['tones'][2], g=MATERIALS['foliage']['tones'][1])   # and the pines' greens
# the courtyard's, then the wood's shade into its tone, a lantern's light into its red;
# where neighbours meet in a cell, a post into the planks, snow into the stone
MERGE = [('M', 'B'), ('A', 'W'), ('Q', 'S'), ('d', 'D'), ('v', 'w'), ('Y', 'D'), ('B', 'S'),
         ('D', 'w'), ('W', 'M'), ('w', 'K')]


def size(lot_w):
    """Its block in cells, for a lot lot_w cells across."""
    return lot_w + 7, 10


def shopfront(width, wall):
    """The ground storey's front: red posts at its ends, a plank board along
    the top for the sign, then shutters -- planks, black between -- over a
    counter."""
    def tone(rx, ry):
        if rx < 3 or rx > width - 4:
            return 'D'
        if ry < 10:
            return 'v' if ry in (0, 9) else 'w'
        if ry > wall - 8:
            return 'K' if ry == wall - 7 else 'v'                  # the counter
        return 'K' if rx % 5 == 0 else 'w'
    return tone


def lattice_side(rd, ry):
    """A long side: brick, a lattice window every 24 back on each storey."""
    if 8 <= rd % 24 < 20 and (6 <= ry <= 14 or 24 <= ry <= 32):
        return 'K' if rd % 24 in (8, 19) or ry in (6, 14, 24, 32) or rd % 3 == 0 or ry % 3 == 0 else 'M'
    return brick_tone(rd, ry)


def door(h, x0, d0=0):
    """A shop's plank door, a cell wide on the ground line, d0 back."""
    B = h.B
    top = B - d0 - DOOR_H - 1
    for y in range(top, B - d0):
        for x in range(x0 + 2, x0 + 14):
            lx = x - x0 - 2
            c = 'K' if lx in (0, 11) or y == top or lx % 3 == 0 else 'v' if lx % 3 == 2 else 'w'
            h.put(x + d0, y, c, B - d0)
    h.put(x0 + 10 + d0, B - d0 - DOOR_H // 2, 'Y', B - d0)
    return x0 + 2 + d0, 12


def lantern(h, x, z, d):
    """A red paper lantern hanging at (x, z), d back: black round it, a gold
    band of its light across the middle."""
    B = h.B
    for j in range(-4, 5):
        for i in range(-3, 4):
            if (i / 3.5) ** 2 + (j / 4.5) ** 2 > 1:
                continue
            edge = (abs(i) + 1) / 3.5 > 1 - (j / 4.5) ** 2 or abs(j) == 4
            c = 'K' if edge else 'Y' if j == 0 else 'D'
            h.put(x + d + i, B - z - d + j, c, B - d + 1)
    h.put(x + d, B - z - d - 5, 'K', B - d + 1)


def draw(h, lot_w, kind='shop', sign=None):
    """The building on a lot lot_w cells across; gives back its door. Nothing
    of it rises past the street behind its lot, so it covers no door there:
    every roof's top, z + d, is under 144 (seven rows and the street's two)."""
    X = lot_w * 16 - 18                                     # its east wall: its feet on the lot at every row
    mid = (2 + X) // 2
    dx = (mid - 8) // 16 * 16                               # its door's cell
    if kind == 'shop':
        h.hall(2, X, 26, 38, 4, d0=2, eave=4, lift=3, ridge=1, snow=0.3, tiles=TILES, ends=False,
               front=shopfront(X - 1, 38))                                                       # the shop, below
        h.hall(4, X - 2, 18, 18, 12, d0=8, z0=42, eave=4, lift=5, tiles=TILES, front=timber, snow=0.4)   # above
        for x0 in (2, X - 4):                                                                    # the yard's walls
            h.hall_d(x0, x0 + 4, 42, 26, 3, d0=29, eave=1, lift=0, ridge=1, snow=0, tiles=TILES, ends=False)
        h.hall(2, X, 24, 28, 12, d0=72, eave=3, lift=4, tiles=TILES)                            # the back house
        at = door(h, dx, 2)
        for x in (8, X - 6):
            lantern(h, x, 29, 1)
        if sign:
            h.sign(mid - (4 * len(sign) + 3) // 2, 24, sign, d0=2, ink='Y')
    else:
        h.hall_d(2, X, 84, 38, 9, d0=2, eave=3, lift=4, snow=0.2, tiles=TILES, face=lattice_side)        # the block
        B, tone = h.B, shopfront(X - 3, 38)
        for z in range(38):                                                                      # its shop front
            for x in range(4, X - 1):
                h.put(x + 2, B - z - 2, 'K' if z == 0 else tone(x - 4, 37 - z), B - 2)
        h.hall(0, X + 2, 3, 38, 2, d0=0, eave=2, lift=2, ridge=1, snow=0.5, tiles=TILES, ends=False, front=False)
        at = door(h, dx, 2)
        for x in (10, X - 8):
            lantern(h, x, 28, 0)
        if sign:
            h.sign(mid - (4 * len(sign) + 3) // 2, 24, sign, d0=2, ink='Y')
    return at


def design(lot_w=8, kind='shop', sign='TEA'):
    w, ch = size(lot_w)
    h = House(w + 1, ch, brick_tone)
    h.shift(16, 0)                                         # its eaves overhang its lot's west edge: a whole cell, so its cells are the town's
    at = draw(h, lot_w, kind, sign)
    h.shift(0, 0)
    return h.finish('shophouse', PAL, (at[0] + 16, at[1]), merge=MERGE)


if __name__ == '__main__':
    a = sys.argv[2:]
    json.dump(design(int(a[0]) if a else 8, a[1] if len(a) > 1 else 'shop', a[2] if len(a) > 2 else 'TEA'),
              open(sys.argv[1], 'w'))
