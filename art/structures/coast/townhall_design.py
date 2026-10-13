"""The coastal town's town hall, laid out for tools/draw_views.py.

    python art/structures/coast/townhall_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/townhall

The widest building, for the town centre: double doors, and a clock in a low
tower on its roof.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House, clapboard_tone, CHIMNEY
from overworld_style import MATERIALS

# white boards and the shadow under each; navy shutters, casing and panes; a slate roof; the chimney's brick
PAL = dict(zip('BS', MATERIALS['white paint']['tones']), K='000000', M=MATERIALS['navy paint']['tones'][0],
           R=MATERIALS['slate']['tones'][1], **dict(zip('Xx', MATERIALS['brick']['tones'])))


def design():
    h = House(9, 10, clapboard_tone)
    h.wing(6, 118, 22, 66, 16, side='S')
    h.belfry(51, 22, 112, 16, depth=14, clock=True)
    for x in (10, 28, 82, 100):
        h.window(x, 8.5, shutters=True)
    for x in (10, 28, 55, 82, 100):
        h.window(x, 6.5, shutters=True)
    h.door(46)
    dx, dw = h.door(62)                                # two doors side by side
    return h.finish('townhall', PAL, (dx - 16, dw + 16))


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
