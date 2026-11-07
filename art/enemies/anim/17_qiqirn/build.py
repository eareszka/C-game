"""Qiqirn's animation (runs round the border away from the player; stands in a fit). PixelLab, 52x52.
views: right = its approved NES sprite; down = rotate's south-west-07 (it faces us), up = north-east-03 (its
back) -- the rotate's labels didn't match what it drew; left = right mirrored.
  idle (the fit, 5 x 260 ms = 1.3 s, the old loop): pixellab/fit-VIEW-NN in FIT order, frame 1 the convulsion,
        mouth gaping -- Qiqirn::breathe throws its twitching ring on it
  flap (the run, 4): pixellab/run-VIEW-01..04 -- a frightened gallop, ears back, tail tucked; 130 ms a pose
Snapped to its palette WITHOUT the mid skin tone (flat NES skin: PixelLab had mottled the two close tones into
soft steps), then pixtools.tidy.
Run: python -B art/enemies/anim/17_qiqirn/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
W = H = 52
VIEWS = ('down', 'right', 'up')
FIT = {'down': [0, 1, 2, 3, 4], 'right': [0, 3, 2, 1, 4], 'up': [0, 1, 2, 1, 0]}

MID, LIGHT = (215, 161, 117, 255), (240, 184, 144, 255)

def flat_skin(im):
    """PixelLab mottled its two close skin tones into soft steps (the checker): the mid one becomes the light one
    -- flat NES skin, the browns left to shade it; 3 shades of the colour, the bible's limit."""
    out = im.copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            if px[x, y] == MID: px[x, y] = LIGHT
    return out

def poses():
    pal = [c for c in pt.palette_of(os.path.join(HERE, 'original_sprite.png')) if c != MID]
    L = lambda n: pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', n)), pal))
    return {v: {'idle': [L('fit-%s-%02d.png' % (v, i)) for i in FIT[v]],
                'flap': [L('run-%s-%02d.png' % (v, i)) for i in range(1, 5)]} for v in VIEWS}

if __name__ == '__main__':
    P = poses(); gap = 4
    board = Image.new('RGBA', (9 * (W + gap) + gap, 3 * (H + gap) + gap), (40, 40, 40, 255))
    for r, v in enumerate(VIEWS):
        for c, fr in enumerate(P[v]['idle'] + P[v]['flap']): board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(HERE, 'review', 'board.png'))
    if '--install' in sys.argv:
        d = os.path.join(ROOT, 'assets/enemies/redraws')
        pt.sheet(P, 'idle', os.path.join(d, '17_qiqirn.png'), W, H)
        pt.sheet(P, 'flap', os.path.join(d, '17_qiqirn_run.png'), W, H)
        for name, n in (('17_qiqirn.png', 5), ('17_qiqirn_run.png', 4)):
            print(name); print('\n'.join('  ' + l for l in pt.check_frames(os.path.join(d, name), n, W, H)))
