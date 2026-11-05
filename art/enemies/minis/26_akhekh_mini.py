"""26 Akhekh's map mini: the winged, falcon-headed antelope of the desert's edge at the player's scale, four views,
two frames (tools/minis.py).

From its redraw (art/enemies/pixellab/26_akhekh: PixelLab's frame 0 with the user's old eyes kept and the crown
fitted to the head by hand): drawn by hand at 12 px, fill only, one black outline round it. Its crown of three
uraei on a gold band, its falcon face, its tan body, its blue wings spread and beating -- up, then down --
as it hovers over its shadow (it hangs in the air in battle). The right view is the left mirrored. 12 px tall:
its battle height (35 px) at the minis' one scale would be 12. Three of its battle colours and black: its tan,
its blue, the gold of its crown (the green of its serpent tail goes, so the crown can stay; the tail is tan).

Its chase: the swoop, as the Shuyu's and the Dingbat's -- a glide, then wingbeats (chase_speed(),
mini_hover(), src/main.cpp; it flies, enemy_flies() in include/enemy.h).

    python art/enemies/minis/26_akhekh_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'T': 'cebe82', 'B': '2850a0', 'Y': 'f0bc3c'}   # the game palette's nearest to its tan, blue, gold (its own are off it)
CHASE = 'swoop'
HOVER = 7               # mini_hover() in src/main.cpp: its shadow's half width
HEIGHT = 12

FRONT = [               # the crown's three uraei on its band, its falcon face, the tan body, its legs, the tail's curl
    'Y.Y.Y',
    'YYYYY',
    'TKTKT',
    '.TTT.',
    '..T..',
    '.TTT.',
    'TTTTT',
    'TTTTT',
    '.T.T.',
    '..TT.',
]
BACK = [                # the crown from behind, no face
    'Y.Y.Y',
    'YYYYY',
    'TTTTT',
    '.TTT.',
    '..T..',
    '.TTT.',
    'TTTTT',
    'TTTTT',
    '.T.T.',
    '.TT..',
]
WING_UP = ['......', '......', 'B.....', 'BB....', '.BBB..', '..BBBB', '...BBB', '......', '......', '......']
WING_DOWN = ['......', '......', '......', '......', '......', '......', '...BBB', '..BBBB', '.BBB..', 'BB....']


def spread(body, wing):
    """The body with a wing out each side, the right the left mirrored."""
    return [w + r + w[::-1] for w, r in zip(wing, body)]


SIDE_UP = [             # its head to the left, the near wing raised over its back
    '.Y.Y.Y.....',
    '.YYYYY..B..',
    'TTKTTT.BB..',
    '..TTT.BBB..',
    '...TTBBB...',
    '...TTTTTT..',
    '..TTTTTTTT.',
    '...TTTTTT..',
    '....T..T...',
    '.....TTT...',
]
SIDE_DOWN = [           # the near wing beaten down along its side
    '.Y.Y.Y.....',
    '.YYYYY.....',
    'TTKTTT.....',
    '..TTT......',
    '...TT......',
    '...TTTTTT..',
    '..TTBBBBTT.',
    '...TBBBBT..',
    '....TBB.T..',
    '.....TTT...',
]


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(spread(FRONT, w)) for w in (WING_UP, WING_DOWN)], 'U': [place(spread(BACK, w)) for w in (WING_UP, WING_DOWN)],
          'L': [place(SIDE_UP), place(SIDE_DOWN)]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(26, 'akhekh', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(26, CHASE, FRAMES, PAL, hover=HOVER)
