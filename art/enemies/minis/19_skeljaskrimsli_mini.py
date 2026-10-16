"""19 Skeljaskrimsli's map mini: the shell monster, a hump of grey shells on brown legs, its mouth glowing
green, at the player's scale, four views of two frames (tools/minis.py).

Placed by hand over the shrink of its battle views (python tools/minis.py 19): the dome of shells with their
scale marks, its glowing eyes and toothed mouth under the front of it, the brown legs; from the back its tail
down the middle, from the side its long head, its shells and its tail trailing. The second frame is a heavy
step. 16 px tall, as the Snawfus: its battle frames stand 32. Three of its battle colours and black: its
shell grey (the dark grey of the shells' joints goes to black marks), its brown (legs), its green (the glow
of its eyes and mouth; the red eye goes to it). Its brown and green are off the game palette (its battle
sheet is from before it), so the nearest in it: 8d6b4f, 4fa667. Its pale grey, dark brown, pale green, white
and sand go.

Its chase: plod -- an armoured thing, it comes at you slow and steady, 0.8x the chase pace, the slowest of
them (still faster than you walk). chase_speed() in src/main.cpp and tools/minis.py.

    python art/enemies/minis/19_skeljaskrimsli_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'S': '9797aa', 'B': '8d6b4f', 'G': '4fa667'}
CHASE = 'plod'

# Front and back from row 12: the left half and the middle column, the right half its mirror.
FRONT = [
    '......KK' 'K',
    '....KKSS' 'S',
    '...KSSSK' 'S',
    '..KSSKSS' 'S',
    '.KSSSSSS' 'K',
    '.KSKSSSK' 'S',
    'KSSSSSSS' 'S',
    'KSSSSGKS' 'S',
    'KBBSSKGG' 'G',
    'KBBBSKGK' 'G',
    'KBBBBSKK' 'K',
    'KBBBBBBB' 'B',
    'KBBBBBKK' 'K',
    'KBBBBBK.' '.',
    'KBBBBBK.' '.',
    '.KKKKK..' '.',
]
BACK = FRONT[:7] + [
    'KSSSSSSS' 'S',
    'KBBSSSSS' 'S',
    'KBBBSSSS' 'S',
    'KBBBBSSS' 'S',
    'KBBBBBKS' 'S',
    'KBBBBBKS' 'S',
    'KBBBBBKK' 'S',
    'KBBBBBK.' 'K',
    '.KKKKK..' '.',
]


def whole(halves):
    return [h + h[7::-1] for h in halves]


def step(rows):
    """Its left foot up off the ground."""
    out = list(rows)
    out[13] = '.KKKKK' + rows[13][6:]
    out[14] = '......' + rows[14][6:]
    out[15] = '......' + rows[15][6:]
    return out


SIDE = [                                         # from row 12, its head to the left
    '.....K.K........K.K.K...........',
    '....KSKSKK....KKSKSKSK..........',
    '..KKSSSSSSKKKKSSSSSSSSK.........',
    '.KSSSSKSSSSSSSSSKSSSSSSKK.......',
    'KSSGSSSSSKSSSSSSSSSSKSSSSK......',
    'KGGGGGSSSSSSSKSSSSSSSSSSSKKK....',
    'KGKGKSSSKSSSSSSSSSSKSSSSSSSSKK..',
    '.KKKKKSSSSSSSSSSSSSSSSSSSSSSSSKK',
    '.....KSSBBSSSSSSSSSBBSSKKSSSSSSK',
    '.....KBBBBBSSSSSSSBBBBKK.KKSSSK.',
    '.....KBBBBBBBBBBBBBBBBK....KKK..',
    '.....KBBBBKKKKKKKBBBBBK.........',
]
SIDE_LEGS = (['.....KBBBK.......KBBBK..........', '.....KBBBK.......KBBBK..........',
              '.....KBBBK.......KBBBK..........', '......KKK.........KKK...........'],
             ['....KBBBBK.......KKBBBK.........', '...KBBBKK..........KBBBK........',
              '...KBBBK...........KBBBK........', '....KKK.............KKK.........'])

VIEWS = {
    'D': [(11, 12, whole(FRONT)), (11, 12, step(whole(FRONT)))],
    'U': [(11, 12, whole(BACK)), (11, 12, step(whole(BACK)))],
    'L': [(4, 12, SIDE + legs) for legs in SIDE_LEGS],
}
VIEWS['R'] = [(40 - x0 - len(rows[0]), top, [r[::-1] for r in rows]) for x0, top, rows in VIEWS['L']]
FRAMES = {v: [ff.grid([(top + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, top, rows in fs]
          for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(19, 'skeljaskrimsli', FRAMES, PAL, cap=16)
    minis.chase_gif(19, CHASE, FRAMES, PAL)
