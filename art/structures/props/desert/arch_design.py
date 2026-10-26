"""The natural arch, desert scenery: a span of rock on two legs.

    python art/structures/props/desert/arch_design.py

64x48, four cells by three, after a PixelLab draft
(pixellab-out/desert-arch/sprites/v1): a thick leg on the right, a thinner
one on the left leaning in, and a heavy span between them, thickest over the
right leg, the opening under it big enough to see the sand through. A solid of
unit cells drawn in the houses' projection (tools/prop_paint.py voxels): tops
lit, the faces looking south the mid tone, those turned east the dark, a
stratum in the dark across the legs. The cliffs' rock, three tones and black.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import voxels, save
from entrance_shapes import check

W, H, BASE = 64, 48, 44
X0, X1 = 4, 48                     # the arch's feet, outside to outside
DEPTH = 5                          # how far back it runs
OPEN = (25.0, 14.5, 26.0)          # the opening: its middle x, half its width, its height
STRATA = (7, 8)


def solid():
    cells = set()
    ox, ow, oh = OPEN
    for x in range(X0, X1 + 1):
        t = (x - X0) / (X1 - X0)
        top = 22 + 12 * math.sin(math.pi * t ** 0.9) + 1.5 * math.sin(9 * t)   # the span's crown, high on the right
        for z in range(0, int(top) + 1):
            # the legs taper as they rise: the outside faces lean in
            lean_l = X0 + z * 0.3
            lean_r = X1 - max(0, z - 4) * 0.25
            if not (lean_l <= x <= lean_r):
                continue
            u = (x - ox) / ow
            if abs(u) < 1 and z < oh * (1 - u * u) ** 0.5 * (1 + 0.15 * u):    # the opening, a lopsided arch
                continue
            for d in range(DEPTH):
                cells.add((x, d, z))
    return cells


CELLS = solid()


def tone(x, d, z, face):
    # where the crown drops a pixel the step is part of the top, not a wall turned east
    if face == 'east' and (x + 1, d, z - 1) in CELLS and (x, d, z + 1) not in CELLS:
        return 'L'
    if face == 'south' and z in STRATA:
        return 'D'
    return None


if __name__ == '__main__':
    g = voxels(W, H, BASE, CELLS, tone)
    check(g, 'arch')
    save(g.g, os.path.join(HERE, 'arch.png'), 'rock', {'L': 'b29e5c', 'M': '887000', 'D': '493712'})
