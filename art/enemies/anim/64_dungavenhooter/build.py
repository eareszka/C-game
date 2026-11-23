"""Dungavenhooter's 8-frame sheet (the user's approved 51x41 still; the slam the user placed, 2026-11-18). The user,
2026-11-18: "it should go from curled in frame 1 to extended and hitting the floor behind", then "have the body breath
instead of walk during that animation also have the curve not go as high", then "make it extend out less". The
impact: k-short-96 (short_key.py: the approved key k-slam-96 with its shaft's duplicate columns removed, 7 px less
reach); then "for the entire arch". f4: uncurl-03 (PixelLab animate base_96 -> k-slam-96) with 7 repeated rows of its
upright shaft dropped (shorten.py, deletion only) to the key's tail length; f5: short8-06 (PixelLab animate base_96
(the curled still) -> k-short-96, 8 frames) -- slanted, no exact repeats to drop, its free tail ~3 px over the key's. The class plays f3-f6 (fewer as its HP drains), all four on ONE body (the
key's, x < CUT) with each frame's tail laid over it, the body breathing in on f4-f5 (rows above SPLIT up 1 px,
the bottom torso row repeated, the feet planted):
  0 rest, the ball bobbing (PL slam-01)  1 rest (the still)  2 as 0  3 CURLED (the still's tail)
  4 unrolling, the ball at head height (uncurl-03, shortened)  5 out behind, low, the ball at the tip (short8-06)
  6 IMPACT (k-short-96)  7 the dust cloud (slam-07).  Loose dust specks cleared (delete only).
Front only: D DR R UR U the drawing, UL L DL its mirror.  Run: python -B art/enemies/anim/64_dungavenhooter/build.py [--install]"""
import os, sys
from PIL import Image, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common')); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import pixtools as pt
import enemy_sheet as es
import shorten
PL = os.path.join(HERE, 'pixellab')
SHEET = os.path.join(ROOT, 'assets/enemies/redraws/64_dungavenhooter.png')
MS = 260
FRAMES = ['slam-01', 'slam-00', 'slam-01', 'slam-00', 'uncurl-03', 'short8-06', 'k-short-96', 'slam-07']
HOLD, KEY = tuple(range(8)), 6      # every frame on the key's body (the old model's: the 51x41 still's, 2 px apart)
CUT, SPLIT = 50, 63                  # the key's body is x < CUT; its feet are rows >= SPLIT (planted)
BREATH = {4: 1, 5: 1}                # px the body rises
SHORTEN = {'uncurl-03': ('up', 7),       # repeated px dropped from the tail (shorten.py), to the key's tail length:
           'slam-07': ('out', 7)}        # rows of an upright shaft, columns of one out behind
LIGHT = (178, 158, 92)                   # the dust's one flat tone (its lighter DUST tone made a 4th gold shade)
AIRDUST = {'uncurl-03', 'short8-06'}     # their dust arcs (hanging off the ball like a second tail) and loose specks cleared above the ground pile
DUST, PILE_TOP = (206, 190, 130), 63
GREY = {(151, 151, 170), (220, 240, 255), (89, 89, 101)}

