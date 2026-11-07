"""Rumptifusel's animation (never moves; one 3/4 view, facing left as drawn, in every direction, never mirrored).
PixelLab from its approved 42x28 NES sprite on a 56x44 canvas.
  idle (5 poses x 390 ms = 1.95 s -- its old loop was 1.94 s, kept so its sheets come no faster): flat (rear-00),
        hood rising (rear-02), REARED, belly bared (rear-03 -- frame 2, Rumptifusel::breathe throws its sheets),
        still up (rear-04), coming down (rear-02)
  BELLY: measured here on the reared frame (the purple's middle) and printed for Rumptifusel::belly().
Run: python -B art/enemies/anim/60_rumptifusel/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
W, H = 56, 44
ORDER = [0, 2, 3, 4, 2]
def frames():
    pal = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    return [pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', 'rear-%02d.png' % i)), pal)) for i in ORDER]
def belly(fr):
    px = fr.load(); pts = [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][2] > px[x, y][1] + 30 and px[x, y][0] > px[x, y][1]]
    return sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)
if __name__ == '__main__':
    F = frames(); gap = 4
    board = Image.new('RGBA', (len(F) * (W + gap) + gap, H + 2 * gap), (40, 40, 40, 255))
    for i, fr in enumerate(F): board.paste(fr, (gap + i * (W + gap), gap), fr)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(HERE, 'review', 'board.png'))
    bx, by = belly(F[2])
    print('belly (frame px, reared): %.1f, %.1f  -> screen offset %.1f, %.1f' % (bx, by, (bx + 0.5 - W / 2) * 2, (by + 0.5 - H / 2) * 2))
    if '--install' in sys.argv:
        path = os.path.join(ROOT, 'assets/enemies/60_rumptifusel.png')
        pt.sheet({'down': {'idle': F}}, 'idle', path, W, H, front_only=True)
        print(pt.check_frames(path, 5, W, H, views=(('down', 0),))[0])
