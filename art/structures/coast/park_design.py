"""The things on the coastal town's green, laid out for tools/draw_views.py.

    python art/structures/coast/park_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/park

A strip three cells tall: a bench, a street lamp (three cells), a fountain
(three by three), a picket fence that joins itself left and right, a flower
bed. Each is a black line round it, three tones and black. The bench is built
in the houses' projection -- its front square on, its ends going back up and
to the right, tops lightest, the side turned away darkest (entrance_shapes.
Scene); the user, 2026-10-13: "bench needs to be oblique projection, street
lamp needs to be taller, fountain needs to be bigger". The fountain is parts
laid back to front, each with its own line, so the nearer interrupts the
farther: a basin, the pedestal rising out of its water, a bowl, the jet.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, stand, depth_layers, check, Scene
from overworld_style import MATERIALS

# a bench's wood; the lamp's iron and its light; white paint; the fountain's stone and water; leaves and flowers
PAL = dict(zip('Wwv', MATERIALS['wood']['tones']), K='000000', I=MATERIALS['slate']['tones'][1],
           Y=MATERIALS['lamplight']['tones'][0], B=MATERIALS['white paint']['tones'][0],
           **dict(zip('SM', MATERIALS['stone']['tones'])), U=MATERIALS['water']['tones'][0],    # S is the paint's shade too
           **dict(zip('Gg', MATERIALS['foliage']['tones'])), P=MATERIALS['meadow']['tones'][1])


def bench():
    """Two legs, a seat, a back along its rear edge; 16x16, standing on row 14
    so its line fits under it."""
    sc = Scene(16, 16, base=14)
    sc.box(1, 2, 3, 0, 3, 0, 4, front='M')
    sc.box(1, 9, 10, 0, 3, 0, 4, front='M')
    sc.box(2, 2, 11, 0, 3, 4, 6, front='M')
    sc.box(3, 2, 11, 3, 3, 6, 10, front='M')
    g = sc.render()
    tone = {'L': 'W', 'M': 'w', 'D': 'v'}
    return [''.join(tone.get(c, c) for c in r) for r in g.rows()]


LAMP = (['......KKKK......',
         '.....KIIIIK.....',
         '....KKKKKKKK....',
         '....KYYKKYYK....',
         '....KYYKKYYK....',
         '....KYYKKYYK....',
         '....KYYKKYYK....',
         '.....KYYYYK.....',
         '.....KKKKKK.....'] + ['......KIIK......'] * 33 +
        ['.....KIIIIK.....',
         '....KIIIIIIK....',
         '....KKKKKKKK....'])
FENCE = ['..K.......K.....',
         '.KBK.....KBK....',
         'KBBBK...KBBBK...',
         'KBBSKKKKKBBSKKKK',
         'KBBSKBBBKBBSKBBB',
         'KBBSKKKKKBBSKKKK',
         'KBBSK...KBBSK...',
         'KBBSK...KBBSK...',
         'KBBSKKKKKBBSKKKK',
         'KBBSKBBBKBBSKBBB',
         'KBBSKKKKKBBSKKKK',
         'KBBSK...KBBSK...',
         'KKKKK...KKKKK...']
FLOWERS = ['....KKKKKKKK....',
           '..KKGGPPGGGGKK..',
           '.KGGGGPPGGPPGGK.',
           '.KGPPGGGGGPPGGK.',
           '.KGPPGGgGGGGGGK.',
           '.KGGGGgggGGPPGK.',
           '.KgGGggggggPPgK.',
           '..KKggggggggKK..',
           '....KKKKKKKK....']


def ellipse(cx, cy, rx, ry, w=48, h=40):
    return {(x, y) for y in range(h) for x in range(w) if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1}


def fountain():
    """48x40: parts back to front, each lined, the nearer over the farther."""
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    parts = []
    body = ellipse(24, 33, 22, 6)
    parts.append({p: 'S' if p[1] < 32 else 'M' for p in body})                   # the basin: lit rim, its wall
    parts.append({(x, y): 'S' if x == 21 else 'M' for y in range(14, 31) for x in range(21, 27)})   # the pedestal
    parts.append({p: 'U' for p in ellipse(24, 29.5, 19, 3)})                     # its water, the pedestal rising out of it
    bowl = ellipse(24, 15, 11, 3.5)
    parts.append({p: 'S' if p[1] < 15 else 'M' for p in bowl})                   # the bowl
    parts.append({p: 'U' for p in ellipse(24, 14, 9, 2)})                        # its water
    parts.append({(x, y): 'U' for y in range(4, 13) for x in (23, 24)})          # the jet
    out = {}
    for part in parts:
        for (x, y), c in part.items():
            out[(x, y)] = c
            for dx, dy in N4:
                if (x + dx, y + dy) not in part:
                    out.setdefault((x + dx, y + dy), 'K') if (x + dx, y + dy) not in out else None
        for (x, y) in list(part):                                               # its line, over what is behind
            for dx, dy in N4:
                q = (x + dx, y + dy)
                if q not in part:
                    out[q] = 'K'
    rows = [''.join(out.get((x, y), '.') for x in range(48)) for y in range(40)]
    return rows


# (its rows, the cell it starts in): each stands on the strip's bottom row
CELLS, H = 7, 48
THINGS = [(bench(), 0), (LAMP, 1), (fountain(), 2), (FENCE, 5), (FLOWERS, 6)]


def design():
    g = Grid(CELLS * 16, H)
    for rows, cell in THINGS:
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                g.put(cell * 16 + x, H - len(rows) + y, c)
    ink = {(x, y) for y in range(H) for x in range(g.w) if g.get(x, y) != '.'}
    stand(g, lambda x, y: H - 1, {p for p in ink if p[1] >= H - 3})
    check(g, 'park', objects=True)
    return {'pal': PAL, 'view_w': g.w, 'order': ['park'], 'views': {'park': g.rows()},
            'depth': depth_layers(g.w, g.h, [(0, 0, g)])}


if __name__ == '__main__':
    d = design()
    json.dump(d, open(sys.argv[1], 'w'))
    for r in d['views']['park']:
        print(r)
