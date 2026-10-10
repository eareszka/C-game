"""Design for the Hidebehind (63), drawn flat to art/direction/SPRITE_STYLE.md.

    python art/enemies/63_hidebehind_design.py <out.json> [--silhouette]
    python tools/draw_views.py <out.json> art/enemies/63_views      # through the pixel plugin
    python art/enemies/63_hidebehind_design.py --txt                # writes 63_hidebehind.txt

A faceless hood of dark shaggy fur: a tall cone with no face, standing with
its upper arms out of its sides and its forearms raised, four long hooked
pale claws fanned from each paw, every claw at its own height. Static (faces
the player): Dh (left half of the front, mirrored by the build), DR and R,
each composed for its angle as one drawing -- silhouette, outline, then three
fur tones placed by form (light on the surface facing the viewer and up, dark
on the far side, under the hood's swell, under the arms and in the hem's
recesses). The shag is the jagged outline and hem, not texture. Big tier:
60 px tall in a 76-px frame.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAL = {'K': '000000', 'D': '2b190e', 'M': '463422', 'L': '633e1b', 'C': 'e8e0c0'}
FUR = set('DML')
W, H = 76, 60
BODY = 42            # the breathing row: plain cone, below the arms

def grid(w, h): return [['.'] * w for _ in range(h)]

def put(g, x0, y0, rows):
    """Lay rows over g; '.' leaves what is there, '_' clears it."""
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == '_': g[y0 + y][x0 + x] = '.'
            elif c != '.': g[y0 + y][x0 + x] = c

def span(g, y, x0, x1, tones):
    """Fill row y from x0 to x1 inclusive; tones = [(letter, count)...] from x0, the last letter fills the rest."""
    x = x0
    for t, n in tones:
        for _ in range(n):
            if x > x1: return
            g[y][x] = t; x += 1
    while x <= x1: g[y][x] = tones[-1][0]; x += 1

def separate(g):
    """A K line between claw and fur wherever they touch (one shared line between parts)."""
    h, w = len(g), len(g[0])
    for y in range(h):
        for x in range(w):
            if g[y][x] == 'C':
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= x + dx < w and 0 <= y + dy < h and g[y + dy][x + dx] in FUR: g[y + dy][x + dx] = 'K'

def outline(g):
    """1-px K ring: every transparent pixel 4-adjacent to a filled one."""
    h, w = len(g), len(g[0])
    ring = set()
    for y in range(h):
        for x in range(w):
            if g[y][x] != '.':
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= x + dx < w and 0 <= y + dy < h and g[y + dy][x + dx] == '.': ring.add((x + dx, y + dy))
    for x, y in ring: g[y][x] = 'K'

def claw(g, pts, base, side):
    """A hooked claw: C along pts from the paw outward; the first `base` points are 2 px thick,
    the second pixel offset by `side` (a (dx, dy) toward the claw's belly)."""
    for i, (x, y) in enumerate(pts):
        g[y][x] = 'C'
        if i < base: g[y + side[1]][x + side[0]] = 'C'

# ---------------------------------------------------------------- the cone, shared by every view
# fill half-width per row: a point, the hood's swell over the head, a slight waist, the body widening
# to the hem; the odd row out is a tuft of the shag
HW = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3, 9: 4, 10: 5, 11: 4, 12: 5, 13: 6, 14: 6, 15: 6,
      16: 7, 17: 8, 18: 7, 19: 6, 20: 6, 21: 6, 22: 7, 23: 7, 24: 7, 25: 8, 26: 8, 27: 8, 28: 9,
      29: 9, 30: 9, 31: 10, 32: 9, 33: 10, 34: 10, 35: 10, 36: 11, 37: 11, 38: 11, 39: 12, 40: 11,
      41: 12, 42: 12, 43: 12, 44: 13, 45: 12, 46: 13, 47: 13, 48: 13, 49: 13, 50: 14,
      51: 15, 52: 13, 53: 14, 54: 14, 55: 14}
# where the lit strip (the surface facing the viewer) starts, as a distance left of the axis, per row:
# widest over the hood's brow, narrower under the swell, widening again down the body, in clumps
LIT = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 2, 8: 2, 9: 3, 10: 3, 11: 4, 12: 4, 13: 5, 14: 6, 15: 5,
       16: 5, 17: 5, 18: 3, 19: 3, 20: 3, 21: 3, 22: 4, 23: 4, 24: 5, 25: 4, 26: 4, 27: 4, 28: 5,
       29: 5, 30: 5, 31: 5, 32: 5, 33: 5, 34: 6, 35: 7, 36: 6, 37: 6, 38: 6, 39: 6, 40: 7, 41: 7,
       42: 7, 43: 7, 44: 8, 45: 7, 46: 7, 47: 7, 48: 7, 49: 8, 50: 8, 51: 8, 52: 8, 53: 8, 54: 8, 55: 8}
