"""Mahwot's animation (side view only, the left mirrored -- the user's design; it swims fast back and forth, rears and
roars atomic breath at each end). PixelLab from its approved 44x20 NES sprite on a 60x40 canvas.
  idle (the swim, 4 x 105 ms -- its old pace, the user: "the speed at which it moved before was better"): swim-01..04
  alt  (the roar, held through the breath): roar-03 only -- reared, jaws wide; one pose so the mouth stays on the beam
  flap (the CLOSE, 4): roar-03, -02, -01, -00 -- jaws closing back down to swimming, played slowly across the
        cooldown after its breath (the user: "need slow animation of it closing mouth after firing before going back
        to swimming"); Mahwot::flap_phase maps the cooldown's progress onto them
  MOUTH: the middle of the open mouth on roar-03, printed for Mahwot (the beam leaves it; facing left mirrored).
Run: python -B art/enemies/anim/72_mahwot/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
W, H = 60, 40
def frames():
    pal = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    pal += [(252, 116, 180, 255)]   # its open mouth's pink: the game palette's (PixelLab's pinks were off it)
    L = lambda n: pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', n)), pal))
    return [L('swim-%02d.png' % i) for i in range(1, 5)], [L('roar-03.png')] * 4   # one held roar pose: the beam leaves its mouth exactly (the user)
def mouth(fr):
    px = fr.load(); pts = [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][0] > 200 and px[x, y][2] > 120 and px[x, y][1] < 140]
    if not pts: pts = [(x, y) for y in range(H) for x in range(W // 2, W) if px[x, y] == pt.BLACK]
    return sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)
if __name__ == '__main__':
    swim, roar = frames(); gap = 4
    board = Image.new('RGBA', (8 * (W + gap) + gap, H + 2 * gap), (40, 40, 40, 255))
    for i, fr in enumerate(swim + roar): board.paste(fr, (gap + i * (W + gap), gap), fr)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(HERE, 'review', 'board.png'))
    mx, my = mouth(roar[1])
    print('mouth (frame px): %.1f, %.1f -> screen offset facing right %.1f, %.1f' % (mx, my, (mx + 0.5 - W / 2) * 2, (my + 0.5 - H / 2) * 2))
    if '--install' in sys.argv:
        pal = pt.palette_of(os.path.join(HERE, 'original_sprite.png')) + [(252, 116, 180, 255)]
        close = [pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', 'roar-%02d.png' % i)), pal)) for i in (3, 2, 1, 0)]
        side = {'idle': swim, 'alt': roar, 'flap': close}; P = {'down': side, 'up': side, 'right': side}
        d = os.path.join(ROOT, 'assets/enemies')
        pt.sheet(P, 'idle', os.path.join(d, '72_mahwot.png'), W, H)
        pt.sheet(P, 'alt', os.path.join(d, '72_mahwot_roar.png'), W, H)
        pt.sheet(P, 'flap', os.path.join(d, '72_mahwot_close.png'), W, H)
        for name in ('72_mahwot.png', '72_mahwot_roar.png'):
            print(name, pt.check_frames(os.path.join(d, name), 4, W, H, views=(('right', 2),))[0])
