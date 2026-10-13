"""The things on the coastal town's green, laid out for tools/draw_views.py.

    python art/structures/coast/park_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/park

A strip two cells tall: a bench, a street lamp (two cells), a fountain (two
by two), a picket fence that joins itself left and right, a flower bed. Each
is an object: a black line round it, three tones and black.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, stand, depth_layers, check
from overworld_style import MATERIALS

# a bench's wood; the lamp's iron and its light; white paint; the fountain's stone and water; leaves and flowers
PAL = dict(zip('Ww', MATERIALS['wood']['tones']), K='000000', I=MATERIALS['slate']['tones'][1],
           Y=MATERIALS['lamplight']['tones'][0], B=MATERIALS['white paint']['tones'][0],
           **dict(zip('SM', MATERIALS['stone']['tones'])), U=MATERIALS['water']['tones'][0],    # S is the paint's shade too
           **dict(zip('Gg', MATERIALS['foliage']['tones'])), P=MATERIALS['meadow']['tones'][1])

BENCH = ['..KKKKKKKKKKKK..',
         '..KWWWWWWWWWWK..',
         '..KKKKKKKKKKKK..',
         '..KWWWWWWWWWWK..',
         '..KKKKKKKKKKKK..',
         '.KKKKKKKKKKKKKK.',
         '.KWWWWWWWWWWWWK.',
         '.KwwwwwwwwwwwwK.',
         '.KKKKKKKKKKKKKK.',
         '..KwK......KwK..',
         '..KKK......KKK..']
LAMP = (['......KKKK......',
         '.....KIIIIK.....',
         '....KKKKKKKK....',
         '....KYYKKYYK....',
         '....KYYKKYYK....',
         '....KYYKKYYK....',
         '....KYYKKYYK....',
         '.....KYYYYK.....',
         '.....KKKKKK.....'] + ['......KIIK......'] * 17 +
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
FOUNTAIN = ['..............KK................',
            '.............KUUK...............',
            '.............KUUK...............',
            '.........KKKKKUUKKKKK...........',
            '........KSSSSSUUSSSSSK..........',
            '........KUMMMMMMMMMMUK..........',
            '........KUKKKKKKKKKKUK..........',
            '........KUK..KSMK..KUK..........',
            '........KUK..KSMK..KUK..........',
            '........KUK..KSMK..KUK..........',
            '........KUK..KSMK..KUK..........',
            '........KUK..KSMK..KUK..........',
            '....KKKKKUKKKKSMKKKKUKKKKK......',
            '..KKSSSSSUSSSSSMSSSSUSSSSSKK....',
            '.KSSUUUUUUUUUUUUUUUUUUUUUUSSK...',
            'KSSUUUUUUUUUUUUUUUUUUUUUUUUSSK..',
            'KSSSUUUUUUUUUUUUUUUUUUUUUUSSSK..',
            'KMSSSSSSSSSSSSSSSSSSSSSSSSSSMK..',
            'KMMMMMMMMMMMMMMMMMMMMMMMMMMMMK..',
            'KMMMMMMMMMMMMMMMMMMMMMMMMMMMMK..',
            'KMKMMMMKMMMMKMMMMKMMMMKMMMMKMK..',
            'KMMMMMMMMMMMMMMMMMMMMMMMMMMMMK..',
            '.KMMMMMMMMMMMMMMMMMMMMMMMMMMK...',
            '..KKMMMMMMMMMMMMMMMMMMMMMMKK....',
            '....KKKKKKKKKKKKKKKKKKKKKK......']
# (its rows, the cell it starts in): each stands on the strip's bottom row
THINGS = [(BENCH, 0), (LAMP, 1), (FOUNTAIN, 2), (FENCE, 4), (FLOWERS, 5)]
CELLS, H = 6, 32


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
    json.dump(design(), open(sys.argv[1], 'w'))
