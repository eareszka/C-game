"""19 Skeljaskrimsli's map mini, redrawn for its new battle art (art/enemies/pixellab/19_skeljaskrimsli: the
user's ink pose, the second reference's look, its head all mouth): at the player's scale, four views, two
frames (tools/minis.py). The old mini (the earlier creature) is kept in old_19/.

Drawn by hand, fill only, one black outline round it, with the detail of its battle shrink (minis.shrink) built
in (the user: "more detail ... not intimidating"): its great hunched dome of overlapping shell plates, lit pale
with charcoal undersides and black seams, spiked tips along its crest; under it, from the front, its whole face one gaping maw of glowing green fangs round a black throat (no
eyes); from behind, the dome over its dark haunches; from the side, hunched, the maw low at its front. Its
thick dark legs step (frame 0, frame 1). The right view is the left mirrored. 20 px tall, bigger than its battle
height (34 px) at the minis' one scale would make it (12; the user: "needs to be bigger"). Three of its battle colours and
black (the overworld's most): its plate grey, its charcoal, its glow green; pale claws in the plate grey.

Its chase: the plod, slow and steady (chase_speed() case 19, src/main.cpp).

    python art/enemies/minis/19_skeljaskrimsli_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'P': 'bcbeca', 'C': '1e1e24', 'G': 'a8f0bc'}
CHASE = 'plod'
HEIGHT = 20               # bigger than its battle height at the one scale (12): the user, "needs to be bigger"
COLOURS = 3               # the overworld bible's most for an object; the plates' undersides take the charcoal

DOME = [                 # spiked plate tips along its crest, overlapping plates lit pale, shaded mid grey, black seams
    '.......P...P...P.....',
    '.....PPPPPPPPPPPPP...',
    '...PPPPCKPPPPCKPPPP..',
    '..PPPCCKPPPPCCKPPPPP.',
    '.PPCKPPPPPCKPPPPPCKP.',
    '.PCCKPPPPCCKPPPPCCKPP',
    'PPPPPCKPPPPPCKPPPPPCP',
]
FRONT = DOME + [         # the plates' shadowed edge, then its whole face one maw: long fangs top and bottom, black throat
    'CCCCCCCCCCCCCCCCCCCCC',
    'CCCGGGGGGGGGGGGGGGCCC',
    'CCGKGKKGKKGKKGKKGKGCC',
    'CCGKGKKGKKGKKGKKGKGCC',
    'CCGKKKKKKKKKKKKKKKGCC',
    'CCGKKGKKGKKGKKGKKKGCC',
    'CCCGGGGGGGGGGGGGGGCCC',
    '.CCCCCCCCCCCCCCCCCCC.',
]
BACK = DOME + [          # from behind: the plates down over its dark haunches
    'PPCKPPPPPCKPPPPPCKPPP',
    'CCCCCCCCCCCCCCCCCCCCC',
    'CCCCCCCCCCCCCCCCCCCCC',
    '.CCCCCCCCCKCCCCCCCCC.',
    '.CCCCCCCCCKCCCCCCCCC.',
    '.CCCCCCCC...CCCCCCCC.',
]
LEGS = (['.CCCC...........CCCC.', '.CCCCC.........CCCCC.', '.P.P.P.........P.P.P.'],    # planted, its pale claws
        ['.CCCC...........CCCC.', '..CCCCC.......CCCCC..', '..P.P.P.......P.P.P..'])    # stepping
SIDE = [                 # its head to the left, lowered: the plated dome, the maw open at its front, fangs top and bottom
    '..........P...P...P......',
    '........PPPPPPPPPPPPP....',
    '......PPPPCKPPPPCKPPPPP..',
    '....PPPPCCKPPPPCCKPPPPPP.',
    '...PPCKPPPPPCKPPPPPCKPPPP',
    '..PCCKPPPPCCKPPPPCCKPPPPP',
    '.PPPPCKPPPPPCKPPPPPCKPPPP',
    'CCCCCCCCCCCCCCCCCCCCCCCCC',
    'GGGGGGGCCCCCCCCCCCCCCCCCC',
    'KGKGKGGCCCCCCCCCCCCCCCCCC',
    'KKKKKKGCCCCCCCCCCCCCCCCC.',
    'KKKKKKGCCCCCCCCCCCCCCCCC.',
    'KGKGKGGCCCCCCCCCCCCCCCC..',
    'GGGGGGCCCCCCCCCCCCCCCCC..',
    '.CCCCCCCCCCCCCCCCCCCCC...',
]
SIDE_LEGS = (['..CCCC.........CCCC.....', '.CCCCC........CCCCC.....', '.P.P.P........P.P.P.....'],
             ['..CCCC.........CCCC.....', '..CCCCC........CCCCC....', '..P.P.P........P.P.P....'])
for rows in (FRONT, BACK, SIDE) + LEGS + SIDE_LEGS:
    assert len({len(r) for r in rows}) == 1, rows

def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(FRONT + legs) for legs in LEGS], 'U': [place(BACK + legs) for legs in LEGS],
          'L': [place(SIDE + legs) for legs in SIDE_LEGS]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(19, 'skeljaskrimsli', FRAMES, PAL, cap=HEIGHT, colours=COLOURS)
    minis.chase_gif(19, CHASE, FRAMES, PAL)
