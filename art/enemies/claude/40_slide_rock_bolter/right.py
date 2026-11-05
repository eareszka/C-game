"""40 Slide-Rock Bolter, giant, one view: its old sprite's RIGHT pose with the reference's look (the user,
2026-10-30: "this model but the original sprite pose", then "it needs to not look like shapes and look like a
correct pixel art creation; also have it use a right pose"). Drawn by Claude, no PixelLab.

The old right view (assets/enemies/40_slide_rock_bolter.png, cell 10: the whale lying with its head to the right,
its tail rising at the left and curling back, its flukes up) is the drawing's skeleton: its silhouette and its
parts (hide, pale underside, flukes, mouth) scaled up SCALE times onto the giant frame with their contours
smoothed (each part's map scaled, then every pixel the part most of its neighbours are, so the old staircases
become the curves they stood for -- the shapes are the old drawing's, not circles and boxes). Then the
reference's look (reference_user.png, EvolutionsVoid's Slide-Rock Bolter): its jaw gaping from the snout back
along the old mouth line, a row of teeth on each jaw, its pink tongue; its underside dark and mottled; its flukes
the two great yellow claws; a ridged hump behind its head.

The bible (art/direction/approved_enemy_study/STYLE_BRIEF.md): the exact palette, one ramp a material; light by
form from the upper left; shared separation lines; a closed one-pixel black outline; eyes one solid 2-px accent
mark; chunky clusters, no texture, no specks. Writes 40_giant_frame0.png.

    python art/enemies/claude/40_slide_rock_bolter/right.py
"""
from pathlib import Path
from collections import Counter
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
W, H = 192, 176
SCALE = 2.3
HL, HM, HD = h('c6ccda'), h('a4aaba'), h('848694')
UL, UD = h('595965'), h('34343e')
TOOTH = h('e8e0c0')
CL, CD = h('f0bc3c'), h('c9a433')
TL, TD = h('fc74b4'), h('b6433d')
MR = h('7c0a1b')                 # the mouth's inside: the Physeter's dark red, not a black hole
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))

NONE, HIDE, UNDER, CLAW, MOUTH, EYE, TEETH, TONGUE, RIDGE, BROW, LINE = range(11)
OLD = {'7c8494': HIDE, '4c5464': HIDE, 'a8b0bc': HIDE, 'c8c0b0': UNDER, 'f0e8d8': CLAW, 'b8b098': CLAW,
       '2c1418': MOUTH, '8c3c44': MOUTH, 'f0d040': EYE}


def skeleton():
    """The old right view's part map, scaled up, contours smoothed; its own black lines read as the part beside
    them (the outline is redrawn at the end)."""
    old = Image.open(ROOT / 'assets/enemies/40_slide_rock_bolter.png').convert('RGBA').crop((98 * 10, 0, 98 * 11, 65))
    old = old.crop(old.getbbox())
    px = old.load()
    ids = {}
    for y in range(old.height):
        for x in range(old.width):
            p = px[x, y]
            if not p[3]: continue
            k = '%02x%02x%02x' % p[:3]
            if k in OLD: ids[x, y] = OLD[k]
    inner = set()                                          # its own interior lines (black between two colours)
    for y in range(old.height):
        for x in range(old.width):
            if px[x, y][3] and px[x, y][:3] == (0, 0, 0):
                o = lambda q: q in ids
                if (o((x - 1, y)) and o((x + 1, y))) or (o((x, y - 1)) and o((x, y + 1))): inner.add((x, y))
    for _ in range(3):                                     # black pixels inside take their neighbours' part
        for y in range(old.height):
            for x in range(old.width):
                if px[x, y][3] and (x, y) not in ids:
                    n = Counter(ids[q] for q in ((x + dx, y + dy) for dx, dy in N8) if q in ids)
                    if n: ids[x, y] = n.most_common(1)[0][0]
    w, hh = round(old.width * SCALE), round(old.height * SCALE)
    ox, oy = (W - w) // 2, H - 2 - hh - DROP
    g = {}
    for y in range(hh):
        for x in range(w):
            q = (int(x / SCALE), int(y / SCALE))
            if q in ids: g[ox + x, oy + y] = ids[q]
    lines_at = set()
    for y in range(hh):                                     # the old interior lines, scaled, kept one pixel wide:
        for x in range(w):                                  # the first pixel of each scaled line's run across
            q, ql, qu = (int(x / SCALE), int(y / SCALE)), (int((x - 1) / SCALE), int(y / SCALE)), (int(x / SCALE), int((y - 1) / SCALE))
            if q in inner and (ql not in inner or qu not in inner): lines_at.add((ox + x, oy + y))
    for _ in range(3):                                     # smooth: a pixel the part most of its 8 are (empty too)
        new = {}
        for y in range(H):
            for x in range(W):
                n = Counter(g.get((x + dx, y + dy), NONE) for dx, dy in N8)
                n[g.get((x, y), NONE)] += 1
                top = n.most_common(1)[0][0]
                if top != g.get((x, y), NONE): new[x, y] = top
        for p, c in new.items():
            if c == NONE: g.pop(p, None)
            else: g[p] = c
    for p in lines_at:
        if p in g and g[p] == HIDE: g[p] = LINE
    return g


