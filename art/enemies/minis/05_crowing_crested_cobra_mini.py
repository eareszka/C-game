"""05 Crowing Crested Cobra's map mini: the crested snake slithering, at the player's scale, four views
(tools/minis.py).

Drawn from its phase 2 slither sheet (assets/enemies/05_crowing_crested_cobra_slither.png, frame 0 of each view),
not its coiled pose (the user, 2026-10-14: "have its sprite be more similar to its slithering 2nd phase"):
coming at you its head is low and near with the body curling up behind, going away the head is high and the
body trails down to the tail, and from the side it lies long and low in a wave. Three of its battle colours and
black: its sand, its pale belly and mouth, its red crest (its brown pattern and pink cheek go).

Its chase: wiggle -- straight at you, its heading swinging 0.6 rad either side every 0.35 s, a quick slither
("it move in a quick slighering sin motion"). chase_bend() in src/main.cpp and tools/minis.py.

    python art/enemies/minis/05_crowing_crested_cobra_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': 'd0c078', 'L': 'e8e0c0', 'R': 'b70000'}
CHASE = 'wiggle'

VIEWS = {
    'D': (15, [
        '.KKK.....',
        'KLMK.....',
        'KMMKK....',
        '.KMMMKK..',
        '..KKMMMK.',
        '.KKKKKMMK',
        'KRRRRRKMK',
        'KMKMKMKK.',
        'KMMMMMK..',
        'KMLLLMK..',
        '.KMMMK...',
        '..KKK....',
    ]),
    'U': (15, [
        '..KKKK...',
        '.KRRRRK..',
        'KMMMMMMK.',
        'KMMMMMMK.',
        '.KMLLMK..',
        '..KMMMK..',
        '..KMMMMK.',
        '...KMMMK.',
        '..KLMMMK.',
        '.KLMMMK..',
        'KMMMKK...',
        '.KKK.....',
    ]),
    'L': (12, [
        '................',
        '................',
        '................',
        '.KK.KK..........',
        'KRRKRRK.........',
        'KMKMMMK.........',
        'KLLLKMK..KKKK...',
        '.KKKLMKKKLMMMKK.',
        '.KMMMLLMMMMMMMLK',
        'KMMMMMMMMKKKMMMK',
        '.KMMMMMMK...KKK.',
        '..KKKKKK........',
    ]),
}
VIEWS['R'] = (40 - 12 - 16, [r[::-1] for r in VIEWS['L'][1]])
FRAMES = {v: ff.grid([(16 + y, x0, r) for y, r in enumerate(rows)], PAL) for v, (x0, rows) in VIEWS.items()}

SLITHER = minis.ROOT / 'assets/enemies/05_crowing_crested_cobra_slither.png'     # 8 views x 4 frames of 26x24


def slither_views():
    from PIL import Image
    im = Image.open(SLITHER).convert('RGBA')
    return {v: im.crop((d * 4 * 26, 0, d * 4 * 26 + 26, 24)) for v, d in minis.VIEWS}


if __name__ == '__main__':
    minis.make(5, 'crowing_crested_cobra', FRAMES, PAL, ref=slither_views())
    minis.chase_gif(5, CHASE, FRAMES, PAL)
