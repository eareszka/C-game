"""The woodcutter's camp, a landmark of the forest, laid out for tools/draw_views.py.

    python art/structures/landmarks/camp_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/landmarks/camp

80x48: a woodshed in the left three columns -- the snow villages' log walls
(house_shapes.log_tone) under a roof of bark, its open front stacked with
cut logs, their ends to the viewer -- then a cold fire ringed with stones,
then its cache (the chest, laid by the game: chest_design.py). The shed is
built; the fire an object (the overworld bible).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landmark_shapes import obj, at, export, main, check, stand, Grid
from house_shapes import House, log_tone

PAL = {'K': '000000', 'M': '967448', 'B': '785830', 'S': '493712', 'R': '463422',
       'L': 'c6ccda', 'm': '9797aa', 'D': '595965'}


def shed():
    h = House(3, 3, log_tone)
    h.wing(8, 34, 9, 20, 10, side='S')
    yt = h.B - 20 + 1
    END = ["KSSSK", "SMMBS", "SMBBS", "SBBBS", "KSSSK"]     # a log's cut end: its bark round, its face lit high left
    for y in range(yt + 2, h.B):                            # the open front, stacked with log ends
        for x in range(10, 33):
            row = (y - yt - 2) // 5
            h.put(x, y, END[(y - yt - 2) % 5][(x - 10 + row % 2 * 2) % 5], h.B)
    g = h.grid('woodshed', merge=[('M', 'B')])            # under the eave, the logs' lit tops go before the roof
    for y in range(11, 30):                                 # the roof's left eave two in, a black edge again (the
        xs = [x for x in range(g.w) if g.g[y][x] != '.']    # sheet's hand edit, 2026-10-14)
        g.g[y][xs[0]] = g.g[y][xs[1]] = '.'
        g.g[y][xs[2]] = 'K'
    for x, y, c in ((13, 15, 'K'), (13, 16, 'K'), (13, 19, 'R'), (13, 20, 'R'),
                    (12, 21, 'R'), (13, 21, 'R'), (12, 22, 'R'), (13, 22, 'R')):
        g.g[y][x] = c                                       # and the eave's edge as it was drawn there
    return g


def fire():
    """Stones in a ring round the cold ashes, lying on the ground: each its
    own, lit high on the left, a black line round it, the far ones first."""
    g = Grid(19, 11)
    for y in range(4, 8):
        for x in range(6, 13):
            g.put(x, y, 'D' if (x * 3 + y) % 7 == 0 else 'K')         # ash and the char
    for i in sorted(range(7), key=lambda i: math.sin(i * 2 * math.pi / 7 + 0.4)):
        a = i * 2 * math.pi / 7 + 0.4
        cx, cy = 9 + 5.3 * math.cos(a), 5.5 + 2.6 * math.sin(a)
        own = {(x, y) for y in range(11) for x in range(19) if ((x - cx) / 2) ** 2 + ((y - cy) / 1.5) ** 2 <= 1}
        for x, y in {(x + i, y + j) for x, y in own for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))} - own:
            g.put(x, y, 'K')
        for x, y in own:
            u, v = x - cx, y - cy
            g.put(x, y, 'L' if u + v < -1.2 else 'D' if u + v > 0.8 else 'm')
    return stand(g, lambda x, y: y)



CACHE, STAMP_W = (4, 2), 5


def design():
    s, f = shed(), fire()
    check(f, 'camp fire')
    return export('camp', PAL, STAMP_W, 3, [(0, 0, s), (*at(f, 3, 2, lift=2), f)], CACHE, STAMP_W)


if __name__ == '__main__':
    main(design)
