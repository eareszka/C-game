"""83 redo: where each shot leaves from, on each frame: mouth, two wingtips, three feet -> the ART tables in src/enemies.cpp.
Prints the C++ rows and writes points.png (points on every frame, for checking by eye).

    python art/enemies/pixellab/83_beast_of_barrisdale/redo/anim/measure.py
"""
from pathlib import Path
from collections import deque
from PIL import Image
HERE = Path(__file__).resolve().parent
K = (0, 0, 0)
SALMON, RIB, PALE, MOUTH = (0xec, 0x84, 0x76), (0xb6, 0x43, 0x3d), (0xf0, 0xb8, 0x90), (0x42, 0x16, 0x18)
GREY = {(0x84, 0x86, 0x94), (0x59, 0x59, 0x65), (0x47, 0x47, 0x51)}


def clusters(ps):
    left, out = set(ps), []
    while left:
        s = left.pop(); c = [s]; q = deque([s])
        while q:
            x, y = q.popleft()
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    n = (x + a, y + b)
                    if n in left: left.discard(n); c.append(n); q.append(n)
        out.append(c)
    return out


def points(im, wrapped=False):
    px = {(x, y): im.getpixel((x, y))[:3] for y in range(65) for x in range(100) if im.getpixel((x, y))[3]}
    H = max(y for x, y in px)
    warm = [p for p, c in px.items() if c in (SALMON, RIB)]
    # feet: the warm clumps in the bottom rows, by x; merged ones are split by the bottom row's gaps
    low = [p for p in warm + [p for p, c in px.items() if c == PALE and p[1] > H - 10] if p[1] >= H - 7]
    feet = sorted(((min(x for x, y in c) + max(x for x, y in c)) / 2, max(y for x, y in c)) for c in clusters(low) if len(c) >= 3)
    # the mouth: reds and dark red by the head, left of the body
    mouth = [p for p, c in px.items() if c in (RIB, MOUTH) and p[0] < 40 and p[1] > 30]
    m = (sum(x for x, y in mouth) / len(mouth), sum(y for x, y in mouth) / len(mouth)) if mouth else None
    # wingtips: highest point left and right of the wings' split
    w = [p for p, c in px.items() if (c in (SALMON, RIB) or c in GREY) and p[1] < 40]
    mid = (min(x for x, y in w) + max(x for x, y in w)) / 2
    tips = [min((p for p in w if (p[0] < mid) == side), key=lambda p: (p[1], p[0])) for side in (True, False)]
    return m, tips, feet


if __name__ == '__main__':
    S, G = 4, (0x6f, 0x9e, 0x5c, 255)
    seqs = [('idle', [0, 2, 4, 6, 8]), ('fly', [0, 2, 4, 6, 8]), ('block', [0, 1, 2, 3])]
    b = Image.new('RGBA', (100 * S * 5, 65 * S * 3), G)
    for r, (n, idx) in enumerate(seqs):
        for k, i in enumerate(idx):
            im = Image.open(HERE / f'{n}_{i}.png').convert('RGBA')
            m, t, f = points(im)
            print(n, i, 'mouth', m and (round(m[0]), round(m[1])), 'wings', t, 'feet', [(round(x), y) for x, y in f])
            big = im.resize((100 * S, 65 * S), 0)
            ox, oy = k * 100 * S, r * 65 * S
            b.alpha_composite(big, (ox, oy))
            def dot(p, c):
                for a in range(-3, 4):
                    for d in range(-3, 4):
                        b.putpixel((min(ox + int(p[0] * S) + 2 + a, b.width - 1), min(oy + int(p[1] * S) + 2 + d, b.height - 1)), c)
            if m: dot(m, (255, 255, 0, 255))
            for p in t: dot(p, (0, 255, 255, 255))
            for p in f: dot(p, (255, 0, 255, 255))
    b.save(HERE / 'points.png')
