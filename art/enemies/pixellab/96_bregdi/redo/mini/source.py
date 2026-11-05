"""96 Bregdi's mini, its source for PixelLab: half under the water, its head, open jaws and long fins over the surface, drawn by hand at mini size, side on as its battle sprite is. Three colours
and black: hide gray, fins taupe, water mint (the eye and teeth take the mint).

    python art/enemies/pixellab/96_bregdi/redo/mini/source.py
"""
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff
from PIL import Image
PAL = {'K': '000000', 'G': '848694', 'T': '8d6b4f', 'M': 'a8f0bc'}
ROWS = [
    '.....................TT.......',
    '.....................TTT......',
    '......................TTT.....',
    '......................TTTT....',
    '..GGGGGGGGG...........TTTT....',
    '.GGGGGGGGMGGG..........TTTT...',
    'GGGGGGGGGGGGGG........TTTT....',
    'GMKMKMKKKKKGGGG......TTTG.....',
    'KKKKKKKKKKKGGGGG...GGGGG......',
    '.GMGMGMGGGKGGGGGGGGGGGG.......',
    '..GGGGGGGGGGGGGGGGGGG.........',
    '....TTGGGGGGGGGGGGGG..........',
    '...TTT.GGGGGGGGGGG............',
    '..TTT..GGGGGGGGGG.............',
    'MM.T...GGGGGGGGGGMMM........MM',
    'MMMMMMMMGGGGGGGGGMMMMMMMMMMMMM',
    '.MMMMMMMMMMMMMMMMMMMMMMMMMMMM.',
]
assert len({len(r) for r in ROWS}) == 1
x0, y0 = minis.W // 2 - len(ROWS[0]) // 2, minis.H - 1 - len(ROWS)
g = ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(ROWS) for x, c in enumerate(r) if c != '.'})
im = ff.image(g, PAL, minis.W, minis.H)
print(im.getbbox())
print('\n'.join(l for l in ff.checks(g, PAL, minis.W, minis.H, cap=24, max_colours=3) if 'hue' not in l))
pad = Image.new('RGBA', (48, 48)); pad.paste(im, (4, 8)); pad.save(HERE / 'input.png')   # cell (x, y) lands at (x + 4, y + 8)
ff.image(g, PAL, minis.W, minis.H, bg=minis.GRASS).resize((minis.W * 10, minis.H * 10), 0).save(HERE / 'first_x10.png')
