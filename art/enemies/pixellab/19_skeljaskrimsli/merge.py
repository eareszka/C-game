"""19 Skeljaskrimsli's frame 0 down to eight colours and black: the clean's near-duplicates folded into four
blue-grey shell tones, the fur's brown, two greens for the teeth; the plates' near-black seams turned to
black separation lines (the bible's shared lines at overlaps; the user: "bible checks").

    python art/enemies/pixellab/19_skeljaskrimsli/merge.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
MERGE = {'292931': '1e1e24', '0c0a12': '1e1e24', '474751': '34343e', 'c6ccda': 'bcbeca', 'a4aaba': '848694',
         'e8e0c0': 'fcfcfc', '4fa667': 'a8f0bc', '9797aa': '848694', '235436': '1e1e24', '0e2016': '1e1e24', '163623': '1e1e24'}   # the look of the user's second reference: charcoal fur, grey banded plates, white claws, green glow
im = Image.open(HERE / 'idle_frame0_clean.png').convert('RGBA')
for y in range(im.height):
    for x in range(im.width):
        p = im.getpixel((x, y))
        k = '%02x%02x%02x' % p[:3]
        if p[3] and k in MERGE:
            im.putpixel((x, y), h(MERGE[k]) + (255,))
# Interior black kept to lines: a black pixel inside the body (all four sides drawn) with three or four black
# neighbours is part of a blob, not a seam -- it takes the plates' dark shade. Until the bible's band (9-14%).
SHADE, BLACK = h('1e1e24'), (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
inside = lambda im, x, y: all(0 <= x + dx < im.width and 0 <= y + dy < im.height and im.getpixel((x + dx, y + dy))[3] for dx, dy in N4)
def interior(im):
    drawn = [(x, y) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3]]
    return sum(1 for x, y in drawn if im.getpixel((x, y))[:3] == BLACK and inside(im, x, y)) / len(drawn)
for need in (4, 3):
    if interior(im) <= 0.14:
        break
    blob = [(x, y) for y in range(im.height) for x in range(im.width)
            if im.getpixel((x, y))[3] and im.getpixel((x, y))[:3] == BLACK and inside(im, x, y)
            and sum(im.getpixel((x + dx, y + dy))[:3] == BLACK for dx, dy in N4) >= need]
    for p in blob:
        im.putpixel(p, SHADE + (255,))
print('interior black %.1f%%' % (100 * interior(im)))
im.save(HERE / 'idle_frame0_clean.png')
# (frame 0 is the turned pose now; idle_frame0_side.png stays the side it was made from)
print(len({p[:3] for p in im.get_flattened_data() if p[3]}) - 1, 'colours + black')
