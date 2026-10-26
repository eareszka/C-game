"""The butte, desert scenery: a chunk of mesa standing alone on the sand.

    python art/structures/props/desert/mesa_design.py

64x48, four cells by three, after a PixelLab draft
(pixellab-out/desert-mesa/sprites/v2): a flat cap of rock on sheer walls that
flare at the foot into a skirt of fallen rock. In the houses' projection
(a footprint x across and d back, z up), in the cliffs' rock the spire and
boulders are: the cap the lightest tone, flat -- the top plane; the walls the
mid tone where they look south, the dark where they turn east -- the side
turned away; strata in the dark across the walls and a few black cracks down
them. Three tones and black, the objects' rule.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from entrance_shapes import Scene, check
from prop_paint import save

W, H, BASE = 64, 48, 44
CX, CD = 24.0, 7.0                 # the footprint's middle: x across, d back
RX, RD = 11.0, 4.0                 # the walls' footprint
TALUS, WALL, CAP = 10, 29, 30       # the skirt's top, the walls' top, the cap's top (z)
FLARE = 1.5                        # the skirt's foot, as a share of the walls' footprint
STRATA = (15, 22)                   # rows of z laid in the dark across the walls
CRACKS = (-2.05, -0.95)  # where a crack runs down the walls (angle round)


def wobble(t):
    """The walls are not turned on a lathe: a squared footprint, wandering a little round."""
    c, s = abs(math.cos(t)), abs(math.sin(t))
    square = 1 / (c ** 3.5 + s ** 3.5) ** (1 / 3.5)
    return square * (0.9 + 0.06 * math.sin(3 * t + 0.6) + 0.04 * math.sin(7 * t + 1.3))


def inset(z):
    """Each stratum steps the wall in: the rock above it a little narrower, a ledge on it."""
    return 1 - 0.07 * sum(z > q for q in STRATA)


def butte():
    sc = Scene(W, H, BASE)
    step = 0.04
    walls, skirt, cap = [], [], []
    t = 0.0
    while t < 2 * math.pi:
        c, s, k = math.cos(t), math.sin(t), wobble(t)
        nx = c / RX                                       # which way the wall looks: east, or south
        east = nx / math.hypot(nx, s / RD) > 0.55
        z = 0.0
        while z <= CAP:
            if z <= TALUS:
                r = k * (1 + (FLARE - 1) * (1 - z / TALUS) ** 2)      # concave: it runs up into the wall
                tone = 'D' if east else 'M'
                skirt.append((CX + r * RX * c, CD + r * RD * s, z, tone))
            elif z <= WALL:
                tone = 'D' if east or any(-0.6 < z - q < 0.2 for q in STRATA) else 'M'
                if any(abs(z - q) < 0.13 for q in STRATA):           # the ledge, lit
                    for f in (inset(z + 1), (inset(z + 1) + inset(z - 1)) / 2, inset(z - 1)):
                        walls.append((CX + k * f * RX * c, CD + k * f * RD * s, z + 0.3, 'L' if not east else 'M'))
                if any(abs(t - (q % (2 * math.pi))) < 0.03 for q in CRACKS) and TALUS - 2 < z < WALL - 1:
                    tone = 'K'
                walls.append((CX + k * inset(z) * RX * c, CD + k * inset(z) * RD * s, z, tone))
            z += 0.25
        t += step
    # the cap: flat, a little proud of the walls
    for i in range(-30, 31):
        for j in range(-30, 31):
            u, v = i / 30 * 1.05, j / 30 * 1.05
            ang = math.atan2(v, u)
            if math.hypot(u, v) <= wobble(ang if ang >= 0 else ang + 2 * math.pi) * 1.04:
                cap.append((CX + u * RX * inset(CAP), CD + v * RD * inset(CAP), CAP, 'L'))
    sc.points(1, skirt)                                   # one piece with the walls: no line between
    sc.points(1, walls)
    sc.points(2, cap, nearer=0.01)
    # boulders fallen from the walls, lying at the foot
    for bx, bd, br in ((CX - RX * 1.25, -1.5, 2.2), (CX + RX * 1.45, -1.2, 1.9)):
        pts = []
        for i in range(-12, 13):
            for j in range(-12, 13):
                u, v = i / 12, j / 12
                if u * u + v * v <= 1:
                    zz = br * 0.9 * (1 - u * u - v * v) ** 0.5
                    pts.append((bx + u * br, bd + v * br * 0.6, zz, 'L' if u + v < -0.6 and zz > br * 0.4 else 'D' if u > 0.35 else 'M'))
        sc.points(5 + len(pts) % 7, pts)
    sc.ground(int(CX - RX * FLARE), int(CX + RX * FLARE), 0, int(CD + RD))
    g = sc.render()
    check(g, 'butte', objects=True)
    return g


if __name__ == '__main__':
    save(butte().g, os.path.join(HERE, 'mesa.png'), 'rock', {'L': 'b29e5c', 'M': '887000', 'D': '493712'})
