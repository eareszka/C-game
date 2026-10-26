"""22 Cactus Cat's map mini: the thorny green bobcat up on its four legs and walking, at the player's scale, four
views, two frames (tools/minis.py).

Its battle sheet only sits. Drawn through PixelLab (art/enemies/pixellab/22_cactus_cat/mini, pixellab-out/22-mini):
its battle frame at 2x, edited to stand mid-stride, rotated to its eight views, a four-frame walk on the front,
the back and the left side; each walk's two stride frames snapped to its colours and shrunk to 12 px
(minis.snap, minis.shrink, minis.clean), then by hand: its eyes, and a back view widened to a cat's (PixelLab's was
four pixels wide), the legs stepping. Three of its battle colours and black: its green, its dark green, its pale
thorns and paws. Its pink flowers and cheeks go.

Its chase: it has drunk the cacti's fermented sap and wanders drunk (the lore), so it meanders, curving one way
then the other, its pace rising and falling (chase_speed() and chase_bend(), src/main.cpp).

    python art/enemies/minis/22_cactus_cat_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '4fa667', 'C': '2c6c44', 'B': 'e8e0c0'}
CHASE = 'meander'

FRONT = [
    (14, 16, [                                   # walk frame 1 of PixelLab's front walk
        '.........K..',
        '.KK....KKBK.',
        'KGGK..KBKBK.',
        '.KGK.KGGGGGK',
        '.KCKKKGKGKGK',
        '.KCCGGGGGGGK',
        '..KGGGGGGGK.',
        '..KGGGGGGCK.',
        '..KGGGGGBCCK',
        '.KGGKCGGKKCK',
        '..KKKCGBK.K.',
        '.....KKK....',
    ]),
    (15, 17, [                                   # walk frame 3
        '.K...KK.K..',
        'KGK.KGBKBK.',
        'KGGKKGGGGGK',
        'KGGKKGKGKGK',
        '.KCGGGGGGGK',
        '..KGGGGGGK.',
        '..KGGGGBCK.',
        '..KGGGGKK..',
        '...KGGGBK..',
        '..KCCBKK...',
        '...KKK.....',
    ]),
]
BACK_TOP = [
    '.K.....K.',
    'KBK...KBK',
    'KGGKKKGGK',
    'KGGGGGGGK',
    '.KGGGGGK.',
    '.KGGCGGK.',
    'KGGGCGGGK',
    'KGGGCGGGK',
]
BACK = [
    (16, 16, BACK_TOP + [                        # its left hind paw up
        'KCGGGGGCK',
        'KBKKKKKCK',
        '.K....KBK',
        '.......K.',
    ]),
    (16, 16, BACK_TOP + [                        # its right
        'KCGGGGGCK',
        'KCKKKKKBK',
        'KBK....K.',
        '.K.......',
    ]),
]
SIDE = [                                         # its head to the left
    (14, 16, [                                   # walk frame 1 of PixelLab's left walk
        '..K.......K.',
        '.KBKKK...KGK',
        '.KBKGGK..KGK',
        '.KGKGGK..KGK',
        'KGGGGGKKKCGK',
        'KBGGGGGGGGGK',
        '.KCGGGGGGGGK',
        '..KBGGGGGGGK',
        '...KGGKKCGGK',
        '...KGGK.KGGK',
        '..KBBK..KCBK',
        '...KK....KK.',
    ]),
    (14, 16, [                                   # walk frame 3
        '..........K.',
        '...K.K...KGK',
        '..KBKGK.KGGK',
        '.KGKGGK..KGK',
        '.KGGGGKKKCCK',
        'KBGGGGGGGGK.',
        '.KCGGGGGGGK.',
        '..KBGGGGGGK.',
        '..KBGGBBGGK.',
        '...KGGKKGGK.',
        '..KBGK.KGK..',
        '...KK...K...',
    ]),
]

VIEWS = {'D': FRONT, 'U': BACK, 'L': SIDE}
VIEWS['R'] = [(40 - x0 - len(rows[0]), top, [r[::-1] for r in rows]) for x0, top, rows in SIDE]
FRAMES = {v: [ff.grid([(top + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, top, rows in fs]
          for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(22, 'cactus_cat', FRAMES, PAL)
    minis.chase_gif(22, CHASE, FRAMES, PAL)
