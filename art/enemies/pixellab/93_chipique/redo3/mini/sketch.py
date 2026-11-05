"""93 Chipique's submerged mini, its source for PixelLab (the user, 2026-11-03: "mini should be submerged"): the approved design with the coil under the water,
only the neck and head, the canoe with its rider and paddle, and the tail's hook above it, pale water at the waterline. Drawn at mini size by hand: a shrink of the
battle frame mushed the canoe, and PixelLab mushes a full-size source. Three colours and black: hide purple, canoe brown, water mint (the rider's eyes take the mint).

    python art/enemies/pixellab/93_chipique/redo3/mini/sketch.py
"""
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff
from PIL import Image

PAL = {'K': '000000', 'P': '423c70', 'B': '785830', 'M': 'a8f0bc'}
ROWS = [
    '.....PPPPPPP........................',
    '...PPPPPPPPPPP......................',
    '..PPPPPPPPPPPPP.....................',
    '.PPKKPPPPPPPPPPP....................',
    'PPPPPPPP...PPPPPP.............PPPP..',
    'PPKKKK......PPPPP............PPPPPP.',
    '.PPP........PPPPP...........PPP..PPP',
    '............PPPPP...........PP....PP',
    '............PPPPP....B......PP.....P',
    '............PPPPP....B......PP......',
    '............PPPPP.....B.....PP......',
    '............PPPPP.....B.PPP.PPP.....',
    '............PPPPP.....BPMPMPPPP.....',
    '............PPPPPB....BPPPPPBPP.....',
    'MM..........PPPPPBBBBBBBBBBBBPPP..MM',
    'MMMM.......MPPPPPKBBBBBBBBBBKPPPMMMM',
    'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM',
    '.MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM.',
]
assert len({len(r) for r in ROWS}) == 1
x0, y0 = minis.W // 2 - len(ROWS[0]) // 2, minis.H - 1 - len(ROWS)
g = ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(ROWS) for x, c in enumerate(r) if c != '.'})
im = ff.image(g, PAL, minis.W, minis.H)
im.save(HERE / 'first.png')
print('box', im.getbbox())
print('\n'.join(l for l in ff.checks(g, PAL, minis.W, minis.H, cap=22, max_colours=3) if 'hue' not in l))
bg = ff.image(g, PAL, minis.W, minis.H, bg=minis.GRASS)
bg.resize((minis.W * 10, minis.H * 10), 0).save(HERE / 'first_x10.png')
