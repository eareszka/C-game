"""45 Kusa Kap's frame 0s brought to the enemy bible by Claude, no PixelLab (the user, 2026-10-30: keep its
design -- the giant bird of the Torres Strait, wings spread, a dugong in its talons -- redrawn to the bible; frame
0 only, no animation). Each of the eight directions' first frame from assets/enemies/45_kusa_kap.png (78x59
cells) is redrawn on the big 98x65 cell by these steps, each a rule of
art/direction/approved_enemy_study/STYLE_BRIEF.md:
1. The project's exact palette, eight colours plus black, one ramp a material: wing brown 341e10 / 463422 /
   8d6b4f, the dugong's grey 595965 / 848694 (its pale step folded in), the head's white fcfcfc, beak and legs
   c18a39 / f0bc3c.
2. No texture: the wings' lattice of feather strokes (single light and dark pixels every third column) folds
   into the wing -- a patch of one colour of four pixels or fewer takes the colour round it. Black inside that
   does not join the outline (the strokes' black ends) folds too; the trailing edge's feather notches, which
   join it, stay: species detail in the silhouette -- thinned where they stack a row apart on the folded wing
   (no hatching: a line at least three rows from the next).
3. Light by form from the upper left: each material's mass lit along its upper edge, dark along its lower.
4. One-pixel black outline, closed; no lone pixels.
Writes 45_kusa_kap.png (24 cells: each direction's frame 0 three times, the still loop) and check_D.png per
direction; bible_check.py checks them. Nothing installed.

    python art/enemies/claude/45_kusa_kap/restyle.py
"""
from pathlib import Path
from collections import Counter
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
SRC = ROOT / 'assets/enemies/45_kusa_kap.png'
CW, CH, W, H, FRAMES = 78, 59, 98, 65, 3
MAP = {'5c402c': '463422', '342418': '341e10', '8c6848': '8d6b4f',
       '8c949c': '848694', '5c646c': '595965', 'b8b8b0': '848694',
       'f0f0e8': 'fcfcfc', 'b08820': 'c18a39', 'f0c830': 'f0bc3c', 'f8e040': 'f0bc3c', '000000': '000000'}
WING = [h('341e10'), h('463422'), h('8d6b4f')]
GREY = [h('595965'), h('848694')]
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
ORDER = ('D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL')


def palette(im):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            px[x, y] = (h(MAP['%02x%02x%02x' % p[:3]]) + (255,)) if p[3] >= 128 else (0, 0, 0, 0)
    return im


def untexture(im, most=4):
    px, w, hh = im.load(), im.width, im.height
    for _ in range(3):
        seen = set()
        for y in range(hh):
            for x in range(w):
                c = px[x, y]
                if (x, y) in seen or not c[3] or c[:3] == K: continue
                comp, todo = [(x, y)], [(x, y)]; seen.add((x, y))
                while todo:
                    a, b = todo.pop()
                    for dx, dy in N4:
                        q = (a + dx, b + dy)
                        if 0 <= q[0] < w and 0 <= q[1] < hh and q not in seen and px[q] == c:
                            seen.add(q); comp.append(q); todo.append(q)
                if len(comp) > most: continue
                nb = Counter(px[q][:3] for a, b in comp for q in ((a + dx, b + dy) for dx, dy in N4)
                             if 0 <= q[0] < w and 0 <= q[1] < hh and px[q][3] and px[q] != c and px[q][:3] != K)
                if nb:
                    for p in comp: px[p] = nb.most_common(1)[0][0] + (255,)
    return im


def strokes(im):
    """Black that does not join the outline folds into the colour round it."""
    px, w, hh = im.load(), im.width, im.height
    at = lambda x, y: px[x, y] if 0 <= x < w and 0 <= y < hh else (0, 0, 0, 0)
    black = {(x, y) for y in range(hh) for x in range(w) if px[x, y][3] and px[x, y][:3] == K}
    keep, todo = set(), [p for p in black if any(not at(p[0] + dx, p[1] + dy)[3] for dx, dy in N4)]
    keep.update(todo)
    while todo:
        x, y = todo.pop()
        for dx, dy in N8:
            q = (x + dx, y + dy)
            if q in black and q not in keep: keep.add(q); todo.append(q)
    for p in black - keep:
        nb = Counter(at(p[0] + dx, p[1] + dy)[:3] for dx, dy in N4 if at(p[0] + dx, p[1] + dy)[3] and at(p[0] + dx, p[1] + dy)[:3] != K)
        if nb: px[p] = nb.most_common(1)[0][0] + (255,)
    return im


