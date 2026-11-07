"""Paoxiao's animation (Stationary in phase 1; phase 2 waits eye-shut, the eye snaps open, it leaps at the player).
All PixelLab, on a 56x52 canvas. The user: "the animation for this sprite should make the eyeball very jarring" --
the flank eye rolls, darts and swells through the idle; in the warning it flickers wide open, jolting a pixel.
  views: right = its approved NES sprite (side); down = rotate's west-06 (it faces us), up = north-east-03 (its
         back) -- the rotate's labels didn't match what it drew; left = right mirrored
  idle (5 x 260 ms; frame 2 = the CRY, mouth wide -- Paoxiao::breathe throws its eye of bullets on it):
         pixellab/idle-VIEW-NN in IDLE[view] order
  alt  (phase 2 waiting, the flank eye shut): pixellab/idleshut-VIEW-NN in SHUT[view] order, the cry on 2 too
  flap (6): 0-3 the SPRINT (pixellab/sprint-VIEW-01..04; the user: "for the dashing phase the legs should look
         like they're sprinting"), 130 ms a pose; 4-5 the warning: the eye wide, jolted, flickering at 130 ms.
         (The first cut's 2-pose leap, leap-VIEW-NN, is no longer used.)
  The flank eye (the user: "for the 4 directions make sure the eyeball shape/size/look is consistent across
         all 4"): PixelLab's own eyes differed view to view, so every idle frame of every view gets the SAME
         drawn eye stamped over it -- an 11x6 squinting almond, the spawners' look (black outline, white, light-grey shade, grey
         iris, black pupil), at one spot a view (EYE_AT), its iris jerking a pixel frame to frame.
  Phase 2 (the user: "always faces forward and make sure its face is more readable"): PixelLab's eye-shut
         edit had greyed over the face, so the alt sheet is now the FRONT idle frames (clean face), the flank
         eye taken away (its eyes have left it), in every column.
Run: python -B art/enemies/anim/11_paoxiao/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W, H = 56, 52
VIEWS = ('down', 'right', 'up')
IDLE = {'down': [0, 4, 2, 3, 0], 'right': [0, 1, 2, 3, 4], 'up': [0, 1, 2, 3, 4]}
SHUT = {'down': [0, 3, 2, 4, 0], 'right': [0, 3, 2, 4, 0], 'up': [0, 1, 2, 3, 4]}
LEAP = {'down': [2, 3], 'right': [3, 2], 'up': [3, 4]}
EYE  = {'down': [(2, 1, -1), (3, -1, 0)], 'right': [(4, 1, -1), (3, -1, 1)], 'up': [(0, 1, -1), (1, -1, 0)]}   # (idle frame, dx, dy)

def palette():
    s = Image.open(os.path.join(HERE, 'original_sprite.png')).convert('RGBA')
    return sorted({s.getpixel((x, y)) for x in range(s.width) for y in range(s.height) if s.getpixel((x, y))[3] == 255})

def snap(im, pal):
    out = im.convert('RGBA').copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            p = px[x, y]
            if p[3] < 128: px[x, y] = (0, 0, 0, 0); continue
            px[x, y] = min(pal, key=lambda q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 + (q[2] - p[2]) ** 2)
    return out

import math
EYE_AT = {'down': (33.5, 27.0), 'right': (28.0, 27.5), 'up': (28.0, 27.5)}   # the eye's middle (float px); the
#   bullet table's numbers are these minus 0.5: down (33.0, 26.5), right/left/up (27.5, 27.0)
DART = [(0, 0), (-1, 0), (0, 0), (1, 0), (0, -1)]                         # the iris, idle frame by frame
BLACK, WHITE, SHADE, IRIS = (0, 0, 0, 255), (252, 252, 252, 255), (198, 204, 218, 255), (132, 134, 148, 255)

def stamp(im, cx, cy, dart, rx=5.6, ry=3.1):
    """The flank eye, squinting (the user: "the squinting shape instead of a full circle"): an almond."""
    out = im.copy(); px = out.load()
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            e = (dx / rx) ** 2 + (dy / ry) ** 2
            if e > 1.0: continue
            ri = math.hypot(dx - dart[0], dy - dart[1])
            edge = e > (1 - 1.0 / ry) ** 2
            px[x, y] = BLACK if edge else BLACK if ri <= 1.2 else IRIS if ri <= 2.3 else SHADE if dy > ry * 0.35 else WHITE
    return out

def clean_haunch(fr):
    """The side view's rump: PixelLab left a dark curl there that reads as an empty eye socket (the user: clean
    it up). Inner black/dark lines in that patch take the colour most of their neighbours have."""
    out = fr.copy(); px = out.load(); src = fr.load()
    for y in range(22, 35):
        for x in range(7, 22):
            p = src[x, y]
            if not p[3] or sum(p[:3]) > 300: continue
            nb = [src[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if any(q[3] == 0 for q in nb): continue                      # the silhouette's own outline stays
            light = [q for q in nb if sum(q[:3]) > 300]
            if light: px[x, y] = max(set(light), key=light.count)
    for _ in range(2):                                                  # a second pass for lines two pixels thick
        src2 = out.copy().load()
        for y in range(22, 35):
            for x in range(7, 22):
                p = src2[x, y]
                if not p[3] or sum(p[:3]) > 300: continue
                nb = [src2[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                if any(q[3] == 0 for q in nb): continue
                light = [q for q in nb if sum(q[:3]) > 300]
                if len(light) >= 2: px[x, y] = max(set(light), key=light.count)
    return out

def tidy(fr):
    """The user: "overall clean up the sprite in its entirety". PixelLab's frames carry speckle and stray bits:
    1. islands of under 4 opaque px (stray pixels off the body) go;
    2. a pixel no neighbour shares, sitting in a field one colour holds 5+ of its 8 neighbours, takes that colour
       (twice, so 2 px specks go too);
    3. the silhouette's edge is closed in black (the NES outline), skin-coloured hands and face included."""
    out = fr.copy(); px = out.load()
    seen = set()
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
                for q in comp: px[q] = (0, 0, 0, 0)
    for _ in range(2):
        src = out.copy().load()
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                p = src[x, y]
                if not p[3]: continue
                nb = [src[x + dx, y + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
                if any(q[3] == 0 for q in nb) or p in nb or p == BLACK: continue      # lines are drawn on purpose
                best = max(set(nb), key=nb.count)
                skin = lambda q: q[0] > 190 and q[0] > q[1] > q[2]
                if skin(best) or any(skin(q) for q in nb): continue                   # the face's features stay
                if nb.count(best) >= 5: px[x, y] = best
    src = out.copy().load()
    for y in range(H):
        for x in range(W):
            if not src[x, y][3]: continue
            edge = any(not (0 <= x + dx < W and 0 <= y + dy < H) or src[x + dx, y + dy][3] == 0 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge: px[x, y] = BLACK
    return out

def hold_back(fr, still):
    out = fr.copy(); out.paste((0, 0, 0, 0), (34, 8, W, H)); out.paste(still, (34, 8), still); return out

def no_eye_front(fr, clean):
    """The front view without its flank eye: the strip it hangs in taken from a frame without one."""
    out = fr.copy(); out.paste(clean.crop((34, 18, W, 35)), (34, 18)); return out

def jolt(im, dx, dy):
    out = Image.new('RGBA', im.size, (0, 0, 0, 0)); out.paste(im, (dx, dy), im); return out

def poses():
    pal = palette(); L = lambda n: snap(Image.open(os.path.join(HERE, 'pixellab', n)), pal)
    P = {}
    clean = L('idle-down-00.png')
    front = [tidy(no_eye_front(L('idle-down-%02d.png' % i), clean)) for i in IDLE['down']]
    # The front view's back half (hind legs, tail) scribbles differently every frame: hold it from the first.
    still = front[0].crop((34, 8, W, H))
    front = [front[0]] + [hold_back(fr, still) for fr in front[1:]]
    for v in VIEWS:
        raw = front if v == 'down' else [tidy(L('idle-%s-%02d.png' % (v, i))) for i in IDLE[v]]
        if v == 'right': raw = [clean_haunch(fr) for fr in raw]
        P[v] = {'idle': [stamp(fr, *EYE_AT[v], DART[k]) for k, fr in enumerate(raw)],
                'shut': front,
                'flap': [L('sprint-%s-%02d.png' % (v, i)) for i in range(1, 5)] +
                        [jolt(L('idle-%s-%02d.png' % (v, i)), dx, dy) for i, dx, dy in EYE[v]]}
    return P

def mirror(im): return im.transpose(Image.FLIP_LEFT_RIGHT)

def sheet(P, k, path):
    n = len(P['down'][k]); im = Image.new('RGBA', (W * 8 * n, H))
    for d, dn in enumerate(['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']):
        seq = P['down'][k] if dn == 'D' else P['up'][k] if dn == 'U' else P['right'][k] if dn in ('DR', 'R', 'UR') else [mirror(x) for x in P['right'][k]]
        if k == 'shut': seq = P['down'][k]                 # phase 2 always faces forward
        for i, fr in enumerate(seq): im.paste(fr, ((d * n + i) * W, 0))
    im.save(path)

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    P = poses(); gap = 4
    board = Image.new('RGBA', (16 * (W + gap) + gap, 3 * (H + gap) + gap), (40, 40, 40, 255))
    for r, v in enumerate(VIEWS):
        for c, fr in enumerate(P[v]['idle'] + P[v]['shut'] + P[v]['flap']): board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board.resize((board.width * 2, board.height * 2), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def install():
    P = poses(); d = os.path.join(ROOT, 'assets/enemies')
    sheet(P, 'idle', os.path.join(d, '11_paoxiao.png'))
    sheet(P, 'shut', os.path.join(d, '11_paoxiao_shut.png'))
    sheet(P, 'flap', os.path.join(d, '11_paoxiao_leap.png'))

if __name__ == '__main__':
    if '--install' in sys.argv: install()
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
