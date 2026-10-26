"""Paint a PixelLab draft's silhouette to the overworld bible's object rule.

    python tools/prop_paint.py DRAFT.png OUT.png --size 32x48 --ramp foliage [--height 46] [--ribs 3]

PixelLab is asked for the shape; the tones are laid here, so a prop always
keeps the objects' rule (OVERWORLD_STYLE.md "Objects"): one ramp placed by
form -- the mid tone over most of it, the dark massed low and on the right,
the light sparse and high on the left -- flat fills, a 1px black line round the
whole silhouette. The draft's alpha is the silhouette; it is scaled (by area,
never resampled colours) to --height rows, stood on the canvas's bottom row
but one and centred across it. --ribs N lays a dark rib every N columns up
each limb, as the saguaro's are. Writes OUT.png and prints the shares of each
tone so the light can be held to the bible's 2-3%.
"""
import argparse
from PIL import Image

RAMPS = {   # tools/overworld_style.py MATERIALS -- light, mid, dark
    'foliage': ('05c43a', '058f3a', '235436'),
    'rock':    ('b29e5c', '887000', '493712'),
    'bark':    ('605028', '463422', '2d230c'),
    'bone':    ('e8e0c0', 'b2966a', '8d6b4f'),
    'stone':   ('c6ccda', '9797aa', '595965'),
    'wood':    ('967448', '785830', '493712'),
}


def silhouette(path, h):
    im = Image.open(path).convert('RGBA')
    box = im.getchannel('A').point(lambda a: 255 if a > 127 else 0).getbbox()
    a = im.getchannel('A').crop(box)
    w = max(1, round(a.width * h / a.height))
    a = a.resize((w, h), Image.BOX)
    m = [[a.getpixel((x, y)) > 110 for x in range(w)] for y in range(h)]
    # a nub the scaling left -- a pixel held on by one side -- is not part of the shape
    for _ in range(2):
        for y in range(h):
            for x in range(w):
                if m[y][x] and sum(0 <= x + dx < w and 0 <= y + dy < h and m[y + dy][x + dx]
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) <= 1:
                    m[y][x] = False
    return m


