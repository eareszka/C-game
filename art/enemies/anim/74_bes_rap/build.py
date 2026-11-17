"""Bes Rap's animation (front view only, always as drawn -- the user, 2026-11-17). PixelLab from its 37x43
NES sprite (pixellab/base.png, 56x56) through animate-with-text-v3, 1 generation each:
  idle (5 x 260 ms, breath_frame 2): idle-00 rest, idle-01 wind-up, idle-03 the SPIT (head turned to us,
        glue puff at the mouth), idle-02 jaw closing, lunge-01 breathes out
  flap (phase 2's lunge, held while it dashes): lunge-04 -- arms flung out ahead
Frames cropped to the union of every pose's drawing (snug: the hit circle comes from the frame).
Run: python -B art/enemies/anim/74_bes_rap/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
IDLE = ['idle-00', 'idle-01', 'idle-03', 'idle-02', 'lunge-01']
LUNGE = 'lunge-04'
SPIT = 2

def frames():
    pal = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    L = lambda n: pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', n + '.png')), pal))
    idle, lunge = [L(n) for n in IDLE], [L(LUNGE)] * 4
    boxes = [f.getbbox() for f in idle + lunge[:1]]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    return [f.crop(box) for f in idle], [f.crop(box) for f in lunge], box

if __name__ == '__main__':
    idle, lunge, box = frames(); W, H = idle[0].size; gap = 4
    board = Image.new('RGBA', (6 * (W + gap) + gap, H + 2 * gap), (0, 0, 0, 255))
    for i, fr in enumerate(idle + lunge[:1]): board.paste(fr, (gap + i * (W + gap), gap), fr)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    board.resize((board.width * 4, board.height * 4), Image.NEAREST).save(os.path.join(HERE, 'review', 'board.png'))
    big = lambda f: Image.alpha_composite(Image.new('RGBA', f.size, (0, 0, 0, 255)), f).convert('RGB').resize((W * 4, H * 4), Image.NEAREST)
    g = [big(f) for f in idle]
    g[0].save(os.path.join(HERE, 'review', 'idle.gif'), save_all=True, append_images=g[1:], duration=260, loop=0)
    print('frame %dx%d, crop %s of the 56x56 canvas' % (W, H, box))
    if '--install' in sys.argv:
        P = {'down': {'idle': idle, 'flap': lunge}}
        d = os.path.join(ROOT, 'assets/enemies')
        pt.sheet(P, 'idle', os.path.join(d, '74_bes_rap.png'), W, H, front_only=True)
        pt.sheet(P, 'flap', os.path.join(d, '74_bes_rap_lunge.png'), W, H, front_only=True)
        for n, k in (('74_bes_rap.png', 5), ('74_bes_rap_lunge.png', 4)):
            print(n, pt.check_frames(os.path.join(d, n), k, W, H, views=(('down', 0),))[0])
