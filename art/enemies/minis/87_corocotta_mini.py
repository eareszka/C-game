"""87 Corocotta's map mini: Pliny's hyena-wolf out of Ethiopia at the player's scale, four views, two frames
(tools/minis.py).

Drawn by hand after its redesigned battle sheet (art/enemies/pixellab/87_corocotta, the user's concept 4), fill
only, one black outline round it. Its grey-steel wolf's head with pointed ears, black eye dots (the bible's tiny marks,
black on lit hide), its jaws open red as if speaking; the dark bristling mane round its neck and down its
sloping hyena back, its dark brush of a tail, long front legs. From the side the back slopes from high shoulders
to low haunches, the jaws open at the front; from behind, the mane down its spine and the tail. It lopes, its
legs stepping (frame 0, frame 1). The right view is the left mirrored. 20 px tall, a little over its battle
height (48 px) at the minis' one scale (17): the user has wanted the minis bigger. Three of its battle colours
and black: its grey, its mane's dark, its mouth red.

Its chase: the skirt (chase_speed(), chase_bend(), src/main.cpp) -- it calls men out at night in a human voice:
circling round you, then darting in.

    python art/enemies/minis/87_corocotta_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '848694', 'D': '292931', 'R': 'b6433d'}
CHASE = 'skirt'
HEIGHT = 20

FRONT = [                # head on: pointed ears, the mane bristling between, eye dots, the long face, jaws open red, the mane round its neck
    '.G.........G.',
    '.GG.D.D.D.GG.',
    '.GGGDDDDDGGG.',
    '..GGGGGGGGG..',
    '.DGKGGGGGKGD.',
    '.DGGGGGGGGGD.',
    'DDDGGGGGGGDDD',
    'DDDDGRRRGDDDD',
    '.DDDGRRRGDDD.',
    '..DDDGGGDDD..',
    '...GGGGGGG...',
    '..GGGGGGGGG..',
    '..GGGGGGGGG..',
]
FRONT_LEGS = (['..GG.D.D.GG..', '..GG.D.D.GG..', '..GG.D.D.GG..', '..GG.D.D.GG..', '..DD.D.D.DD..'],
              ['..GG.D.D.GG..', '..GG.D.D.GG..', '...GGD.DGG...', '...GGD.DGG...', '...DDD.DDD...'])
BACK = [                 # from behind: ears, the mane down its spine to the dark brush of its tail hanging
    '.G.........G.',
    '.GG.D.D.D.GG.',
    '.GGGDDDDDGGG.',
    '..GGGDDDGGG..',
    '.GGGGDDDGGGG.',
    '.GGGGGDGGGGG.',
    'GGGGGGDGGGGGG',
    'GGGGGGDGGGGGG',
    '.GGGGGDGGGGG.',
    '..GGGDDDGGG..',
    '..GGDDDDDGG..',
    '..GGGDDDGGG..',
    '..GGGDDDGGG..',
]
BACK_LEGS = (['..GG.DDD.GG..', '..GG..D..GG..', '..GG.....GG..', '..GG.....GG..', '..DD.....DD..'],
             ['..GG.DDD.GG..', '..GG..D..GG..', '...GG...GG...', '...GG...GG...', '...DD...DD...'])
SIDE = [                 # its head to the left, ears up, jaws open; the back sloping from high maned shoulders to low haunches,
    '...G.G..................',   # the dark brush of its tail hanging behind
    '...GGGG.D.D.D...........',
    '..GGGGGDDDDDDD..........',
    '.GGKGGGGDDDDDDDD........',
    'GGGGGGGGGDDDDDDDDD......',
    'RRRRGGGGGGGGGGGDDDDD....',
    'GGGGGGGGGGGGGGGGGGDDDD..',
    '...GGGGGGGGGGGGGGGGG.DD.',
    '....GGGGGGGGGGGGGGGG..DD',
    '.....GGGGGGGGGGGGGG...D.',
]
SIDE_LEGS = (['.......VVDD....DDVV.....', '......VV.DD....DD.VV....', '......VV..DD..DD..VV....', '.....VV...DD..DD...VV...',
              '.....DD....DD.DD....DD..'],                                     # stretched out in its lope
             ['........VVDD..DDVV......', '........VVDD..DDVV......', '........VVDD..DDVV......', '........VVDD..DDVV......',
              '........DDDD..DDDD......'])                                     # gathered under it
SIDE_LEGS = tuple([r.replace('V', 'G') for r in legs] for legs in SIDE_LEGS)
for rows in (FRONT, BACK, SIDE) + FRONT_LEGS + BACK_LEGS + SIDE_LEGS:
    assert len({len(r) for r in rows}) == 1, rows


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(FRONT + legs) for legs in FRONT_LEGS], 'U': [place(BACK + legs) for legs in BACK_LEGS],
          'L': [place(SIDE + legs) for legs in SIDE_LEGS]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(87, 'corocotta', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(87, CHASE, FRAMES, PAL)
