"""Enemy 23 Olgoi-Khorkhoi, its body ringed like an earthworm, as the death worm is drawn (the user, 2026-10-19:
"update the texture of body ... match the mongolian death worm illustrations online more").

From the master as it was (art/_backup/23_before_rings_20261019/23_olgoi_khorkhoi_frame0_ground.aseprite): the arch's
body is drawn again by the first frame's tube without its beads (a smooth edge); the back keeps the user's hand-drawn
shape; the maw, petals, spines and feelers stay their pixels, over it. Then, over the whole body (the user: "make sure
the shading is consistent throughout ... matches the bible and pixellab", art/direction/approved_enemy_study/
STYLE_BRIEF.md): one shading by form, the arch's tone rule on every body pixel (lit where the tube faces up, left and
us, dark where it turns under), and a ring every PERIOD px along the spine, bowed a little across it (CURVE): a
one-pixel black separation line between two segments -- no lighter ridge, the bible has no repeated skin texture --
and where a ring meets the edge the outline steps in a pixel, so the rings read in the silhouette too. Interior black
comes to about 10 % (the bible's 9.35-14.49 %).

    python art/enemies/23_olgoi_khorkhoi_rings.py look OUT.png   # a 4x board: before, after
    python art/enemies/23_olgoi_khorkhoi_rings.py                # write 23_olgoi_khorkhoi_frame0_ground (the master)
"""
from pathlib import Path
import importlib, json, math, sys
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(HERE)]
import first_frame as ff
A = importlib.import_module('23_olgoi_khorkhoi_pose_first')
PAL, W, H = A.PAL, A.W, A.H
BEFORE = ROOT / 'art/_backup/23_before_rings_20261019/23_olgoi_khorkhoi_frame0_ground.aseprite'
MASTER = HERE / '23_olgoi_khorkhoi_frame0_ground'
PERIOD, CURVE = 8.0, 0.2
LIT = (0.12, 0.55)                                   # the tone rule's dark and light thresholds: an even light band down the lit side
MIN_BAND = 150                                       # a light band smaller than this many px is a patch, not a band
NOTCH_R = 10.0                                       # a ring steps the outline in only where the body is at least this thick
TAIL_R = (8.0, 15.5)                                 # the back thins evenly from the leg (15.5) to off the screen (8)
BACK = lambda p: p[0] >= 102 and p[1] >= 53          # the user's hand-drawn back, in the master before the rings


def spine0():
    """The whole body's spine as drawn at rest: the back's course as fitted to the user's shape, thinning evenly
    (no steps, so the outline stays steady down to the thin end), and the arch as thick as its beads were on average.
    Returns the spine and where the arch starts on it."""
    n = len(A.TAIL)
    pts = A.TAIL + [A.SPINE[n]]
    d = [0.0]
    for a, b in zip(pts, pts[1:]): d.append(d[-1] + math.dist(a[:2], b[:2]))
    lo, hi = TAIL_R
    tail = [(x, y, lo + (hi - lo) * d[i] / d[-1]) for i, (x, y, r) in enumerate(A.TAIL)]
    arch = [(x, y, r - A.DEPTH / 2) for x, y, r in A.SPINE[n:]]
    dense = [tuple(q[:3]) for q in ff.path(tail + arch[:1])][:-1][::4]   # the back every ~4 px, so a wave bends it smoothly
    sp, n = dense + arch, len(dense)
    return elbow(sp, n), n


def slack(spine, at=None, near=1e9):
    """How much rounder than the body each bend of a spine is: the least (turning radius - body radius) along it,
    from samples 3 apart. Below 0 the body folds on the inside of the bend (the "cranked" look)."""
    S = ff.path(spine)
    worst = 1e9
    for k in range(3, len(S) - 3):
        a, b, c = S[k - 3][:2], S[k][:2], S[k + 3][:2]
        ab, bc, ca = math.dist(a, b), math.dist(b, c), math.dist(c, a)
        cross = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        if cross < 1e-6 or at and math.dist(b, at) > near: continue
        worst = min(worst, ab * bc * ca / (2 * cross) - S[k][2])
    return worst


