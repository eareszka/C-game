"""42 Nykur's map mini: the dapple-grey water horse of Iceland at the player's scale, four views, two frames
(tools/minis.py).

From its redraw (art/enemies/pixellab/42_nykur): drawn by hand, fill only, one black outline round it. Its long
grey face, pricked ears, dark eyes, pale muzzle and nostrils, the dark weedy mane hanging either side of its
neck, pale dapples on its coat, dark hooves. From the side it gallops -- stretched out (frame 0), then gathered
(frame 1) -- its weedy tail streaming. The right view is the left mirrored. 17 px tall, a little over its
battle height (39 px) at the minis' one scale (14): the user has wanted the minis bigger. Three of its battle
colours and black: its grey, its pale grey, its weed green.

Its chase: the dash (chase_speed(), src/main.cpp) -- a gallop straight at you, then a breath: it tempts riders
and runs off into the water with them.

    python art/enemies/minis/42_nykur_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '848694', 'L': 'bcbeca', 'N': '235436'}
CHASE = 'dash'
HEIGHT = 17

FRONT = [                # its long face: ears, eyes, the weedy mane framing it, the long pale muzzle and nostrils; dappled chest
    '....G.G....',
    '....GGG....',
    '...NGGGN...',
    '...NKGKN...',
    '...NGGGN...',
    '...NGGGN...',
    '....GLG....',
    '....LLL....',
    '....KLK....',
    '..GGGGGGG..',
    '.GGLGGGLGG.',
    '.GGGGGGGGG.',
]
FRONT_LEGS = (['..GG...GG..', '..GG...GG..', '..KK...KK..'],     # its long legs, dark hooves,
              ['..GG...GG..', '...GG.GG...', '...KK.KK...'])     # then stepping in
BACK = [                 # its mane down its long neck, the wide rump, its weedy tail
    '....G.G....',
    '....GGG....',
    '....GNG....',
    '....GNG....',
    '....GNG....',
    '...GGNGG...',
    '..GGGNGGG..',
    '.GGGGGGGGG.',
    '.GGGGNGGGG.',
    'GGGGGNGGGGG',
    'GGGGNNNGGGG',
    '.GGGNNNGGG.',
]
BACK_LEGS = (['..GG.N.GG..', '..GG...GG..', '..KK...KK..'],
             ['..GG.N.GG..', '...GG.GG...', '...KK.KK...'])
SIDE = [                 # its head to the left, up on its long neck, the weedy mane down it, its tail out behind
    '..GG..............',
    '.GGGG.............',
    'GKGGGN............',
    'GGGGGNN...........',
    '.LGGGGNN..........',
    '..L.GGGNN.........',
    '....GGGGNGGGGGGG..',
    '....GGGGGGGGGGGGGN',
    '....GLGGGGLGGGGGNN',
    '....GGGGGGGGGGGG.N',
    '.....GGGGGGGGGG...',
]
SIDE_LEGS = (['.....GG......GG...', '....GG........GG..', '...GG..........GG.', '..KK............KK'],   # stretched out in the gallop
             ['......GG....GG....', '......GG....GG....', '.....GG....GG.....', '.....KK....KK.....'])   # gathered under it
for rows in (FRONT, BACK, SIDE) + FRONT_LEGS + BACK_LEGS + SIDE_LEGS:
    assert len({len(r) for r in rows}) == 1, rows


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(FRONT + legs) for legs in FRONT_LEGS], 'U': [place(BACK + legs) for legs in BACK_LEGS],
          'L': [place(SIDE + legs) for legs in SIDE_LEGS]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(42, 'nykur', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(42, CHASE, FRAMES, PAL)
