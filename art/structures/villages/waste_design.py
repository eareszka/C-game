"""The wasteland villages' set: a barracks settlement of ruined stone, laid
out for tools/draw_views.py (village_shapes.py).

    python art/structures/villages/waste_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/villages/waste

The user, 2026-10-13: the wasteland's buildings "should look like barracks
settlement from yume nikki" and "shouldnt even be structural"; asked, they
chose ruined stone: dark stone in the brick's courses, every hut bitten and
cracked by the weather (village_shapes.ruin), under sheets of slate, a rusty
stovepipe on one; the village sets them close together. A well of the same
dark stone with a wooden windlass.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from house_shapes import House, brick_tone
from overworld_style import MATERIALS
from village_shapes import strip, well, ruin

# the stone, its shade, its lit tops (and trim and panes), slate; the stovepipe's rust; the well's dark stone and wood
PAL = {'K': '000000', 'B': MATERIALS['dark stone']['tones'][1], 'S': MATERIALS['dark stone']['tones'][2],
       'M': MATERIALS['dark stone']['tones'][0], 'R': MATERIALS['slate']['tones'][1],
       **dict(zip('Xx', MATERIALS['rust']['tones'])),
       **dict(zip('lmd', MATERIALS['dark stone']['tones'])), 'w': MATERIALS['wood']['tones'][1]}
RUST = {'B': 'X', 'S': 'x', 'M': 'x'}
WELL = {'L': 'l', 'M': 'm', 'D': 'd', 'x': 'w'}


def door_rect(h, door):
    dx, dw = door
    return (dx - 2, h.B - 24, dx + dw + 1, h.B)


def design():
    a = House(4, 5, brick_tone)
    a.wing(6, 44, 12, 34, 12, side='S')
    a.window(27, 3.5)
    da = a.door(8)
    b = House(5, 5, brick_tone)
    b.wing(6, 60, 14, 34, 14, side='S')
    b.chimney(12, 6, 13, 56, depth=2, tones=RUST)
    db = b.door(14)
    b.window(40, 3.5)
    c = House(6, 5, brick_tone)
    c.wing(6, 76, 16, 34, 14, side='S')
    dc = c.door(32)
    c.window(10, 3.5)
    c.window(56, 3.5)
    return strip('waste', PAL,
                 [(a, da, 'waste small', ruin(a, 'waste small', 11, [door_rect(a, da)])),
                  (b, db, 'waste middle', ruin(b, 'waste middle', 12, [door_rect(b, db)])),
                  (c, dc, 'waste large', ruin(c, 'waste large', 13, [door_rect(c, dc)]))],
                 well(WELL))


if __name__ == '__main__':
    d = design()
    json.dump(d, open(sys.argv[1], 'w'))
    for r in d['views'][d['order'][0]]:
        print(r)
