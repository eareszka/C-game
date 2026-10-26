"""21 Asp's map mini: the green serpent with its yellow belly that stops one ear with its tail -- uncoiled and
slithering at you, its head up on its neck, its ears pricked, at the player's scale, four views of two frames
(tools/minis.py).

It is a snake, so it slithers (the user, over its first mini, which sprang upright on its coils): drawn as the
Angont's is (32), from flat parts after that pose -- its body a wave along the ground, dark beneath, tapering to its
tail, the tip raised (the lore's tail held to its ear); its neck rising in an S, yellow down its throat; its head
held still from frame to frame, its two yellow ears up. Only the body's wave moves, a half-step each frame, as a
snake's does. One silhouette, one black outline round it, its parts told apart by colour.
17 px tall, its ears over its raised head: its battle frames stand 34. Three of its battle
colours and black: its green, its dark green (its underside, its far curve), its yellow (throat, belly, ears).

Its chase: it slithers at you without stopping, weaving side to side (the Cobra's wiggle: chase_bend(),
src/main.cpp).

    python art/enemies/minis/21_asp_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'D': '2c6c44', 'G': '4fa667', 'Y': 'd0c078'}
CHASE = 'wiggle'


def ellipse(cx, cy, rx, ry):
    return {(x, y) for y in range(int(cy - ry), int(cy + ry) + 1) for x in range(int(cx - rx), int(cx + rx) + 1)
            if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1}


def line(*pts):
    out = set()
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        out |= {(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)}
    return out


def thick(pts, r):
    """A tube through the points, r pixels either side."""
    return {(x + dx, y + dy) for x, y in line(*pts) for dx in range(-r, r + 1) for dy in range(-r, r + 1)
            if dx * dx + dy * dy <= r * r + r}


def under(px):
    """The lowest pixel of each column: its dark underside."""
    low = {}
    for x, y in px: low[x] = max(low.get(x, y), y)
    return {(x, y): 'D' for x, y in low.items()}


def build(parts):
    """parts, back to front: (pixels, letter) or (pixels, letter, marks), painted one over the next, then one black
    outline round the whole."""
    g = {}
    for part in parts:
        for p in part[0]: g[p] = part[1]
        for p, m in (part[2] if len(part) > 2 else {}).items(): g[p] = m
    return ff.outline(g)


def ears(cx, top, apart):
    """Its two ears pricked up over its head, apart px between them."""
    return {(cx - apart // 2, top): 'Y', (cx - apart // 2, top + 1): 'Y',
            (cx + apart - apart // 2, top): 'Y', (cx + apart - apart // 2, top + 1): 'Y'}


def front(step):
    """Coming at you: its head up over its neck, its yellow throat facing you, its body's curve swinging out behind
    to one side, then the other, its tail tip raised at its end."""
    s = 1 if step == 0 else -1
    m = lambda x: 20 + s * (x - 20)
    body = thick([(20, 25), (m(15), 25), (m(12), 23), (m(14), 21), (m(20), 21), (m(26), 22)], 1)
    tail = line((m(26), 22), (m(29), 24), (m(31), 23), (m(32), 21))
    neck = thick([(20, 17), (20, 23)], 1)
    head = ellipse(20, 15, 3, 2)
    face = {(19, 15): 'K', (21, 15): 'K'}
    return build([(body, 'G', under(body)), (tail, 'G'), (neck, 'Y'), (head | set(ears(20, 12, 4)), 'G',
                  {**face, **ears(20, 12, 4)})])


def back(step):
    """Going from you: the back of its head, its ears, its neck down to the ground, its body nearer you trailing in
    a curve that swings one way then the other, out to its raised tail tip."""
    s = 1 if step == 0 else -1
    m = lambda x: 20 + s * (x - 20)
    head = ellipse(20, 15, 3, 2)
    neck = thick([(20, 17), (20, 21)], 1)
    body = thick([(20, 21), (m(25), 22), (m(26), 24), (m(20), 25), (m(14), 25)], 1)
    tail = line((m(14), 25), (m(11), 24), (m(10), 22))
    return build([(head | set(ears(20, 12, 4)), 'G', ears(20, 12, 4)), (neck, 'G'),
                  (body, 'G', under(body)), (tail, 'G')])


def side(step):
    """Its head to the left, held up on an S of neck, its throat yellow; its body a wave along the ground behind it,
    the wave a half-step on each frame, tapering to its tail, the tip raised."""
    wave = [(15, 25), (19, 23), (23, 25), (27, 23)] if step == 0 else [(15, 25), (19, 25), (23, 23), (27, 25)]
    body = thick([(12, 18), (11, 21), (13, 24)] + wave, 1)
    tail = line(wave[-1], (31, 24), (33, 23), (34, 21))
    throat = {(x, y): 'Y' for x, y in body if y < 24 and x <= 11 + (y > 20)}
    head = ellipse(10, 16, 3, 2)
    face = {(9, 15): 'K', **ears(11, 13, 2)}
    return build([(body, 'G', {**under(body), **throat}), (tail, 'G'), (head | set(ears(11, 13, 2)), 'G', face)])


FRAMES = {'D': [front(0), front(1)], 'U': [back(0), back(1)], 'L': [side(0), side(1)]}
FRAMES['R'] = [{(39 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(21, 'asp', FRAMES, PAL, cap=17)
    minis.chase_gif(21, CHASE, FRAMES, PAL)
