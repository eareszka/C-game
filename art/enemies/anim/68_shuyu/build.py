"""Shuyu's animation (Two-mode: plucks the air with its heads in phase 1; flaps, hopping short flights, in phase 2).
From its approved 50x41 frames: idle (rest, left pair jab, right pair jab) and the wingbeat (up, out, down, out).
Four views: down, right, up; left = right mirrored.
  idle: rest, JAB front-left/back-right (frame 1), rest, JAB front-right/back-left (frame 3), rest   5 x 260 ms
        (Shuyu::on_idle_frame fires on 1 and 3: the old 1.3 s loop, both jabs kept)
  flap: PixelLab's wingbeat (the user: "use pixellab to animate"), pixellab/shuyu-VIEW-0N.png from its
        flap frame 0, 4 frames a view; used as a ping-pong loop -- up (00), mid (01), down (02), mid (01) --
        because frames 03-04 fold the wings shut (and go wrong in the side view). Colours snapped to its own
        palette. 260 ms a pose on the ground, 130 ms in the air (the user: faster only when airborne).
Run: python -B art/enemies/anim/68_shuyu/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W, H = 50, 41
DIRS = {'down': 0, 'right': 2, 'up': 4}

def cell(im, i): return im.crop((i * W, 0, i * W + W, H)).convert('RGBA')

def palette():
    a = Image.open(os.path.join(HERE, 'original_idle.png')).convert('RGBA')
    r = Image.open(os.path.join(HERE, 'original_flap.png')).convert('RGBA')
    return sorted({p for im in (a, r) for p in im.getdata() if p[3] == 255})

def snap(im, pal):
    """PixelLab's colours to the nearest of the sprite's own; half-clear pixels clear."""
    out = im.convert('RGBA').copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            p = px[x, y]
            if p[3] < 128: px[x, y] = (0, 0, 0, 0); continue
            px[x, y] = min(pal, key=lambda q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 + (q[2] - p[2]) ** 2)
    return out

def poses():
    a = Image.open(os.path.join(HERE, 'original_idle.png'))
    pal = palette(); P = {}
    for v, d in DIRS.items():
        f = [cell(a, d * 3 + i) for i in range(3)]
        g = [snap(Image.open(os.path.join(HERE, 'pixellab', 'shuyu-%s-%02d.png' % (v, i))), pal) for i in range(3)]
        P[v] = {'idle': [f[0], f[1], f[0], f[2], f[0]], 'flap': [g[0], g[1], g[2], g[1]]}
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
    for r, v in enumerate(DIRS):
        for c, fr in enumerate(P[v]['idle'] + P[v]['flap']): board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def install():
    P = poses(); d = os.path.join(ROOT, 'assets/enemies/redraws')
    sheet(P, 'idle', os.path.join(d, '68_shuyu.png')); sheet(P, 'flap', os.path.join(d, '68_shuyu_flap.png'))

if __name__ == '__main__':
    if '--install' in sys.argv: install()
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
