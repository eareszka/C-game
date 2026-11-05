"""12 Ebigane's map mini: the purple tusked pig-bat with red wings and a curly pink tail, flying, at the player's
scale, four views of two frames (tools/minis.py).

Placed by hand over the shrink of its fly sheet (assets/enemies/12_ebigane_fly.png, python tools/minis.py 12):
the wings held up either side, the horned head with its pink snout and tusks, the legs tucked up under it as
it flies, the tail curled behind. The first frame is the wings up, the second the downstroke, as Alber's and
the Grand Goule's. 24 px tall, Alber's size (the user, 2026-10-14: "Ebigane should be alber size and flying
again"; an 18 px one is in art/_backup/12_mini_18px_20261014/). Three of its battle colours and black: its
purple, its dark red (the wings), its pink (snout, horns, tusks, tail). Its dark purple legs, cream and red
wing veins go.

Its chase: jink -- as a bat flies, it darts at you off one side of your line, then the other: its heading
0.8 rad off the line for 0.25 s, then 0.8 rad the other way, at 1.2x the chase pace (closes at 0.84).
chase_speed() and chase_bend() in src/main.cpp and tools/minis.py.

    python art/enemies/minis/12_ebigane_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'P': '5e486a', 'W': '531b1c', 'C': 'ec8476'}
CHASE = 'jink'

# Front and back: the left half and the middle column, the right half its mirror.
FRONT = [
    '...K..........' '.',
    '..KWKK........' '.',
    '.KWWWWK.......' '.',
    'KWWWWWWK......' '.',
    'KWWWWWWK......' '.',
    '.KWWWWWWK.....' '.',
    '..KWWWWWWK....' '.',
    '..KWWWWWWK.K..' '.',
    '..KWWWWWWWKCKK' 'K',
    '..KWWWWWWWKCKP' 'P',
    '...KWWWWWWKPPP' 'P',
    '....KKWWWWKPKP' 'P',
    '......KKKKPPCC' 'C',
    '.........KPPCK' 'C',
    '.........KCPPP' 'P',
    '.........KKPPP' 'P',
    '........KPPPPP' 'P',
    '.......KPPPPPP' 'P',
    '.......KPPPPPP' 'P',
    '.......KPPPPPP' 'P',
    '........KPPPKK' 'K',
    '.........KKK..' '.',
]
BACK = FRONT[:10] + [
    '...KWWWWWWKPPP' 'P',
    '....KKWWWWKPPP' 'P',
    '......KKKKPPPP' 'P',
    '.........KPPPP' 'P',
    '.........KPPPP' 'P',
    '.........KKPPP' 'P',
    '........KPPPPP' 'P',
    '.......KPPPPPP' 'P',
    '.......KPPPPPP' 'C',
    '.......KPPPPPK' 'C',
    '........KPPPKK' 'C',
    '.........KKK..' 'K',
]
# The downstroke: the wings taken off, then swept down and out beside the body from the shoulders.
DOWN = {
    9:  '........KK',
    10: '......KKWW',
    11: '....KKWWWW',
    12: '..KKWWWWWK',
    13: '.KWWWWWWWK',
    14: 'KWWWWWWWWK',
    15: 'KWWWWWWWK.',
    16: 'KWWWWWWK..',
    17: 'KWWWWWK...',
    18: 'KWKWKWK...',
    19: '.K.K.K....',
}


def downstroke(rows):
    g = [list(r) for r in rows]
    for y in range(15):
        g[y][:10] = '.' * 10
    for y, t in DOWN.items():
        for i, c in enumerate(t):
            if c != '.':
                g[y][i] = c
    return [''.join(r) for r in g]


def whole(halves):
    return [h + h[13::-1] for h in halves]


SIDE = [
    '......KKK............K.....',
    '.....KWWWK..........KWK....',
    '....KWWWWK.........KWWWK...',
    '.....KWWWWK.......KWWWWWK..',
    '.....KWWWWWK......KWWWWWWK.',
    '....KWWWWWWK.....KWWWWWWWK.',
    '.....KWWWWWWK...KWWWWWWWK..',
    '...K..KWWWWWWK..KWWWWWWWK..',
    '..KCKKKKKKWKKKKKWWWWWWWWK..',
    '.KCCPKPKKKPPPPPWWWWWWWWWK..',
    '.KCKPPPKKPPPPPPPKWWWWWKK...',
    'KCPPPPPPPPPPPPPPPPKWKK.....',
    'KCPPPPPPPPPPPPPPPPPPKK.....',
    '.KKKKKPPPPPPPPPPPPPPPPK....',
    '.....KPPPPPPPPPPPPPPPPK....',
    '......KKPPPPPPPPPPPPPPPKK..',
    '.......KPPPPPPPPPPPPPPKCCK.',
    '.......KKPPKKKKKKPPPKKKCCCK',
    '........KPPK....KPPPK.KCCK.',
    '.........KK......KKK...KK..',
]
# From the side the downstroke hides the wings, as Alber's: the far one's tip over its back, the near one
# hanging over its flank to below its belly.
SIDE_DOWN = [
    '...........................',
    '...........................',
    '...........................',
    '...........................',
    '...........................',
    '.............K.............',
    '............KWK............',
    '...K.......KWWK............',
    '..KCKKKKKKKKWWKKK..........',
    '.KCCPKPKKKPPPPPPPKK........',
    '.KCKPPPKKPPPPPPPPPPK.......',
    'KCPPPPPPPPPPPPPPPPPPKK.....',
    'KCPPPPPPPKKKKPPPPPPPPK.....',
    '.KKKKKPPKWWWWKPPPPPPPPK....',
    '.....KPKWWWWWWKPPPPPPPK....',
    '......KKWWWWWWWKPPPPPPPKK..',
    '.......KWWWWWWWWKPPPPPKCCK.',
    '.......KWWWWWWWWKPPPKKKCCCK',
    '........KWKWKWKWKPPPK.KCCK.',
    '.........K.K.K.K.KKK...KK..',
]

VIEWS = {
    'D': [(5, 4, whole(FRONT)), (5, 4, whole(downstroke(FRONT)))],
    'U': [(5, 4, whole(BACK)), (5, 4, whole(downstroke(BACK)))],
    'L': [(6, 6, SIDE), (6, 6, SIDE_DOWN)],
}
VIEWS['R'] = [(40 - x0 - len(rows[0]), top, [r[::-1] for r in rows]) for x0, top, rows in VIEWS['L']]
FRAMES = {v: [ff.grid([(top + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, top, rows in fs]
          for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(12, 'ebigane', FRAMES, PAL, cap=24)
    minis.chase_gif(12, CHASE, FRAMES, PAL)
