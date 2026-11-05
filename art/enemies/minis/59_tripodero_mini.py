"""59 Tripodero's map mini: the pipefish-snouted stilt-walker of the chaparral at the player's scale, four views,
two frames (tools/minis.py).

From its redraw (art/enemies/pixellab/59_tripodero, after abookofcreatures.com's tripodero, the user's
reference): drawn by hand, fill only, one black outline round it -- its green head and tube snout, its
striped orange hunch, two brown telescoping stilt legs and orange feet, its green tail down to the ground
beside them (its third leg). From behind the tail is nearest, so it is drawn over the legs. The right view
is the left mirrored. 18 px tall: its battle height (52 px) at the minis' one scale (28/79). Three of its
battle colours and black: its orange, its green, the light brown of its legs (its darker leg brown reads as black beside the outline).

Its chase: a steady stride straight at you on its stilts (the lore: legs extended it stands above the brush),
one stilt reaching out, then the other.

    python art/enemies/minis/59_tripodero_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'O': 'fc9838', 'G': '4fa667', 'B': '967448'}
CHASE = 'stride'        # no style of its own: straight at you at the chase pace
HEIGHT = 18

FRONT = [                                        # its head, the tube snout coming down at you, the striped hunch
    '...GGG...',
    '..GGGGG..',
    '..GKGKG..',
    '...GGG...',
    '..OOGOO..',
    '.OOOGOOO.',
    '.OGOGOGO.',
    '.OOGGGOO.',
    '..OOOOO..',
]
FRONT_LEGS = ([                                  # both stilts down, its tail beside the left
    '..B...B..',
    '..B...B..',
    '.GB...B..',
    '.GB...B..',
    '.GB....B.',
    'GGB....B.',
    '.OO....OO',
], [                                             # the left stilt lifted in its stride
    '..B...B..',
    '..B...B..',
    '.GB...B..',
    '.GOO..B..',
    '.G.....B.',
    'GG.....B.',
    '.......OO',
])
BACK = [                                         # its back: the stripes, no face
    '...GGG...',
    '..GGGGG..',
    '..GGGGG..',
    '...GGG...',
    '..OOOOO..',
    '.OGOGOGO.',
    '.OOGOGOO.',
    '.OGOGOGO.',
    '..OOOOO..',
]
BACK_LEGS = ([                                   # the tail nearest, down over the legs
    '..B.G.B..',
    '..B.G.B..',
    '..B.G.B..',
    '..B.G.B..',
    '.B..G..B.',
    '.B..GG.B.',
    'OO...GGOO',
], [
    '..B.G.B..',
    '..B.G.B..',
    '..B.G.B..',
    '..OOG.B..',
    '....G..B.',
    '....GG.B.',
    '.....GGOO',
])
SIDE = [                                         # its head to the left, the long snout out in front
    '.....GGG.......',
    '....GGKGG......',
    'GGGGGGGGO......',
    'G...OOOOOO.....',
    '....OGOGOOO....',
    '.....OOGOGOO...',
    '......OOOOOOO..',
]
SIDE_LEGS = ([                                   # one stilt reaching forward, one back, the tail to the ground
    '.......BB..OO..',
    '......B..B..OO.',
    '......B..B...G.',
    '.....B...B...G.',
    '.....B....B..G.',
    '....B.....B..GG',
    '....B......B..G',
    '...B.......B.GG',
    '..OO......OO..G',
], [                                             # the stilts swung the other way
    '.......BB..OO..',
    '.......BB...OO.',
    '.......B.B...G.',
    '.......B.B...G.',
    '.......B..B..G.',
    '.......B..B..GG',
    '.......B...B..G',
    '.......B...B.GG',
    '......OO...OO.G',
])


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(FRONT + legs) for legs in FRONT_LEGS], 'U': [place(BACK + legs) for legs in BACK_LEGS],
          'L': [place(SIDE + legs) for legs in SIDE_LEGS]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(59, 'tripodero', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(59, CHASE, FRAMES, PAL)