def frames():
    P = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    fs = [pt.snap(Image.open(os.path.join(PL, n + '.png')), P) for n in FRAMES]
    for i, n in enumerate(FRAMES):
        if n in SHORTEN:
            g = max(blobs(fs[i], lambda q: q in GREY), key=len); how, k = SHORTEN[n]
            if how == 'up': fs[i], d = shorten.up(fs[i], k, 47, max(y for _, y in g) + 1)
            else: fs[i], d = shorten.out(fs[i], k, 51, min(x for x, _ in g) - 1)
            assert d == k, (n, d)
    for n, f in zip(FRAMES, fs):
        if n in AIRDUST:
            for c in blobs(f, lambda q: q == DUST):
                if len(c) > 20:
                    for x, y in c:
                        if y < PILE_TOP: f.putpixel((x, y), pt.CLEAR)
            for c in sorted(blobs(f, lambda q: True), key=len)[:-1]:      # loose specks: all but the creature itself
                for x, y in c:
                    if y < PILE_TOP: f.putpixel((x, y), pt.CLEAR)
            for c in blobs(f, lambda q: q not in GREY and q != (0, 0, 0)):  # specks stuck to the ball's spikes
                p = f.load(); empty = sum(1 for x, y in c for dx in (-1, 0, 1) for dy in (-1, 0, 1) if not p[x + dx, y + dy][3])
                if len(c) <= 3 and min(y for _, y in c) < 40 and empty >= 3 * len(c):      # sticking out, not inside the ball
                    print('speck cleared', n, c)
                    for x, y in c: f.putpixel((x, y), pt.CLEAR)
    hold(fs)
    box = (8, 9, 88, 69)                 # 80x60, as before
    for n, f in zip(FRAMES, fs):
        b = f.getbbox()
        if not (b[0] >= box[0] and b[1] >= box[1] and b[2] <= box[2] and b[3] <= box[3]): print("clipped by the 80x60 box:", n, b)
    return [f.crop(box) for f in fs], box

def hold(fs):
    """One body for the fight's frames: the key's body; each frame (lined up with it by the best vertical match of
    its front half) gives only its px right of CUT or above the body's top edge -- the tail, the ball, the dust."""
    key = fs[KEY]; W, H = key.size
    body = key.copy(); body.paste(pt.CLEAR, (CUT, 0, W, H)); bp = body.load()
    top = [next((y for y in range(H) if bp[x, y][3]), H) for x in range(W)]
    def lined(f):
        diff = lambda dy: sum(1 for y in range(40, 70) for x in range(CUT - 10) if key.getpixel((x, y)) != f.getpixel((x, y + dy)))
        dy = min((-2, -1, 0, 1, 2), key=diff); a = Image.new('RGBA', (W, H), pt.CLEAR); a.alpha_composite(f, (0, -dy)); return a
    for i in HOLD:
        a = lined(fs[i]); ap = a.load(); out = body.copy(); op = out.load()
        take = {(x, y) for y in range(H) for x in range(W) if ap[x, y][3] and (x >= CUT or y < top[x])}
        extra = set()
        for c in blobs_of(take):                 # only pieces joined to the tail (not the frame's own head edge)
            if any(x >= CUT for x, _ in c):
                for x, y in c: op[x, y] = ap[x, y]; extra.add((x, y))
        fs[i] = breathe(nes(out, extra), BREATH.get(i, 0))

