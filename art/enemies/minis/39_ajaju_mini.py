"""39 Ajaju's map mini: the terror of the Garo Hills, a chameleon up on four long kneeless stilt legs, its forked red
tongues hanging, stalking at you, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet has a front, a side and a back. Through PixelLab (art/enemies/pixellab/39_ajaju/mini,
pixellab-out/39-mini, one generation, the user: "only need 1 generation for each"): its side frame given a stalk --
the body held level, the stilts swinging stiff, diagonal pairs by turns. Drawn here after it from flat parts, back to
front, each with its own black edge where it overlaps what is behind: the stilts, the green body with its crest and
curled tail, the head, its mouth wide open (the user: "full open while chasing"), three forked tongues
writhing out of it, other ways each frame, and its 3 x 3 turret eyes, one size from every side. The body holds still from frame to frame; only the
stilts step, swinging from the hip without a knee.
14 px tall: its battle height (40 px) at the minis' one scale, 28/79. Three of its battle colours and black: its
green (body), its pale yellow (stilts, eyes), its tongue red (tongues, crest).

Its chase: it stalks at you without stopping, slow on its stilts then a longer stride (the Opimachus's dash:
chase_speed(), src/main.cpp).

    python art/enemies/minis/39_ajaju_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'A': '4fa667', 'B': 'fae488', 'G': 'b6433d'}
CHASE = 'dash'


def ellipse(cx, cy, rx, ry):
    return {(x, y) for y in range(int(cy - ry), int(cy + ry) + 1) for x in range(int(cx - rx), int(cx + rx) + 1)
            if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1}


def line(*pts):
    out = set()
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        out |= {(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)}
    return out


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


def stilt(hip, swing, lift=0):
    """A stilt from the hip straight to the foot, no knee: swing pixels forward (-) or back (+), lift off the ground."""
    return (line(hip, (hip[0] + swing, 26 - lift)), 'B')


def tongues(root, tips):
    """Its forked tongues out of its open mouth at root, each to its tip and forked there, writhing: each frame
    gives them other tips. One part, so they writhe together without black between them."""
    return [(set().union(*(line(root, (x, y)) | {(x - 1, y + 1), (x + 1, y + 1)} for x, y in tips)), 'G')]


def eye(x, y, pupil=True):
    """A chameleon's turret eye, 3 x 3, the same from every side; its pupil only where it looks your way."""
    return (ellipse(x, y, 1, 1), 'B', {(x, y): 'K'} if pupil else {})


def side(step):
    """Its head to the left, its mouth wide open, three forked tongues writhing out of it: the far stilts first,
    then its body level on them, its tail curled up behind, its head. step 0: the near front stilt and the far hind
    one reach out, the others swing back; 1 the reverse."""
    s = 1 if step == 0 else -1
    far = [stilt((18, 18), 2 * s), stilt((25, 18), -2 * s)]
    near = [stilt((16, 18), -2 * s), stilt((27, 18), 2 * s)]
    body = ellipse(22, 17, 6, 1)
    tail = line((28, 16), (31, 15), (33, 15), (34, 16), (33, 17), (32, 16))
    head = ellipse(14, 16, 4, 1)
    jaw = line((10, 19), (16, 19))
    tips = [(4, 20), (7, 24), (12, 24)] if step == 0 else [(5, 23), (4, 18), (10, 24)]
    return build(far + [(tail, 'A'), (body, 'A', {(20, 16): 'G', (24, 16): 'G'})] + near + tongues((10, 18), tips) +
                 [(jaw, 'A'), (head, 'A', {(15, 15): 'G'}), eye(14, 16)])


def front(step):
    """Facing you: its big head, the eyes bulging either side, its mouth wide open, three forked tongues writhing
    out of it between its forelegs, which hide the hind ones; its tail curled out to one side. The forelegs lift
    by turns."""
    a, b = (0, 1) if step == 0 else (1, 0)
    fore = [stilt((17, 19), -2, a), stilt((23, 19), 2, b)]
    tail = line((24, 18), (26, 17), (27, 16), (28, 17), (27, 18))
    mouth = {**{(x, 18): 'K' for x in range(18, 23)}, **{(x, 19): 'G' for x in range(19, 22)}}
    tips = [(17, 23), (20, 25), (23, 22)] if step == 0 else [(18, 25), (21, 22), (23, 25)]
    return build([(tail, 'A')] + fore + tongues((20, 20), tips) +
                 [(ellipse(20, 17, 3, 2), 'A', {(20, 15): 'G', **mouth}), eye(16, 17), eye(24, 17)])


def back(step):
    """Going from you: the back of its head, its eyes bulging either side, the red crest down its spine, its tail
    curled down between its hind stilts, which hide the fore ones and lift by turns."""
    a, b = (0, 1) if step == 0 else (1, 0)
    hind = [stilt((17, 19), -2, a), stilt((23, 19), 2, b)]
    tail = line((20, 20), (20, 23), (21, 24), (22, 23))
    return build([eye(16, 16, False), eye(24, 16, False), (ellipse(20, 16, 3, 1), 'A', {(20, 15): 'G'}),
                  (ellipse(20, 18, 4, 1), 'A', {(20, 18): 'G'})] + hind + [(tail, 'A')])


FRAMES = {'D': [front(0), front(1)], 'U': [back(0), back(1)], 'L': [side(0), side(1)]}
FRAMES['R'] = [{(39 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(39, 'ajaju', FRAMES, PAL, cap=14)
    minis.chase_gif(39, CHASE, FRAMES, PAL)
