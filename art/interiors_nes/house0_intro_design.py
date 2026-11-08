"""Room 0 on the intro's foggy night (docs/story.md): the dog's things stand
where the morning's will be. Its bed where the plant is, its bowl beside it,
where the opening chest is (the user, 2026-11-08: plant and chest after the intro, bowl
and bed in it; the chest of drawers in both). The chest is the game's
(src/main.cpp DEBUG_CHEST_X/Y), hidden while the intro runs; everything
else is house0_design.py's.

The game loads it as room 0 while the intro runs (src/interior.cpp). Run
this, not tools/interior_nes.py, so the morning's room_0 is left alone:

    python art/interiors_nes/house0_intro_design.py

It writes assets/interiors/room_0_intro.png, _depth.png and .txt, and
room_0_morning.*: the everyday room with the curtains still shut, for the
morning after until the day has come (the user, 2026-11-08).
"""
import os, shutil, sys, tempfile
DESIGNS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DESIGNS, '..', '..', 'tools'))
sys.path.insert(0, DESIGNS)
from interior_nes import *
from house0_design import PAL, WOOD, piece, curtains
import house0_design
from PIL import Image

FOOD = {'K': '000000', 'R': PAL['R'], 'U': '84a7e9', 'F': WOOD['F']}       # blue bowl, lit rim, kibble
BED  = {'K': '000000', 'W': PAL['W'], 'Z': PAL['Z'], 'm': PAL['m']}        # red rim, its shadow, cream cushion

# A dog bed, round and soft, its rim standing higher at the back: 20 x 10.
DOG_BED = [
    "....KKKKKKKKKKKK....",
    "..KKWWWWWWWWWWWWKK..",
    ".KWWZZZZZZZZZZZZWWK.",
    "KWWZmmmmmmmmmmmmZWWK",
    "KWZmmmmmmmmmmmmmmZWK",
    "KWWZmmmmmmmmmmmmZWWK",
    "KWWWZZZZZZZZZZZZWWWK",
    ".KWWWWWWWWWWWWWWWWK.",
    "..KZZZZZZZZZZZZZZK..",
    "...KKKKKKKKKKKKKK...",
]
# Its bowl, full: 10 x 5.
BOWL = [
    ".KKKKKKKK.",
    "KUFFFFFFUK",
    "KRUUUUUURK",
    ".KRRRRRRK.",
    "..KKKKKK..",
]


def draw(rows, tones):
    im = Image.new('RGBA', (len(rows[0]), len(rows)))
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != '.':
                im.putpixel((x, y), rgb(tones[c]) + (255,))
    return im


def standing(r, rows, tones, x0, fy, foot_rows):
    """A drawing on floor row fy, its left at x0; the bottom foot_rows rows of
    its middle are ground the feet can't cross."""
    im = draw(rows, tones)
    w, h = im.size
    sprite(r, im, x0, fy - h + 1, tones, fy,
           foot=[(x, y) for x in range(x0 + 1, x0 + w - 1) for y in range(fy - foot_rows + 1, fy + 1)])


def design():
    r = new_room()
    rug(r, 98, 114, 46, 14)
    piece(r, lambda: bed(r, 168, BACK + 8, flip=True), art('house0_B_bed'),
          {'K': '000000', 'R': PAL['R'], 'm': PAL['m']})
    piece(r, lambda: dresser(r, 112), art('house0_C_dresser'),          # in both rooms
          choices=['f0bc3c', '815423', '3c2412', 'fce4a0', 'c9a433'])
    curtains(r, closed=True)        # night: drawn shut
    sprite(r, art('s_picture'), 116, 22, {'K': '000000', 'U': '84a7e9', 'h': '4fa667'}, BACK)
    sprite(r, art('s_clock'), 132, 16, {'K': '000000', 'F': WOOD['F'], 'm': PAL['m']}, BACK)
    # The dog's bed in the back left corner, where the plant stands by day.
    standing(r, DOG_BED, BED, 73, 69, 4)
    # Its bowl beside the bed, where the opening chest stands by day (src/main.cpp
    # DEBUG_CHEST_X/Y: art pixels 94-109 x 54-69, the bowl centred on it).
    standing(r, BOWL, FOOD, 97, 68, 2)
    return finish(r, 'house 0 intro', PAL)


if __name__ == '__main__':
    out = os.path.join(DESIGNS, '..', '..', 'assets', 'interiors')
    for name, room in (('room_0_intro', design()), ('room_0_morning', house0_design.design(closed=True))):
        with tempfile.TemporaryDirectory() as tmp:
            export(0, room, out=tmp)
            for ext in ('.png', '_depth.png', '.txt'):
                shutil.copy(os.path.join(tmp, 'room_0' + ext), os.path.join(out, name + ext))
    print('room 0 intro and morning written')
