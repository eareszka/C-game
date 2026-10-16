"""08 Snawfus's map mini: the white deer with flowering antlers at the player's scale, four views (tools/minis.py).

Placed by hand from its battle views (python tools/minis.py 8), 16 px tall (a medium enemy is 12, but the deer
is tall and at 12 its legs and antlers went): the pink blossoms on its antlers, the white head
and body, the grey underside and legs. Narrow from the front (the user, 2026-10-14: "make front view thinner"), and two frames a view, a gallop
("2 frames galloping"): from the side its legs stretched out, then gathered under it; from the front and back
one foreleg lifts. Three of its battle colours and black: its white, its pale grey, its
blossom pink (the antlers' brown goes -- they are grey -- and so do the blue wisps).

Its chase: bound -- a deer's leaps, 1.7x your running speed for 0.3 s, then a landing at 0.2x for 0.3 s
(0.95 on average; chase_speed() in src/main.cpp and tools/minis.py). Its frames follow the bound (the user:
"have its movement match its sprites current frame"): stretched out in the leap, gathered on the landing
(chase_frame()).

    python art/enemies/minis/08_snawfus_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'W': 'fcfcfc', 'G': 'c6ccda', 'P': 'fc74b4'}
CHASE = 'bound'

FRONT = [                       # the head and chest, the same in both frames (no eyes from behind)
    '.KK.....KK.',
    'KPPK...KPPK',
    '.KGK...KGK.',
    '..KGKKKGK..',
    '..KKWWWKK..',
    '..KWKWKWK..',
    '...KWWWK...',
    '....KWK....',
    '...KKWKK...',
    '..KWWWWGK..',
    '..KWWWWGK..',
    '..KGGGGGK..',
    '..KGKKKGK..',
]
LEGS_FRONT = (['..KGK.KGK..', '..KGK.KGK..', '...K...K...'],      # both forelegs down
              ['...K..KGK..', '......KGK..', '.......K...'])      # one lifted in the gallop
SIDE = [
    '.KK.KK..........',
    'KPPKPPK.........',
    '.KGKGK..........',
    '..KGGK..........',
    '.KKWWK..........',
    'KWKWWWK.........',
    'KWWWWWWK........',
    '.KKKWWWK........',
    '....KWWWKKKKKK..',
    '....KWWWWWWWWWK.',
    '....KGWWWWWWWGK.',
    '....KGGGGGGGGGK.',
]
LEGS_SIDE = (['...KGKKKKKKKGK..', '..KGK.......KGK.', '.KGK.........KGK', '..K...........K.'],   # stretched out
             ['....KKGKKKGKKKK.', '......KGKGK.....', '.......K.K......', '................'])  # gathered under it
back = [r.replace('KWKWKWK', 'KWWWWWK') for r in FRONT]
VIEWS = {
    'D': [(14, FRONT + LEGS_FRONT[0]), (14, FRONT + LEGS_FRONT[1])],
    'U': [(14, back + LEGS_FRONT[0]), (14, back + [r[::-1] for r in LEGS_FRONT[1]])],
    'L': [(12, SIDE + LEGS_SIDE[0]), (12, SIDE + LEGS_SIDE[1])],
}
VIEWS['R'] = [(40 - x0 - len(rows[0]), [r[::-1] for r in rows]) for x0, rows in VIEWS['L']]
FRAMES = {v: [ff.grid([(12 + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, rows in fs] for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(8, 'snawfus', FRAMES, PAL, cap=16)
    minis.chase_gif(8, CHASE, FRAMES, PAL)
