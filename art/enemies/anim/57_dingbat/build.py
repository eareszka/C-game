"""Dingbat's animation (a flyer: always faces down, front view only; glides perch to perch, perched it CATCHES
shots -- a blocker). PixelLab from its approved 33x22 NES sprite on a 48x40 canvas.
  idle (gliding, 5 x 260 ms): pixellab/glide-NN -- spread wings, one strong downstroke; frame 2 the downstroke
  alt  (perched, BLOCKING, 5 x 260 ms): pixellab/wrap.png -- a PixelLab edit: both feathered wings folded
        forward and crossed over its whole body, only the antler tips showing (the user: "when blocking the
        entire body should be covered by wings, blocking should be very visually obvious"); it shivers a pixel
        side to side (plus the blocking flicker). (The first cut's cupped catch-NN poses showed too much body.)
  flap (4): 0 the stare's cupped wings, 1 the stare's flare (wings thrown open, eyes wide) -- 260 ms each;
        2 guard IN (catch-02, wings half round it, a step as it perches); 3 guard OUT (catch-01, wings opening, a
        step as it takes off)
Blocking it also flickers like the player's i-frames (src/battle.cpp, _draw_enemy).
Run: python -B art/enemies/anim/57_dingbat/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
W, H = 48, 40
def frames():
    pal = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    L = lambda k, i: pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', '%s-%02d.png' % (k, i))), pal))
    wrap = pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', 'wrap.png')), pal))
    return {'idle': [L('glide', i) for i in (0, 1, 2, 3, 1)],
            'catch': [pt.jolt(wrap, dx, 0) for dx in (0, 1, 0, -1, 0)],
            'flap': [L('stare', 2), L('stare', 4), L('catch', 2), L('catch', 1)]}
if __name__ == '__main__':
    F = frames(); P = {'down': F}; gap = 4
    seq = F['idle'] + F['catch'] + F['flap']
    board = Image.new('RGBA', (len(seq) * (W + gap) + gap, H + 2 * gap), (40, 40, 40, 255))
    for i, fr in enumerate(seq): board.paste(fr, (gap + i * (W + gap), gap), fr)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(HERE, 'review', 'board.png'))
    if '--install' in sys.argv:
        d = os.path.join(ROOT, 'assets/enemies')
        for k, name in (('idle', '57_dingbat.png'), ('catch', '57_dingbat_catch.png'), ('flap', '57_dingbat_stare.png')):
            pt.sheet(P, k, os.path.join(d, name), W, H, front_only=True)
            print(name, pt.check_frames(os.path.join(d, name), len(F[k]), W, H, views=(('down', 0),))[0])
