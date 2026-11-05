"""78 Zankallala's map mini: the hairy trickster in his beehive hat, riding his jerboa, at the player's scale, four
views, two frames (tools/minis.py).

Drawn by hand after its battle sheet (assets/enemies/78_zankallala.png), fill only, one black outline round it:
the striped beehive hat, the dark hairy rider and his eyes, the tan jerboa under him with its long ears, its
long tail with its dark tuft. A jerboa goes in long two-legged hops, so it bounds: stretched out in the leap
(frame 0), gathered on landing (frame 1), as the Snawfus's and the Billdad's. The right view is the left
mirrored. 14 px tall: its battle height (40 px) at the minis' one scale (28/79). Three of its battle colours
and black: the jerboa's tan, the rider's dark brown, the hat's gold (the staff's green goes).

Its chase: the bound (chase_speed() and chase_frame(), src/main.cpp) -- a leap, a landing.

    python art/enemies/minis/78_zankallala_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'T': 'b29e5c', 'D': '3c2412', 'Y': 'd89830'}
CHASE = 'bound'
HEIGHT = 14

HAT = [                 # the beehive hat over the rider, his eyes
    '....YYY....',
    '...DDDDD...',
    '...YYYYY...',
]
FRONT_LEAP = HAT + [    # up off its hind legs, the jerboa's ears up either side of him
    '.T.DKDKD.T.',
    '.TTDDDDDTT.',
    '..TTDDDTT..',
    '..TTTTTTT..',
    '..TKTTTKT..',
    '...TTTTT...',
    '...TTTTT...',
    '...T...T...',
    '..TT...TT..',
]
FRONT_LAND = HAT + [    # crouched on landing
    '.T.DKDKD.T.',
    '.TTDDDDDTT.',
    '..TTDDDTT..',
    '..TTTTTTT..',
    '..TKTTTKT..',
    '.TTTTTTTTT.',
    '.TTT...TTT.',
]
BACK_LEAP = HAT + [     # his back, the jerboa's back, its tail's tuft out to one side
    '.T.DDDDD.T.',
    '.TTDDDDDTT.',
    '..TTDDDTT..',
    '..TTTTTTT..',
    '..TTTTTTT..',
    '...TTTTT...',
    '...TTTTTDD.',
    '...T...T.DD',
    '..TT...TT..',
]
BACK_LAND = HAT + [
    '.T.DDDDD.T.',
    '.TTDDDDDTT.',
    '..TTDDDTT..',
    '..TTTTTTT..',
    '..TTTTTTT..',
    '.TTTTTTTTDD',
    '.TTT...TTDD',
]
SIDE_LEAP = [           # its head to the left: the rider on its back, its long tail out behind, stretched in the leap
    '.......YYY......',
    '......DDDDD.....',
    '......YYYYY.....',
    '.TT...DKDDD.....',
    '.TTT..DDDDD.....',
    '..TTTTTDDDTT....',
    '.TKTTTTTTTTTTTTD',
    'TTTTTTTTTTTT..DD',
    '...TTTTTTTT.....',
    '.......TT.......',
    '........TT......',
    '.........TTT....',
]
SIDE_LAND = [           # gathered on landing, its tail curled up
    '.......YYY......',
    '......DDDDD.....',
    '......YYYYY.....',
    '.TT...DKDDD.....',
    '.TTT..DDDDD...DD',
    '..TTTTTDDDTT..DD',
    '.TKTTTTTTTTTTT..',
    'TTTTTTTTTTTT....',
    '...TTTTTTTTT....',
    '....TTT..TTT....',
]


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(FRONT_LEAP), place(FRONT_LAND)], 'U': [place(BACK_LEAP), place(BACK_LAND)],
          'L': [place(SIDE_LEAP), place(SIDE_LAND)]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(78, 'zankallala', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(78, CHASE, FRAMES, PAL)
