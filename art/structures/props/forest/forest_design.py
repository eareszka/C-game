"""The forest's props: seventeen things for the woods' floor, one function each.

    python art/structures/props/forest/forest_design.py          # every prop, and the board
    python art/structures/props/forest/forest_design.py fern     # one

Each writes art/structures/props/forest/<name>.png (and the sapling its frames).
The list was approved by the user on 2026-10-26 (sizes in cells, materials,
drops); PixelLab drafts under pixellab-out/forest-*/ gave the designs of the
hollow log, woodpile, mushrooms, berry bush, mossy boulder, lean-to and
uprooted tree.

Objects keep the objects' rule (OVERWORLD_STYLE.md): one black line round the
silhouette, three colours and black, one ramp placed by form, flat fills. A
thing of two materials gives up a tone to stay at three -- the mossy boulder is
stone's base and shade with moss for its lit top, the berry bush two greens
with the berries in the light's place. The woodpile and the lean-to are built,
in the houses' projection. Leaf litter is ground cover and drawn as the
ground draws a tuft (the dry grass ruling).
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from entrance_shapes import Scene

# tools/overworld_style.py MATERIALS
BARK = ('605028', '463422', '2d230c')
WOOD = ('967448', '785830', '493712')
FOLIAGE = ('05c43a', '058f3a', '235436')
STONE = ('c6ccda', '9797aa', '595965')
RED = ('b70000', '7c0a1b')              # red paint
WHITE = 'fcfcfc'
THATCH = ('c9a433', '876a1f')
RUST = ('764c20', '3e1c0e')
BONE = ('e8e0c0', 'b2966a', '8d6b4f')


# ---------------------------------------------------------------- shared
def blank(w, h):
    return [['.'] * w for _ in range(h)]


def outline(g):
    """A 1px black line round what is coloured (not round a line already drawn)."""
    h, w = len(g), len(g[0])
    ink = {(x, y) for y in range(h) for x in range(w) if g[y][x] not in '.K'}
    for x, y in ink:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q, r = x + dx, y + dy
            if 0 <= q < w and 0 <= r < h and g[r][q] == '.':
                g[r][q] = 'K'
    assert all(c == '.' for c in g[0] + [r[0] for r in g] + [r[w - 1] for r in g]), 'drawn at the edge'
    return g


def typed(rows):
    return fit([list(r) for r in rows])


def fit(g):
    """Slide a drawing so its line will clear the canvas's top and side edges (the bottom row
    may be drawn on: it is the ground) -- typed by hand, a sprite is often a pixel out."""
    h, w = len(g), len(g[0])
    ink = [(x, y) for y in range(h) for x in range(w) if g[y][x] != '.']
    x0, x1, y0 = min(x for x, y in ink), max(x for x, y in ink), min(y for x, y in ink)
    dx = 2 - x0 if x0 < 2 else (w - 3 - x1 if x1 > w - 3 else 0)
    dy = 2 - y0 if y0 < 2 else 0
    assert x1 - x0 <= w - 5, 'too wide for its canvas'
    if not dx and not dy:
        return g
    out = [['.'] * w for _ in range(h)]
    for x, y in ink:
        if 0 <= y + dy < h:
            out[y + dy][x + dx] = g[y][x]
    return out


def stroke(g, pts, c, pick=None):
    """A run of (x, y, thickness) points, a capsule between each pair; pick(x, y, t, side) may
    answer the tone per pixel (side -1 left of the stroke .. 1 right)."""
    h, w = len(g), len(g[0])
    for (xa, ya, wa), (xb, yb, wb) in zip(pts, pts[1:]):
        vx, vy = xb - xa, yb - ya
        L2 = vx * vx + vy * vy or 1
        for y in range(h):
            for x in range(w):
                px, py = x + 0.5, y + 0.5
                t = max(0.0, min(1.0, ((px - xa) * vx + (py - ya) * vy) / L2))
                r = (wa + (wb - wa) * t) / 2
                ox, oy = px - xa - vx * t, py - ya - vy * t
                d = math.hypot(ox, oy)
                if d <= r:
                    side = (ox * -vy + oy * vx) / math.sqrt(L2) / max(r, 0.5)
                    g[y][x] = pick(x, y, t, side) if pick else c


def ellipse(cx, cy, rx, ry):
    return lambda x, y: ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1


# ---------------------------------------------------------------- 1. fallen log
def log_side(g, x0, x1, y0, y1, grain=True):
    """A log lying across, its side toward us: lit along its top, shade beneath, a grain line."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x == x0) and y in (y0, y1):
                continue
            t = (y - y0) / (y1 - y0)
            c = 'l' if t < 0.25 else 'd' if t > 0.7 else 'm'
            if grain and abs(t - 0.45) < 0.12 and (x * 3) % 11 < 5:
                c = 'd'
            g[y][x] = c


