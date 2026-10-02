"""Shape helpers for the enemy generators in art/enemies/*_gen.py.

A grid is a list of rows of palette letters ('.' = empty). Parts are dicts
{(x, y): letter}; put() draws one with its own black outline, so parts drawn
back to front stay separate where they overlap."""
import os

def blank(w, h): return [['.'] * w for _ in range(h)]

def inside(g, x, y): return 0 <= y < len(g) and 0 <= x < len(g[0])

def put(g, cells):
    """Draw a part: cells with a 4-neighbour outside the part become outline."""
    for (x, y), c in cells.items():
        if not inside(g, x, y): continue
        edge = any((x + dx, y + dy) not in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        g[y][x] = 'K' if edge else c

def stamp(g, x0, y0, rows):
    """Paste hand-drawn rows; '.' leaves what is underneath."""
    for dy, r in enumerate(rows):
        for dx, c in enumerate(r):
            if c != '.' and inside(g, x0 + dx, y0 + dy): g[y0 + dy][x0 + dx] = c

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
            if (x, y) in cells and inside(g, x, y) and g[y][x] != 'K': g[y][x] = bone

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
            g[y][x] = hoof if y >= hy - 1 else c
            if inside(g, x + edge, y) and g[y][x + edge] != c: g[y][x + edge] = 'K'
    for x in (hx, hx + edge):
        if inside(g, x, hy): g[hy][x] = 'K'

def check_legs(g, bottom, top):
    """Every foot on row `bottom` connects, through its leg, up past row `top`
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
