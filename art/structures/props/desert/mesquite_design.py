"""The dead mesquite, desert scenery: a low, wide, bare tree.

    python art/structures/props/desert/mesquite_design.py

32x32, two cells square, after a PixelLab draft
(pixellab-out/desert-mesquite/sprites/v1). In bark, as the wasteland's dead
tree is, but a mesquite's shape: a short trunk leaning off true and four heavy
bent limbs spreading wide rather than up, a short branch or two each, placed by
hand (OVERWORLD_STYLE.md: a tree's limbs are drawn, few and bold, never grown
into a thicket). Each limb a stroke tapering to its tip; the whole shaded by
form by its edges -- lit where a limb faces up and to the left, in shade where
it faces right or down, the trunk's foot in shade -- and one black line round it.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import save

W, H = 32, 32
# each a run of (x, y, thickness), trunk first; a branch starts on its limb
STROKES = [
    [(13, 29.5, 4.2), (14, 25, 3.4), (16, 20, 3.0)],                       # the trunk, leaning
    [(16, 20, 2.6), (12, 16.5, 2.0), (7, 14.5, 1.6), (3, 12.5, 1.2)],      # out low to the left
    [(7.5, 14.5, 1.3), (6, 10.5, 1.0)],
    [(16, 20, 2.4), (15, 14, 1.9), (13.5, 9, 1.5), (12.5, 4.5, 1.1)],      # up and a little left
    [(13.8, 9.5, 1.2), (10.5, 7, 1.0)],
    [(16.5, 20, 2.4), (19.5, 14.5, 1.9), (21.5, 9.5, 1.5), (23.5, 5.5, 1.1)],   # up and to the right
    [(21.3, 10, 1.2), (25, 8.5, 1.0)],
    [(17, 21.5, 2.3), (22, 18.5, 1.8), (26, 16.5, 1.4), (29, 14.5, 1.1)],  # out low to the right
    [(25.8, 16.8, 1.2), (27, 12.5, 1.0)],
]


def mask():
    m = [[False] * W for _ in range(H)]
    for run in STROKES:
        for (xa, ya, wa), (xb, yb, wb) in zip(run, run[1:]):
            for y in range(H):
                for x in range(W):
                    px, py = x + 0.5, y + 0.5
                    vx, vy = xb - xa, yb - ya
                    t = max(0.0, min(1.0, ((px - xa) * vx + (py - ya) * vy) / (vx * vx + vy * vy)))
                    r = (wa + (wb - wa) * t) / 2
                    if math.hypot(px - xa - vx * t, py - ya - vy * t) <= r:
                        m[y][x] = True
    return m


def shade(m):
    """Limbs two or three pixels thick are too thin to shade by their width, so by their
    edges: a pixel with nothing above it and to its left is lit, one with nothing to its
    right or below in shade, the mid tone between; the foot of the trunk in shade."""
    on = lambda x, y: 0 <= x < W and 0 <= y < H and m[y][x]
    g = [['.'] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if not m[y][x]:
                continue
            up_left = not on(x, y - 1) and not on(x - 1, y)
            if up_left and on(x + 1, y) and y < H - 6:
                c = 'l'
            elif not on(x + 1, y) and (on(x - 1, y) or not on(x, y + 1)):
                c = 'd'
            elif y >= H - 4:
                c = 'd'
            else:
                c = 'm'
            g[y][x] = c
    return g


def tree():
    g = shade(mask())
    ink = {(x, y) for y in range(H) for x in range(W) if g[y][x] != '.'}
    for x, y in list(ink):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in ink and 0 <= q[0] < W and 0 <= q[1] < H:
                g[q[1]][q[0]] = 'K'
    assert all(c == '.' for c in g[0] + [r[0] for r in g] + [r[W - 1] for r in g]), 'at the edge'
    return g


if __name__ == '__main__':
    save(tree(), os.path.join(HERE, 'mesquite.png'), 'bark')
