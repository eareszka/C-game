"""16 Kamaitachi's map mini: the white sickle-weasel riding its whirlwind, at the player's scale, four views of
two frames (tools/minis.py).

Placed by hand from its battle views (python tools/minis.py 16): the weasel on top, ears up, sitting in the
funnel of its whirlwind; the whirlwind in diagonal bands of wind narrowing to its point, a grey gust
swirling out high on one side and low on the other. The second frame is the whirlwind's turn: the bands half
a band on, the gusts swapped sides. And it spins whichever way it goes (the user, 2026-10-14: "have its blue
and white stripes be angled and spin, also have it spin no matter what direction it goes in"): the game
turns it round its four views, D R U L, every 120 ms (draw_chaser in src/main.cpp).
24 px tall, Alber's size: it flies (the user, 2026-10-14, of the Ebigane: "alber size and flying again").
Three of its battle colours and black: its white (the weasel, the light bands), its blue (the wind), its grey
(the gusts). Its pale blue goes to white, its pale and dark greys to grey.

Its chase: gust -- as it darts and spins in its fight: a gust straight at you, 2.0x the chase pace for
0.35 s, then a whirl, one small loop round at 0.6x for 0.45 s (closes at 0.88). chase_speed() and
chase_bend() in src/main.cpp and tools/minis.py.

    python art/enemies/minis/16_kamaitachi_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'W': 'fcfcfc', 'B': '84a7e9', 'G': '848694'}
CHASE = 'gust'

WEASEL = [                       # from row 4, coming at you
    '......K.....K......',
    '.....KWK...KWK.....',
    '....KWWKKKKKWWK....',
    '....KWWWWWWWWWK....',
    '....KWKWWWWWKWK....',
    '....KWWWWKWWWWK....',
    '.....KWWWWWWWK.....',
    '.KK...KWWWWWK......',
]
WIND = [                         # from row 12: its funnel, the bands, the point; a gust out either side
    'KGGKKKKWWWWWKKK....',
    'KGKKBBBKWWWKBBBKK..',
    '.KBBBBBBKKKBBBBBBK.',
    'KWWWWWWWWWWWWWWWWWK',
    'KWWWWWWWWWWWWWWWWWK',
    '.KBBBBBBBBBBBBBBBK.',
    '..KBBBBBBBBBBBBBKGK',
    '...KWWWWWWWWWWWKGGK',
    '....KWWWWWWWWWKGGK.',
    '.....KBBBBBBBKKKK..',
    '......KBBBBBK......',
    '.......KWWWK.......',
    '.......KWWWK.......',
    '........KBK........',
    '........KBK........',
    '.........K.........',
]
FRONT = WEASEL + WIND
BACK = WEASEL[:4] + ['....KWWWWWWWWWK....', '....KWWWWWWWWWK....'] + WEASEL[6:] + WIND
SIDE = [                         # from row 4: its head to the left, its tail curled up behind
    '.....................',
    '...K.............KK..',
    '..KWK...........KWWK.',
    '.KWWWK..........KWWWK',
    'KWKWWWKKKKKKKKK.KWWWK',
    'KWWWWWWWWWWWWWWKWWWWK',
    'KKWWWWWWWWWWWWWWWWWK.',
    '..KKKWWWWWWWWWWWKKK..',
] + ['.' + r + '.' for r in WIND]


def stripes(rows, top, phase):
    """Its wind from row `top` down in diagonal bands, two white, two blue, `phase` columns along."""
    return rows[:top] + [''.join(('W' if (x + y + phase) // 2 % 2 else 'B') if c in 'WB' else c
                                 for x, c in enumerate(r)) for y, r in enumerate(rows[top:])]


def spin(rows, top, gusts):
    """Its two frames: the bands turned half a band on, and the rows from `gusts` (where its gusts begin)
    mirrored so the gusts swap sides."""
    return [stripes(rows, top, 0), stripes(rows[:gusts] + [r[::-1] for r in rows[gusts:]], top, 2)]


VIEWS = {
    'D': [(10, 4, f) for f in spin(FRONT, 10, 7)],
    'U': [(10, 4, f) for f in spin(BACK, 10, 7)],
    'L': [(9, 4, f) for f in spin(SIDE, 10, 8)],
}
VIEWS['R'] = [(40 - x0 - len(rows[0]), top, [r[::-1] for r in rows]) for x0, top, rows in VIEWS['L']]
FRAMES = {v: [ff.grid([(top + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, top, rows in fs]
          for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(16, 'kamaitachi', FRAMES, PAL, cap=24)
    minis.chase_gif(16, CHASE, FRAMES, PAL, spin=True)
