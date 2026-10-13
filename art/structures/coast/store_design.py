"""The coastal town's store, laid out for tools/draw_views.py.

    python art/structures/coast/store_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/store

A shop: two wide windows under a striped awning, its sign above.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House, clapboard_tone, CHIMNEY
from overworld_style import MATERIALS

# white boards and the shadow under each; red shutters, casing and panes; a slate roof; the chimney's brick
PAL = dict(zip('BS', MATERIALS['white paint']['tones']), K='000000', M=MATERIALS['red paint']['tones'][1],
           R=MATERIALS['slate']['tones'][1], **dict(zip('Xx', MATERIALS['brick']['tones'])))


def design():
    h = House(8, 7, clapboard_tone)
    h.wing(6, 102, 16, 50, 20, side='S')
    for x in (10, 66):
        h.window(x, 5.5, tiles=2)
    door = h.door(46)
    h.awning(8, 100, 36, 0)
    h.sign(43, 37, 'STORE', ink='B')
    return h.finish('store', PAL, door)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
