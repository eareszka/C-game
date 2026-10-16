"""The grass villages' set: timber cottages under thatch, laid out for tools/draw_views.py (village_shapes.py).

    python art/structures/villages/grass_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/villages/grass

Plaster panels in white paint between posts and beams of bark (timber_tone),
the panes and casings the paint's shade, a thatched roof in its rows, a brick
chimney; a well of stone with a wooden windlass.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from house_shapes import House, brick_tone, clapboard_tone, timber_tone, adobe_tone, log_tone, CHIMNEY
from overworld_style import MATERIALS
from village_shapes import strip, well

# plaster, the timber, the paint's shade (trim and panes), thatch; the chimney's brick; the well's stone and wood
PAL = {'K': '000000', 'B': MATERIALS['white paint']['tones'][0], 'S': MATERIALS['bark']['tones'][1],
       'M': MATERIALS['white paint']['tones'][1], 'R': MATERIALS['thatch']['tones'][0],
       **dict(zip('Xx', MATERIALS['brick']['tones'])),
       **dict(zip('lmd', MATERIALS['stone']['tones'])), 'w': MATERIALS['wood']['tones'][1]}
WELL = {'L': 'l', 'M': 'm', 'D': 'd', 'x': 'w'}

def design():
    a = House(4, 5, timber_tone)
    a.wing(6, 44, 12, 34, 14, side='M')
    a.window(27, 3.5)
    da = a.door(8)
    b = House(5, 5, timber_tone)
    b.wing(6, 60, 14, 34, 16, side='M')
    b.chimney(10, 9, 13, 56, depth=3, tones=CHIMNEY)
    db = b.door(14)
    b.window(40, 3.5)
    c = House(6, 5, timber_tone)
    c.wing(6, 76, 16, 34, 16, side='M')
    dc = c.door(32)
    c.window(10, 3.5)
    c.window(56, 3.5)
    return strip('grass', PAL, [(a, da, 'grass small'), (b, db, 'grass middle'), (c, dc, 'grass large')], well(WELL))

if __name__ == '__main__':
    d = design()
    json.dump(d, open(sys.argv[1], 'w'))
    for r in d['views'][d['order'][0]]:
        print(r)