def log_end(g, cx, cy, rx, ry, hole=False):
    """The cut end, square on: a ring of bark round its face, rings in the wood -- or a hole."""
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            r = math.hypot(u, v)
            if r > 1:
                continue
            if r > 0.72:
                c = 'd'
            elif hole:
                c = 'K'
            else:
                c = 'd' if abs(r - 0.4) < 0.13 else 'l'
            g[y][x] = c


def fallen_log():
    g = blank(32, 16)
    log_side(g, 3, 25, 7, 13)
    log_end(g, 26, 10.5, 2.6, 3.9)
    return outline(g), {'l': BARK[0], 'm': BARK[1], 'd': BARK[2]}


# ---------------------------------------------------------------- 2. hollow log
def hollow_log():
    g = blank(48, 16)
    log_side(g, 3, 39, 5, 14)
    log_end(g, 40, 9.8, 3.4, 5.0, hole=True)
    for x, y in ((14, 8), (15, 8), (15, 9)):          # a knot
        g[y][x] = 'K'
    return outline(g), {'l': BARK[0], 'm': BARK[1], 'd': BARK[2]}


# ---------------------------------------------------------------- 3. mossy stump
def mossy_stump():
    g = blank(16, 16)
    body, top = ellipse(8, 7.5, 4.5, 2.2), None
    for y in range(7, 15):
        for x in range(3, 13):
            if 3 < x < 12 or (y >= 13 and 2 < x < 13):            # the body, its roots flaring
                g[y][x] = 'd' if x >= 10 or y >= 13 else 'm'
    for y in range(4, 10):
        for x in range(2, 14):
            if body(x, y):
                g[y][x] = 'g'                                      # moss over the cut top
    for x, y in ((6, 7), (7, 7), (8, 7), (7, 6)):                  # the cut showing through, its rings
        g[y][x] = 'm' if (x, y) != (7, 7) else 'd'
    for x, y in ((4, 9), (4, 10), (5, 10), (4, 11), (5, 9)):       # moss creeping down the lit side
        g[y][x] = 'g'
    return outline(g), {'g': FOLIAGE[1], 'm': BARK[1], 'd': BARK[2]}


# ---------------------------------------------------------------- 4. stump with an axe
def axe_stump():
    """Three colours: the bark's mid and shade, and the axe head in stone's light -- the brightest
    thing on it. The cut top is in the bark's mid, its rings in shade, so the head reads."""
    g = blank(16, 32)
    for y in range(20, 30):
        for x in range(3, 13):
            if 3 < x < 12 or (y >= 28):
                g[y][x] = 'd' if x >= 10 or y >= 28 else 'm'
    top = ellipse(8, 19.5, 4.6, 2.0)
    for y in range(16, 23):
        for x in range(2, 14):
            if top(x, y):
                g[y][x] = 'm'
    for x, y in ((7, 19), (8, 19), (9, 20), (6, 20), (10, 19)):    # its rings
        g[y][x] = 'd'
    stroke(g, [(9.5, 18.5, 1.5), (12.5, 8.5, 1.5)], 'm')            # the handle, sloping up
    for x, y in ((5, 16), (6, 16), (7, 16), (8, 16), (4, 17), (5, 17), (6, 17), (7, 17), (8, 17), (9, 17),
                 (5, 18), (6, 18), (7, 18), (8, 18)):
        g[y][x] = 'l'                                              # the head, bitten into the cut
    for x, y in ((8, 16), (9, 17), (8, 18)):
        g[y][x] = 'd'                                              # its eye, round the handle
    out = outline(g)
    return out, {'l': STONE[0], 'm': BARK[1], 'd': BARK[2]}

