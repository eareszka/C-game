"""The coastal town's inn, laid out for tools/draw_views.py.

    python art/structures/coast/inn_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/inn

A two-storey middle between two low wings, its sign over the door.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House, clapboard_tone, CHIMNEY
from overworld_style import MATERIALS

# white boards and the shadow under each; green shutters, casing and panes; a slate roof; the chimney's brick
PAL = dict(zip('BS', MATERIALS['white paint']['tones']), K='000000', M=MATERIALS['green paint']['tones'][0],
           R=MATERIALS['slate']['tones'][0], **dict(zip('Xx', MATERIALS['brick']['tones'])))


def design():
    h = House(11, 9, clapboard_tone)
    h.wing(6, 47, 16, 34, 14, side='S')                # first: the middle's wall stands in front of its roof
    h.wing(48, 111, 22, 66, 14, side='S')              # its ridge on a tile row (y 48); its walls end on tile columns,
    h.chimney(74, 10, 18, 96, tones=CHIMNEY)           # so its windows share no tile with a wing's roof
    h.wing(112, 146, 16, 34, 14, eave=1, side='S')
    for x in (54, 90):
        h.window(x, 5.5, shutters=True)
    for x in (18, 52, 92, 122):
        h.window(x, 7.5, shutters=True)
    h.sign(72, 44, 'INN', ink='B')
    return h.finish('inn', PAL, h.door(72))


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
