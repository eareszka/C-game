"""Asp's animation. PixelLab from its 47x42 NES still (pixellab/base.png, 64x64); the old sheet was that still in all
80 cells. Four views (the fight's tongue() / hiss_face: it holds the view it faced at the flick):
  D = the still (3/4 front), R = PixelLab's east view, U = its north view, L = R mirrored.
The 10 drawn frames (at 260 ms the sheet keeps KEEP: 0 2 4 7 8 -> 5 frames, the hiss on 4):
  0 rest  1-2 the tail rising  3-5 the tail tip pressed on its ear (it stops its ears against the charmer)
  6 the tail coming down  7 the mouth opening  8 the tongue fully out (breath_frame 8: the hiss leaves its tip)
  9 the tongue drawing back
Key poses by `edit` (tailkey2d / tonguekey2d, tailkeyr / tonguekeyr, tailkeyu), the moves by `animate --last` onto them;
the back view's tongue from a plain animate (tongueu, 04 held: 03 had a blob). The tongue is the game palette's red;
the still's near-black (14,32,22) is folded into black to keep 8 colours plus black.
Run: python -B art/enemies/anim/21_asp/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
RED = (183, 0, 0, 255)
IDLE = {'down': ['in_D', 'tailgo-d-01', 'tailgo-d-03', 'tailgo-d-04', 'tailgo-d-04', 'tailgo-d-04', 'tailgo-d-02',
                 'tonguego-d-01', 'tonguego-d-02', 'tonguego-d-03'],
        'right': ['in_R', 'tailgo-r-01', 'tailgo-r-03', 'tailgo-r-04', 'tailgo-r-04', 'tailgo-r-04', 'tailgo-r-02',
                  'tonguego-r-02', 'tonguego-r-03', 'tonguego-r-04'],
        'up': ['in_U', 'tailgo-u-01', 'tailgo-u-03', 'tailgo-u-04', 'tailgo-u-04', 'tailgo-u-04', 'tailgo-u-02',
               'tongueu-02', 'tongueu-04', 'tongueu-04']}
MS, HISS = 260, 4
KEEP = [0, 2, 4, 7, 8]   # the 260 ms rule (the user, 2026-11-18; bullets' cut): rest, tail rising, tail on the ear, mouth
                         # opening, tongue out -- of the 10 drawn below

def frames():
    P = [c for c in pt.palette_of(os.path.join(HERE, 'original_sprite.png')) if c != (14, 32, 22, 255)] + [RED]   # its near-black (9 px) goes to black: room for the tongue in 8 + black
    L = lambda n: pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', n + '.png')), P), keep=lambda q: q == RED)
    idle = {v: [L(n) for n in ns] for v, ns in IDLE.items()}
    def union(fs):
        bs = [f.getbbox() for f in fs]
        return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))
    boxes = {v: union(fs) for v, fs in idle.items()}
    W = max(b[2] - b[0] for b in boxes.values()); H = max(b[3] - b[1] for b in boxes.values())
    out = {}
    for v, fs in idle.items():
        b = boxes[v]; out[v] = []
        for f in fs:
            c = Image.new('RGBA', (W, H), pt.CLEAR); part = f.crop(b)
            c.paste(part, ((W - part.width) // 2, H - part.height), part); out[v].append(c)
    fix_up_tail(out['up']); [fix_down_eyes(f) for f in out['down'][1:7]]; [fix_right_eye(f) for f in out['right'][2:6]]
    return {v: [fs[i] for i in KEEP] for v, fs in out.items()}, W, H

# The user's review fixes (2026-11-18), on the cut frames:
GOLD = ((240, 188, 60, 255), (201, 164, 51, 255), (193, 138, 57, 255))
GREEN = (79, 166, 103, 255)

def gold_parts(fr):
    """The 8-connected gold patches of a frame, as pixel lists."""
    px = fr.load(); seen, parts = set(), []
    for y in range(fr.height):
        for x in range(fr.width):
            if px[x, y] not in GOLD or (x, y) in seen: continue
            comp, st = [], [(x, y)]; seen.add((x, y))
            while st:
                cx, cy = st.pop(); comp.append((cx, cy))
                for q in ((cx + dx, cy + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    if 0 <= q[0] < fr.width and 0 <= q[1] < fr.height and q not in seen and px[q] in GOLD: seen.add(q); st.append(q)
            parts.append(comp)
    return parts

# The back view's tail, drawn (the user: "idle ups tail should still have the same funky animation from front and
# left"; PixelLab drew the lifted tail as a second one, an arch, beside the real one). Frames 1-6 are frame 0 with its
# own tail, the upright on the left, cut off above the coils and drawn again as a thick tapering curve through these
# points (pixel coords in the cut frame): rising, over, the tip pressed to the side of the head (the ear) on 3-5 --
# bullets' ring fires on f3 -- and coming down. Light from the top left: the lower right half of it in the dark green.
UP_TAIL = {1: [(4.5, 30), (4.5, 20), (6.5, 12), (9.5, 7)],
           2: [(4.5, 30), (4.5, 18), (7.5, 9), (12.5, 4), (17.5, 4)],
           3: [(4.5, 30), (4.5, 17), (8, 7), (13.5, 3), (18.5, 4), (21, 8.5)],
           6: [(4.5, 30), (4.5, 21), (5.5, 14), (7.5, 10)]}
UP_TAIL[4] = UP_TAIL[5] = UP_TAIL[3]
DARK = (41, 99, 62, 255)

def draw_tail(fr, pts, r0=3.0, r1=1.4):
    import math
    segs = list(zip(pts, pts[1:])); total = sum(math.dist(a, b) for a, b in segs)
    def near(x, y):
        best, run = None, 0.0
        for (ax, ay), (bx, by) in segs:
            L = math.dist((ax, ay), (bx, by)); t = max(0, min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / (L * L)))
            cx, cy = ax + t * (bx - ax), ay + t * (by - ay); d = math.dist((x, y), (cx, cy))
            if best is None or d < best[0]: best = (d, x - cx, y - cy, (run + t * L) / total)
            run += L
        return best
    px = fr.load(); inside = {}
    for y in range(fr.height):
        for x in range(fr.width):
            d, ox, oy, u = near(x + .5, y + .5); r = r0 + (r1 - r0) * u
            if d <= r: inside[x, y] = DARK if (ox + oy) / 1.414 > 0.3 * r else GREEN
    for (x, y), c in inside.items(): px[x, y] = c
    for x, y in {(x + dx, y + dy) for x, y in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - set(inside):
        if 0 <= x < fr.width and 0 <= y < fr.height and not (y >= 31 and x < 9): px[x, y] = pt.BLACK

def fix_up_tail(fs):
    for i, pts in UP_TAIL.items():
        f = fs[0].copy(); px = f.load()
        for y in range(31):
            for x in range(10): px[x, y] = pt.CLEAR
        draw_tail(f, pts); fs[i] = f

def fix_down_eyes(fr):
    """Down frames 1-6 came back with open yellow eyes (a black column beside a gold one); frame 0's are closed black
    slits. Each small gold patch above the throat goes green, with the black beside it on its rows, and a 2-px slit
    is drawn on its bottom row, on its column and the next one toward the face's middle."""
    px = fr.load(); eyes = [c for c in gold_parts(fr) if len(c) <= 6]
    if not eyes: return
    mid = sum(x for c in eyes for x, _ in c) / sum(len(c) for c in eyes)
    for c in eyes:
        for x, y in c:
            px[x, y] = GREEN
            for dx in (-1, 1):
                q = (x + dx, y)
                if px[q] == pt.BLACK and all(px[q[0] + a, q[1] + b][3] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))): px[q] = GREEN
        x, y = max(c, key=lambda p: (p[1], -abs(p[0] - mid)))
        px[x, y] = pt.BLACK; px[x + (1 if x < mid else -1), y] = pt.BLACK

