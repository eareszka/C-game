"""95 Wendigo's mini, its source for PixelLab: the approved frame drawn by hand at mini size (a block shrink mushed it): skull with crimson eyes and fangs, ice horns, big arms ending in claws,
icicles between the legs. The left half, mirrored. Three colours and black: frost, ice, crimson.

    python art/enemies/pixellab/95_wendigo/mini/source.py
"""
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff
from PIL import Image
PAL = {'K': '000000', 'F': 'c6ccda', 'I': '84a7e9', 'R': 'b6433d'}
LEFT = [
    '...I...I......',
    '....I.I.......',
    '.....II....F.F',
    '......II..FFFF',
    '.......IIFFFFF',
    '........FFFFFF',
    '........FFKRFF',
    '.........FFFFF',
    '..FFF.FI.FKFKF',
    '.FFIFF.FFIFIFF',
    'FFI.FFFFIIIIFF',
    'FF...FFFIIIFFF',
    'FI...FFIIIIIII',
    'FF..F.IFFIIIII',
    '.FI.....IIIIII',
    '.F.F...FFIIIII',
    'F.F...FF.IIIII',
    '......FF..I.II',
    '....FFFF...I.I',
    '...FFF.F.....I',
]
ROWS = [r + r[-2::-1] for r in LEFT]
x0, y0 = minis.W // 2 - len(ROWS[0]) // 2, minis.H - 1 - len(ROWS)
g = ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(ROWS) for x, c in enumerate(r) if c != '.'})
im = ff.image(g, PAL, minis.W, minis.H)
print(im.getbbox())
print('\n'.join(l for l in ff.checks(g, PAL, minis.W, minis.H, cap=23, max_colours=3) if 'hue' not in l))
pad = Image.new('RGBA', (44, 44)); pad.paste(im, (2, 8)); pad.save(HERE / 'input.png')   # cell (x, y) lands at (x + 2, y + 8)
ff.image(g, PAL, minis.W, minis.H, bg=minis.GRASS).resize((minis.W * 10, minis.H * 10), 0).save(HERE / 'first_x10.png')
