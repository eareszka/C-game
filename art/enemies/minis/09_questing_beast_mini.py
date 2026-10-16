"""09 Questing Beast's map mini: snake's head, leopard's body, hart's legs, galloping, at the player's scale,
four views of two frames (tools/minis.py).

Drawn from its walk sheet (assets/enemies/09_questing_beast_walk.png, frames 0 and 2, shrunk and cleaned with
minis.clean, then placed by hand). 16 px tall, as the Snawfus: its legs are long. Three of its battle colours
and black: its leopard tan, its snake green, its dark brown (legs, spots, the tail's tuft).

Its chase: dash -- straight at you (the user, 2026-10-14: "have it be a straight dash", over tacking across
your line): 1.5x your running speed for 0.5 s, then 0.5x for 0.5 s, 1.0 on average. chase_speed() in
src/main.cpp and tools/minis.py.

    python art/enemies/minis/09_questing_beast_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'T': 'c18a39', 'G': '29633e', 'D': '3c2412'}
CHASE = 'dash'

FRONT = [
    '...KKK...',
    '..KGGGK..',
    '.KGDGDGK.',
    '..KGGGK..',
    '...KGK...',
    '..KKGKK..',
    '.KTTTTTK.',
    '.KTDTTTK.',
    '.KTTTDTK.',
    '.KTTTTTK.',
    '.KKTTTKK.',
]
BACK = [r.replace('KGDGDGK', 'KGGGGGK') for r in FRONT[:9]] + ['.KTTDTTK.', '.KKTDTKK.']
LEGS = (['.KDKKKDK.', '.KDK.KDK.', '.KDK.KDK.', '.KDK.KDK.', '..K...K..'],
        ['.KDKKKDK.', '..K..KDK.', '.....KDK.', '.....KDK.', '......K..'])
SIDE = [
    '..KKK..............',
    '.KGGGK.............',
    'KGDGGK.............',
    '.KKGGK.............',
    '..KGGK.............',
    '..KGGGKKKKKKKK.....',
    '...KGGTTTTTTTTKK...',
    '...KTTTDTTTDTTTTKK.',
    '...KTTTTTTTTTTTTKDK',
    '....KTTDTTTTTTTKKDK',
]
STRIDE = (['....KDKKKKKKKKDKKDK', '...KDK........KDKK.', '..KDK.........KDK..', '.KDK...........KDK.',
           '.KDK...........KDK.', '..K.............K..'],                                    # stretched out
          ['....KKDKKKKKKDKKKDK', '.....KDK....KDK.KK.', '.....KDK....KDK....', '.....KDK....KDK....',
           '.....KDK....KDK....', '......K......K.....'])                                    # legs under it
VIEWS = {
    'D': [(16, FRONT + LEGS[0]), (16, FRONT + LEGS[1])],
    'U': [(16, BACK + LEGS[0]), (16, BACK + [r[::-1] for r in LEGS[1]])],
    'L': [(10, SIDE + STRIDE[0]), (10, SIDE + STRIDE[1])],
}
VIEWS['R'] = [(40 - x0 - len(rows[0]), [r[::-1] for r in rows]) for x0, rows in VIEWS['L']]
FRAMES = {v: [ff.grid([(12 + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, rows in fs] for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(9, 'questing_beast', FRAMES, PAL, cap=16)
    minis.chase_gif(9, CHASE, FRAMES, PAL)
