"""Shape helpers for the enemy generators in art/enemies/*_gen.py.

A grid is a list of rows of palette letters ('.' = empty). Parts are dicts
{(x, y): letter}; put() draws one with its own black outline, so parts drawn
back to front stay separate where they overlap."""
import math, os

class Canvas(list):
    """Rows of letters. `ox` shifts every helper's x so a big enemy can be drawn
    in its usual coordinates on a wider canvas without parts falling off the
    left edge; generators that index rows directly keep ox = 0."""
    ox = 0

def blank(w, h, ox=0):
    g = Canvas(['.'] * w for _ in range(h)); g.ox = ox
    return g

def ox(g): return getattr(g, 'ox', 0)

def inside(g, x, y): return 0 <= y < len(g) and 0 <= x + ox(g) < len(g[0])

def get(g, x, y): return g[y][x + ox(g)]

def set_(g, x, y, c): g[y][x + ox(g)] = c

def put(g, cells):
    """Draw a part: cells with a 4-neighbour outside the part become outline."""
    for (x, y), c in cells.items():
        if not inside(g, x, y): continue
        edge = any((x + dx, y + dy) not in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        set_(g, x, y, 'K' if edge else c)

def stamp(g, x0, y0, rows):
    """Paste hand-drawn rows; '.' leaves what is underneath."""
    for dy, r in enumerate(rows):
        for dx, c in enumerate(r):
            if c != '.' and inside(g, x0 + dx, y0 + dy): set_(g, x0 + dx, y0 + dy, c)

def ellipse(cx, cy, rx, ry, colour):
    """colour(x, y, t) -> letter, t = 0 at the top row .. 1 at the bottom."""
    return {(x, y): colour(x, y, (y - (cy - ry)) / (2 * ry))
            for y in range(int(cy - ry), int(cy + ry) + 1)
            for x in range(int(cx - rx), int(cx + rx) + 1)
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1}

def rect(x0, y0, x1, y1, c):
    return {(x, y): c for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}

def thick_line(x0, y0, x1, y1, r, c):
    """A round-ended line of radius r; c is a letter or colour(x, y, d) with d
    the distance from the line's centre."""
    cells = {}
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n); y = round(y0 + (y1 - y0) * i / n)
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                d2 = dx * dx + dy * dy
                if d2 <= r * r + 1:
                    p = (x + dx, y + dy); d = d2 ** 0.5
                    if p not in cells or d < cells[p][1]:
                        cells[p] = (c if isinstance(c, str) else c(*p, d), d)
    return {p: v[0] for p, v in cells.items()}

def polygon(points, c):
    """Filled polygon (even-odd rule, pixel centres)."""
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    cells = {}
    for y in range(int(min(ys)), int(max(ys)) + 1):
        for x in range(int(min(xs)), int(max(xs)) + 1):
            px, py, hit = x + 0.5, y + 0.5, False
            for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
                if (ay > py) != (by > py) and px < ax + (py - ay) * (bx - ax) / (by - ay):
                    hit = not hit
            if hit: cells[(x, y)] = c if isinstance(c, str) else c(x, y)
    return cells

