"""The traveller's cairn, a landmark of the snow, laid out for tools/draw_views.py.

    python art/structures/landmarks/cairn_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/landmarks/cairn

48x32: a pile of stones stacked to a point in the left two columns, snow
lying on each stone's top; its cache stands at its foot in the third (the
chest, laid by the game: chest_design.py). An object (the overworld bible):
rock in its base and shade and black, no lit tone (the cliffs' rule), the
snow on top.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landmark_shapes import Grid, obj, at, export, main, stand, check

PAL = {'K': '000000', 'M': '9797aa', 'D': '595965', 'S': 'fcfcfc'}

# the stones from the ground up, each resting on those before it and drawn
# over them: (centre x, centre y, half width, half height)
STONES = [(8, 24.5, 4.5, 3.5), (24, 24.5, 4.5, 3.5), (16, 25, 5, 3.5), (12, 18.5, 4.5, 3), (20, 18.5, 4.5, 3),
          (16, 13, 5, 3), (15.5, 8, 3.5, 2.5)]


def cairn():
    """Each stone an ellipse, laid over those it rests on, a black line round
    each: base on its top half and left, shade low on its right, snow in a
    cap on its top rows -- hidden where a stone above sits on it."""
    g = Grid(32, 32)
    for cx, cy, a, b in STONES:
        own = {(x, y) for y in range(32) for x in range(32) if ((x - cx) / a) ** 2 + ((y - cy) / b) ** 2 <= 1}
        ring = {(x + i, y + j) for x, y in own for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))} - own
        for x, y in ring:
            g.put(x, y, 'K')
        for x, y in own:
            u, v = (x - cx) / a, (y - cy) / b
            g.put(x, y, 'S' if v < -0.45 else 'D' if u + v > 0.55 else 'M')
    for x, y in [(x, y) for y in range(32) for x in range(32) if g.get(x, y) == 'K']:   # a line's spur out of the pile
        if sum(g.get(x + i, y + j) != '.' for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))) <= 1:
            g.put(x, y, '.')
    for x, y in [(x, y) for y in range(32) for x in range(32) if g.get(x, y) not in '.K']:   # and closed where that opened it
        for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if g.get(x + i, y + j) == '.':
                g.put(x + i, y + j, 'K')
    check(g, 'cairn')
    foot = {(x, y) for y in range(26, 29) for x in range(32) if g.get(x, y) != '.'}
    return stand(g, lambda x, y: 28, foot)



CACHE, STAMP_W = (2, 1), 3


def design():
    return export('cairn', PAL, STAMP_W, 2, [(0, 2, cairn())], CACHE, STAMP_W)


if __name__ == '__main__':
    main(design)
