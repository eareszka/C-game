"""32 Angont's map mini: the venomous serpent of the lakes and swamps, uncoiled and slithering at you, its head up on
its neck, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet only sits coiled, facing front. Through PixelLab (art/enemies/pixellab/32_angont/mini,
pixellab-out/32-mini): its battle frame edited to uncoil, side on (its head raised on an S of neck, its body long
along the ground), then a slither on the left side -- which only flicked its tongue. So it is built here from flat
parts after that pose, back to front, each with its own black edge where it overlaps what is behind: the body a
thick wave along the ground, tapering to its tail, its throat cream up the neck, the head held still from frame to
frame. Only the body's wave moves, a half-step each frame, as a snake's does.
18 px tall: its battle height (51 px) at the minis' one scale, 28/79. Three of its battle colours and black: its
olive (body), its cream (throat and belly), its poison green (eyes). Its dark brown blotches go to black spots. Its
floating poison skulls come with it, 3 x 4 px each, bobbing by it (the user: "have the green skulls float from it
from mini scale too").

Its chase: it slithers at you without stopping, weaving side to side (the Cobra's wiggle: chase_bend(),
src/main.cpp).

    python art/enemies/minis/32_angont_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'A': '7b601d', 'B': 'd0c078', 'D': '4edc4a'}
CHASE = 'wiggle'


def rect(x0, y0, x1, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


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


def build(parts):
    """parts, back to front: (pixels, letter) or (pixels, letter, marks). Each part takes a black edge on whatever
    it covers, so overlapping parts stay apart."""
    g = {}
    for part in parts:
        px, c = part[0], part[1]
        for x, y in px:
            for dx, dy in ff.N4:
                if (x + dx, y + dy) not in px: g[x + dx, y + dy] = 'K'
        for p in px: g[p] = c
        for p, m in (part[2] if len(part) > 2 else {}).items(): g[p] = m
    return ff.outline(g)


def belly(px):
    """The cream underside: the lowest pixel of each column."""
    low = {}
    for x, y in px: low[x] = max(low.get(x, y), y)
    return {(x, y): 'B' for x, y in low.items()}


def spots(px, pts):
    return {p: 'K' for p in pts if p in px}


def skulls(step, a, b):
    """Its two poison skulls floating by it, 3 x 4 px each (eyes, a jaw) (the battle's at the minis' scale), bobbing one up while the
    other goes down."""
    out = []
    for (x, y), d in ((a, -1), (b, 1)):
        y += d if step else 0
        out.append((rect(x, y, x + 2, y + 3), 'D', {(x, y + 1): 'K', (x + 2, y + 1): 'K', (x + 1, y + 3): 'K'}))
    return out


def front(step):
    """Coming at you: the head up over its neck, the cream throat facing you, the body's curve swinging out behind
    to one side, then the other, the tail tip at its end."""
    s = 1 if step == 0 else -1
    m = lambda x: 20 + s * (x - 20)
    body = thick([(20, 25), (m(13), 25), (m(9), 23), (m(11), 20), (m(17), 19), (m(25), 19), (m(30), 21)], 1)
    tail = line((m(30), 21), (m(33), 24), (m(36), 25))
    neck = thick([(20, 16), (20, 22)], 1)
    head = ellipse(20, 14, 4, 3)
    face = {(18, 14): 'D', (22, 14): 'D', **{(x, 16): 'K' for x in range(19, 22)}}
    return build([(body, 'A', spots(body, [(m(9), 23), (m(15), 19), (m(23), 19)])), (tail, 'A'),
                  (neck, 'B'), (head, 'A', face)] + skulls(step, (10, 12), (28, 12)))


def back(step):
    """Going from you: the back of its head, its neck down to the ground, its body nearer you, trailing toward you
    in a curve that swings one way then the other, out to its tail."""
    s = 1 if step == 0 else -1
    m = lambda x: 20 + s * (x - 20)
    head = ellipse(20, 14, 4, 3)
    neck = thick([(20, 16), (20, 20)], 1)
    body = thick([(20, 20), (m(26), 21), (m(27), 24), (m(20), 25), (m(13), 24)], 1)
    tail = line((m(13), 24), (m(9), 22), (m(7), 21))
    return build([(head, 'A'), (neck, 'A'),
                  (body, 'A', spots(body, [(m(26), 22), (m(17), 25)])), (tail, 'A')] + skulls(step, (10, 12), (28, 12)))


def side(step):
    """Its head to the left, held up on an S of neck; its body a wave along the ground behind it, the wave a
    half-step on each frame, tapering to its tail."""
    wave = [(15, 24), (20, 22), (25, 24), (30, 22)] if step == 0 else [(15, 24), (20, 24), (25, 22), (30, 24)]
    body = thick([(13, 16), (12, 19), (13, 22)] + wave, 2)
    tail = thick([wave[-1], (33, 23)], 1) | line((33, 23), (37, 24))
    throat = {(x, y): 'B' for x, y in body if y < 23 and x <= 11 + (y > 19)}
    head = ellipse(10, 13, 4, 2)
    face = {(9, 12): 'D', **{(x, 14): 'K' for x in range(6, 10)}}
    return build([(body, 'A', {**belly(body), **throat, **spots(body, [(18, 22), (23, 23), (28, 22)])}),
                  (tail, 'A'), (head, 'A', face)] + skulls(step, (20, 12), (31, 13)))


FRAMES = {'D': [front(0), front(1)], 'U': [back(0), back(1)], 'L': [side(0), side(1)]}
FRAMES['R'] = [{(39 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(32, 'angont', FRAMES, PAL, cap=18)
    minis.chase_gif(32, CHASE, FRAMES, PAL)
