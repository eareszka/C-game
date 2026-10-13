"""The coastal town's meeting house, laid out for tools/draw_views.py.

    python art/structures/coast/meeting_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/meeting

Tall, a square belfry through the front of its roof and a spire on that.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House, clapboard_tone, CHIMNEY
from overworld_style import MATERIALS

# white boards and the shadow under each; black shutters, casing and panes; a slate roof; the chimney's brick
PAL = dict(zip('BS', MATERIALS['white paint']['tones']), K='000000', M=MATERIALS['black paint']['tones'][0],
           R=MATERIALS['slate']['tones'][1], **dict(zip('Xx', MATERIALS['brick']['tones'])))


def design():
    h = House(7, 11, clapboard_tone)
    h.wing(6, 70, 30, 66, 22, side='S')
    h.belfry(29, 18, 118, 30)
    for x in (10, 52):
        for cy in (7.5, 9.5):
            h.window(x, cy, shutters=True)
    return h.finish('meeting', PAL, h.door(30))


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
