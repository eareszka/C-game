"""Drawing helpers for draw.py. Everything is hard pixels: no scaling, blur or blending.

    from pix import *

    PAL = {'a': 'f0b890', 'b': 'b6433d'}            # letter -> palette hex; '.' is empty, 'K' is black

    im = grid(['..aa..', '.abba.', '..aa..'], PAL)  # small sprites: one letter per pixel
    im = grid(mirror(['..a', '.ab', '..a']), PAL)   # the same, each row mirrored around its right end

    im = canvas(200, 120)                           # big sprites: draw on a canvas with the shapes below
    rect(im, 10, 10, 40, 20, 'f0b890')              # x, y, width, height, colour
    poly(im, [(0, 0), (30, 0), (15, 40)], 'b6433d') # filled polygon
    oval(im, 20, 20, 60, 30, 'f0b890')              # x, y, width, height, colour
    stamp(im, grid(['aa', 'ab'], PAL), 50, 60)      # paste a tile or part; empty pixels stay as they are
    tile(im, grid(['ab', 'ba'], PAL), 10, 10, 40, 20, within='f0b890')  # repeat a tile over an area, only on that colour

    im = outline(im)                                # adds the 1 px black outline round the silhouette, growing the frame by 2
    save(im)                                        # writes sprite.png, trimmed to what is drawn. Call it last.

Draw fill only, then call outline() once at the end.
"""
from PIL import Image, ImageDraw

BLACK = (0, 0, 0, 255)
CLEAR = (0, 0, 0, 0)


def rgba(colour):
    if isinstance(colour, str):
        return tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    return tuple(colour[:3]) + (255,)


def grid(rows, pal):
    width = max(len(r) for r in rows)
    im = Image.new('RGBA', (width, len(rows)), CLEAR)
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '.' or ch == ' ':
                continue
            px[x, y] = BLACK if ch == 'K' else rgba(pal[ch])
    return im


def mirror(rows):
    return [r + r[-2::-1] for r in rows]


def canvas(w, h):
    return Image.new('RGBA', (w, h), CLEAR)


def rect(im, x, y, w, h, colour):
    ImageDraw.Draw(im).rectangle((x, y, x + w - 1, y + h - 1), fill=rgba(colour))


def poly(im, points, colour):
    ImageDraw.Draw(im).polygon(points, fill=rgba(colour))


def oval(im, x, y, w, h, colour):
    ImageDraw.Draw(im).ellipse((x, y, x + w - 1, y + h - 1), fill=rgba(colour))


def stamp(im, part, x, y):
    im.alpha_composite(part, (x, y))


def tile(im, part, x, y, w, h, within=None):
    want = rgba(within) if within else None
    src, dst = part.load(), im.load()
    for yy in range(y, min(y + h, im.height)):
        for xx in range(x, min(x + w, im.width)):
            c = src[(xx - x) % part.width, (yy - y) % part.height]
            if c[3] and (want is None or dst[xx, yy] == want):
                dst[xx, yy] = c


def outline(im):
    big = Image.new('RGBA', (im.width + 2, im.height + 2), CLEAR)
    big.alpha_composite(im, (1, 1))
    src = big.copy().load()
    px = big.load()
    for y in range(big.height):
        for x in range(big.width):
            if src[x, y][3]:
                continue
            if any(0 <= x + a < big.width and 0 <= y + b < big.height and src[x + a, y + b][3] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = BLACK
    return big


def save(im):
    box = im.getbbox()
    if box is None:
        raise SystemExit('nothing drawn')
    im.crop(box).save('sprite.png')
