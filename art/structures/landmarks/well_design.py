"""The old well, a landmark of the grass and the meadow, laid out for tools/draw_views.py.

    python art/structures/landmarks/well_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/landmarks/well

A landmark is a small place out in the country with one cache to strike open
(src/tilemap.cpp, "Landmarks"; the user, 2026-10-13: "we need something so
whereever the player goes its fun and something new"). 48x32, three cells by
two: the well in the left two columns, its cache standing beside it in the
third (the chest, laid by the game: chest_design.py).

The well is built: stone in the entrances' courses and projection, round --
a drum with the dark of its shaft in its top, lit down its left and in shade
down its right as a round pillar is.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
from entrance_shapes import Grid, check, stand, outline, depth_layers

# tools/overworld_style.py MATERIALS: stone (lit, base, dark) and wood (light, mid, dark)
PAL = {'K': '000000', 'L': 'c6ccda', 'M': '9797aa', 'D': '595965',
       'w': '967448', 'x': '785830', 'y': '493712'}
E = "................"

# what is laid out: the well's block is cells (0..1, 0..1), its cache's cell (2, 1)
CACHE, STAMP_W = (2, 1), 3


def well():
    """A round shaft (the user, 2026-10-13: "well should be round shape and
    still oblique projection"), round as the round things of the coastal
    town's green are -- the fountain's basin, the gazebo: its top a level
    ellipse, seen from in front and above, and its wall the front of the drum
    under it. The lip is lit, the shaft dark with the far side of its wall in
    shade; the wall is stone in courses that ring the drum, lit down its left
    edge and in flat shade down its right, as a round pillar is."""
    import math
    CX, CY, A, B, H = 15.5, 13.5, 9.5, 4.5, 10               # the top's centre and radii, the wall's height
    HA, HB = 4.8, 1.9                                        # the shaft's
    inside = lambda x, y, cy, a, b: ((x - CX) / a) ** 2 + ((y - cy) / b) ** 2 <= 1.0
    front = lambda x: CY + B * math.sqrt(max(0.0, 1.0 - ((x - CX) / A) ** 2))    # the lip's front edge down column x
    g = Grid(32, 32)
    footy, foot = {}, set()
    for Y in range(32):
        for X in range(32):
            if inside(X, Y, CY, A, B):
                if inside(X, Y, CY, HA, HB):
                    g.put(X, Y, 'D' if not inside(X, Y - 1, CY, HA, HB) else 'K')
                else:
                    g.put(X, Y, 'L')
                footy[(X, Y)] = Y + H
            elif abs(X - CX) <= A and front(X) < Y <= front(X) + H:
                u, zz = (X - CX) / A, int(Y - front(X) - 0.5)       # across the drum -1..1; rows down from the lip
                if u > 0.5:
                    c = 'D'                                 # turned from the light: flat shade
                elif u < -0.8:
                    c = 'L'                                 # its lit left edge
                elif zz % 4 == 3:
                    c = 'D'                                 # the bed joint, a ring round the drum
                else:
                    along = int(A * math.asin(u) + 40 + (zz // 4 % 2) * 3)
                    c = 'D' if along % 6 == 5 else 'L' if zz % 4 == 0 else 'M'
                g.put(X, Y, c)
                footy[(X, Y)] = int(front(X) + H)
            if inside(X, Y, CY + H, A, B):                  # the ground it stands on
                foot.add((X, Y))
    # its windlass: a post at each end of the lip and the beam across them, in
    # wood's mid tone alone (the cells it stands in have the stone's lit, its
    # shade and black already: four colours a cell), a black line round it
    rim = int(CY) - 1
    left, right = int(CX - A) + 2, int(CX + A) - 2
    wood = {(x, y) for px in (left, right) for x in (px, px + 1) for y in range(rim - 9, rim + 1)}
    wood |= {(x, y) for x in range(left, right + 2) for y in (rim - 10, rim - 9)}
    for x, y in wood:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in wood and g.get(x + dx, y + dy) != '.':
                g.put(x + dx, y + dy, 'K')                  # against the stone; outline() lines the rest
    for x, y in wood:
        g.put(x, y, 'x')
        footy[(x, y)] = int(CY + H)
    outline(g)
    for x in (left, right + 1):
        g.put(x, rim - 10, 'K')                             # the beam's ends rounded (as on the sheet, 2026-10-14)
    near =lambda x, y: [footy[q] for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if q in footy]
    return stand(g, lambda x, y: footy.get((x, y), min(near(x, y) or [y])), foot)



def design():
    w = well()
    check(w, 'old well')
    rows = [a + E for a in w.rows()]
    return {'pal': PAL, 'view_w': 48, 'order': ['well'], 'views': {'well': rows},
            'depth': depth_layers(48, 32, [(0, 0, w)]), 'cache': CACHE, 'stamp_w': STAMP_W}


if __name__ == '__main__':
    d = design()
    if len(sys.argv) > 1:
        json.dump(d, open(sys.argv[1], 'w'))
    for r in d['views']['well']:
        print(r)
