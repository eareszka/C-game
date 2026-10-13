"""The coastal town's fish shack, laid out for tools/draw_views.py.

    python art/structures/coast/shack_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/shack

One small room for the wharf: a door and a window.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House, clapboard_tone, CHIMNEY
from overworld_style import MATERIALS

# white boards and the shadow under each; grey shutters, casing and panes; a slate roof; the chimney's brick
PAL = dict(zip('BS', MATERIALS['white paint']['tones']), K='000000', M=MATERIALS['slate']['tones'][1],
           R=MATERIALS['slate']['tones'][0], **dict(zip('Xx', MATERIALS['brick']['tones'])))


def design():
    h = House(4, 5, clapboard_tone)
    h.wing(6, 44, 12, 34, 14, side='S')
    h.window(27, 3.5)
    return h.finish('shack', PAL, h.door(8))


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