def fix_right_eye(fr):
    """'Gold blob forms around eye when tail is forward in right pose' (the user): on right frames 2-5 PixelLab
    painted a gold patch round the eye. It goes green, but for the one pixel just left of the eye (the gold eye
    pixel of the clean frames 0, 1 and 6). Its patch is the gold not joined to the throat (all above row 13)."""
    px = fr.load()
    for c in gold_parts(fr):
        if max(y for _, y in c) > 12: continue
        left = [(x, y) for x, y in c if px[x + 1, y] == pt.BLACK]
        keep = max(left, key=lambda p: (p[1], p[0])) if left else None
        for p in c:
            px[p] = GOLD[0] if p == keep else GREEN

def tongue_tip(fr, view):
    """The tongue's far end: its leftmost red px from the front (it points left), the rightmost from the side/back."""
    px = fr.load(); pts = [(x, y) for y in range(fr.height) for x in range(fr.width) if px[x, y] == RED]
    if not pts: return None
    return min(pts) if view == 'down' else max(pts)

def coils(fr):
    """The middle of the coiled heap: the centroid of the drawing's lower half."""
    px = fr.load(); b = fr.getbbox(); mid = (b[1] + b[3]) // 2
    pts = [(x, y) for y in range(mid, b[3]) for x in range(fr.width) if px[x, y][3]]
    return sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)

def gif(fs, ms, path):
    W, H = fs[0].size
    g = [Image.alpha_composite(Image.new('RGBA', (W, H), (24, 24, 32, 255)), f).convert('RGB').resize((W * 4, H * 4), Image.NEAREST) for f in fs]
    g[0].save(path, save_all=True, append_images=g[1:], duration=ms, loop=0, disposal=2)

if __name__ == '__main__':
    idle, W, H = frames(); gap = 4
    board = Image.new('RGBA', (len(KEEP) * (W + gap) + gap, 3 * (H + gap) + gap), (24, 24, 32, 255))
    for r, v in enumerate(('down', 'right', 'up')):
        for i, fr in enumerate(idle[v]): board.paste(fr, (gap + i * (W + gap), gap + r * (H + gap)), fr)
    rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
    board.resize((board.width * 4, board.height * 4), Image.NEAREST).save(os.path.join(rv, 'board.png'))
    for v in ('down', 'right', 'up'): gif(idle[v], MS, os.path.join(rv, 'idle_%s.gif' % v))
    off = lambda c: '(%.1f, %.1f)' % ((c[0] + 0.5 - W / 2) * 2, (c[1] + 0.5 - H / 2) * 2) if c else 'none'
    print('frame %dx%d' % (W, H))
    for v in ('down', 'right', 'up'):
        print('tongue tip', v, 'frame', HISS, off(tongue_tip(idle[v][HISS], v)), )
    print('coils (down, frame 0)', off(coils(idle['down'][0])))
    if '--install' in sys.argv:
        P = {v: {'idle': idle[v]} for v in ('down', 'right', 'up')}
        path = os.path.join(ROOT, 'assets/enemies/21_asp.png')
        pt.sheet(P, 'idle', path, W, H)
        print('21_asp.png', *pt.check_frames(path, len(KEEP), W, H), sep='\n  ')
    else:
        import tempfile
        t = os.path.join(tempfile.gettempdir(), '21_check.png')
        pt.sheet({v: {'idle': idle[v]} for v in ('down', 'right', 'up')}, 'idle', t, W, H)
        print('check', *pt.check_frames(t, len(KEEP), W, H), sep='\n  ')
