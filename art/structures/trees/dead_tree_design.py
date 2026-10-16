"""The dead tree the wasteland is scattered with, laid out for tools/draw_views.py.

    python art/structures/trees/dead_tree_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/trees/dead_tree
    python art/structures/build_fc_structures.py --stamp     # sheet col 20

Drawn fresh (the user, 2026-10-13: new shape) to the trees' rule, in bark:
a bare trunk forking into four bold limbs, as the great oak's does, roots
splayed at its foot, light along the upper left of the trunk and the limbs,
dark down the right, a black line round the whole and between limbs. 16x32,
canopy cell over trunk cell. Its fills are typed; the line is laid round
them (outline()).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, check, outline
from overworld_style import MATERIALS

PAL = dict(zip('wxy', MATERIALS['bark']['tones']), K='000000')
E = '................'

FILLS = [E, E,
    '..wx........xy..',
    '..wx.......xy...',
    '...wx..wx..xy...',
    '...wx..wx..xy...',
    '....wx.wx.xy....',
    '....wxwxx.xy....',
    '.....wxxyxy.....',
    '.....wxxyy......',
    '..wx..wxxy......',
    '..wx..wxxy..xy..',
    '...wx.wxxy.xy...',
    '....wxwxxyxy....',
    '.....wxxxyy.....',
    '......wxxy......',
    '......wxxy......',
    '......wxxy......',
    '......wxxy......',
    '......wxxy......',
    '......wxxy......',
    '......wxxy......',
    '......wxxy......',
    '......wxxy......',
    '......wxxy......',
    '.....wwxxyy.....',
    '....wwxxxyyy....',
    '...wxx.xxy.yy...',
    '..wx...xy...y...',
    '..x....yy.......', E, E]


def tree():
    assert len(FILLS) == 32 and all(len(r) == 16 for r in FILLS)
    g = Grid(16, 32)
    g.g = [list(r) for r in FILLS]
    outline(g)
    check(g, 'dead tree')
    return g


def design():
    return {'pal': PAL, 'view_w': 16, 'order': ['dead tree'], 'views': {'dead tree': tree().rows()}}


if __name__ == '__main__':
    d = design()
    json.dump(d, open(sys.argv[1], 'w'))
    for r in d['views']['dead tree']:
        print(r)
