"""The desert signpost: a tall post with two arrow boards, pointing two ways.

    python art/structures/props/desert/signpost_design.py

16x32, one tile two cells tall. The town's signpost (town/sign_design.py)
carried out to a crossroads: its material (`sign`) and its way of drawing a
board -- black round the front, the cream face with a stroke of writing (an
arrow too small to keep the town board's frame of wood inside its line), the top receding a row back and the right edge a column back in
shade, the oblique view the houses are drawn in -- but two boards cut to arrows,
the upper pointing right and the lower left, on a post twice as tall, lit down
its left and in shade down its right. One black line round it all.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import save

W, H = 16, 32
SIGN = {'W': '94703d', 'M': 'e8e0c0', 'D': '633e1b'}    # wood, face, writing and shade (the town sign's PAL)
PX0, PX1 = 6, 9                                          # the post, outline to outline

# the two boards typed out (W wood, M face, D writing or shade, K line): the upper pointing right,
# the lower left -- the top of each a row back in wood, the lower's square end a column back in shade
BOARDS = {
    2:  "...WWWWWWWWW....",
    3:  "..KKKKKKKKKK....",
    4:  "..KMMMMMMMMMK...",
    5:  "..KMMMMMMMMMMK..",
    6:  "..KMDDDMDDDMMMK.",
    7:  "..KMMMMMMMMMMK..",
    8:  "..KMMMMMMMMMK...",
    9:  "..KKKKKKKKKK....",
    12: "....WWWWWWWWW...",
    13: "...KKKKKKKKKKD..",
    14: "...KMMMMMMMMKD..",
    15: "..KMMMMMMMMMKD..",
    16: ".KMMMDDDMDDMKD..",
    17: "..KMMMMMMMMMKD..",
    18: "...KMMMMMMMMKD..",
    19: "...KKKKKKKKKKK..",
}
assert all(len(r) == 16 for r in BOARDS.values())


def sign():
    g = [['.'] * W for _ in range(H)]
    for y in range(3, H - 1):                               # the post, behind the boards
        for x in range(PX0, PX1 + 1):
            g[y][x] = 'K' if x in (PX0, PX1) or y == H - 2 else 'W' if x == PX0 + 1 else 'D'
    for y, row in BOARDS.items():
        for x, c in enumerate(row):
            if c != '.':
                g[y][x] = c
    # the line round the whole, round what is coloured and not round a line already drawn
    ink = {(x, y) for y in range(H) for x in range(W) if g[y][x] not in '.K'}
    for x, y in list(ink):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in ink and 0 <= q[0] < W and 0 <= q[1] < H and g[q[1]][q[0]] == '.':
                g[q[1]][q[0]] = 'K'
    assert all(c == '.' for c in g[0] + [r[0] for r in g] + [r[W - 1] for r in g]), 'at the edge'
    return g


if __name__ == '__main__':
    save(sign(), os.path.join(HERE, 'signpost.png'), 'wood', SIGN)
