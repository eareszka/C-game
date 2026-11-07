"""Mice That Eat Iron's animation (Stationary, front only by the user's design: three mice on one iron beam).
From its approved 28x21 NES sprite on a 28x23 canvas (1 px pad top and bottom).
  idle (4 x 260 ms): rest, then each mouse in turn dips its head a pixel onto the beam -- gnawing out of step
  walk (alt, same 4 frames): the gnaw with the feet stepping -- each mouse's two feet spread, then
         crossed, a pose a step, the outer mice opposite the middle one (shuffling) -- shown while it drifts
  (the old heads-up volley pose is still built, as 65_mice_that_eat_iron_up_unused.png)
The mice are cut as column bands above the beam (rows 0-13); the beam and feet stay put.
Run: python -B art/enemies/anim/65_mice_that_eat_iron/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W, H0, PAD = 28, 21, 1
H = H0 + 2 * PAD
CLEAR = (0, 0, 0, 0)
BEAM = 14                                   # rows from here down: beam, feet
BANDS = {'left': range(0, 10), 'middle': range(10, 18), 'right': range(18, 28)}

def grid():
    s = Image.open(os.path.join(HERE, 'original_sprite.png')).convert('RGBA')
    g = [[CLEAR] * W for _ in range(H)]
    for y in range(H0):
        for x in range(W): g[y + PAD][x] = s.getpixel((x, y))
    return g

def shift(g, cols, dy):
    """Rows above the beam in `cols` moved dy (down +); the beam row keeps its own pixels."""
    out = [list(r) for r in g]
    top, beam = PAD, BEAM + PAD
    for x in cols:
        col = [g[y][x] for y in range(top - PAD, beam)]
        for y in range(top - PAD, beam): out[y][x] = CLEAR
        for i, p in enumerate(col):
            y = top - PAD + i + dy
            if top - PAD <= y < beam and p[3]: out[y][x] = p
        if dy < 0:                                      # lifted: the row above the beam repeats down to it
            for y in range(beam + dy, beam): out[y][x] = g[beam - 1][x]
    return out

# Feet, in sprite rows/cols: (rows, cols of the first foot, cols of the second foot).
FEET = {'left': (range(19, 21), range(2, 6), range(6, 10)), 'right': (range(19, 21), range(18, 22), range(22, 26)),
        'middle': (range(17, 19), range(10, 14), range(14, 18))}

def stride(g, phase):
    """phase 0: feet spread (first a px out to the left, second to the right); 1: crossed (each a px in)."""
    out = [list(r) for r in g]
    for m, (rows, a, b) in FEET.items():
        p = phase if m != 'middle' else 1 - phase          # the middle mouse steps opposite the outer two
        da, db = (-1, 1) if p == 0 else (1, -1)
        cells = []
        for cols, dx in ((a, da), (b, db)):
            for y in rows:
                for x in cols:
                    q = g[y + PAD][x]
                    if q[3]: cells.append((x + dx, y + PAD, q))
                    out[y + PAD][x] = CLEAR
        for x, y, q in cells:
            if 0 <= x < W: out[y][x] = q
    return out

def frames():
    g = grid()
    idle = [g] + [shift(g, BANDS[m], 1) for m in ('left', 'middle', 'right')]
    up = g
    for m in BANDS: up = shift(up, BANDS[m], -1)
    return {'idle': idle, 'walk': [stride(f, i % 2) for i, f in enumerate(idle)], 'up': [up] * 4}

def to_img(g):
    im = Image.new('RGBA', (W, H))
    for y in range(H):
        for x in range(W): im.putpixel((x, y), g[y][x])
    return im

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    F = frames(); seq = F['idle'] + F['walk'] + F['up'][:1]; gap = 4
    board = Image.new('RGBA', (len(seq) * (W + gap) + gap, H + 2 * gap), (40, 40, 40, 255))
    for i, g in enumerate(seq):
        fr = to_img(g); board.paste(fr, (gap + i * (W + gap), gap), fr)
    board.resize((board.width * 8, board.height * 8), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def install():
    F = frames(); d = os.path.join(ROOT, 'assets/enemies/redraws')
    for k, path in (('idle', '65_mice_that_eat_iron.png'), ('walk', '65_mice_that_eat_iron_walk.png'), ('up', '65_mice_that_eat_iron_up_unused.png')):
        im = Image.new('RGBA', (W * 8 * 4, H))
        for dd in range(8):
            for i, g in enumerate(F[k]):
                fr = to_img(g); im.paste(fr, ((dd * 4 + i) * W, 0))
        im.save(os.path.join(d, path))

if __name__ == '__main__':
    if '--install' in sys.argv: install()
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