def tube(points, radii, colour):
    """One body along a path of points (radius per stretch), outlined once --
    no seams between stretches. colour(d, below) gives each cell's letter from
    its distance d to the nearest stretch's centre line and whether it is on
    the right of the path's direction (below, for a path running left to right)."""
    best = {}
    for (a, b), r in zip(zip(points, points[1:]), radii):
        (ax, ay), (bx, by) = a, b
        L2 = max((bx - ax) ** 2 + (by - ay) ** 2, 1)
        for p in thick_line(ax, ay, bx, by, r, 'x'):
            px, py = p
            u = min(max(((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / L2, 0), 1)
            d = ((px - ax - u * (bx - ax)) ** 2 + (py - ay - u * (by - ay)) ** 2) ** 0.5
            below = (bx - ax) * (py - ay) - (by - ay) * (px - ax) > 0
            if p not in best or d < best[p][0]: best[p] = (d, below)
    return {p: colour(d, below) for p, (d, below) in best.items()}

def edges(cells):
    """For shading a part: at(x, y) is 1 near its lit edge (top / left), -1
    near its shaded one (bottom / right), else 0 -- light from the up-left."""
    rmin, rmax, cmin, cmax = {}, {}, {}, {}
    for (x, y) in cells:
        rmin[y] = min(rmin.get(y, 999), x); rmax[y] = max(rmax.get(y, -1), x)
        cmin[x] = min(cmin.get(x, 999), y); cmax[x] = max(cmax.get(x, -1), y)
    def at(x, y):
        if x >= rmax[y] - 2 or y >= cmax[x] - 1: return -1
        if x <= rmin[y] + 1 or y <= cmin[x] + 1: return 1
        return 0
    return at

def shaded(light, mid, dark):
    """A painter for skeleton parts: `mid`, with `light` along the part's
    top-left edge and `dark` along its bottom-right."""
    def paint(cells):
        at = edges(cells)
        return {(x, y): {1: light, 0: mid, -1: dark}[at(x, y)] for (x, y) in cells}
    return paint

# ── 3D skeletons: a creature laid out once as tubes and balls in body space,
# turned to each view and composited with a per-pixel depth buffer ──
YAW = {'D': 0, 'DR': 45, 'R': 90, 'UR': 135, 'U': 180}   # degrees the creature has turned from facing you

def turn(p, yaw, cx, ground, scale=1.0):
    """Body space (x to the creature's left -- your right from the front --,
    y up, z forward) -> screen (x, y) and depth (px, larger = nearer you)."""
    x, y, z = p
    a = math.radians(yaw)
    X = x * math.cos(a) + z * math.sin(a)
    D = -x * math.sin(a) + z * math.cos(a)
    return cx + X * scale, ground - y * scale, D * scale

def facing_dir(yaw, s=1, toward=1):
    """A body-space direction (dx, dz) that lies across the screen in this
    view -- so a curl or fan laid along it is never seen edge-on -- pointing
    toward the creature's front (toward=1) or back (-1); from straight in
    front or behind, out to its side `s` instead."""
    a = math.radians(yaw)
    dx, dz = math.cos(a), math.sin(a)
    if abs(dz) < 1e-6: return s * abs(dx), 0.0
    return (dx, dz) if dz * toward > 0 else (-dx, -dz)

def spiral(centre, d, r, a0, sweep, tighten=0.35, n=7):
    """Points round a curl in the plane of direction d = (dx, dz) and up:
    from angle a0 through `sweep` radians, the radius tightening by
    `tighten` of itself by the end."""
    cx, cy, cz = centre
    out = []
    for k in range(1, n + 1):
        a = a0 + sweep * k / n
        rr = r * (1 - tighten * k / n)
        out.append((cx + d[0] * rr * math.cos(a), cy + rr * math.sin(a), cz + d[1] * rr * math.cos(a)))
    return out

def skeleton(g, parts, yaw, cx, ground, scale=1.0, jump=None):
    """Draw the parts -- (kind, points, radii, paint[, bias[, group]]): 'tube'
    through 3D points (a radius per stretch) or 'ball' at one point
    (rx, ry[, rz]); paint(cells) colours a part's cells -- turned by `yaw`.
    Every pixel gets its own depth (along a tube's axis plus the bulge of its
    round surface toward you; + bias, to force a part in front), the nearest
    part wins it, and a part's edge pixels are its outline -- so a long limb
    can pass in front of one thing and behind another. Parts sharing a
    `group` are one seamless shape: outlined only round the group's outside,
    no lines where they join (legs into a body, a neck into a head), only
    where one part stands more than `jump` px (default JUMP) in front of another."""
    zbuf, drawn, groups = {}, [], {}
    for kind, pts, rad, paint, *extra in parts:
        pp = [turn(p, yaw, cx, ground, scale) for p in pts]
        if kind == 'tube':
            radii = [r * scale for r in rad[:len(pp) - 1]]
            cells = paint(tube([(round(x), round(y)) for x, y, z in pp], tuple(round(r) for r in radii), lambda *a: '?'))
        else:
            radii = None
            cells = paint(ellipse(pp[0][0], pp[0][1], rad[0] * scale, rad[1] * scale, lambda *a: '?'))
        bias = extra[0] if extra else 0
        group = extra[1] if len(extra) > 1 else None
        if group is not None: groups.setdefault(group, set()).update(cells)
        drawn.append((kind, pp, rad, radii, cells, bias, group))
    for kind, pp, rad, radii, cells, bias, group in drawn:
        shape = groups[group] if group is not None else cells
        for (x, y), c in cells.items():
            px, py = x + 0.5, y + 0.5
            if kind == 'tube':
                best = None
                for i, ((x0, y0, z0), (x1, y1, z1)) in enumerate(zip(pp, pp[1:])):
                    dx, dy = x1 - x0, y1 - y0
                    L = dx * dx + dy * dy
                    u = 0 if L == 0 else max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / L))
                    d = math.hypot(px - (x0 + u * dx), py - (y0 + u * dy))
                    if best is None or d < best[0]: best = (d, z0 + u * (z1 - z0), radii[i])
                d, zc, r = best
            else:
                rz = rad[2] if len(rad) > 2 else (rad[0] + rad[1]) / 2           # the ball's depth radius
                n = math.hypot((px - pp[0][0]) / (rad[0] * scale), (py - pp[0][1]) / (rad[1] * scale))
                d, zc, r = min(n, 1) * rz * scale, pp[0][2], rz * scale
            depth = zc + math.sqrt(max(0.0, r * r - d * d)) + bias
            edge = any((x + ex, y + ey) not in shape for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if inside(g, x, y) and ((x, y) not in zbuf or depth > zbuf[(x, y)][0]):
                zbuf[(x, y)] = (depth, 'K' if edge else c, group)
    # Within a seamless group, still outline where one part stands clearly in
    # front of another (a near leg over a far one): a jump in depth, not a join.
    out = {}
    for (x, y), (depth, c, group) in zbuf.items():
        if group is not None and c != 'K':
            for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = zbuf.get((x + ex, y + ey))
                if n and n[2] == group and depth - n[0] > (JUMP if jump is None else jump) * scale:
                    c = 'K'; break
        out[(x, y)] = c
    for (x, y), c in out.items(): set_(g, x, y, c)

JUMP = 3      # px of depth between neighbouring pixels of one seamless shape that still draws a line

def bat_wing(g, shoulder, wrist, tips, trail, membrane, bone, flap=(0, 0)):
    """Draw a bat wing: arm shoulder->wrist, three fingers wrist->tips, a broad
    membrane scalloped between the fingertips, back to the body at `trail`.
    `flap` moves the tips by (dx, dy) and the wrist half as far."""
    fx, fy = flap
    wrist = (wrist[0] + fx // 2, wrist[1] + fy // 2)
    tips = [(x + fx, y + fy) for x, y in tips]
    notch = lambda a, b: (round((a[0] + b[0]) * 0.35 + wrist[0] * 0.3), round((a[1] + b[1]) * 0.35 + wrist[1] * 0.3))
    cells = polygon([shoulder, wrist, tips[0], notch(tips[0], tips[1]), tips[1],
                     notch(tips[1], tips[2]), tips[2], trail], membrane)
    put(g, cells)
    for a, b in [(shoulder, wrist)] + [(wrist, tp) for tp in tips]:
        for (x, y) in thick_line(*a, *b, 0, bone):
            if (x, y) in cells and inside(g, x, y) and get(g, x, y) != 'K': set_(g, x, y, bone)

def top_of(cells, x):
    ys = [y for (cx, y) in cells if cx == x]
    return min(ys) if ys else None

def slim_leg(g, points, c, edge, hoof):
    """A slender 2-pixel leg along a path of joints (hip, knee/hock, hoof):
    the leg colour, a black outline on the `edge` side (-1 left, +1 right),
    and `hoof` on its last two rows over a black sole."""
    hx, hy = points[-1]
    for a, b in zip(points, points[1:]):
        for (x, y) in thick_line(*a, *b, 0, c):
            if not inside(g, x, y): continue
            set_(g, x, y, hoof if y >= hy - 1 else c)
            if inside(g, x + edge, y) and get(g, x + edge, y) != c: set_(g, x + edge, y, 'K')
    for x in (hx, hx + edge):
        if inside(g, x, hy): set_(g, x, hy, 'K')

def check_legs(g, bottom, top):
    """(Works on the raw canvas, so it is unaffected by ox.) Every foot on row `bottom` connects, through its leg, up past row `top`
    (where the legs start, inside the body) -- no leg hangs off with nothing
    above it. Follows the leg's pixels, so bent and angled legs pass."""
    h, w = len(g), len(g[0])
    for x in range(w):
        if g[bottom][x] == '.': continue
        seen, todo, ok = {(x, bottom)}, [(x, bottom)], False
        while todo and not ok:
            cx, cy = todo.pop()
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy - 1), (cx, cy + 1)):
                if 0 <= nx < w and 0 <= ny <= bottom and (nx, ny) not in seen and g[ny][nx] != '.':
                    ok = ok or ny < top
                    seen.add((nx, ny)); todo.append((nx, ny))
        assert ok, f'foot at column {x} does not reach the body above row {top}'