def thin(im):
    """No hatching: where two interior black lines run one row apart (the folded wing's stacked feather lines),
    the lower one folds into the colour between them, so a line sits at least three rows from the next."""
    px, w, hh = im.load(), im.width, im.height
    at = lambda x, y: px[x, y] if 0 <= x < w and 0 <= y < hh else (0, 0, 0, 0)
    inner = lambda x, y: at(x, y)[3] and at(x, y)[:3] == K and all(at(x + dx, y + dy)[3] for dx, dy in N4)
    for _ in range(2):
        for y in range(hh):
            for x in range(w):
                if y >= 2 and inner(x, y) and inner(x, y - 2) and at(x, y - 1)[:3] != K and at(x, y - 1)[3]:
                    px[x, y] = at(x, y - 1)                       # stacked rows
                if x >= 2 and inner(x, y) and inner(x - 2, y) and at(x - 1, y)[:3] != K and at(x - 1, y)[3]:
                    px[x, y] = at(x - 1, y)                       # stacked columns (the folded wing's feathers)
    return im


def form(im):
    """Light by form from the upper left on the wings and the dugong: the two rows under a mass's upper edge and
    the column inside its left edge the light step, the two rows over its lower edge and the column inside its
    right edge the dark step, the rest the mid."""
    px, w, hh = im.load(), im.width, im.height
    for ramp in (WING, GREY):
        isin = lambda x, y: 0 <= x < w and 0 <= y < hh and px[x, y][3] and px[x, y][:3] in ramp
        def run(x, y, dx, dy):
            n = 0
            while isin(x + dx * (n + 1), y + dy * (n + 1)): n += 1
            return n
        new = {}
        for y in range(hh):
            for x in range(w):
                if not isin(x, y): continue
                up, dn, lf, rt = run(x, y, 0, -1), run(x, y, 0, 1), run(x, y, -1, 0), run(x, y, 1, 0)
                if up < 2 or lf < 1: new[x, y] = ramp[-1]
                elif dn < 2 or rt < 1: new[x, y] = ramp[0]
                else: new[x, y] = ramp[1] if len(ramp) == 3 else ramp[1]
        for p, c in new.items(): px[p] = c + (255,)
    return im


def outline(im):
    px, w, hh = im.load(), im.width, im.height
    at = lambda x, y: px[x, y] if 0 <= x < w and 0 <= y < hh else (0, 0, 0, 0)
    for x, y in [(x, y) for y in range(hh) for x in range(w) if not px[x, y][3]
                 and any(at(x + dx, y + dy)[3] and at(x + dx, y + dy)[:3] != K for dx, dy in N4)]:
        px[x, y] = K + (255,)
    for x in range(w):
        if px[x, hh - 1][3] and px[x, hh - 1][:3] != K: px[x, hh - 1] = K + (255,)
    for _ in range(2):
        for y in range(hh):
            for x in range(w):
                c = px[x, y]
                if not c[3] or c[:3] == K: continue
                near = [at(x + dx, y + dy) for dx, dy in N8]
                if any(n[3] and n[:3] == c[:3] for n in near): continue
                pick = Counter(n[:3] for n in near if n[3] and n[:3] != K).most_common(1)
                px[x, y] = (pick[0][0] if pick else K) + (255,)
    return im


def place(im):
    im = im.crop(im.getbbox())
    out = Image.new('RGBA', (W, H))
    out.paste(im, ((W - im.width) // 2, H - 2 - im.height))
    return out


if __name__ == '__main__':
    old = Image.open(SRC).convert('RGBA')
    sheet = Image.new('RGBA', (W * 8 * FRAMES, H))
    for d, name in enumerate(ORDER):
        c = old.crop((d * FRAMES * CW, 0, d * FRAMES * CW + CW, CH))
        c = outline(form(thin(strokes(untexture(palette(c))))))
        cell = place(c)
        cell.save(HERE / f'check_{name}.png')
        for f in range(FRAMES): sheet.paste(cell, ((d * FRAMES + f) * W, 0))
    sheet.save(HERE / '45_kusa_kap.png')
    print('written', sheet.size, len({p[:3] for p in sheet.get_flattened_data() if p[3]}) - 1, 'colours + black')
