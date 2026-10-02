"""Writes 08_snawfus.txt: the Snawfus, a white Ozark deer with flowering
boughs for antlers, folded owl-feather wings, and spirals of blue smoke.

Heads and blossoms are hand-drawn stamps; body, legs, neck, wing, antler
boughs and smoke are shapes. Body and legs hold still; the head and antlers
bob, the smoke curls drift."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import blank, inside, put, stamp, ellipse, rect, thick_line, polygon, slim_leg, check_legs, write, source_path

W, H = 28, 30
FEET = H - 1
HEAD = {  # 9x6, 1x1 black eyes
    'side':  ['KK.......', 'KSKKKK...', '.KWWWWKK.', '.KWKWWWWK', '..KWWWWKK', '...KKKK..'],
    'front': ['KK.....KK', 'KSKKKKKSK', '.KWWWWWK.', '.KWKWKWK.', '..KWWWK..', '...KKK...'],
    'back':  ['KK.....KK', 'KSKKKKKSK', '.KWWWWWK.', '.KWWWWWK.', '..KWWWK..', '...KKK...'],
}
BLOSSOM = ['.P.', 'PWP', '.P.']
BOB = (0, -1, 1)                     # head and antlers, per frame
SMOKE_SWAY = ((0, 0), (1, -1), (-1, -2))   # smoke curl drift per frame

def body_colour(x, y, t): return 'S' if t > 0.65 else 'W'

def legs(g, view):
    """Drawn before the body, starting inside it, so the body covers their tops."""
    for points, edge in LEGS[view]['far']: slim_leg(g, points, 'S', edge, 's')
    for points, edge in LEGS[view]['near']: slim_leg(g, points, 'W', edge, 's')

# Graceful: one foreleg lifted mid-step (knee forward, hoof tucked back), the
# other three planted, hind legs angled back to the hock. (path of joints, outline side)
LEGS = {
    'side':  {'far':  [([(10, 20), (9, 25), (10, FEET)], -1), ([(14, 21), (14, FEET)], -1)],
              'near': [([(7, 20), (5, 25), (6, FEET)], -1), ([(17, 21), (19, 24), (18, 27)], -1)]},
    'diag':  {'far':  [([(9, 20), (8, 25), (9, FEET)], -1), ([(13, 21), (13, FEET)], -1)],
              'near': [([(6, 20), (4, 25), (5, FEET)], -1), ([(16, 21), (18, 24), (17, 27)], -1)]},
}

def bough(g, points):
    """A thin brown branch, unoutlined, ending in a blossom."""
    for a, b in zip(points, points[1:]):
        for (x, y) in thick_line(*a, *b, 0, 'B'):
            if inside(g, x, y): g[y][x] = 'B'
    tx, ty = points[-1]
    stamp(g, tx - 1, ty - 1, BLOSSOM)

def antlers(g, base_l, base_r, dy):
    """Two flowering boughs, each with a side branch."""
    for (bx, by), s in ((base_l, -1), (base_r, 1)):
        by += dy
        mid = (bx + 2 * s, by - 3)
        bough(g, [(bx, by), mid, (bx + 4 * s, by - 5)])
        bough(g, [mid, (bx + 1 * s, by - 6)])

def wing(points):
    """A folded owl wing: grey with darker feather rows."""
    cells = polygon(points, 'S')
    for (x, y) in cells:
        if (y + x // 2) % 3 == 0: cells[(x, y)] = 's'
    return cells

def smoke(g, roots, frame):
    """Blue curls rising from the back -- connected lines, so no loose pixels."""
    sx, sy = SMOKE_SWAY[frame]
    curl = [(0, 0), (-1, -1), (-1, -2), (0, -3), (1, -4), (1, -5), (0, -6)]
    for rx, ry in roots:
        pts = [(rx + dx + (sx if i > 2 else 0), ry + dy + (sy if i > 2 else 0)) for i, (dx, dy) in enumerate(curl)]
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            for (x, y) in thick_line(*a, *b, 0, 'E'):
                if inside(g, x, y) and g[y][x] == '.': g[y][x] = 'e' if i >= 4 else 'E'

def view_side(kind, frame):
    g = blank(W, H); dy = BOB[frame]
    legs(g, 'side')
    neck = thick_line(17, 16, 21, 11 + dy, 2, 'W')
    body = ellipse(12, 18, 8, 5, body_colour)
    put(g, {**neck, **body, **rect(5, 13, 7, 15, 'W')})          # neck, body and tail outlined as one
    put(g, wing([(8, 15), (15, 14), (17, 17), (13, 19), (7, 19)]))
    check_legs(g, FEET, 19)
    smoke(g, [(9, 12)], frame)
    antlers(g, (21, 7), (24, 7), dy)
    stamp(g, 19, 7 + dy, HEAD['side'])
    return g

def view_diag(kind, frame):
    """3/4, facing down-right (or up-right from behind): body angled, head
    forward on the right, the near wing folded on the body's left side."""
    g = blank(W, H); dy = BOB[frame]
    legs(g, 'diag')
    neck = thick_line(15, 16, 17, 11 + dy, 2, 'W')
    body = ellipse(11, 18, 6.5, 5, body_colour)
    tail = rect(5, 13, 7, 15, 'W') if kind == 'back' else {}
    put(g, {**neck, **body, **tail})
    put(g, wing([(6, 15), (13, 14), (14, 17), (10, 19), (6, 19)]))
    check_legs(g, FEET, 19)
    smoke(g, [(8, 12)], frame)
    antlers(g, (15, 7), (20, 7), dy)
    stamp(g, 13, 7 + dy, HEAD[kind])
    return g

def main():
    V = {}
    for suffix, frame in (('', 0), ('@1', 1), ('@2', 2)):
        # No straight front/back view -- it reads too wide for this deer (user's call)
        V.update({'R' + suffix: view_side('side', frame), 'DR' + suffix: view_diag('front', frame),
                  'UR' + suffix: view_diag('back', frame)})
    pal = {'K': '000000', 'W': 'fcfcfc', 'S': 'c6ccda', 's': '9797aa', 'B': '785830',
           'P': 'fc74b4', 'E': '5c94fc', 'e': '84a7e9'}
    write(source_path(__file__), pal, '#POSE\nframes\n#DIRS\n6\n', V)

if __name__ == '__main__':
    main()
