"""13 Beast of the Charred Forests' map mini: the long charcoal lizard with ember spines, a glowing grin and
cracks of fire down its flank, at the player's scale, four views of two frames (tools/minis.py).

Placed by hand over the shrink of its battle views (python tools/minis.py 13): the head with its spikes and
its grin of teeth, the grey back with its ridge of spikes, the charcoal belly with its embers, the legs
splayed; the tail trailing from the side, coming down behind it from the back. Its two frames are stomps (the user,
2026-10-14: "enemy should look like its stomping more"): a foot lifted high, left then right, or from the
side the front leg then the back.
16 px tall, as the Snawfus and the Questing Beast (its battle frames stand 29). Three of its battle colours
and black: its grey (back, legs from the front, tail), its charcoal (head, belly, legs, feet), its ember
orange (spikes, eye, teeth, cracks). Its yellow, white teeth and red go: the grin glows.

Its chase: prowl -- it circles in on you, its heading turned 0.6 rad off the line to you the whole way, at
1.1x the chase pace (closes at 0.91). chase_speed() and chase_bend() in src/main.cpp and tools/minis.py.

    python art/enemies/minis/13_beast_of_the_charred_forests_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '595965', 'B': '282828', 'O': 'fc9838'}
CHASE = 'prowl'

# Front and back from row 12: the left half and the middle column, the right half its mirror.
FRONT = [
    '........K.' 'K',
    '.......KOK' 'O',
    '......KBBB' 'B',
    '.....KBOBB' 'B',
    '.....KOKOK' 'O',
    '.....KKKKK' 'K',
    '....KKBBBB' 'B',
    '...KGGBOBB' 'B',
    '..KGGGBBOB' 'B',
    '.KGGGGBBBB' 'B',
    '.KGGGGKBBB' 'B',
    '.KGGGGKBBB' 'B',
    'KGGGGK.KKK' 'K',
    'KGGGGK....' '.',
    'KBBBBK....' '.',
    '.KKKK.....' '.',
]
BACK = FRONT[:3] + [
    '.....KBBBB' 'B',
    '.....KBBBB' 'B',
    '.....KKBBB' 'B',
    '....KKGGGK' 'O',
    '...KGGGGGK' 'O',
    '..KGGGGGGG' 'G',
    '.KGGGGGGGG' 'G',
    '.KGGGGKGGG' 'G',
    '.KGGGGKGGG' 'G',
    'KGGGGK.KKG' 'G',
    'KGGGGK...K' 'G',
    'KBBBBK...K' 'G',
    '.KKKK.....' 'K',
]


def whole(halves):
    return [h + h[9::-1] for h in halves]


def stomp(rows):
    """Its left foot lifted high off the ground, the right one planted: the next stomp is the mirror."""
    out = list(rows)
    out[11] = 'KBBBBK' + rows[11][6:]
    out[12] = '.KKKK..' + rows[12][7:]
    for y in (13, 14, 15):
        out[y] = '......' + rows[y][6:]
    return out


SIDE = [
    '.....K.K.K......................',
    '....KOKOKOK.......K.K.K.K.......',
    '...KBBBBBBBK....KKOKOKOKOK......',
    '..KBBBBBBBBBKKKKGGGGGGGGGKKK....',
    '.KBBBBBOBBBBBBGGGGGGGGGGGGGGK...',
    'KOKOKOKOKOKBBGGGGGGGGGGGGGGGGK..',
    'KKOKOKOKOKKBBGGGGGGGGGGGGGGGGGK.',
    '.KBBBBBBBBBBBBBBOOBBBOOBBGGGGGK.',
    '..KKKKKKKKKBBBBBBBOBBBBOBBBGGGGK',
    '..........KBBBBBBBBBBBBBBBKGGGK.',
    '..........KBBBBKKKKKKBBBBKKGGK..',
]
# The stomps from the side: the front leg swung up and forward, then the back one raised.
LEGS = (['........KKBBBBK......KBBBK.KGK..',
         '.......KBBBBKK.......KBBBK..K...',
         '........KKKK.........KBBBK......',
         '....................KBBBBK......',
         '.....................KKKK.......'],
        ['..........KBBBK......KBBBK.KGK..',
         '..........KBBBK......KKKKK..K...',
         '..........KBBBK.................',
         '.........KBBBBK.................',
         '..........KKKK..................'])


VIEWS = {
    'D': [(10, 12, stomp(whole(FRONT))), (10, 12, [r[::-1] for r in stomp(whole(FRONT))])],
    'U': [(10, 12, stomp(whole(BACK))), (10, 12, [r[::-1] for r in stomp(whole(BACK))])],
    'L': [(4, 12, SIDE + list(LEGS[0])), (4, 12, SIDE + list(LEGS[1]))],
}
VIEWS['R'] = [(40 - x0 - len(rows[0]), top, [r[::-1] for r in rows]) for x0, top, rows in VIEWS['L']]
FRAMES = {v: [ff.grid([(top + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, top, rows in fs]
          for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(13, 'beast_of_the_charred_forests', FRAMES, PAL, cap=16)
    minis.chase_gif(13, CHASE, FRAMES, PAL)
