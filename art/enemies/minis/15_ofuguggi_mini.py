"""15 Ofuguggi's map mini: the black reverse-fin trout with its red stripe, swimming through the air tail first
as in its fight, at the player's scale, four views of two frames (tools/minis.py).

Placed by hand over the shrink of its swim sheet (assets/enemies/15_ofuguggi_swim.png, python tools/minis.py
15). Drawn the way it swims, TAIL FIRST, as its battle sheets are: coming at you you see its tail and its fins
spread, going away its face; from the side its tail leads the way and its head trails. The second frame is a
bob of its swim. 12 px tall: its battle frames stand 16. Three of its battle colours and black: its dark grey,
its grey (the light along its back, high on the left), its red (stripe, eyes, mouth). Its near-black, pale
grey, dark red and pink go.

Its chase: meander -- as it wanders in its fight, curving and changing pace: its heading swings 0.7 rad
either way off the line to you every 1.3 s, its pace rises and falls from 0.5x to 1.5x every 0.9 s (closes
at 0.89). chase_speed() and chase_bend() in src/main.cpp and tools/minis.py.

    python art/enemies/minis/15_ofuguggi_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '474751', 'L': '848694', 'R': 'b70000'}
CHASE = 'meander'

# Coming at you, its tail; going away, its face. From row 16: the left half and the middle column, the right
# half its mirror.
TAIL = [
    '.....K' 'K',
    '....KG' 'G',
    '....KG' 'G',
    '...KLL' 'G',
    '..KGLG' 'G',
    '.KGKGG' 'G',
    'KGKGGG' 'G',
    'KKKKGG' 'G',
    'K...KG' 'G',
    '....KG' 'G',
    '...KGK' 'G',
    '...KK.' 'K',
]
FACE = [
    '.....K' 'K',
    '....KG' 'G',
    '....KG' 'G',
    '...KLL' 'L',
    '..KLLG' 'G',
    '.KLKGG' 'G',
    'KRGGGG' 'G',
    'KGKGGG' 'G',
    'KKKKKR' 'R',
    '....KG' 'G',
    '....KK' 'K',
    '......' '.',
]
SIDE = [
    '....................',
    '.KK.........K.......',
    '.KGK.......KGK......',
    '..KGK.....KGGGK.....',
    '..KGGKKKKKLLLLLKKK..',
    '..KGGGLLLLGGGGGGGGKK',
    '...KGGGGGGGGGGGGGRGK',
    '...KGRRRRRRRRRRGGGGK',
    '..KGGKKKKGGGGGGGGRK.',
    '..KGK....KKKKKKKKK..',
    '.KGK................',
    '.KK.................',
]


def whole(halves):
    return [h + h[5::-1] for h in halves]


def swish(rows):
    """Its tail flicked a pixel to one side."""
    return rows[:9] + ['.' + r[:-1] for r in rows[9:]]


VIEWS = {
    'D': [(13, 16, whole(TAIL)), (13, 15, swish(whole(TAIL)))],
    'U': [(13, 16, whole(FACE)), (13, 15, whole(FACE))],
    'L': [(10, 16, SIDE), (10, 15, SIDE)],
}
VIEWS['R'] = [(40 - x0 - len(rows[0]), top, [r[::-1] for r in rows]) for x0, top, rows in VIEWS['L']]
FRAMES = {v: [ff.grid([(top + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, top, rows in fs]
          for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(15, 'ofuguggi', FRAMES, PAL, cap=12)
    minis.chase_gif(15, CHASE, FRAMES, PAL)