# ---------------------------------------------------------------- 5. woodpile (built)
def woodpile():
    """A stack of split logs, built: a box in the houses' projection -- its top the bark of the
    top logs, lit; its east side the log ends' shade -- with the round ends of the logs laid on
    its front face, the gaps between them dark."""
    W, H, BASE, R = 32, 32, 29, 2.75
    sc = Scene(W, H, BASE)
    sc.box(0, 3, 23, 0, 4, 0, 14, front='K')
    g = sc.render().g
    for i in range(3):                                             # three rows of five ends
        for k in range(5):
            cx, cy = 5.6 + k * 5.2 + (i % 2) * 2.6, BASE - 2.7 - i * 4.9
            if cx + R > 24.2:
                continue
            for y in range(int(cy - R) - 1, int(cy + R) + 2):
                for x in range(int(cx - R) - 1, int(cx + R) + 2):
                    r = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / R
                    if r <= 1.0 and g[y][x] == 'K':
                        g[y][x] = 'd' if r > 0.78 else 'l'                 # the bark's ring round the wood
    top_row = BASE - 14
    for y in range(H):
        for x in range(W):
            if g[y][x] == 'L':
                d = top_row - y                                    # how far back this pixel of the top is
                along = x - d - 3                                  # where across the front it runs back from
                g[y][x] = 'd' if 0 < d and round(along) % 5 == 4 else 'b'   # a log's edge running back
            elif g[y][x] == 'D':
                g[y][x] = 'd'
    return g, {'l': WOOD[0], 'd': WOOD[2], 'b': BARK[0]}

# ---------------------------------------------------------------- 6. mushrooms
def mushrooms():
    g = typed([
        "................",
        "................",
        "................",
        "....rrrrr.......",
        "...rrrwrrR......",
        "..rwrrrrrrR.....",
        "..rrrrrwrRR.....",
        "..RRRRRRRRR.....",
        ".....www..rrR...",
        ".....www.rwrRR..",
        ".....www..RRR...",
        ".....www...w....",
        "....wwwww.www...",
        "................",
        "................",
        "................"])
    return outline(g), {'r': RED[0], 'R': RED[1], 'w': WHITE}

# ---------------------------------------------------------------- 7. fern
def quad(p0, p1, p2, n=60):
    """Points along a quadratic curve from p0 through the pull of p1 to p2."""
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def fern():
    """Two cells wide (the user, 2026-10-26: a one-cell fern was a blob): five fronds arching out of
    one root, each a rib with leaflets down both sides, a pixel apart so the line between them
    shows each one -- lit on the frond's upper side, in shade on its lower, the rib the mid."""
    g = blank(32, 16)
    root = (15.5, 13.5)
    fronds = [((3, 8), (6, 4)), ((28, 8), (25, 4)), ((7, 3), (9, 2)), ((24, 3), (22, 2)), ((15.5, 2), (15.5, 6))]
    for tip, pull in fronds:
        pts = quad(root, pull, tip)
        for i, (x, y) in enumerate(pts):
            px, py = int(x), int(y)
            if not (2 <= px <= 29 and 2 <= py <= 13):
                continue
            g[py][px] = 'm'
            t = i / (len(pts) - 1)
            if i % 11 == 5 and 0.15 < t < 0.9 and i + 1 < len(pts):
                dx, dy = pts[i + 1][0] - x, pts[i + 1][1] - y
                n = math.hypot(dx, dy) or 1
                nx, ny = -dy / n, dx / n                                   # across the rib
                reach = 2.2 * (1 - t) + 0.9
                for side, c in ((-1, 'l'), (1, 'd')):
                    for k in (1, 2, 3):
                        if k > reach:
                            break
                        qx, qy = int(x + side * nx * k + dx / n * k * 0.6), int(y + side * ny * k + dy / n * k * 0.6)
                        if 2 <= qx <= 29 and 2 <= qy <= 13 and g[qy][qx] == '.':
                            g[qy][qx] = c
    for x in range(13, 19):
        g[13][x] = 'd'
    return outline(g), {'l': FOLIAGE[0], 'm': FOLIAGE[1], 'd': FOLIAGE[2]}

# ---------------------------------------------------------------- 8. bramble
def bramble():
    """A low mound of leaves, and over it thorny canes arching up out of it and bowing back down,
    in bark, a thorn standing off each arch's outer side now and then. Two greens and the bark."""
    g = blank(32, 16)
    for cx, cy, rx, ry in ((10, 10.5, 7.5, 4.5), (21, 10, 8.0, 5.0), (15.5, 8.5, 6.5, 4.5)):
        inside = ellipse(cx, cy, rx, ry)
        for y in range(16):
            for x in range(32):
                if inside(x, y) and y <= 13:
                    u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                    g[y][x] = 'G' if u + v > 0.5 or y >= 13 else 'g'
    arches = [((3, 13), (7, -1), (13, 12)), ((10, 13), (16, -3), (22, 12)), ((18, 13), (24, -1), (29, 12))]
    for a in arches:
        pts = quad(*a)
        for i, (x, y) in enumerate(pts):
            px, py = int(x), int(y)
            if 2 <= px <= 29 and 2 <= py <= 13:
                g[py][px] = 'm'
                if i % 14 == 7 and py - 1 >= 2 and g[py - 1][px] in '.gG':
                    g[py - 1][px] = 'm'                                    # a thorn, standing off its top
    return outline(g), {'m': BARK[1], 'g': FOLIAGE[1], 'G': FOLIAGE[2]}

