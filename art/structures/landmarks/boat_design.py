"""The wrecked boat, a landmark of the coast, laid out for tools/draw_views.py.

    python art/structures/landmarks/boat_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/landmarks/boat

64x32: a rowing boat cast up on the shore in the left three columns, square
stern to the left, bow up on the right, a hole stove in its near side; its
cache stands beside it in the fourth column (the chest, laid by the game:
chest_design.py). Wood (the wharf's planks): an object, one black line round
it, lit along the gunwale and high on the left, dark low and right.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landmark_shapes import obj, at, export, main, check, stand, Grid

PAL = {'K': '000000', 'l': '967448', 'm': '785830', 'd': '493712'}

X0, X1, BACK = 4, 42, 4          # the boat from stern to bow; how far up and right its far side lies


def boat():
    g = Grid(48, 32)
    top = lambda x: 15 - 6 * ((x - X0) / (X1 - X0)) ** 3                       # the sheer, rising to the bow
    bot = lambda x: 25 - 13 * ((x - X0) / (X1 - X0)) ** 4                    # the keel, curving up into the stem
    # the far side's rim and the inside of the boat, seen over the near gunwale
    for x in range(X0, X1 - 2):
        rim = int(round(top(x) - BACK + (0 if x + BACK <= X1 else 2)))
        fx = x + BACK
        g.put(fx, rim, 'l')
        for y in range(rim + 1, int(round(top(fx))) + 1):
            g.put(fx, y, 'm' if fx % 6 == 0 else 'd')                       # its ribs across the dark
    for x in range(X0, X1 + 1):                                              # the near side, over it
        t, b = int(round(top(x))), int(round(bot(x)))
        for y in range(t, b + 1):
            r = y - t
            c = 'l' if r == 0 else 'd' if r % 3 == 0 or y == b or (x > X1 - 8 and r > 1) else 'm'
            g.put(x, y, c)
    for x0, x1, r0 in ((15, 25, 4), (18, 22, 7)):                           # the hole stove in: planks gone, a rib across
        for x in range(x0, x1):
            for y in range(int(round(top(x))) + r0, int(round(top(x))) + r0 + 2):
                g.put(x, y, 'm' if x == 20 else 'K')
    from entrance_shapes import outline
    outline(g)
    check(g, 'wrecked boat')
    foot = {(x, y) for x in range(48) for y in range(32) if g.get(x, y) != '.' and y >= 22}
    return stand(g, lambda x, y: 27, foot)



CACHE, STAMP_W = (3, 1), 4


def design():
    return export('boat', PAL, STAMP_W, 2, [(0, 0, boat())], CACHE, STAMP_W)


if __name__ == '__main__':
    main(design)
