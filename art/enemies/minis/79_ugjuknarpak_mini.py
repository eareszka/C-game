"""79 Ugjuknarpak's map mini: the giant tusked seal of Kodiak, reared up like a bear, with its long pink rat's
tail, at the player's scale, four views, two frames (tools/minis.py).

From its redraw (art/enemies/pixellab/79_ugjuknarpak: frame 0 with the user's long pink curled rat tail, the
views reassigned by eye): drawn by hand, fill only, one black outline round it. Reared up on its hind
flippers, its pale ears, eyes and two long ivory tusks, its clawed fists up, its bare pink tail curling on the
ground behind it. It lumbers at you upright, a step at a time (frame 0 one foot forward, frame 1 the other).
The right view is the left mirrored. 17 px tall: its battle height (47 px) at the minis' one scale (28/79).
Three of its battle colours and black: its grey hide, its ivory (tusks, ears, claws), its pink tail.

Its chase: a slow heavy lumber straight at you, as the Sasnalkahi's (chase_speed(), src/main.cpp).

    python art/enemies/minis/79_ugjuknarpak_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '848694', 'C': 'e8e0c0', 'P': 'ec8476'}
CHASE = 'plod'
HEIGHT = 17

FRONT = [                # its ears, its eyes, the two tusks down its chest, its fists up either side
    '.....C.......C...',
    '.....CMMMMMMMC...',
    '.....MMKMMMKMM...',
    '.....MMMCMCMMM...',
    '...C.MMMCMCMMM.C.',
    '...CMMMMCMCMMMMC.',
    '....MMMMCMCMMMM..',
    '.....MMMMMMMMM...',
    '.....MMMMMMMMM...',
    'P....MMMMMMMMM...',
    'P....MMMMMMMMM...',
    'PP....MMMMMMM....',
    '.PPPPPMMM.MMM....',
]
BACK = [                 # its back; the tail nearest, curling out from under it
    '.....C.......C...',
    '.....CMMMMMMMC...',
    '.....MMMMMMMMM...',
    '.....MMMMMMMMM...',
    '...C.MMMMMMMMM.C.',
    '...CMMMMMMMMMMMC.',
    '....MMMMMMMMMMM..',
    '.....MMMMMMMMM...',
    '.....MMMMMMMMM...',
    '.....MMMMMMMMM..P',
    '.....MMMMMMMMM..P',
    '......MMMPMMM..PP',
    '......MMMPPPPPPP.',
]
FRONT_LEGS = (['......MM...MM....', '.....MMM...MMM...'],    # one foot forward,
              ['......MM...MM....', '......MMM.MMM....'])    # then the other
SIDE = [                 # its head to the left, the tusks down, a fist out in front, the tail curling behind
    '...C.C...........',
    '..MMMMM..........',
    '.MKMMMMM.........',
    '.MMMMMMMM........',
    '.CMMMMMMMM.......',
    'CC.MMMMMMMM......',
    'CC.MMMMMMMMM.....',
    '...MMMMMMMMM.....',
    '...MMMMMMMMM....P',
    '....MMMMMMMM...PP',
    '....MMMMMMMM..P.P',
    '.....MMMMMMMPP...',
    '.....MMMMMM......',
]
SIDE_LEGS = (['.....MM..MM......', '....MMM..MMM.....'],
             ['......MM..MM.....', '.....MMM..MMM....'])


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(FRONT + legs) for legs in FRONT_LEGS], 'U': [place(BACK + legs) for legs in FRONT_LEGS],
          'L': [place(SIDE + legs) for legs in SIDE_LEGS]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(79, 'ugjuknarpak', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(79, CHASE, FRAMES, PAL)