# ---------------------------------------------------------------- 9. berry bush
def berry_bush():
    g = blank(16, 32)
    clumps = [(8, 17, 5.0, 4.6), (5.5, 22, 3.3, 3.6), (10.5, 22, 3.3, 3.6), (8, 25, 4.8, 3.6)]
    for cx, cy, rx, ry in clumps:
        inside = ellipse(cx, cy, rx, ry)
        for y in range(H32):
            for x in range(16):
                if inside(x, y):
                    lit = (x + 0.5 - cx) / rx + (y + 0.5 - cy) / ry
                    g[y][x] = 'G' if lit > 0.75 or y >= 27 else 'g'
    for x, y in ((6, 15), (10, 16), (4, 20), (8, 20), (12, 21), (6, 24), (10, 25), (3, 23), (13, 24), (8, 13)):
        g[y][x] = 'r'
    return outline(g), {'g': FOLIAGE[1], 'G': FOLIAGE[2], 'r': RED[0]}


H32 = 32


# ---------------------------------------------------------------- 10. mossy boulder
def mossy_boulder():
    g = blank(32, 32)
    inside = ellipse(15.5, 20.5, 12.5, 9.5)
    inner = ellipse(19, 23, 9.5, 7.5)
    for y in range(32):
        for x in range(32):
            if inside(x, y) and y <= 29:
                u, v = (x + 0.5 - 15.5) / 12.5, (y + 0.5 - 20.5) / 9.5
                g[y][x] = 'd' if u + v > 0.55 or y >= 28 else 'm'
    moss_line = lambda x: 15 + 2.5 * math.sin(x * 0.55) + 0.12 * (x - 15) ** 2 / 3
    for y in range(32):
        for x in range(32):
            if g[y][x] != '.' and y < moss_line(x) - 1:
                g[y][x] = 'g'                                      # moss over its crown, lit
    for x, y in ((9, 16), (9, 17), (22, 17), (13, 18)):            # moss dripping over the edge
        if g[y][x] != '.':
            g[y][x] = 'g'
    for x, y in ((14, 22), (15, 23), (15, 24), (16, 25), (20, 21), (21, 22)):   # a crack
        g[y][x] = 'K'
    return outline(g), {'g': FOLIAGE[1], 'm': STONE[1], 'd': STONE[2]}


# ---------------------------------------------------------------- 11. deer skull
def deer_skull():
    g = typed([
        "................",
        "................",
        "..b...b..b...b..",
        "..b.b.b..b.b.b..",
        "...bbb....bbb...",
        "....bb....bb....",
        ".....bb..bb.....",
        "......llll......",
        ".....llllll.....",
        ".....lKllKl.....",
        "......llll......",
        "......lllm......",
        "......llmm......",
        ".......lm.......",
        ".......mm.......",
        "................"])
    return outline(g), {'l': BONE[0], 'b': BONE[1], 'm': BONE[2]}


