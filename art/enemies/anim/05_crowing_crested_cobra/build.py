"""Crowing Crested Cobra's animation (Two-mode: coiled in phase 1, slithers after the player in phase 2).
From its approved 26x24 frames: coiled idle (3 a view) and slither (4 a view).
Views down, right, up (left = right mirrored).
  coiled idle: rest, rear up, tail-tip curl, low            260 ms each
  attack:      the hiss -- reared, mouth open (spray and crow, phase 1)
  phase 2:     uncoil (hiss, first slither pose; it holds still) then the slither wave, 260 ms a pose
Run: python -B art/enemies/anim/05_crowing_crested_cobra/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W, H = 26, 24
PAL = {'.': (0, 0, 0, 0), 'a': (0, 0, 0, 255), 'b': (183, 0, 0, 255), 'c': (208, 192, 120, 255),
       'd': (236, 132, 118, 255), 'e': (150, 116, 72, 255), 'f': (232, 224, 192, 255)}
INV = {v: k for k, v in PAL.items()}
DIRS = {'down': 0, 'right': 2, 'up': 4}

def rows_of(im, i):
    c = im.crop((i * W, 0, i * W + W, H)).convert('RGBA')
    return [''.join(INV.get(c.getpixel((x, y)), '?') if c.getpixel((x, y))[3] else '.' for x in range(W)) for y in range(H)]

def put(row, col, s): return row[:col] + s + row[col + len(s):]

def tail_curl(f0, f2):
    """f0 with the tail tip (rows 0-14, cols 0-5) taken from the low pose: curled in."""
    return [f2[y][:6] + f0[y][6:] if y < 15 else f0[y] for y in range(H)]

def hiss(f1, view):
    r = list(f1)
    if view == 'down':
        r[6] = put(r[6], 9, 'acddddca'); r[7] = put(r[7], 10, 'adddda')
    elif view == 'right':
        r[7] = put(r[7], 14, 'affaddddda'); r[8] = put(r[8], 14, 'afbbaaaaa')
    else:   # from behind: the neck stretched a pixel more
        r = r[1:10] + [r[9]] + r[10:]
    return r

def poses():
    idle = Image.open(os.path.join(HERE, 'original_idle.png'))
    sl = Image.open(os.path.join(HERE, 'original_slither.png'))
    P = {}
    for v, d in DIRS.items():
        f = [rows_of(idle, d * 3 + i) for i in range(3)]
        s = [rows_of(sl, d * 4 + i) for i in range(4)]
        P[v] = {'idle': [f[0], f[1], tail_curl(f[0], f[2]), f[2]], 'attack': [hiss(f[1], v)],
                'move': [hiss(f[1], v)] + s}           # flap sheet: uncoil hiss, then the 4-pose wave
    return P

def to_img(rows):
    im = Image.new('RGBA', (W, H))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r): im.putpixel((x, y), PAL[ch])
    return im

def mirror(rows): return [r[::-1] for r in rows]
ORDER = ['down', 'right', 'up']

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    P = poses(); gap = 4
    cols = [('idle', i) for i in range(4)] + [('attack', 0)] + [('move', i) for i in range(1, 5)]
    board = Image.new('RGBA', ((W + gap) * len(cols) + gap, (H + gap) * 3 + gap), (40, 40, 40, 255))
    for r, v in enumerate(ORDER):
        for c, (k, i) in enumerate(cols):
            fr = to_img(P[v][k][i]); board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board.resize((board.width * 6, board.height * 6), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def write_sheets(assets):
    P = poses()
    def view(dn, k):
        if dn == 'D': return P['down'][k]
        if dn == 'U': return P['up'][k]
        return P['right'][k] if dn in ('DR', 'R', 'UR') else [mirror(g) for g in P['right'][k]]
    for k, n, path in (('idle', 4, '05_crowing_crested_cobra.png'), ('attack', 4, '05_crowing_crested_cobra_hiss.png'),
                       ('move', 5, '05_crowing_crested_cobra_slither.png')):
        im = Image.new('RGBA', (W * 8 * n, H))
        for d, dn in enumerate(['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']):
            seq = view(dn, k)
            for f in range(n):
                fr = to_img(seq[f % len(seq)]); im.paste(fr, ((d * n + f) * W, 0))
        im.save(os.path.join(assets, path))

if __name__ == '__main__':
    if '--install' in sys.argv: write_sheets(os.path.join(ROOT, 'assets/enemies'))
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
