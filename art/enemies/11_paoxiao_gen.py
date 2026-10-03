"""Writes 11_paoxiao.txt: the Paoxiao of Mount Gouwu -- a goat-like body with
"a human face armed with tiger's teeth", "human hands", and "its eyes are
behind its armpits"; it "makes sounds like a baby".

Heads and the armpit eye are hand-drawn stamps; body, legs, arms and tail are
shapes. Idle: the eyeless face wails (mouth open, then gaping), the armpit
eyes glance and blink; body and limbs stay put."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import blank, inside, put, stamp, ellipse, thick_line, slim_leg, check_legs, write, source_path

W, H = 30, 26
FEET = H - 1

def head(kind, mouth):
    """Head stamps. Human face (S skin, no eyes) under goat horns; mouth is
    'shut' (a fanged grin), 'open' or 'wide' (red, wailing)."""
    if kind == 'side':
        jaw = {'shut':  ['.KMSKWKWK.', '..KSSSSK..'],
               'open':  ['.KMSKrrKK.', '..KSWKWK..'],
               'wide':  ['.KMSKrrrK.', '..KSrrrK..', '..KSWKWK..']}[mouth]
        return ['.KKK......', 'KDDDKK....', 'KDKKMMKK..', '.KMMSSSSK.', '.KMSSSSSSK'] + jaw + ['...KKKK...']
    if kind == 'front':
        jaw = {'shut':  ['..KWKKKWK..', '...KSSSK...'],
               'open':  ['..KWrrrWK..', '...KSSSK...'],
               'wide':  ['..KWrrrWK..', '...KrrrK...', '...KWKWK...']}[mouth]
        return ['KK.......KK', 'KDK.....KDK', '.KDKKKKKDK.', '..KSSSSSK..', '..KSSKSSK..'] + jaw + ['....KKK....']
    return ['KK.......KK', 'KDK.....KDK', '.KDKKKKKDK.', '..KMMMMMK..', '..KMMMMMK..',
            '..KMMMMMK..', '...KMMMK...', '....KKK....']

MOUTH = ('shut', 'open', 'wide')
EYE = (['.KKK.', 'KWWKK', '.KKK.'],      # staring
       ['.KKK.', 'KKWWK', '.KKK.'],      # glancing back
       ['.....', 'KKKKK', '.....'])      # blink
BOB = (0, 0, 1)                          # the head dips as it gapes

def fur(x, y, t):
    if (x * 5 + y * 3) % 7 == 0: return 'D'           # shaggy flecks
    return 'L' if t < 0.3 else 'M'

def legs(g, hind, arms):
    """Goat hind legs with hooves; front legs are arms ending in human hands
    whose fingers spread forward on the ground (touching the hand, so no loose
    pixels)."""
    for points, edge, c in hind: slim_leg(g, points, c, edge, 'h')
    for points, edge, c, toward in arms:
        slim_leg(g, points, c, edge, 'S')
        hx, hy = points[-1]
        for y in range(hy - 4, hy):                      # bare human forearm
            for x in (hx, hx - edge):
                if inside(g, x, y) and g[y][x] == c: g[y][x] = 'S'
        for dx in (1, 2):
            x = hx + toward * dx
            if inside(g, x, hy) and g[hy][x] == '.': g[hy][x] = 'S'

def view_side(frame):
    g = blank(W, H); dy = BOB[frame]
    legs(g, hind=[([(10, 17), (9, 21), (10, FEET)], -1, 'D'), ([(7, 17), (5, 21), (6, FEET)], -1, 'M')],
            arms=[([(18, 17), (18, FEET)], -1, 'D', 1), ([(16, 17), (16, FEET)], -1, 'M', 1)])
    put(g, {**thick_line(18, 13, 21, 9 + dy, 2, 'M'),
            **ellipse(12, 15, 8, 4.5, fur),
            **ellipse(4.5, 11, 1.5, 1.5, lambda *_: 'L')})       # neck, body, a small goat tail
    check_legs(g, FEET, 17)
    stamp(g, 12, 15, EYE[frame])                                 # the eye behind the armpit
    stamp(g, 19, 3 + dy, head('side', MOUTH[frame]))
    return g

def view_diag(kind, frame):
    """3/4: body angled, the near armpit eye showing (from the front)."""
    g = blank(W, H); dy = BOB[frame]
    legs(g, hind=[([(9, 17), (8, 21), (9, FEET)], -1, 'D'), ([(6, 17), (4, 21), (5, FEET)], -1, 'M')],
            arms=[([(17, 17), (17, FEET)], 1, 'D', 1), ([(14, 17), (14, FEET)], -1, 'M', 1)])
    put(g, {**thick_line(16, 13, 19, 9 + dy, 2, 'M'),
            **ellipse(11, 15, 7, 4.8, fur),
            **ellipse(4, 11, 1.5, 1.5, lambda *_: 'L')})
    check_legs(g, FEET, 17)
    if kind == 'front':
        stamp(g, 10, 15, EYE[frame])
        stamp(g, 14, 2 + dy, head('front', MOUTH[frame]))
    else:
        stamp(g, 14, 3 + dy, head('back', 'shut'))
    return g

def main():
    V = {}
    for suffix, frame in (('', 0), ('@1', 1), ('@2', 2)):
        # No straight front/back view, like the Snawfus: down and up reuse the 3/4 views
        V.update({'R' + suffix: view_side(frame), 'DR' + suffix: view_diag('front', frame),
                  'UR' + suffix: view_diag('back', frame)})
    pal = {'K': '000000', 'L': 'c6ccda', 'M': '9797aa', 'D': '595965', 'h': '34343e',
           'S': 'f0b890', 'W': 'fcfcfc', 'r': '7c0a1b'}
    write(source_path(__file__), pal, '#POSE\nframes\n#DIRS\n6\n', V)

if __name__ == '__main__':
    main()
