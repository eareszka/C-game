"""Teakettler's animation (Two-mode: stands in phase 1, walks backwards, still facing the player, in phase 2).
From its approved 32x29 frames: idle (rest, whistle with a puff, puff trailing) and the backwards trot (4).
Views down, right, up (left = right mirrored).
  idle:   rest, WHISTLE (frame 1: Teakettler::breathe fires on it), puff trailing, rest, squash
          -- 5 poses at 260 ms = 1.3 s, the old loop's length, so the whistle keeps its rate
  attack: the steam snort (alt) -- the puff pose, one step a steam volley
  walk:   the backwards trot, 4 poses at 260 ms
Run: python -B art/enemies/anim/50_teakettler/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W, H = 32, 29
CLEAR = (0, 0, 0, 0)
DIRS = {'down': 0, 'right': 2, 'up': 4}
WAIST = {'down': 20, 'right': 22, 'up': 20}   # the body row the squash drops

def cell(im, i):
    c = im.crop((i * W, 0, i * W + W, H)).convert('RGBA')
    return [[c.getpixel((x, y)) for x in range(W)] for y in range(H)]

def squash(g, v):
    w = WAIST[v]
    return [[CLEAR] * W] + [list(r) for r in g[:w]] + [list(r) for r in g[w + 1:]]

def poses():
    idle = Image.open(os.path.join(HERE, 'original_idle.png'))
    walk = Image.open(os.path.join(HERE, 'original_walk.png'))
    P = {}
    for v, d in DIRS.items():
        f = [cell(idle, d * 3 + i) for i in range(3)]
        P[v] = {'idle': [f[0], f[1], f[2], f[0], squash(f[0], v)], 'attack': [f[1]],
                'walk': [cell(walk, d * 4 + i) for i in range(4)]}
    return P

def to_img(g):
    im = Image.new('RGBA', (W, H))
    for y in range(H):
        for x in range(W): im.putpixel((x, y), g[y][x])
    return im

def mirror(g): return [list(reversed(r)) for r in g]
ORDER = ['down', 'right', 'up']

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    P = poses(); gap = 4
    cols = [('idle', i) for i in range(5)] + [('walk', i) for i in range(4)]
    board = Image.new('RGBA', ((W + gap) * len(cols) + gap, (H + gap) * 3 + gap), (40, 40, 40, 255))
    for r, v in enumerate(ORDER):
        for c, (k, i) in enumerate(cols):
            fr = to_img(P[v][k][i]); board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board.resize((board.width * 5, board.height * 5), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def write_sheets(assets):
    P = poses()
    def view(dn, k):
        if dn == 'D': return P['down'][k]
        if dn == 'U': return P['up'][k]
        return P['right'][k] if dn in ('DR', 'R', 'UR') else [mirror(g) for g in P['right'][k]]
    for k, n, path in (('idle', 5, '50_teakettler.png'), ('attack', 5, '50_teakettler_steam.png'), ('walk', 4, '50_teakettler_walk.png')):
        im = Image.new('RGBA', (W * 8 * n, H))
        for d, dn in enumerate(['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']):
            seq = view(dn, k)
            for f in range(n):
                fr = to_img(seq[f % len(seq)]); im.paste(fr, ((d * n + f) * W, 0))
        im.save(os.path.join(assets, path))

if __name__ == '__main__':
    if '--install' in sys.argv: write_sheets(os.path.join(ROOT, 'assets/enemies/redraws'))
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
