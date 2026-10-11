"""16 Kamaitachi: the user's ear outline carried to every other frame.

    python art/enemies/16_kamaitachi_ears.py SHEET.png BEFORE.png
        SHEET:  the sheet with the user's new front frame 0 (exported from the .aseprite); rewritten
        BEFORE: the sheet as it was before that edit (to see what they changed)

The user gave the black ears a white rim on the front frame (2026-10-10), so they show on the battle's
black. Here:
- the front's other two frames get the same pixels they changed, moved to where the head rides;
- every other view's ears (the black tufts above its head) get the same rim: each empty pixel beside an
  ear pixel turns white.
The sheet is 8 directions x 3 frames of 45x47."""
import sys
from PIL import Image
W, H = 45, 47
K, WHITE = (0, 0, 0, 255), (0xfc, 0xfc, 0xfc, 255)
# view: (first frame, the head's box, [ear boxes]) in the right-facing drawing; x1, y1 exclusive
VIEWS = {'DR': (3, (24, 6, 37, 21), [(24, 7, 37, 12)]),
         'R':  (6, (27, 8, 40, 23), [(30, 9, 36, 12)]),
         'UR': (9, (26, 5, 37, 20), [(27, 7, 32, 11)]),
         'U':  (12, (15, 3, 30, 20), [(15, 7, 19, 11), (26, 7, 30, 11)])}
MIRROR = {'UL': ('UR', 15), 'L': ('R', 18), 'DL': ('DR', 21)}
FRONT_RIDES = {1: (0, -1), 2: (0, 0)}             # where the front head sits in its frames 1 and 2 (16_kamaitachi_match.py)

def run(path, before):
    im = Image.open(path).convert('RGBA'); px = im.load(); old = Image.open(before).convert('RGBA').load()
    key = lambda p: (p[3], p[:3] if p[3] else 0)
    changed = [(x, y) for y in range(H) for x in range(W) if key(px[x, y]) != key(old[x, y])]
    for k, (dx, dy) in FRONT_RIDES.items():
        for (x, y) in changed: px[k * W + x + dx, y + dy] = px[x, y]
    def flipbox(b, flip): return (W - b[2], b[1], W - b[0], b[3]) if flip else b
    def offset(i, base, box):
        best = None
        for dy in range(-4, 5):
            for dx in range(-3, 4):
                bad = sum(1 for y in range(box[1], box[3]) for x in range(box[0], box[2])
                          if 0 <= x + dx < W and 0 <= y + dy < H and (px[base * W + x, y][3] > 0) != (px[i * W + x + dx, y + dy][3] > 0))
                if best is None or bad < best[0]: best = (bad, dx, dy)
        return best[1], best[2]
    plans = [(v, f0, head, ears, False) for v, (f0, head, ears) in VIEWS.items()]
    plans += [(v, f0, VIEWS[src][1], VIEWS[src][2], True) for v, (src, f0) in MIRROR.items()]
    offs = {f0 + k: offset(f0 + k, f0, flipbox(head, flip)) for v, f0, head, ears, flip in plans for k in range(3)}
    n = 0
    for v, f0, head, ears, flip in plans:
        for k in range(3):
            dx, dy = offs[f0 + k]; ox = (f0 + k) * W
            ear = {(x + dx, y + dy) for b in ears for bx in [flipbox(b, flip)] for y in range(bx[1], bx[3]) for x in range(bx[0], bx[2])
                   if 0 <= x + dx < W and 0 <= y + dy < H and px[ox + x + dx, y + dy] == K}
            for (x, y) in ear:
                for qx, qy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= qx < W and 0 <= qy < H and px[ox + qx, qy][3] == 0: px[ox + qx, qy] = WHITE; n += 1
    im.save(path)
    print('front pixels carried to its frames 1 and 2:', len(changed), '| rim pixels added on the other views:', n)

if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