def nes(f, extra):
    """The PixelLab parts (the tail, the ball, the dust: `extra`) brought to the old still's NES look; the body untouched.
    The dust one flat tone; specks of fewer than 4 px gone; a lone px (no same colour round it) takes its neighbours'
    colour; the edge closed in black, 1 px. The ball's greys are left as drawn (its centre is the bullets' point)."""
    p = f.load(); W, H = f.size
    paint = lambda q: q[3] and q[:3] != (0, 0, 0) and q[:3] not in GREY
    for x, y in extra:
        if p[x, y][:3] == DUST and y >= 48: p[x, y] = LIGHT + (255,)
    for c in blobs_of(extra):
        if len(c) < 4:
            for q in c: p[q] = pt.CLEAR
    for _ in range(2):
        src = f.copy().load()
        for x, y in extra:
            c = src[x, y]
            if not paint(c): continue
            nb = [src[x + dx, y + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy) and 0 <= x + dx < W and 0 <= y + dy < H]
            if c in nb: continue
            best = max({q for q in nb if paint(q)}, key=nb.count, default=None)
            if best is not None and nb.count(best) >= 3: p[x, y] = best
    src = f.copy().load()
    for x, y in extra:
        if paint(src[x, y]) and any(not (0 <= x + dx < W and 0 <= y + dy < H) or not src[x + dx, y + dy][3]
                                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            p[x, y] = pt.BLACK
    return f

def breathe(f, n):
    """The rows above SPLIT up n px, the last of them repeated to fill the gap: the body swells, the feet stay."""
    if not n: return f
    W, H = f.size; out = f.copy(); out.paste(pt.CLEAR, (0, 0, W, SPLIT))
    out.paste(f.crop((0, n, W, SPLIT)), (0, 0))
    for k in range(1, n + 1): out.paste(f.crop((0, SPLIT - 1, W, SPLIT)), (0, SPLIT - k))
    return out

def blobs(f, keep):
    """8-connected groups of the px whose colour passes keep(rgb)."""
    p = f.load(); W, H = f.size
    return blobs_of({(x, y) for y in range(H) for x in range(W) if p[x, y][3] and keep(p[x, y][:3])})

def blobs_of(g):
    g = set(g); out = []
    while g:
        st = [g.pop()]; c = []
        while st:
            q = st.pop(); c.append(q)
            for r in ((q[0] + dx, q[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                if r in g: g.remove(r); st.append(r)
        out.append(c)
    return out

def ball(f):
    """The ball's middle: the centre of the largest group of grey px."""
    g = max(blobs(f, lambda q: q in GREY), key=len)
    return (min(x for x, _ in g) + max(x for x, _ in g)) / 2, (min(y for _, y in g) + max(y for _, y in g)) / 2

def full_sheet(fs):
    W, H = fs[0].size; sh = Image.new('RGBA', (8 * len(fs) * W, H), pt.CLEAR)
    for d in range(8):
        for i, f in enumerate(fs): sh.paste(f.transpose(Image.FLIP_LEFT_RIGHT) if d in (5, 6, 7) else f, ((d * len(fs) + i) * W, 0))
    return sh

def on_bg(f): return Image.alpha_composite(Image.new('RGBA', f.size, (24, 24, 32, 255)), f)

def gif(fs, path, s=4):
    g = [on_bg(f).convert('RGB').resize((f.width * s, f.height * s), Image.NEAREST) for f in fs]
    g[0].save(path, save_all=True, append_images=g[1:], duration=MS, loop=0, disposal=1, optimize=False)
    n = Image.open(path).n_frames; back = []
    for i in range(n):
        r = Image.open(path); r.seek(i); r.load(); back.append(r.convert('RGB'))
    assert n == len(g) and all(ImageChops.difference(back[i - 1], back[i]).getbbox() for i in range(1, n)), (path, n)
    return n

if __name__ == '__main__':
    fs, box = frames(); W, H = fs[0].size
    rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
    gap = 3; st = Image.new('RGBA', (len(fs) * (W + gap) + gap, H + 2 * gap), (24, 24, 32, 255))
    for i, f in enumerate(fs): st.alpha_composite(f, (gap + i * (W + gap), gap))
    st.resize((st.width * 3, st.height * 3), Image.NEAREST).save(os.path.join(rv, 'strip_8.png'))
    print('slam gif (f3-f6, as the fight plays it) frames', gif(fs[3:7], os.path.join(rv, 'slam_260.gif')))
    print('all 8 gif frames', gif(fs, os.path.join(rv, 'all8_260.gif')))
    t = os.path.join(rv, 'check.png'); full_sheet(fs).save(t)
    print(*pt.check_frames(t, len(fs), W, H, views=(('D', 0),)), sep=chr(10)); os.remove(t)
    off = lambda p: '(%+.0f,%+.0f)' % ((p[0] + .5 - W / 2) * 2, (p[1] + .5 - H / 2) * 2)
    print('frame %dx%d, box' % (W, H), box)
    for i, f in enumerate(fs):
        b = ball(f); print('f%d ball' % i, 'art (%.1f,%.1f) %s' % (*b, off(b)))
    bs = [ball(f) for f in fs[3:7]]
    print('fight loop steps (px) f3>f4>f5>f6>f3:', ['%.1f' % ((bs[i][0] - bs[i - 1][0]) ** 2 + (bs[i][1] - bs[i - 1][1]) ** 2) ** .5 for i in (1, 2, 3, 0)])
    if '--install' in sys.argv:
        sh = full_sheet(fs); sh.save(SHEET)
        es.pack(sh, SHEET[:-4] + '.aseprite', len(fs), False); es.built(SHEET); os.utime(SHEET, None)
