"""The stonehenge entrance, laid out for tools/draw_views.py.

    python art/structures/entrances/stonehenge_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/stonehenge

192x80, twelve cells by five, over a 2x2 stamp in the bottom two rows of the
middle two columns. The stones beside the stamp are solid and the rows above
are walked behind (gen_entrance_art.py works that out, as for a building).

A horseshoe of trilithons after the real one, opening toward the viewer:
grey uprights in the houses' oblique projection, each pair capped by a lintel,
curving round the back and the sides of a ring. In its open mouth, on the
stamp, the way down: a stone-framed opening in the ground with steps going
into a barrow, drawn square on as flat ground is. Old: one lintel has fallen
and lies on the ground, one upright is gone, and the stone is chipped and
cracked (entrance_shapes.weather). In the ruins' grey stone.
"""
import json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Scene, check, rect, fill, stair, weather, depth_layers

PAL = {'K': '000000', 'D': '595965', 'M': '9797aa', 'L': 'c6ccda'}
W, H, B = 192, 80, 77
# The ring's middle on the ground: across, and back. Across is 12 left of the
# stamp's middle (96): the oblique draws the back of the ring to the right, and
# this is what puts the pit -- which must stay on the stamp -- in the middle of
# the ring as it is seen.
CX, DC = 84, 10
R, RD = 54, 22                # its radius across, and back (the ring seen low)
TALL, THICK = 26, 3
R2, RD2 = 76, 30              # the outer ring of smaller stones
SMALL = 11


def henge():
    sc = Scene(W, H, B)
    # The trilithons, round the back and sides of the horseshoe (angle 0 to
    # the right, 90 straight back): each a pair of uprights side by side at
    # one depth under a lintel laid straight across them -- a lintel slanting
    # back between stones at two depths drew as a ramp. Of the pair at the
    # back one upright stands alone, its partner and their lintel fallen.
    # Placed by where each is SEEN, evenly round the pit's middle (96), and
    # set back by the ring's depth there: placed by ground position, the
    # oblique drew the right-hand pairs one on top of the other, since going
    # back moves a thing right.
    pid = 0
    for ang, whole in ((180, True), (135, True), (90, False), (45, True), (0, True)):
        d = round(DC + RD * math.sin(math.radians(ang)))
        seen = 96 - 28 * math.cos(math.radians(ang)) * 2      # 40 .. 152, even
        x = round(seen - d - (8 if whole else 2.5))
        if not whole:
            sc.box(pid, x, x + 5, d, d + THICK, 0, TALL, 'M'); pid += 1
            continue
        sc.box(pid, x, x + 5, d, d + THICK, 0, TALL, 'M'); pid += 1
        sc.box(pid, x + 11, x + 16, d, d + THICK, 0, TALL, 'M'); pid += 1
        sc.box(pid, x - 1, x + 17, d, d + THICK, TALL, TALL + 4, 'M'); pid += 1
    # a fallen lintel, lying on the ground on the left
    sc.box(pid, 32, 48, 2, 5, 0, 4, 'M'); pid += 1
    # The outer ring: smaller stones all round the back and sides, as far
    # forward as the ground in front of the way down goes. A few are gone.
    for k, ang in enumerate(range(200, -26, -14)):
        if k in (3, 8, 12):
            continue
        a = math.radians(ang)
        x = round(CX + R2 * math.cos(a) - 2)
        d = round(DC + RD2 * math.sin(a))
        if d < 0:
            continue
        sc.box(pid, x, x + 4, d, d + 2, 0, SMALL - (k % 3), 'M')
        pid += 1

    # The way down: a pit cut into the ground in the middle of the ring, in
    # the same oblique as everything standing -- its opening a parallelogram,
    # its far edge further back and so higher and to the right -- rimmed with
    # low kerb stones. Inside, the far wall catches the light under its edge,
    # the left wall is in shade, and steps go down, darker the deeper.
    X0, X1, D0, D1 = 76, 98, 2, 16
    sc.box(pid, X0 - 2, X1 + 2, D0 - 2, D0 - 1, 0, 1, 'M'); pid += 1   # front kerb
    sc.box(pid, X0 - 2, X1 + 2, D1 + 1, D1 + 2, 0, 1, 'M'); pid += 1   # back kerb
    sc.box(pid, X0 - 2, X0 - 1, D0, D1, 0, 1, 'M'); pid += 1           # left kerb
    sc.box(pid, X1 + 1, X1 + 2, D0, D1, 0, 1, 'M'); pid += 1           # right kerb

    def pit(g):
        for d in range(D0, D1 + 1):
            y = B - d
            for x in range(X0 + d, X1 + d + 1):
                c = 'K'
                if y <= B - D1 + 2:
                    c = 'M'                                # the far wall, lit
                elif x <= X0 + d + 1:
                    c = 'D'                                # the left wall, in shade
                g.put(x, y, c)
        for y, c in ((B - D0, 'L'), (B - D0 - 3, 'D')):
            d = B - y                                      # treads, nearest lightest
            for x in range(X0 + d + 2, X1 + d + 1):
                g.put(x, y, c)
    sc.flat(pid, pit, (D0 + D1) / 2, opening='ground')
    g = sc.render()
    weather(g, 77, 'M', 'D', chips=14, cracks=18, keep=[(X0 - 4, B - D1 - 6, X1 + D1 + 4, B + 2)])
    return g


def design():
    g = henge()
    check(g, 'stonehenge', objects=True)
    return {'pal': PAL, 'view_w': W, 'order': ['henge'], 'views': {'henge': g.rows()},
            'depth': depth_layers(W, H, [(0, 0, g)])}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
