"""The coastal town's lighthouse, laid out for tools/draw_views.py.

    python art/structures/coast/lighthouse_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/lighthouse

A landmark, not a way in (the user, 2026-10-12, over a short harbour light
and a tower with a keeper's house): a tall white tower tapering to its
gallery, a red band round its middle, a glazed lantern and a cap. Round, so
it is shaded as the bible's pillar is -- its paint, shade down its right,
deeper at the edge -- and the band lies on whole tile rows, so the red and
the white never share a tile.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, stand, depth_layers, check
from overworld_style import MATERIALS

# white paint lit to dark; the band and its shade; the lantern's glass and its lamp; the cap
PAL = dict(zip('MGH', MATERIALS['white paint']['tones']), K='000000', **dict(zip('rq', MATERIALS['red paint']['tones'])),
           U=MATERIALS['lantern glass']['tones'][0], Y=MATERIALS['lamplight']['tones'][0], C=MATERIALS['slate']['tones'][1])
CW, CH = 6, 11
CX, TOP = 47, 64               # the tower's middle, and its top: a tile row, under the gallery
HW0, HW1 = 10, 15              # half across at its top and at its foot
BAND = (96, 127)               # two tile rows
FOOT = 10                      # rows of ground it stands on


def design():
    g = Grid(CW * 16, CH * 16)
    base = g.h - 1
    put = g.put
    for y in range(TOP, base + 1):                           # the tower
        hw = int(round(HW0 + (HW1 - HW0) * (y - TOP) / (base - TOP)))
        inset = {0: 3, 1: 1}.get(base - y, 0)                # its round foot
        x0, x1 = CX - hw + inset, CX + hw - inset
        for x in range(x0, x1 + 1):
            dark = x - x0 >= .6 * (x1 - x0)
            if BAND[0] <= y <= BAND[1]:
                put(x, y, 'q' if dark else 'r')
            else:
                put(x, y, 'H' if x > x1 - 3 else 'G' if dark else 'M')
    for y in range(base - 15, base + 1):                     # its door: planks under a round head
        for x in range(CX - 6, CX + 3):
            lx, ly = x - (CX - 6), y - (base - 15)
            if not (ly == 0 and lx in (0, 8)):
                put(x, y, 'K' if lx in (0, 8) or ly == 0 or lx % 3 == 1 else 'H')
    for y in range(TOP + 14, TOP + 20):                      # a slit window
        for x in (CX - 4, CX - 3):
            put(x, y, 'K')
    for i in range(3):                                       # the gallery's deck, on a bracket
        for x in range(CX - HW0 - 3 + 2 * (i == 0), CX + HW0 + 4 - 2 * (i == 0)):
            put(x, TOP - 1 - i, 'K')
    for y in range(TOP - 25, TOP - 3):                       # the lantern: glass in black bars, the lamp in it
        for x in range(CX - 6, CX + 7):
            lx = x - (CX - 6)
            bar = lx % 4 == 0 or y in (TOP - 25, TOP - 14)
            put(x, y, 'K' if bar else 'Y' if 4 < lx < 8 and TOP - 21 < y < TOP - 8 else 'U')
    for y in range(TOP - 9, TOP - 3):                        # the rail before it
        for x in range(CX - HW0 - 3, CX + HW0 + 4):
            if y == TOP - 9 or (x - CX) % 3 == 0:
                put(x, y, 'K')
    for i, hw in enumerate((8, 8, 8, 7, 7, 6, 5, 4, 2)):     # the cap
        for x in range(CX - hw, CX + hw + 1):
            put(x, TOP - 26 - i, 'K' if i == 0 else 'C')
    for y in range(TOP - 40, TOP - 34):                      # its ball
        for x in range(CX - 1, CX + 2):
            if x == CX or y < TOP - 37:
                put(x, y, 'K')
    ink = lambda x, y: g.get(x, y) != '.'                    # a black line round it, inside its edge
    for x, y in [(x, y) for y in range(g.h) for x in range(g.w) if ink(x, y) and not all(
            ink(x + i, y + j) for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))]:
        put(x, y, 'K')
    stand(g, lambda x, y: base, {(x, y) for y in range(base - FOOT + 1, base + 1) for x in range(g.w) if ink(x, y)})
    check(g, 'lighthouse')
    return {'pal': PAL, 'view_w': g.w, 'order': ['lighthouse'], 'views': {'lighthouse': g.rows()},
            'depth': depth_layers(g.w, g.h, [(0, 0, g)])}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
