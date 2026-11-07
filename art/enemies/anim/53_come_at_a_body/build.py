"""Come-at-a-body's animation (Two-mode: lurks/stands, then rushes and flees at a gallop).
From its approved 42x29 frames: idle (rest, spit, spit fading) and the dash (4).
Views down, right, up (left = right mirrored).
  idle: rest, stretch, rest, squash, rest -- 5 at 260 ms = 1.3 s, the old loop, so the spit
        (it leaves when the idle turns to frame 1) keeps its timing
  spit (alt, laid out by idle frame): the spit pose on frame 1, the fading spit after -- shown
        only for the two steps after it really spits
  dash: the gallop, 4 poses; 260 ms each rushing, 390 ms fleeing (it flees slower)
Run: python -B art/enemies/anim/53_come_at_a_body/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W, H = 42, 29
CLEAR = (0, 0, 0, 0)
DIRS = {'down': 0, 'right': 2, 'up': 4}

def cell(im, i):
    c = im.crop((i * W, 0, i * W + W, H)).convert('RGBA')
    return [[c.getpixel((x, y)) for x in range(W)] for y in range(H)]

def waist(g):
    ys = [y for y in range(H) if any(p[3] for p in g[y])]
    return ys[0] + int((ys[-1] - ys[0]) * 0.6)

def stretch(g, k):
    w = waist(g); rows = [list(r) for r in g]
    if k > 0: rows = rows[k:w] + [rows[w]] * k + rows[w:]          # top half up, the row repeated
    else:     rows = [[CLEAR] * W] * (-k) + rows[:w + k] + rows[w:]  # top half down, rows dropped
    return rows

def poses():
    idle = Image.open(os.path.join(HERE, 'original_idle.png'))
    dash = Image.open(os.path.join(HERE, 'original_dash.png'))
    P = {}
    for v, d in DIRS.items():
        f = [cell(idle, d * 3 + i) for i in range(3)]
        P[v] = {'idle': [f[0], stretch(f[0], 1), f[0], stretch(f[0], -1), f[0]],
                'spit': [f[2], f[1], f[2], f[2], f[2]],
                'dash': [cell(dash, d * 4 + i) for i in range(4)]}
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
    cols = [('idle', i) for i in range(5)] + [('spit', 1), ('spit', 2)] + [('dash', i) for i in range(4)]
    board = Image.new('RGBA', ((W + gap) * len(cols) + gap, (H + gap) * 3 + gap), (40, 40, 40, 255))
    for r, v in enumerate(ORDER):
        for c, (k, i) in enumerate(cols):
            fr = to_img(P[v][k][i]); board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board.resize((board.width * 4, board.height * 4), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def write_sheets(assets):
    P = poses()
    def view(dn, k):
        if dn == 'D': return P['down'][k]
        if dn == 'U': return P['up'][k]
        return P['right'][k] if dn in ('DR', 'R', 'UR') else [mirror(g) for g in P['right'][k]]
    for k, n, path in (('idle', 5, '53_come_at_a_body.png'), ('spit', 5, '53_come_at_a_body_spit.png'), ('dash', 4, '53_come_at_a_body_dash.png')):
        im = Image.new('RGBA', (W * 8 * n, H))
        for d, dn in enumerate(['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']):
            seq = view(dn, k)
            for f in range(n):
                fr = to_img(seq[f]); im.paste(fr, ((d * n + f) * W, 0))
        im.save(os.path.join(assets, path))

if __name__ == '__main__':
    if '--install' in sys.argv: write_sheets(os.path.join(ROOT, 'assets/enemies/redraws'))
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
