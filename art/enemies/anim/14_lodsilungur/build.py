"""Lodsilungur's animation (Swimmer: a slow S in phase 1, very fast wall-to-wall dashes in phase 2). PixelLab,
48x48 canvas. views: down = its approved NES sprite (face-on); right = rotate's east-02; up = north-04; left mirrored.
  idle (swimming, 5 x 260 ms = 1.3 s, the old loop): pixellab/swim-VIEW-NN in SWIM order, frame 1 the INHALE
        (cheeks puffed, mouth shut) -- Lodsilungur::breathe sprays its spores on it
  alt  (the beard flick, a 260 ms step each flick in phase 1): pixellab/flick-VIEW-NN
  flap (5): 0-3 the dash (pixellab/dash-VIEW-01..04), 130 ms a pose; 4 the SLAM -- a dash pose squashed wide
        and flat (an NES squish), held while it gets its breath against the wall
Every frame through pixtools.tidy (the clean-up pass) after the palette snap.
Run: python -B art/enemies/anim/14_lodsilungur/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
W = H = 48
VIEWS = ('down', 'right', 'up')
SWIM  = {'down': [0, 3, 4, 2, 1], 'right': [0, 3, 4, 2, 1], 'up': [0, 2, 3, 4, 1]}
FLICK = {'down': 2, 'right': 2, 'up': 3}

def squash(im):
    b = im.getbbox(); c = im.crop(b)
    c = c.resize((round(c.width * 1.25), round(c.height * 0.78)), Image.NEAREST)
    out = Image.new('RGBA', (W, H), pt.CLEAR); out.paste(c, (W // 2 - c.width // 2, b[3] - c.height), c); return out

def poses():
    pal = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    L = lambda n: pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', n)), pal))
    P = {}
    for v in VIEWS:
        dash = [L('dash-%s-%02d.png' % (v, i)) for i in range(1, 5)]
        P[v] = {'idle': [L('swim-%s-%02d.png' % (v, i)) for i in SWIM[v]],
                'flick': [L('flick-%s-%02d.png' % (v, FLICK[v]))] * 5,
                'flap': dash + [pt.tidy(squash(dash[0]))]}
    return P

if __name__ == '__main__':
    P = poses(); gap = 4
    board = Image.new('RGBA', (11 * (W + gap) + gap, 3 * (H + gap) + gap), (40, 40, 40, 255))
    for r, v in enumerate(VIEWS):
        for c, fr in enumerate(P[v]['idle'] + P[v]['flick'][:1] + P[v]['flap']): board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(HERE, 'review', 'board.png'))
    if '--install' in sys.argv:
        d = os.path.join(ROOT, 'assets/enemies')
        pt.sheet(P, 'idle', os.path.join(d, '14_lodsilungur.png'), W, H)
        pt.sheet(P, 'flick', os.path.join(d, '14_lodsilungur_flick.png'), W, H)
        pt.sheet(P, 'flap', os.path.join(d, '14_lodsilungur_dash.png'), W, H)
        for name, n in (('14_lodsilungur.png', 5), ('14_lodsilungur_flick.png', 5), ('14_lodsilungur_dash.png', 5)):
            print(name); print('\n'.join('  ' + l for l in pt.check_frames(os.path.join(d, name), n, W, H)))
