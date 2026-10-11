"""16 Kamaitachi, half as big again: its own drawing enlarged, not redrawn.

    python art/enemies/16_kamaitachi_grow.py art/enemies/16_kamaitachi_small.png assets/enemies/16_kamaitachi.png
        (16_kamaitachi_small.png is the 30x31 sheet 16_kamaitachi.txt builds; then tools/enemy_sheet.py pack ... 3)

The user (2026-10-10): larger than it was -- twice the size was too big, so one and a half times. Each
30x31 frame of the old sheet becomes 45x47: tripled by Scale3x (a pixel becomes nine, its corners and edges
taking the neighbours' colour where they agree, so diagonals and curves stay smooth), then halved, each
2x2 block taking its commonest colour. No colour is added. Then the outline is thinned back to 1 px
(SPRITE_STYLE.md, Outline) -- of two black pixels side by side, the one with fill on its far side takes
that fill's colour -- and the parts that had no outline get one (rim)."""
import sys
from PIL import Image
FW, FH = 30, 31
K = (0, 0, 0, 255); T = (0, 0, 0, 0)

def grown(fr):
    """fr at 1.5x: Scale3x, then every 2x2 block's commonest colour (black, then any colour, before nothing)."""
    w, h = fr.size; s = fr.load()
    g = lambda x, y: s[x, y] if 0 <= x < w and 0 <= y < h and s[x, y][3] else T
    big = {}
    for y in range(h):
        for x in range(w):
            A, B, C, D, E, F, G, Hh, I = (g(x + dx, y + dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1))
            e = [E] * 9
            if B != Hh and D != F:
                e[0] = D if D == B else E
                e[1] = B if (D == B and E != C) or (B == F and E != A) else E
                e[2] = F if B == F else E
                e[3] = D if (D == B and E != G) or (D == Hh and E != A) else E
                e[5] = F if (B == F and E != I) or (Hh == F and E != C) else E
                e[6] = D if D == Hh else E
                e[7] = Hh if (D == Hh and E != I) or (Hh == F and E != G) else E
                e[8] = F if Hh == F else E
            for k in range(9): big[(3 * x + k % 3, 3 * y + k // 3)] = e[k]
    W2, H2 = (3 * w + 1) // 2, (3 * h + 1) // 2
    out = Image.new('RGBA', (W2, H2), T); o = out.load()
    for y in range(H2):
        for x in range(W2):
            four = [big.get((2 * x + i, 2 * y + j), T) for j in (0, 1) for i in (0, 1)]
            o[x, y] = max(set(four), key=lambda c: (four.count(c), c == K, c != T))
    return out

def thin(im):
    w, h = im.size; px = im.load()
    g = lambda x, y: px[x, y] if 0 <= x < w and 0 <= y < h else T
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        gone = []
        for y in range(h):
            for x in range(w):
                if px[x, y] != K: continue
                near, far = g(x - dx, y - dy), g(x + dx, y + dy)
                if near == K and far != K and far != T: gone.append((x, y, far))     # the inner of a pair: becomes the fill beyond it
        for x, y, c in gone:
            if g(x - dx, y - dy) == K: px[x, y] = c
    return im

def rim(im):
    """A 1-px black line round whatever of the silhouette has none (the whirlwind, the sickles): SPRITE_STYLE.md's
    outline, unseen on the battle's black."""
    w, h = im.size; px = im.load()
    add = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] == 0 and any(
        0 <= x + dx < w and 0 <= y + dy < h and px[x + dx, y + dy][3] and px[x + dx, y + dy] != K for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for p in add: px[p] = K
    return im

if __name__ == '__main__':
    old = Image.open(sys.argv[1]).convert('RGBA'); n = old.width // FW
    frames = [rim(thin(grown(old.crop((i * FW, 0, (i + 1) * FW, FH))))) for i in range(n)]
    w, h = frames[0].size
    out = Image.new('RGBA', (n * w, h), T)
    for i, f in enumerate(frames): out.paste(f, (i * w, 0))
    out.save(sys.argv[2])
    cols = {p[:3] for p in out.getdata() if p[3]}
    print(out.size, 'frame', (w, h), 'colours', len(cols), 'same as before:', cols == {p[:3] for p in old.getdata() if p[3]})