# ---------------------------------------------------------------- 12. lean-to (built)
def lean_to():
    sc = Scene(48, 32, 29)
    sc.gable(0, 6, 32, 0, 9, 0, 15)
    g = sc.render()
    for y in range(g.h):                                          # the thatch laid in rows down its slopes
        for x in range(g.w):
            if sc.pid[y][x] == 0 and g.g[y][x] in 'LD' and (2 * 29 - x - y) % 4 == 0:
                g.g[y][x] = 'D' if g.g[y][x] == 'L' else 'K'
    # the front triangle is the way in: dark, a pole down each side, the poles crossed over the ridge
    for y in range(g.h):
        for x in range(g.w):
            if sc.pid[y][x] == 1000 and g.g[y][x] in 'LM':
                g.g[y][x] = 'K'
    rows = [y for y in range(g.h) if any(sc.pid[y][x] == 1000 for x in range(g.w))]
    for y in rows:
        xs = [x for x in range(g.w) if sc.pid[y][x] == 1000]
        g.g[y][min(xs)] = 'w'
        g.g[y][max(xs)] = 'w'
    top = min(rows)
    xs = [x for x in range(g.w) if sc.pid[top][x] == 1000]
    xm = (min(xs) + max(xs)) // 2
    for k in range(1, 4):                                         # the crossed poles above the ridge
        for x, y in ((xm - k, top - k), (xm + k, top - k)):
            if 0 < y and 0 < x < g.w - 1:
                g.g[y][x] = 'w'
                g.g[y - 1][x] = 'K' if g.g[y - 1][x] == '.' else g.g[y - 1][x]
    for y in range(g.h):                                          # the line round the poles' ends
        for x in range(g.w):
            if g.g[y][x] == 'w':
                for dx, dy in ((1, 0), (-1, 0), (0, -1)):
                    if g.g[y + dy][x + dx] == '.':
                        g.g[y + dy][x + dx] = 'K'
    return g.g, {'L': THATCH[0], 'D': THATCH[1], 'w': WOOD[1]}


# ---------------------------------------------------------------- 13. stump with a nest
def nest_stump():
    """Short and broad, a big nest on its broken top -- tall and thin, it read as a post
    (redrawn 2026-10-27 after the in-world check)."""
    g = blank(16, 32)
    for y in range(19, 30):
        for x in range(3, 13):
            jag = {3: 22, 4: 20, 5: 19, 6: 21, 7: 19, 8: 20, 9: 19, 10: 21, 11: 20, 12: 22}[x]
            if y >= jag:
                g[y][x] = 'd' if x >= 10 or y >= 27 else 'm'
    for x in (2, 13):                                             # the roots
        for y in (28, 29):
            g[y][x] = 'd'
    for x in (5, 8):                                              # bark split down the lit side
        for y in range(22, 26):
            g[y][x] = 'd'
    rim, bowl = ellipse(7.5, 17.5, 5.6, 3.4), ellipse(7.5, 17.0, 3.4, 1.6)
    for y in range(12, 23):
        for x in range(16):
            if bowl(x, y):
                g[y][x] = 'd'                                     # the hollow of the nest
            elif rim(x, y):
                g[y][x] = 'm' if (x * 5 + y * 3) % 7 == 0 else 't'   # woven: twigs through the straw
    return outline(g), {'m': BARK[1], 'd': BARK[2], 't': THATCH[0]}


# ---------------------------------------------------------------- 14. fallen branch
def fallen_branch():
    g = blank(32, 16)
    pick = lambda x, y, t, side: 'l' if side < -0.3 else 'd' if side > 0.45 else 'm'
    stroke(g, [(3, 12, 2.6), (14, 10.5, 2.2), (27, 8, 1.4)], 'm', pick)
    stroke(g, [(14, 10.5, 1.6), (19, 13, 1.2), (24, 13.5, 1.0)], 'm', pick)
    stroke(g, [(9, 11.5, 1.4), (11, 7, 1.0)], 'm', pick)
    return outline(g), {'l': BARK[0], 'm': BARK[1], 'd': BARK[2]}


# ---------------------------------------------------------------- 15. leaf litter (ground)
def leaf_litter():
    g = typed([
        "................",
        "................",
        "................",
        "...tt...........",
        "..tRt.....rr....",
        "...R.....rRr....",
        "..........R.....",
        "......tt........",
        ".....tttR...tt..",
        "......RR...tRt..",
        "..rr........R...",
        ".rRr....rr......",
        "..R....rrR......",
        ".........R......",
        "................",
        "................"])
    for y in range(15, 0, -1):                                     # a dot of shadow under a few
        for x in range(16):
            if g[y - 1][x] in 'R' and g[y][x] == '.' and (x + y) % 3 == 0:
                g[y][x] = 'K'
    return g, {'t': THATCH[0], 'r': RUST[0], 'R': RUST[1]}