ELBOW = ((132, 72), 32.0)                            # the bend from the leg down into the back, and how far round it is rounded


def elbow(sp, n, need=3.0):
    """The bend where the leg turns into the back, rounded: the spine points within ELBOW of it averaged with their
    neighbours (place and thickness) until every bend there is at least `need` px rounder than the body. The rest of
    the spine -- the arch, the back's run off the screen -- is left as it is."""
    sp = [list(p) for p in sp]
    at, near = ELBOW
    movable = [k for k in range(1, len(sp) - 1) if math.dist(sp[k][:2], at) <= near]
    for _ in range(80):
        if slack([tuple(p) for p in sp], at, near) >= need: break
        new = [p[:] for p in sp]
        for k in movable:
            for c in range(3): new[k][c] = 0.25 * sp[k - 1][c] + 0.5 * sp[k][c] + 0.25 * sp[k + 1][c]
        sp = new
    return [tuple(p) for p in sp]


def run(spine=None, n=None):
    """A spine as the tube samples it: (x, y, r, s), s counted from where the back meets the arch (point n)."""
    if spine is None: spine, n = spine0()
    S = ff.path(spine)                                              # one smooth path through the whole body
    s0 = min(S, key=lambda q: (q[0] - spine[n][0]) ** 2 + (q[1] - spine[n][1]) ** 2)[3]
    return [(x, y, r, s - s0) for x, y, r, s in S]


