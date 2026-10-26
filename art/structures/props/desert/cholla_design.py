"""The cholla, desert scenery: chains of short joints branching from a stub.

    python art/structures/props/desert/cholla_design.py

32x32, two cells square, after a PixelLab draft
(pixellab-out/desert-cholla/sprites/v4; the other three drew saguaros). A
dark stub of trunk and joints set end to end up three branches and two low
ones, each joint a part of its own (tools/prop_paint.py blobs) parted from the
one behind by the black line, in the trees' greens.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import blobs, save

JOINTS = [           # cx, cy, rx, ry, turn -- back to front: the tips first
    (7, 6, 1.7, 2.5, -5), (25, 7, 1.7, 2.5, 5), (16, 3, 1.6, 2.2, 0), (21, 11, 1.5, 2.2, -35),
    (8, 12, 1.8, 2.8, -20), (24, 13, 1.8, 2.8, 20), (16, 8, 1.8, 2.7, 0),
    (5, 17, 1.6, 2.3, -70),
    (12, 17, 1.8, 2.8, -40), (20, 18, 1.8, 2.8, 40), (16, 14, 2.0, 3.0, 0),
]

def cholla():
    g = blobs(32, 32, JOINTS)
    for y in range(18, 30):                   # the trunk, dark, under the joints
        for x in range(14, 19):
            if g[y][x] in '.K' or y > 19:
                g[y][x] = 'K' if x in (14, 18) or y == 29 else 'd'
    return g

if __name__ == '__main__':
    save(cholla(), os.path.join(HERE, 'cholla.png'), 'foliage')