DROP = 26                                     # the lower jaw dropped this far at the snout's tip
LIFT = 14                                      # the hinge line this far above the old mouth slit
JAW = 10                                       # the lower jaw's thickness at the hinge


def line(x0, y0, x1, y1):
    """A pixel-art line: one pixel a column, its steps even (Bresenham)."""
    pts, dx, dy = [], abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1: return pts
        e2 = 2 * err
        if e2 >= dy: err += dy; x0 += sx
        if e2 <= dx: err += dx; y0 += sy


def mouth(g):
    """The jaw gaping (the reference's), drawn clean: the old mouth slit marks the hinge. The upper jaw's edge a
    straight line from the hinge to the snout's tip, rising a little; the lower jaw's edge a straight line from the
    hinge dropping DROP to the tip -- even steps, no jaggies. Between them the open mouth (black). Under the lower
    edge the lower jaw, a band JAW thick, on its throat and belly as drawn. Teeth: regular
    triangles every fifth column, hanging from the upper edge and standing on the lower, longer toward the tip.
    The tongue: a clean band lying on the lower jaw, thicker toward the front."""
    xs = [x for (x, y), c in g.items() if c == MOUTH]
    ys = [y for (x, y), c in g.items() if c == MOUTH]
    hinge, ym = min(xs) - 6, round(sum(ys) / len(ys)) - LIFT
    tip = max(x for (x, y), c in g.items() if c != CLAW and abs(y - ym) < 4) + 2
    upper = {x: y for x, y in line(hinge, ym, tip, ym - 3)}
    lower = {x: y for x, y in line(hinge, ym + 1, tip, ym + DROP)}
    for x in range(hinge, tip + 1):
        for y in range(upper[x] + 1, lower[x]): g[x, y] = MOUTH
        for y in range(lower[x], lower[x] + JAW - (x - hinge) // 12): g[x, y] = HIDE   # the throat below kept
    for x, y in line(hinge - 14, ym - 2, hinge, ym):          # the lip line, carried back along its cheek
        if g.get((x, y)) == HIDE: g[x, y] = LINE
    for x in range(hinge + 6, tip - 2, 7):                 # few big teeth, as the Physeter's: a 5-wide root
        n = 4 + (x - hinge) * 3 // max(1, tip - hinge)      # tapering to a 1-px point, longer toward the snout
        for k in range(n):
            half = max(0, 2 - k * 2 // n)
            for dx in range(-half, half + 1):
                if g.get((x + dx, upper[x] + 1 + k)) == MOUTH: g[x + dx, upper[x] + 1 + k] = TEETH
        for k in range(n - 1):
            half = max(0, 2 - k * 2 // (n - 1))
            for dx in range(-half, half + 1):
                if g.get((x + 3 + dx, lower[x] - 1 - k)) == MOUTH: g[x + 3 + dx, lower[x] - 1 - k] = TEETH
    for x in range(hinge + 6, tip - 3):
        t = (x - hinge) / max(1, tip - hinge)
        for k in range(3, 5 + round(4 * t)):
            q = (x, lower[x] - k)
            if g.get(q) == MOUTH: g[q] = TONGUE
    return g


def underside(g):
    """Its dark underside (the reference's): in each column, the lowest fifth of its hide and all of its lower jaw's
    lowest third, under one smooth edge -- a flat cluster, no dither, no slab."""
    cols = {}
    for (x, y), c in g.items():
        if c in (HIDE, UNDER): cols.setdefault(x, []).append(y)
    for x, ys in cols.items():
        top, bot = min(ys), max(ys)
        cut = bot - max(3, round((bot - top) * 0.2))
        for y in ys:
            g[x, y] = UNDER if y > cut else HIDE
    for (x, y) in [p for p, c in g.items() if c == HIDE and g.get((p[0], p[1] + 1)) == UNDER]:
        g[x, y] = LINE                                    # the line parting its hide from its underside
    return g


def eye(g):
    """Its eye: above the gape's hinge, a third of the way to the snout, a 2-px accent mark with a black brow."""
    xs = [x for (x, y), c in g.items() if c == MOUTH]
    hinge, tip = min(xs), max(xs)
    ex = hinge + (tip - hinge) // 3
    ey = min(y for (x, y), c in g.items() if c in (MOUTH, TEETH) and x == ex) - 6
    g[ex, ey] = g[ex + 1, ey] = EYE
    g[ex - 1, ey - 1] = g[ex, ey - 1] = g[ex + 1, ey - 1] = BROW
    return g


def ridge(g):
    """Its ridged hump: three plates standing on its back behind its head, each a bump on the outline with a line
    apart from the next."""
    top = {}
    for (x, y), c in g.items():
        if c == HIDE and (x not in top or y < top[x]): top[x] = y
    xs = sorted(top)
    mid = xs[len(xs) // 2]
    for k, cx in enumerate((mid + 2, mid + 11, mid + 20, mid + 29)):
        if cx not in top: continue
        cy = top[cx]
        for dx in range(-4, 5):
            for dy in range(0, 4 - abs(dx) // 2 - (1 if abs(dx) == 4 else 0)):
                g[cx + dx, cy - dy] = RIDGE if k % 2 else HIDE
    return g


def islands(g, few=6):
    """No fragments: a connected piece of one part of FEW pixels or fewer (teeth and the eye spared) becomes the part
    most common round it, or empty."""
    seen = set()
    for p0, c in list(g.items()):
        if p0 in seen or c in (TEETH, EYE, BROW, LINE): continue
        comp, todo = [p0], [p0]; seen.add(p0)
        while todo:
            x, y = todo.pop()
            for dx, dy in N4:
                q = (x + dx, y + dy)
                if q not in seen and g.get(q) == c: seen.add(q); comp.append(q); todo.append(q)
        if len(comp) > few: continue
        n = Counter(g.get((x + dx, y + dy), NONE) for x, y in comp for dx, dy in N4 if g.get((x + dx, y + dy)) != c)
        top = n.most_common(1)[0][0] if n else NONE
        for p in comp:
            if top == NONE: g.pop(p)
            else: g[p] = top
    return g


def paint(g):
    im = Image.new('RGBA', (W, H))
    px = im.load()
    col = {HIDE: HM, RIDGE: HM, UNDER: UL, CLAW: CL, MOUTH: MR, EYE: CL, TEETH: TOOTH, TONGUE: TL, BROW: K, LINE: K}
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: px[x, y] = col[c] + (255,)

    def run(x, y, dx, dy, parts):
        n = 0
        while g.get((x + dx * (n + 1), y + dy * (n + 1))) in parts: n += 1
        return n
    hide = (HIDE, EYE, RIDGE, BROW, LINE)
    # light by form on the hide, from the upper left: the three rows under an up-facing edge and the column inside
    # a left edge lit; the four over a lower edge and two inside a right edge dark -- each part's own contour
    for (x, y), c in g.items():
        if c in (HIDE, RIDGE):
            same = (c,) if c == RIDGE else hide
            up, dn, lf, rt = run(x, y, 0, -1, same), run(x, y, 0, 1, same), run(x, y, -1, 0, same), run(x, y, 1, 0, same)
            v = up / max(1, up + dn)                           # how far down its mass this pixel is
            u = lf / max(1, lf + rt)                           # how far across
            if (v < 0.34 and u < 0.8) or lf < 2: px[x, y] = HL + (255,)   # the broad lit plane, upper left
            elif v > 0.72 or rt < 3: px[x, y] = HD + (255,)              # the shaded lower and far side
        elif c == UNDER:
            # its dark underside, mottled: its upper edge broken into chunky darker clusters, its lower part the
            # darkest step
            if run(x, y, 0, 1, (UNDER,)) < 3: px[x, y] = UD + (255,)      # its lowest rows the darkest step
        elif c == CLAW:
            if run(x, y, 1, 0, (CLAW,)) < 1 or run(x, y, 0, 1, (CLAW,)) < 1: px[x, y] = CD + (255,)
        elif c == TONGUE:
            if run(x, y, 0, 1, (TONGUE,)) < 1: px[x, y] = TD + (255,)
    return im


def lines(im, g):
    """Separation lines where parts meet (hide over underside, plate over plate, teeth and tongue in the mouth
    are on black already), the closed outline, no specks."""
    px = im.load()
    over = {UNDER: HIDE, RIDGE: HIDE}
    for (x, y), c in g.items():
        for dx, dy in N4:
            b = g.get((x + dx, y + dy))
            if (c == UNDER and b in (HIDE,) and dy == -1) or (c == RIDGE and b == HIDE) or (c == CLAW and b == HIDE):
                px[x, y] = K + (255,)
                break
    for x, y in [(x, y) for y in range(H) for x in range(W) if not px[x, y][3]
                 and any(0 <= x + dx < W and 0 <= y + dy < H and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] != K
                         for dx, dy in N4)]:
        px[x, y] = K + (255,)
    for x in range(W):
        if px[x, H - 1][3] and px[x, H - 1][:3] != K: px[x, H - 1] = K + (255,)
    for _ in range(2):
        for y in range(H):
            for x in range(W):
                c = px[x, y]
                if not c[3] or c[:3] in (K, CL, TOOTH): continue
                near = [px[x + dx, y + dy] for dx, dy in N8 if 0 <= x + dx < W and 0 <= y + dy < H]
                if any(n[3] and n[:3] == c[:3] for n in near): continue
                pick = Counter(n[:3] for n in near if n[3] and n[:3] != K).most_common(1)
                px[x, y] = (pick[0][0] if pick else K) + (255,)
    return im


if __name__ == '__main__':
    g = eye(islands(ridge(underside(mouth(skeleton())))))
    im = lines(paint(g), g)
    im.save(HERE / '40_giant_frame0.png')
    print(im.getbbox())
