"""Writes 06_wakmangganchi_aragondi.txt: a mountain-sized boar with seven
one-eyed tusked heads and bamboo, grass and a stream on its back.

The heads are hand-drawn stamps; body, legs, necks and the back's plants are
shapes. Each part is drawn back to front with its own black outline, so
overlapping parts stay separate."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import blank as _blank, put, stamp, ellipse as _ellipse, rect, thick_line, top_of, check_legs, write, source_path

W, H = 48, 42
HEAD = {  # side (facing right), front, back -- 9x7, one moon eye (Y/W), scimitar tusks (W)
    'side':  ['..KKKK...', '.KMMMMKK.', 'KMMYYMMMK', 'KMMYWMMLK', 'KMMMMMLLK', 'KWKKKWKKK', '.WW...WW.'],
    'front': ['.KK...KK.', 'KMMKKKMMK', 'KMMYWYMMK', 'KMMYYYMMK', 'KWMLLLMWK', 'WKKLDLKKW', 'W..KKK..W'],
    'back':  ['.KK...KK.', 'KMMKKKMMK', 'KMMMMMMMK', 'KMDMMMDMK', 'KMMMMMMMK', '.KMMMMMK.', '..KKKKK..'],
}
OPEN = {  # jaw dropped, red mouth showing -- 9x8
    'side':  ['..KKKK...', '.KMMMMKK.', 'KMMYYMMMK', 'KMMYWMMLK', 'KMMMKKKKK', 'KMMKRRR..', 'KWKKKWKK.', '.WW...W..'],
    'front': ['.KK...KK.', 'KMMKKKMMK', 'KMMYWYMMK', 'KMMYYYMMK', 'KWMLLLMWK', 'WKRRRRRKW', 'WKMKKKMKW', '..KKKKK..'],
}
# Each head moves its own way, out of step with the others: (dx, dy) in frames 1 and 2.
MOVES = [((-2, 0), (2, 0)), ((0, -2), (0, 1)), ((2, 0), (-1, 0)), ((0, 2), (0, -1)),
         ((-1, -1), (1, 1)), ((0, -1), (0, 2)), ((2, -1), (-2, 1))]
SNAP = {1: {1, 3, 5}, 2: {0, 2, 4, 6}}   # heads whose jaws are open in each frame

BAMBOO = (0, 1, -1)   # stalk growth per frame

def blank(): return _blank(W, H)

def ellipse(cx, cy, rx, ry):
    """Boar body: light back, dark belly, scattered bristle flecks."""
    def colour(x, y, t):
        c = 'L' if t < 0.18 else 'D' if t > 0.72 else 'M'
        return 'D' if c == 'M' and (x * 7919 + y * 104729) % 13 == 0 else c
    return _ellipse(cx, cy, rx, ry, colour)

def back_life(g, body, xs_bamboo, xs_grass, stream, grow=0):
    """Bamboo stalks, grass tufts and a stream along the top of `body`."""
    for x in xs_bamboo:
        t = top_of(body, x)
        h = 9 + (x * 7) % 5 + grow
        # 4 wide so the outline leaves a 2-wide green stalk; dark nodes every 4 rows
        put(g, {(x + dx, y): ('D' if (t - y) % 4 == 0 else 'G' if dx < 1 else 'g')
                for dx in (-1, 0, 1, 2) for y in range(t - h, t + 1)})
        put(g, {(x + 2 + dx, t - h + 3 + dy): 'g' for dx in range(3) for dy in range(3) if dx + dy < 3})
    for x in xs_grass:
        t = top_of(body, x)
        for i, dx in enumerate((-1, 1, 3)):
            g[t - 2 - i % 2][x + dx] = 'g'; g[t - 1][x + dx] = 'G'
    x0, x1 = stream
    for x in range(x0, x1 + 1):
        t = top_of(body, x)
        if t is not None:
            g[t + 1][x] = 'B' if (x // 2) % 2 else 'b'; g[t + 2][x] = 'B'

def leg(x, top, bottom, c):
    """5 wide at the hip, 3 below, a dark hoof."""
    cells = rect(x, top, x + 4, top + 3, c)
    cells.update(rect(x + 1, top + 4, x + 3, bottom - 2, c))
    cells.update(rect(x + 1, bottom - 1, x + 3, bottom, 'D'))
    return cells

def legs(g, near, far, top, bottom):
    """Drawn before the body, starting inside it, so the body covers every
    leg's top -- no leg ever hangs past the belly."""
    for x in far: put(g, leg(x, top, bottom, 'D'))
    for x in near: put(g, leg(x, top, bottom, 'M'))

def heads(g, root, spots, kind, frame=0):
    """Necks from `root` to each head spot (back to front), then the head
    stamps -- each head moved and its jaw snapped per MOVES and SNAP."""
    for i, (hx, hy) in enumerate(spots):
        dx, dy = MOVES[i][frame - 1] if frame else (0, 0)
        rows = OPEN[kind] if kind in OPEN and i in SNAP.get(frame, ()) else HEAD[kind]
        hx = min(max(hx + dx, 0), W - len(rows[0])); hy = min(max(hy + dy, 0), H - len(rows))
        put(g, thick_line(root[0], root[1], hx + 3, hy + 3, 2, 'M'))
        stamp(g, hx, hy, rows)

def view_side(kind, frame=0):
    g = blank()
    body = ellipse(18, 25, 16, 9)
    legs(g, (7, 23), (11, 26), 25, 41)
    put(g, {**thick_line(1, 21, 3, 23, 1, 'M')})            # tail
    put(g, body)
    check_legs(g, 41, 25)
    back_life(g, body, (8, 13, 19, 25), (4, 16, 29), (6, 27), BAMBOO[frame])
    spots = [(28, 6), (33, 1), (39, 3), (38, 11), (39, 19), (33, 17), (29, 23)]
    heads(g, (31, 24), spots, kind, frame)
    return g

def view_front(kind, frame=0):
    g = blank()
    body = ellipse(24, 24, 15, 10)
    legs(g, (15, 29), (12, 32), 25, 41)
    put(g, body)
    check_legs(g, 41, 25)
    back_life(g, body, (14, 20, 29, 34), (11, 24, 37), (16, 32), BAMBOO[frame])
    spots = [(4, 17), (9, 9), (17, 3), (30, 9), (35, 17), (12, 18), (27, 18)]
    if kind == 'back':           # heads sit behind the body: draw them first
        g2 = blank(); heads(g2, (24, 20), spots, kind, frame)
        for y in range(H):
            for x in range(W):
                if g[y][x] == '.': g[y][x] = g2[y][x]
    else:
        heads(g, (24, 24), spots, kind, frame)
    return g

def main():
    # Body and legs hold still; the heads writhe and snap, the bamboo grows and shrinks.
    V = {}
    for suffix, frame in (('', 0), ('@1', 1), ('@2', 2)):
        V.update({'R' + suffix: view_side('side', frame), 'DR' + suffix: view_side('front', frame),
                  'UR' + suffix: view_side('back', frame), 'D' + suffix: view_front('front', frame),
                  'U' + suffix: view_front('back', frame)})
    pal = {'K': '000000', 'D': '341e10', 'M': '633e1b', 'L': '967448', 'Y': 'fae488', 'W': 'fcfcfc',
           'R': 'b70000', 'G': '058f3a', 'g': '4edc4a', 'B': '3e91cc', 'b': '84a7e9'}
    write(source_path(__file__), pal, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
