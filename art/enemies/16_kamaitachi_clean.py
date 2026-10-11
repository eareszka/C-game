"""16 Kamaitachi: take out the dead pixels the enlarging left (the user: "dead pixels during some frames").

    python art/enemies/16_kamaitachi_clean.py SHEET.png

In every frame (8 directions x 3 frames of 45x47):
- a hole -- one empty pixel boxed in on all four sides, in the whirlwind or the sickles -- is filled with
  the colour most of its neighbours have: on the battle's black it showed as a black dot, in a different
  place each frame;
- a loose piece of three pixels or fewer, touching nothing (the black scrap off the side view's nose), goes;
- a lone coloured pixel with only black or nothing round it, below the ermine (not the ears' rim), goes;
- on the two back-3/4 views, which have no face, a lone black pixel inside the white goes white."""
import sys
from collections import Counter
from PIL import Image
W, H, ERMINE = 45, 47, 20                          # rows above ERMINE are the ermine (and its ears' one-pixel rim)
K, WHITE, T = (0, 0, 0, 255), (0xfc, 0xfc, 0xfc, 255), (0, 0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1)); N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
FACELESS = (9, 10, 11, 15, 16, 17)                 # UR and UL frames

def run(path):
    im = Image.open(path).convert('RGBA'); px = im.load(); n = Counter()
    for i in range(im.width // W):
        ox = i * W
        g = lambda x, y: px[ox + x, y] if 0 <= x < W and 0 <= y < H else T
        inside = [(x, y) for y in range(H) for x in range(W) if g(x, y)[3]]
        # loose pieces
        seen = set(); comps = []
        for p in inside:
            if p in seen: continue
            c, todo = {p}, [p]
            while todo:
                x, y = todo.pop()
                for dx, dy in N8:
                    q = (x + dx, y + dy)
                    if g(*q)[3] and q not in c: c.add(q); todo.append(q)
            seen |= c; comps.append(c)
        comps.sort(key=len, reverse=True)
        for c in comps[1:]:
            if len(c) <= 3:
                for (x, y) in c: px[ox + x, y] = T
                n['loose'] += len(c)
        # holes
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                if g(x, y)[3] == 0 and all(g(x + dx, y + dy)[3] for dx, dy in N4):
                    px[ox + x, y] = Counter(g(x + dx, y + dy) for dx, dy in N4).most_common(1)[0][0]; n['holes'] += 1
        # lone coloured pixels below the ermine
        for y in range(ERMINE, H):
            for x in range(W):
                c = g(x, y)
                if c[3] and c != K and all(g(x + dx, y + dy) in (K, T) or g(x + dx, y + dy)[3] == 0 for dx, dy in N4):
                    px[ox + x, y] = K if any(g(x + dx, y + dy) == K for dx, dy in N4) else T; n['specks'] += 1
        if i in FACELESS:
            for y in range(1, H - 1):
                for x in range(1, W - 1):
                    if g(x, y) == K and all(g(x + dx, y + dy) == WHITE for dx, dy in N4): px[ox + x, y] = WHITE; n['dots'] += 1
    im.save(path)
    print(dict(n))

if __name__ == '__main__':
    run(sys.argv[1])