def paint(mask, ribs=0):
    h, w = len(mask), len(mask[0])
    g = [['.' if not mask[y][x] else 'm' for x in range(w)] for y in range(h)]
    on = lambda x, y: 0 <= x < w and 0 <= y < h and mask[y][x]

    def reach(x, y, dx, dy):                             # how far in from the edge that way
        n = 0
        while on(x + dx * (n + 1), y + dy * (n + 1)):
            n += 1
        return n
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                continue
            dl, dr, du, dd = reach(x, y, -1, 0), reach(x, y, 1, 0), reach(x, y, 0, -1), reach(x, y, 0, 1)
            across, up = dl + dr + 1, du + dd + 1
            if up < across and up <= 8:
                # a limb lying along: lit along its top if high, its underside in shade
                if dd == 0 and up >= 3:
                    g[y][x] = 'd'
                elif du == 0 and up >= 4 and y < h * 0.3:
                    g[y][x] = 'l'
                continue
            # a limb standing up: shade down its right, lit down its left high, ribs between
            if across >= 3 and (dr == 0 or (across >= 7 and dr <= across // 5)):
                g[y][x] = 'd'
            elif ribs and 6 <= across <= 12 and dl % ribs == ribs - 1 and dl > 1 and dr > 1:
                g[y][x] = 'd'
            elif across >= 3 and dl == (1 if across >= 6 else 0) and (y < h * 0.3 or du == 0):
                g[y][x] = 'l'
    # a rib runs on through a joint: where an arm meets the trunk the row is too wide to place
    # ribs by, so a rib broken there is carried straight across from its rows above to below
    if ribs:
        for x in range(w):
            rows = [y for y in range(h) if g[y][x] == 'd' and on(x - 1, y) and on(x + 1, y)
                    and g[y][x - 1] != 'd' and g[y][x + 1] != 'd']
            for ya, yb in zip(rows, rows[1:]):
                if 1 < yb - ya <= 12 and all(on(x, y) for y in range(ya, yb)):
                    for y in range(ya + 1, yb):
                        if g[y][x] == 'm':
                            g[y][x] = 'd'
    # flat fills: a lone pixel walled in by one other tone takes that tone
    for _ in range(2):
        for y in range(h):
            for x in range(w):
                if g[y][x] == '.':
                    continue
                n = [g[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                     if 0 <= x + dx < w and 0 <= y + dy < h and g[y + dy][x + dx] != '.']
                same = sum(c == g[y][x] for c in n)
                if same == 0 and n:
                    g[y][x] = max(set(n), key=n.count)
                elif same == 1 and len(n) == 4 and g[y][x] == 'd' and n.count('m') == 3 and not ribs:
                    g[y][x] = 'm'
    # the lowest rows in shade: massed low
    for y in range(h - max(2, h // 12), h):
        for x in range(w):
            if g[y][x] == 'm':
                g[y][x] = 'd'
    return g


def columns(W, H, cols, ramp='foliage', ground=None):
    """A cluster of upright limbs -- an organ pipe, a cholla's stems -- drawn back to front from
    cols [(x0, x1, top)], each standing on the ground row (H - 2 unless given): a black line
    round each, so where a nearer one stands before a farther one the line parts them; its
    top rounded, lit down its left in its upper third and across its cap, its right in shade,
    a rib up the middle of one five wide or more, its foot in shade. Returns the canvas rows."""
    ground = H - 2 if ground is None else ground
    g = [['.'] * W for _ in range(H)]
    for x0, x1, top in cols:
        n = x1 - x0 + 1
        for y in range(top - 1, ground + 2):
            for x in range(x0 - 1, x1 + 2):
                cap = y < top + 1 and (x < x0 + 1 or x > x1 - 1)        # rounded shoulders
                ring = x in (x0 - 1, x1 + 1) or y in (top - 1, ground + 1) or (y == top and x in (x0, x1))
                if 0 <= x < W and 0 <= y < H and not (cap and ring and y == top - 1):
                    g[y][x] = 'K'
        for y in range(top, ground + 1):
            for x in range(x0, x1 + 1):
                if y == top and x in (x0, x1):
                    continue
                if y >= ground - 1:
                    c = 'd'
                elif x == x1 or (n >= 5 and x == x0 + n // 2 + 1):
                    c = 'd'
                elif x == x0 and y < top + (ground - top) // 4 + 1:
                    c = 'l'
                else:
                    c = 'm'
                g[y][x] = c
    return g


def blobs(W, H, parts, ramp='foliage'):
    """A thing made of rounded parts -- a cholla's joints, a pear's pads, boulders in a pile --
    drawn back to front from parts [(cx, cy, rx, ry, degrees)]: each an ellipse turned by its
    angle, a black line round it, so a nearer part is parted from the one behind; lit at its
    upper left, its lower right in shade, the rest the mid tone. Returns the canvas rows."""
    import math
    g = [['.'] * W for _ in range(H)]
    for cx, cy, rx, ry, deg in parts:
        a = math.radians(deg)
        def uv(x, y):
            dx, dy = x - cx, y - cy
            return ((dx * math.cos(a) + dy * math.sin(a)) / rx, (-dx * math.sin(a) + dy * math.cos(a)) / ry)
        inside = lambda x, y: sum(t * t for t in uv(x, y)) <= 1.0
        body = {(x, y) for y in range(H) for x in range(W) if inside(x, y)}
        for x, y in body:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in body and 0 <= q[0] < W and 0 <= q[1] < H:
                    g[q[1]][q[0]] = 'K'
        for x, y in body:
            dx, dy = (x - cx) / rx, (y - cy) / ry          # on the screen, whatever the part's turn
            if dx + dy > 0.55 or dy > 0.6:
                c = 'd'
            elif dx + dy < -1.0:
                c = 'l'
            else:
                c = 'm'
            g[y][x] = c
    return g


def voxels(W, H, base, solid, tone=None, pieces=None):
    """A rock given as a solid -- a set of unit cells (x, d, z), x across, d back, z up -- drawn
    in the houses' projection (entrance_shapes.oblique) through a Scene, so the depth test
    and the black lines are the buildings' own. Each cell shows the faces nothing covers:
    its top the light tone, its south face the mid, its east face the dark -- the three
    planes, three steps. tone(x, d, z, face) may answer another letter (a stratum, a crack)
    or None to keep the plane's. pieces(x, d, z) -> an id parts the rock into pieces with a
    line between (fallen blocks); by default it is one. Returns the rendered Grid."""
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from entrance_shapes import Scene
    sc = Scene(W, H, base)
    by = {}
    q = (0.1, 0.35, 0.6, 0.85)
    for x, d, z in solid:
        pid = pieces(x, d, z) if pieces else 0
        pts = by.setdefault(pid, [])
        faces = []
        if (x, d, z + 1) not in solid:
            faces.append(('top', [(x + u, d + v, z + 1) for u in q for v in q]))
        if (x, d - 1, z) not in solid:
            faces.append(('south', [(x + u, d, z + v) for u in q for v in q]))
        if (x + 1, d, z) not in solid:
            faces.append(('east', [(x + 1, d + u, z + v) for u in q for v in q]))
        for face, ps in faces:
            c = (tone(x, d, z, face) if tone else None) or {'top': 'L', 'south': 'M', 'east': 'D'}[face]
            pts += [(px, pd, pz, c) for px, pd, pz in ps]
    for pid, pts in by.items():
        sc.points(pid, pts)
    sc.ground(min(x for x, d, z in solid), max(x for x, d, z in solid), 0, max(d for x, d, z in solid))
    return sc.render()


def save(canvas, out, ramp, extra=None):
    """extra: more letters for a second material, {'p': 'fc74b4'} -- a flower."""
    light, mid, dark = RAMPS[ramp]
    col = {'l': light, 'm': mid, 'd': dark, 'K': '000000', **(extra or {})}
    H, W = len(canvas), len(canvas[0])
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for y in range(H):
        for x in range(W):
            if canvas[y][x] != '.':
                im.putpixel((x, y), tuple(int(col[canvas[y][x]][i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    im.save(out)
    body = [c for r in canvas for c in r if c not in '.K']
    print(out, {k: f'{body.count(k) / len(body):.1%}' for k in sorted(set(body))})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('draft'); ap.add_argument('out')
    ap.add_argument('--size', default='16x32'); ap.add_argument('--ramp', default='foliage')
    ap.add_argument('--height', type=int); ap.add_argument('--ribs', type=int, default=0)
    ap.add_argument('--trunk', help='x0-x1 on the canvas: the trunk keeps its own pattern through every joint')
    a = ap.parse_args()
    W, H = map(int, a.size.split('x'))
    mask = silhouette(a.draft, a.height or H - 3)
    g = paint(mask, a.ribs)
    h, w = len(g), len(g[0])
    assert w + 2 <= W, f'{w} wide does not fit {W} with its line'
    ox, oy = (W - w) // 2, H - 2 - h
    light, mid, dark = RAMPS[a.ramp]
    col = {'l': light, 'm': mid, 'd': dark, 'K': '000000'}
    canvas = [['.'] * W for _ in range(H)]
    for y in range(h):
        for x in range(w):
            if g[y][x] != '.':
                canvas[oy + y][ox + x] = g[y][x]
    if a.trunk:
        # a trunk is one limb top to bottom: through a joint, where an arm widens the row, its
        # columns take the pattern of the trunk's own rows (the first row below the joints)
        t0, t1 = map(int, a.trunk.split('-'))
        alone = lambda y: canvas[y][t0 - 1] == '.' and canvas[y][t1 + 1] == '.' and canvas[y][t0] != '.'
        below = [y for y in range(H) if alone(y)]
        ref = max(below) - 3
        for y in range(H):
            if canvas[y][t0] != '.' and not alone(y) and y < ref:
                for x in range(t0, t1 + 1):
                    canvas[y][x] = canvas[ref][x]
    ink = {(x, y) for y in range(H) for x in range(W) if canvas[y][x] != '.'}
    for x, y in list(ink):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in ink and 0 <= q[0] < W and 0 <= q[1] < H:
                canvas[q[1]][q[0]] = 'K'
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for y in range(H):
        for x in range(W):
            c = canvas[y][x]
            if c != '.':
                im.putpixel((x, y), tuple(int(col[c][i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    im.save(a.out)
    body = [c for r in canvas for c in r if c in 'lmd']
    print(a.out, {k: f'{body.count(k) / len(body):.1%}' for k in 'lmd'})


if __name__ == '__main__':
    main()
