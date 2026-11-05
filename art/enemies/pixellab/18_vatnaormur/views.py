"""18 Vatnaormur's new battle frame (the user, 2026-11-02: a full redo through PixelLab, the same creature; symmetrical,
looking straight down, a slug face; "left but longer tentacles" = pixellab-out/18-concepts3 e2, mirrored). No water.

The stalks are drawn longer by repeating their own narrow row, STALK rows more. Slug the palette's soft peach-pink
with a shade (the old sprite's belly colour) and a deep shade, spiked body two dark greys. Each eye one 2 px black mark on its stalk's bulb, no
white. Built on the left half and mirrored, so it is exactly symmetrical. One black outline, on the 98x65 frame, its
base on the bottom row.

    python art/enemies/pixellab/18_vatnaormur/views.py     # writes frame0.png, frame0_x8.png
"""
from pathlib import Path
from collections import Counter
import colorsys
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / 'concepts3/e2_sym.png'
W, H = 98, 65
STALK = 8             # rows added to each eyestalk
CUT = 12              # the stalk's narrow row, source coordinates: everything lower moves down
K = '000000'
PINK, PINK_D, PINK_DD = 'f0b890', 'ec8476', 'b6433d'
GREY, GREY_D = '595965', '34343e'
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def fold(p):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in p))
    h *= 360
    if v < 0.175: return K
    if s < 0.1 and v > 0.9: return PINK               # the eye whites go
    if 280 <= h or h < 20:
        if v > 0.72: return PINK
        if v > 0.5: return PINK_D
        if s > 0.45: return PINK_DD
    return GREY if v > 0.3 else GREY_D


def flat(g, most):
    seen, out = set(), dict(g)
    for p, c in g.items():
        if p in seen: continue
        piece, todo = {p}, [p]
        while todo:
            a = todo.pop()
            for dx, dy in N4:
                q = (a[0] + dx, a[1] + dy)
                if q not in piece and g.get(q) == c: piece.add(q); todo.append(q)
        seen |= piece
        if c == K or len(piece) > most: continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def longer(g):
    out = {}
    for (x, y), c in g.items():
        out[x, y + (STALK if y > CUT else 0)] = c
        if y == CUT:
            for k in range(1, STALK + 1): out[x, y + k] = c
    return out


def main():
    im = Image.open(SRC).convert('RGBA')
    left = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(48) if im.getpixel((x, y))[3] > 127}
    left = flat(left, 6)
    for (x, y), c in list(left.items()):              # the frown: black, not the body's grey
        if 20 <= y <= 31 and 38 <= x and c in (GREY, GREY_D): left[x, y] = K
    left = longer(left)
    for x in range(41, 44):                           # the eye: bulb cleared, one 2 px mark
        for y in range(7, 10):
            if left.get((x, y)) == K: left[x, y] = PINK
    left[42, 7] = left[42, 8] = K
    g = dict(left)
    for (x, y), c in left.items(): g[95 - x, y] = c
    edge = {p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)}
    body = {p: c for p, c in g.items() if p not in edge}
    g = dict(body)
    for x, y in body:
        for a, b in N4:
            if (x + a, y + b) not in body: g[x + a, y + b] = K
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = 1, H - 1 - max(ys)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        out.putpixel((x + dx, y + dy), tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    out.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    print('bbox', out.getbbox(), 'colours', len(set(g.values())) - 1, '+ black', dict(Counter(g.values())))


main()
