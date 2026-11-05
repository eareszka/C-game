"""90 Chipekwe redo: frame 0 from the picked concept (the user, 2026-11-03: concepts/c3.png, built from A Book of Creatures: hairless,
smooth, dark, one ivory horn). A long-necked lake reptile on the standard 98x65 frame, facing left.

PixelLab's 9 colours fold onto the palette: a dark green hide and its shade, charcoal for the far legs, ivory and its shade for the
horn and claws. By hand: the concept had no mouth, so a jaw line and two teeth; its one red pixel becomes a 2 px eye mark. One closed
black outline; its feet on the frame's last row but one.

    python art/enemies/pixellab/90_chipekwe/redo/views.py   # writes frame0.png, frame0_x8.png
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / '83_beast_of_barrisdale'))
import tidy as tidy_mod

W, H = 98, 65
K = (0, 0, 0)
HIDE, SHADE, FAR = (0x23, 0x54, 0x36), (0x16, 0x36, 0x23), (0x29, 0x29, 0x31)
IVORY, IVORY_D, RED = (0xe8, 0xe0, 0xc0), (0x84, 0x86, 0x94), (0xb6, 0x43, 0x3d)
FOLD = {'485046': HIDE, '332e2b': FAR, '262320': FAR, '1d1b19': K, '151412': K, 'd8d3be': IVORY, '908581': IVORY_D, 'f6f6f6': IVORY, 'cb3359': RED}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
EYE = ((20, 28), (21, 28))                                   # source coordinates
JAW = ((16, 33), (17, 33), (18, 34), (19, 34), (20, 34), (21, 34), (22, 34), (23, 34), (24, 34), (25, 33), (26, 33), (27, 33))
TEETH = ((19, 33), (22, 33))


def main():
    im = Image.open(HERE / 'concepts/c3.png').convert('RGBA')
    g = {(x, y): FOLD['%02x%02x%02x' % im.getpixel((x, y))[:3]] for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    # light by form: the hide's lower half of each mass in its shade, a few rows above any black or far-leg edge below it
    for (x, y), c in list(g.items()):
        if c == HIDE and any(g.get((x, y + d)) in (K, FAR, None) for d in (1, 2)) and y > 26:
            g[x, y] = SHADE
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    for p in JAW: g[p] = K
    for p in TEETH: g[p] = IVORY
    for p in EYE: g[p] = RED
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = W // 2 - (min(xs) + max(xs) + 1) // 2, H - 2 - max(ys)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items(): out.putpixel((x + dx, y + dy), c + (255,))
    tidy_mod.SHADE = SHADE
    tidy_mod.KEEP = {IVORY, RED}
    tidy_mod.tidy(out)
    for p in JAW: out.putpixel((p[0] + dx, p[1] + dy), K + (255,))
    out.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    print('offset', dx, dy, 'bbox', out.getbbox(), Counter('%02x%02x%02x' % p[:3] for p in out.get_flattened_data() if p[3]))


main()
