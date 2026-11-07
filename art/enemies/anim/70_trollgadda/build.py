"""Trollgadda's animation (redone 2026-11-06: swims around near the top, shaking its tree harder and harder as its
HP drops). Side view only (left = mirrored). PixelLab from its approved 36x25 NES sprite on a 52x40 canvas.
  shake sheet (flap, always on), 12 a direction -- three levels, each 4 poses (PixelLab frames 01-04):
     0-3  shake1: swimming, the tree swaying gently          (HP > 2/3)  260 ms a pose
     4-7  shake2: the tree shaken hard, jolted a pixel        (> 1/3)     200 ms
     8-11 shake3: thrashing, jolted 2-3 px                    (below)     130 ms
  The jolts are added here: PixelLab's levels differed too little to read as "more and more aggressive".
  idle sheet: shake1's poses (it is always swimming; the flap sheet covers it).
Run: python -B art/enemies/anim/70_trollgadda/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
W, H = 52, 40
JOLT = {1: [(0, 0)] * 4, 2: [(0, -1), (1, 0), (0, 1), (-1, 0)], 3: [(2, -2), (-3, 1), (2, 2), (-2, -1)]}
def poses():
    pal = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    L = lambda k, i: pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', 'shake%d-%02d.png' % (k, i))), pal))
    flap = [pt.jolt(L(k, i), *JOLT[k][i - 1]) for k in (1, 2, 3) for i in range(1, 5)]
    side = {'idle': flap[:4] + [flap[0]], 'flap': flap}
    return {'down': side, 'up': side, 'right': side}
if __name__ == '__main__':
    P = poses(); gap = 4; seq = P['right']['flap']
    board = Image.new('RGBA', (4 * (W + gap) + gap, 3 * (H + gap) + gap), (40, 40, 40, 255))
    for i, fr in enumerate(seq): board.paste(fr, (gap + (i % 4) * (W + gap), gap + (i // 4) * (H + gap)), fr)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(HERE, 'review', 'board.png'))
    if '--install' in sys.argv:
        d = os.path.join(ROOT, 'assets/enemies')
        pt.sheet(P, 'idle', os.path.join(d, '70_trollgadda.png'), W, H)
        pt.sheet(P, 'flap', os.path.join(d, '70_trollgadda_shake.png'), W, H)
        print(pt.check_frames(os.path.join(d, '70_trollgadda_shake.png'), 12, W, H, views=(('right', 2),))[0])
