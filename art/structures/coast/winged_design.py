"""The coastal town's house with a wing, laid out for tools/draw_views.py.

    python art/structures/coast/winged_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/winged

Two storeys, and a low wing against its side. (A saltbox was tried first: its
long back roof does not show in this view, it reads as a box.)
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House, clapboard_tone, CHIMNEY
from overworld_style import MATERIALS

# white boards and the shadow under each; black shutters, casing and panes; a slate roof; the chimney's brick
PAL = dict(zip('BS', MATERIALS['white paint']['tones']), K='000000', M=MATERIALS['black paint']['tones'][0],
           R=MATERIALS['slate']['tones'][0], **dict(zip('Xx', MATERIALS['brick']['tones'])))


def design():
    h = House(8, 9, clapboard_tone)
    h.wing(6, 60, 22, 66, 14, side='S')                # its ridge on a tile row (y 48)
    h.chimney(26, 10, 18, 96, tones=CHIMNEY)
    h.wing(60, 100, 16, 34, 14, side='S')
    for x in (8, 30):                                  # clear of the tile column the wing's roof is in
        h.window(x, 5.5, shutters=True)
    h.window(30, 7.5, shutters=True)
    h.window(72, 7.5, shutters=True)
    return h.finish('winged', PAL, h.door(8))


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
