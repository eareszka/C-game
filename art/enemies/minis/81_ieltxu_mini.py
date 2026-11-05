"""81 Ieltxu's map mini: the Basque night bird of fire, near black, at the player's scale, four views, two frames
(tools/minis.py).

Drawn by hand after its battle sheet (assets/enemies/81_ieltxu.png, kept as it is at the user's word), on the
Lagopus mini's layout: fill only, one black outline round it. Its near-black body and broad wings, their
upper edges lit its dark purple so the shape reads, its dull red eyes, its hooked beak; its wings beating --
up, then down -- as it hovers over its shadow. The right view is the left mirrored. 12 px tall: its battle
height (24 px) at the minis' one scale would be 9; 12 is the floor. Three of its colours and black: its near
black, its purple, the red of its eyes (its fire sheet's red, so they show).

Its chase: it flits (in battle it "flits about at random"): the jink, as the Ebigane's -- darting off one side,
then the other (chase_speed(), chase_bend(), mini_hover(), src/main.cpp; it flies, enemy_flies()).

    python art/enemies/minis/81_ieltxu_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'D': '14101e', 'P': '2b1f40', 'R': 'b6433d'}
CHASE = 'jink'
HOVER = 6               # mini_hover() in src/main.cpp: its shadow's half width
HEIGHT = 12

FRONT = [               # its head lit purple on top, its red eyes, its hooked beak, its dark body, its legs
    '..DDD..',
    '.PDDDP.',
    '.DRDRD.',
    '..DPD..',
    '.DDDDD.',
    'DDDDDDD',
    'DDDDDDD',
    '.PDDDP.',
    '..DPD..',
    '..D.D..',
]
BACK = [                # its back, no face, its tail
    '..DDD..',
    '.PDDDP.',
    '.DDDDD.',
    '..DDD..',
    '.DDDDD.',
    'DDDDDDD',
    'DDPDPDD',
    '.DKKKD.',
    '..KKK..',
    '..D.D..',
]
WING_UP = ['......', 'D.....', 'DD....', 'PDD...', '.PDDD.', '..PDDD', '...PDD', '......', '......', '......']
WING_DOWN = ['......', '......', '......', '......', '......', '...PDD', '..PDDD', '.PDDD.', 'PDD...', 'DP....']


def spread(body, wing):
    """The body with a wing out each side, the right the left mirrored."""
    return [w + r + w[::-1] for w, r in zip(wing, body)]


SIDE_UP = [             # its head to the left, its red eye, the near wing swept up and back, its tail out behind
    '......DDD..',
    '..DD.DDPP..',
    '.RDDDDPP...',
    'KDKDDDP....',
    '.DDDDDD....',
    '.DDDDDDDKK.',
    '..DDDDDDKK.',
    '..PDDDDP...',
    '...DPPD....',
    '...D..D....',
]
SIDE_DOWN = [           # the near wing beaten down past its side
    '...........',
    '..DD.......',
    '.RDD.......',
    'KDKDD......',
    '.DDDDDD....',
    '.DDDPPPDKK.',
    '..DDPDDPKK.',
    '..PDDPDDP..',
    '...DPPDPP..',
    '...D..D.D..',
]

def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(spread(FRONT, w)) for w in (WING_UP, WING_DOWN)], 'U': [place(spread(BACK, w)) for w in (WING_UP, WING_DOWN)],
          'L': [place(SIDE_UP), place(SIDE_DOWN)]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(81, 'ieltxu', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(81, CHASE, FRAMES, PAL, hover=HOVER)
