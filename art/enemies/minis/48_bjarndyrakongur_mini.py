"""48 Bjarndyrakongur's map mini: the polar bear king, up on its hind legs as in battle, the horn on its brow with
the star at its tip, lumbering at you with a heavy sway, at the player's scale, four views, two frames
(tools/minis.py).

Its battle sheet has one view, its front. Its back is its front's body with the face gone (back()). Through PixelLab (art/enemies/pixellab/48_bjarndyrakongur/mini,
pixellab-out/48-mini, four generations): eight rotations of its front shrunk to 64 px, then its front, back and left
side each given an upright lumber -- swaying side to side, legs stepping in turn, arms swinging. PixelLab threw the
star off the horn's tip in most frames, so the horn is cut from every frame (all above the head's top row) and
drawn back by hand on each: a stalk of orange up from the head's middle, a white star at its top. Each body is the
frame on the mini's palette (minis.recolour), shrunk (minis.shrink, a view's frames by one box so they line up),
cleaned (minis.clean); one black outline round all. The right view is the left mirrored.
48 px tall: its battle height (136 px) at the minis' one scale, 28/79 -- too tall for the sheet's 40 x 28 cells, so a
strip of its own (assets/enemies/minis_48.png). Three of its battle colours and black: its white fur, its grey fur
turned from the light, its orange (the ear flaps, the horn). The star is the white.

Its chase: a bear's charge -- a lumber, then a rush straight at you (the dash: chase_speed(), src/main.cpp).

    python art/enemies/minis/48_bjarndyrakongur_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'W': 'fcfcfc', 'C': 'bcbeca', 'O': 'fc9838'}
CHASE = 'dash'
CW, CH = 40, 52                              # its canvas; the outline under its feet on the bottom row
BODY = 40                                    # the bear without its horn, outline included
HORN = 4                                     # the stalk, under the star (3 tall)
SRC = ROOT / 'pixellab-out/48-mini/animations'
WALKS = {'D': ('v2/walkd', (0, 2)), 'L': ('v1/walkl', (0, 2))}   # one foot forward, the other


def tone(h, s, v):
    """Its oranges and reds the orange, its pale greys white or grey by how lit, the darkest black."""
    if v < 0.15: return 'K'
    if s > 0.35 and (h < 55 or h > 330): return 'O'
    return 'W' if v > 0.86 else 'C'


def body(im):
    """The frame with all above its head's top row (the first 6 px wide) cleared: the horn and its star; and the
    loose bits PixelLab threw off (all but its biggest piece)."""
    solid = {(x, y) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    pieces, seen = [], set()
    for p in solid:
        if p in seen: continue
        piece, todo = set(), [p]
        while todo:
            q = todo.pop()
            if q in seen or q not in solid: continue
            seen.add(q); piece.add(q)
            todo += [(q[0] + dx, q[1] + dy) for dx, dy in ff.N4]
        pieces.append(piece)
    keep = max(pieces, key=len)
    im = im.copy()
    for p in solid - keep: im.putpixel(p, (0, 0, 0, 0))
    top = next(y for y in range(im.height) if sum(im.getpixel((x, y))[3] > 127 for x in range(im.width)) >= 6)
    for y in range(top):
        for x in range(im.width): im.putpixel((x, y), (0, 0, 0, 0))
    return im


def horned(g):
    """The horn drawn back on: up from the middle of the head's top row, the star a white cross at its top."""
    top = min(y for x, y in g)
    xs = [x for x, y in g if y == top]
    cx = (min(xs) + max(xs)) // 2
    g = {p: c for p, c in g.items()}
    for y in range(top - HORN, top + 1): g[cx, y] = 'O'
    sy = top - HORN - 2
    for dx, dy in ((0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)): g[cx + dx, sy + dy] = 'W'
    return ff.outline({p: c for p, c in g.items() if c != 'K' or p in g and any((p[0] + dx, p[1] + dy) in g and g[p[0] + dx, p[1] + dy] != 'K' for dx, dy in ff.N4)})


def view(name, picks):
    ims = [body(minis.recolour(Image.open(SRC / f'{name}-{i:02d}.png').convert('RGBA'), tone, PAL)) for i in picks]
    boxes = [im.getbbox() for im in ims]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    letters = {v: k for k, v in PAL.items() if k != 'K'}
    return [horned({(x, y + CH - minis.H): c for (x, y), c in minis.clean(minis.shrink(im, BODY, letters, box)).items()}) for im in ims]


EYES = {'D': [[(18, 18), (22, 18), (20, 20)], [(18, 18), (21, 18), (20, 20)]],   # by hand: eyes and nose, lost in the shrink
        'L': [[(17, 17), (15, 19)], [(16, 18), (14, 20)]]}



def back(g):
    """Its back, from its front: the same body (PixelLab's own back was a thinner bear, the user: "doesnt match the
    other perspectives bodily proportions"), the face gone -- the muzzle's shadow white, no eyes or nose -- the ear
    flaps and the horn as they are."""
    top = min(y for (x, y), c in g.items() if sum(1 for (i, j) in g if j == y) >= 8)   # the head's top row
    return {(x, y): 'W' if c == 'C' and top <= y < top + 9 else c for (x, y), c in g.items()}


FRAMES = {v: view(*WALKS[v]) for v in 'DL'}
FRAMES['U'] = [back(g) for g in FRAMES['D']]     # before the face goes on the front
for v, fs in EYES.items():
    for g, eyes in zip(FRAMES[v], fs):
        for p in eyes:
            assert g[p] != 'K', (v, p)
            g[p] = 'K'
FRAMES['R'] = [{(CW - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    cap = round((minis.battle_views(48)['D'].getbbox()[3] - minis.battle_views(48)['D'].getbbox()[1]) * 28 / 79)
    minis.make(48, 'bjarndyrakongur', FRAMES, PAL, cap=cap, cell=(CW, CH))
    minis.chase_gif(48, CHASE, FRAMES, PAL, cell=(CW, CH))