def DARK(r):            # the front view's edges turning away from the viewer, deeper under the hood's swell
    return 0 if r <= 3 else 1 if r < 18 else 3 if r <= 21 else 2 if r < 40 else 3
# the far side of a turned cone: how much of the left edge is in shadow, per row (round over the hood,
# deepest under its swell and toward the hem, the odd row a clump of the shag)
FAR = {1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 2, 11: 2, 12: 2, 13: 3, 14: 3, 15: 4,
       16: 3, 17: 3, 18: 4, 19: 4, 20: 4, 21: 4, 22: 3, 23: 3, 24: 3, 25: 3, 26: 3, 27: 4, 28: 3,
       29: 3, 30: 4, 31: 4, 32: 4, 33: 4, 34: 3, 35: 3, 36: 4, 37: 3, 38: 4, 39: 4, 40: 4, 41: 4,
       42: 4, 43: 4, 44: 5, 45: 4, 46: 5, 47: 5, 48: 5, 49: 5, 50: 5, 51: 6, 52: 5, 53: 5, 54: 5, 55: 5}
# the shaggy hem: teeth of fur hanging below the cone's last row (55), across its 28 columns;
# each tooth keeps the tone of the fur above it, the fur over a recess goes dark
TEETH = ['.XX.XXX.XX..XXX.XX.XXX.XXX.X',
         '.X...XX.X....XX.X...XX..XX..',
         '.....X.......X......X.......']

# The front view's left arm: the upper arm out of the cone's side, an elbow, the forearm raised, a paw
# and four claws fanned from it, every tip at its own height. Fur as row -> [(x0, x1)...] spans.
ARM = {11: [(7, 11)], 12: [(6, 12)], 13: [(5, 13)], 14: [(5, 13)], 15: [(5, 13)], 16: [(6, 12)],
       17: [(8, 11)], 18: [(8, 11)], 19: [(8, 11)], 20: [(8, 11)], 21: [(8, 11)], 22: [(8, 11)],
       23: [(8, 12)], 24: [(8, 12)], 25: [(8, 12)], 26: [(8, 12)], 27: [(8, 12)],
       28: [(8, 12), (19, 23)], 29: [(8, 12), (15, 23)], 30: [(8, 23)], 31: [(8, 23)], 32: [(8, 23)],
       33: [(8, 23)], 34: [(8, 23)], 35: [(9, 17)], 36: [(10, 13)]}
ARM_LIT = [(7, 11), (8, 11), (9, 11), (10, 11), (11, 11), (6, 12), (12, 12),                     # the paw's top
           (19, 28), (20, 28), (21, 28), (22, 28), (23, 28), (15, 29), (16, 29), (17, 29), (18, 29), (13, 30), (14, 30)]
ARM_DARK = [(11, 17), (11, 18), (11, 19), (11, 20), (11, 21), (11, 22), (12, 23), (12, 24), (12, 25), (12, 26), (12, 27),
            (8, 34), (9, 35), (10, 36), (11, 36), (12, 36), (13, 36),                           # the elbow's underside
            (14, 35), (15, 35), (16, 35), (17, 35), (18, 34), (19, 34), (20, 34), (21, 34), (22, 34), (23, 34)]
CLAWS = [([(10, 10), (10, 9), (10, 8), (10, 7), (10, 6), (10, 5), (9, 4), (9, 3), (8, 2), (7, 1), (6, 1), (5, 2)], 4, (1, 0)),
         ([(6, 10), (5, 9), (4, 8), (3, 7), (2, 6), (1, 6), (0, 7), (-1, 8), (-1, 9)], 3, (1, 0)),
         ([(3, 13), (2, 13), (1, 13), (0, 13), (-1, 14), (-2, 15), (-3, 16), (-3, 17)], 3, (0, 1)),
         ([(5, 17), (4, 18), (3, 19), (2, 20), (2, 21), (1, 22), (1, 23), (2, 24), (3, 25)], 3, (0, -1))]
# its outline where it lies over the cone: the shoulder line and the underside, with the shadow it casts
ARM_ROOT = (21, 27, ['....', '...K', '...K', '...K', '...K', '...K', '...K', '...K', 'KKKK', 'DDDD', '.DD.'])

