"""The coastal town's Cape house, laid out for tools/draw_views.py.

    python art/structures/coast/cape_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/cape

Low, one storey, its chimney in the middle of the roof, a window either side
of the door.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House, clapboard_tone, CHIMNEY
from overworld_style import MATERIALS

# white boards and the shadow under each; green shutters, casing and panes; a slate roof; the chimney's brick
PAL = dict(zip('BS', MATERIALS['white paint']['tones']), K='000000', M=MATERIALS['green paint']['tones'][0],
           R=MATERIALS['slate']['tones'][1], **dict(zip('Xx', MATERIALS['brick']['tones'])))


def design():
    h = House(7, 7, clapboard_tone)
    h.wing(6, 86, 20, 34, 31, side='S')                # its ridge on a tile row (y 32)
    h.chimney(40, 12, 16, 74, tones=CHIMNEY)
    for x in (16, 64):
        h.window(x, 5.5, shutters=True)
    return h.finish('cape', PAL, h.door(40))


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
