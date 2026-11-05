"""Read what the game actually loads (ENEMY_SHEETS), cut each enemy's first view, measure its drawing style."""
import os, re, math, sys
from collections import Counter, deque
from PIL import Image
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def read(p):
    return open(os.path.join(ROOT, p), encoding='utf-8').read()


def table(path, start):
    s = read(path)
    i = s.index(start)
    return s[i:s.index('};', i)]


def split_top(s):
    out, depth, cur, q = [], 0, '', False
    for ch in s:
        if ch == '"':
            q = not q
        if not q:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            elif ch == ',' and depth == 0:
                out.append(cur.strip())
                cur = ''
                continue
        cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


FIELDS = ['path', 'loop', 'frames', 'rows', 'flap', 'alt', 'log', 'log_frames', 'log_rows', 'marks', 'step_ms', 'parts']


def parse_sheets():
    src = table('src/battle.cpp', 'ENEMY_SHEETS[] = {').split('{', 1)[1]
    src = re.sub(r'//[^\n]*', '', src)
    entries, depth, cur = [], 0, ''
    for ch in src:
        if ch == '{':
            depth += 1
            if depth == 1:
                cur = ''
                continue
        if ch == '}':
            depth -= 1
            if depth == 0:
                entries.append(cur)
                continue
        if depth >= 1:
            cur += ch
    sheets = []
    for e in entries:
        vals = split_top(e)
        d = dict(path=None, loop='', frames=3, rows=False, flap=None, alt=None, log=None,
                 log_frames=1, log_rows=1, marks=None, step_ms=0, parts=None)
        for k, v in zip(FIELDS, vals):
            if v == 'nullptr':
                d[k] = None
            elif v.startswith('"'):
                d[k] = v.strip('"')
            elif k == 'rows':
                d[k] = v == 'true'
            elif k == 'loop':
                d[k] = v
            else:
                d[k] = int(v)
        sheets.append(d)
    return sheets


def names_tiers():
    tiers = re.findall(r'T_([A-Z0-9]+)', table('include/enemy.h', 'ENEMY_TIERS[] = {'))
    names = re.findall(r'"([^"]+)"', table('src/main.cpp', 'ENEMY_NAMES[] = {'))
    return names, tiers


def cut(im, frames, rows, frame=0, d=0):
    W, H = im.size
    if rows:
        fw, fh = W // frames, H // 8
        return im.crop((frame * fw, d * fh, (frame + 1) * fw, (d + 1) * fh))
    fw, fh = W // (8 * frames), H
    return im.crop(((d * frames + frame) * fw, 0, (d * frames + frame + 1) * fw, fh))


def lab_l(rgb):
    def f(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    y = 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2])
    return 116 * (y ** (1 / 3)) - 16 if y > 0.008856 else 903.3 * y