def arm(g, cx, right, fy=lambda y: y, scale=1.0, lit=True):
    """The front view's left arm (drawn about an axis at 32) placed on the cone about cx: the left
    arm, or mirrored as the right one; fy moves rows; scale < 1 foreshortens it toward the body
    (a far arm in a 3/4 view)."""
    fx = (lambda x: cx + 31 - x) if right else (lambda x: cx - 32 + x)
    sx = lambda x: fx(21 - round((21 - x) * scale))
    for y, spans in ARM.items():
        for x0, x1 in spans:
            for x in range(x0, x1 + 1): g[fy(y)][sx(x)] = 'M'
    for x, y in ARM_LIT:
        if lit: g[fy(y)][sx(x)] = 'L'
    for x, y in ARM_DARK: g[fy(y)][sx(x)] = 'D'
    flip = -1 if fx(1) < fx(0) else 1
    for pts, base, side in CLAWS:
        claw(g, [(sx(x), fy(y)) for x, y in pts], base, (side[0] * flip, side[1]))
    if scale == 1.0:
        x0, y0, rows = ARM_ROOT
        rows = [r[::-1] for r in rows] if flip < 0 else rows
        put(g, fx(x0) if flip > 0 else fx(x0 + 3), fy(y0), rows)

def cone(g, cx, shift=lambda r: 0, lit_side=1, edge=1):
    """The cone about column cx; shift(r) bends the tip; lit_side 0: the front, lit strip on the axis
    and both edges dark; +1: turned right, the far (left) edge in shadow, the lit strip right of the
    axis and `edge` px of mid at the near edge. Then the hem's teeth."""
    for r, hw in HW.items():
        x0, x1 = cx - hw + shift(r), cx + hw - 1 + shift(r)
        d, l = DARK(r), LIT[r]
        if lit_side == 0:
            tones = [('D', d), ('M', max(0, hw - d - l)), ('L', 2 * l), ('M', max(0, hw - d - l)), ('D', d)]
        else:
            f = FAR[r]
            tones = [('D', f), ('M', max(0, 2 * hw - f - 2 * l - edge)), ('L', 2 * l), ('M', edge)]
        span(g, r, x0, x1, tones)
    x0 = cx - HW[55]
    for i, row in enumerate(TEETH):
        for j, c in enumerate(row):
            if c == 'X': g[56 + i][x0 + j] = g[55 + i][x0 + j]
            elif i == 0: g[55][x0 + j] = 'D'

def finish(g, sil):
    separate(g)
    outline(g)
    if sil: g = [[('K' if c != '.' else '.') for c in r] for r in g]
    return [''.join(r) for r in g]

# ---------------------------------------------------------------- the views
def front_half(sil=False):
    """Left half of the straight front: the cone's axis is the right edge (mirrored by the build)."""
    g = grid(W, H)
    cx = W // 2
    cone(g, cx, lit_side=0)
    arm(g, cx, right=False)
    put(g, cx - 7, 18, ['KK', '.K'])                      # the hood's swell overhanging the shoulder
    return [r[:cx] for r in finish(g, sil)]

def three_quarter(sil=False):
    """3/4 front-right: the tip leans to the facing side, the lit strip sits right of the axis, the
    near (right) arm full size, the far (left) arm foreshortened and half behind the cone."""
    g = grid(W, H)
    cx = 37
    arm(g, cx, right=False, scale=0.7, lit=False)                           # far arm first: the cone covers its root
    cone(g, cx, shift=lambda r: 2 if r <= 3 else 1 if r <= 6 else 0, lit_side=1, edge=2)
    for r in range(24, 40):                                                  # the cone's edge over the far arm
        x = cx - HW[r] - 1
        if g[r][x] != '.': g[r][x] = 'K'
    arm(g, cx, right=True, fy=lambda y: y + 1)
    put(g, cx + 5, 18, ['KK', 'K.'])
    return finish(g, sil)

def side(sil=False):
    """Side, facing right: the hood's point droops forward, the lit face is the front (right),
    the dark the back; one arm, reaching forward and up, claws fanned before it."""
    g = grid(W, H)
    cx = 30
    cone(g, cx, shift=lambda r: 4 if r <= 2 else 3 if r <= 4 else 2 if r <= 6 else 1 if r <= 8 else 0,
         lit_side=1, edge=0)
    arm(g, cx, right=True, fy=lambda y: y + 1)
    put(g, cx + 5, 18, ['KK', 'K.'])
    return finish(g, sil)

VIEWS = {'Dh': front_half, 'DR': three_quarter, 'R': side}

def main():
    sil = '--silhouette' in sys.argv
    views = {k: f(sil) for k, f in VIEWS.items()}
    if '--txt' in sys.argv:
        out = os.path.join(HERE, '63_hidebehind.txt')
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write('#PAL\n' + ''.join(f'{k} {v}\n' for k, v in PAL.items()))
            # down: only the front is shown in battle (the user, 2026-10-10); the build
            # copies it into every direction. DR and R stay drawn above as reference.
            fh.write(f'#BODY\n{BODY}\n#DIRS\ndown\n')
            fh.write('#Dh\n' + '\n'.join(views['Dh']) + '\n')
        print(out); return
    d = {'pal': PAL, 'view_w': W, 'views': views, 'order': list(views)}
    json.dump(d, open(sys.argv[1], 'w'), indent=0)

if __name__ == '__main__':
    main()
