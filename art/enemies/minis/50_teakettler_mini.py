"""50 Teakettler's map mini: the little Northwoods kettle-dog at the player's scale, four views, two frames (tools/minis.py).

From its PixelLab redraw (art/enemies/pixellab/50_teakettler): the front, back and side frame 0s shrunk to 12 px
(python tools/minis.py's shrink) were a smear of ears, so each frame is drawn by hand after them, fill only, one
black outline round it; the back is the front's body with the ears' backs dark and its tail stub. The right view
is the left mirrored. 12 px tall: its battle height (22 px) at the minis' one scale would be 8; 12 is the floor
every small one keeps (00-05, 54). Three of its battle colours and black: its brown, its dark brown, the pink of
its ears.

It walks backwards by choice (the lore; the user, 2026-10-28: "the enemy should chase the player backwards"):
mini_backwards() in src/main.cpp shows the view opposite the way it goes, so it trots at you tail first, its
legs stepping toward its tail (frame 0 legs forward, frame 1 back). A steady trot, straight at you.

    python art/enemies/minis/50_teakettler_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '8d6b4f', 'D': '463422', 'P': 'ec8476'}
CHASE = 'trot'          # no style of its own: straight at you at the chase pace
HEIGHT = 12

FRONT = [                                        # big upright ears lined pink, its eyes and nose
    'M.....M',
    'MP...PM',
    'MPMMMPM',
    'MMMMMMM',
    'MKMMMKM',
    '.MMKMM.',
    '.DMMMD.',
    '.MMMMM.',
]
BACK = [                                         # the front's body: the ears' backs dark, its tail stub
    'M.....M',
    'MD...DM',
    'MDMMMDM',
    'MMMMMMM',
    'MMMMMMM',
    '.MMMMM.',
    '.MMDMM.',
    '.MDDDM.',
]
FRONT_LEGS = (['.M...M.', '.M.....'], ['.M...M.', '.....M.'])   # one foreleg up, then the other
SIDE = [                                         # its head to the left, the curled tail up behind
    '..M.........',
    '.MPM........',
    '.MPMM....DD.',
    'MMKMMM...DD.',
    'KMMMMMMMMMD.',
    '.DMMMMMMMMM.',
    '...MMMMMMMM.',
    '...MDMMMDMM.',
]
SIDE_LEGS = (['...M.M..M.M.', '..M...M..M..'],   # legs reaching toward its nose,
             ['...M.M..M.M.', '....M..M...M'])   # then stepping back toward its tail (it walks backwards)


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(FRONT + legs) for legs in FRONT_LEGS], 'U': [place(BACK + legs) for legs in FRONT_LEGS],
          'L': [place(SIDE + legs) for legs in SIDE_LEGS]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(50, 'teakettler', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(50, CHASE, FRAMES, PAL, backwards=True)
