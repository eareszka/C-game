"""21 Asp's map mini: the coiled green serpent with its yellow belly, its tail stopping its ear, springing along
on its coils, at the player's scale, four views of two frames (tools/minis.py).

Placed by hand over the shrink of its battle views (python tools/minis.py 21): the head with its ears up, the
neck with its yellow belly rising out of three tiers of coils, the tail climbing beside it to its ear; from
the back the head and neck all green, the tail on the other side; from the side the head to the left. The
second frame is the spring, up in the air. 16 px tall: its battle frames stand 34. Three of its battle
colours and black: its dark green, its green, its yellow (belly, ears). Its pink, white, red and darkest
green go.

Its chase: spring -- its coils spring it at you, 1.7x the chase pace for 0.2 s, up in the air, then 0.5x for
0.3 s (closes at 0.98). chase_speed() and chase_frame() in src/main.cpp and tools/minis.py.

    python art/enemies/minis/21_asp_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'D': '2c6c44', 'G': '4fa667', 'Y': 'd0c078'}
CHASE = 'spring'

COILS = [                                        # rows 21-27: three tiers, the tail joining the top one
    '..KGGGGGGGKGK...',
    '.KDDDDDDDDDGK...',
    '.KYYYYYYYYYYK...',
    'KGGGGGGGGGGGGK..',
    'KDDDDDDDDDDDDK..',
    '.KYYYYYYYYYYK...',
    '..KKKKKKKKKK....',
]
FRONT = [                                        # from row 12
    '...K.....K......',
    '..KYK...KYK.....',
    '..KYGKKKGYKK....',
    '...KGGGGGKKGK...',
    '...KKDDDKKKGK...',
    '....KDDDK.KGK...',
    '....KYYYK.KGK...',
    '....KYYYK.KGK...',
    '...KDYYYDKKGK...',
] + COILS
BACK = [r[::-1] for r in FRONT[:4] + [
    '...KDDDDDKKGK...',
    '....KDDDK.KGK...',
    '....KDDDK.KGK...',
    '....KDDDK.KGK...',
    '...KDDDDDKKGK...',
] + COILS]
SIDE = [                                         # its head to the left
    '........K.......',
    '....KKKKYK......',
    '..KKGGGGDYKK....',
    '.KDDGKGGKKKGK...',
    '.KDDDDDDK.KGK...',
    '..KYYYYDK.KGK...',
    '...KKYYDK.KGK...',
    '....KYYDK.KGK...',
    '...KKYYDDKKGK...',
] + COILS

VIEWS = {v: [(12, 12, rows), (12, 10, rows)] for v, rows in (('D', FRONT), ('U', BACK), ('L', SIDE))}
VIEWS['R'] = [(40 - x0 - len(rows[0]), top, [r[::-1] for r in rows]) for x0, top, rows in VIEWS['L']]
FRAMES = {v: [ff.grid([(top + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, top, rows in fs]
          for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(21, 'asp', FRAMES, PAL, cap=16)
    minis.chase_gif(21, CHASE, FRAMES, PAL)
