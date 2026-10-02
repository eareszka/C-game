"""Writes 07_alber.txt: the Alber, a great fiery dragon "glowing like an
electric fire", in flight -- wings flapping, body hovering, flames flickering.

Heads are hand-drawn stamps; body, wings, legs and flames are shapes."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import blank, put, stamp, thick_line, tube, bat_wing, top_of, write, source_path

W, H = 40, 40
HEAD = {  # 10x7: horns, 1x1 black eyes (the side one under a scowling brow), fangs
    'side':  ['..KK......', '.KRRKKKK..', 'KRRRKKOOKK', 'KOOOKOOOOK', 'KOOOOOKKKK', '.KOOKWKWK.', '..KKKKKK..'],
    'front': ['KK......KK', 'KRK....KRK', '.KRKKKKRK.', '.KOKOOKOK.', '.KOOOOOOK.', '..KWKKWK..', '...KKKK...'],
    'back':  ['KK......KK', 'KRK....KRK', '.KRKKKKRK.', '.KROOOORK.', '.KRROORRK.', '..KRRRRK..', '...KKKK...'],
}
HOVER = (4, 3, 5)           # body offset per frame (2 down leaves room for the raised wings)
FLAP = ((0, 0), (0, -3), (1, 4))   # wing-tip offset per frame: rest, up, down

# How much of the glowing belly a view shows: all of it from the front, the
# lower half from the side, none from behind (just the dark-red back).
SHOW = {'front': 'full', 'side': 'belly', 'back': 'none'}

def colour(show, d, below):
    """d: distance from the body's centre line; below: on the belly side of it."""
    glow = 'Y' if d < 1.2 else 'O' if d < 2.3 else 'R'
    if show == 'full' or (show == 'belly' and below): return glow
    return 'D' if d < 1.0 else 'R'

def dragon_body(points, radii, show):
    return tube(points, radii, lambda d, below: colour(show, d, below))

def draw_wing(g, shoulder, wrist, tips, trail, frame, dark=False, mirror=False):
    fx, fy = FLAP[frame]
    bat_wing(g, shoulder, wrist, tips, trail, 'D' if dark else 'R', 'O', (-fx if mirror else fx, fy))

def flames(g, body, xs, frame):
    """Flickering flame tips along the top of the body, unoutlined so they glow."""
    for x in xs:
        t = top_of(body, x)
        if t is None: continue
        h = (x * 5 + frame * 7) % 3 + 1
        for i in range(h):
            if 0 <= t - 1 - i: g[t - 1 - i][x] = 'Y' if i == h - 1 else 'O'

def legs(g, hips, dy):
    for hx, hy in hips:
        put(g, thick_line(hx, hy + dy, hx + 1, hy + 3 + dy, 1, 'R'))

def view_side(kind, frame):
    g = blank(W, H); dy = HOVER[frame]
    path = [(2, 31), (7, 30), (11, 27), (15, 24), (20, 22), (25, 20), (28, 16), (29, 11)]
    path = [(x, y + dy) for x, y in path]
    draw_wing(g, (22, 19 + dy), (28, 6 + dy), [(34, 1 + dy), (38, 7 + dy), (37, 14 + dy)], (26, 18 + dy), frame, dark=True)   # far wing
    body = dragon_body(path, (1, 2, 3, 4, 4, 3, 2), 'none' if kind == 'back' else 'belly')
    legs(g, [(16, 26), (22, 24)], dy)
    put(g, body)
    flames(g, body, range(6, 28, 2), frame)
    draw_wing(g, (18, 21 + dy), (12, 8 + dy), [(4, 2 + dy), (1, 10 + dy), (4, 17 + dy)], (12, 21 + dy), frame)   # near wing
    stamp(g, 25, 4 + dy, HEAD[kind])
    return g

def view_front(kind, frame):
    g = blank(W, H); dy = HOVER[frame]
    tail = dragon_body([(19, 22 + dy), (22, 28 + dy), (26, 31 + dy), (30, 32 + dy)], (4, 2, 1), SHOW[kind])
    put(g, tail)
    left = ((16, 14), (9, 4), [(2, 1), (0, 8), (3, 15)], (14, 19))
    for mirror in (False, True):
        m = (lambda p: (39 - p[0], p[1] + dy)) if mirror else (lambda p: (p[0], p[1] + dy))
        s, w, tips, tr = left
        draw_wing(g, m(s), m(w), [m(p) for p in tips], m(tr), frame, mirror=mirror)
    legs(g, [(14, 22), (23, 22)], dy)
    body = dragon_body([(19, 8 + dy), (19, 13 + dy), (19, 20 + dy)], (3, 5), SHOW[kind])
    put(g, body)
    if kind == 'back': flames(g, body, range(16, 24), frame)
    stamp(g, 15, 2 + dy, HEAD[kind])
    return g

def view_diag(kind, frame):
    """3/4 view, facing up or down and to the right: wings spread to both
    sides -- the near one full, the far one foreshortened. From the front the
    wings are behind the body; from behind they are drawn over its back."""
    g = blank(W, H); dy = HOVER[frame]
    m = lambda p: (p[0], p[1] + dy)
    show = 'none' if kind == 'back' else 'belly'   # 3/4 front shows half the glow, like the side
    near = ((16, 14), (9, 4), [(2, 1), (0, 8), (3, 15)], (14, 19))
    far = ((24, 14), (30, 6), [(35, 2), (38, 8), (36, 13)], (26, 18))
    def wings():
        for s, w, tips, tr in (far, near):
            draw_wing(g, m(s), m(w), [m(p) for p in tips], m(tr), frame)
    if kind != 'back': wings()
    put(g, dragon_body([m(p) for p in ((4, 32), (9, 30), (14, 26), (19, 20))], (1, 2, 4), show))
    legs(g, [(15, 23), (21, 22)], dy)
    body = dragon_body([m(p) for p in ((17, 23), (20, 16), (23, 10))], (5, 3), show)
    put(g, body)
    if kind == 'back':
        flames(g, body, range(16, 25), frame)
        wings()
    stamp(g, 19, 3 + dy, HEAD[kind])
    return g

def main():
    V = {}
    for suffix, frame in (('', 0), ('@1', 1), ('@2', 2)):
        V.update({'R' + suffix: view_side('side', frame), 'DR' + suffix: view_diag('front', frame),
                  'UR' + suffix: view_diag('back', frame), 'D' + suffix: view_front('front', frame),
                  'U' + suffix: view_front('back', frame)})
    pal = {'K': '000000', 'D': '7c0a1b', 'R': 'b70000', 'O': 'fc9838', 'Y': 'fae488',
           'W': 'fcfcfc', 'E': '84a7e9'}
    write(source_path(__file__), pal, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
