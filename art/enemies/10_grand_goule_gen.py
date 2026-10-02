"""Writes 10_grand_goule.txt: the Grand'Goule of Poitiers -- "a monstrous
bat-winged dragon with a gaping mouth", hooked claws (too small to read at this size, so left out), a forked scorpion's
stinger for a tail, bronze-green with a red collar, and poisonous breath.

Crouched on the ground. Heads and the stinger are hand-drawn stamps; body,
legs, wings and tail are shapes. Idle: the wings lift and dip, the mouth gapes
wider and breathes a poison puff, the stinger draws back and strikes."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import blank, put, stamp, ellipse, thick_line, tube, bat_wing, check_legs, write, source_path

W, H = 44, 34
FEET = H - 1

def mouth(kind, rows):
    """A head stamp with `rows` rows of open mouth (r) between the teeth."""
    if kind == 'side':
        top = ['..KKKK......', '.KGGGGKKK...', 'KGGKGGGGGKK.', 'KGGGGGGGGGGK', 'KGGKWKWKWKKK']
        gape = ['KGKrrrrrrrK.', 'KGKrrrrrrrK.', 'KGKrrrrrK...'][3 - rows:]
        return top + gape + ['KGGKWKWKK...', '.KKKKKKK....']
    top = ['..KKKKKKK..', '.KGGGGGGGK.', 'KGKGGGGGKGK', 'KGGGGGGGGGK', 'KWKWKWKWKWK']
    return top + ['KrrrrrrrrrK'] * rows + ['KWKWKWKWKWK', '.KKKKKKKKK.']

BACK_HEAD = ['..KKKKKKK..', '.KGGGGGGGK.', 'KGGDDDDDGGK', 'KGGGGGGGGGK', 'KGDGGGGGDGK', '.KGGGGGGGK.', '..KKKKKKK..']
STINGER = ['KKK', 'KWK', 'WKW']   # forked, below the tail's tip

# Per frame: wing flap (dx, dy), rows of open mouth, poison puff, tail-tip offset.
FLAP = ((0, 0), (0, -3), (1, 2))
GAPE = (2, 1, 3)
PUFF = (False, False, True)
STING = ((0, 0), (-2, -1), (3, 2))

def body_colour(d, below):
    """Bronze belly plates underneath, dark green along the back, green between."""
    if below and d >= 2: return 'Z'
    if not below and d >= 3: return 'D'
    return 'G'

def scorpion_tail(g, points, radii, frame):
    """Banded tail along `points` (rump first), the forked stinger at its tip."""
    sx, sy = STING[frame]
    points = points[:-2] + [(x + sx // 2, y + sy // 2) for x, y in points[-2:-1]] + [(points[-1][0] + sx, points[-1][1] + sy)]
    cells = tube(points, radii, lambda d, below: 'G')
    for (x, y) in cells:
        if (x + y) % 4 < 2: cells[(x, y)] = 'D'       # segment bands
    put(g, cells)
    tx, ty = points[-1]
    stamp(g, tx - 1, ty + 1, STINGER)

def leg(g, points, c):
    """A thick crouched leg."""
    put(g, tube(points, [2] * (len(points) - 1), lambda d, below: c))

def collar(g, cx, cy, r, side=0):
    """Red band round the neck, painted over the neck's own pixels. `side`
    +1/-1 paints only that half (the throat, seen from the side)."""
    for (x, y) in thick_line(cx - r, cy + 1, cx + r, cy - 1, 1, 'R'):
        if side and (x - cx) * side < 0: continue
        if 0 <= y < H and 0 <= x < W and g[y][x] not in '.K': g[y][x] = 'R'

def puff(g, cx, cy):
    """Poison breath: a green cloud over the mouth (overlapping it, so it is
    never a loose blob), a lighter wisp rising off it."""
    put(g, {**ellipse(cx, cy, 3, 3, lambda *_: 'P'), **ellipse(cx + 1, cy - 3, 2, 2, lambda *_: 'p')})

def view_side(frame):
    g = blank(W, H)
    bat_wing(g, (24, 16), (29, 6), [(34, 1), (38, 5), (37, 11)], (27, 17), 'z', 'Z', FLAP[frame])   # far wing
    scorpion_tail(g, [(9, 23), (4, 20), (3, 13), (6, 7), (11, 4), (14, 6)], (3, 2, 2, 1, 1), frame)
    leg(g, [(12, 25), (9, 29), (11, FEET - 1)], 'D')          # far hind
    leg(g, [(22, 25), (23, FEET - 1)], 'D')                   # far fore
    leg(g, [(10, 25), (7, 29), (9, FEET - 1)], 'G')           # near hind, crouched
    leg(g, [(20, 25), (20, FEET - 1)], 'G')                   # near fore
    put(g, tube([(9, 23), (16, 22), (22, 20), (26, 16), (28, 13)], (6, 6, 4, 3), body_colour))
    check_legs(g, FEET, 25)
    collar(g, 26, 16, 3, side=1)       # from the side only the throat half of the collar shows
    bat_wing(g, (20, 17), (14, 6), [(8, 1), (4, 8), (7, 15)], (13, 18), 'z', 'Z', FLAP[frame])      # near wing
    head = mouth('side', GAPE[frame])
    stamp(g, 27, 5, head)
    if PUFF[frame]: puff(g, 40, 11)
    return g

def view_diag(kind, frame):
    """3/4: body angled toward down-right (front) or up-right (back); tail
    arcing up behind on the left. Wings spread to both sides, the far one
    foreshortened; from the front they are behind the body, from behind they
    are drawn over its back."""
    g = blank(W, H)
    front = kind == 'front'
    fx, fy = FLAP[frame]
    def wings():
        bat_wing(g, (25, 14), (30, 6), [(34, 3), (37, 7), (35, 11)], (27, 16), 'z', 'Z', (-fx, fy))   # far, right
        bat_wing(g, (16, 15), (10, 5), [(4, 1), (1, 8), (4, 14)], (12, 18), 'z', 'Z', (fx, fy))       # near, left
    tail = lambda: scorpion_tail(g, [(13, 22), (8, 18), (7, 12), (10, 7), (15, 5), (18, 7)], (3, 2, 2, 1, 1), frame)
    if front:
        tail(); wings()    # from the front the tail is behind the wings
    leg(g, [(14, 25), (12, 29), (13, FEET - 1)], 'D')
    leg(g, [(25, 25), (26, FEET - 1)], 'D')
    leg(g, [(12, 25), (10, 29), (11, FEET - 1)], 'G')
    leg(g, [(21, 25), (21, FEET - 1)], 'G')
    put(g, tube([(12, 23), (18, 21), (23, 18), (25, 15)], (6, 6, 4), body_colour if front else (lambda d, b: 'D' if d < 1.5 else 'G')))
    check_legs(g, FEET, 25)
    if front:
        collar(g, 24, 15, 3)
        stamp(g, 20, 5, mouth('front', GAPE[frame]))
        if PUFF[frame]: puff(g, 26, 13)
    else:
        stamp(g, 20, 6, BACK_HEAD)
        wings(); tail()    # from behind: wings over the head, the tail in front of both
    return g

def view_front(kind, frame):
    """Head-on (front) or from behind (back): wings spread both sides, body
    squat, tail arcing up over the back."""
    g = blank(W, H)
    front = kind == 'front'
    fx, fy = FLAP[frame]
    left = ((17, 15), (10, 5), [(3, 1), (0, 9), (4, 15)], (15, 19))
    def wings():   # behind the body from the front, over its back from behind
        for mirror in (False, True):
            m = (lambda p: (43 - p[0], p[1])) if mirror else (lambda p: p)
            s, w, tips, tr = left
            bat_wing(g, m(s), m(w), [m(p) for p in tips], m(tr), 'z', 'Z', ((-fx if mirror else fx), fy))
    if front:
        scorpion_tail(g, [(22, 20), (27, 15), (28, 9), (25, 4), (21, 3)], (3, 2, 1, 1), frame)
        wings()
    for x, c in ((15, 'D'), (28, 'D'), (17, 'G'), (26, 'G')):
        leg(g, [(x, 25), (x + (-1 if x < 22 else 1), FEET - 1)], c)
    body = ellipse(21.5, 21, 7, 6, lambda x, y, t: 'Z' if front and t > 0.35 and abs(x - 21.5) < 4 else 'G')
    neck = {**thick_line(21, 16, 21, 10, 3, 'G'), **thick_line(22, 16, 22, 10, 3, 'G')}   # joins head to body
    put(g, {**neck, **body})
    check_legs(g, FEET, 25)
    if front:
        collar(g, 21, 14, 4)
        stamp(g, 16, 6, mouth('front', GAPE[frame]))
        if PUFF[frame]: puff(g, 21, 15)
    else:
        wings()
        scorpion_tail(g, [(22, 22), (27, 17), (28, 10), (25, 5), (21, 4)], (3, 2, 1, 1), frame)   # in front of the wings
        stamp(g, 16, 7, BACK_HEAD)
    return g

def main():
    V = {}
    for suffix, frame in (('', 0), ('@1', 1), ('@2', 2)):
        V.update({'R' + suffix: view_side(frame), 'DR' + suffix: view_diag('front', frame),
                  'UR' + suffix: view_diag('back', frame), 'D' + suffix: view_front('front', frame),
                  'U' + suffix: view_front('back', frame)})
    pal = {'K': '000000', 'D': '163623', 'G': '2c6c44', 'Z': 'c9a433', 'z': '887000',
           'R': 'b70000', 'r': '792727', 'W': 'fcfcfc', 'P': '4edc4a', 'p': 'a8f0bc'}
    write(source_path(__file__), pal, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
