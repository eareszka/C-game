"""The starting town's houses, built the way the game's first house sprite
was (sheet cells 1-6 x 0-5): a brick front wall square on, the front slope of
its roof in rows of shingles above it, its gable end receding up and to the
right in the oblique view (entrance_shapes.oblique) a step darker than the
front, in the brick's base tone, plank doors, black lines. The brick is laid in courses, as the catacombs'
and the church's are: cream mortar, each brick its base tone shaded along
its bottom and right edge -- three tones and the black fill a tile. So that
every brick keeps all three, the windows and the doors are drawn in those
tones too, as the user's reference (a Mother-style house) draws its own: black
frames and bars, panes of the cream, a door of the brick's shade. The walls
start on a tile row under the eave (34 or 66 high), and a chimney stands
behind a ridge on a tile row, so no brick shares a tile with the roof.
A design lays out a house from these parts and hands
it to tools/draw_views.py, which draws it through the pixel plugin.

Tones: K line; B brick (also the side face), S its shade (also the door);
M mortar (also the trim and the panes); R roof.

The coastal town's houses (art/structures/coast/) are the same parts in white
clapboard: House(cw, ch, clapboard_tone), B the paint and S the shadow under
each board, M the paint of the shutters, the casing and the panes, and a
chimney in its own red brick (tones=CHIMNEY).

Every pixel says the ground row it stands over (Grid.footy) and each wing the
ground it covers (Grid.foot), for the game's per-pixel collision and for
what is drawn over the player.
"""
from entrance_shapes import Grid, stand, depth_layers, check, four_per_cell

BRICK_W, COURSE_H = 6, 4    # the catacombs' bond: a brick six across, a course four high

DOOR_W, DOOR_H = 12, 22    # every house's door

# 3x5 capitals for a sign
FONT = {'B': ['##.', '#.#', '##.', '#.#', '##.'], 'O': ['.#.', '#.#', '#.#', '#.#', '.#.'],
        'K': ['#.#', '#.#', '##.', '#.#', '#.#'], 'S': ['.##', '#..', '.#.', '..#', '##.'],
        'T': ['###', '.#.', '.#.', '.#.', '.#.'], 'R': ['##.', '#.#', '##.', '#.#', '#.#'],
        'E': ['###', '#..', '##.', '#..', '###'], 'I': ['###', '.#.', '.#.', '.#.', '###'],
        'N': ['###', '#.#', '#.#', '#.#', '#.#']}

CHIMNEY = {'B': 'X', 'S': 'x', 'M': 'x'}    # a chimney's own brick on a house that is not brick


