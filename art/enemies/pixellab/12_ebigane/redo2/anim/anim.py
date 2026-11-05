"""12 Ebigane's sheets, timed to its patterns (the user, 2026-11-03: "animate to match bullet patterns"). One left view; the right-hand directions (DR R UR) are it mirrored.
Idle, 3 poses in the default 0 1 0 2 loop: 0 the approved frame; 1 fins flared tall, the pose it holds as a pentagram opens from its middle; 2 jaws wide -- its screech leaves on this frame (breathe, breath_frame 2),
from the mouth. Fly, 4 frames: its legs running through the air on the figure-eight, played by flap_phase. PixelLab (pixellab-out/12-redo2-anim, 6 generations; idle.log, fly.log). All fold onto the approved colours,
feet on the last row, one outline.

    python art/enemies/pixellab/12_ebigane/redo2/anim/anim.py   # c_N.png, f_N.png, review.png, 12.gif, 12_fly.gif; review.lua makes 12_review.aseprite
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H, MS = 104, 68, 260      # not the standard 98x65: its tall fins and the screech's stretch need the room
OX, OY = 15, 31
MOUTH = (21, 43)               # the gaping gullet in pose 2, this frame's pixels (mirrored: W - 1 - x)
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
IDLE = (7, 4)            # raw frames for poses 1 and 2
FLY = (3, 5, 6, 8)
FRAME0 = Image.open(HERE.parent / 'frame0.png').convert('RGBA')
PAL = sorted({p[:3] for p in FRAME0.get_flattened_data() if p[3] and p[:3] != K})
print(['%02x%02x%02x' % c for c in PAL])
def logged(n): return [l.strip() for l in (HERE / f'{n}.log').read_text().splitlines() if l.strip().endswith('.png')]
def fold(p):
    return K if max(p) < 0x2b else min(PAL, key=lambda c: sum((a - v) ** 2 for a, v in zip(c, p)))
def clean(path):
    im = Image.open(path).convert('RGBA')
    g = {(x - OX, y - OY): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    for _ in range(3):
        for (x, y), c in list(g.items()):
            if c == K: continue
            near = [g.get((x + a, y + b)) for a, b in N8]
            if c not in near:
                pick = Counter(n for n in near if n and n != K).most_common(1)
                if pick: g[x, y] = pick[0][0]
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
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    drop = H - 1 - max(y for x, y in g)
    g = {(x, y + drop): c for (x, y), c in g.items()}
    xs, ys = [x for x, y in g], [y for x, y in g]
    print('cols', min(xs), max(xs), 'rows', min(ys), max(ys), 'drop', drop)
    f = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: f.putpixel((x, y), c + (255,))
    return f
base = Image.new('RGBA', (W, H)); base.paste(FRAME0, (2, 3))
idle = [base] + [clean(logged('idle')[i]) for i in IDLE]
fly = [clean(logged('fly')[i]) for i in FLY]
for i, f in enumerate(idle): f.save(HERE / f'c_{i}.png')
for i, f in enumerate(fly): f.save(HERE / f'f_{i}.png')
S = 3
rev = Image.new('RGBA', (W * S * 4, H * S * 2), (0, 0, 0, 255))
for i, f in enumerate(idle): rev.alpha_composite(f.resize((W * S, H * S), 0), (i * W * S, 0))
for i, f in enumerate(fly): rev.alpha_composite(f.resize((W * S, H * S), 0), (i * W * S, H * S))
rev.save(HERE / 'review.png')
def gif(seq, name, ms):
    big = []
    for f in seq:
        bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(f); big.append(bg.resize((W * 4, H * 4), 0).convert('P', palette=Image.ADAPTIVE))
    big[0].save(HERE / name, save_all=True, append_images=big[1:], duration=ms, loop=0)
gif([idle[0], idle[1], idle[0], idle[2]], '12.gif', [400, 250, 400, 250])
gif(fly, '12_fly.gif', 150)
m = idle[2].copy(); m.putpixel(MOUTH, (255, 255, 255, 255))
c = m.crop((7, 18, 47, 58))
bg = Image.new('RGBA', c.size, (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(c); bg.resize((480, 480), 0).save(HERE / 'mouth_x12.png')
