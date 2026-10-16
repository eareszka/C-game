"""00 Skvader's map mini: the winged hare at the player's scale, four views (tools/minis.py).

Started from the shrink of its battle views (python tools/minis.py 0), then placed by hand: the ears, the
wings spread up either side, the eyes, the cream belly. Three of its battle colours and black: its fur, its
dark brown, its cream (the wings' orange goes; at this size they are fur with the dark low on the right).

    python art/enemies/minis/00_skvader_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': 'b2966a', 'D': '633e1b', 'L': 'e8e0c0'}
X = 13      # the first column; the feet on row 26, its outline on 27

VIEWS = {
    'D': [
        'KK....K.K....KK',
        'KLK..KMKMK..KMK',
        'KMLK.KMKMK.KMDK',
        '.KMLKKMMMKKMDK.',
        '.KMMKMKMKMKDDK.',
        '..KMKMMDMMKDK..',
        '...KKMMMMDKK...',
        '..KMMKKKKKMDK..',
        '.KMMMKLLLKMMDK.',
        '.KMMMKLLLKMDDK.',
        '.KMMDKLKLKMDDK.',
        '..KKKKKKKKKKK..',
    ],
    'U': [
        'KK....K.K....KK',
        'KLK..KMKMK..KMK',
        'KMLK.KMKMK.KMDK',
        '.KMLKKMMMKKMDK.',
        '.KMMKMMMMMKDDK.',
        '..KMKMMMMDKDK..',
        '...KKMMMMDKK...',
        '..KMMKKKKKMDK..',
        '.KMMMMKKKMMMDK.',
        '.KMMMMKLKMMDDK.',
        '.KMMDDKKKDDDDK.',
        '..KKKKKKKKKKK..',
    ],
    'L': [
        '.K.K......KKK..',
        'KMKMK....KLMMK.',
        'KMKMK...KLMMDK.',
        'KMMMMK.KLMMDK..',
        'KMKMMMKKMMDK...',
        'KDMMMMMKMDDKK..',
        '.KKLMKKKKKKMDK.',
        '..KLMMMMMMMMDK.',
        '..KLMMMMMMMDDKK',
        '..KLMMMDMMMDDLK',
        '..KLLMDKMMDDDKK',
        '...KKKKKKKKKKK.',
    ],
}
VIEWS['R'] = [r[::-1] for r in VIEWS['L']]
FRAMES = {v: ff.grid([(16 + y, X, r) for y, r in enumerate(rows)], PAL) for v, rows in VIEWS.items()}

if __name__ == '__main__':
    minis.make(0, 'skvader', FRAMES, PAL)
