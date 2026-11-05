"""10 Grand'Goule, flatter (the user, 2026-11-03: "enemy looks too detailed, needs to be more flat colors"; the cast is one colour and one shade a material). The poses' silhouettes stay (anim.py's c_N):
bone goes into tan, so chest and beak are one fill; hide patches of navy under MERGE px go into the blue, keeping only the big shadows; small interior black marks and small patches of anything merge.
Red gullet and claws, ember rims and yellow eyes are spared. Writes flat_N.png, review_flat.png, compare_flat.png, 10_flat.gif, spawn_flat.png; review_flat.lua makes 10_flat_review.aseprite.

    python art/enemies/pixellab/10_grand_goule/redo2/anim/flatten.py
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
K, RED = (0, 0, 0), (0xb7, 0x00, 0x00)
HIDE, NAVY, BONE, TAN, CHAR, EMBER = (0x37, 0x5a, 0x94), (0x37, 0x38, 0x7b), (0xe8, 0xe0, 0xc0), (0xb2, 0x96, 0x6a), (0x34, 0x34, 0x3e), (0xf0, 0xbc, 0x3c)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
MERGE = 14
MOUTH = ((41, 38), (31, 25), (38, 31))


def patches(g, colours):
    seen = set()
    for p, c in g.items():
        if p in seen or c not in colours: continue
        piece, todo = {p}, [p]
        while todo:
            a = todo.pop()
            for d in N4:
                q = (a[0] + d[0], a[1] + d[1])
                if q not in piece and g.get(q) == c: piece.add(q); todo.append(q)
        seen |= piece
        yield c, piece


def neighbours(g, piece, avoid=(K,)):
    return Counter(g[q] for a in piece for q in ((a[0] + d[0], a[1] + d[1]) for d in N4) if q in g and q not in piece and g[q] not in avoid)


def flatten(im):
    W, H = im.size
    g = {(x, y): im.getpixel((x, y))[:3] for y in range(H) for x in range(W) if im.getpixel((x, y))[3]}
    for p, c in list(g.items()):
        if c == BONE: g[p] = TAN
    for c, piece in list(patches(g, (NAVY, HIDE, TAN, CHAR))):       # small patches of any fill, big shadows kept
        if len(piece) < MERGE:
            n = neighbours(g, piece)
            if n:
                for a in piece: g[a] = n.most_common(1)[0][0]
    for c, piece in list(patches(g, (K,))):                          # small black marks inside the body: the outline stays
        if len(piece) <= 5 and all((a[0] + d[0], a[1] + d[1]) in g for a in piece for d in N4):
            n = neighbours(g, piece)
            if n:
                for a in piece: g[a] = n.most_common(1)[0][0]
    for (x, y), c in list(g.items()):                                # stray ember dots off a run: the rim reads as a line or not at all
        if c == EMBER and not any(g.get((x + a, y + b)) == EMBER for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b):
            n = neighbours(g, {(x, y)})
            if n: g[x, y] = n.most_common(1)[0][0]
    f = Image.new('RGBA', (W, H))
    for p, c in g.items(): f.putpixel(p, c + (255,))
    return f


src = [Image.open(HERE / f'c_{i}.png').convert('RGBA') for i in range(3)]
fr = [flatten(s) for s in src]
W, H = fr[0].size
for i, f in enumerate(fr): f.save(HERE / f'flat_{i}.png')
S = 4
rev = Image.new('RGBA', (W * S * 3, H * S), (0, 0, 0, 255))
for i, f in enumerate(fr): rev.alpha_composite(f.resize((W * S, H * S), 0), (i * W * S, 0))
rev.save(HERE / 'review_flat.png')
cmp = Image.new('RGBA', (W * 6 * 2 + 10, H * 6), (0, 0, 0, 255))
cmp.alpha_composite(src[0].resize((W * 6, H * 6), 0), (0, 0)); cmp.alpha_composite(fr[0].resize((W * 6, H * 6), 0), (W * 6 + 10, 0)); cmp.save(HERE / 'compare_flat.png')
big = []
for i in (0, 1, 0, 2):
    bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(fr[i]); big.append(bg.resize((W * 4, H * 4), 0).convert('P', palette=Image.ADAPTIVE))
big[0].save(HERE / '10_flat.gif', save_all=True, append_images=big[1:], duration=[400, 250, 400, 250], loop=0)
for i, f in enumerate(fr): print(i, len({p[:3] for p in f.get_flattened_data() if p[3]}), 'colours with black')
