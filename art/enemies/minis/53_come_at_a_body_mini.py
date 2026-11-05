"""53 Come-at-a-body's map mini: the velvet-furred woodchuck of the White Mountains at the player's scale, four views,
two frames (tools/minis.py).

From its redraw (art/enemies/pixellab/53_come_at_a_body: frame 0 by hand, PixelLab's views with the bushy tail
drawn back on): the shrink of each view to 12 px was a smear, so each frame is drawn by hand after them, fill
only, one black outline round it; the back is the front's body, its tail between its legs. The right view is
the left mirrored. 12 px tall: its battle height (19 px) at the minis' one scale would be 7; 12 is the floor
every small one keeps (00-05, 50, 54). Three of its battle colours and black: its fur, its dark brown (the
tail's plume, the shade under it), its cream (muzzle, belly).

Its chase is the lore's (A Book of Creatures: it "runs directly at unsuspecting passers-by ... and comes to a
sudden halt a few inches away", then runs off): the surge, as the Grand Goule's -- a rush at you, then it
draws back -- in chase_speed() in src/main.cpp. Frame 0 its legs planted, frame 1 flung out running.

    python art/enemies/minis/53_come_at_a_body_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '94703d', 'D': '5c4616', 'C': 'cebe82'}
CHASE = 'surge'
HEIGHT = 12

FRONT = [                                        # sitting up: small round ears, its eyes, nose in the cream muzzle
    'M.....M',
    'MMMMMMM',
    'MKMMMKM',
    'MMCKCMM',
    '.MCCCM.',
    'MDCCCDM',
    'MMCCCMM',
    'MMCCCMM',
    'DMMMMMD',
]
BACK = [                                         # the front's body, the bushy tail down its back
    'M.....M',
    'MMMMMMM',
    'MMMMMMM',
    'MMMMMMM',
    '.MMMMM.',
    'MMMMMMM',
    'MMMDMMM',
    'MMDDDMM',
    'DMDDDMD',
]
FRONT_LEGS = (['.MM.MM.'], ['MM...MM'])          # planted, then flung out in the rush
SIDE = [                                         # its head to the left, low, the plume of its tail up behind
    '..M......DD.',
    '.MMM....DMMD',
    'MMKMM...DMMD',
    'CMMMMMMMDMD.',
    'CCMMMMMMMDD.',
    '.CMMMMMMMM..',
    '.CCMMMMMMM..',
    '.CCMMMMMMM..',
    '..DMMMMMMD..',
]
SIDE_LEGS = (['..M.M..M.M..'], ['.M..M.M..M..'])  # planted, then reaching out fore and aft


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(FRONT + legs) for legs in FRONT_LEGS], 'U': [place(BACK + legs) for legs in FRONT_LEGS],
          'L': [place(SIDE + legs) for legs in SIDE_LEGS]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(53, 'come_at_a_body', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(53, CHASE, FRAMES, PAL)
