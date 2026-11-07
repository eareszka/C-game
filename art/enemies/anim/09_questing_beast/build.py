"""Questing Beast's animation (Two-mode: gallops side to side in phase 1; phase 2 trots back to the middle,
stands and throws its coat's spots). All PixelLab:
  views: down = its approved NES sprite (front, on a 44x44 canvas); right = PixelLab rotate's east, up = its
         north (pixellab/qb-east-02.png, qb-north-04.png); left = right mirrored
  idle   (4 x 260 ms): pixellab/idle-VIEW-00..03   -- snake neck swaying, tongue flicking
  gallop (flap sheet), 8 frames a direction, made CHAOTIC (the user: "the walking/sprinting animation should
         be more chaotic"): each pose taken from a different PixelLab set (gallop-, walk-, chaos-) and jolted
         a pixel or two up/down/sideways, so no two poses in a row look alike --
         0-3 the sprint (130 ms a pose), 4-7 the walk (260 ms). Before that: 0-3 and 4-7 both its regular WALK (the user rejected the
         leopard dash below: "looks wrong just have it walk regularly"; the dash plays the walk at 130 ms a
         pose, the slow walk at 260). History: 0-3 were the DASH on all fours (the user: "when dashing it should go
         towards player and be on all 4's") -- pixellab/dashside-00..03, animated from a PixelLab edit of the
         sprite into a low four-legged leopard run (dashpose_from_front.png, mirrored to face right); side
         view in EVERY column, the code faces it left or right; 130 ms a pose. (The first gallop,
         gallop-VIEW-*, kept the upright many-legged body.) 4-7 pixellab/walk-VIEW-01..04 -- the slow
         walk it throws spots on (phase 2 after the user's phase swap), 260 ms a pose
  throw  (alt sheet):  the braced shake, neck thrown back -- one 260 ms step a spot volley
Colours snapped to the sprite's own palette.
Run: python -B art/enemies/anim/09_questing_beast/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W = H = 44
VIEWS = ('down', 'right', 'up')
THROW = {'down': 3, 'right': 2, 'up': 3}

def palette():
    s = Image.open(os.path.join(HERE, 'original_sprite.png')).convert('RGBA')
    return sorted({s.getpixel((x, y)) for x in range(s.width) for y in range(s.height) if s.getpixel((x, y))[3] == 255})

def snap(im, pal):
    out = im.convert('RGBA').copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            p = px[x, y]
            if p[3] < 128: px[x, y] = (0, 0, 0, 0); continue
            px[x, y] = min(pal, key=lambda q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 + (q[2] - p[2]) ** 2)
    return out

# (file, dx, dy): a pose and how far it is jolted (px; dy negative = up).
SPRINT = [('gallop-%s-02.png', 0, -2), ('chaos-%s-03.png', -1, 0), ('gallop-%s-03.png', 1, -1), ('chaos-%s-04.png', 0, 1)]
WALK   = [('walk-%s-01.png', 0, 0), ('chaos-%s-01.png', 1, -1), ('walk-%s-03.png', -1, 0), ('chaos-%s-02.png', 0, -1)]

def jolt(im, dx, dy):
    out = Image.new('RGBA', im.size, (0, 0, 0, 0)); out.paste(im, (dx, dy), im); return out

def poses():
    pal = palette(); L = lambda n: snap(Image.open(os.path.join(HERE, 'pixellab', n)), pal)
    P = {}
    for v in VIEWS:
        P[v] = {'idle': [L('idle-%s-%02d.png' % (v, i)) for i in range(4)],
                'gallop': [jolt(L(n % v), dx, dy) for n, dx, dy in SPRINT + WALK],
                'volley': [L('throw-%s-%02d.png' % (v, THROW[v]))] * 4}
    return P

def mirror(im): return im.transpose(Image.FLIP_LEFT_RIGHT)

def sheet(P, k, path):
    n = len(P['down'][k]); im = Image.new('RGBA', (W * 8 * n, H))
    for d, dn in enumerate(['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']):
        seq = P['down'][k] if dn == 'D' else P['up'][k] if dn == 'U' else P['right'][k] if dn in ('DR', 'R', 'UR') else [mirror(x) for x in P['right'][k]]
        for i, fr in enumerate(seq): im.paste(fr, ((d * n + i) * W, 0))
    im.save(path)

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    P = poses(); gap = 4
    board = Image.new('RGBA', (13 * (W + gap) + gap, 3 * (H + gap) + gap), (40, 40, 40, 255))
    for r, v in enumerate(VIEWS):
        for c, fr in enumerate(P[v]['idle'] + P[v]['gallop'] + P[v]['volley'][:1]): board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def install():
    P = poses(); d = os.path.join(ROOT, 'assets/enemies')
    sheet(P, 'idle', os.path.join(d, '09_questing_beast.png'))
    sheet(P, 'gallop', os.path.join(d, '09_questing_beast_gallop.png'))
    sheet(P, 'volley', os.path.join(d, '09_questing_beast_throw.png'))

if __name__ == '__main__':
    if '--install' in sys.argv: install()
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
