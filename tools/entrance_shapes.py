"""Shared drawing helpers for the overworld dungeon-entrance designs.

A design is a grid of tone letters -- K line, D shade, M base, L lit, '.' for
nothing -- that an art/structures/entrances/*_design.py lays out with these and
hands to tools/draw_views.py, which draws it through the pixel plugin into the
.aseprite that is the source of truth. Light comes from the upper left.

Kept in one place so every entrance is built from the same stonework, outline
and shading rules: a pyramid's courses and a ruin's courses are one function,
not two that drift.
"""


class Grid:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [['.'] * w for _ in range(h)]

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else '.'

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = c

    def rows(self):
        return [''.join(r) for r in self.g]


def rect(x0, y0, x1, y1):
    """The set of pixels in a rectangle, inclusive."""
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def columns(tops, bottom):
    """A wall with a broken top: tops is [(x0, x1, top_y)], filled down to bottom."""
    s = set()
    for x0, x1, t in tops:
        s |= rect(x0, t, x1, bottom)
    return s


def courses(grid, mask, block_w=6, course_h=4, y0=0, x0=0, shade_right=1):
    """Fill mask with stone laid in staggered courses, like Dajna's pyramid: the
    top row of each block lit, the bed joint and the head joint in shade, the
    rest base. The mask's own right edge is in shade (the face turned from the
    light) and its top edge lit."""
    for (x, y) in mask:
        r = (y - y0) % course_h
        off = ((y - y0) // course_h) % 2 * (block_w // 2)
        if r == course_h - 1 or (x - x0 + off) % block_w == block_w - 1:
            c = 'D'
        elif r == 0:
            c = 'L'
        else:
            c = 'M'
        grid.put(x, y, c)
    for (x, y) in mask:
        if (x, y - 1) not in mask:
            grid.put(x, y, 'L')
        for i in range(1, shade_right + 1):
            if (x + i, y) not in mask and all((x + j, y) in mask for j in range(1, i)):
                grid.put(x, y, 'D')


def column(grid, x0, x1, top, bottom):
    """A round pillar: lit stripe on the left, shade on the right, a ring of
    shade every few rows where the drums meet."""
    for y in range(top, bottom + 1):
        for x in range(x0, x1 + 1):
            if x == x0:
                c = 'L'
            elif x >= x1 - (1 if x1 - x0 >= 4 else 0):
                c = 'D'
            else:
                c = 'M'
            if (y - top) % 5 == 4 and x != x0:
                c = 'D'
            grid.put(x, y, c)


def oblique(x, d, z, base):
    """The game's projection, measured off the town houses: the front face
    square on, depth going up and to the right at 45 degrees. A point x across,
    d back and z up lands at screen (x + d, base - z - d)."""
    return x + d, base - z - d


class Scene:
    """Blocks of stone in the oblique view, drawn with a depth buffer.

    Every pixel remembers how far back (d) the surface it shows is, and only a
    nearer surface may overwrite it -- so where pieces cross, the one in front
    wins whatever order they were added in. Each piece has an id; the black
    line goes round the outside of the whole drawing and along every edge where
    a piece stands in front of a different one, on the far piece's side, so
    the near piece keeps its full shape. Faces of one piece meet without a line
    (they differ by tone)."""

    def __init__(self, w, h, base):
        self.g = Grid(w, h)
        self.base = base
        self.depth = [[float('inf')] * w for _ in range(h)]
        self.pid = [[-1] * w for _ in range(h)]
        self.broken = {}
        self.slated = {}          # pid -> 'front' or 'slope': laid in slates at render

    def break_off(self, pids, x0, x1, y, amp, seed):
        """A piece broken off above a line that wanders a pixel at a time, as
        broken stone does: from here on those pieces are not drawn above it, so
        whatever stands behind them shows where they were. Before drawing, not
        after -- cutting a finished picture left a hole where the depth test had
        already thrown away what the piece hid."""
        import random
        rng = random.Random(seed)
        cut, line = y, {}
        for x in range(x0, x1 + 1):
            cut = max(y - amp, min(y + amp, cut + rng.choice((-1, 0, 0, 1))))
            line[x] = cut
        for p in pids:
            self.broken[p] = line

    def _gone(self, pid, x, y):
        line = self.broken.get(pid)
        return line is not None and x in line and y <= line[x]

    def _merge(self, tmp, depth_at, pid):
        for y in range(tmp.h):
            for x in range(tmp.w):
                c = tmp.g[y][x]
                if c == '.':
                    continue
                d = depth_at(x, y)
                if d <= self.depth[y][x] and not self._gone(pid, x, y):
                    self.g.g[y][x], self.depth[y][x], self.pid[y][x] = c, d, pid

    def box(self, pid, x0, x1, d0, d1, z0, z1, front='courses', block_w=6):
        """Its front face (stonework, a pillar's drum shading, or flat), its
        right side face in shade -- flat, like the houses' -- its top lit."""
        base = self.base
        t = Grid(self.g.w, self.g.h)
        sx0, sy1 = oblique(x0, d0, z0, base)
        sx1, sy0 = oblique(x1, d0, z1, base)
        face = rect(sx0, sy0, sx1, sy1)
        if front == 'courses':
            courses(t, face, block_w=block_w, y0=base % 4, x0=0, shade_right=0)
        elif front == 'column':
            column(t, sx0, sx1, sy0, sy1)
        else:
            fill(t, face, front)
        fill(t, rect(sx0, sy0, sx1, sy0), 'L')                 # the front face's lit top edge
        self._merge(t, lambda x, y: d0, pid)
        side, top = Grid(t.w, t.h), Grid(t.w, t.h)
        for d in range(d0 + 1, d1 + 1):
            x, ytop = oblique(x1, d, z1, base)
            _, ybot = oblique(x1, d, z0, base)
            fill(side, rect(x, ytop, x, ybot), 'D')
            xa, y = oblique(x0, d, z1, base)
            fill(top, rect(xa, y, x - 1, y), 'L')
        self._merge(side, lambda x, y: x - x1, pid)              # column x1+d is depth d
        self._merge(top, lambda x, y: base - z1 - y, pid)        # row base-z1-d is depth d

    def points(self, pid, pts, nearer=0.0):
        """A surface given as points (x, d, z, tone), each projected and kept
        only where nothing nearer is already drawn -- for faces that are not
        boxes: a roof's slopes, a pyramid's sides. `nearer` brings the whole
        surface that much forward in the depth test without moving it on the
        screen: a stair built out in front of the terraces it climbs."""
        # Fine patterns are not sampled here -- several samples land on each
        # pixel and the last decides it, which scrambles anything finer than
        # a pixel; they are laid on the screen afterwards (see slates).
        g, base = self.g, self.base
        for x, d, z, c in pts:
            sx, sy = oblique(x, d, z, base)
            sx, sy = int(round(sx)), int(round(sy))
            dd = d - nearer
            if (0 <= sx < g.w and 0 <= sy < g.h and dd <= self.depth[sy][sx]
                    and not self._gone(pid, sx, sy)):
                g.g[sy][sx], self.depth[sy][sx], self.pid[sy][sx] = c, dd, pid

    def gable(self, pid, x0, x1, d0, d1, z0, h, front_pid=None, shingles=False):
        """A gabled roof running back from d0 to d1 over x0..x1, eaves at z0
        and the ridge h above: its front triangle square on (base tone, the
        raking edges lit), the slope toward the light lit, the other in shade.
        Not 45 degrees steep, or a slope would stand edge-on to the view. The
        front triangle is a piece of its own (front_pid, by default pid + 1000)
        so a line parts it from the slopes behind it.

        shingles=True lays the roof in fish-scale slates rather than one sheet
        -- a pointed roof's front and both its slopes: rows four high running
        along the eaves, each slate's rounded lower edge curving under the
        row below, every row half a slate along from the last. Pale slates
        edged in grey where lit, dark ones edged lighter on the shaded slope;
        a scale, not a course, so a roof does not read as more of the wall."""
        xm, half = (x0 + x1) / 2, (x1 - x0) / 2
        top = lambda x: z0 + h * (1 - abs(x - xm) / half)
        step = 0.25

        fpid = pid + 1000 if front_pid is None else front_pid
        if shingles:
            self.slated[pid], self.slated[fpid] = 'slope', 'front'
        pts, front = [], []
        n = int((x1 - x0) / step)
        for i in range(n + 1):
            x = x0 + i * step
            dd = d0
            while dd <= d1:
                pts.append((x, dd, top(x), 'L' if x <= xm else 'D'))
                dd += step
            z = z0
            while z <= top(x):
                front.append((x, d0 - 0.01, z, 'L' if top(x) - z < 1.5 else 'M'))
                z += step
        self.points(pid, pts)
        self.points(fpid, front)

    def flat(self, pid, draw, d):
        """Anything drawn square-on at one depth: draw(grid) paints it."""
        t = Grid(self.g.w, self.g.h)
        draw(t)
        self._merge(t, lambda x, y: d, pid)

    def slates(self):
        """Lay the slated pieces in fish-scale slates, pixel by pixel on the
        screen, so the pattern is exact rather than sampled. A slate is six
        across and four up, its edge the U of its lower rim; each row half a
        slate along from the last. A pointed roof's front lies in level rows;
        a slope's rows follow its eaves, which run up and to the right at 45
        degrees here -- along an eave x + y is fixed, so that is the row's
        height. Pale slates edged in the base grey where lit, dark ones edged
        in it on the shaded slope."""
        def edge(along, up):
            row, t = up // 4, up % 4
            u = (along + (row % 2) * 3) % 6
            return (t == 0 and u in (2, 3)) or (t == 1 and u in (1, 4)) or (t == 2 and u in (0, 5))
        g, P = self.g, self.pid
        for y in range(g.h):
            for x in range(g.w):
                kind = self.slated.get(P[y][x])
                c = g.g[y][x]
                if kind is None or c not in 'LDM':
                    continue
                up = (self.base - y) if kind == 'front' else (self.base * 2 - x - y)
                if edge(x, up):
                    g.g[y][x] = 'M'
                elif kind == 'front':
                    g.g[y][x] = 'L'

    def render(self):
        g, D, P = self.g, self.depth, self.pid
        # A sliver of a face one pixel big, walled in by another face's tone
        # on all four sides, reads as a speck: it takes that tone.
        for y in range(1, g.h - 1):
            for x in range(1, g.w - 1):
                n = {g.g[y - 1][x], g.g[y + 1][x], g.g[y][x - 1], g.g[y][x + 1]}
                if len(n) == 1 and g.g[y][x] != '.' and '.' not in n and n != {g.g[y][x]}:
                    g.g[y][x] = n.pop()
        # after that, not before: a slate's curved rim is single pixels by
        # design, and the sliver rule would take them for specks
        self.slates()
        far =lambda q, p: (D[q[1]][q[0]], -P[q[1]][q[0]]) > (D[p[1]][p[0]], -P[p[1]][p[0]])
        line = set()
        for y in range(g.h):
            for x in range(g.w):
                if g.g[y][x] == '.':
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if not (0 <= q[0] < g.w and 0 <= q[1] < g.h):
                        continue
                    if g.g[q[1]][q[0]] == '.' or (P[q[1]][q[0]] != P[y][x] and far(q, (x, y))):
                        line.add(q)
        for x, y in line:
            g.g[y][x] = 'K'
        return g


def weather(grid, seed, faces, crack, chips=8, cracks=10, keep=()):
    """Age a finished drawing. chips: small bites out of its silhouette -- a
    corner knocked off a block -- each outlined again. cracks: short lines of
    the `crack` tone wandering across the `faces` tones. Seeded, so a design
    builds the same every time; `keep` is a list of rects (x0, y0, x1, y1)
    left alone, a doorway or a stair that must stay whole. Only tones already
    in the cell are used, so the four-colour rule holds."""
    import random
    rng = random.Random(seed)
    g = grid.g
    h, w = grid.h, grid.w
    kept = lambda x, y: any(a <= x <= c and b <= y <= d for a, b, c, d in keep)
    ink = lambda x, y: 0 <= x < w and 0 <= y < h and g[y][x] != '.'
    rim = [(x, y) for y in range(h) for x in range(w)
           if g[y][x] == 'K' and not kept(x, y) and y < h - 2
           and any(not ink(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, -1)))]
    for _ in range(chips):
        if not rim:
            break
        x, y = rng.choice(rim)
        bw, bh = rng.choice(((2, 1), (2, 2), (3, 1), (1, 2)))
        for yy in range(y, y + bh):
            for xx in range(x - bw // 2, x - bw // 2 + bw):
                if ink(xx, yy) and not kept(xx, yy):
                    g[yy][xx] = '.'
    # line the new edges, inward this time: the bite's own pixels are gone
    for y in range(h):
        for x in range(w):
            if g[y][x] not in '.K' and any(not ink(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 'K'
    face = [(x, y) for y in range(h) for x in range(w) if g[y][x] in faces and not kept(x, y)]
    for _ in range(cracks):
        if not face:
            break
        x, y = rng.choice(face)
        for _ in range(rng.randint(2, 4)):
            if not (0 <= x < w and 0 <= y < h):
                break                                   # wandered off the drawing
            if g[y][x] in faces and not kept(x, y):
                g[y][x] = crack
            x += rng.choice((-1, 1))
            y += 1


def drop_crumbs(grid, speck=16):
    """Sweep away anything left standing alone after a piece is broken off --
    a stretch of its outline, a corner -- smaller than `speck` pixels: what a
    break leaves behind is never a scatter of dots."""
    h, w = grid.h, grid.w
    seen = set()
    for y in range(h):
        for x in range(w):
            if grid.g[y][x] == '.' or (x, y) in seen:
                continue
            part, stack = [], [(x, y)]
            seen.add((x, y))
            while stack:
                px, py = stack.pop()
                part.append((px, py))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (px + dx, py + dy)
                    if 0 <= q[0] < w and 0 <= q[1] < h and q not in seen and grid.g[q[1]][q[0]] != '.':
                        seen.add(q)
                        stack.append(q)
            if len(part) < speck:
                for px, py in part:
                    grid.g[py][px] = '.'


def four_per_cell(grid, merge, cell=16):
    """The four-colour rule, kept by the drawing rather than broken and found
    later: in any cell with more than four tones, merge them away in the order
    given -- merge is [(tone, into), ...], the least needed first (a stone's
    lit and shaded edges before the glass in a window, say) -- until it fits."""
    for cy in range(0, grid.h, cell):
        for cx in range(0, grid.w, cell):
            pix = [(x, y) for y in range(cy, min(cy + cell, grid.h))
                   for x in range(cx, min(cx + cell, grid.w))]
            for tone, into in merge:
                if len({grid.g[y][x] for x, y in pix} - {'.'}) <= 4:
                    break
                for x, y in pix:
                    if grid.g[y][x] == tone:
                        grid.g[y][x] = into


def read_sprite(path, x0, y0, w, h, pal):
    """A piece of an existing export (path under art/structures/) as rows of
    tone letters, pal being {letter: 'rrggbb'} -- so a part drawn once, a
    ladder or a palm, is laid into other designs rather than drawn again."""
    import os
    from PIL import Image
    here = os.path.dirname(os.path.abspath(__file__))
    im = Image.open(os.path.join(here, '..', 'art', 'structures', path)).convert('RGBA')
    tone = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)): k for k, v in pal.items()}
    return [''.join(tone[im.getpixel((x0 + x, y0 + y))[:3]] if im.getpixel((x0 + x, y0 + y))[3] else '.'
                    for x in range(w)) for y in range(h)]


