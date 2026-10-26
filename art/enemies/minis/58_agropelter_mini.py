"""58 Agropelter's map mini: the lumberjack's widow-maker, an ape's face on a sinewy little body, arms like whips,
waiting crouched and then pouncing at you, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet has one view, its front. Through PixelLab (art/enemies/pixellab/58_agropelter/mini,
pixellab-out/58-mini, four generations): eight rotations of its battle front, then its front, back and left side
each given a pounce -- crouched still, then springing with its whip arms flung out. Its side is its three-quarter
view (south-west): the side itself hides its arms. Each mini frame is one of those on the mini's palette
(minis.recolour), shrunk (minis.shrink, a view's frames by one box so they line up), cleaned (minis.clean), one black
outline round it: crouched and waiting, then the pounce, two pixels off the ground. The right view is the left
mirrored.
17 px tall: its battle height (49 px) at the minis' one scale, 28/79. Three of its battle colours and black: its
pale skin (arms, face, chest), its brown fur, its dark fur.

Its chase: the pounce (as the Paoxiao's, chase_speed() and chase_frame(), src/main.cpp) -- crouched still in wait
(frame 0), then a leap (frame 1): it lies in wait for lumberjacks.

    python art/enemies/minis/58_agropelter_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis

PAL = {'K': '000000', 'S': 'f0b890', 'F': '8d6b4f', 'D': '463422'}
CHASE = 'pounce'
HEIGHT = 17
LEAP = 2                                         # the pounce frame's lift off the ground
SRC = ROOT / 'pixellab-out/58-mini/animations'
POUNCES = {'D': ('v2/pounced', (0, 4)), 'U': ('v3/pounceu', (0, 4)), 'L': ('v1/pouncel', (0, 4))}   # waiting, pouncing


def tone(h, s, v):
    """Its darkest black, its pale warm skins the skin, its furs brown or dark by value."""
    if v < 0.2: return 'K'
    if v > 0.8 and s > 0.2: return 'S'
    return 'F' if v > 0.42 else 'D'


def view(name, picks):
    ims = [minis.recolour(Image.open(SRC / f'{name}-{i:02d}.png').convert('RGBA'), tone, PAL) for i in picks]
    boxes = [im.getbbox() for im in ims]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    letters = {v: k for k, v in PAL.items() if k != 'K'}
    gs = [minis.clean(minis.shrink(im, HEIGHT - LEAP, letters, box)) for im in ims]
    return [gs[0], {(x, y - LEAP): c for (x, y), c in gs[1].items()}]


# By hand: its ape's face, which the shrink loses -- its eyes (K) and a grin of teeth (K corners, S teeth).
FACE = {'D': [{(18, 17): 'K', (20, 17): 'K', (18, 19): 'K', (19, 19): 'S', (20, 19): 'S', (21, 19): 'K'},
              {(18, 14): 'K', (20, 14): 'K', (18, 16): 'K', (19, 16): 'S', (20, 16): 'S', (21, 16): 'K'}],
        'L': [{(20, 18): 'K', (19, 19): 'S'}, {(19, 14): 'K', (18, 15): 'K'}]}

FRAMES = {v: view(*POUNCES[v]) for v in 'DUL'}
for v, fs in FACE.items():
    for g, face in zip(FRAMES[v], fs):
        for p, c in face.items():
            assert p in g and g[p] != 'K', (v, p)
            g[p] = c
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(58, 'agropelter', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(58, CHASE, FRAMES, PAL)
