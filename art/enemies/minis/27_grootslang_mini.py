"""27 Grootslang's map mini: the great snake, an elephant's head on a serpent's body, slithering at you, its rattle
up behind, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet only sits coiled, facing front. Through PixelLab (art/enemies/pixellab/27_grootslang/mini,
pixellab-out/27-mini): its battle frame at 2x, edited, rotated to its eight views and given a slither on the left
side -- every one of them came back still coiled, so they give it only its head from each side. The slither is
built here from flat parts, back to front, each with its own black edge where it overlaps what is behind: the snake
body a thick wave along the ground, its rattle raised at the end, the elephant's head held up over it -- ears,
tusks, trunk. The head holds still from frame to frame; only the body's wave swings, one way then the other, as a
snake's does. 24 px tall, under the Myrmecoleon's 28 as its battle frame (65 px) is under that one's (79). Three
of its battle colours and black: its grey, the pink of its ears, its ivory (tusks and rattle). Its dark grey goes:
black edges part its coils.

Its chase: it slithers at you without stopping, weaving side to side (the Cobra's wiggle: chase_bend(),
src/main.cpp).

    python art/enemies/minis/27_grootslang_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '9797aa', 'P': 'ec8476', 'I': 'e8e0c0'}
CHASE = 'wiggle'


def ellipse(cx, cy, rx, ry):
    return {(x, y) for y in range(int(cy - ry), int(cy + ry) + 1) for x in range(int(cx - rx), int(cx + rx) + 1)
            if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1}


def rect(x0, y0, x1, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


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


def rattle(x, y, up=True):
    """Its rattle: three ivory beads stacked, ending the tail at (x, y)."""
    d = -1 if up else 1
    return [(rect(x - 1, y + d * 2 * i, x + 1, y + d * 2 * i), 'I') for i in range(3)]


def head_front(cx, top):
    ears = [(ellipse(cx - 6, top + 6, 3, 5), 'G', {p: 'P' for p in ellipse(cx - 6, top + 6, 1, 3)}),
            (ellipse(cx + 6, top + 6, 3, 5), 'G', {p: 'P' for p in ellipse(cx + 6, top + 6, 1, 3)})]
    head = ellipse(cx, top + 5, 4, 5)
    trunk = rect(cx - 1, top + 9, cx + 1, top + 16) | {(cx, top + 17)}
    tusks = [(line((cx - 3, top + 9), (cx - 4, top + 12)), 'I'), (line((cx + 3, top + 9), (cx + 4, top + 12)), 'I')]
    return ears + [(head, 'G', {(cx - 2, top + 5): 'K', (cx + 2, top + 5): 'K'})] + tusks + [(trunk, 'G')]


def front(step):
    """Coming at you: the head over its body, the body's curve swinging out behind to one side, then the other."""
    s = 1 if step == 0 else -1
    m = lambda x: 20 + s * (x - 20)
    body = thick([(20, 24), (m(13), 23), (m(9), 21), (m(12), 17), (m(18), 16), (m(26), 15), (m(30), 12)], 2)
    return build([(body, 'G')] + rattle(m(30), 9) + head_front(20, 5))


def back(step):
    """Going from you: the back of its head, and its body nearer you, trailing toward you in a curve that swings
    one way then the other, the rattle up at its end."""
    s = 1 if step == 0 else -1
    m = lambda x: 20 + s * (x - 20)
    ears = [(ellipse(14, 11, 3, 5), 'G'), (ellipse(26, 11, 3, 5), 'G')]
    body = thick([(20, 15), (20, 18), (m(26), 21), (m(26), 24), (m(19), 24), (m(12), 23)], 2)
    return build(ears + [(ellipse(20, 10, 4, 5), 'G'), (body, 'G')] + rattle(m(10), 20))


def side(step):
    """Its head to the left, held up on its neck; its body a wave along the ground behind it, the wave a half-step
    on each frame, the rattle raised at the end."""
    wave = [(14, 23), (19, 20), (24, 24), (29, 20)] if step == 0 else [(14, 21), (19, 24), (24, 20), (29, 24)]
    body = thick([(12, 14), (12, 19)] + wave, 2)
    tail = thick([wave[-1], (33, wave[-1][1] - 2), (35, 17)], 1)
    ear = (ellipse(15, 10, 3, 5), 'G', {p: 'P' for p in ellipse(15, 10, 1, 3)})
    head = (ellipse(9, 10, 5, 4), 'G', {(7, 9): 'K'})
    trunk = (thick([(4, 12), (3, 16), (3, 19), (5, 21)], 1), 'G')
    tusk = (line((7, 14), (6, 15), (6, 17)), 'I')
    return build([(body, 'G'), (tail, 'G')] + rattle(35, 15) + [ear, head, trunk, tusk])


FRAMES = {'D': [front(0), front(1)], 'U': [back(0), back(1)], 'L': [side(0), side(1)]}
FRAMES['R'] = [{(39 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(27, 'grootslang', FRAMES, PAL, cap=24)
    minis.chase_gif(27, CHASE, FRAMES, PAL)
