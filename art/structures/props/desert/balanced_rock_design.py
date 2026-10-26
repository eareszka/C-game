"""The balanced rock, desert scenery: a boulder left standing on a stem of rock.

    python art/structures/props/desert/balanced_rock_design.py

48x48, three cells square, after a PixelLab draft
(pixellab-out/desert-balanced/sprites/v2): a stout pedestal flared at its foot
and worn thin at its neck, and on it a wide, flattened boulder sitting a little
off true to the right. Two pieces of the cliffs' rock, parted by the black line,
drawn as solids in the houses' projection (tools/prop_paint.py voxels). The
pedestal takes the three planes -- tops lit, south faces mid, east faces dark --
its neck in the boulder's shadow; the boulder is round, so it is shaded by its
curve instead: lit on its crown, dark down its east side and underneath.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import voxels, save
from entrance_shapes import check

W, H, BASE = 48, 48, 44
PX, PD, PH = 19.0, 4.0, 21          # the pedestal: middle x, middle d, height
BX, BD, BZ = 21.0, 4.0, 27.5        # the boulder's middle
BA, BB, BC = 12.5, 5.5, 7.0         # its half-sizes: across, back, up


def stem(z):
    """The pedestal's radius at height z: flared at the foot, thin at the neck."""
    r = 7.0 - 3.6 * (z / PH)
    if z < 4:
        r += 3.0 * (1 - z / 4) ** 1.5
    return r


def solid():
    cells, part = set(), {}
    for z in range(0, PH + 1):
        r = stem(z)
        for x in range(int(PX - 12), int(PX + 13)):
            for d in range(0, 10):
                if ((x + 0.5 - PX) / r) ** 2 + ((d + 0.5 - PD) / (r * 0.55)) ** 2 <= 1:
                    cells.add((x, d, z)); part[(x, d, z)] = 0
    for z in range(int(BZ - BC), int(BZ + BC) + 1):
        for x in range(int(BX - BA) - 1, int(BX + BA) + 2):
            for d in range(-2, 12):
                if ((x + 0.5 - BX) / BA) ** 2 + ((d + 0.5 - BD) / BB) ** 2 + ((z + 0.5 - BZ) / BC) ** 2 <= 1:
                    cells.add((x, d, z)); part[(x, d, z)] = 1
    return cells, part


CELLS, PART = solid()


def tone(x, d, z, face):
    if PART[(x, d, z)] == 0:
        east = x + 0.5 - PX > stem(z) * 0.45
        if z >= PH - 3 or east:
            return 'D'                                                # the neck in the boulder's shadow, the east
        return 'M'                                                    # the stem narrowing: wall, not a top
    nx, nd, nz = (x + 0.5 - BX) / BA ** 2, (d + 0.5 - BD) / BB ** 2, (z + 0.5 - BZ) / BC ** 2
    n = math.sqrt(nx * nx + nd * nd + nz * nz)
    nx, nd, nz = nx / n, nd / n, nz / n
    if nz > 0.75 and nx < 0.35:
        return 'L'                                                    # the crown
    if nx > 0.5 or nz < -0.2:
        return 'D'                                                    # the east side, and underneath
    return 'M'


if __name__ == '__main__':
    g = voxels(W, H, BASE, CELLS, tone, lambda x, d, z: PART[(x, d, z)])
    check(g, 'balanced rock')
    save(g.g, os.path.join(HERE, 'balanced_rock.png'), 'rock', {'L': 'b29e5c', 'M': '887000', 'D': '493712'})