def views_reader(png, pal):
    """For views hand-drawn with the plugin (NN_views.png): returns
    grab(x, y, w, h) -> rows of palette letters ('.' = transparent)."""
    from PIL import Image
    im = Image.open(png).convert('RGBA')
    letter = {tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)): k for k, h in pal.items()}
    px = lambda x, y: '.' if im.getpixel((x, y))[3] == 0 else letter[im.getpixel((x, y))[:3]]
    return lambda x0, y0, w, h: [''.join(px(x0 + x, y0 + y) for x in range(w)) for y in range(h)]

def float_frame(view_rows, n, mouth=None, size=None, bob=(1, 0, 2), x=1):
    """Idle frame n for a floating enemy drawn as plugin views: the view bobs
    (rest, up, down -- its top row in the frame per `bob`) and on the way down
    an open mouth (rows, (x, y) on the view) replaces the shut one."""
    v = [list(r) for r in view_rows]
    if n == 2 and mouth: stamp(v, *mouth[1], mouth[0])
    g = blank(*size)
    stamp(g, x, bob[n], [''.join(r) for r in v])
    return g

def lift(rows, pivot):
    """Breathing in: the rows above `pivot` rise one pixel (the pivot row is
    doubled), the rows below -- legs, feet -- stay put."""
    assert not rows[0].strip('.'), 'breathing would lift the top row off the canvas'
    return rows[1:pivot + 1] + rows[pivot:]

