"""Room 0, the spawn house, NES style: PixelLab's brick on the back wall,
its bed and chest of drawers over the old boxes (the same places and sizes,
the feet meet them as before), and to make it lived in, things that stand in
nobody's way: curtains at both windows, a picture over the drawers, a clock,
a houseplant in the back corner, a rug on the boards.

    python tools/interior_nes.py 0 art/interiors_nes/house0_design.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from interior_nes import *

PAL = {'W': 'b6433d', 'Z': '792727', 'm': 'e8e0c0', 'R': '375a94'}
WOOD = {'K': '000000', 'F': '94703d', 'P': 'd7a175'}


def piece(r, draw, im, tones=None, choices=None):
    """An old box drawn for its place, its feet and its floor rows, then
    PixelLab's drawing of the same thing put where it stood."""
    before = set(r.fc)
    draw()
    mine = [q for q in r.fc if q not in before]
    box = (min(x for x, _ in mine), min(y for _, y in mine), max(x for x, _ in mine), max(y for _, y in mine))
    rows = clear_furniture(r, box)
    if tones:
        sprite(r, im, box[0], box[1], tones, box[3], rows=rows)
    else:
        sprite_rich(r, im, box[0], box[1], box[3], rows=rows, choices=choices)


CURTAIN_TONES = {'K': '000000', 'm': PAL['m'], 'a': 'a4aaba'}


def closed_curtains():
    """PixelLab's curtains drawn shut: the two panels meet over the glass
    (its pixels 9-14, rows 8-19), a fold either side and a dark seam where
    they meet. The intro's night and the morning until the day comes
    (house0_intro_design.py)."""
    im = art('s_curtains').copy()
    cream, fold = (251, 245, 233, 255), (207, 194, 193, 255)
    for y in range(8, 20):
        for x in range(9, 15):
            im.putpixel((x, y), (0, 0, 0, 255) if x == 11 else fold if x in (10, 13) else cream)
    return im


def curtains(r, closed=False):
    """At both windows, on the back wall behind everyone; open, the glass shows through."""
    for wx in (80, 160):
        if closed:
            sprite(r, closed_curtains(), wx, 14, CURTAIN_TONES, BACK)
        else:
            sprite(r, art('s_curtains'), wx, 14, CURTAIN_TONES, BACK,
                   cut=lambda x, y: 8 <= x <= 15 and y >= 8)


def design(closed=False):
    r = new_room()
    # the back wall's brick: the room's own (interior_room.shell), as the user wants it
    rug(r, 98, 114, 46, 14)
    piece(r, lambda: bed(r, 168, BACK + 8, flip=True), art('house0_B_bed'),
          {'K': '000000', 'R': PAL['R'], 'm': PAL['m']})
    piece(r, lambda: dresser(r, 112), art('house0_C_dresser'),          # PixelLab's own: honey top, brown front, dark side, lit edges, brass
          choices=['f0bc3c', '815423', '3c2412', 'fce4a0', 'c9a433'])
    curtains(r, closed)
    sprite(r, art('s_picture'), 116, 22, {'K': '000000', 'U': '84a7e9', 'h': '4fa667'}, BACK)
    sprite(r, art('s_clock'), 132, 16, {'K': '000000', 'F': WOOD['F'], 'm': PAL['m']}, BACK)
    # the plant in the back left corner, on the floor: its pot is in the way.
    # Leaves and pot are in tile rows of their own (the pot's rim on frame row
    # 63, a tile's top), so each gets two shades and the black.
    plant = art('s_plant')
    bb = plant.getbbox()
    pw, ph = bb[2] - bb[0], bb[3] - bb[1]
    px, fy, rim = 76, 69, 13                       # rim: the pot's first row in the drawing
    leaf = lambda x, y: y - bb[1] < rim
    sprite(r, plant, px, fy - ph + 1, {'K': '000000', 'g': '2c6c44', 'h': '4fa667'}, fy,
           cut=lambda x, y: not leaf(x, y))
    sprite(r, plant, px, fy - ph + 1, {'K': '000000', 'o': 'b6433d', 'l': 'ec8476'}, fy,
           cut=leaf, foot=[(x, y) for x in range(px + 3, px + pw - 3) for y in range(fy - 3, fy + 1)])
    return finish(r, 'house 0 nes', PAL)
