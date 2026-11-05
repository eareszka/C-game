"""68 Shuyu's map mini: the four-headed red chicken of the Peng River at the player's scale, four views, two
frames (tools/minis.py).

From its redraw (art/enemies/pixellab/68_shuyu: PixelLab's frame 0 and front views, the backs built from the
fronts with the faces off and the tail fan over all): drawn by hand at 12 px, fill only, one black outline
round it. Its four heads in a row from the front, beakless from behind with its three tails fanned over its
back (the user: "tail should be drawn on top of everything if back faced"), stacked at its breast from the
side with the tails up behind. It flies (the user, 2026-10-28: "Have the mini fly. Not walk"): its wings
spread and beating, up then down, its feet tucked, hovering over its shadow. The right view is the
left mirrored. 12 px tall: its battle height (31 px) at the minis' one scale would be 11; 12 is the floor.
Three of its battle colours and black: its red, the dark red of its wings and tails, the yellow of its beaks
and feet.

Its chase: the swoop, as the Dingbat's -- a glide, then wingbeats (chase_speed(), mini_hover(), src/main.cpp).

    python art/enemies/minis/68_shuyu_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': 'b6433d', 'D': '792727', 'Y': 'f0bc3c'}
CHASE = 'swoop'         # a glide, then wingbeats (as the Dingbat's)
HOVER = 6               # mini_hover() in src/main.cpp: its shadow's half width
HEIGHT = 12

BODY = [                                         # four heads, each its beak, on a round red breast, feet tucked
    'MM.MM.MM.MM',
    'YM.MY.YM.MY',
    '.MMMMMMMMM.',
    'DMMMMMMMMMD',
    'DMMMMMMMMMD',
    '.DMMMMMMMD.',
    '..DDMMMDD..',
    '...Y...Y...',
]
BACK = [                                         # the backs of the heads; the tail fan over its back
    'MM.MM.MM.MM',
    'MM.MM.MM.MM',
    '.MMMMMMMMM.',
    'DMMDMDMDMMD',
    'DMMDDDDDMMD',
    '.DMDDDDDMD.',
    '..DDDDDDD..',
    '...Y...Y...',
]
# Its left wing beside the body, three columns a row: up, then down (a beat every 150 ms as it hovers).
WING_UP = ['D..', 'MD.', 'MMD', '.MM', '...', '...', '...', '...']
WING_DOWN = ['...', '...', '...', '.MM', 'MMD', 'MD.', 'D..', '...']


def spread(body, wing):
    """The body with a wing out each side, the right the left mirrored."""
    return [w + r + w[::-1] for w, r in zip(wing, body)]


SIDE_UP = [                                      # its head to the left; the near wing raised over its back
    '......D....',
    '.....DMD...',
    '.MM.MDMD...',
    'YMMYMMMD.DD',
    '.MMMMMD.DDD',
    '..MMMMMMDD.',
    '.MMMMMMMMD.',
    '..MMMMMMM..',
    '...DDDDD...',
    '....Y.Y....',
]
SIDE_DOWN = [                                    # the near wing beaten down along its side
    '...........',
    '...........',
    '.MM.MM.....',
    'YMMYMM...DD',
    '.MMMMM..DDD',
    '..MMMMMMDD.',
    '.MMMDDDDMD.',
    '..MMDDDDM..',
    '...DDDDD...',
    '....Y.Y....',
]

def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(spread(BODY, w)) for w in (WING_UP, WING_DOWN)], 'U': [place(spread(BACK, w)) for w in (WING_UP, WING_DOWN)],
          'L': [place(SIDE_UP), place(SIDE_DOWN)]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(68, 'shuyu', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(68, CHASE, FRAMES, PAL, hover=HOVER)
