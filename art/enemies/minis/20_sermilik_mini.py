"""20 Sermilik's map mini: the ice-clad polar bear of Aasiaat at the player's scale, four views, two frames
(tools/minis.py).

From its redraw (art/enemies/pixellab/20_sermilik): drawn by hand, fill only, one black outline round it. Its
great head, small dark eyes and nose over an ice-blue muzzle, its long fur white along its back and shading to
grey below, hints of ice-blue icicles in it, its four paws lumps of blue ice. It lumbers at you, its legs
stepping (frame 0, frame 1). The right view is the left mirrored. 17 px tall, a little over its battle height
(44 px) at the minis' one scale (16): the last minis the user wanted bigger. Three of its battle colours and
black: its white, its grey, its ice blue.

Its chase: a slow heavy lumber straight at you, as the Sasnalkahi's (chase_speed(), src/main.cpp).

    python art/enemies/minis/20_sermilik_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'W': 'fcfcfc', 'G': 'a4aaba', 'B': 'dcf0ff'}
CHASE = 'plod'
HEIGHT = 17

FRONT = [                # its head lowered between its great humped shoulders, outlined on its own: the ears, the small
    '.....WWWWWWWWWWW.....',   # dark eyes, the ice-blue muzzle and nose, the dark open mouth; white above, grey below
    '...WWWWWWWWWWWWWWW...',
    '..WWWWWWWWWWWWWWWWW..',
    '.WWWWWKWWWWWWWKWWWWW.',
    'WWWWWKWKKKKKKKWKWWWWW',
    'WWWWGKWWWWWWWWWKGWWWW',
    'WWWGGKWKWWWWWKWKGGWWW',
    'WWGGGKWWWBBBWWWKGGGWW',
    'WGGGGKWWWBKBWWWKGGGGW',
    'GGGGGGKWWKKKWWKGGGGGG',
    'GGGGGGGKKKKKKKGGGGGGG',
    'GGBGGGGGGGGGGGGGGGBGG',
    'GBGBGGGGGGGGGGGGGBGBG',
]
BACK = [                 # its back: the great hump, the white of its iced fur down its spine, its stub of a tail
    '.....WWWWWWWWWWW.....',
    '...WWWWWWWWWWWWWWW...',
    '..WWWWWWWWWWWWWWWWW..',
    '.WWWWWWWWWWWWWWWWWWW.',
    'WWWWWWWWWWWWWWWWWWWWW',
    'WWWWGWWWWWWWWWWWGWWWW',
    'WWWGGGWWWWWWWWWGGGWWW',
    'WWGGGGGWWWWWWWGGGGGWW',
    'WGGGGGGGWWWWWGGGGGGGW',
    'GGGGGGGGGWWWGGGGGGGGG',
    'GGGGGGGGGGWGGGGGGGGGG',
    'GGBGGGGGGGGGGGGGGGBGG',
    'GBGBGGGGGGGGGGGGGBGBG',
]
LEGS = (['.GGG...GGG.GGG...GGG.', '.BBB...BBB.BBB...BBB.'],     # its legs planted on their ice,
        ['.GGG...GGG.GGG...GGG.', '..BBB..BBB.BBB..BBB..'])     # then stepping
SIDE = [                 # its head to the left, low, its great iced back humped behind
    '.....WW..................',
    '...WWWWW......WWWWWWW....',
    '..WWWWWWW..WWWWWWWWWWWW..',
    '.WKWWWWWWWWWWWWWWWWWWWWW.',
    'BWWWWWWWWWWWWWWWWWWWWWWWW',
    'KBWWWWGWWWWWWWWWWWWWWWWWW',
    '.BBWGGGGWWWWWWWWWWWWWGGGG',
    '..GGGGGGGGGGGGGGGGGGGGGGG',
    '...GGBGGGGGGGGGGGGGGGBGG.',
    '...GGGG.GGGGGGGGGGGGGGG..',
]
SIDE_LEGS = (['...GGG..GGG.......GGG.GGG', '...BBB..BBB.......BBB.BBB'],
             ['....GGG.GGG......GGG.GGG.', '....BBB.BBB......BBB.BBB.'])
for rows in (FRONT, BACK, SIDE) + LEGS + SIDE_LEGS:
    assert len({len(r) for r in rows}) == 1, rows


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(FRONT + legs) for legs in LEGS], 'U': [place(BACK + legs) for legs in LEGS],
          'L': [place(SIDE + legs) for legs in SIDE_LEGS]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(20, 'sermilik', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(20, CHASE, FRAMES, PAL)