def body(spine=None, n=None):
    """The body drawn on a spine, whole: the tube (every pixel belongs to its nearest spine sample, inside if within
    that sample's radius), toned by form, the rings, the notches where it is thick, and its outline -- open past the
    canvas's right edge, where it runs on out of view. {(x, y): letter}, in the first frame's coordinates."""
    S = np.array(run(spine, n))
    xs, ys, rs, ss = S[:, 0], S[:, 1], S[:, 2], S[:, 3]
    k = np.arange(len(xs)); hi, lo = np.minimum(k + 6, len(xs) - 1), np.maximum(k - 6, 0)
    tx, ty = xs[hi] - xs[lo], ys[hi] - ys[lo]                       # the direction along it, over +-6 samples: the bands turn smoothly
    n = np.hypot(tx, ty); n[n == 0] = 1; tx, ty = tx / n, ty / n
    x0, x1 = max(0, int((xs - rs).min()) - 1), min(W - 1, int((xs + rs).max()) + 1)
    y0, y1 = max(0, int((ys - rs).min()) - 1), min(H - 1, int((ys + rs).max()) + 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
    gx, gy = gx.ravel(), gy.ravel()
    d2 = (gx[:, None] - xs[None, :]) ** 2 + (gy[:, None] - ys[None, :]) ** 2
    i = d2.argmin(1)
    inside = np.sqrt(d2[np.arange(len(i)), i]) <= rs[i]
    gx, gy, i = gx[inside], gy[inside], i[inside]
    v = np.clip(((gx - xs[i]) * -ty[i] + (gy - ys[i]) * tx[i]) / rs[i], -1, 1)
    lit = -ty[i] * v * A.LIGHT3[0] + tx[i] * v * A.LIGHT3[1] + np.sqrt(1 - v * v) * A.LIGHT3[2]
    along = ss[i] + CURVE * rs[i] * v * v
    out, at, rad = {}, {}, {}
    for k in range(len(gx)):
        p = (int(gx[k]), int(gy[k]))
        out[p] = 'L' if lit[k] > LIT[1] else 'D' if lit[k] < LIT[0] else 'M'
        at[p], rad[p] = along[k], rs[i[k]]
    inner = set(out)
    edge = lambda p: any(0 <= p[0] + dx < W and (p[0] + dx, p[1] + dy) not in inner for dx, dy in ff.N4)
    for p in list(out):                                             # specks: a tone with at most one neighbour of its own goes
        near = [out.get((p[0] + dx, p[1] + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
        if near.count(out[p]) <= 1:
            out[p] = max(('L', 'M', 'D'), key=near.count)
    todo = {p for p, c in out.items() if c == 'L'}                  # a light band too short to read as one (a patch): mid
    while todo:
        st = [todo.pop()]; comp = set(st)
        while st:
            q = st.pop()
            for dx in (-2, -1, 0, 1, 2):                            # joined across a ring line
                for dy in (-2, -1, 0, 1, 2):
                    r = (q[0] + dx, q[1] + dy)
                    if r in todo: todo.remove(r); comp.add(r); st.append(r)
        if len(comp) < MIN_BAND:
            for q in comp: out[q] = 'M'
    crease = set()
    for p, a in at.items():                                         # a ring where the segment count steps by one between neighbours
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            q = (p[0] + dx, p[1] + dy)
            if q in at and abs(at[q] - a) < PERIOD / 2 and math.floor(at[q] / PERIOD) > math.floor(a / PERIOD):
                crease.add(p); break
    for p in crease: out[p] = 'K'
    for p in [p for p in crease if edge(p) and rad[p] >= NOTCH_R]:  # the notch: a thick ring steps the edge in a pixel
        del out[p]
    for p, c in list(out.items()):                                  # the outline
        if c != 'K' and any(0 <= p[0] + dx < W and (p[0] + dx, p[1] + dy) not in out for dx, dy in ff.N4): out[p] = 'K'
    for p, c in list(out.items()):                                  # lone tone pixels: to their neighbours' tone
        if c == 'K': continue
        nb = [out.get((p[0] + dx, p[1] + dy)) for dx, dy in ff.N4]
        tones = [q for q in nb if q in ('L', 'M', 'D')]
        if len(tones) >= 2 and c not in tones: out[p] = max(set(tones), key=tones.count)
    return out


def parts():
    """The maw, petals, spines and feelers as the user's first frame has them (from the master before the rings)."""
    before = ff.read(BEFORE, PAL)
    _, _, owner = A.layer(A.parts()[0])
    body_at = lambda p: owner.get(p) == 'body' or (p not in owner and (BACK(p) or p[1] > 48))
    return before, {p: c for p, c in before.items() if not body_at(p)}


def compose(bod, over):
    """A body with parts over it, the body's outline closed again where a part left a gap (not past the right edge)."""
    out = dict(bod); out.update(over)
    for p, c in list(out.items()):
        if p in bod and p not in over and c != 'K' and any(
                0 <= p[0] + dx < W and (p[0] + dx, p[1] + dy) not in out for dx, dy in ff.N4): out[p] = 'K'
    return out


def rings():
    before, over = parts()
    return before, compose(body(), over)


def board(before, after, path):
    pics = []
    for g in (before, after):
        im = ff.image(g, PAL, W, H); bg = Image.new('RGBA', im.size, (90, 96, 110, 255)); bg.alpha_composite(im)
        pics.append(bg.resize((W * 4, H * 4), Image.NEAREST))
    b = Image.new('RGBA', (W * 4, H * 8 + 8), (30, 30, 36, 255))
    b.paste(pics[0], (0, 0)); b.paste(pics[1], (0, H * 4 + 8))
    b.save(path)


if __name__ == '__main__':
    before, after = rings()
    print('pieces', ff.pieces(set(after)), flush=True)
    for line in ff.checks(after, PAL, W, H, open_ok=lambda p, c: before.get(p) == c and not BACK(p),
                          cap=224, max_colours=24, right_open=True):
        print(' ', line, flush=True)
    if sys.argv[1:2] == ['look']:
        board(before, after, sys.argv[2])
    else:
        if MASTER.with_suffix('.aseprite').exists(): MASTER.with_suffix('.aseprite').unlink()
        MASTER.with_suffix('.json').write_text(json.dumps({f'{x},{y}': c for (x, y), c in after.items()}))
        ff.draft(after, PAL, W, H, MASTER)
