"""Writes 09_questing_beast.txt: Malory's Questing Beast -- "a head like a
serpent's, a body like a leopard's, buttocks like a lion's, and feet like a
hart", its belly full of the noise of barking hounds.

Heads are hand-drawn stamps; body, haunches, tail, neck and legs are shapes."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import blank, put, stamp, ellipse, thick_line, slim_leg, check_legs, write, source_path

W, H = 36, 30
FEET = H - 1
HEAD = {  # 9x5 snake heads, 1x1 black eyes; the tongue is drawn per frame (TONGUE)
    'side':  ['.KKKKK...', 'KGGGGGKK.', 'KGKGGGGGK', 'KgggggKK.', '.KKKKK...'],
    'front': ['..KKKKK..', '.KGGGGGK.', 'KGKGGGKGK', '.KgggggK.', '..KKKKK..'],
    'back':  ['..KKKKK..', '.KGGGGGK.', 'KGHHHHHGK', '.KGGGGGK.', '..KKKKK..'],
}

def beast(cx, cy, rx, ry, lion):
    """Spotted leopard body; where lion(x) holds, plain tawny lion haunches."""
    def colour(x, y, t):
        if lion(x): return 'T' if t < 0.7 else 't'
        if (x * 3 + y * 7) % 9 == 0 or (x * 5 + y * 3) % 13 == 0: return 'D'   # rosettes
        return 'L' if t < 0.25 else 'Y' if t < 0.75 else 'y'
    return ellipse(cx, cy, rx, ry, colour)

def tail(x0, y0, x1, y1, tuft):
    """Lion tail: a thin line ending in a dark tuft."""
    cells = thick_line(x0, y0, x1, y1, 0, 'T')
    cells.update(thick_line(*tuft, tuft[0], tuft[1] + 1, 1, 'D'))
    return cells

def neck(points, r=2):
    cells = {}
    for a, b in zip(points, points[1:]): cells.update(thick_line(*a, *b, r, 'G'))
    for (x, y) in list(cells):
        if (x + y) % 4 == 0: cells[(x, y)] = 'H'      # scales
    return cells

def legs(g, near, far):
    """Hart's legs: slender, hooved. Far legs darker. Drawn before the body."""
    for points, edge in far: slim_leg(g, points, 't', edge, 'h')
    for points, edge in near: slim_leg(g, points, 'T', edge, 'h')

# Idle, per frame: the head bobs, the tongue flicks (in, a short flick, fully
# out and forked) and the lion tail swings; body and legs stay planted.
BOB = (0, -1, 1)
TONGUE = {   # (dx, dy, rows) from the mouth
    'side':  [None, (0, 0, ['RR']), (0, -1, ['..R', 'RR.', '..R'])],   # forward, forking up and down
    'front': [None, (0, 0, ['R']), (-1, 0, ['.R.', '.R.', 'R.R'])],   # down from the mouth, head-on
}
TAIL_TIP = {  # where the tail ends in each frame: rest, swung back/up, swung forward/down
    'side': ((2, 20), (0, 15), (5, 21)),
    'diag': ((4, 19), (2, 14), (7, 20)),
    'back': ((15, 20), (12, 19), (20, 19)),   # from behind it swings side to side
    'front': ((17, 24), (27, 23), (8, 23)),   # head-on it hangs behind: between the legs, then out past each side
}

def head(g, x, y, kind, frame, mouth):
    """Head stamp at (x, y) plus this frame's tongue at mouth (mx, my) from it."""
    stamp(g, x, y, HEAD[kind])
    shape = TONGUE.get(kind, [None] * 3)[frame]
    if shape:
        dx, dy, rows = shape
        stamp(g, x + mouth[0] + dx, y + mouth[1] + dy, rows)

def view_side(kind, frame):
    g = blank(W, H); dy = BOB[frame]
    legs(g, near=[([(9, 19), (7, 24), (8, FEET)], -1), ([(23, 20), (23, FEET)], -1)],
            far=[([(12, 19), (11, 24), (12, FEET)], -1), ([(20, 20), (20, FEET)], -1)])
    tx, ty = TAIL_TIP['side'][frame]
    put(g, {**neck([(23, 15), (27, 10), (28, 6 + dy)]),
            **beast(16, 16, 11, 5, lambda x: x < 14),
            **tail(5, 14, tx, ty, (tx, ty + 1))})
    check_legs(g, FEET, 19)
    head(g, 25, 2 + dy, kind, frame, (8, 3))
    return g

def view_diag(kind, frame):
    """3/4: body angled, lion haunches toward the back-left, head forward-right."""
    g = blank(W, H); dy = BOB[frame]
    legs(g, near=[([(9, 19), (7, 24), (8, FEET)], -1), ([(18, 19), (18, FEET)], -1)],
            far=[([(12, 19), (11, 24), (12, FEET)], -1), ([(20, 19), (21, FEET)], 1)])
    tx, ty = TAIL_TIP['diag'][frame]
    put(g, {**neck([(21, 15), (23, 10), (24, 6 + dy)]),
            **beast(15, 16, 9, 5.5, lambda x: x < 13),
            **tail(7, 13, tx, ty, (tx, ty + 1))})
    check_legs(g, FEET, 19)
    head(g, 20, 2 + dy, 'front' if kind == 'front' else 'back', frame, (4, 5))
    return g

def view_front(kind, frame):
    """Head-on: narrow leopard chest (front) or lion rump with the tail (back)."""
    g = blank(W, H); dy = BOB[frame]
    tx, ty = TAIL_TIP[kind][frame]
    if kind == 'front':   # behind everything: drawn first, root hidden by the body
        put(g, tail(17, 16, tx, ty, (tx, ty + 1)))
    legs(g, near=[([(15, 20), (15, FEET)], -1), ([(20, 20), (20, FEET)], 1)],
            far=[([(13, 20), (12, FEET)], -1), ([(22, 20), (23, FEET)], 1)])
    body = beast(17.5, 16, 6, 5.5, lambda x: kind == 'back')   # chest is leopard, rump is lion
    # thin from the front, so the head reads
    parts = {**neck([(17, 12), (17, 7 + dy)], 1), **neck([(18, 12), (18, 7 + dy)], 1), **body}
    if kind == 'back':
        parts.update(tail(17, 13, tx, ty, (tx, ty + 1)))
    put(g, parts)
    check_legs(g, FEET, 19)
    head(g, 13, 2 + dy, kind, frame, (4, 5))
    return g

def main():
    V = {}
    for suffix, frame in (('', 0), ('@1', 1), ('@2', 2)):
        V.update({'R' + suffix: view_side('side', frame), 'DR' + suffix: view_diag('front', frame),
                  'UR' + suffix: view_diag('back', frame), 'D' + suffix: view_front('front', frame),
                  'U' + suffix: view_front('back', frame)})
    pal = {'K': '000000', 'Y': 'd89830', 'L': 'f4ce80', 'y': '967448', 'D': '3c2412',
           'T': 'c18a39', 't': '876a1f', 'h': '463422', 'G': '29633e', 'g': '4fa667',
           'H': '14301f', 'R': 'b70000'}
    write(source_path(__file__), pal, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
