"""The agave, desert scenery: a low rosette of pointed leaves.

    python art/structures/props/desert/agave_design.py

32x32, two cells square, after a PixelLab draft
(pixellab-out/desert-agave/sprites/v1): thick sword-shaped leaves fanned from
one root, the upright ones behind, the low spreading ones in front. Each leaf a
part of its own, drawn back to front with a black line round it, so a nearer
leaf is parted from the one behind; lit down its left (a lying leaf, its top),
in shade down its right. The trees' greens, three tones and black.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import save

W, H = 32, 32
ROOT = (15.5, 29.5)
LEAVES = [           # degrees off upright (left negative), length, width at the root -- back to front
    (-18, 20, 6.5), (18, 19, 6.5), (0, 23, 7.0),
    (-45, 17, 6.0), (45, 17, 6.0),
    (-72, 15, 5.5), (72, 15, 5.5), (4, 13, 6.5),
]


def agave():
    g = [['.'] * W for _ in range(H)]
    rx, ry = ROOT
    for deg, length, width in LEAVES:
        a = math.radians(deg)
        ux, uy = math.sin(a), -math.cos(a)            # along the leaf, root to tip
        vx, vy = -uy, ux                              # across it, left edge to right
        body = set()
        tone = {}
        for y in range(H):
            for x in range(W):
                px, py = x + 0.5 - rx, y + 0.5 - ry
                t = (px * ux + py * uy) / length
                if not 0 <= t <= 1:
                    continue
                half = width / 2 * (1 - t) ** 0.85
                s = px * vx + py * vy
                if abs(s) > half:
                    continue
                body.add((x, y))
                side = s / max(half, 0.6)
                upper = -side if deg < -45 else side      # a lying leaf: its top looks to the light
                if deg > 45:
                    upper = side
                if upper > 0.4:
                    tone[(x, y)] = 'd'
                elif upper < -0.6 and t < 0.7:
                    tone[(x, y)] = 'l'
                else:
                    tone[(x, y)] = 'm'
        for x, y in body:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in body and 0 <= q[0] < W and 0 <= q[1] < H:
                    g[q[1]][q[0]] = 'K'
        for p in body:
            g[p[1]][p[0]] = tone[p]
    for x in range(W):                                 # the root's foot, in shade
        for y in (H - 4, H - 3):
            if g[y][x] in 'lm':
                g[y][x] = 'd'
    assert all(c == '.' for c in g[0] + [r[0] for r in g] + [r[W - 1] for r in g]), 'at the edge'
    return g


if __name__ == '__main__':
    save(agave(), os.path.join(HERE, 'agave.png'), 'foliage')
