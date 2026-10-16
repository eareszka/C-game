"""04 Lili's map mini: the round pink many-legged scuttler at the player's scale, four views (tools/minis.py).

Started from the shrink of its battle views (python tools/minis.py 4), placed by hand: the pointed ears, the
pale band across its face with the eyes, the round mouth, the dark underside, the legs. Three of its battle
colours and black: its pink, its pale, and the bright pink of its mouth and snout (its dark red underside goes:
the mouth is what it is known by, as the Wolpertinger's red wings were).

Its chase: straight at you, head on (the user, 2026-10-14, over a curved approach from the side).

    python art/enemies/minis/04_lili_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': 'ec8476', 'L': 'f0b890', 'P': 'fc74b4'}
CHASE = 'straight'

VIEWS = {
    'D': (14, [
        '.K........K.',
        'KMK......KMK',
        'KMMKKKKKKMMK',
        'KMLKLLLLKLMK',
        'KMMMMKKMMMMK',
        'KMMMKPPKMMMK',
        'KMMKPPPPKMMK',
        'KMMMKPPKMMMK',
        'KMKMKKKKMKMK',
        'KMKMK..KMKMK',
        'KMKMK..KMKMK',
        '.K.K....K.K.',
    ]),
    'U': (14, [
        '.K........K.',
        'KMK......KMK',
        'KMMKKKKKKMMK',
        'KMMLLKKLLMMK',
        'KMLLLLLLLLMK',
        'KMLLLKKLLLMK',
        'KMMLLLLLLMMK',
        'KMMMMMMMMMMK',
        'KMKMKKKKMKMK',
        'KMKMK..KMKMK',
        'KMKMK..KMKMK',
        '.K.K....K.K.',
    ]),
    'L': (12, [
        '....K....K.....',
        '...KMK..KMK.K..',
        '..KMMMKKMMMKMK.',
        '.KLKLMMMMMMMMMK',
        'KPPKLMMMMMMMMMK',
        'KPPPMMMMLLMMMMK',
        'KPPKMMMMMMMMMMK',
        '.KKMMMMMMMMMMK.',
        '..KMKMKKMKMKK..',
        '..KMKMK.KMKMK..',
        '..KMKMK.KMKMK..',
        '...K.K...K.K...',
    ]),
}
VIEWS['R'] = (40 - 12 - 15, [r[::-1] for r in VIEWS['L'][1]])
FRAMES = {v: ff.grid([(16 + y, x0, r) for y, r in enumerate(rows)], PAL) for v, (x0, rows) in VIEWS.items()}

if __name__ == '__main__':
    minis.make(4, 'lili', FRAMES, PAL)
    minis.chase_gif(4, CHASE, FRAMES, PAL)
