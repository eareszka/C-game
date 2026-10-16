"""10 Grand Goule's map mini: the green fire-gulping dragon with golden wings, flying, at the player's scale,
four views of two frames (tools/minis.py).

Placed by hand from its battle views (python tools/minis.py 10): the wings held up either side, the head with
its toothy open mouth, the gold belly, the tail from the side; it flies with its legs tucked up under it (the
user, 2026-10-14: "Grand Goule should by flying with legs tucked"). The first frame is the wings up, the
second the downstroke, as Alber's. 24 px tall, Alber's size ("it should be same size as alber overworld since
its a big classification"). Three of its battle colours and black: its green, its gold (wings, belly, teeth),
its dark green (eyes, the mouth, the shade low on the right). Its olive, red throat and white teeth go.

Its chase: surge -- as its breath goes out and comes back in its fight, it surges at you, 1.6x the chase pace
for 0.4 s, then draws back at 0.3x for 0.2 s (0.97 on average). chase_speed() in src/main.cpp and
tools/minis.py.

    python art/enemies/minis/10_grand_goule_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '2c6c44', 'Y': 'c9a433', 'D': '163623'}
CHASE = 'surge'

# Wings up: down to the thighs, as it stood; then the legs tucked under its belly. 31 wide (a column of room on
# the right, so the downstroke can mirror about the head's middle, column 15).
FRONT = [
    '.............................',
    '...K.....................K...',
    '..KYK.........KKK.......KYK..',
    '..KYYKK......KDDDK....KKYYK..',
    '.KYYYYYK...KKGGGGGKK.KYYYYK..',
    'KYYYYYYYK..KGGGGGGGGKYYYYYYK.',
    'KYYYYYYYK.KGGDGGGDGGKYYYYYYYK',
    '.KKYYYYYYKKGYDYDYDYGKYYYYYKK.',
    '..KYYYYYYYKDDDDDDDDDKYYYYYK..',
    '..KYYYYYYYKGDYDYDYDGKYYYYYK..',
    '..KYYYYYYYKGGGGGGGGGKYYYYYK..',
    '...KKKKYYYKKKDGGGGKYYYKKKK...',
    '.......KKYKGGGGGGGKYKK.......',
    '.........KKGGGGGGGGK.........',
    '..........KGYYYYYYGK.........',
    '.........KKGYYYYYYGK.........',
    '........KDKGYYYYYYGDK........',
    '........KDKGYYYYYYGDK........',
]
BACK = [
    '.............................',
    '...K.....................K...',
    '..KYK.........KKK.......KYK..',
    '..KYYKK......KDDDK....KKYYK..',
    '.KYYYYYK.....KYDDGK..KYYYYK..',
    'KYYYYYYYK..KKKKKKGGKKYYYYYYK.',
    'KYYYYYYYK.KGGGGGGGGDKYYYYYYYK',
    '.KKYYYYYYKKGGGGGGGGDKYYYYYKK.',
    '..KYYYYYYYKGGGGGGGDDKYYYYYK..',
    '..KYYYYYYYKKKKKKGGDDKYYYYYK..',
    '..KYYYYYYYYKKGGGGDDDYYYYYYK..',
    '...KKKKYYYKKKGGGGDDGKYKKKK...',
    '.......KKYKGGGGGGGGGKK.......',
    '.........KKGGGGGGGGGK........',
    '..........KGGGGGGGGK.........',
    '.........KKGGGGGGGGK.........',
    '........KDKGGGGGGGGDK........',
    '........KDKGGGGGGGGDK........',
]
TUCKED = [                                 # the belly closed, the feet folded up under it
    '........KKKGGGGGGGGKK........',
    '..........KGGKKKKGGK.........',
    '..........KDDK..KDDK.........',
    '...........KK....KK..........',
    '.............................',
    '.............................',
]
# The downstroke, the left wing (the right one its mirror about column 15): from the shoulder out and down.
WING_DOWN = {
    9:  '.......KKK',
    10: '.....KKYYY',
    11: '...KKYYYYY',
    12: '.KKYYYYYYY',
    13: 'KYYYYYYYYK',
    14: 'KYYYYYYYK.',
    15: 'KYYYYYYK..',
    16: '.KYKYKK...',
    17: '..K.K.....',
}


def downstroke(rows):
    """The wings-up rows with the wings taken off above the shoulders and WING_DOWN laid over both sides."""
    g = [list(r) for r in rows]
    for y in range(14):
        for x in list(range(10)) + list(range(21, 31)):
            g[y][x] = '.'
    for y, t in WING_DOWN.items():
        for i, c in enumerate(t):
            if c != '.':
                g[y][i] = g[y][30 - i] = c
    return [''.join(r) for r in g]


SIDE = [
    '..........................',
    '....K..............K......',
    '...KYK...........KKYK.....',
    '..KYYYK.........KDKYKKK...',
    '.KYYGGGK.......KGGYYYYGK..',
    '.KGDGGGGK.......KYYYYYKK..',
    'KGGGGGGGK......KYYYYYYGDK.',
    'KYDYDDGGK......KYYYYYDGGK.',
    '.KKDDDGGGK....KYYYYYYKGGGK',
    '...KKKKGGGKKK.KYYYYYYKGGGK',
    '....KDDDGGGDDKYYYYYYYKKDGK',
    '.....KDDDGGGDKKYYYKKKKDDGK',
    '.....KYDDGGGDDDDDDDDDKGGGK',
    '......KYYGGGGGGGDDDDDDKGGK',
    '......KYYYGGGGGGGGGGDDDGGK',
    '.......KYYYGGGGGGGGGGGDDK.',
    '.......KYYYYYGGGGGGGGYDDK.',
    '........KKYYYYYYYYYYYYYK..',
    '.........KDYYYYYYYYYYYYK..',
    '.........KDDGGGKKKKDGGGK..',
    '..........KKKDDDK..KKDDDK.',
    '.............KKK.....KKK..',
    '..........................',
    '..........................',
]
# From the side the downstroke hides the wings, as Alber's: the far one's tip over its back, the near one
# hanging below its belly; the tail rises behind where the wing was.
SIDE_DOWN = [
    '..........................',
    '....K.....................',
    '...KYK....................',
    '..KYYYK...............K...',
    '.KYYGGGK.............KGK..',
    '.KGDGGGGK............KDK..',
    'KGGGGGGGK............KGDK.',
    'KYDYDDGGK............KDGK.',
    '.KKDDDGGGK......K....KGGGK',
    '...KKKKGGGKKK..KYK...KGGGK',
    '....KDDDGGGDDKKYYKKKKKKDGK',
    '.....KDDDGGGDGGGGGGGGKDDGK',
    '.....KYDDGGGGGGGGGGGGKGGGK',
    '......KYYGGGGGGGGGGGDDKGGK',
    '......KYYYGGGGGGGGGGDDDGGK',
    '.......KYYYGGGGGGGGGGGDDK.',
    '.......KYYYYYGGGGGGGGYDDK.',
    '........KKYYYYYYYYYYYYYK..',
    '.........KDYYYYYYYYYYYYK..',
    '.........KDDGKYYYYYKGGGK..',
    '..........KKKKYYYYKKKDDDK.',
    '..............KYKYKK.KKK..',
    '...............K.K........',
    '..........................',
]

VIEWS = {
    'D': [(6, [r + '..' for r in FRONT + TUCKED]), (6, downstroke([r + '..' for r in FRONT + TUCKED]))],
    'U': [(6, [r + '..' for r in BACK + TUCKED]), (6, downstroke([r + '..' for r in BACK + TUCKED]))],
    'L': [(8, SIDE), (8, SIDE_DOWN)],
}
VIEWS['R'] = [(40 - x0 - len(rows[0]), [r[::-1] for r in rows]) for x0, rows in VIEWS['L']]
FRAMES = {v: [ff.grid([(4 + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, rows in fs] for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(10, 'grand_goule', FRAMES, PAL, cap=24)
    minis.chase_gif(10, CHASE, FRAMES, PAL)
