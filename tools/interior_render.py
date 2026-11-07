"""Render each room in include/interiors.h as the game draws it -- the room's
cells, then the furniture layer over them -- from assets/tileset.png.

    python tools/interior_render.py OUTDIR            # room_N.png (320x240) and room_N_crop.png (the walls' box)
"""
import os, re, sys
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
COLS = 256


def rooms():
    src = open(os.path.join(ROOT, 'include', 'interiors.h')).read()
    out = {}
    for m in re.finditer(r'interior_(\d+)_(tiles|furn)\[IMAP_H\]\[IMAP_W\] = \{(.*?)\n\};', src, re.S):
        rows = [[int(v) for v in r.split(',') if v.strip()] for r in re.findall(r'\{([^{}]*)\}', m.group(3))]
        out.setdefault(int(m.group(1)), {})[m.group(2)] = rows
    return out


def render(sheet, room, bg=(0, 0, 0, 255)):
    im = Image.new('RGBA', (320, 240), bg)
    for layer in ('tiles', 'furn'):
        for y, row in enumerate(room[layer]):
            for x, v in enumerate(row):
                if v >= 6:
                    i = v - 6
                    cell = sheet.crop(((i % COLS) * 16, (i // COLS) * 16, (i % COLS) * 16 + 16, (i // COLS) * 16 + 16))
                    im.alpha_composite(cell, (x * 16, y * 16))
    return im


if __name__ == '__main__':
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    sheet = Image.open(os.path.join(ROOT, 'assets', 'tileset.png')).convert('RGBA')
    px = sheet.load()                                    # the game's colour key: pure red is clear
    data = [(0, 0, 0, 0) if p[:3] == (255, 0, 0) else p for p in sheet.getdata()]
    sheet.putdata(data)
    for n, room in sorted(rooms().items()):
        im = render(sheet, room)
        im.save(os.path.join(out, f'room_{n}.png'))
        im.crop((32, 48, 288, 192)).save(os.path.join(out, f'room_{n}_crop.png'))
        print(n)
