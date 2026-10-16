"""03 Qique's map mini: the crested rooster-bird at the player's scale, four views (tools/minis.py).

Started from the shrink of its battle views (python tools/minis.py 3), placed by hand: the white head with its
comb, the beak, the navy body, its wings held out with pale tips, the tail up behind it in the side views, the
legs. Three of its battle colours and black: its navy, its white, its orange (beak, wing bars, legs). Not one ramp:
its dark navy goes so the beak and wings keep their orange, as the Wolpertinger kept its red wings (the user,
2026-10-14); the red comb is navy, the pink legs orange.

Its chase: zigzag -- it runs at you weaving side to side, a weave every 0.7 s (chase_bend() in src/main.cpp,
chase_move() in tools/minis.py).

    python art/enemies/minis/03_qique_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'N': '423c70', 'W': 'fcfcfc', 'O': 'fc9838'}
CHASE = 'zigzag'

VIEWS = {
    'D': (14, [
        '.....KK.....',
        '....KNNK....',
        '...KWWWWK...',
        '..KWKWWKWK..',
        '..KWWOOWWK..',
        '.KKKKWOKKKK.',
        'KOWKNNNNKWOK',
        'KNOKNNNNKONK',
        '.KKKNNNNKKK.',
        '...KNNNNK...',
        '...KOKKOK...',
        '....K..K....',
    ]),
    'U': (14, [
        '.....KK.....',
        '....KNNK....',
        '...KWWWWK...',
        '..KWWWWWWK..',
        '..KWWWWWWK..',
        '.KKKKWWKKKK.',
        'KOWKNNNNKWOK',
        'KNOKNNNNKONK',
        '.KKKNNNNKKK.',
        '...KNNNNK...',
        '...KOKKOK...',
        '....K..K....',
    ]),
    'L': (12, [
        '....KK.........',
        '...KNNK......K.',
        '..KWWWWK....KNK',
        '.KKWKWWK...KNNK',
        'KOOWWWWK..KNNNK',
        '.KKKWWWKKKNNNK.',
        '...KWKNNNNNNNK.',
        '..KOWKNNNNNNNK.',
        '..KKKNNNNNNNNK.',
        '....KNNNNNNNK..',
        '.....KOKKOKK...',
        '......K..K.....',
    ]),
}
VIEWS['R'] = (40 - 12 - 15, [r[::-1] for r in VIEWS['L'][1]])
FRAMES = {v: ff.grid([(16 + y, x0, r) for y, r in enumerate(rows)], PAL) for v, (x0, rows) in VIEWS.items()}

if __name__ == '__main__':
    minis.make(3, 'qique', FRAMES, PAL)
    minis.chase_gif(3, CHASE, FRAMES, PAL)
