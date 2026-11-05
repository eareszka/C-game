"""82 Nadubi's map mini: the barbed spirit on all fours at the player's scale, four views, two frames (tools/minis.py).

Drawn by hand after its battle sheet (assets/enemies/82_nadubi.png), fill only, one black outline round it: its
dark-red body bristling with ivory barbs, its red face hung under it as in battle -- hollow black eyes with
pale pupils, a long mouth lined with ivory teeth -- its four long legs and ivory claws (the user: "face match"). Its battle sheet shows it one way from every side, so the sides here are its front too; from
behind, no face. It skitters (its flap in battle is a spider's crawl): two of its legs lifted, then the other
two. 22 px tall, larger than its battle height (50 px) at the minis' one scale (18; the user: "needs to be
larger"). Three of its battle colours and
black: its red, its dark red, its ivory.

Its chase: the scuttle, as the Myrmecoleon's -- never stopping, weaving a little (chase_speed(), chase_bend(),
src/main.cpp).

    python art/enemies/minis/82_nadubi_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '792727', 'D': '5d1e1f', 'C': 'e8e0c0'}
CHASE = 'scuttle'
HEIGHT = 22               # larger than its battle height at the one scale (18): the user, so its face reads

BARBS = [                # the ivory barbs along its back
    'C.........C.........C',
    'C...C.....C.....C...C',
    '.C..C..C..C..C..C..C.',
]
BODY = [                 # its back, its outer legs going down dark either side
    '.MMMMMMMMMMMMMMMMMMM.',
    'DDMMMMMMMMMMMMMMMMMDD',
    'DD.MMMMMMMMMMMMMMM.DD',
]
FRONT = BARBS + BODY + [ # its red face hung under it (as in battle): hollow eyes, their pale pupils, the long mouth lined with teeth
    'DD..M.MMMMMMMMM.M..DD',
    'DD..M.MMMMMMMMM.M..DD',
    'DD..M.MKCKMKCKM.M..DD',
    'DD..M.MMMMMMMMM.M..DD',
    'DD..M.MDCDCDCDM.M..DD',
    'DD..M.MDKKKKKDM.M..DD',
    'DD..M.MDKKKKKDM.M..DD',
    'DD..M..DCDCDCD..M..DD',
    'DD..M...MMMMM...M..DD',
    'DD..M...........M..DD',
    'DD..M...........M..DD',
]
BACK = BARBS + BODY + [  # from behind: the back of its head, no face
    'DD..M.MMMMMMMMM.M..DD',
    'DD..M.MMMDMDMMM.M..DD',
    'DD..M.MMMMMMMMM.M..DD',
    'DD..M.MMDMMMDMM.M..DD',
    'DD..M.MMMMMMMMM.M..DD',
    'DD..M..MMMMMMM..M..DD',
    'DD..M...MMMMM...M..DD',
    'DD..M....MMM....M..DD',
    'DD..M...........M..DD',
    'DD..M...........M..DD',
    'DD..M...........M..DD',
]
LEGS = ([                # all four down, the claws planted
    'DD..M...........M..DD',
    'DD.CCC.........CCC.DD',
    'CCC...............CCC',
], [                     # the outer pair lifted
    'DD..M...........M..DD',
    'CCC.M...........M.CCC',
    '...CCC.........CCC...',
])

def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(FRONT + legs) for legs in LEGS], 'U': [place(BACK + legs) for legs in LEGS],
          'L': [place(FRONT + legs) for legs in LEGS]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(82, 'nadubi', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(82, CHASE, FRAMES, PAL)
