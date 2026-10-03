"""Writes 12_ebigane.txt: the Ebigane of Fang folklore -- "something like a
cross between a bat, a buffalo, and a vampire", with "sharp fangs and claws
and great bat-like wings".

A hulking buffalo body, a bat face with buffalo horns, great bat wings.
Heads are hand-drawn stamps; body, legs and wings are shapes. Idle: the wings
beat, the head bobs, and on the down-beat it bares its fangs in a hiss.
Wings follow the view rules: behind the body from the front, over it from
behind, the far one foreshortened in 3/4."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import blank, put, stamp, ellipse, thick_line, tube, bat_wing, check_legs, write, source_path

W, H = 44, 40
FEET = H - 1

def head(kind, hiss):
    """Bat face under buffalo horns; 1x1 eyes, pink bat nose, white fangs."""
    if kind == 'side':   # facing right, hung low like a buffalo's, horns curving forward
        jaw = ['.KMKrrrrK..', '..KWKKWK...', '...KKKK....'] if hiss else ['.KMMWKKWKK.', '..KKKKKK...']
        return ['..KK.......', '.KMMK.KK...', 'KMMMMKBBK..', 'KMMKMMKBBK.', 'KMMMMMMMKBK', 'KMMMMMMMMnK'] + jaw
    top = ['.K.........K.', 'KBK.K...K.KBK', 'KBBKMK.KMKBBK', '.KBKMMKMMKBK.', '..KMMMMMMMK..']
    if kind == 'front':
        jaw = ['...KWrrrWK...', '....KrrrK....', '.....KKK.....'] if hiss else ['...KWMMMWK...', '....KKKKK....']
        return top + ['..KMKMMMKMK..', '..KMMnnnMMK..'] + jaw
    return top + ['..KMDDDDDMK..', '...KMMMMMK...', '....KKKKK....']

FLAP = ((0, 0), (0, -3), (1, 3))   # wing tips: rest, up, down
BOB = (0, -1, 1)
HISS = (False, False, True)

def leg(g, x0, y0, x1, c):
    """Thick buffalo leg, hoof at the bottom."""
    cells = tube([(x0, y0), (x1, FEET - 1)], [2], lambda d, b: c)
    for (x, y) in cells:
        if y >= FEET - 1: cells[(x, y)] = 'h'
    put(g, cells)

# A thin pink rat tail (the mouse it was) that curls a new way every frame.
# Paths start inside the rump. Side/3-4 curl back from the rump; from behind
# it curls over the rump; head-on it is hidden.
TAIL = {
    'side':  [[(6, 25), (2, 26), (1, 29), (2, 31), (4, 31), (4, 29)],     # curled down
              [(6, 24), (2, 22), (1, 19), (2, 17), (4, 17), (4, 19)],     # curled up
              [(6, 26), (2, 29), (1, 33), (3, 35), (5, 34)]],             # hanging low
    'back':  [[(21, 24), (21, 30), (23, 33), (25, 32), (24, 30)],
              [(21, 24), (20, 30), (18, 33), (16, 32), (17, 30)],
              [(21, 24), (22, 29), (25, 30), (26, 28)]],
}

def rat_tail(g, points, dx=0):
    """1-pixel pink tail with black only where it borders empty space, so it
    stays thin and needs no outline where it crosses the body."""
    line = set()
    for a, b in zip(points, points[1:]):
        line |= set(thick_line(a[0] + dx, a[1], b[0] + dx, b[1], 0, 'n'))
    for (x, y) in line:
        if 0 <= x < W and 0 <= y < H: g[y][x] = 'n'
    for (x, y) in line:
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < W and 0 <= ny < H and g[ny][nx] == '.': g[ny][nx] = 'K'

def hump_body(hump, rump, front=True):
    """Buffalo build: a high shoulder hump and a lower rump, outlined as one.
    Light ridge along the top, dark belly underneath."""
    def colour(x, y, t):
        return 'L' if t < 0.15 else 'D' if (front and t > 0.7) else 'M'
    return {**ellipse(*rump, colour), **ellipse(*hump, colour)}

def view_side(frame):
    g = blank(W, H); dy = BOB[frame]; f = FLAP[frame]
    bat_wing(g, (18, 17), (24, 6), [(29, 2), (33, 6), (32, 12)], (22, 18), 'w', 'v', f)   # far wing, behind the hump
    rat_tail(g, TAIL['side'][frame])
    leg(g, 12, 28, 13, 'D'); leg(g, 25, 28, 26, 'D')                                      # far legs
    leg(g, 9, 28, 9, 'M'); leg(g, 22, 28, 22, 'M')                                         # near legs
    put(g, {**thick_line(24, 22, 28, 21 + dy, 3, 'M'),                                    # short thick neck
            **hump_body((19, 22, 8, 7.5), (10, 25, 6, 5))})
    check_legs(g, FEET, 28)
    bat_wing(g, (17, 18), (11, 7), [(4, 3), (0, 10), (3, 17)], (10, 21), 'w', 'v', f)     # near wing, over the body
    stamp(g, 27, 15 + dy, head('side', HISS[frame]))                                       # head hung low and forward
    return g

def view_diag(kind, frame):
    """3/4: body angled toward down-right (front) or up-right (back)."""
    g = blank(W, H); dy = BOB[frame]; fx, fy = FLAP[frame]
    front = kind == 'front'
    def wings():
        if front:   # the left wing is nearer: full size; the right one foreshortened
            bat_wing(g, (24, 17), (29, 8), [(33, 5), (36, 9), (35, 13)], (26, 19), 'w', 'v', (-fx, fy))
            bat_wing(g, (16, 18), (10, 7), [(3, 3), (0, 10), (3, 17)], (12, 21), 'w', 'v', (fx, fy))
        else:       # from behind the right wing is nearer: full size; the left foreshortened
            bat_wing(g, (16, 18), (12, 9), [(8, 5), (5, 10), (7, 14)], (13, 20), 'w', 'v', (fx, fy))
            bat_wing(g, (24, 17), (30, 6), [(37, 2), (41, 9), (38, 16)], (27, 19), 'w', 'v', (-fx, fy))
    if front:
        wings(); rat_tail(g, TAIL['side'][frame], dx=1)
    leg(g, 13, 28, 13, 'D'); leg(g, 25, 28, 26, 'D')
    leg(g, 10, 28, 9, 'M'); leg(g, 21, 28, 21, 'M')
    if not front:   # from behind the low head is on the far side of the hump: drawn first, mostly hidden
        stamp(g, 20, 13 + dy, head('back', False))
    put(g, hump_body((19, 22, 7.5, 7.5), (11, 25, 5.5, 5), front))
    check_legs(g, FEET, 28)
    if front:
        stamp(g, 20, 15 + dy, head('front', HISS[frame]))
    else:
        rat_tail(g, TAIL['side'][frame], dx=1)
        wings()    # over the hump and the head
    return g

def view_front(kind, frame):
    """Head-on (front: wings behind, head low on the chest) or from behind
    (back: wings over the back, the head just showing over the hump)."""
    g = blank(W, H); dy = BOB[frame]; fx, fy = FLAP[frame]
    front = kind == 'front'
    left = ((17, 19), (10, 8), [(3, 4), (0, 12), (4, 19)], (15, 24))
    def wings():
        for mirror in (False, True):
            m = (lambda p: (43 - p[0], p[1])) if mirror else (lambda p: p)
            s, w, tips, tr = left
            bat_wing(g, m(s), m(w), [m(p) for p in tips], m(tr), 'w', 'v', ((-fx if mirror else fx), fy))
    if front: wings()                   # head-on the tail is hidden behind the body
    leg(g, 15, 28, 14, 'D'); leg(g, 28, 28, 29, 'D')
    leg(g, 18, 28, 18, 'M'); leg(g, 25, 28, 25, 'M')
    put(g, ellipse(21.5, 23, 8, 7.5, lambda x, y, t: 'L' if t < 0.15 else 'D' if front and t > 0.7 else 'M'))
    check_legs(g, FEET, 28)
    if front:
        stamp(g, 15, 15 + dy, head('front', HISS[frame]))
    else:
        stamp(g, 15, 10 + dy, head('back', False))
        wings()
        rat_tail(g, TAIL['back'][frame])
    return g

def main():
    V = {}
    for suffix, frame in (('', 0), ('@1', 1), ('@2', 2)):
        V.update({'R' + suffix: view_side(frame), 'DR' + suffix: view_diag('front', frame),
                  'UR' + suffix: view_diag('back', frame), 'D' + suffix: view_front('front', frame),
                  'U' + suffix: view_front('back', frame)})
    pal = {'K': '000000', 'D': '2b1f40', 'M': '5e486a', 'L': '664b95', 'h': '1e1e24',
           'B': 'e8e0c0', 'w': '531b1c', 'v': 'b6433d', 'n': 'ec8476', 'W': 'fcfcfc', 'r': 'b70000'}
    write(source_path(__file__), pal, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
