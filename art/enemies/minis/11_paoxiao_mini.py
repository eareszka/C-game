"""11 Paoxiao's map mini: the grey goat with a man's face and hands and an eye under its arm, at the player's
scale, four views of two frames (tools/minis.py).

Placed by hand over the shrink of its battle views (python tools/minis.py 11): from the front and back a narrow
goat, face (or the back of its head) between little horns, hands as forefeet; from the side the face forward,
the eye on its flank, the tail up. The second frame is the leap: in the air, legs flung out. 14 px tall: its
battle frames stand 24, between the 12 px small ones and the 16 px Snawfus. Three of its battle colours and
black: its grey, its skin (face, hands, the eye), its dark grey (horns, mouth, hind legs, the shade low on the
right). Its pale grey, white and near-black go.

Its chase: pounce -- as it lies in wait in its fight, it stands still 0.5 s, then leaps at you, 2.3x the
chase pace for 0.35 s (0.95 on average); standing in the wait, in the air in the leap. chase_speed() and
chase_frame() in src/main.cpp and tools/minis.py.

    python art/enemies/minis/11_paoxiao_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'A': '9797aa', 'C': 'f0b890', 'B': '595965'}
CHASE = 'pounce'

FRONT = [
    '..K...K..',
    '.KBKKKBK.',
    '.KCCCCCK.',
    '.KCKCKCK.',
    '..KCBCK..',
    '.KKAAAKK.',
    'KAAAAAAAK',
    'KAAAAAAAK',
    'KAAAAAABK',
    '.KAAAABK.',
]
BACK = FRONT[:2] + ['.KAAAAAK.', '.KAAAABK.', '..KAABK..'] + FRONT[5:6] + ['KAAABAAAK'] + FRONT[7:]
STAND = ['.K{0}KKK{0}K.', '.K{0}K.K{0}K.', '.K{0}K.K{0}K.', '..K...K..']      # forefeet hands, or hind legs
LEAP = ['K{0}KKKKK{0}K', 'K{0}K...K{0}K', '.K.....K.']                         # flung out, a row up

SIDE = [
    '..K.K............',
    '.KBKBK...........',
    'KCCCAAK..........',
    'KCKCAAK..........',
    'KCBCAAAK.........',
    '.KKKKAAAK.....KK.',
    '.....KAAAKKKKKBK.',
    '.....KAAAAAAAAAK.',
    '.....KAACKAAAAAK.',
    '.....KAAAAAAAABK.',
]
SIDE_STAND = ['.....KCKCKKKBKBK.', '.....KCKCK.KBKBK.', '.....KCKCK.KBKBK.', '......K.K...K.K..']
SIDE_LEAP = ['....KCCKKKKKKBBK.', '...KCCK......KBBK', '....KK........KK.']


def frame(x0, top, rows):
    return ff.grid([(top + y, x0, r) for y, r in enumerate(rows)], PAL)


VIEWS = {
    'D': [(15, 14, FRONT + [r.format('C') for r in STAND]), (15, 13, FRONT + [r.format('C') for r in LEAP])],
    'U': [(15, 14, BACK + [r.format('B') for r in STAND]), (15, 13, BACK + [r.format('B') for r in LEAP])],
    'L': [(11, 14, SIDE + SIDE_STAND), (11, 13, SIDE + SIDE_LEAP)],
}
VIEWS['R'] = [(40 - x0 - len(rows[0]), top, [r[::-1] for r in rows]) for x0, top, rows in VIEWS['L']]
FRAMES = {v: [frame(*f) for f in fs] for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(11, 'paoxiao', FRAMES, PAL, cap=14)
    minis.chase_gif(11, CHASE, FRAMES, PAL)
