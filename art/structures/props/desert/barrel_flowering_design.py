"""The flowering barrel cactus, desert scenery.

    python art/structures/props/desert/barrel_flowering_design.py

16x32, one tile, standing in the bottom cell as the old strip's things did.
After a PixelLab draft (pixellab-out/desert-barrel/sprites/v1): a squat barrel
whose ribs bow out and close in at the crown, and a ring of blooms on top.
Three colours and black: the barrel in the trees' mid and dark greens -- the
dark down its right and low, ribs of it across the lit side -- and the blooms
in the meadow's flower pink, which takes the light tone's place: the crown is
the brightest thing on it, high and to the left of the shade.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import save

W, H = 16, 32
CX, CY, RX, RY = 7.5, 23.0, 5.6, 6.6        # the barrel, its foot on row 29
RIBS = (-0.45, 0.15)                         # where each rib crosses the barrel, -1 left to 1 right
BLOOMS = [(3, 15), (6, 14), (9, 15)]         # each bloom's top-left: three across, two down, its top corners off


def barrel():
    g = [['.'] * W for _ in range(H)]
    body = set()
    for y in range(H):
        for x in range(W):
            u, v = (x - CX) / RX, (y - CY) / RY
            if u * u + v * v <= 1.0 and y <= 29:
                body.add((x, y))
    for x, y in body:
        v = (y - CY) / RY
        half = RX * max(0.05, 1 - v * v) ** 0.5
        u = (x - CX) / half                                # across the barrel at this row
        if u > 0.62 or y >= 28:
            c = 'd'                                         # the side turned away, and low
        elif any(abs(u - r) * half < 0.5 for r in RIBS) and abs(v) < 0.85:
            c = 'd'                                         # a rib
        else:
            c = 'm'
        g[y][x] = c
    for bx, by in BLOOMS:
        for y in (by, by + 1):
            for x in (bx, bx + 1, bx + 2):
                if y == by and x != bx + 1:
                    continue
                g[y][x] = 'p'
                body.add((x, y))
    for x, y in list(body):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in body and 0 <= q[0] < W and 0 <= q[1] < H:
                g[q[1]][q[0]] = 'K'
    return g


if __name__ == '__main__':
    save(barrel(), os.path.join(HERE, 'barrel_flowering.png'), 'foliage', {'p': 'fc74b4'})
