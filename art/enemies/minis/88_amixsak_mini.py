"""88 Amixsak's map mini: the Yupik walrus hide risen as a vengeful monster, at the player's scale, four views,
two frames (tools/minis.py) -- swimming SUBMERGED (the user, 2026-10-29: the battle sprite out of the water,
"its mini be the submerged chase").

Drawn by hand after its redesigned battle sheet (art/enemies/pixellab/88_amixsak, the hollow hide), fill only,
one black outline round it. Under the water all but what breaks the surface, as it rises under a skin boat:
frame 0 it lurks, only the top of its brown head, its eye dots and nostrils and its two long pale tusks over the
water; frame 1 it seizes, risen higher with both flippers flung up over the water, as it reaches them over a
boat's gunwales. From behind, the hump of the empty hide, the flippers rising in the seize; from the side, the
head and tusk at the front, the hide's hump behind. The right view is the left mirrored. Three colours and
black: its brown, its tusks' pale, the pale mint of the water round it (as 85 Nanabolele's).

Its chase: the pounce (chase_speed(), chase_frame(), src/main.cpp) -- lurking still under the water, then a
lunge, the seize frame in the lunge.

    python art/enemies/minis/88_amixsak_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'B': '8d6b4f', 'T': 'fce4a0', 'M': 'a8f0bc'}
CHASE = 'pounce'
HEIGHT = 13

FRONT = ([               # lurking: the top of its head, eye dots, nostrils, its tusks running down into the water
    '....BBBBB....',
    '...BBBBBBB...',
    '..BBKBBBKBB..',
    '..BBBBBBBBB..',
    '..BBBKBKBBB..',
    '.M.BTBBBTB.M.',
    'MMMMTMMMTMMMM',
    '.MMMMMMMMMMM.',
], [                     # the seize: risen, both flippers flung up, the tusks clear of the water
    'B...........B',
    'BB..BBBBB..BB',
    '.BBBBBBBBBBB.',
    '..BBKBBBKBB..',
    '..BBBBBBBBB..',
    '..BBBKBKBBB..',
    '..BBTBBBTBB..',
    '...BTBBBTB...',
    '.M..T...T..M.',
    'MMMMMMMMMMMMM',
    '.MMMMMMMMMMM.',
])
BACK = ([                # from behind: the hump of the empty hide over the water
    '....BBBBB....',
    '...BBBBBBB...',
    '..BBBBBBBBB..',
    '.M.BBBBBBB.M.',
    'MMMMBBBBBMMMM',
    '.MMMMMMMMMMM.',
], [                     # the seize: its flippers flung up either side
    'B...........B',
    'BB..BBBBB..BB',
    '.BBBBBBBBBBB.',
    '..BBBBBBBBB..',
    '..BBBBBBBBB..',
    '.M.BBBBBBB.M.',
    'MMMMBBBBBMMMM',
    '.MMMMMMMMMMM.',
])
SIDE = ([                # its head to the left, low: eye, a tusk down into the water, the hide's hump behind
    '...BBBB...........',
    '.BBBBBBB.....BB...',
    'BKBBBBBBB..BBBBBB.',
    'BBBBBBBBBBBBBBBBBB',
    '.TBBBBBBBBBBBBBBB.',
    'MTMMMMMMMMMMMMMMMM',
    '.MMMMM.MMMMMM.MMM.',
], [                     # the seize: head raised, a flipper flung up and over
    '..........B.......',
    '...BBBB..BB.......',
    '.BBBBBBBBB........',
    'BKBBBBBBB.....BB..',
    'BBBBBBBBBBBBBBBBB.',
    '.TBBBBBBBBBBBBBBBB',
    '.TBBBBBBBBBBBBBBB.',
    'MTMMMMMMMMMMMMMMMM',
    '.MMMMM.MMMMMM.MMM.',
])
for rows in FRONT + BACK + SIDE:
    assert len({len(r) for r in rows}) == 1, rows


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(r) for r in FRONT], 'U': [place(r) for r in BACK], 'L': [place(r) for r in SIDE]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(88, 'amixsak', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(88, CHASE, FRAMES, PAL)
