"""The sand villages' set: round houses in the pyramid's brick under domes,
laid out for tools/draw_views.py (village_shapes.py).

    python art/structures/villages/sand_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/villages/sand

The user, 2026-10-13/14: "deserts should be the brick used in the pyramid"
and "the desert homes should be oblique projected but circular with the dome
on top". Each is a round wall in the oblique view (House.round_wall), its
courses the pyramid's sandstone (pyramid_tone: blocks in courses, a bed of
mortar under each, the face lit, the part turned away in its shade), and a
dome on its rim (House.dome). A round rim is an ellipse on the screen, so
the dome shares cells with the wall, and four colours a cell leave it the
wall's own brick: a beehive house, its dome's courses rows round it. A well
of sandstone with a wooden windlass.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from house_shapes import House, pyramid_tone
from overworld_style import MATERIALS
from village_shapes import strip, well

# the lit face (and the dome), the shade (the side turned away, the door), the mortar (and trim and panes);
# the well's sandstone and wood
PAL = {'K': '000000', 'B': MATERIALS['sandstone']['tones'][0], 'S': MATERIALS['sandstone']['tones'][1],
       'M': MATERIALS['sandstone']['joint'], 'R': MATERIALS['sandstone']['tones'][0],
       'l': MATERIALS['sandstone']['tones'][0], 'm': MATERIALS['sandstone']['tones'][1], 'd': MATERIALS['sandstone']['tones'][2],
       'w': MATERIALS['wood']['tones'][1]}
WELL = {'L': 'l', 'M': 'm', 'D': 'd', 'x': 'w'}
WALL = 28


def house(cw, rx, rd, rise):
    """A round house in a block cw cells wide: its plan an ellipse rx across
    and rd back, its front at the ground line, the door at its front's
    middle; no windows (the user, 2026-10-14: better without)."""
    h = House(cw, 5, pyramid_tone)
    cx = cw * 8 - rd                                           # so the whole, depth and all, sits in its cells
    h.round_wall(cx, rd, rx, rd, WALL)
    h.dome(cx - rx, cx + rx, 0, 2 * rd, WALL, rise, shade='S')
    return h, h.door(cx - 8)


def design():
    a, da = house(4, 20, 6, 12)
    b, db = house(5, 26, 7, 14)
    c, dc = house(6, 34, 8, 16)
    return strip('sand', PAL, [(a, da, 'sand small'), (b, db, 'sand middle'), (c, dc, 'sand large')], well(WELL))


if __name__ == '__main__':
    d = design()
    json.dump(d, open(sys.argv[1], 'w'))
    for r in d['views'][d['order'][0]]:
        print(r)
