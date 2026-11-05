"""43 Sazae-oni's map mini: the turban sea-snail turned demon at the player's scale, four views, two frames
(tools/minis.py).

Drawn by hand after its battle sheet (kept as drawn, moved onto the game palette: art/enemies/pixellab/43_sazae_oni),
fill only, one black outline round it. Its spiky khaki turban shell, spines out round its whorls, and in the
shell's mouth the red oni face: eyes, a grin of teeth. Frame 0 it sits in its shell, frame 1 it leans out
grinning, its mouth wider, as it does in battle. From behind, the shell's spiral; from the side, the shell's
spire up behind, the red face out at the front, its foot along the ground. The right view is the left mirrored.
15 px tall, over its battle height (30 px) at the minis' one scale (11): the user has wanted the minis bigger.
Three of its battle colours and black: its shell khaki, the shell's dark, its demon red.

Its chase: a slow creep straight at you -- a sea snail (chase_speed(), src/main.cpp).

    python art/enemies/minis/43_sazae_oni_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'P': 'b29e5c', 'D': '605028', 'R': 'b6433d'}
CHASE = 'plod'
HEIGHT = 15

SHELL = [                # the spire, its whorls and their dark lines
    '......D......',
    '.....DPD.....',
    '.....PPP.....',
    '....DPPPD....',
    '....PPPPP....',
    '..PDPPPPPDP..',
]
FACES = ([               # in its shell: eyes, a closed grin
    'P.PPRRRRRPP.P',
    'PPPRKRRRKRPPP',
    '.PPRRRRRRRPP.',
    'P.PRKPKPKRP.P',
    '.PPRRRRRRRPP.',
    '..DDDDDDDDD..',
], [                     # leaning out grinning, its mouth wide
    'P.PRRRRRRRP.P',
    'PPRRKRRRKRRPP',
    '.PRRRRRRRRRP.',
    'P.RKPKPKPKR.P',
    '.PRKKKKKKKRP.',
    '..DRPKPKPRD..',
])
FOOT = ['..DDDDDDDDD..']
BACK = SHELL + [         # from behind: the shell's spiral, its spines
    'P.PPPDPPPPP.P',
    'PPPDPPPDPPPPP',
    '.PPPPPPPDPPP.',
    'P.PDPPPPPPP.P',
    '.PPPPDPPPPPP.',
    '..DDDDDDDDD..',
]
SIDE = ([                # its head to the left: the spire up behind, the red face out at the front, its foot
    '..........D....',
    '.........DPD...',
    '........DPPPD..',
    '.......DPPPPPP.',
    '......PPDPPPPPD',
    '.....PPPPPDPPPP',
    '.RRRPPPPPPPPDPP',
    'RKRRRPPPPPPPPPP',
    'RRRRRPPDPPPPPPD',
    'RPKPRDPPPPPPDP.',
    '.RRRDDDDDDDDDD.',
    '.DDDDDDDDDDDDD.',
], [                     # leaning out, its jaw dropped
    '..........D....',
    '.........DPD...',
    '........DPPPD..',
    '.......DPPPPPP.',
    '......PPDPPPPPD',
    '.RRR.PPPPPDPPPP',
    'RKRRRPPPPPPPDPP',
    'RRRRRPPPPPPPPPP',
    'RKPKRPPDPPPPPPD',
    'RKKKRDPPPPPPDP.',
    'RPKPRDDDDDDDDD.',
    '.DDDDDDDDDDDDD.',
])
for rows in (SHELL, BACK, FOOT) + FACES + SIDE:
    assert len({len(r) for r in rows}) == 1, rows


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(SHELL + face + FOOT) for face in FACES], 'U': [place(BACK + FOOT), place(BACK + FOOT)],
          'L': [place(side) for side in SIDE]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(43, 'sazae_oni', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(43, CHASE, FRAMES, PAL)
