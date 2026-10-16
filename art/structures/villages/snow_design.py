"""The snow villages' set: log cabins under snow, laid out for tools/draw_views.py (village_shapes.py).

    python art/structures/villages/snow_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/villages/snow

Logs laid one on the next in wood (log_tone), each lit along its top and
dark beneath, the panes and casings the wood's light tone, snow lying on the
roof in its rows (white paint), a stone chimney; a well of stone, snow on its lip.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from house_shapes import House, brick_tone, clapboard_tone, timber_tone, adobe_tone, log_tone, CHIMNEY
from overworld_style import MATERIALS
from village_shapes import strip, well

# the logs, their undersides, their lit tops (and trim and panes), snow on the roof; the chimney's stone; the well's stone, snow, wood
PAL = {'K': '000000', 'B': MATERIALS['wood']['tones'][1], 'S': MATERIALS['wood']['tones'][2],
       'M': MATERIALS['wood']['tones'][0], 'R': MATERIALS['white paint']['tones'][0],
       'X': MATERIALS['stone']['tones'][1], 'x': MATERIALS['stone']['tones'][2],
       'n': MATERIALS['white paint']['tones'][0], 'm': MATERIALS['stone']['tones'][1], 'd': MATERIALS['stone']['tones'][2],
       'w': MATERIALS['wood']['tones'][1]}
STONE = {'B': 'X', 'S': 'x', 'M': 'x'}
WELL = {'L': 'n', 'M': 'm', 'D': 'd', 'x': 'w'}

def design():
    a = House(4, 5, log_tone)
    a.wing(6, 44, 12, 34, 14, side='S')
    a.window(27, 3.5)
    da = a.door(8)
    b = House(5, 5, log_tone)
    b.wing(6, 60, 14, 34, 16, side='S')
    b.chimney(10, 9, 13, 56, depth=3, tones=STONE)
    db = b.door(14)
    b.window(40, 3.5)
    c = House(6, 5, log_tone)
    c.wing(6, 76, 16, 34, 16, side='S')
    dc = c.door(32)
    c.window(10, 3.5)
    c.window(56, 3.5)
    return strip('snow', PAL, [(a, da, 'snow small'), (b, db, 'snow middle'), (c, dc, 'snow large')], well(WELL))

if __name__ == '__main__':
    d = design()
    json.dump(d, open(sys.argv[1], 'w'))
    for r in d['views'][d['order'][0]]:
        print(r)
