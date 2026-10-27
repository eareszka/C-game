"""The wasteland's mini volcanoes, the props that stand where its dead trees did
(the user, 2026-10-27: "red stands should be like mini volcanos", then "make
volcanoes larger/denser"; the mock-up art/concept/wasteland/).

    python art/structures/props/wasteland/volcano_design.py

A broad red cone, slopes flaring to the foot, a notched black crater at the top
and a bite out of one slope, in four sizes. The objects' rule: the red ramp
(ec8476 light, sparse and high on the left and on the crater's left lip;
b70000 most of it; 7c0a1b massed low and down the right, and the crater's
throat) and one black line round it. Each is written to its own PNG, its cells'
size, the cone standing on the bottom row and centred across it:

    volcano_big.png    2x2 cells, the grove's anchor
    volcano_mid.png    2x2
    volcano_small.png  2x1
    volcano_tiny.png   1x1
"""
import os, random
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
RED = {'l': (0xec, 0x84, 0x76, 255), 'm': (0xb7, 0x00, 0x00, 255), 'd': (0x7c, 0x0a, 0x1b, 255),
       'K': (0, 0, 0, 255)}
# name: cone width, height, crater width, seed, cells across, cells down
SIZES = {'big': (29, 24, 9, 1, 2, 2), 'mid': (25, 20, 7, 2, 2, 2),
         'small': (21, 13, 6, 3, 2, 1), 'tiny': (13, 11, 4, 4, 1, 1)}
GULLIES = (-0.38, 0.08)                           # where each runs down, across the slope -1..1


def cone(vw, vh, cw, seed):
    """The cone as rows of letters (l m d K, '.' clear), its line included: slopes curving
    out to a broad skirt, their edges broken by crags, gullies run down from the crater's lip
    with a lit ridge beside each, the crater an open ring at the top (after the PixelLab
    drafts, pixellab-out/waste-volcano-*; redrawn 2026-10-27 -- the first were flat
    triangles in the world)."""
    rr = random.Random(seed)
    w, h = vw + 2, vh + 2
    cx = w / 2
    m = [[False] * w for _ in range(h)]
    half = []
    for y in range(vh):
        t = y / (vh - 1)
        hw = cw / 2 + (vw / 2 - cw / 2) * t ** 2.0              # concave: steep high, a broad skirt
        if 2 < y < vh - 2 and rr.random() < 0.3:
            hw -= 1                                            # a crag in the slope
        half.append(hw)
        for x in range(w):
            if abs(x + .5 - cx) <= hw:
                m[y + 1][x] = True
    g = [['.'] * w for _ in range(h)]
    for y in range(1, h - 1):
        hw = half[y - 1]
        for x in range(w):
            if not m[y][x]:
                continue
            u = (x + .5 - cx) / max(hw, 1)
            c = 'd' if u > .45 or y >= h - 2 else 'm'
            if x + .5 - (cx - hw) < 1.6 and y < h - 4:
                c = 'l'                                        # the lit flank, a band down the left edge
            if vw >= 19 and 3 < y < 3 + (vh * 2) // 3:
                for gu in GULLIES:                             # a gully, its ridge lit on the left
                    gx = cx + gu * hw
                    if abs(x + .5 - gx) < .5:
                        c = 'd'
                    elif gu < 0 and -1.5 < x + .5 - gx < -.5:
                        c = 'l'
            g[y][x] = c
    ring = cw / 2                                              # the crater: lip lit on the left, throat black
    for y in (1, 2, 3):
        for x in range(w):
            dx = x + .5 - cx
            if not m[y][x]:
                continue
            if y < 3 and abs(dx) < ring - 1.2:
                g[y][x] = 'K'
            elif y == 1 or (y == 2 and abs(dx) >= ring - 1.2) or (y == 3 and abs(dx) < ring - .5):
                g[y][x] = 'l' if dx < 0 else 'd'
    for y in range(h):                                         # the line round it
        for x in range(w):
            if not m[y][x] and any(0 <= x + dx < w and 0 <= y + dy < h and m[y + dy][x + dx]
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 'K'
    return g


def export(name):
    vw, vh, cw, seed, cx, cy = SIZES[name]
    g = cone(vw, vh, cw, seed)
    W, H = cx * 16, cy * 16
    gh, gw = len(g), len(g[0])
    assert gw <= W and gh <= H, name
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    x0, y0 = (W - gw) // 2, H - gh
    for y in range(gh):
        for x in range(gw):
            if g[y][x] != '.':
                im.putpixel((x0 + x, y0 + y), RED[g[y][x]])
    out = os.path.join(HERE, 'volcano_%s.png' % name)
    im.save(out)
    return out


if __name__ == '__main__':
    for n in SIZES:
        print('wrote', export(n))
