"""67 Lagopus's map mini: the great snow ptarmigan at the player's scale, four views, two frames (tools/minis.py).

From its redraw (art/enemies/pixellab/67_lagopus): drawn by hand at 12 px, fill only, one black outline round
it. Its round white body, the red combs over its eyes, its feathered feet, its dark tail, its white wings
shaded grey, spread and beating -- up, then down -- as it hovers over its shadow (it perches and flies in
battle). The right view is the left mirrored. 12 px tall: its battle height (30 px) at the minis' one scale
would be 11; 12 is the floor. Three of its battle colours and black: its white, its grey, its red combs (the
tail's near-black is the outline's black).

Its chase: the swoop, as the Akhekh's and the Shuyu's -- a glide, then wingbeats (chase_speed(), mini_hover(),
src/main.cpp; it flies, enemy_flies() in include/enemy.h).

    python art/enemies/minis/67_lagopus_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'W': 'fcfcfc', 'G': 'bcbeca', 'R': 'b6433d'}
CHASE = 'swoop'
HOVER = 7               # mini_hover() in src/main.cpp: its shadow's half width
HEIGHT = 12

FRONT = [               # its head, the red combs over its eyes, its beak, the round white breast, feathered feet
    '..WWW..',
    '.RWWWR.',
    '.WKWKW.',
    '..WKW..',
    '.WWWWW.',
    'WWWWWWW',
    'WWWWWWW',
    '.GWWWG.',
    '..WGW..',
    '..W.W..',
]
BACK = [                # its back, no face, its dark tail
    '..WWW..',
    '.RWWWR.',
    '.WWWWW.',
    '..WWW..',
    '.WWWWW.',
    'WWWWWWW',
    'WWGWGWW',
    '.WKKKW.',
    '..KKK..',
    '..W.W..',
]
WING_UP = ['......', 'W.....', 'WW....', 'GWW...', '.GWWW.', '..GWWW', '...GWW', '......', '......', '......']
WING_DOWN = ['......', '......', '......', '......', '......', '...GWW', '..GWWW', '.GWWW.', 'GWW...', 'WG....']


def spread(body, wing):
    """The body with a wing out each side, the right the left mirrored."""
    return [w + r + w[::-1] for w, r in zip(wing, body)]


SIDE_UP = [             # its head to the left, the near wing swept up and back over its back, its tail out behind
    '......WWW..',
    '..WW.WWGG..',
    '.RWWWWGG...',
    'KWKWWWG....',
    '.WWWWWW....',
    '.WWWWWWWKK.',
    '..WWWWWWKK.',
    '..GWWWWG...',
    '...WGGW....',
    '...W..W....',
]
SIDE_DOWN = [           # the near wing beaten down past its side
    '...........',
    '..WW.......',
    '.RWW.......',
    'KWKWW......',
    '.WWWWWW....',
    '.WWWGGGWKK.',
    '..WWGWWGKK.',
    '..GWWGWWG..',
    '...WGGWGG..',
    '...W..W.W..',
]

def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(spread(FRONT, w)) for w in (WING_UP, WING_DOWN)], 'U': [place(spread(BACK, w)) for w in (WING_UP, WING_DOWN)],
          'L': [place(SIDE_UP), place(SIDE_DOWN)]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(67, 'lagopus', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(67, CHASE, FRAMES, PAL, hover=HOVER)