def brick_tone(rx, ry):
    """The bond, rx across and ry down from the wall's top left: a row of
    mortar atop each course, a mortar joint between the bricks, half a brick
    along from the course above; each brick shaded along its bottom row and
    its right edge."""
    r = ry % COURSE_H
    lx = (rx + (ry // COURSE_H) % 2 * (BRICK_W // 2)) % BRICK_W
    if r == 0 or lx == 0:
        return 'M'
    if r == COURSE_H - 1 or lx == BRICK_W - 1:
        return 'S'
    return 'B'


def clapboard_tone(rx, ry):
    """Boards laid in the brick's courses, four high: the board its base tone,
    the shadow under it along its bottom row. No joints."""
    return 'S' if ry % COURSE_H == COURSE_H - 1 else 'B'


# The villages' walls (art/structures/villages/): each a material laid in
# units, as the brick is, in the house's four letters.
def timber_tone(rx, ry):
    """A timber frame: posts two wide every ten across and a beam two deep
    every sixteen down, in the shade's letter (the timber), the panels
    between them plaster, the base."""
    return 'S' if rx % 10 < 2 or ry % 16 < 2 else 'B'


def adobe_tone(rx, ry):
    """Adobe blocks in wide plain courses, eight high: the lit top row of each
    in the mortar's letter, its bottom row the shade, no joints."""
    r = ry % 8
    return 'M' if r == 0 else 'S' if r == 7 else 'B'


def log_tone(rx, ry):
    """Logs laid one on the next, four high: the lit line along the top of
    each (the mortar's letter), the dark under it (the shade), the log between."""
    r = ry % COURSE_H
    return 'M' if r == 0 else 'S' if r == COURSE_H - 1 else 'B'


def pyramid_tone(rx, ry):
    """The pyramid's sandstone (entrances/pyramid_design.py stone()): blocks
    eight along in courses four high, a bed of mortar under each course and a
    joint between the blocks, half a block along from the course above; the
    face lit, the base -- its shade is the side turned away."""
    course = ry // COURSE_H
    if ry % COURSE_H == COURSE_H - 1 or (rx + (course % 2) * 4) % 8 == 0:
        return 'M'
    return 'B'


def triangle(put, a, b, c, tone):
    """A filled triangle a, b, c, black along its edge."""
    side = lambda p, q, r: (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    xs, ys = [p[0] for p in (a, b, c)], [p[1] for p in (a, b, c)]
    pts = set()
    for x in range(min(xs), max(xs) + 1):
        for y in range(min(ys), max(ys) + 1):
            v = [side(a, b, (x, y)), side(b, c, (x, y)), side(c, a, (x, y))]
            if all(i >= 0 for i in v) or all(i <= 0 for i in v):
                pts.add((x, y))
    for x, y in pts:
        edge = any((x + i, y + j) not in pts for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        put(x, y, 'K' if edge else tone)


class House:
    """A block cw x ch cells; the ground line its front stands on is the
    bottom row. A point x across, d back and z up lands at (x + d, B - z - d).
    tone(rx, ry) is what its walls are laid in."""
    def __init__(self, cw, ch, tone=brick_tone):
        self.tone = tone
        self.w, self.h = cw * 16, ch * 16
        self.B = self.h - 1
        self.c, self.f = {}, {}
        self.foot = set()

    def put(self, x, y, c, f):
        """The nearer -- the lower ground row -- wins; a tie goes to the later."""
        if 0 <= x < self.w and 0 <= y < self.h and c and f >= self.f.get((x, y), -1):
            self.c[(x, y)], self.f[(x, y)] = c, f

    def wing(self, x0, x1, depth, wall, rise, d0=0, eave=2, ridge=0.7, side='B'):
        """A brick block x0..x1 across, its front d0 back from the ground line
        and depth deep, its wall `wall` high, under a gabled roof `rise` above
        that -- its ridge `ridge` of the way back, as the first house's is, so
        the front slope is long -- or rise 0, a flat roof behind the wall. Its
        side in the tone `side`, a step darker than the front looks."""
        B = self.B
        d1, mid = d0 + depth, d0 + depth * ridge
        # The gable end, in the mortar's tone, and the roof's back edge. The
        # ridge stops where the gable's peak is -- it does not overhang the
        # side as the eave overhangs the front -- and from that corner one
        # line runs down and out to the wall's back corner: the gable fills up
        # to it and the roof is cut off by it, so the corner is one clean
        # point (the user's fix to the sheet, 2026-10-05).
        qx, qy = x1 + d1, B - wall - d1
        if rise:
            ax, ay = x1 + int(round(mid)) - 1, B - (wall + rise) - int(mid)
            # the roof's back edge overhangs the back wall by a pixel, as
            # the eave does the front, then the wall's corner runs down
            outer = lambda y: ax if y <= ay else qx if y >= qy else \
                int(round(ax + (qx + 1 - ax) * (y - ay) / (qy - ay)))
        else:
            ay, outer = qy - (qx - x1 - d0), lambda y: qx
        roof = self._slope(x0, x1, d0, mid, wall, rise, eave, outer) if rise else set()
        gable = set()
        for y in range(ay, B + 1):
            for x in range(x1 + d0, outer(y) + 1):
                if y <= B - (x - x1) and (rise or y >= qy + (qx - x)):
                    gable.add((x, y))
        # Black round it as the first house's is: the corner with the front
        # wall and the ground line, three pixels wide along the back of the
        # roof as it steps down, then two down the wall's back corner.
        for x, y in gable - roof:                            # the roof, nearer, keeps its own
            d = x - x1
            band = 3 if y < qy else 2
            edge = (d in (d0, d0 + 1) or y == B - d or (x, y - 1) not in gable
                    or any((x + i, y) not in gable for i in range(1, band + 1)))
            self.put(x, y, 'K' if edge else side, B - d)
        yt = B - d0 - wall + 1                               # the front wall
        for y in range(yt, B - d0 + 1):
            for x in range(x0, x1 + 1):
                c = 'K' if x == x0 or y == B - d0 else self.tone(x - x0, y - yt)
                self.put(x + d0, y, c, B - d0)
        if not rise:
            for d in range(d0, d1 + 1):                      # the flat roof's top
                for x in range(x0, x1 + 1):
                    edge = x in (x0, x1) or d in (d0, d1)
                    self.put(x + d, B - wall - d, 'K' if edge else 'R', B - d)
        self.foot |= {(x + d, B - d) for x in range(x0, x1 + 1) for d in range(d0, d1 + 1)}

    def _slope(self, x0, x1, d0, mid, wall, rise, eave, outer):
        """The roof's front slope: rows of shingles six deep (two black, four
        of tiles), the tiles eight across, half a tile along from the row
        below, the lower half of each joint doubled; a black eave four deep
        and a black ridge; each row cut off at the gable's back edge,
        outer(y), black for its last two pixels. Gives back the pixels laid."""
        B = self.B
        de, ze = d0 - eave, wall                             # the eave, overhanging
        drawn = set()
        ye, yr = B - ze - de, B - (wall + rise) - int(mid)
        for y in range(yr, ye + 1):
            t = (ye - y) / max(1, ye - yr)
            d = de + t * (mid - de)
            sx = int(round(d))
            rr = y - yr
            band, within = rr // 6, rr % 6
            bd = de + (ye - (yr + band * 6 + 3)) / max(1, ye - yr) * (mid - de)
            off = (7 if band % 2 == 0 else 3) + int(round(bd))
            end = min(x1 + eave + sx, outer(y))
            for x in range(x0 - eave + sx, end + 1):
                if within < 2 or y > ye - 4 or x == x0 - eave + sx or x >= end - 1:
                    c = 'K'
                else:
                    lx = (x - off) % 8
                    c = 'K' if lx == 0 or (within >= 4 and lx == 7) else 'R'
                self.put(x, y, c, B - sx)
                drawn.add((x, y))
        return drawn

    def barn(self, x0, x1, depth, wall, h1, h2):
        """A barn: its gable end to the front under a gambrel roof running
        back. The wall `wall` high in the house's tone; above it the end in
        the plain base tone, two pixels of trim up its raking edges and down
        the corners; the roof `depth` back in the roof's tone, black along the
        ridge, the two breaks (h1 up the steep lower slopes) and the eaves,
        and a row line every six pixels back; under the right eave its side
        in the shade, black on the ground line and the back corner, as a
        wing's is. The ground under it is stood on."""
        B = self.B
        xm, half = (x0 + x1) / 2.0, (x1 - x0) / 2.0
        def top(x):
            t = abs(x - xm) / half                          # 0 at the ridge, 1 at the eave
            return h1 + h2 * (1 - t / 0.5) if t <= 0.5 else h1 * (1 - (t - 0.5) / 0.5)
        yt = B - wall + 1
        for y in range(yt, B + 1):                           # the wall
            for x in range(x0, x1 + 1):
                c = 'K' if x in (x0, x1) or y == B else self.tone(x - x0, y - yt)
                if x0 < x <= x0 + 2 or x1 - 2 <= x < x1:
                    c = 'M'
                self.put(x, y, c, B)
        for x in range(x0, x1 + 1):                          # the end above it
            zt = wall + top(x)
            for z in range(wall, int(zt) + 1):
                c = 'M' if zt - z < 2.5 else 'B'
                if z == int(zt) or x in (x0, x1):
                    c = 'K'
                self.put(x, y := B - z, c, B)
        for d in range(1, depth + 1):                        # the roof, back from the front edge
            for i in range(2 * (x1 - x0) + 1):
                x = x0 + i * 0.5
                z = wall + top(x)
                sx, sy = int(round(x + d)), int(round(B - z - d))
                line = (x <= x0 or x >= x1 or abs(x - xm) < 1 or abs(abs(x - xm) - half * 0.5) < 1
                        or d == depth or d % 6 == 0)
                c = 'K' if line else 'R'
                self.put(sx, sy, c, B - d)
                self.put(sx, sy + 1, c, B - d)               # the sheet is solid: fill down to the step before
            for x in (x0, x1):                               # the eaves' lower edge, so each step back is joined
                self.put(x + d, B - wall - d + 1, 'K', B - d)
            for z in range(wall):                            # the side, up to the eave
                self.put(x1 + d, B - z - d, 'K' if z == 0 or d == depth else 'S', B - d)
        self.foot |= {(x + d, B - d) for x in range(x0, x1 + 1) for d in range(depth + 1)}

    def barn_door(self, x0, w, h=30):
        """A barn door `w` wide and `h` high on the ground line: planks in the
        shade with black between, a frame and an X brace in the trim."""
        B = self.B
        for y in range(B - h, B):
            for x in range(x0, x0 + w):
                lx, ly = x - x0, y - (B - h)
                edge = lx in (0, w - 1) or ly in (0, h - 1)
                cross = abs(lx * (h - 1) - ly * (w - 1)) < w - 1 or abs((w - 1 - lx) * (h - 1) - ly * (w - 1)) < w - 1
                self.put(x, y, 'M' if edge or cross else 'K' if lx % 4 == 0 else 'S', B)

    def round_wall(self, cx, cd, rx, rd, wall):
        """A round wall in the oblique view: the rim of the ellipse cx, cd by
        rx, rd in the plan, raised `wall` high where it is turned to the
        viewer or to the right (the back-left of it is hidden by the rest),
        laid in the wall's tone along the rim so its courses run round, the
        part turned away to the right in the shade; black at its foot and
        its top. The ground inside the rim is what it stands on."""
        import math
        B = self.B
        n = int(2 * math.pi * max(rx, rd) * 3)
        for i in range(n):
            th = 2 * math.pi * i / n
            x, d = cx + rx * math.cos(th), cd + rd * math.sin(th)        # d grows back
            nx, nd = math.cos(th) / rx, math.sin(th) / rd                 # the outward normal
            if nd > 0 and nx <= 0:
                continue
            sx, f = int(round(x + d)), B - int(round(d))
            along = int(round(rx * th))
            for z in range(wall + 1):
                sy = int(round(B - z - d))
                c = 'K' if z == 0 or z == wall else self.tone(along, wall - z)
                if nx > 0.35 and c == 'B':
                    c = 'S'
                self.put(sx, sy, c, f)
        for d in range(int(cd - rd), int(cd + rd) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                if ((x - cx) / rx) ** 2 + ((d - cd) / rd) ** 2 <= 1:
                    self.foot.add((x + d, B - d))

    def dome(self, x0, x1, d0, depth, wall, rise, shade='T'):
        """A dome over the wall's top, x0..x1 across and `depth` back from
        d0, `rise` high at its crown: a half ball in the roof's tone, its
        rows laid with a black line every six (hay, a dome of it), the side
        turned from the light -- the right and the back -- in `shade`. The
        surface is sampled finely and each point stands over the ground row
        of its depth, so the nearer wins as everywhere."""
        import math
        B = self.B
        cx, cd = (x0 + x1) / 2.0, d0 + depth / 2.0
        rx, rd = (x1 - x0) / 2.0, depth / 2.0
        n = int(2 * max(rx, rd) * 4)
        for i in range(n + 1):
            for j in range(n + 1):
                u, v = -1 + 2.0 * i / n, -1 + 2.0 * j / n
                q = u * u + v * v
                if q > 1:
                    continue
                zf = math.sqrt(1 - q)
                x, d, z = cx + u * rx, cd + v * rd, wall + rise * zf
                sx, sy = int(round(x + d)), int(round(B - z - d))
                lit = u - v * 0.6 - zf * 0.3 < 0.35      # away from the light: the right side, the back
                c = 'K' if int(z - wall) % 6 == 0 and z - wall >= 1 else (shade if not lit else 'R')
                self.put(sx, sy, c, B - int(round(d)))

    def door(self, x0):
        """The door, every house's alike, at x0 on the ground line: planks in
        the brick's shade, black round them and between, a knob, in a cream
        casing two deep -- a tile wide, as tall as a window's top."""
        B = self.B
        top = B - DOOR_H - 2
        for y in range(top, B):
            for x in range(x0, x0 + 16):
                edge = x in (x0, x0 + 15) or y == top
                self.put(x, y, 'K' if edge else 'M', B)
        dx = x0 + 2
        for y in range(B - DOOR_H, B):
            for x in range(dx, dx + DOOR_W):
                edge = x in (dx, dx + DOOR_W - 1) or y == B - DOOR_H
                self.put(x, y, 'K' if edge or (x - dx) % 3 == 0 else 'S', B)
        self.put(dx + DOOR_W - 3, B - DOOR_H // 2, 'M', B)
        return dx, DOOR_W

    def window(self, x0, cy, tiles=1, shutters=False):
        """A window, tiles wide, at x0 in tile row cy (half rows allowed: 5.5
        is 8 pixels into row 5): a black frame and bars, cream panes, a cream
        sill; black shutters with cream slats either side if asked."""
        B, y0 = self.B, int(cy * 16)
        x1 = x0 + 16 * tiles - 1
        gx0, gx1 = (x0 + 4, x1 - 4) if shutters else (x0 + 1, x1 - 1)
        my = y0 + 6
        for y in range(y0, y0 + 16):
            for x in range(x0, x1 + 1):
                ly = y - y0
                if ly == 14:
                    c = 'M'                                  # the sill
                elif ly in (0, 13, 15):
                    c = 'K'
                elif gx0 <= x <= gx1:
                    bar = x in (gx0, gx1) or y == my or ((x - gx0) % 8 in (0, 7) and gx0 < x < gx1
                                                         and (x - gx0) // 8 < (gx1 - gx0) // 8)
                    c = 'K' if bar else 'M'
                elif shutters and x not in (x0, x1) and x not in (gx0 - 1, gx1 + 1) and ly % 3 == 1:
                    c = 'M'                                  # a shutter's slat
                else:
                    c = 'K'
                self.put(x, y, c, B)

    def chimney(self, x0, w, d, z_top, depth=4, tones=None):
        """A brick chimney, a box in the oblique view like the house: its
        front face d back, brick; its right side running back `depth` in the
        side face's tone; its top, a rim round a black flue. It stands from
        the ground up, so whatever of the house is nearer -- the roof in front
        of its foot, the wall -- hides the rest (the depth test). tones: the
        letters it takes for the wall's, where the house is not brick."""
        B = self.B
        put = self.put if not tones else lambda x, y, c, f: self.put(x, y, tones.get(c, c), f)
        for z in range(z_top + 1):                           # the front
            for x in range(x0, x0 + w):
                ry = z_top - z
                c = 'K' if x == x0 or ry == 0 else brick_tone(x - x0, ry)
                put(x + d, B - z - d, c, B - d)
        for k in range(1, depth + 1):                        # the side, column by column back
            for z in range(z_top + 1):
                c = 'K' if k == depth or z == z_top else 'B'
                put(x0 + w - 1 + k + d, B - z - d - k, c, B - d - k)
        for k in range(1, depth + 1):                        # the top
            for x in range(x0, x0 + w):
                rim = k in (1, depth) or x in (x0, x0 + w - 1)
                put(x + k + d, B - z_top - d - k, 'M' if rim and k != depth and x != x0 else 'K', B - d - k)

    def awning(self, x0, x1, z, d0, stripe='S', out=5):
        """A striped awning sloping out and down from the wall, its lower
        edge scalloped -- striped in the brick's own shade and the trim, so it
        lies on the brick in the brick's four tones."""
        B = self.B
        for k in range(out + 1):                             # k toward the viewer
            d = d0 - k
            y = B - (z - k) - d
            for dy in (0, 1):
                for x in range(x0 - k, x1 - k + 1):
                    lx = x + k - x0
                    edge = x in (x0 - k, x1 - k) or k == out
                    c = 'K' if edge else (stripe if (lx // 4) % 2 == 0 else 'M')
                    if k == out and dy == 1 and lx % 4 in (0, 3):
                        c = None
                    self.put(x, y + dy, c, B - d)

    def sign(self, x0, z0, text, d0=0, ink='M'):
        """A black board with the words in trim (or the tone `ink`), three by
        five letters."""
        B = self.B
        w, h = 4 * len(text) + 3, 9
        y0 = B - d0 - z0 - h
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.put(x + d0, y, 'K', B - d0)
        for i, ch in enumerate(text):
            for gy, row in enumerate(FONT[ch]):
                for gx, v in enumerate(row):
                    if v == '#':
                        self.put(x0 + 2 + i * 4 + gx + d0, y0 + 2 + gy, ink, B - d0)

    def belfry(self, x0, w, z_top, spire, d=2, depth=12, clock=False):
        """A square tower through the roof, its front just behind the wall's:
        the wall's own boards, its side a step darker, louvres near its top
        (or a clock), and on it a four-sided spire `spire` high in the roof's
        tone, its side turned away black."""
        B = self.B
        for z in range(z_top + 1):
            for x in range(x0, x0 + w):
                lx, lz = x - x0, z_top - z
                c = 'K' if lx in (0, w - 1) or lz == 0 else self.tone(lx, lz)
                if clock:
                    r2 = (2 * lx - w + 1) ** 2 + (2 * lz - 25) ** 2      # a face 13 across, its centre 12 down
                    if r2 <= 13 * 13:
                        hand = (lx == w // 2 and 7 <= lz <= 12) or (lz == 12 and w // 2 <= lx <= w // 2 + 3)
                        c = 'K' if r2 > 10 * 10 or hand else 'B'
                elif 4 <= lx <= w - 5 and 6 <= lz <= 19:
                    c = 'K' if lx in (4, w - 5) or lz in (6, 19) or lz % 3 == 0 else 'S'
                self.put(x + d, B - z - d, c, B - d)
        for k in range(1, depth + 1):
            for z in range(z_top + 1):
                self.put(x0 + w - 1 + k + d, B - z - d - k, 'K' if k == depth or z == z_top else 'S', B - d - k)
        yb = B - z_top - d - 1
        p0, p1, p2 = (x0 + d - 1, yb), (x0 + w + d, yb), (x0 + w + d + depth, yb - depth)
        apex = (x0 + d + w // 2 + depth // 2, yb - depth // 2 - spire)
        triangle(lambda x, y, c: self.put(x, y, c, B - d - depth), p1, p2, apex, 'K')
        triangle(lambda x, y, c: self.put(x, y, c, B - d), p0, p1, apex, 'R')

    def grid(self, name, merge=()):
        """The house as a drawing with its layers (entrance_shapes.Grid):
        the pixels, a black line round the whole, each pixel's ground row
        and the ground stood on."""
        g = Grid(self.w, self.h)
        for (x, y), c in self.c.items():
            g.put(x, y, c)
        # a black line round the whole house, inside its edge, as the first
        # house has: whatever part ends there, the silhouette is one clean line
        ink = lambda x, y: g.get(x, y) != '.'
        for (x, y) in [p for p in self.c if any(not ink(p[0] + dx, p[1] + dy)
                                                  for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]:
            g.put(x, y, 'K')
        if merge:
            four_per_cell(g, merge, by_count=False)
        f = dict(self.f)
        stand(g, lambda x, y: f.get((x, y), y), self.foot)
        check(g, name)
        return g

    def door_cells(self, door):
        """(cell across, cell down, cells wide) of a door's foot, from what door() gave."""
        dx, dw = door
        return [dx // 16, self.h // 16 - 1, max(1, (dx + dw - 1) // 16 - dx // 16 + 1)]

    def finish(self, name, pal, door, merge=()):
        """The design for draw_views: the house, its layers, and its door --
        (cell across, cell down, cells wide) of the door's foot."""
        g = self.grid(name, merge)
        return {'pal': pal, 'view_w': self.w, 'order': ['house'], 'views': {'house': g.rows()},
                'depth': depth_layers(self.w, self.h, [(0, 0, g)]),
                'door': self.door_cells(door)}
