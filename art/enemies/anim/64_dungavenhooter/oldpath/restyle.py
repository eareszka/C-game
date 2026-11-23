"""The old-path Dungavenhooter (assets/enemies/64_dungavenhooter.png, 98x65, 8 frames x 8 views), the model the user
picked 2026-11-19 ("thats the model i want, but its texture and colors need to match the nes style"), recoloured to
the NES style of the old 51x41 still (art/_backup/64_before_slam_*.png): the still's colours; the body's checker of
scales flattened into a base and a shadow, following the checker's own light and dark (light from the upper left);
patches under MIN px merged into their neighbours. Recolour only: every px keeps its place, the silhouette and the
outline are the sheet's own. Writes oldpath/64_dungavenhooter_nes.png (the original is not touched).
Run: python -B art/enemies/anim/64_dungavenhooter/oldpath/restyle.py"""
import os, sys
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import enemy_sheet as es
SRC = os.path.join(ROOT, 'assets/enemies/64_dungavenhooter.png')
OUT = os.path.join(HERE, '64_dungavenhooter_nes.png')
BLACK, CLEAR = (0, 0, 0, 255), (0, 0, 0, 0)
# the still's colours
SHADOW, BASE, CREAM = (92, 70, 22, 255), (135, 106, 31, 255), (206, 190, 130, 255)
STEEL, STEEL_DARK, EYE = (151, 151, 170, 255), (89, 89, 101, 255), (240, 232, 128, 255)   # the eye: the palette's brighter yellow
SHINE = (220, 240, 255, 255)      # the ball's lit upper left and its spike tips (the still's ball has it)
# the sheet's colours: the scale checker (by lightness), and the rest straight across
SCALES = {(135, 106, 31): 2, (104, 80, 24): 1, (54, 42, 14): 0}
ACROSS = {(0, 0, 0): BLACK, (34, 20, 12): BLACK, (164, 170, 186): STEEL, (89, 89, 101): STEEL_DARK,
          (206, 190, 130): CREAM, (178, 158, 92): CREAM, (240, 188, 60): EYE, (236, 132, 118): EYE}
R, BASE_SHARE, MIN = 2, 0.66, 7   # the blur radius over the scales; the share of them lit BASE (the still: 2 to 1); the smallest patch
LINES = 0.14                      # the most interior black (the bible: 9 to 14%)
SEAMS = [(37, 3), (43, 4), (48, 3), (54, 4), (61, 3), (66, 4), (72, 2)]   # the side view's back plates: (x, length) in R's cell

def restyle(f, view):
    W, H = f.size; p = f.load(); out = Image.new('RGBA', (W, H), CLEAR); o = out.load()
    scale = lambda x, y: 0 <= x < W and 0 <= y < H and p[x, y][3] and p[x, y][:3] in SCALES
    for y in range(H):
        for x in range(W):
            c = p[x, y]
            if not c[3]: continue
            if c[:3] in SCALES:      # shade by shape: each part's underside and lower right, away from the upper-left light
                o[x, y] = SHADOW if not (scale(x, y + 1) and scale(x, y + 2) and scale(x + 1, y + 1)) else BASE
            else:
                o[x, y] = ACROSS[c[:3]]
    merge(out, {BASE, SHADOW})
    if view == 'R': plates(out)
    ball(out)
    thin(out)
    return out

