"""Remap an enemy sheet's colours one for one, every frame, keeping every pixel's place.

    python tools/palette_remap.py SHEET.png OLD=NEW [OLD=NEW ...] [--out OUT.png] [--ms 260]

For a sprite whose drawing is right and only its values are not (Roperite's khaki on khaki):
the game PNG is remapped and installed over itself with enemy_sheet.install (old PNG and
.aseprite backed up to art/_backup/, .aseprite repacked with the same tags, frame time and the
new palette) -- so hit/rope/club coordinates measured on the art stay exact. Colours are hex
without '#'. With --out, writes only a preview PNG and changes nothing.
"""
import sys
from datetime import datetime
from pathlib import Path
from PIL import Image

import enemy_sheet


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def remap(im, table):
    im = im.convert('RGBA')
    out = im.copy()
    px, opx = im.load(), out.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a and (r, g, b) in table:
                opx[x, y] = table[(r, g, b)] + (a,)
    return out


def option(argv, name, default=None):
    if name not in argv:
        return argv, default
    i = argv.index(name)
    return argv[:i] + argv[i + 2:], argv[i + 1]


def main(argv):
    argv, out = option(argv, '--out')
    argv, ms = option(argv, '--ms', '260')
    png = Path(argv[0]).resolve()
    table = {rgb(a): rgb(b) for a, b in (pair.split('=') for pair in argv[1:])}
    sheet = remap(Image.open(png), table)
    if out:
        sheet.save(out)
        print(out)
        return
    rel = png.relative_to(enemy_sheet.ROOT).as_posix()
    frames, rows = next((f, r) for p, f, r in enemy_sheet.battle_sheets() if p == rel)
    palette = sorted({'%02x%02x%02x' % p[:3] for p in sheet.getdata() if p[3]})
    backup = Path(enemy_sheet.ROOT) / 'art/_backup' / ('remap_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    enemy_sheet.install(sheet, png, frames, rows, ms=int(ms), palette=palette, backup=str(backup))
    print(png, 'backup', backup)


if __name__ == '__main__':
    main(sys.argv[1:])