LADDER_TONES = {'x': '474751', 'y': '848694', 'z': 'bcbeca'}   # the cave's stone


def ladder_hole():
    """The ladder down a hole: every 1x1 way in looks like this. Read from the
    cave's own drawing (cave_entrance.png, x 48..63, in the stone tones), so
    there is one ladder; its tones are LADDER_TONES and black."""
    return read_sprite('cave_entrance.png', 48, 0, 16, 16, dict(LADDER_TONES, K='000000'))


def drum(grid, x0, x1, y0, y1):
    """A pillar lying on its side: lit along the top, shade along the bottom,
    a shaded ring where each drum meets the next."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            c = 'L' if y == y0 else 'D' if y >= y1 - 1 else 'M'
            if (x - x0) % 6 == 5 and y != y0:
                c = 'D'
            grid.put(x, y, c)


def fill(grid, mask, c):
    for (x, y) in mask:
        grid.put(x, y, c)


def outline(grid):
    """A 1px black line round everything drawn, on the outside."""
    ink = {(x, y) for y in range(grid.h) for x in range(grid.w) if grid.g[y][x] != '.'}
    for (x, y) in list(ink):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in ink:
                grid.put(x + dx, y + dy, 'K')


def stair(grid, x0, x1, top, bottom, tread=3):
    """A dark doorway with a stair going down into it: treads two rows deep
    (lit nose, shaded rise), lightest nearest the viewer, lost in the dark
    toward the back."""
    fill(grid, rect(x0, top, x1, bottom), 'K')
    for i, y in enumerate(range(bottom - 1, top + 3, -tread)):
        nose = 'LMD'[i] if i < 3 else None
        if nose is None:
            break
        fill(grid, rect(x0, y, x1, y), nose)
        if i < 2:
            fill(grid, rect(x0, y + 1, x1, y + 1), 'D')


def check(grid, name, objects=False, speck=16):
    """The rules every entrance keeps: nothing on the top or side edges of its
    block (the bottom row is the ground it stands on), and no loose specks.
    A building is one drawing and must be in one piece. A scene of separate
    things -- a pool and the palms beside it -- passes objects=True: then
    every piece must be a whole thing, at least `speck` pixels."""
    rows = grid.rows()
    ink = {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}
    edge = [p for p in ink if p[0] in (0, grid.w - 1) or p[1] == 0]
    assert not edge, f"{name}: touches its block's edge at {sorted(edge)[:4]}"
    left, parts = set(ink), []
    while left:
        seen, stack = set(), [next(iter(left))]
        while stack:
            p = stack.pop()
            if p in seen:
                continue
            seen.add(p)
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (p[0] + d[0], p[1] + d[1])
                if q in left and q not in seen:
                    stack.append(q)
        left -= seen
        parts.append(seen)
    if not objects:
        assert len(parts) == 1, f"{name}: {len(ink) - max(map(len, parts))} pixels not joined to the rest"
        return
    small = [min(p) for p in parts if len(p) < speck]
    assert not small, f"{name}: loose specks at {small[:4]}"
