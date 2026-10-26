"""Angont's PixelLab draft mapped to the project palette by hand, with shaded poison skulls.

    python tools/angont_recolor.py DRAFT.png green|gold OUT.png

The draft's olive has no palette neighbour (nearest-colour snapping turns it brown), so each
draft colour gets a chosen palette entry: `green` makes the snake forest green, `gold` a mustard
olive. The skulls (and eyes) were one flat neon; they become a pale poison ramp, shaded on their
lower-right edges, with the darkest tone where the skull meets its outline.
"""
import sys
from PIL import Image


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


BODY = {  # draft colour -> palette colour
    'green': {'6e7339': '29633e', '33351e': '163623', '383b21': '163623', 'bea469': 'b29e5c'},
    'gold':  {'6e7339': '7b601d', '33351e': '493712', '383b21': '493712', 'bea469': 'd0c078'},
}
SKULL = 'a5f14c'
SKULL_LIGHT, SKULL_MID = 'a8f0bc', '4edc4a'


def recolor(im, variant):
    im = im.convert('RGBA')
    out = im.copy()
    w, h = im.size
    hexes = {(x, y): '%02x%02x%02x' % im.getpixel((x, y))[:3] for y in range(h) for x in range(w) if im.getpixel((x, y))[3]}

    def edge(x, y):   # a skull pixel whose right or lower neighbour is not skull: the shaded side
        return any(hexes.get(n) != SKULL for n in ((x + 1, y), (x, y + 1)))
    for (x, y), hx in hexes.items():
        if hx == '000000':
            new = hx
        elif hx == SKULL:
            new = SKULL_MID if edge(x, y) else SKULL_LIGHT
        else:
            new = BODY[variant][hx]
        out.putpixel((x, y), rgb(new) + (255,))
    return out


if __name__ == '__main__':
    src, variant, dst = sys.argv[1:4]
    recolor(Image.open(src), variant).save(dst)
    print(dst)
