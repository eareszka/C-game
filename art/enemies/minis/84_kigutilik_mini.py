"""84 Kigutilik's map mini: the huge hairless stilt-legged beast of the central Arctic's Inuit at the player's
scale, four views, two frames (tools/minis.py).

Drawn by hand after its battle sheet (kept as drawn, its colours brought to eight: art/enemies/pixellab/
84_kigutilik), fill only, one black outline round it. The cup-shaped bowl up on its stalk from the top of its
head, its walrus head, small pale glinting eyes, its dark open mouth and two long ivory tusks hanging, its bulk behind, high
on four long stilt legs, dark on their far sides. From behind, its two tentacle tails curling over its rump;
from the side, its long body, the head low at the front, the tails curling up behind. It strides, its legs
stretched out (frame 0) then gathered (frame 1). The right view is the left mirrored. 22 px tall, over its
battle height (54 px) at the minis' one scale (19): the user has wanted the minis bigger. Three of its battle
colours and black: its violet, its dark violet, its ivory.

Its chase: the dash (chase_speed(), src/main.cpp) -- long strides on its stilts straight at you, then a breath.

    python art/enemies/minis/84_kigutilik_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'V': '664b95', 'D': '3b2a58', 'I': 'c6ccda'}
CHASE = 'dash'
HEIGHT = 22

CUP = [                  # the flat bowl up on its stalk, dark inside, clear of its head
    '.....DDDDDDD.....',
    '.....VVVVVVV.....',
    '........V........',
    '........V........',
    '........V........',
]
FRONT = CUP + [          # its walrus head framed before its humped bulk: pale glinting eyes, the open mouth, the tusks
    '.VVVVVVVVVVVVVVV.',
    'VVVDVVVVVVVVVDVVV',
    'VVVDVIVVVVVIVDVVV',
    'VVVDVVVVVVVVVDVVV',
    'DVVDVVKKKKKVVDVVD',
    'DDVDVVIKKKIVVDVDD',
    'DDDDVVIKKKIVVDDDD',
    '.DDDDDIDDDIDDDDD.',
]
BACK = CUP + [           # the back of its head, its rump, the two tentacle tails curling down over it
    '.VVVVVVVVVVVVVVV.',
    'VVVVVVVVVVVVVVVVV',
    'VVVVVVDVVVDVVVVVV',
    'VVVVVDVDVDVDVVVVV',
    'DVVVVDVVVVVDVVVVD',
    'DDVVVVDVVVDVVVVDD',
    'DDDVVVVDVDVVVVDDD',
    '.DDDDDDDDDDDDDDD.',
]
STILTS = ['.VV.DD.....DD.VV.'] * 5
LEGS = (['.VV.DD.I.I.DD.VV.'] + STILTS + ['.DD.DD.....DD.DD.'],    # its four stilts planted, the tusk tips between,
        ['.VV.DD.I.I.DD.VV.'] + STILTS + ['.DD.DD.....DD....'])    # then a far foot lifted
BACK_LEGS = tuple([STILTS[0]] + legs[1:] for legs in LEGS)          # from behind, no tusks
SIDE = [                 # its head to the left, hung low at the front of its humped body, the cup up on its stalk,
    '..DDDDD..................V',   # its two tentacle tails curling up behind
    '..VVVVV..............V..V.',
    '....V................V..V.',
    '....V.......VVVVVV...VVV..',
    '....V...VVVVVVVVVVVVVV....',
    '..VVVVVVVVVVVVVVVVVVVV....',
    '.VIVVVVVVVVVVVVVVVVVVD....',
    'VVVVVVVVVVVVVVVVVVVVVD....',
    'VKKKVVVVVVVVVVVVVVVVDD....',
    'VKKKDVVVVVVVVVVVVVVDDD....',
    '.IKIDDVVVVVVVVVVVVDDD.....',
    '.I..IDDDDDDDDDDDDDDD......',
    '.I.....VVD......DVV.......',
]
SIDE_LEGS = (['.......VVD......DVV.......'] * 6 + ['.......DDD......DDD.......'],     # near legs out front and behind,
             ['.......DVV......VVD.......'] * 6 + ['.......DDD......DDD.......'])     # then the far ones: its stride
for rows in (FRONT, BACK, SIDE) + LEGS + BACK_LEGS + SIDE_LEGS:
    assert len({len(r) for r in rows}) == 1, rows


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(FRONT + legs) for legs in LEGS], 'U': [place(BACK + legs) for legs in BACK_LEGS],
          'L': [place(SIDE + legs) for legs in SIDE_LEGS]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(84, 'kigutilik', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(84, CHASE, FRAMES, PAL)
