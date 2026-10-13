"""The coastal town's captain's house, laid out for tools/draw_views.py.

    python art/structures/coast/captain_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/captain

Wide, two storeys, a chimney at each end and a roof walk between them.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House, clapboard_tone, CHIMNEY
from overworld_style import MATERIALS

# white boards and the shadow under each; navy shutters, casing and panes; a slate roof; the chimney's brick
PAL = dict(zip('BS', MATERIALS['white paint']['tones']), K='000000', M=MATERIALS['navy paint']['tones'][0],
           R=MATERIALS['black paint']['tones'][0], **dict(zip('Xx', MATERIALS['brick']['tones'])))


def design():
    h = House(9, 9, clapboard_tone)
    h.wing(6, 104, 20, 66, 15, side='S')               # its ridge on a tile row (y 48)
    for x in (24, 78):
        h.chimney(x, 10, 16, 94, tones=CHIMNEY)
    ridge = h.B - 81 - 14
    for x in range(54, 91):                            # the roof walk: a rail along the ridge
        for up in range(1, 9):
            if up == 8 or (x - 54) % 4 == 0:
                h.put(x, ridge - up, 'K', h.B - 14)
    for x in (10, 30, 68, 88):
        h.window(x, 7.5, shutters=True)
    for x in (10, 30, 49, 68, 88):
        h.window(x, 5.5, shutters=True)
    return h.finish('captain', PAL, h.door(48))


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
