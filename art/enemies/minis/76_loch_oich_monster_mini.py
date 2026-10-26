"""76 Loch Oich monster's map mini: Loch Ness's smaller neighbour in the Great Glen, seen as a string of humps --
and with the head of a dog on a long neck: swimming at you through the ground as through its loch, its humps
rolling, its dog's head held up, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet is a dog's head on an eel's body, floating, from one side. Drawn here after it, from flat parts,
as the snakes are (21, 32): its head a dog's -- a pale muzzle, a black nose, an eye, a long ear hanging dark -- up
on a long neck; behind it its eel's body along the ground in a string of humps, each an arch breaking the ground,
rolling back half a hump each frame; its tail tapering after them. One silhouette, one black outline round it,
its parts told apart by colour.
19 px tall, its head up on its neck: a little over its battle height (49 px) at the minis' one scale, 28/79. Three of its battle colours and black, one
ramp: its brown, its dark brown (its ears, its underside), its tan (its muzzle and throat, high and on its front).

Its chase: the surf (chase_speed(), src/main.cpp) -- a lunge through the water, then a glide.

    python art/enemies/minis/76_loch_oich_monster_mini.py
"""
from pathlib import Path
import math, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'L': 'd7a175', 'M': '94703d', 'D': '633e1b'}
CHASE = 'surf'
GROUND = 25                                      # its body's middle row where it lies along the ground


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


def humps(x0, x1, step, rise=5, span=11):
    """Its eel's body from x0 to x1 (either way), a string of humps: arches rise px high, span px long, the string
    rolled back half a hump on step 1."""
    pts, d = [], 1 if x1 > x0 else -1
    for x in range(x0, x1 + d, d):
        u = (abs(x - x0) / span + 0.5 * step) % 1
        pts.append((x, GROUND - round(rise * max(0.0, math.sin(2 * math.pi * u)))))
    return thick(pts, 1)


def side(step):
    """Its head to the left, up on its neck; its humps behind it, then its tail."""
    neck = thick([(12, 16), (12, 20), (14, 24), (16, GROUND)], 1)
    body = humps(16, 32, step)
    tail = line((32, GROUND), (35, GROUND), (37, GROUND - 1))
    head = ellipse(11, 13, 3, 2) | ellipse(7, 14, 2, 1)
    marks = {(5, 13): 'K', (10, 12): 'K',                                      # nose, eye
             **{(x, y): 'L' for x, y in ellipse(7, 14, 2, 1) if (x, y) != (5, 13)},
             **{p: 'D' for p in ellipse(14, 14, 1, 2)},                        # its long ear, hanging
             **{(x, y): 'L' for x, y in neck if x <= 11 + (y > 19) and y < GROUND - 1}}
    return build([(body, 'M', under(body)), (tail, 'M'), (neck | head | ellipse(14, 14, 1, 2), 'M',
                   {**under(neck), **marks})])


def front(step):
    """Coming at you: its dog's face, muzzle forward, ears hanging either side, up on its neck; its humps rising
    behind it to one side, then the other."""
    s = 1 if step == 0 else -1
    body = humps(20, 20 + s * 14, 0, rise=4, span=10) | humps(20, 20 - s * 10, 1, rise=3, span=10)
    neck = thick([(20, 16), (20, GROUND)], 1)
    head = ellipse(20, 13, 4, 3)
    marks = {**{(x, y): 'L' for x, y in ellipse(20, 15, 2, 1)}, (20, 14): 'K', (18, 12): 'K', (22, 12): 'K',
             **{p: 'D' for p in ellipse(15, 13, 1, 2) | ellipse(25, 13, 1, 2)},
             **{(x, y): 'L' for x, y in neck if y < GROUND - 1}}
    return build([(body, 'M', under(body)), (neck | head | ellipse(15, 13, 1, 2) | ellipse(25, 13, 1, 2), 'M',
                   marks)])


def back(step):
    """Going from you: the back of its head and its hanging ears, its neck, its humps trailing toward you to one
    side, then the other."""
    s = 1 if step == 0 else -1
    body = humps(20, 20 + s * 14, 0, rise=4, span=10) | humps(20, 20 - s * 10, 1, rise=3, span=10)
    neck = thick([(20, 16), (20, GROUND)], 1)
    head = ellipse(20, 13, 4, 3)
    ears = ellipse(15, 13, 1, 2) | ellipse(25, 13, 1, 2)
    return build([(neck | head | ears, 'M', {p: 'D' for p in ears}), (body, 'M', under(body))])


FRAMES = {'D': [front(0), front(1)], 'U': [back(0), back(1)], 'L': [side(0), side(1)]}
FRAMES['R'] = [{(39 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(76, 'loch_oich_monster', FRAMES, PAL, cap=19)
    minis.chase_gif(76, CHASE, FRAMES, PAL)
