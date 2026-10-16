"""01 Wolpertinger's map mini: the antlered winged hare at the player's scale, four views (tools/minis.py).

The Skvader's mini (00) with its antlers for ears, in its own colours: three of its battle colours and black --
its fur, its dark brown, its wings' red (the user, 2026-10-14: "have the wings be red to match the sprite more").
Three colours, so the cream goes: the antlers and belly are fur, the tail's puff too.

    python art/enemies/minis/01_wolpertinger_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '8d6b4f', 'D': '463422', 'R': 'b6433d'}
X = 13      # the first column; the feet on row 26, its outline on 27

VIEWS = {
    'D': [
        'KK..K.K.K.K..KK',
        'KRKKMKMKMKMKKRK',
        'KRRKKMMKMMKKRDK',
        '.KRRKKMMMKKRDK.',
        '.KRDKMKMKMKRDK.',
        '..KDKMMDMMKDK..',
        '...KKMMMMDKK...',
        '..KMMKKKKKMDK..',
        '.KMMMKMMMKMMDK.',
        '.KMMMKMMMKMDDK.',
        '.KMMDKMKMKMDDK.',
        '..KKKKKKKKKKK..',
    ],
    'U': [
        'KK..K.K.K.K..KK',
        'KRKKMKMKMKMKKRK',
        'KRRKKMMKMMKKRDK',
        '.KRRKKMMMKKRDK.',
        '.KRDKMMMMMKRDK.',
        '..KDKMMMMDKDK..',
        '...KKMMMMDKK...',
        '..KMMKKKKKMDK..',
        '.KMMMMMMMMMMDK.',
        '.KMMMMMMMMMDDK.',
        '.KMMDDMMMDDDDK.',
        '..KKKKKKKKKKK..',
    ],
    'L': [
        '.K.K......KKK..',
        'KMKMK....KRRRK.',
        'KMKMK...KRRRDK.',
        'KMMMMK.KRRRDK..',
        'KMKMMMKKRRDK...',
        'KDMMMMMKRDDKK..',
        '.KKMMKKKKKKMDK.',
        '..KMMMMMMMMMDK.',
        '..KMMMMMMMMDDKK',
        '..KMMMMDMMMDDMK',
        '..KMMMDKMMDDDKK',
        '...KKKKKKKKKKK.',
    ],
}
VIEWS['R'] = [r[::-1] for r in VIEWS['L']]
FRAMES = {v: ff.grid([(16 + y, X, r) for y, r in enumerate(rows)], PAL) for v, rows in VIEWS.items()}

if __name__ == '__main__':
    minis.make(1, 'wolpertinger', FRAMES, PAL)
