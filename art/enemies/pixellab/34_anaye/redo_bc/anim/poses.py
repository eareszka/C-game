"""34 Anaye's 9 battle poses, each with the meaning Anaye::anim_frame gives it (the user: keep 9 distinct poses, 260 ms each).
0 approved frame 0; 1 breath, the lift's start; 2 3 axe rising; 4 overhead, screaming; 5 raising slightly; 6 up and over; 7 the slash, with redo2's pale arc pasted behind; 8 blade in the ground.

    python art/enemies/pixellab/34_anaye/redo_bc/anim/poses.py    # p_N.png, review.png, GIFs, measures
"""
from collections import Counter
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H, MS = 130, 118, 260
K = (0, 0, 0)
BONE = (0xe8, 0xe0, 0xc0)
LILAC = (0xb6, 0x9c, 0xee)
STEEL = (0x84, 0x86, 0x94)
VIOLET = (0x66, 0x4b, 0x95)
RIM_BOX = (4, 92, 36, 112)    # pose 7's blade
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
PICK = (None, 'lift_1', 'lift_2', 'lift_3', 'lift_4', 'slam_1', 'slam_3', 'slam_6', 'slam_8')


def arc():
    """redo2's slash: its longest connected run of bone colour, which is not on the body."""
    im = Image.open(HERE.parents[1] / 'redo2/anim2/c_11.png').convert('RGBA')
    px = im.load()
    left = {(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] == BONE}
    best = set()
    while left:
        piece, todo = set(), [left.pop()]
        while todo:
            a = todo.pop(); piece.add(a)
            for d in N8:
                q = (a[0] + d[0], a[1] + d[1])
                if q in left: left.discard(q); todo.append(q)
        if max(p[0] for p in piece) - min(p[0] for p in piece) > (max(p[0] for p in best) - min(p[0] for p in best) if best else -1): best = piece
    return best


frames = []
for i, name in enumerate(PICK):
    f = Image.open(HERE.parent / 'idle_frame0_clean.png' if name is None else HERE / f'{name}.png').convert('RGBA')
    if i == 7:
        px = f.load()
        line = arc()
        print('arc', len(line), 'px')
        for x, y in line:
            if not px[x, y][3]: px[x, y] = BONE + (255,)
        for x, y in line:             # its outline, only on empty canvas
            for a, b in N4:
                q = (x + a, y + b)
                if 0 <= q[0] < W and 0 <= q[1] < H and not px[q][3]: px[q] = K + (255,)
    px = f.load()
    # Hand fixes. Lilac is the blade's rim only: specks of it folded from light steel go back to steel.
    seen = set()
    for y in range(H):
        for x in range(W):
            if (x, y) in seen or not px[x, y][3] or px[x, y][:3] != LILAC: continue
            piece, todo = {(x, y)}, [(x, y)]
            while todo:
                a = todo.pop()
                for d in N8:
                    q = (a[0] + d[0], a[1] + d[1])
                    if 0 <= q[0] < W and 0 <= q[1] < H and q not in piece and px[q][3] and px[q][:3] == LILAC: piece.add(q); todo.append(q)
            seen |= piece
            if len(piece) < 30:
                for p in piece: px[p] = STEEL + (255,)
    if i == 7:                    # PixelLab dropped the rim here: the blade's outer, lower-left edge, painted from pose 8
        x0, y0, x1, y1 = RIM_BOX
        rim = [(x, y) for y in range(y0, y1) for x in range(x0, x1) if px[x, y][3] and px[x, y][:3] == VIOLET
               and any(not px[x + a, y + b][3] or px[x + a, y + b][:3] == K for a, b in ((-1, 1), (-2, 2), (0, 2), (-2, 0)) if 0 <= x + a < W and 0 <= y + b < H)]
        for p in rim: px[p] = LILAC + (255,)
    f.save(HERE / f'p_{i}.png')
    frames.append(f)
    c = Counter(p[:3] for p in f.get_flattened_data() if p[3])
    px = f.load()
    lil = [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] == LILAC]
    bone = [(x, y) for y in range(45, H) for x in range(W) if px[x, y][3] and px[x, y][:3] == BONE and 40 <= x <= 90]
    lil = lil or [(0, 0)]
    print(i, name, 'bbox', f.getbbox(), len(c), 'colours', 'lilac centre', sum(p[0] for p in lil) // len(lil), sum(p[1] for p in lil) // len(lil),
          'x', min(p[0] for p in lil), max(p[0] for p in lil), 'y', min(p[1] for p in lil), max(p[1] for p in lil),
          'mask centre', sum(p[0] for p in bone) // max(1, len(bone)), sum(p[1] for p in bone) // max(1, len(bone)))

S = 3
rev = Image.new('RGBA', (W * S * 3 + 8, H * S * 3 + 8), (40, 40, 40, 255))
for i, f in enumerate(frames):
    x, y = (i % 3) * (W * S + 4), (i // 3) * (H * S + 4)
    rev.paste((0, 0, 0, 255), (x, y, x + W * S, y + H * S))
    rev.alpha_composite(f.resize((W * S, H * S), 0), (x, y))
rev.save(HERE / 'review.png')


def gif(seq, name):
    big = []
    for i in seq:
        bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(frames[i])
        big.append(bg.resize((W * 3, H * 3), 0).convert('P', palette=Image.ADAPTIVE))
    big[0].save(HERE / name, save_all=True, append_images=big[1:], duration=MS, loop=0)


gif((0, 1), 'idle.gif')
gif((1, 2, 3, 4), 'lift.gif')
gif((5, 6, 7, 8), 'slam.gif')
gif((0, 1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 8), 'cycle.gif')
