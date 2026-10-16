"""The palm, laid out for tools/draw_views.py: the oasis's tree.

    python art/structures/entrances/palm_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/palm

Drawn fresh (the user, 2026-10-13: new shape) to the trees' rule: three
colours and black. A crown of fronds in the trees' three greens -- light high
on the left, dark massed low and on the right -- on a trunk that is black
with the dark green along its lit side, as the forest trees' trunks are,
curving as it rises; two black coconuts under the crown as its accent; a
black line round the whole and between the fronds. 16x32, as tall as the
game's tall trees. Its fills are typed; the line is laid round them
(outline()).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, check, outline
from overworld_style import MATERIALS

PAL = dict(zip('cgG', MATERIALS['foliage']['tones']), K='000000')
E = '................'

FILLS = [E, E,
    '.......ccg......',
    '....ccccggg.....',
    '...ccgggGgggc...',
    '..cggGgGGGgggg..',
    '..cgG.GGG.GGgg..',
    '..gG..KGK..GGg..',
    '..G..KKGKK...G..',
    '......GKK.......',
    '......GKK.......',
    '......GKK.......',
    '......GKK.......',
    '.....GGKK.......',
    '.....GKK........',
    '.....GKK........',
    '.....GKK........',
    '.....GKK........',
    '.....GKK........',
    '....GGKK........',
    '....GKK.........',
    '....GKK.........',
    '....GKK.........',
    '....GKK.........',
    '....GKK.........',
    '....GKK.........',
    '....GKK.........',
    '...GGKKK........',
    '..GGGKKKK.......',
    '..GGKKKKKK......',
    '...KKKKKK.......', E]


def palm():
    assert len(FILLS) == 32 and all(len(r) == 16 for r in FILLS)
    g = Grid(16, 32)
    g.g = [list(r) for r in FILLS]
    outline(g)
    # a part laid into a block with room above it, so checked with that room
    room = Grid(16, 33)
    room.g = [['.'] * 16] + [r[:] for r in g.g]
    check(room, 'palm')
    return g


def design():
    return {'pal': PAL, 'view_w': 16, 'order': ['palm'], 'views': {'palm': palm().rows()}}


if __name__ == '__main__':
    d = design()
    json.dump(d, open(sys.argv[1], 'w'))
    for r in d['views']['palm']:
        print(r)
