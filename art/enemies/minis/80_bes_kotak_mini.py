"""80 Bes Kotak's map mini: the Jah Hut box spirit of the muddy hollows at the player's scale, four views, two
frames (tools/minis.py).

From its redraw (art/enemies/pixellab/80_bes_kotak, the tongue taken out at the user's word): drawn by hand,
fill only, one black outline round it. A blocky wooden chest, its lid lighter, its glowing square eyes, its
mouth slot, its block arms. Two frames: the lid shut, then the lid lifted off (a black gap under it) and the
mouth gaping -- as in battle. It floats, never walking: it hovers over its shadow. The right view is the
left mirrored. 13 px tall: its battle height (37 px) at the minis' one scale (28/79). Three of its battle
colours and black: the lid's light wood, the box's mid wood, its yellow eyes (the mouth is the black).

Its chase: slow and heavy, a floating chest (chase_speed(), mini_hover(), src/main.cpp; it flies,
enemy_flies() in include/enemy.h).

    python art/enemies/minis/80_bes_kotak_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'L': 'b2966a', 'M': '785830', 'Y': 'f0bc3c'}
CHASE = 'plod'
HOVER = 7               # mini_hover() in src/main.cpp: its shadow's half width
HEIGHT = 13

LID = ['.LLLLLLLLLLL.', '.LLLLLLLLLLL.']
GAP = ['.............']      # the lid lifted: its outline and the box's make a black gap
FRONT = [                    # its eyes, its block arms, its mouth slot
    '..MMMMMMMMM..',
    '..MYYMMMYYM..',
    'M.MYYMMMYYM.M',
    'MMMMMMMMMMMMM',
    'MMMKKKKKKKMMM',
    '..MMMMMMMMM..',
    '..MMMMMMMMM..',
    '..MMMMMMMMM..',
]
FRONT_OPEN = FRONT[:5] + ['..MKKKKKKKM..'] + FRONT[6:]   # the mouth gaping
BACK = [
    '..MMMMMMMMM..',
    '..MMMMMMMMM..',
    'M.MMMMMMMMM.M',
    'MMMMMMMMMMMMM',
    'MMMMMMMMMMMMM',
    '..MMMMMMMMM..',
    '..MMMMMMMMM..',
    '..MMMMMMMMM..',
]
SIDE_LID = ['..LLLLLLLL.', '..LLLLLLLL.']
SIDE = [                     # side on, facing left: an eye's glow at its front edge, an arm out ahead
    '...MMMMMMM.',
    '...YMMMMMM.',
    'M..YMMMMMM.',
    'MMMMMMMMMM.',
    'MMMKMMMMMM.',
    '...MMMMMMM.',
    '...MMMMMMM.',
    '...MMMMMMM.',
]
SIDE_OPEN = SIDE[:4] + ['MMMKMMMMMM.', '...KMMMMMM.'] + SIDE[6:]
SIDE_GAP = ['...........']


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(LID + FRONT), place(LID + GAP + FRONT_OPEN)], 'U': [place(LID + BACK), place(LID + GAP + BACK)],
          'L': [place(SIDE_LID + SIDE), place(SIDE_LID + SIDE_GAP + SIDE_OPEN)]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(80, 'bes_kotak', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(80, CHASE, FRAMES, PAL, hover=HOVER)
