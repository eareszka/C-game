"""The burnt wagon, a landmark of the wasteland, laid out for tools/draw_views.py.

    python art/structures/landmarks/wagon_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/landmarks/wagon

64x32: a cart burnt to its frame in the left three columns -- its bed of
boards, both sides burnt down to a ragged edge, its two wheels, its shaft
dropped to the ground -- in the houses' projection, in the dead trees' bark
(charred wood); its cache stands beside it in the fourth column (the chest,
laid by the game: chest_design.py).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landmark_shapes import obj, at, export, main, check, Grid
from entrance_shapes import Scene, rect, fill

PAL = {'K': '000000', 'L': '605028', 'M': '463422', 'D': '2d230c'}


def cart():
    sc = Scene(48, 32, 29)
    sc.break_off([0], 0, 47, 11, 1, 7)                      # the sides burnt down to a ragged edge
    sc.break_off([2], 0, 47, 18, 1, 8)
    sc.box(0, 4, 36, 9, 9, 6, 11, front='D')                # the far side, its inner face in shade
    sc.box(1, 4, 36, 1, 9, 5, 6, front='M')                 # the bed's floor, its boards' tops lit
    sc.box(2, 4, 36, 1, 1, 6, 11, front='M')                # the near side
    def wheel(cx):
        def draw(t):
            for y in range(19, 30):
                for x in range(cx - 5, cx + 6):
                    r = ((x - cx) ** 2 + (y - 24.5) ** 2) ** 0.5
                    if r <= 4.8:
                        t.put(x, y, 'L' if r < 1.2 else 'M' if r > 3.4 or x == cx or int(y) == 24 else 'D')
        return draw
    sc.flat(3, wheel(10), 0)
    sc.flat(4, wheel(31), 0)
    sc.flat(5, lambda t: fill(t, rect(2, 26, 5, 27), 'M') or fill(t, rect(2, 26, 5, 26), 'L'), 0)   # the shaft, dropped
    sc.ground(4, 36, 0, 9)
    g = sc.render()
    for y in range(g.h):                                    # the boards: the near side's, the floor's
        for x in range(g.w):
            if sc.pid[y][x] in (1, 2) and g.g[y][x] in 'ML' and (x + (y if sc.pid[y][x] == 1 else 0)) % 5 == 0:
                g.g[y][x] = 'D'
    check(g, 'burnt wagon')
    return g



CACHE, STAMP_W = (3, 1), 4


def design():
    return export('wagon', PAL, STAMP_W, 2, [(0, 0, cart())], CACHE, STAMP_W)


if __name__ == '__main__':
    main(design)
