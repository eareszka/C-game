"""54 Billdad's map mini: the beaver of Boundary Pond on a kangaroo's hind legs, its hawk's bill and flat tail,
bounding at you -- it clears sixty rods in a leap -- at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet has a front, a back and a side. Through PixelLab (art/enemies/pixellab/54_billdad/mini,
pixellab-out/54-mini, four generations): eight rotations of its front at twice its size, then its front, back and
left side each given a bound -- crouched, then up off its long hind legs, its tail out behind. Their shrink to 12 px
was a blob with no face, so each frame is drawn by hand after it, fill only, one black outline round it; the back is
the front's body, its tail behind. The right view is the left mirrored.
12 px tall: its battle height (21 px) at the minis' one scale would be 7; 12 is the floor every small one keeps
(00-05, 22, 24, 33). Three of its battle colours and black: its tan (body), its brown (tail), its pale tan (belly,
muzzle).

Its chase: the bound (as the Snawfus's, chase_speed() and chase_frame(), src/main.cpp) -- a leap, stretched up off its
legs (frame 0), then a landing, crouched (frame 1).

    python art/enemies/minis/54_billdad_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': 'd7a175', 'D': '8d6b4f', 'L': 'f0b890'}
CHASE = 'bound'
HEIGHT = 12
# Drawn by hand, fill only (one outline goes round each at the end), from the shrink of PixelLab's leaps
# (pixellab-out/54-mini: the front, back and left each crouched, then up off its hind legs): at 12 px the shrink
# itself is a blob with no face. Its head to the left on the side; M tan, L pale (bill, belly), D brown (tail),
# K its eye. Each: (lift off the ground, rows).
LEAP_SIDE = (2, [                                # up off its long hind legs, its tail straight out behind
    '..MMM.........',
    '.MKMMM........',
    'LLMMMMM.......',
    '...LMMMMM.....',
    '...LLMMMMMM...',
    '....LMMMMMMDD.',
    '....M.MMM.DDDD',
    '.......MM..DDD',
    '........MM....',
    '.........MMMM.',
])
CROUCH_SIDE = (0, [                              # gathered on its haunches, its tail flat on the ground
    '..MMM.........',
    '.MKMM.........',
    'LLMMM.........',
    '..MMMM........',
    '..LMMMM.......',
    '.MLMMMMM......',
    '..LMMMMMM.....',
    '..LMMMMMMDDDD.',
    '...MMMMMMDDDDD',
    '.MMMM.MMMM.DDD',
])
LEAP_FRONT = (2, [                               # stretched up, its forepaws out, its tail hanging behind
    '.M....M..',
    '.MMMMMM..',
    '.MKMMKM..',
    '.MMLLMM..',
    'M.MLLM.M.',
    '.MMLLMM..',
    '..MLLM...',
    '..MLLMDD.',
    '..M..M.DD',
    '.MM..MM..',
])
CROUCH_FRONT = (0, [                             # squat on its haunches, its tail out to its left
    '.M....M....',
    '.MMMMMM....',
    '.MKMMKM....',
    '.MMLLMM....',
    '..MLLM.....',
    '.MMLLMM....',
    'MMLLLLMM...',
    'MMLLLLMMDD.',
    'MMMLLMMMDDD',
    'MMM..MMMDDD',
])
LEAP_BACK = (2, [                                # its front's body (the user, of 48: the views' proportions match)
    '.M....M.',
    '.MMMMMM.',
    '.MMMMMM.',
    '.MMMMMM.',
    'M.MMMM.M',
    '.MMMMMM.',
    '..MMMM..',
    '..MDDM..',
    '..MDDM..',
    '.MMDDMM.',
])
CROUCH_BACK = (0, [                              # its tail flat on the ground behind it
    '.M....M.',
    '.MMMMMM.',
    '.MMMMMM.',
    '.MMMMMM.',
    '..MMMM..',
    '.MMMMMM.',
    'MMMMMMMM',
    'MMMDDMMM',
    'MMDDDDMM',
    'MMDDDDMM',
])


def place(lift, rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it), lift up."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - lift - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(*LEAP_FRONT), place(*CROUCH_FRONT)], 'U': [place(*LEAP_BACK), place(*CROUCH_BACK)],
          'L': [place(*LEAP_SIDE), place(*CROUCH_SIDE)]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(54, 'billdad', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(54, CHASE, FRAMES, PAL)
