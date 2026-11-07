"""Shared helpers for the PixelLab animation builds (art/enemies/anim/NN_name/build.py).
  snap(im, pal)     PixelLab colours to the nearest of the sprite's own; alpha < 128 clear
  palette_of(path)  the opaque colours of an image
  tidy(im, strong)  the clean-up pass the user asked for on Paoxiao ("clean up the sprite in its entirety"):
                    islands < 4 px go; a lone speck takes the colour 5+ of its 8 neighbours share (never black
                    lines, never next to skin -- faces); the silhouette's edge closed in black.
                    strong=True also flattens pixels only one neighbour shares (PixelLab's mottled shading into
                    clean patches; for skin-coloured bodies like Qiqirn's, where 'next to skin' can't be the guard)
  jolt(im, dx, dy)  the frame moved a few px (chaotic movement)
  mirror(im)
  sheet(P, k, path, W, H, front_only=False)  8 columns D DR R UR U UL L DL x n frames: down/up their own,
                    the side view in DR R UR, mirrored in UL L DL; front_only puts the down view everywhere
  check_frames(path, n, W, H)  tools/enemy_style.py's check() on every frame of every drawn view"""
import os, sys
from PIL import Image
BLACK = (0, 0, 0, 255)
CLEAR = (0, 0, 0, 0)

def palette_of(path):
    s = Image.open(path).convert('RGBA')
    return sorted({s.getpixel((x, y)) for x in range(s.width) for y in range(s.height) if s.getpixel((x, y))[3] == 255})

def snap(im, pal):
    out = im.convert('RGBA').copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            p = px[x, y]
            if p[3] < 128: px[x, y] = CLEAR; continue
            px[x, y] = min(pal, key=lambda q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 + (q[2] - p[2]) ** 2)
    return out

def skin(q): return q[3] and q[0] > 190 and q[0] > q[1] > q[2] and q[0] - q[2] > 60

def tidy(fr, keep=lambda q: False, strong=False):
    W, H = fr.size; out = fr.copy(); px = out.load(); seen = set()
    for y in range(H):
        for x in range(W):
            if not px[x, y][3] or (x, y) in seen: continue
            comp, st = [], [(x, y)]; seen.add((x, y))
            while st:
                cx, cy = st.pop(); comp.append((cx, cy))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        q = (cx + dx, cy + dy)
                        if 0 <= q[0] < W and 0 <= q[1] < H and q not in seen and px[q][3]: seen.add(q); st.append(q)
            if len(comp) < 4:
                for q in comp: px[q] = CLEAR
    for _ in range(2):
        src = out.copy().load()
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                p = src[x, y]
                if not p[3] or p == BLACK or keep(p): continue
                nb = [src[x + dx, y + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
                if any(q[3] == 0 for q in nb) or nb.count(p) > (1 if strong else 0): continue
                if not strong and any(skin(q) or keep(q) for q in nb): continue
                if strong and any(q == BLACK for q in nb) and nb.count(p) == 0 and skin(p): continue   # a face feature's edge
                best = max(set(q for q in nb if q != BLACK), key=nb.count, default=None)
                if best is not None and nb.count(best) >= 5: px[x, y] = best
    src = out.copy().load()
    for y in range(H):
        for x in range(W):
            if src[x, y][3] and any(not (0 <= x + dx < W and 0 <= y + dy < H) or src[x + dx, y + dy][3] == 0
                                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = BLACK
    return out

def jolt(im, dx, dy):
    out = Image.new('RGBA', im.size, CLEAR); out.paste(im, (dx, dy), im); return out

def mirror(im): return im.transpose(Image.FLIP_LEFT_RIGHT)

def sheet(P, k, path, W, H, front_only=False):
    n = len(P['down'][k]); im = Image.new('RGBA', (W * 8 * n, H))
    for d, dn in enumerate(['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']):
        if front_only: seq = P['down'][k]
        else: seq = P['down'][k] if dn == 'D' else P['up'][k] if dn == 'U' else P['right'][k] if dn in ('DR', 'R', 'UR') else [mirror(x) for x in P['right'][k]]
        for i, fr in enumerate(seq): im.paste(fr, ((d * n + i) * W, 0))
    im.save(path)

def check_frames(path, n, W, H, views=(('down', 0), ('right', 2), ('up', 4))):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    sys.path.insert(0, os.path.join(root, 'tools'))
    import enemy_style as es
    im = Image.open(path).convert('RGBA'); lines = []
    for name, d in views:
        row = []
        for f in range(n):
            m, bad = es.check(im.crop(((d * n + f) * W, 0, (d * n + f) * W + W, H)))
            row.append('%d:%s' % (f, '; '.join(b[1] for b in bad if b[0] in ('FAIL', 'WARN')) or 'ok'))
        lines.append('%-5s %s' % (name, ' | '.join(row)))
    return lines
