"""34 Anaye's appearance mini (the user, 2026-11-03: "a mini of it walking forward and then raising its axe"; it comes through a portal in a cutscene, no chase; an exception to no minis for bosses). Drawn by PixelLab alone: m1 (pixellab-out/34-mini), a walk and a raise
(pixellab-out/34-mini-anim), the overhead pose t2. Sequence: walk 0 1 2 3 (loop as long as it needs), then raise 1, raise 2, t2 (held). Three colours and black on a 48x48 cell, feet on the last row but one, one outline. Not wired into the game: there is no cutscene yet.

    python art/enemies/pixellab/34_anaye/redo2/mini/seq.py   # seq/f_N.png, seq/strip.png, seq/all_x6.png, seq/walk.gif, seq/raise.gif, seq/34_mini_seq.aseprite (via seq.lua)
"""
from pathlib import Path
import sys
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

PAL = {'K': '000000', 'A': '595965', 'C': 'e8e0c0', 'L': 'b69cee'}
CW, CH = 48, 48
RGB = {k: tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for k, c in PAL.items()}
N8 = ff.N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
def logged(name): return [l.strip() for l in (HERE / name).read_text().splitlines() if l.strip().endswith('.png')]
def frame(path, anchor=None):
    im = Image.open(path).convert('RGBA')
    g = {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127: g[x, y] = min(RGB, key=lambda k: sum((a - b) ** 2 for a, b in zip(RGB[k], p[:3])))
    left, pieces = set(g), []
    while left:
        piece, todo = set(), [left.pop()]
        while todo:
            a = todo.pop(); piece.add(a)
            for d in N8:
                q = (a[0] + d[0], a[1] + d[1])
                if q in left: left.discard(q); todo.append(q)
        pieces.append(piece)
    g = {p: g[p] for p in max(pieces, key=len)}
    g = {p: c for p, c in g.items() if not (c == 'K' and any((p[0] + a, p[1] + b) not in g for a, b in ff.N4))}
    # the body is centred on its legs, the lowest rows, so the axe does not push it about
    ys = [y for x, y in g]; low = max(ys)
    feet = [x for x, y in g if y >= low - 3]
    dx, dy = CW // 2 - (min(feet) + max(feet)) // 2, CH - 2 - low
    return ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()})
W, R = logged('walk.log'), logged('raise.log')
frames = [frame(W[i]) for i in (0, 1, 2, 3)] + [frame(R[1]), frame(R[2]), frame(HERE / 't2.png')]
ims = [ff.image(g, PAL, CW, CH) for g in frames]
for i, im in enumerate(ims): im.save(HERE / 'seq' / f'f_{i}.png')
for i, g in enumerate(frames):
    xs, ys = [x for x, y in g], [y for x, y in g]
    print(i, 'cols', min(xs), max(xs), 'rows', min(ys), max(ys), 'colours', len(set(g.values())) - ('K' in g.values()))
    assert min(xs) >= 1 and max(xs) <= CW - 1 and min(ys) >= 1
strip = Image.new('RGBA', (CW * len(ims), CH))
for i, im in enumerate(ims): strip.alpha_composite(im, (i * CW, 0))
strip.save(HERE / 'seq/strip.png')
k = 6; G = (0x4e, 0xdc, 0x4a, 255)
b = Image.new('RGBA', ((CW * k + 6) * 4, (CH * k + 6) * 2), G)
for i, im in enumerate(ims): b.alpha_composite(im.resize((CW * k, CH * k), 0), ((i % 4) * (CW * k + 6), (i // 4) * (CH * k + 6)))
b.save(HERE / 'seq/all_x6.png')
def gif(seq, name, ms):
    big = []
    for im in seq:
        bg = Image.new('RGBA', (CW, CH), G); bg.alpha_composite(im); big.append(bg.resize((CW * 6, CH * 6), 0).convert('P', palette=Image.ADAPTIVE))
    big[0].save(HERE / 'seq' / name, save_all=True, append_images=big[1:], duration=ms, loop=0)
gif(ims[:4], 'walk.gif', 200)
gif(ims[:4] + ims[:4] + ims[4:], 'raise.gif', [200] * 8 + [180, 180, 900])
