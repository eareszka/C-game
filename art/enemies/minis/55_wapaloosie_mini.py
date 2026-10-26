"""55 Wapaloosie's map mini: the dachshund-sized critter of the Pacific Coast forests, velvet fur, woodpecker feet, a
spiked tail, humping at you like an inchworm, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet has a front and a side (its back is its side). Through PixelLab (art/enemies/pixellab/55_wapaloosie/
mini, pixellab-out/55-mini, two generations): its side and front at twice their size, each given an inchworm's hump --
arched high, then stretched out flat along the ground. The side came back as asked; the front did not (a blob grew
over its head), so its front stretch is its battle front with the hump let down. At 12 px the shrinks lose its
spikes and face, so each frame is drawn by hand after them, fill only, one black outline round it. Its back is its
front's body (the user, of 48: the views' proportions match), its face gone, its tail's spike where the face was.
The right view is the left mirrored. In the side's stretch its tail end stays where it was and its head goes on:
an inchworm reaching.
12 px tall: its battle height (15 px) at the minis' one scale would be 5; 12 is the floor every small one keeps.
Three of its battle colours and black: its red (velvet fur; its pink goes to it), its cream (muzzle, belly, the
yellow tips of its back spikes), its grey (woodpecker feet).

Its chase: the inch (chase_speed() and chase_frame(), src/main.cpp) -- stretched out as it reaches at you (frame 1),
arched while it gathers itself up (frame 0), hardly moving.

    python art/enemies/minis/55_wapaloosie_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'A': 'b6433d', 'B': 'e8e0c0', 'C': '848694'}
CHASE = 'inch'
HEIGHT = 12

# Fill only; its head to the left on the side. A red, B cream, C grey feet, K its eyes.
ARCH_SIDE = [                                    # PixelLab's side, frame 0: arched high
    '......B.....B....',
    '.....AAAAAAAA....',
    '....AAAAAAAAAA...',
    '.B.BAAAB...AAAA..',
    'AAAAAAAB....AAA..',
    'AKAAAAB.....AAAA.',
    'BBBAAAB.....AAAA.',
    '.BBAAA.......AAAA',
    '..CCCC......CCC..',
    '..CC.C......C.C..',
]
STRETCH_SIDE = [                                 # its frame 4: flat out along the ground
    '.B.B.....B.....B...',
    'AAAAAAAAAAAAAAAAA..',
    'AKAAAAAAAAAAAAAAAAA',
    'BBBBAAAAAAAAAAAAAAA',
    '..BBBBBBBBBBBBBAAA.',
    '..CCCC.......CCCC..',
]
ARCH_FRONT = [                                   # its battle front: the hump over its head
    '..AAA..',
    '.BAAAB.',
    '..AAA..',
    '.AAAAA.',
    '.AAAAA.',
    'AAKAKAA',
    'AABBBAA',
    '.BBBBB.',
    '.CC.CC.',
    '.CC.CC.',
]
STRETCH_FRONT = ARCH_FRONT[1:2] + ARCH_FRONT[4:]   # the hump let down
ARCH_BACK = [                                    # its front's body from behind: its tail's spike low in the middle
    '..AAA..',
    '.BAAAB.',
    '..AAA..',
    '.AAAAA.',
    '.AAAAA.',
    'AAAAAAA',
    'AAAAAAA',
    '.AABAA.',
    '.CC.CC.',
    '.CC.CC.',
]
STRETCH_BACK = ARCH_BACK[1:2] + ARCH_BACK[4:]


def place(rows, right=None):
    """Fill rows to a frame: centred (or its right end on column `right`), the bottom row on the cell's last but one."""
    x0 = right - len(rows[0]) + 1 if right else minis.W // 2 - len(rows[0]) // 2
    y0 = minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


RIGHT = minis.W // 2 + 9                         # the side's tail end, the same in both frames
FRAMES = {'D': [place(ARCH_FRONT), place(STRETCH_FRONT)], 'U': [place(ARCH_BACK), place(STRETCH_BACK)],
          'L': [place(ARCH_SIDE, RIGHT), place(STRETCH_SIDE, RIGHT)]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(55, 'wapaloosie', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(55, CHASE, FRAMES, PAL)