def rising_frame(layers, size, x, top, lean):
    """A creature rising out of water, drawn as plugin layers (behind, the
    body that moves, in front): the moving layer's row y shifts sideways by
    lean(y) -- so it can sway, more toward the top -- and everything sits with
    its top row at `top` (the heave)."""
    behind, body, front = layers
    g = blank(*size)
    stamp(g, x, top, behind)
    for y, r in enumerate(body): stamp(g, x + lean(y), top + y, [r])
    stamp(g, x, top, front)
    return g

def sea(g, n, water, cx, rx, frames, letters='AaW'):
    """Water (or sand) over everything from row `water` down: a flat oval pool
    centred at cx, ripple dashes drifting a step each of the `frames` frames
    (frame n), foam (or kicked-up dust) either side of each part breaking the
    surface. `letters`: the pool, its ripples, the foam."""
    pool, ripple, foam = letters
    w, h = len(g[0]), len(g)
    body = [g[water - 1][x] != '.' for x in range(w)]
    for y in range(water, h):
        for x in range(w):
            g[y][x] = pool if ((x - cx) / rx) ** 2 + ((y - water - 2) / 6.5) ** 2 <= 1 else '.'
    for y, step in ((water, 0), (water + 3, 3)):
        for x in range(w):
            if g[y][x] == pool and (x - n + step) % frames < 2: g[y][x] = ripple
    for x in range(w):
        if body[x] and (x == 0 or not body[x - 1] or x == w - 1 or not body[x + 1]):
            for xx in (x - 1, x, x + 1):
                if 0 <= xx < w and g[water][xx] != '.': g[water][xx] = foam

def drawn_frames(png, pal, vw, vh, frames=3, order=('D', 'DR', 'R', 'UR', 'U')):
    """Views drawn whole for every frame with the plugin -- row n of the
    exported sheet is frame n -- laid out as build sections (R, R@1, ...)
    with a 1 px margin each side (the build adds a top row)."""
    grab = views_reader(png, pal)
    return {view + (f'@{n}' if n else ''): ['.' + r + '.' for r in grab(i * vw, n * vh, vw, vh)]
            for n in range(frames) for i, view in enumerate(order)}

def write(path, pal, header, views, patches=()):
    """Write a build_enemy.py source: #PAL, extra header lines, each view, then
    (frame, x, y, view, rows) patches."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write('#PAL\n' + ''.join(f'{k} {v}\n' for k, v in pal.items()) + header)
        for k, g in views.items():
            f.write('#' + k + '\n' + '\n'.join(''.join(r) for r in g) + '\n')
        for n, x, y, view, rows in patches:
            f.write(f'#PATCH{n} {x} {y} {view}\n' + '\n'.join(rows) + '\n')

def source_path(gen_file):
    """art/enemies/NN_name_gen.py -> art/enemies/NN_name.txt"""
    return os.path.join(os.path.dirname(os.path.abspath(gen_file)),
                        os.path.basename(gen_file).replace('_gen.py', '.txt'))
