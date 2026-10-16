"""02 Treesqueak's map mini: the tree squirrel at the player's scale, four views (tools/minis.py).

Started from the shrink of its battle views (python tools/minis.py 2), placed by hand: round ears, the muzzle
and belly in its tan, the tail curled on the ground behind it in the side views and up its back from behind.
Three of its battle colours and black: its brown, its dark brown, its tan (the pink nose, white eye and moss
spots go).

Its chase: dart -- a scurry at 1.5x the player's running speed for 0.3 s, then a freeze for 0.25 s (0.82x on
average), chase_speed() in tools/minis.py and chase_step() in src/main.cpp.

    python art/enemies/minis/02_treesqueak_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '785830', 'D': '3c2412', 'L': 'cebe82'}
CHASE = 'dart'

VIEWS = {
    'D': (15, [
        '.KK.....KK.',
        'KMDKKKKKMDK',
        '.KKMMMMMKK.',
        '.KMKMMMKMDK',
        '.KMLLDLLMDK',
        '..KMLLLMDK.',
        '..KKMMMKKK.',
        '.KMMLLLMDK.',
        '.KMMLLLMDK.',
        'KMMMLLLMDDK',
        'KMKMLLLMKDK',
        '.KKKKKKKKK.',
    ]),
    'U': (15, [
        '.KK.....KK.',
        'KMDKKKKKMDK',
        '.KKMMMMMKK.',
        '.KMMMMMMMDK',
        '.KMMMMMMMDK',
        '..KMMMMMDK.',
        '..KKMDMKKK.',
        '.KMMMDMMDK.',
        '.KMMMDMMDK.',
        'KMMMMDMMDDK',
        'KMDMMDMMKDK',
        '.KKKKKKKKK.',
    ]),
    'L': (13, [
        '.....KK........',
        '..KKKMDK.......',
        '.KMMMMMDK......',
        'KMMKMMMDK......',
        'KDLLMMMDK......',
        '.KKLMMDK.......',
        '.KLLMMDK...KKK.',
        '.KLLMMMDK.KDDDK',
        '.KLLMMMDK.KDKDK',
        '.KLLMMMDKKKDDDK',
        '.KLLLMMDDDDDKK.',
        '..KKKKKKKKKKK..',
    ]),
}
VIEWS['R'] = (40 - 13 - 15, [r[::-1] for r in VIEWS['L'][1]])
FRAMES = {v: ff.grid([(16 + y, x0, r) for y, r in enumerate(rows)], PAL) for v, (x0, rows) in VIEWS.items()}

if __name__ == '__main__':
    minis.make(2, 'treesqueak', FRAMES, PAL)
    minis.chase_gif(2, CHASE, FRAMES, PAL)
