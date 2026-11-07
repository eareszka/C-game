"""Ofuguggi's animation (always swimming, TAIL FIRST -- the user: "swims backwards"). PixelLab, 48x48.
Drawn upright like the other fish: front = its approved NES sprite, side = rotate's east-02, back = north-04.
Tail first: the sheet's columns hold the view facing AWAY from the way it moves --
  moving down (toward the player): its BACK;  moving up: its FRONT;
  moving right: the side view facing LEFT (east mirrored);  moving left: east as drawn.
Ofuguggi::move_facing returns the way it moves; the reversal lives here.
  swim sheet (flap, always on), 6 a direction: 0-3 the swim (pixellab/swim-VIEW-01..04: tail beating, body
        rippling) -- 260 ms a pose, 160 in phase 2 (it swims 1.6x faster); 4 the fins FLARED (the reverse-fin
        fans, a step); 5 the belly SWOLLEN (the swell orb, a step)
  idle sheet: the swim's poses (5 frames, 1.3 s -- only its clock matters: the fans leave on frame 1)
Run: python -B art/enemies/anim/15_ofuguggi/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
W = H = 48
FLARE = {'front': 2, 'side': 2, 'back': 2}
SWELL = {'front': 3, 'side': 3, 'back': 3}

def poses():
    pal = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    L = lambda n: pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', n)), pal))
    V = {}
    for v in ('front', 'side', 'back'):
        swim = [L('swim-%s-%02d.png' % (v, i)) for i in range(1, 5)]
        V[v] = {'flap': swim + [L('flare-%s-%02d.png' % (v, FLARE[v])), L('swell-%s-%02d.png' % (v, SWELL[v]))],
                'idle': swim + [swim[0]]}
    side_left = {k: [pt.mirror(f) for f in fr] for k, fr in V['side'].items()}   # facing left
    return {'down': V['back'], 'up': V['front'], 'right': side_left}            # tail first

if __name__ == '__main__':
    P = poses(); gap = 4
    board = Image.new('RGBA', (6 * (W + gap) + gap, 3 * (H + gap) + gap), (40, 40, 40, 255))
    for r, v in enumerate(('down', 'right', 'up')):
        for c, fr in enumerate(P[v]['flap']): board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(HERE, 'review', 'board.png'))
    if '--install' in sys.argv:
        d = os.path.join(ROOT, 'assets/enemies')
        pt.sheet(P, 'idle', os.path.join(d, '15_ofuguggi.png'), W, H)
        pt.sheet(P, 'flap', os.path.join(d, '15_ofuguggi_swim.png'), W, H)
        print('\n'.join(pt.check_frames(os.path.join(d, '15_ofuguggi_swim.png'), 6, W, H)))
