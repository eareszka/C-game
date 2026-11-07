"""Qique's animation (Two-mode: perched, then flies to a new perch in phase 2).
From its approved 20x20 frames: idle (3 a view) and flap (4 a view: up, out, mid, out).
Views down, right, up (left = right mirrored); canvas stays 20x20.
  idle:   rest, stretch, wing shake (wings out), squash        260 ms each
  attack: the peck -- head dropped, held through a burst
  flight: take-off (wings up), air (wings out), land (wings up)  one step each
Run: python -B art/enemies/anim/03_qique/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W = H = 20
CLEAR = (0, 0, 0, 0)
DIRS = {'down': 0, 'right': 2, 'up': 4}
# The head, cut out for the peck: (rows, cols) and how far it drops.
HEAD = {'down': (range(0, 8), range(5, 15), 2), 'up': (range(0, 8), range(5, 15), 2),
        'right': (range(0, 8), range(10, 20), 2)}

def cell(im, i):
    c = im.crop((i * W, 0, i * W + W, H)).convert('RGBA')
    return [[c.getpixel((x, y)) for x in range(W)] for y in range(H)]

def peck(g, view):
    rows, cols, dy = HEAD[view]
    out = [list(r) for r in g]
    head = {(x, y): g[y][x] for y in rows for x in cols if g[y][x][3]}
    for (x, y) in head: out[y][x] = CLEAR
    # what the head hid: the neck below shows through as the body's outline colour
    for (x, y), p in head.items():
        if y + dy < H: out[y + dy][x] = p
    return out

def poses():
    idle = Image.open(os.path.join(HERE, 'original_idle.png'))
    flap = Image.open(os.path.join(HERE, 'original_flap.png'))
    P = {}
    for v, d in DIRS.items():
        f = [cell(idle, d * 3 + i) for i in range(3)]
        fl = [cell(flap, d * 4 + i) for i in range(4)]
        P[v] = {'idle': [f[0], f[1], fl[1], f[2]], 'attack': [peck(f[0], v)], 'fly': [fl[0], fl[1], fl[0]]}
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
    P = poses()
    cols = [('idle', i) for i in range(4)] + [('attack', 0)] + [('fly', i) for i in range(3)]
    gap = 4
    board = Image.new('RGBA', ((W + gap) * len(cols) + gap, (H + gap) * 3 + gap), (40, 40, 40, 255))
    for r, v in enumerate(ORDER):
        for c, (k, i) in enumerate(cols):
            fr = to_img(P[v][k][i]); board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board.resize((board.width * 8, board.height * 8), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))
    def gif(seq, name, lifts=None):
        frames = []
        n = len(seq('down'))
        for i in range(n):
            strip = Image.new('RGBA', (3 * (W + 6) + 2, H + 14), (0, 0, 0, 255))
            for j, v in enumerate(ORDER):
                fr = to_img(seq(v)[i]); strip.paste(fr, (4 + j * (W + 6), 10 - (lifts[i] if lifts else 0)), fr)
            frames.append(strip.resize((strip.width * 6, strip.height * 6), Image.NEAREST).convert('RGB'))
        frames[0].save(os.path.join(out_dir, name), save_all=True, append_images=frames[1:], duration=260, loop=0)
    gif(lambda v: P[v]['idle'] + P[v]['attack'] * 2 + P[v]['idle'], 'qique_perch_idle_and_peck.gif')
    gif(lambda v: P[v]['idle'][:2] + P[v]['fly'] + P[v]['idle'], 'qique_flight.gif', [0, 0, 4, 8, 0, 0, 0, 0, 0])

def write_sheets(assets):
    """One row, 8 directions D DR R UR U UL L DL; diagonals hold the side view."""
    P = poses()
    def view(dn, k):
        if dn == 'D': return P['down'][k]
        if dn == 'U': return P['up'][k]
        return P['right'][k] if dn in ('DR', 'R', 'UR') else [mirror(g) for g in P['right'][k]]
    for k, n, path in (('idle', 4, '03_qique.png'), ('attack', 4, '03_qique_peck.png'), ('fly', 3, '03_qique_flap.png')):
        im = Image.new('RGBA', (W * 8 * n, H))
        for d, dn in enumerate(['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']):
            seq = view(dn, k)
            for f in range(n):
                fr = to_img(seq[f % len(seq)]); im.paste(fr, ((d * n + f) * W, 0))
        im.save(os.path.join(assets, path))

if __name__ == '__main__':
    if '--install' in sys.argv: write_sheets(os.path.join(ROOT, 'assets/enemies'))
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
