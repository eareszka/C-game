"""26 Akhekh's frame 0 by hand from PixelLab's draft (idle_frame0_premerge.png, the draft on the sheet's
palette). The user, 2026-10-28: keep the eyes as they were before the colours were cut ("I like the old
eyes more") and "have the crown fit more". So the dark-brown eyes stay; the colours come down to eight and
black by folding the light gold and the white collar into the tan instead. The crown, which floated wide
above the head, is redrawn sitting on it: a gold band the width of the head's top, three small uraei
standing on it, a red sun disc over each, its own outline.

    python art/enemies/pixellab/26_akhekh/crown.py   -> idle_frame0_clean.png
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
X0 = 14               # the grid columns below are counted from here
GOLD, RED, BLACK = (0xd8, 0xa8, 0x00), (0xb7, 0x1c, 0x00), (0, 0, 0)
FOLD = {(0xf8, 0xd8, 0x78): (0xe0, 0xc0, 0x88), (0xfc, 0xfc, 0xfc): (0xe0, 0xc0, 0x88)}
CROWN = {               # (column, row): colour -- on the head's top (its outline is row 13, columns 9-15)
    **{(c, 9): RED for c in (10, 12, 14)},
    **{(c, 10): GOLD for c in (10, 12, 14)},
    **{(c, r): GOLD for c in range(9, 16) for r in (11, 12)},
}

im = Image.open(HERE / 'idle_frame0_premerge.png').convert('RGBA')
for y in range(im.height):
    for x in range(im.width):
        p = im.getpixel((x, y))
        if p[3] and p[:3] in FOLD:
            im.putpixel((x, y), FOLD[p[:3]] + (255,))
for y in range(7, 13):                       # the old crown off
    for x in range(X0 + 6, X0 + 20):
        im.putpixel((x, y), (0, 0, 0, 0))
for c in range(9, 17):                       # the head's top outline, whole again
    im.putpixel((X0 + c, 13), BLACK + (255,) if c < 16 else (0, 0, 0, 0))
for (c, r), col in CROWN.items():
    im.putpixel((X0 + c, r), col + (255,))
for (c, r) in CROWN:                         # its outline
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        q = (X0 + c + dx, r + dy)
        if not im.getpixel(q)[3]:
            im.putpixel(q, BLACK + (255,))
im.save(HERE / 'idle_frame0_clean.png')
print(len({p[:3] for p in im.get_flattened_data() if p[3]}) - 1, 'colours + black', im.getbbox())
