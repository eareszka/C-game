"""Agropelter's animation (never moves; front view only -- it squats facing the player by design). PixelLab from
its approved 37x28 NES sprite on a 60x44 canvas.
  idle (5 x 260 ms = 1.3 s, the old loop): 0 rest (whip-00), 1 its RIGHT arm (screen right) lashed out (whip-01)
        -- the right lash; 2 arms flung wide (scream-04); 3 its LEFT arm lashed out (whip-02) -- the left lash;
        4 the SCREAM, mouth widest (scream-02). Agropelter::on_idle_frame lashes on 1 and 3, screams on 4.
  HANDS / MOUTH: measured here from the frames (the outermost skin pixel each side, the mouth's middle) and
        printed as the C++ table for Agropelter::HAND / MOUTH_Y (offsets from the frame's middle, drawn 2x).
Run: python -B art/enemies/anim/58_agropelter/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
W, H = 60, 44
ORDER = [('whip', 0), ('whip', 1), ('scream', 4), ('whip', 2), ('scream', 2)]

def frames():
    pal = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    return [pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', '%s-%02d.png' % k)), pal)) for k in ORDER]

def hands(fr):
    px = fr.load(); sk = [(x, y) for y in range(H) for x in range(W) if pt.skin(px[x, y])]
    r = max(sk, key=lambda p: p[0]); l = min(sk, key=lambda p: p[0])
    off = lambda p: ((p[0] + 0.5 - W / 2) * 2, (p[1] + 0.5 - H / 2) * 2)
    return off(r), off(l)

def mouth(fr):
    px = fr.load(); b = fr.getbbox()
    cx = (b[0] + b[2]) / 2
    blk = [(x, y) for y in range(b[1], b[1] + 18) for x in range(int(cx) - 5, int(cx) + 6)
           if px[x, y] == pt.BLACK and all(px[x + dx, y][3] for dx in (-1, 1))]
    return (sum(y for _, y in blk) / len(blk) + 0.5 - H / 2) * 2 if blk else -10.0

if __name__ == '__main__':
    F = frames(); gap = 4
    board = Image.new('RGBA', (len(F) * (W + gap) + gap, H + 2 * gap), (40, 40, 40, 255))
    for i, fr in enumerate(F): board.paste(fr, (gap + i * (W + gap), gap), fr)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(HERE, 'review', 'board.png'))
    print('static constexpr float HAND[5][2][2] = {')
    print('    ' + ', '.join('{{%d, %d}, {%d, %d}}' % (*map(round, hands(f)[0]), *map(round, hands(f)[1])) for f in F) + ' };')
    print('static constexpr float MOUTH_Y = %.1ff;' % mouth(F[4]))
    if '--install' in sys.argv:
        path = os.path.join(ROOT, 'assets/enemies/58_agropelter.png')
        pt.sheet({'down': {'idle': F}}, 'idle', path, W, H, front_only=True)
        print(pt.check_frames(path, 5, W, H, views=(('down', 0),))[0])
