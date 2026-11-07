"""Snawfus's animation (redone 2026-11-06 by the user: phase 1 gallops across the screen, fast or slow;
phase 2 stands, volleys massive shots, gallops to its next spot). All PixelLab:
  views: right = its approved NES sprite (3/4, on a 44x44 canvas); down = PixelLab rotate's south,
         up = its north (pixellab/snawfus-south-00.png, snawfus-north-04.png); left = right mirrored
  idle   (4 x 260 ms): pixellab/idle-VIEW-00..03   -- breathing, head dipping, blossoms swaying
  gallop (flap sheet): pixellab/gallop2-VIEW-01..04 -- a big exaggerated gallop (the user: "less subtle and
         quicker"; the first try, gallop-*, was too subtle); 130 ms a pose fast, 260 slow (phase 1 only)
  volley (alt sheet):  pixellab/volley-VIEW-02     -- reared up, forelegs high (held as it volleys)
Colours snapped to the sprite's own palette.
Run: python -B art/enemies/anim/08_snawfus/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W = H = 44
VIEWS = ('down', 'right', 'up')

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

def poses():
    pal = palette(); L = lambda n: snap(Image.open(os.path.join(HERE, 'pixellab', n)), pal)
    P = {}
    for v in VIEWS:
        P[v] = {'idle': [L('idle-%s-%02d.png' % (v, i)) for i in range(4)],
                'gallop': [L('gallop2-%s-%02d.png' % (v, i)) for i in range(1, 5)],
                'volley': [L('volley-%s-02.png' % v)] * 4}
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
    board = Image.new('RGBA', (9 * (W + gap) + gap, 3 * (H + gap) + gap), (40, 40, 40, 255))
    for r, v in enumerate(VIEWS):
        for c, fr in enumerate(P[v]['idle'] + P[v]['gallop'] + P[v]['volley'][:1]): board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def install():
    P = poses(); d = os.path.join(ROOT, 'assets/enemies')
    sheet(P, 'idle', os.path.join(d, '08_snawfus.png'))
    sheet(P, 'gallop', os.path.join(d, '08_snawfus_gallop.png'))
    sheet(P, 'volley', os.path.join(d, '08_snawfus_volley.png'))

if __name__ == '__main__':
    if '--install' in sys.argv: install()
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
