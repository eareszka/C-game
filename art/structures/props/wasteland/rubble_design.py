"""The wasteland's rubble, the props laid round its void pools (the user,
2026-10-27, the wasteland overhaul; the mock-up art/concept/wasteland/).

    python art/structures/props/wasteland/rubble_design.py

Grey rocks of the waste stone -- base 595965 and shade 34343e, a black line
round each and a crack, no lit tone (the bible's rock) -- a fallen stub of the
maze's wall in its courses, and a bone lying in the roster's bone. Each is
written to its own PNG, its cells' size, standing on the bottom row:

    rubble_pile.png     2x1 cells, the group's anchor: three rocks heaped
    rubble_boulder.png  1x1
    rubble_pebbles.png  1x1, lying
    rubble_stub.png     1x1, a fallen length of wall
    rubble_bone.png     1x1, lying
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
K = (0, 0, 0, 255)
BASE, SHADE = (0x59, 0x59, 0x65, 255), (0x34, 0x34, 0x3e, 255)
LIT = (0x97, 0x97, 0xaa, 255)                                  # the stub's lit course (waste stone)
BONE = {'l': (0xe8, 0xe0, 0xc0, 255), 'm': (0xb2, 0x96, 0x6a, 255), 'd': (0x8d, 0x6b, 0x4f, 255), 'K': K}


def rock(w, h, crack=True, seed=0):
    """An angular rock (after pixellab-out/waste-rubble-*; redrawn 2026-10-27 -- the first,
    round and unlit, sank into the dark floor): a block with its corners knocked off, its top
    face lit, its right side and foot in shade, a crack slanting down its front."""
    import random
    rr = random.Random(seed * 7 + w * 13 + h)
    big = 3 if w >= 9 else 2
    cut = {(0, 0): rr.randint(1, big), (1, 0): rr.randint(1, big), (0, 1): rr.randint(1, 2), (1, 1): 1}
    m = [[True] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            for (sx, sy), c in cut.items():
                dx = x if sx == 0 else w - 1 - x
                dy = y if sy == 0 else h - 1 - y
                if dx + dy < c:
                    m[y][x] = False
    top = max(2, h * 2 // 5)                                   # the top face's depth
    px = {}
    for y in range(h):
        for x in range(w):
            if not m[y][x]:
                continue
            ridge = top - (1 if x > w * .6 else 0)
            if y < ridge:
                c = LIT if x < w * .7 else BASE
            elif x >= w - 2 or y >= h - 1 or (x > w * .6 and y > h * .6):
                c = SHADE
            else:
                c = BASE
            px[(x + 1, y + 1)] = c
    for x in range(w):                                         # the edge where the top meets the front
        y = top - (1 if x > w * .6 else 0)
        if (x + 1, y + 1) in px and px[(x + 1, y + 1)] == BASE and x < w - 2:
            px[(x + 1, y + 1)] = BASE
    if crack and w >= 9:
        cx = w // 2 - 1
        for k in range(min(4, h - top - 1)):
            q = (cx + k + 1, top + 1 + k)
            if q in px:
                px[q] = K
    return px


def outline(px):
    out = dict(px)
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in px:
                out[(x + dx, y + dy)] = K
    return out


def place(canvas_w, canvas_h, parts):
    """parts [(pixels, x0, y0)] drawn back to front onto a clear canvas."""
    im = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    for px, x0, y0 in parts:
        for (x, y), c in outline(px).items():
            if 0 <= x0 + x < canvas_w and 0 <= y0 + y < canvas_h:
                im.putpixel((x0 + x, y0 + y), c)
    return im


def stub():
    """A broken length of wall: two courses of 6x4 blocks, its top broken off in steps, the
    top lit, the east side dark, a fallen block at its foot."""
    px = {}
    w, d = 10, 2
    tops = [0, 0, 0, 0, 0, 1, 1, 2, 3, 3]                      # how far down each column was broken
    for x in range(w):
        for y in range(tops[x], 8):
            row, off = y % 4, (3 if (y // 4) % 2 else 0)
            px[(x + 1, y + 1 + d)] = LIT if y == tops[x] else SHADE if (x + off) % 6 == 5 or row == 3 else BASE
    for k in range(1, d + 1):
        for x in range(w):
            if tops[x] == 0:
                px[(x + 1 + k, 1 + d - k)] = LIT
        for y in range(tops[-1], 8):
            px[(w + k, y + 1 + d - k)] = SHADE
    return px


def bone():
    """A skull and a long bone lying in the dust, in the roster's bone."""
    rows = ['..KKKKK.........',
            '.KllllmK........',
            'KllmmmmdK.......',
            'KlKKmKKdK.......',
            'KlKKmKKdK.......',
            '.KmmKmmK........',
            '..KdmdK.........',
            '...KKK..........',
            '......KK....KK..',
            '.....KlmKKKKlmK.',
            '.....KmllllllmdK',
            '.....KmdKKKKKmdK',
            '......KK.....KK.']
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != '.':
                im.putpixel((x, 16 - len(rows) - 1 + y), BONE[c])
    return im


def export():
    outs = {
        'rubble_pile': place(32, 16, [(rock(10, 8, seed=1), 2, 6), (rock(9, 7, seed=2), 19, 7),
                                      (rock(11, 7, seed=3), 9, 1), (rock(8, 6, seed=4), 12, 8)]),
        'rubble_boulder': place(16, 16, [(rock(13, 10, seed=5), 0, 4)]),
        'rubble_pebbles': place(16, 16, [(rock(6, 4, False, 6), 0, 9), (rock(6, 5, False, 7), 8, 4),
                                         (rock(5, 4, False, 8), 7, 10)]),
        'rubble_stub': place(16, 16, [(stub(), 0, 3), (rock(4, 3, False, 9), 10, 11)]),
        'rubble_bone': bone(),
    }
    for name, im in outs.items():
        im.save(os.path.join(HERE, name + '.png'))
        print('wrote', name, im.size)


if __name__ == '__main__':
    export()
