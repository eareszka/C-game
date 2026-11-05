"""Xuelin's courtyard house (a siheyuan's front), laid out for tools/draw_views.py.

    python art/structures/xuelin/courtyard_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/xuelin/courtyard

A whole courtyard house (siheyuan) filling its lot -- the user, 2026-10-28:
"full compounds". Its street front after PixelLab draft 3
(pixellab-out/xuelin-courtyard/sprites/v3): a grey brick wall along the lane,
capped with tiles, a gatehouse under its own roof, a red double door. Every
roof is the Chinese one (house_shapes.House.hall, hall_d), snow on its upper
slope and ridge.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House, brick_tone
from overworld_style import MATERIALS

# grey brick: stone's two darker tones, laid with its lightest as the joint;
# the roof's slate (its lit tone the brick's shade); the snowpack; red lacquer, gold
STONE = MATERIALS['stone']['tones']
PAL = dict(K='000000', M=STONE[0], B=STONE[1], S=STONE[2], Q=MATERIALS['slate']['tones'][1],
           W=MATERIALS['snowpack']['tones'][0], A=MATERIALS['snowpack']['tones'][1],
           D=MATERIALS['red paint']['tones'][0], d=MATERIALS['red paint']['tones'][1],
           Y=MATERIALS['yellow paint']['tones'][0])
TILES = ('S', 'Q')
ROAD_MID = 8                  # a road going back: its paving's middle lies this far west of its middle
                              # cell's (measured in game, 2026-10-29), so a door it ends at sits there
# where a cell holds more than four: the joint into the brick, the snow's shade
# into its white, the roof's dark into its lit, the lacquer's shade into it
MERGE = [('M', 'B'), ('A', 'W'), ('Q', 'S'), ('d', 'D'), ('B', 'S')]


def gate(h, x0, top):
    """The red double door, a cell wide, from `top` to the ground line: two
    leaves in the lacquer, shaded down their right edge, black between and
    round them, a gold ring on each."""
    B = h.B
    for y in range(top, B):
        for x in range(x0, x0 + 16):
            lx, ly = x - x0, y - top
            if lx in (0, 15, 7, 8) or ly == 0:
                c = 'K'
            elif lx in (6, 14) or ly == 1:
                c = 'd'
            elif ly % 8 == 7:
                c = 'd'                                        # the leaves' rails
            else:
                c = 'D'
            h.put(x, y, c, B)
    for x in (x0 + 5, x0 + 9):
        h.put(x, top + 15, 'Y', B)
        h.put(x, top + 16, 'Y', B)
    return x0 + 1, 14


def timber(rx, ry):
    """A hall's front to the courtyard: red posts every 24, a lacquered beam
    along the top, and between the posts lattice windows -- a black grid on
    pale paper."""
    if rx % 24 < 3:
        return 'D'
    if ry < 3:
        return 'd'
    return 'K' if rx % 4 == 1 or ry % 4 == 0 else 'M'


SIZE = (14, 9)                  # its block in cells


def draw(h):
    """The whole compound on its lot, eight cells across and seven back: the
    lane wall and the gatehouse (east of the middle, as a siheyuan's is) on
    the street, the side halls left and right of an open courtyard, the main
    hall across its back facing the gate. Its back stops short of the street
    behind, so nothing of it covers the next row's doors. Gives back its door."""
    h.hall(4, 110, 28, 32, 14, d0=68, eave=3, lift=5, tiles=TILES, front=timber)      # the main hall
    h.hall_d(4, 36, 44, 30, 12, d0=22, tiles=TILES, face=timber)                       # the west side hall
    h.hall_d(78, 110, 44, 30, 12, d0=22, tiles=TILES)                                  # the east side hall
    for x0 in (4, 106):                                                                # the walls back to them
        h.hall_d(x0, x0 + 4, 14, 28, 3, d0=8, eave=1, lift=0, ridge=1, snow=0, tiles=TILES, ends=False)
    h.hall(4, 110, 6, 30, 4, d0=2, eave=2, lift=1, ridge=1, snow=0, tiles=TILES, ends=False)   # the lane wall
    h.hall(70, 105, 14, 44, 10, d0=0, eave=3, lift=3, tiles=TILES)                     # the gatehouse
    return gate(h, 80, h.B - 31)


def design():
    h = House(*SIZE, brick_tone)
    return h.finish('courtyard', PAL, draw(h), merge=MERGE)

if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