def to_lab(rgb):
    def f(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = f(rgb[0]), f(rgb[1]), f(rgb[2])
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    def g2(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return (116 * g2(y) - 16, 500 * (g2(x) - g2(y)), 200 * (g2(y) - g2(z)))


def chroma(rgb):
    L, a, b = to_lab(rgb)
    return math.hypot(a, b)


def components(mask_key):
    """4-connected components of equal value; value -1 = transparent, skipped. Returns list of (value, area, pixels)."""
    h, w = mask_key.shape
    seen = np.zeros((h, w), bool)
    out = []
    for y in range(h):
        for x in range(w):
            v = mask_key[y, x]
            if v < 0 or seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            pix = []
            while q:
                cy, cx = q.popleft()
                pix.append((cy, cx))
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and mask_key[ny, nx] == v:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            out.append((int(v), len(pix), pix))
    return out


def measure(view):
    bb = view.getbbox()
    a = np.array(view.crop(bb) if bb else view)
    h, w = a.shape[:2]
    alpha = a[..., 3]
    opq = alpha > 0
    partial = int(((alpha > 0) & (alpha < 255)).sum())
    n = int(opq.sum())
    key = (a[..., 0].astype(np.int64) << 16) | (a[..., 1].astype(np.int64) << 8) | a[..., 2].astype(np.int64)
    key[~opq] = -1
    cols = Counter(key[opq].tolist())
    rgb_of = lambda k: ((k >> 16) & 255, (k >> 8) & 255, k & 255)

    # silhouette edge: opaque with a transparent / outside 4-neighbour
    pad = np.pad(opq, 1, constant_values=False)
    inner = pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    edge = opq & ~inner
    black = key == 0
    Lmap = np.zeros((h, w))
    for k in cols:
        Lmap[key == k] = lab_l(rgb_of(k))
    nearblack = opq & (Lmap < 12)
    edge_n = int(edge.sum())
    outline_black = float((edge & black).sum()) / max(1, edge_n)
    outline_dark = float((edge & nearblack).sum()) / max(1, edge_n)
    interior_black = float((opq & black & ~edge).sum()) / max(1, n)
    # second ring: pixels one step inside the outline; black here = doubled/thick line
    pad2 = np.pad(inner, 1, constant_values=False)
    inner2 = pad2[:-2, 1:-1] & pad2[2:, 1:-1] & pad2[1:-1, :-2] & pad2[1:-1, 2:]
    ring2 = inner & ~inner2
    thick = float((ring2 & black).sum()) / max(1, int(ring2.sum()))
    edge_cols = Counter(key[edge].tolist())

    # colour clusters
    comp = components(key)
    fill = [c for c in comp if c[0] != 0]
    fill_area = sum(c[1] for c in fill) or 1
    tiny = sum(c[1] for c in fill if c[1] <= 2) / fill_area
    small = sum(c[1] for c in fill if c[1] <= 6) / fill_area
    n_clusters_per100 = 100.0 * len(fill) / fill_area
    mean_cluster = fill_area / max(1, len(fill))
    biggest = max((c[1] for c in fill), default=0) / fill_area
    # 2x2 checkerboards (dither)
    k = key
    chk = ((k[:-1, :-1] == k[1:, 1:]) & (k[:-1, 1:] == k[1:, :-1]) & (k[:-1, :-1] != k[:-1, 1:]) &
           (k[:-1, :-1] >= 0) & (k[:-1, 1:] >= 0))
    dither = float(chk.sum()) / max(1, n)
    # boundary density between differing fills (neither black nor transparent)
    def pairs(p, q):
        ok = (p > 0) & (q > 0)
        return ok, ok & (p != q)
    okh, dh = pairs(k[:, :-1], k[:, 1:])
    okv, dv = pairs(k[:-1, :], k[1:, :])
    boundary = float(dh.sum() + dv.sum()) / max(1, int(okh.sum() + okv.sum()))
    # how big are the steps in L* across fill boundaries (soft = small steps = rendered)
    steps = []
    for (p, q, d) in ((Lmap[:, :-1], Lmap[:, 1:], dh), (Lmap[:-1, :], Lmap[1:, :], dv)):
        steps.append(np.abs(p - q)[d])
    steps = np.concatenate(steps) if steps else np.array([])
    step_med = float(np.median(steps)) if steps.size else 0.0
    soft = float((steps < 12).mean()) if steps.size else 0.0

    # horizontal/vertical run lengths; resample fingerprint
    def edges_mod(m):
        ch = np.zeros(m, dtype=np.int64)
        return ch
    changes_x = np.array([(k[:, x] != k[:, x + 1]).sum() for x in range(w - 1)]) if w > 1 else np.zeros(0)
    changes_y = np.array([(k[y, :] != k[y + 1, :]).sum() for y in range(h - 1)]) if h > 1 else np.zeros(0)
    def mod_share(ch, m):
        if ch.sum() == 0:
            return 0.0
        tot = np.zeros(m)
        for i, c in enumerate(ch):
            tot[i % m] += c
        return float(tot.min() / tot.sum() * m)      # 1 = even; 0 = a residue with no changes (upscale fingerprint)
    resample2 = min(mod_share(changes_x, 2), mod_share(changes_y, 2))
    resample3 = min(mod_share(changes_x, 3), mod_share(changes_y, 3))
    # share of 1px-wide fill runs
    runs = []
    for row in k:
        cur, l = None, 0
        for v in row:
            if v == cur:
                l += 1
            else:
                if cur is not None and cur > 0:
                    runs.append(l)
                cur, l = v, 1
        if cur is not None and cur > 0:
            runs.append(l)
    runs = np.array(runs) if runs else np.array([1])
    one_px = float((runs == 1).mean())

    # luminosity / chroma on the body (excluding pure black)
    body = [(c, ct) for c, ct in cols.items() if c != 0]
    body_n = sum(ct for _, ct in body) or 1
    mean_L = sum(lab_l(rgb_of(c)) * ct for c, ct in body) / body_n
    mean_C = sum(chroma(rgb_of(c)) * ct for c, ct in body) / body_n
    Ls = [lab_l(rgb_of(c)) for c, _ in body]
    # shades per material: group colours by hue bucket (grey separate), count those with >=2 % of body
    groups = {}
    for c, ct in body:
        rgb = rgb_of(c)
        L_, a_, b_ = to_lab(rgb)
        C_ = math.hypot(a_, b_)
        hue = 'grey' if C_ < 10 else int(((math.degrees(math.atan2(b_, a_)) + 360) % 360) // 40)
        groups.setdefault(hue, []).append((ct, c))
    shades = max((sum(1 for ct, _ in v if ct / body_n >= 0.02) for v in groups.values()), default=0)
    significant = sum(1 for _, ct in body if ct / body_n >= 0.02)
    # near-identical pairs: colours closer than dE 8 (read as a smear, not a step)
    keys = [c for c, _ in body]
    labs = [to_lab(rgb_of(c)) for c in keys]
    close = 0
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            if math.dist(labs[i], labs[j]) < 8:
                close += 1
    # dark share: how much of the body is close to the arena's pure black
    dark = float(sum(ct for c, ct in body if lab_l(rgb_of(c)) < 22)) / body_n
    # silhouette busy-ness: perimeter^2 / area
    perim = float((opq[:, :-1] != opq[:, 1:]).sum() + (opq[:-1, :] != opq[1:, :]).sum()) + 2 * (opq[0, :].sum() + opq[:, 0].sum())
    compact = perim * perim / (4 * math.pi * max(1, n))

    return dict(w=w, h=h, opaque=n, partial=partial, colours=len(cols), body_colours=len(body),
                significant=significant, max_shades=shades, near_dupes=close,
                outline_black=round(outline_black, 3), outline_dark=round(outline_dark, 3),
                interior_black=round(interior_black, 3), thick=round(thick, 3),
                black_total=round(float(black.sum()) / max(1, n), 3),
                edge_top=[('#%06x' % c, round(ct / max(1, edge_n), 3)) for c, ct in edge_cols.most_common(3)],
                tiny=round(tiny, 3), small=round(small, 3), clusters_per100=round(n_clusters_per100, 2),
                mean_cluster=round(mean_cluster, 1), biggest=round(biggest, 3), dither=round(dither, 4),
                boundary=round(boundary, 3), step_med=round(step_med, 1), soft=round(soft, 3),
                resample2=round(resample2, 2), resample3=round(resample3, 2), one_px=round(one_px, 3),
                mean_L=round(mean_L, 1), mean_C=round(mean_C, 1), L_lo=round(min(Ls), 1) if Ls else 0,
                L_hi=round(max(Ls), 1) if Ls else 0, dark=round(dark, 3), compact=round(compact, 1),
                top_cols=[('#%06x' % c, round(ct / max(1, n), 3)) for c, ct in cols.most_common(10)])


def load_all():
    sheets = parse_sheets()
    names, tiers = names_tiers()
    rows = []
    for i, s in enumerate(sheets):
        p = os.path.join(ROOT, s['path'])
        im = Image.open(p).convert('RGBA')
        v = cut(im, s['frames'], s['rows'])
        rows.append(dict(id=i, name=names[i], tier=tiers[i], sheet=s, view=v, im_size=im.size))
    return rows
