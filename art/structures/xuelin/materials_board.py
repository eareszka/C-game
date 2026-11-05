"""Xuelin's materials, for review: every one is a material the art bible
already names (tools/overworld_style.py MATERIALS), so none is drawn in a
second set of colours. Draws a swatch board, and a PixelLab draft remapped
onto these colours alone, to show the town's look before anything is drawn.

    python art/structures/xuelin/materials_board.py <draft.png> <out.png>
"""
import os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from overworld_style import MATERIALS

# what each is for in Xuelin -> the bible's material
USE = [
    ('grey brick walls (qingzhuan)', 'stone'),          # the bond in stone's three tones, pale joints
    ('roof tile',                    'slate'),
    ('snow on the roofs',            'snowpack'),
    ('red lacquer: doors, columns',  'red paint'),
    ('door studs, signboard gold',   'yellow paint'),
    ('beams, lattice, stalls',       'wood'),
    ('painted eaves (drum tower)',   'navy paint'),
    ('painted eaves (drum tower)',   'green paint'),
    ('lantern light',                'lamplight'),
    ('pines, as the snowfield',      'foliage'),
]


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lab(c):
    """sRGB -> CIELAB (D65), as art/direction/fcremap.py measures nearness."""
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = map(lin, c)
    X, Y, Z = (r * .4124 + g * .3576 + b * .1805) / .95047, r * .2126 + g * .7152 + b * .0722, (r * .0193 + g * .1192 + b * .9505) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return 116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))


def nearest(c, pal):
    L = lab(c)
    return min(pal, key=lambda p: sum((a - b) ** 2 for a, b in zip(L, lab(p))))


def main(draft, out):
    tones = [t for _, m in USE for t in MATERIALS[m]['tones']] + ['000000']
    pal = [hexrgb(t) for t in dict.fromkeys(tones)]
    im = Image.open(draft).convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 128:
                px[x, y] = (0, 0, 0, 0)
                continue
            px[x, y] = nearest((r, g, b), pal) + (255,)
    S = 3
    W, row = 900, 34
    board = Image.new('RGB', (W, 60 + row * len(USE) + im.height * S + 40), (30, 30, 36))
    d = ImageDraw.Draw(board)
    d.text((12, 10), 'Xuelin materials -- all already in the art bible (tools/overworld_style.py MATERIALS)', fill='white')
    y = 40
    for use, m in USE:
        x = 12
        for t in MATERIALS[m]['tones']:
            d.rectangle((x, y, x + 40, y + 24), fill=hexrgb(t), outline=(0, 0, 0))
            x += 46
        d.text((160, y + 6), '%s  =  %s  (%s)' % (use, m, ' '.join(MATERIALS[m]['tones'])), fill='white')
        y += row
    d.text((12, y + 6), 'Draft 3 (PixelLab), remapped onto these colours only -- the look, not the drawing:', fill='white')
    board.paste(Image.alpha_composite(Image.new('RGBA', im.size, (78, 110, 90, 255)), im).resize(
        (im.width * S, im.height * S), Image.NEAREST).convert('RGB'), (12, y + 28))
    board.save(out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
