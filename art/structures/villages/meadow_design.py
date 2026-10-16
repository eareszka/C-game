"""The meadow villages' set: farms, laid out for tools/draw_views.py (village_shapes.py).

    python art/structures/villages/meadow_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/villages/meadow

A farm (the user, 2026-10-13: "meadow towns should be like farms", with
"different house colors since the current approach looks like the lake
town"): clapboard in yellow paint (clapboard_tone) with white trim, a red
roof on the farmhouse and a green one on the cottage, a shed in the barn's
red with white trim, a brick chimney; the barn itself, tall, in red paint
with white trim and double doors under a hayloft window; a well of stone;
and the field's cell, rows of earth with sprouts, which the village lays in
fenced rectangles.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from house_shapes import House, clapboard_tone, CHIMNEY
from overworld_style import MATERIALS
from village_shapes import strip, well, field

# yellow boards and their shadow, white trim; red boards (the shed, the barn) 'P' and their shadow 'p';
# the farmhouse's red roof 'R', the cottage's green 'G', slate on the shed and the barn 'Z';
# the chimney's brick; the well's stone and wood; the field's earth, furrow, sprout
PAL = {'K': '000000', 'B': MATERIALS['yellow paint']['tones'][0], 'S': MATERIALS['yellow paint']['tones'][1],
       'M': MATERIALS['white paint']['tones'][0], 'R': MATERIALS['red paint']['tones'][1],
       'G': MATERIALS['green paint']['tones'][0], 'Z': MATERIALS['slate']['tones'][0],
       'P': MATERIALS['red paint']['tones'][0], 'p': MATERIALS['red paint']['tones'][1],
       **dict(zip('Xx', MATERIALS['brick']['tones'])),
       **dict(zip('lmd', MATERIALS['stone']['tones'])), 'w': MATERIALS['wood']['tones'][1],
       **dict(zip('ef', MATERIALS['dirt']['tones'])), 'c': MATERIALS['foliage']['tones'][0]}
WELL = {'L': 'l', 'M': 'm', 'D': 'd', 'x': 'w'}
RED = {'B': 'P', 'S': 'p', 'R': 'Z'}              # the shed and the barn: red boards under slate
GREEN = {'R': 'G'}


def recolour(g, tones):
    for y in range(g.h):
        for x in range(g.w):
            g.g[y][x] = tones.get(g.g[y][x], g.g[y][x])
    return g


def design():
    a = House(4, 5, clapboard_tone)                           # the shed
    a.wing(6, 44, 12, 34, 14, side='S')
    a.window(27, 3.5)
    da = a.door(8)
    ga = recolour(a.grid('meadow shed'), RED)
    b = House(5, 5, clapboard_tone)                           # the cottage
    b.wing(6, 60, 14, 34, 16, side='S')
    b.chimney(10, 9, 13, 56, depth=3, tones=CHIMNEY)
    db = b.door(14)
    b.window(40, 3.5, shutters=True)
    gb = recolour(b.grid('meadow cottage'), GREEN)
    c = House(6, 5, clapboard_tone)                           # the farmhouse
    c.wing(6, 76, 16, 34, 16, side='S')
    c.chimney(14, 9, 14, 56, depth=3, tones=CHIMNEY)
    dc = c.door(32)
    c.window(10, 3.5, shutters=True)
    c.window(56, 3.5, shutters=True)
    gc = c.grid('meadow farmhouse')
    n = House(6, 7, clapboard_tone)                           # the barn: gable end to the front, a gambrel roof back,
    n.barn(4, 80, 14, 48, 18, 10)                             # X-braced double doors, a hayloft window (the user's reference)
    n.barn_door(27, 16); n.barn_door(43, 16)
    n.window(35, 2.75)
    gn = recolour(n.grid('meadow barn'), {'B': 'P', 'S': 'p', 'R': 'w'})
    return strip('meadow', PAL,
                 [(a, da, 'meadow shed', ga), (b, db, 'meadow cottage', gb), (c, dc, 'meadow farmhouse', gc),
                  (n, None, 'meadow barn', gn)],
                 well(WELL), extras=[('field', field())])


if __name__ == '__main__':
    d = design()
    json.dump(d, open(sys.argv[1], 'w'))
    for r in d['views'][d['order'][0]]:
        print(r)
