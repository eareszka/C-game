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
           **dict(zip('GgH', MATERIALS['foliage']['tones'])), P=MATERIALS['meadow']['tones'][1],
           J=MATERIALS['slate']['tones'][1], D=MATERIALS['stone']['tones'][2], X=MATERIALS['water']['tones'][1])


def bench():
    """A slatted park bench (after a PixelLab draft, pixellab-out/old-park-bench): two end
    frames standing as arms, a seat of two slats and a back of two, the slats' gaps in
    black; 16x16, standing on row 14 so its line fits under it."""
    sc = Scene(16, 16, base=14)
    sc.box(1, 2, 2, 2, 2, 0, 10, front='M')                        # the back posts
    sc.box(2, 12, 12, 2, 2, 0, 10, front='M')
    sc.box(3, 3, 11, 2, 2, 8, 9, front='M')                        # the back's upper slat
    sc.box(4, 3, 11, 2, 2, 5, 6, front='M')                        # its lower slat
    sc.box(5, 2, 12, 1, 1, 3, 4, front='M')                        # the seat's back slat
    sc.box(6, 2, 12, 0, 0, 3, 4, front='M')                        # its front slat
    sc.box(7, 2, 2, 0, 0, 0, 2, front='M')                         # the front legs
    sc.box(8, 12, 12, 0, 0, 0, 2, front='M')
    g = sc.render()
    tone = {'L': 'W', 'M': 'w', 'D': 'v'}
    return [''.join(tone.get(c, c) for c in r) for r in g.rows()]


# A cast-iron street lamp (after pixellab-out/old-park-lamp): a lantern under a little
# peaked roof with a finial, its glass lit, a collar and a slender post, a fluted foot.
LAMP = (['.......KK.......',
         '......KIIK......',
         '.....KIIJJK.....',
         '....KIIIJJJK....',
         '...KKKKKKKKKK...',
         '....KYYKYYJK....',
         '....KYYKYYJK....',
         '....KYYKYYJK....',
         '....KYYKYYJK....',
         '....KKKKKKKK....',
         '.....KIIJJK.....',
         '......KIJK......'] +
        ['......KIJK......'] * 25 +
        ['.....KIIJJK.....',
         '......KIJK......',
         '......KIJK......',
         '.....KIIJJK.....',
         '....KIIIJJJK....',
         '....KIIIJJJK....',
         '...KKKKKKKKKK...'])
# Pointed pickets on two rails (after pixellab-out/old-park-fence), joining left and right.
FENCE = ['..K.......K.....',
         '.KBK.....KBK....',
         'KBBSK...KBBSK...',
         'KBBSKKKKKBBSKKKK',
         'KBBSKBBBKBBSKBBB',
         'KBBSKSSSKBBSKSSS',
         'KBBSKKKKKBBSKKKK',
         'KBBSK...KBBSK...',
         'KBBSK...KBBSK...',
         'KBBSKKKKKBBSKKKK',
         'KBBSKBBBKBBSKBBB',
         'KBBSKSSSKBBSKSSS',
         'KBBSKKKKKBBSKKKK',
         'KBBSK...KBBSK...',
         'KKKKK...KKKKK...']
# A round bed of roses (after pixellab-out/old-park-flowers): leaves in two greens, lit
# high on the left, and blooms in clusters of pink with a black heart.
FLOWERS = ['.....KKKKKK.....',
           '...KKGGPPGGKK...',
           '..KGGGPKPGGGgK..',
           '.KGGPPGPGGPPggK.',
           '.KGPKPGGGPKPggK.',
           '.KGGPGgGGgPgggK.',
           '.KgGGgPPggggggK.',
           '.KggggPKPgggggK.',
           '..KggggPgggggK..',
           '...KKggggggKK...',
           '.....KKKKKK.....']


def ellipse(cx, cy, rx, ry, w=48, h=40):
    return {(x, y) for y in range(h) for x in range(w) if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1}


def fountain():
    """48x40, after pixellab-out/old-park-fountain: a wide basin, its rim lit and its wall
    carved in panels, the pool in it, a pedestal rising out of the water to an upper bowl,
    and a jet with its spray. Three tones, as an object keeps: the stone's light and mid,
    the water -- the jet's core and the panels' cuts in the stone's light and the line.
    Parts back to front, each lined, the nearer over the farther."""
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    parts = []
    body = ellipse(24, 32, 22, 6.5)
    wall = {}
    for (x, y) in body:
        c = 'S' if y < 30 else 'M'
        if 31 <= y <= 36 and (x - 4) % 7 == 0:
            c = 'K'                                                              # the wall's carved panels
        wall[(x, y)] = c
    parts.append(wall)                                                           # the basin
    parts.append({p: 'U' for p in ellipse(24, 29, 18.5, 3.2)})                  # its pool
    ped = {}
    for y in range(13, 31):
        half = 3 if y < 27 else 4
        for x in range(24 - half, 24 + half):
            ped[(x, y)] = 'S' if x <= 24 - half + 1 else 'M'
    parts.append(ped)                                                            # the pedestal, flared at its foot
    bowl = ellipse(24, 14, 11, 3.6)
    parts.append({p: 'S' if p[1] < 14 else 'M' for p in bowl})                  # the upper bowl
    parts.append({p: 'U' for p in ellipse(24, 13, 8.5, 1.8)})                   # its water
    jet = {(x, y): ('S' if x == 24 else 'U') for y in range(5, 12) for x in (23, 24, 25)}
    for x, y in ((24, 3), (24, 4), (23, 4), (25, 4)):                           # the jet's crown of spray
        jet[(x, y)] = 'S'
    parts.append(jet)
    out = {}
    for part in parts:
        for (x, y), c in part.items():
            out[(x, y)] = c
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
