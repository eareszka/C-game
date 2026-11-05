"""53 Come-at-a-body's frame 0, drawn by hand (PixelLab's edit copied its reference in three times: the user,
2026-10-28, chose a hand redraw). The sitting woodchuck front-on in its own five colours: a big round head lit on
top, small round ears, a cream muzzle with its nose and mouth line, a dark shadow under the chin, forepaws held
at the cream belly, feet lit on top.

    python art/enemies/pixellab/53_come_at_a_body/hand_frame0.py   -> idle_frame0_clean.png
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
PAL = {'K': (0, 0, 0), 'D': (0x5c, 0x46, 0x16), 'M': (0x94, 0x70, 0x3d), 'L': (0xc1, 0x8a, 0x39), 'C': (0xce, 0xbe, 0x82)}
X, Y = 12, 9          # where the grid's top left sits on the 42x29 canvas (the source's place)
ROWS = [
    '....KK.......KK....',
    '...KLDK.....KDLK...',
    '...KLDKKKKKKKDLK...',
    '....KLLLLLLLLLK....',
    '...KLLMMMMMMMLLK...',
    '...KMMMMMMMMMMMK...',
    '...KMMKMMMMMKMMK...',
    '...KMMMCCCCCMMMK...',
    '...KDMCCCKCCCMDK...',
    '....KDMCCKCCMDK....',
    '...KLKKDDDDDKKLK...',
    '..KLLMKCCCCCKMLLK..',
    '..KLMMKCCCCCKMMLK..',
    '..KMMMKCCCCCKMMMK..',
    '..KMMMCCCCCCCMMMK..',
    '..KDMMMCCCCCMMMDK..',
    '..KDDMMMMMMMMMDDK..',
    '..KLLMKKKKKKKMLLK..',
    '...KKK.......KKK...',
]
assert all(len(r) == 19 for r in ROWS)
im = Image.new('RGBA', (42, 29))
for y, r in enumerate(ROWS):
    for x, c in enumerate(r):
        if c != '.': im.putpixel((X + x, Y + y), PAL[c] + (255,))
im.save(HERE / 'idle_frame0_clean.png')
print(im.size, im.getbbox())
