"""The cattle skull, desert scenery: a longhorn's skull bleached on the sand.

    python art/structures/props/desert/cattle_skull_design.py

32x16, two cells across, after a PixelLab draft
(pixellab-out/desert-skull/sprites/v1): the face seen from in front, lying
flat, its horns swept out wide and turning up at the tips. In the desert's
bone, three tones and black: the face the bone white, in shade down its right
and at the muzzle, black sockets drooping to the nose, two black nostrils; the horns in the
two darker tones -- lit along their tops, in shade beneath -- so they read apart
from the face. One black line round it. It lies flat and is walked over.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import save

W, H, C = 32, 16, 15.5
FACE = {4: 4, 5: 5, 6: 5, 7: 5, 8: 5, 9: 4, 10: 3, 11: 3, 12: 3, 13: 2.5, 14: 2}   # row: half its width
SOCKETS = {(12, 7), (13, 7), (13, 8), (14, 8), (18, 7), (19, 7), (17, 8), (18, 8)}
NOSTRILS = {(14, 12), (17, 12)}
# the left horn, mirrored for the right: (x, y, tone) -- its top lit, its underside in shade
HORN = [(x, 5, 'n') for x in range(5, 11)] + [(x, 6, 'm') for x in range(5, 11)] + \
       [(4, 5, 'n'), (4, 6, 'm'), (3, 4, 'n'), (4, 4, 'm'), (3, 3, 'n'), (4, 3, 'm'), (3, 2, 'n')]


def skull():
    g = [['.'] * W for _ in range(H)]
    for y, hw in FACE.items():
        x0, x1 = int(C - hw + 0.5), int(C + hw + 0.5) - 1
        for x in range(x0, x1 + 1):
            g[y][x] = 'm' if x == x1 or (y >= 12 and x > C) else 'l'
    for x, y in SOCKETS:
        g[y][x] = 'K'
    for x, y in NOSTRILS:
        g[y][x] = 'K'
    for x, y, c in HORN:
        g[y][x] = c
        g[y][W - 1 - x] = c
    ink = {(x, y) for y in range(H) for x in range(W) if g[y][x] != '.'}
    for x, y in list(ink):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in ink and 0 <= q[0] < W and 0 <= q[1] < H:
                g[q[1]][q[0]] = 'K'
    assert all(c == '.' for c in g[0] + [r[0] for r in g] + [r[W - 1] for r in g]), 'at the edge'
    return g


if __name__ == '__main__':
    save(skull(), os.path.join(HERE, 'cattle_skull.png'), 'bone', {'l': 'e8e0c0', 'n': 'b2966a', 'm': '8d6b4f'})
