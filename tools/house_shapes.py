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

Every pixel says the ground row it stands over (Grid.footy) and each wing the
ground it covers (Grid.foot), for the game's per-pixel collision and for
what is drawn over the player.
"""
from entrance_shapes import Grid, stand, depth_layers, check, four_per_cell

BRICK_W, COURSE_H = 6, 4    # the catacombs' bond: a brick six across, a course four high

DOOR_W, DOOR_H = 12, 22    # every house's door

# 3x5 capitals for a sign
FONT = {'B': ['##.', '#.#', '##.', '#.#', '##.'], 'O': ['.#.', '#.#', '#.#', '#.#', '.#.'],
        'K': ['#.#', '#.#', '##.', '#.#', '#.#'], 'S': ['.##', '#..', '.#.', '..#', '##.']}


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


class House:
    """A block cw x ch cells; the ground line its front stands on is the
    bottom row. A point x across, d back and z up lands at (x + d, B - z - d)."""
    def __init__(self, cw, ch):
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
                c = 'K' if x == x0 or y == B - d0 else brick_tone(x - x0, y - yt)
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

    def chimney(self, x0, w, d, z_top, depth=4):
        """A brick chimney, a box in the oblique view like the house: its
        front face d back, brick; its right side running back `depth` in the
        side face's tone; its top, a rim round a black flue. It stands from
        the ground up, so whatever of the house is nearer -- the roof in front
        of its foot, the wall -- hides the rest (the depth test)."""
        B = self.B
        for z in range(z_top + 1):                           # the front
            for x in range(x0, x0 + w):
                ry = z_top - z
                c = 'K' if x == x0 or ry == 0 else brick_tone(x - x0, ry)
                self.put(x + d, B - z - d, c, B - d)
        for k in range(1, depth + 1):                        # the side, column by column back
            for z in range(z_top + 1):
                c = 'K' if k == depth or z == z_top else 'B'
                self.put(x0 + w - 1 + k + d, B - z - d - k, c, B - d - k)
        for k in range(1, depth + 1):                        # the top
            for x in range(x0, x0 + w):
                rim = k in (1, depth) or x in (x0, x0 + w - 1)
                self.put(x + k + d, B - z_top - d - k, 'M' if rim and k != depth and x != x0 else 'K', B - d - k)

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

    def sign(self, x0, z0, text, d0=0):
        """A black board with the words in trim, three by five letters."""
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
                        self.put(x0 + 2 + i * 4 + gx + d0, y0 + 2 + gy, 'M', B - d0)

    def finish(self, name, pal, door, merge=()):
        """The design for draw_views: the house, its layers, and its door --
        (cell across, cell down, cells wide) of the door's foot."""
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
        dx, dw = door
        return {'pal': pal, 'view_w': self.w, 'order': ['house'], 'views': {'house': g.rows()},
                'depth': depth_layers(self.w, self.h, [(0, 0, g)]),
                'door': [dx // 16, self.h // 16 - 1, max(1, (dx + dw - 1) // 16 - dx // 16 + 1)]}
