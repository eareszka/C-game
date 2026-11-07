"""Wolpertinger's animation (Two-mode: sits, then hops), the same set as Skvader's. Built from its approved 20x19 frames.
Views: down, right, up (left = right mirrored). Canvas 20x23 (2 px pad top and bottom).
Run: python -B art/enemies/anim/01_wolpertinger/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
ORIG = os.path.join(HERE, 'original_20x19.png')   # the approved 3-frame sheet the poses are cut from
SRC = ORIG
W, H0, H = 20, 19, 23
WAIST = 13   # the row the stretch repeats or drops: the top half moves, the haunches below stay planted
PAD = 2

def grid(im, cell):
    c = im.crop((cell * W, 0, cell * W + W, H0))
    return [[c.getpixel((x, y)) for x in range(W)] for y in range(H0)]

CLEAR = (0, 0, 0, 0)
def blank(h=H0): return [[CLEAR] * W for _ in range(h)]
def body_rows(g):   # rows of f0 that move with the top (above the haunch line, row 11)
    return g

def stretch(f0, k):
    """k>0: top half lifted k rows (row 11 repeated); k<0: dropped (rows above 11 removed into it).
    The bottom (rows 11..16) stays planted. Returns a 17+... grid on the 21 canvas."""
    out = [[CLEAR] * W for _ in range(H)]
    bottom = f0[WAIST:]                   # planted haunches and feet
    top = f0[:WAIST]
    base = PAD + WAIST                    # where the waist row lands on the canvas
    for i, r in enumerate(bottom): out[base + i] = list(r)
    if k >= 0:
        rows = top + [f0[WAIST]] * k      # repeat the waist row
    else:
        rows = top[:k]                    # drop the lowest waist rows of the top
    for i, r in enumerate(reversed(rows)):
        y = base - 1 - i
        if 0 <= y < H: out[y] = list(r)
    return out

def shift_cols(g, cols, dy):
    """Move the pixels in `cols` (wings) by dy rows, above row lim; leaves the rest."""
    out = [list(r) for r in g]
    for x in cols:
        col = [g[y][x] for y in range(H)]
        for y in range(H): out[y][x] = CLEAR
        for y in range(H):
            ny = y + dy
            if 0 <= ny < H and col[y][3]: out[ny][x] = col[y]
    return out

def merge_wings(body, wings, cols, upto):
    """Body pose, with the wing columns above row `upto` taken from another pose."""
    out = [list(r) for r in body]
    for x in cols:
        for y in range(upto):
            out[y][x] = wings[y][x]
    return out

def lift(g, dy):
    out = [[CLEAR] * W for _ in range(H)]
    for y in range(H):
        ny = y - dy
        if 0 <= ny < H: out[ny] = list(g[y])
    return out

def to_img(g):
    im = Image.new('RGBA', (W, H))
    for y in range(H):
        for x in range(W): im.putpixel((x, y), g[y][x])
    return im

def views():
    im = Image.open(SRC).convert('RGBA')
    return {name: grid(im, d * 3) for name, d in (('down', 0), ('right', 2), ('up', 4))}

# The wings, cut from f0 by view: (row, first col, last col) spans. Everything else is body.
def _side(spans): return spans + [(r, 19 - b, 19 - a) for r, a, b in spans]
_DOWN = _side([(3, 0, 3), (4, 0, 4)] + [(r, 0, 5) for r in range(5, 12)])
WING = {
    'down':  _DOWN,
    'up':    _DOWN,
    'right': [(3, 0, 5), (4, 0, 6), (5, 0, 7), (6, 0, 8), (7, 0, 9), (8, 0, 10), (9, 0, 10), (10, 0, 8)],
}

def split(f0, view):
    body = [list(r) for r in f0]; wing = [[CLEAR] * W for _ in range(H0)]
    for r, a, b in WING[view]:
        for x in range(a, b + 1):
            wing[r][x] = f0[r][x]; body[r][x] = CLEAR
    return body, wing

def pose(f0, view, kb, kw, up=0):
    """kb: body stretch (rows the top half rises, negative sinks); kw: how far the wings rise;
    up: the whole thing lifted off the ground (in the air)."""
    body, wing = split(f0, view)
    out = [[CLEAR] * W for _ in range(H)]
    for r in range(H0):                      # wings first, behind the body
        y = PAD + r - kw
        if 0 <= y < H:
            for x in range(W):
                if wing[r][x][3]: out[y][x] = wing[r][x]
    b = stretch(body, kb)
    for y in range(H):
        for x in range(W):
            if b[y][x][3]: out[y][x] = b[y][x]
    return lift(out, up) if up else out

def poses(f0, view):
    P = lambda kb, kw, up=0: pose(f0, view, kb, kw, up)
    return {'idle':   [P(0, 0), P(1, 1), P(1, -1), P(-1, -1)],   # rest, stretch up, wing flick, squash
            'attack': [P(-1, 0)],                                 # head ducked, wings flared: the antler fan
            'hop':    [P(-2, -3), P(2, 2), P(1, 2, 2), P(-2, -2)]}  # crouch, launch, air, land

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    v = views()
    P = {name: poses(g, name) for name, g in v.items()}
    order = ['down', 'right', 'up']
    # Board: rows = views, columns = idle 4 | attack | hop 4.
    cols = [('idle', i) for i in range(4)] + [('attack', 0)] + [('hop', i) for i in range(4)]
    S = 8; gap = 4
    board = Image.new('RGBA', ((W + gap) * len(cols) + gap, (H + gap) * 3 + gap), (40, 40, 40, 255))
    for r, name in enumerate(order):
        for c, (k, i) in enumerate(cols):
            fr = to_img(P[name][k][i]); board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board = board.resize((board.width * S, board.height * S), Image.NEAREST)
    board.save(os.path.join(out_dir, 'board.png'))
    # GIFs at 260 ms, 6x on black (the arena).
    def gif(frames, path):
        ims = []
        for g in frames:
            bg = Image.new('RGBA', (W + 8, H + 8), (0, 0, 0, 255)); fr = to_img(g); bg.paste(fr, (4, 4), fr)
            ims.append(bg.resize((bg.width * 6, bg.height * 6), Image.NEAREST).convert('RGB'))
        ims[0].save(path, save_all=True, append_images=ims[1:], duration=260, loop=0, disposal=2)
    def strip(seq_of):   # all three views side by side, one GIF frame per step
        n = len(seq_of(order[0])); frames = []
        for i in range(n):
            row = [[CLEAR] * 0 for _ in range(H)]
            for name in order:
                g = seq_of(name)[i]
                for y in range(H): row[y] = row[y] + [CLEAR] * 6 + g[y]
            frames.append(row)
        return frames
    def gif_rows(frames, path):
        ims = []
        for g in frames:
            w = len(g[0]); bg = Image.new('RGBA', (w + 8, H + 8), (0, 0, 0, 255))
            fr = Image.new('RGBA', (w, H))
            for y in range(H):
                for x in range(w): fr.putpixel((x, y), g[y][x])
            bg.paste(fr, (2, 4), fr)
            ims.append(bg.resize((bg.width * 6, bg.height * 6), Image.NEAREST).convert('RGB'))
        ims[0].save(path, save_all=True, append_images=ims[1:], duration=260, loop=0, disposal=2)
    gif_rows(strip(lambda n: P[n]['idle'] * 2 + P[n]['attack'] + P[n]['idle']), os.path.join(out_dir, 'wolpertinger_sit_idle_and_attack.gif'))
    gif_rows(strip(lambda n: [P[n]['idle'][0]] * 3 + P[n]['hop'] + P[n]['idle']), os.path.join(out_dir, 'wolpertinger_hop.gif'))
    return P



def mirror(g): return [list(reversed(r)) for r in g]

def write_sheets(assets):
    """The game's sheets, one row, 8 directions D DR R UR U UL L DL x n frames.
    Only 4 views are drawn (the game picks them by quarter, Enemy::four_views); the
    diagonal cells hold the side view, for anything that still reads 8."""
    v = views(); P = {name: poses(g, name) for name, g in v.items()}
    def view(dirname, k):
        side = 'right' if dirname in ('DR', 'R', 'UR') else 'left' if dirname in ('UL', 'L', 'DL') else None
        if dirname == 'D': return P['down'][k]
        if dirname == 'U': return P['up'][k]
        seq = P['right'][k]
        return seq if side == 'right' else [mirror(g) for g in seq]
    DIRS = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
    def sheet(k, n, path):
        im = Image.new('RGBA', (W * 8 * n, H))
        for d, dn in enumerate(DIRS):
            seq = view(dn, k)
            for f in range(n):
                fr = to_img(seq[f % len(seq)]); im.paste(fr, ((d * n + f) * W, 0))
        im.save(path)
    sheet('idle', 4, os.path.join(assets, '01_wolpertinger.png'))
    sheet('attack', 4, os.path.join(assets, '01_wolpertinger_attack.png'))   # the alt sheet: same layout as the idle
    sheet('hop', 4, os.path.join(assets, '01_wolpertinger_hop.png'))         # the flap sheet: crouch, launch, air, land


if __name__ == '__main__':
    # Keep the approved 3-frame original: the source for every pose.
    if not os.path.exists(ORIG):
        Image.open(SRC).save(ORIG)
    if '--install' in sys.argv:
        write_sheets(os.path.join(ROOT, 'assets/enemies'))
    else:
        build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
