"""The coastal town's boathouse, laid out for tools/draw_views.py.

    python art/structures/coast/boathouse_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/coast/boathouse

A long low shed for the wharf, its doors wide enough for a boat.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House, clapboard_tone, CHIMNEY
from overworld_style import MATERIALS

# white boards and the shadow under each; red shutters, casing and panes; a slate roof; the chimney's brick
PAL = dict(zip('BS', MATERIALS['white paint']['tones']), K='000000', M=MATERIALS['red paint']['tones'][1],
           R=MATERIALS['slate']['tones'][0], **dict(zip('Xx', MATERIALS['brick']['tones'])))


def design():
    h = House(8, 6, clapboard_tone)
    h.wing(6, 96, 24, 34, 18, side='S')
    B, x0, w, tall = h.B, 18, 42, 28
    for y in range(B - tall, B):                       # two plank leaves in a casing
        for x in range(x0, x0 + w):
            lx, ly = x - x0, y - (B - tall)
            if lx in (0, w - 1) or ly == 0:
                c = 'K'
            elif lx in (1, w - 2) or ly == 1:
                c = 'M'
            else:
                c = 'K' if lx in (2, w - 3, w // 2 - 1, w // 2) or ly == 2 or (lx - 2) % 4 == 0 else 'S'
            h.put(x, y, c, B)
    h.window(72, 4.5)
    return h.finish('boathouse', PAL, (x0 + 2, w - 4))


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