# ---------------------------------------------------------------- 16. sapling (4 frames)
def sapling(frame=0):
    """A young tree, bushy and low: a round crown on a short trunk, the old round tree's build --
    a lollipop on a stick read as a pole (redrawn 2026-10-27 after the in-world check)."""
    sway = (0, 1, 0, -1)[frame]                                    # only the crown's top stirs
    g = blank(16, 32)
    for y in range(25, 30):                                        # the trunk, in the leaves' shade
        g[y][7] = g[y][8] = 'G'
    for cx, cy, rx, ry, s in ((7.5, 19.5, 5.2, 5.0, 0), (4.6, 22.5, 2.5, 2.4, 0), (10.4, 22.0, 2.5, 2.4, 0),
                              (7.8, 14.0, 3.6, 3.2, sway)):
        cx += s
        inside = ellipse(cx, cy, rx, ry)
        for y in range(32):
            for x in range(16):
                if inside(x, y):
                    u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                    g[y][x] = 'G' if u + v > 0.6 else 'c' if u + v < -0.95 else 'g'
    for x, y in ((5, 18), (9, 17), (7, 22), (11, 21)):           # leaf clumps broken by a line
        g[y][x] = 'K'
    return outline(g), {'c': FOLIAGE[0], 'g': FOLIAGE[1], 'G': FOLIAGE[2]}


# ---------------------------------------------------------------- 17. uprooted tree
def uprooted_tree():
    g = blank(48, 32)
    pick = lambda x, y, t, side: 'l' if side < -0.45 else 'd' if side > 0.35 else 'm'
    stroke(g, [(3, 25, 3.0), (14, 24, 4.6), (32, 22, 6.4)], 'm', pick)             # the trunk, lying
    stroke(g, [(10, 24.5, 1.8), (6, 18, 1.4), (4, 15, 1.0)], 'm', pick)            # snapped limbs
    stroke(g, [(19, 23, 2.0), (21, 16, 1.4), (24, 13, 1.0)], 'm', pick)
    ball = ellipse(37.5, 19.5, 5.5, 8.0)
    for y in range(32):
        for x in range(48):
            if ball(x, y) and y <= 29:
                g[y][x] = 'd'                                       # the root ball, earth in shade
    for pts in ([(37, 18, 1.6), (33, 9, 1.1), (30, 5, 0.9)], [(38, 17, 1.6), (41, 8, 1.1), (44, 4, 0.9)],
                [(39, 19, 1.5), (44, 17, 1.1), (46, 13, 0.9)], [(39, 21, 1.5), (44, 24, 1.0), (45, 28, 0.9)],
                [(37, 20, 1.3), (36, 28, 1.0)], [(36, 18, 1.3), (31, 13, 1.0), (29, 11, 0.9)],
                [(38, 18, 1.3), (37, 7, 1.0), (36, 3, 0.9)]):
        stroke(g, pts, 'm')                                         # roots torn out of it
    for x, y in ((36, 16), (37, 16), (38, 17), (36, 18), (38, 19)):                 # the trunk's heart
        g[y][x] = 'l'
    return outline(g), {'l': BARK[0], 'm': BARK[1], 'd': BARK[2]}


PROPS = [
    ('fallen_log', fallen_log), ('hollow_log', hollow_log), ('mossy_stump', mossy_stump),
    ('axe_stump', axe_stump), ('woodpile', woodpile), ('mushrooms', mushrooms), ('fern', fern),
    ('bramble', bramble), ('berry_bush', berry_bush), ('mossy_boulder', mossy_boulder),
    ('deer_skull', deer_skull), ('lean_to', lean_to), ('nest_stump', nest_stump),
    ('fallen_branch', fallen_branch), ('leaf_litter', leaf_litter), ('sapling', sapling),
    ('uprooted_tree', uprooted_tree),
]


def write(g, pal, path):
    from PIL import Image
    pal = dict(pal, K='000000')
    im = Image.new('RGBA', (len(g[0]), len(g)), (0, 0, 0, 0))
    for y, row in enumerate(g):
        for x, c in enumerate(row):
            if c != '.':
                im.putpixel((x, y), tuple(int(pal[c][i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    im.save(path)
    return im


if __name__ == '__main__':
    want = sys.argv[1:]
    for name, make in PROPS:
        if want and name not in want:
            continue
        if name == 'sapling':
            os.makedirs(os.path.join(HERE, 'sapling_frames'), exist_ok=True)
            frames = [make(k) for k in range(4)]
            for k, (g, pal) in enumerate(frames):
                write(g, pal, os.path.join(HERE, 'sapling_frames', f'sapling_{k}.png'))
            strip = [sum((f[0][y] for f in frames), []) for y in range(32)]
            write(strip, frames[0][1], os.path.join(HERE, 'sapling.png'))
        else:
            try:
                g, pal = make()
            except AssertionError as e:
                print(name, 'FAILED:', e)
                continue
            write(g, pal, os.path.join(HERE, name + '.png'))
        print(name)
