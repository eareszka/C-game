"""The coastal town's bandstand, laid out for tools/draw_views.py.

    python art/structures/coast/gazebo_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/gazebo

The middle of the town's green: an eight-sided open pavilion, seen as the
houses are -- a boarded deck on a slatted skirt, a step up at its front, white
posts and a rail between them (open at the front), a pointed roof. What is
between the posts is clear, so the green shows through.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, stand, depth_layers, check, outline, rect, fill
from overworld_style import MATERIALS

# white paint and its shade; the roof's slate
PAL = dict(zip('BS', MATERIALS['white paint']['tones']), K='000000', R=MATERIALS['slate']['tones'][1])
POSTS = (8, 26, 51, 69)        # the four at the front, each three wide
BACK = (23, 55)                # the two behind, two wide, in shade
EAVE, DECK, SKIRT = 25, 60, 67


def design():
    g = Grid(80, 80)
    for x in BACK:                                           # behind: posts and their rail
        fill(g, rect(x, EAVE, x + 1, DECK), 'S')
    fill(g, rect(29, 50, 50, 50), 'S')                       # seen through the way in
    for y, (x0, x1) in zip(range(DECK, SKIRT), ((14, 65), (11, 68), (8, 71), (8, 71), (8, 71), (9, 70), (11, 68))):
        fill(g, rect(x0, y, x1, y), 'S' if y == DECK + 3 else 'B')     # the deck, a joint across its boards
    for y in range(SKIRT, SKIRT + 6):                        # its skirt of slats
        x0, x1 = (9, 70) if y < SKIRT + 4 else (11, 68)
        for x in range(x0, x1 + 1):
            g.put(x, y, 'K' if x % 4 == 1 or y == SKIRT else 'S')
    for y in range(SKIRT + 6, SKIRT + 11):                   # the step
        for x in range(31, 49):
            g.put(x, y, 'K' if y == SKIRT + 8 else 'B' if y < SKIRT + 8 else 'S')
    for x in POSTS:
        for y in range(EAVE, DECK + 4):
            for i in range(-1, 4):
                g.put(x + i, y, 'K' if i in (-1, 3) else 'S' if i == 2 else 'B')
    apex, half = 6, 37                                       # the roof: a ridge down to each post
    for y in range(apex, EAVE + 2):
        hw = min(half, 2 + (y - apex) * (half - 2) // (EAVE - 2 - apex))
        for x in range(40 - hw, 40 + hw + 1):
            rib = any(abs(x - (40 + (p + 1 - 40) * (y - apex) / (EAVE - apex))) < .6 for p in POSTS)
            g.put(x, y, 'K' if rib or y >= EAVE else 'R')
    fill(g, rect(39, 2, 41, 5), 'K')                         # its ball
    outline(g)
    for x0, x1 in ((12, 25), (55, 68)):                      # the rail either side of the way in, laid after
        for x in range(x0, x1 + 1):                          # the line so the green shows between its bars
            for y in range(49, DECK + 3):
                if y in (49, 50, 51) or x % 3 == 0:
                    g.put(x, y, 'B' if y == 50 else 'K')
    ink = {(x, y) for y in range(g.h) for x in range(g.w) if g.get(x, y) != '.'}
    stand(g, lambda x, y: SKIRT + 5, {p for p in ink if DECK <= p[1] <= SKIRT + 5})
    check(g, 'gazebo')
    return {'pal': PAL, 'view_w': g.w, 'order': ['gazebo'], 'views': {'gazebo': g.rows()},
            'depth': depth_layers(g.w, g.h, [(0, 0, g)])}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
