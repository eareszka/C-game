"""Treesqueak's animation (Stationary: sits and squeaks in both phases). Built from its
approved 20x19 frames by row edits. Views: down, right, up (left = right mirrored).
Canvas 20x23 (2 px pad top and bottom).
  idle:   rest, stretch, ears perked, squash  (260 ms each)
  attack: the squeak -- ears perked, mouth gaping pink (from behind: ears perked, stretched)
Run: python -B art/enemies/anim/02_treesqueak/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
ORIG = os.path.join(HERE, 'original_20x19.png')
W, H0, H, PAD = 20, 19, 23, 2
WAIST = 13
PAL = {'.': (0, 0, 0, 0), 'a': (0, 0, 0, 255), 'b': (120, 88, 48, 255), 'c': (60, 36, 18, 255),
       'd': (206, 190, 130, 255), 'e': (236, 132, 118, 255), 'f': (252, 252, 252, 255), 'g': (79, 166, 103, 255)}
INV = {v: k for k, v in PAL.items()}

def rows_of(im, cell):
    c = im.crop((cell * W, 0, cell * W + W, H0)).convert('RGBA')
    return [''.join(INV[c.getpixel((x, y))] if c.getpixel((x, y))[3] else '.' for x in range(W)) for y in range(H0)]

# Ears perked: rows 1-2 replaced by three (one taller).
EARS = {'down':  ['.....aa......aa.....', '....abca....acba....', '....abcaaaaaacba....'],
        'up':    ['.....aa......aa.....', '....abca....acba....', '....abcaaaaaacba....'],
        'right': ['.........aa.........', '........abba........', '........abbaaaa.....']}
# The squeak: a row of open mouth put in under `after` (the upper jaw).
MOUTH = {'down': (6, '.......aeeeea.......'), 'right': (5, '.........abbdddaeea.')}

def place(rows):
    """Bottom-anchored on the canvas: the last row on canvas row PAD + H0 - 1."""
    out = ['.' * W] * H
    for i, r in enumerate(reversed(rows)):
        y = PAD + H0 - 1 - i
        if y >= 0: out[y] = r
    return out

def stretch(rows, k):
    return rows[:WAIST] + [rows[WAIST]] * k + rows[WAIST:] if k >= 0 else rows[:WAIST + k] + rows[WAIST:]

def perk(rows, view): return rows[:1] + EARS[view] + rows[3:]

def gape(rows, view):
    if view not in MOUTH: return stretch(perk(rows, view), 0)
    at, row = MOUTH[view]
    return rows[:at + 1] + [row] + rows[at + 1:]

def poses(f0, view):
    return {'idle': [place(f0), place(stretch(f0, 1)), place(perk(stretch(f0, 1), view)), place(stretch(f0, -1))],
            'attack': [place(perk(gape(f0, view), view)) if view in MOUTH else place(perk(stretch(f0, 1), view))]}

def to_img(rows):
    im = Image.new('RGBA', (W, H))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r): im.putpixel((x, y), PAL[ch])
    return im

def mirror(rows): return [r[::-1] for r in rows]

def all_poses():
    im = Image.open(ORIG)
    return {name: poses(rows_of(im, d * 3), name) for name, d in (('down', 0), ('right', 2), ('up', 4))}

ORDER = ['down', 'right', 'up']

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    P = all_poses()
    cols = [('idle', i) for i in range(4)] + [('attack', 0)]
    S, gap = 8, 4
    board = Image.new('RGBA', ((W + gap) * len(cols) + gap, (H + gap) * 3 + gap), (40, 40, 40, 255))
    for r, name in enumerate(ORDER):
        for c, (k, i) in enumerate(cols):
            fr = to_img(P[name][k][i]); board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board.resize((board.width * S, board.height * S), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))
    seq = lambda n: P[n]['idle'] * 2 + P[n]['attack'] + P[n]['idle'] + P[n]['attack'] + P[n]['idle']
    frames = []
    for i in range(len(seq('down'))):
        strip = Image.new('RGBA', (3 * (W + 6) + 2, H + 8), (0, 0, 0, 255))
        for j, n in enumerate(ORDER):
            fr = to_img(seq(n)[i]); strip.paste(fr, (4 + j * (W + 6), 4), fr)
        frames.append(strip.resize((strip.width * 6, strip.height * 6), Image.NEAREST).convert('RGB'))
    frames[0].save(os.path.join(out_dir, 'treesqueak_idle_and_squeak.gif'), save_all=True, append_images=frames[1:], duration=260, loop=0)

def write_sheets(assets):
    """One row, 8 directions D DR R UR U UL L DL x 4 frames; diagonals hold the side view."""
    P = all_poses()
    def view(dn, k):
        if dn == 'D': return P['down'][k]
        if dn == 'U': return P['up'][k]
        return P['right'][k] if dn in ('DR', 'R', 'UR') else [mirror(g) for g in P['right'][k]]
    for k, path in (('idle', '02_treesqueak.png'), ('attack', '02_treesqueak_attack.png')):
        im = Image.new('RGBA', (W * 8 * 4, H))
        for d, dn in enumerate(['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']):
            seq = view(dn, k)
            for f in range(4):
                fr = to_img(seq[f % len(seq)]); im.paste(fr, ((d * 4 + f) * W, 0))
        im.save(os.path.join(assets, path))

if __name__ == '__main__':
    if '--install' in sys.argv: write_sheets(os.path.join(ROOT, 'assets/enemies'))
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
