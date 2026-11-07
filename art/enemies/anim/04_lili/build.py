"""Lili's animation (Walker: scuttles in both phases, stops only to pinch).
From its approved 28x22 frames (3 a view: legs one way, under, the other way).
Views down, right, up (left = right mirrored); 8 columns kept, the code only faces D R U L.
  scuttle: legs one way, under, other way, under      260 ms a step (Lili::anim_frame)
  pinch:   braced, legs splayed both ways, ears turned in -- held while it pinches (sheet frame 3)
Run: python -B art/enemies/anim/04_lili/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W, H = 28, 22
CLEAR = (0, 0, 0, 0)
DIRS = {'down': 0, 'right': 2, 'up': 4}
# Ears on a standing frame: (row, first col, last col, dx) -- tips turned in.
CLAWS = {'down': [(2, 8, 8, 2), (3, 7, 9, 2), (4, 7, 11, 1), (2, 19, 19, -2), (3, 18, 20, -2), (4, 16, 20, -1)],
         'right': [(2, 16, 16, 2), (3, 15, 17, 2), (4, 15, 18, 1)]}
CLAWS['up'] = CLAWS['down']

def cell(im, i):
    c = im.crop((i * W, 0, i * W + W, H)).convert('RGBA')
    return [[c.getpixel((x, y)) for x in range(W)] for y in range(H)]

def pinch(g, view):
    out = [list(r) for r in g]
    moves = []
    for r, a, b, dx in CLAWS[view]:
        for x in range(a, b + 1):
            moves.append((r, x + dx, g[r][x])); out[r][x] = CLEAR
    for r, x, p in moves:
        if p[3]: out[r][x] = p
    return out

def poses():
    im = Image.open(os.path.join(HERE, 'original.png'))
    P = {}
    for v, d in DIRS.items():
        f = [cell(im, d * 3 + i) for i in range(3)]
        # Braced: front and back views take the left legs of one stride and the right
        # legs of the other (body rows match); the side's first stride is already splayed.
        brace = [f[2][y][:W // 2] + f[0][y][W // 2:] for y in range(H)] if v != 'right' else f[0]
        P[v] = f + [pinch(brace, v)]
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
    board = Image.new('RGBA', ((W + gap) * 4 + gap, (H + gap) * 3 + gap), (40, 40, 40, 255))
    for r, v in enumerate(ORDER):
        for c in range(4):
            fr = to_img(P[v][c]); board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board.resize((board.width * 8, board.height * 8), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def write_sheets(assets):
    P = poses()
    def view(dn):
        if dn == 'D': return P['down']
        if dn == 'U': return P['up']
        return P['right'] if dn in ('DR', 'R', 'UR') else [mirror(g) for g in P['right']]
    im = Image.new('RGBA', (W * 8 * 4, H))
    for d, dn in enumerate(['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']):
        for f, g in enumerate(view(dn)):
            fr = to_img(g); im.paste(fr, ((d * 4 + f) * W, 0))
    im.save(os.path.join(assets, '04_lili.png'))

if __name__ == '__main__':
    if '--install' in sys.argv: write_sheets(os.path.join(ROOT, 'assets/enemies'))
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