def ball(f):
    """The club as a spiked steel ball, recolour only: its round core (the grey opened by 2 px) lit upper left, dark
    lower right; the spikes (the grey the opening took off) dark at the root, lit at the tip; dark where the tail meets it."""
    W, H = f.size; p = f.load()
    grey = {(x, y) for y in range(H) for x in range(W) if p[x, y] in (STEEL, STEEL_DARK)}
    if not grey: return
    m = Image.new('L', (W, H), 0); mp = m.load()
    for q in grey: mp[q] = 255
    op = m.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5)).load()
    core = {q for q in grey if op[q]}
    for c in blobs_of(core):
        cx, cy = sum(x for x, _ in c) / len(c), sum(y for _, y in c) / len(c); r = max(1.0, (len(c) / 3.1416) ** 0.5)
        for x, y in c:
            dx, dy = (x - cx) / r, (y - cy) / r; diag, dist = dx + dy, (dx * dx + dy * dy) ** 0.5
            p[x, y] = STEEL_DARK if diag > 0.5 or (dist > 0.85 and diag > 0) else SHINE if -1.2 < diag < -0.5 and abs(dx - dy) < 0.5 and dist < 0.9 else STEEL   # a spot, upper left
    spikes = grey - core
    for c in blobs_of(spikes):
        root = [q for q in c if any((q[0] + dx, q[1] + dy) in core for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        for q in c: p[q] = STEEL
        for q in root: p[q] = STEEL_DARK
        if len(c) >= 2:
            cx, cy = (sum(x for x, _ in core) / len(core), sum(y for _, y in core) / len(core)) if core else (0, 0)
            tip = max(c, key=lambda q: (q[0] - cx) ** 2 + (q[1] - cy) ** 2)
            if tip not in root: p[tip] = SHINE
    for x, y in grey:                                  # the socket: where the tail (brown) meets the steel
        if any(0 <= x + dx < W and 0 <= y + dy < H and p[x + dx, y + dy] in (BASE, SHADOW) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            p[x, y] = STEEL_DARK

def thin(f, only=None):
    """Inner black down to LINES of the drawn px, recolouring only: first the outline's doubled second ring (a black px
    inside the rim lying against the rim's black), then 2x2 blocks of black (doubled inner lines); each takes the
    colour most of its fill neighbours have."""
    W, H = f.size; p = f.load()
    on = lambda x, y: 0 <= x < W and 0 <= y < H and p[x, y][3]
    rim = lambda x, y: any(not on(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    drawn = sum(1 for y in range(H) for x in range(W) if p[x, y][3])
    while True:
        inner = [(x, y) for y in range(H) for x in range(W) if p[x, y] == BLACK and not rim(x, y)]
        if len(inner) <= LINES * drawn: break
        best = None
        for x, y in inner:
            if only is not None and (x, y) not in only: continue
            nb = [p[x + dx, y + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy) and on(x + dx, y + dy)]
            fill = [c for c in nb if c != BLACK]
            if not fill: continue
            doubled = any(on(x + dx, y + dy) and p[x + dx, y + dy] == BLACK and rim(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            block = any(all(on(x + a, y + b) and p[x + a, y + b] == BLACK for a, b in ((sx, 0), (0, sy), (sx, sy))) for sx in (-1, 1) for sy in (-1, 1))
            stub = sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if on(x + dx, y + dy) and p[x + dx, y + dy] == BLACK) <= 1
            score = (3 if doubled else 2 if block else 1 if stub else 0, len(fill))   # stub: a line ending in open surface
            if score[0] and (best is None or score > best[0]): best = (score, (x, y), max(set(fill), key=fill.count))
        if best is None: break
        p[best[1]] = best[2]

def plates(f):
    """The side view's details (recolour only): a black line where the body meets the cream belly, and the back's
    plate seams -- short black lines down from the back at SEAMS (uneven, as the bible asks), each plate's right end
    in shadow."""
    W, H = f.size; p = f.load(); body = {BASE, SHADOW}
    for y in range(H - 1):
        for x in range(W):
            if p[x, y] in body and p[x, y + 1] == CREAM: p[x, y] = BLACK
    for x, n in SEAMS:
        top = next((y for y in range(H) if p[x, y][3]), None)
        if top is None: continue
        for y in range(top + 1, top + 1 + n):
            if p[x, y] in body: p[x, y] = BLACK
            if p[x - 1, y] in body and y < top + n: p[x - 1, y] = SHADOW

def blobs_of(g):
    """8-connected groups of a set of px."""
    g = set(g); out = []
    while g:
        st = [g.pop()]; c = []
        while st:
            q = st.pop(); c.append(q)
            for r in ((q[0] + dx, q[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                if r in g: g.remove(r); st.append(r)
        out.append(c)
    return out

def merge(f, kinds):
    """Patches (8-connected, one colour of `kinds`) under MIN px take the colour most of their rim has."""
    W, H = f.size; p = f.load()
    for _ in range(4):
        seen, changed = set(), False
        for y in range(H):
            for x in range(W):
                if (x, y) in seen or p[x, y] not in kinds: continue
                c, st, comp = p[x, y], [(x, y)], []; seen.add((x, y))
                while st:
                    q = st.pop(); comp.append(q)
                    for r in ((q[0] + dx, q[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                        if 0 <= r[0] < W and 0 <= r[1] < H and r not in seen and p[r] == c: seen.add(r); st.append(r)
                if len(comp) >= MIN: continue
                rim = [p[r] for q in comp for r in ((q[0] + dx, q[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                       if 0 <= r[0] < W and 0 <= r[1] < H and p[r] in kinds and p[r] != c]
                if rim:
                    best = max(set(rim), key=rim.count)
                    for q in comp: p[q] = best
                    changed = True
        if not changed: break

if __name__ == '__main__':
    src = Image.open(SRC).convert('RGBA'); n = 8; W, H = src.width // 64, src.height
    cells = es.cells_of(src, n, False); done = {}
    for d in ('D', 'DR', 'R', 'UR', 'U'):           # UL L DL are the sheet's own mirrors of UR R DR: mirrored after
        f0 = cells[d][0]; r0 = restyle(f0, d); done[d] = [r0]
        for i in range(1, n):                       # the body stands still: frame 0's px wherever the drawing is the same
            f = cells[d][i]; r = restyle(f, d); a, b, c, o = f0.load(), r0.load(), f.load(), r.load()
            own = set(); steel = {(164, 170, 186), (89, 89, 101)}
            near = lambda im, x, y: any(0 <= x + dx < W and 0 <= y + dy < H and im[x + dx, y + dy][:3] in steel and im[x + dx, y + dy][3]
                                        for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            for y in range(H):
                for x in range(W):        # the ball moves: it and its ring are this frame's own, never frame 0's
                    if c[x, y][3] and c[x, y] == a[x, y] and not near(c, x, y) and not near(a, x, y): o[x, y] = b[x, y]
                    elif c[x, y][3]: own.add((x, y))
            thin(r, own)                            # its own parts (the club, the dust) thinned again, the body kept
            done[d].append(r)
    for m, s in (('UL', 'UR'), ('L', 'R'), ('DL', 'DR')): done[m] = [x.transpose(Image.FLIP_LEFT_RIGHT) for x in done[s]]
    out = Image.new('RGBA', src.size, CLEAR)
    for j, d in enumerate(es.ORDER):
        for i in range(n): out.paste(done[d][i], ((j * n + i) * W, 0))
    a, b = src.load(), out.load()
    assert all(bool(a[x, y][3]) == bool(b[x, y][3]) for y in range(H) for x in range(src.width)), 'silhouette moved'
    out.save(OUT); print('wrote', OUT)
