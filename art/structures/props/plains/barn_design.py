"""The farmsteads' barns: eight designs, one of which stands in four farmsteads in five.

    python art/structures/props/plains/barn_design.py            # writes barns.png (+ barns_<n>.png)

The user, 2026-11-16: "80% of farmsteads have a barn. we will have 8 different
barn exterior designs ... spread out so it doesnt appear that the same barn is
shown a lot, the design should follow the oblique projection and bible rules
of overworld buildings". The eight were approved the same day:

  a  classic: red boards, white trim, a gambrel in wood (the village barn, smaller)
  b  white boards, red trim, a slate gambrel
  c  weathered bare wood, upright boards, a plain gable, no trim
  d  green boards, white trim, a slate gable, a tall white silo with a slate cap beside it
  e  long and low, red upright boards, a gable, a lean-to shed on its east side
  f  yellow boards, white trim, a thatched gable
  g  tall red gambrel, a cupola on the ridge and a hay hood over the loft door
  h  a bank barn: a lower storey of stone, wood above, a slate gable

Every one is tools/house_shapes.House: the gable end square on to the front,
the roof running back up and to the right at 45 degrees ((x + d, B - z - d)),
its east side a step darker than the front, black round the whole, walls
laid in units (clapboard's 4 px courses, upright boards 6 across, stone's
blocks) and every colour a material's (tools/overworld_style.py MATERIALS).
The strip barns.png holds them side by side at 96 px apart, each standing on
the strip's bottom row; props.py reads each one's cells from its offset.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from house_shapes import House, clapboard_tone, triangle
from overworld_style import MATERIALS

T = lambda m, i=0: MATERIALS[m]['tones'][i]

SLOT_W, STRIP_H = 96, 96       # each barn's slot in the strip; all stand on its bottom row


def boards_tone(rx, ry):
    """Upright boards six across: the board its base tone, the joint at its right in the shade."""
    return 'S' if rx % 6 == 5 else 'B'


def stone_tone(rx, ry):
    """Stone blocks six along in courses four high, half a block along from the course
    above: the top row lit, the rest the base, the joints dark (OVERWORLD_STYLE stone)."""
    r = ry % 4
    lx = (rx + (ry // 4) % 2 * 3) % 6
    if r == 3 or lx == 0:
        return 'd'
    return 'l' if r == 0 else 'm'


def gambrel(h1, h2):
    """A gambrel's height over the wall at t (0 the ridge, 1 the eave): steep
    below the break half way out, flatter above."""
    return lambda t: h1 + h2 * (1 - t / 0.5) if t <= 0.5 else h1 * (1 - (t - 0.5) / 0.5)


def gable(rise):
    return lambda t: rise * (1 - t)


class Barn(House):
    """A House that may lay a part in other letters (remap) -- a silo's white
    beside the barn's green, a lower storey's stone."""
    remap = None

    def put(self, x, y, c, f):
        if self.remap and c:
            c = self.remap.get(c, c)
        House.put(self, x, y, c, f)

    def body(self, x0, x1, depth, wall, top, breaks=(), trim=True, side=None, end='plain'):
        """The barn: its gable end to the front, the roof running back `depth`.
        top(t): the roof's height above the wall, t 0 at the ridge and 1 at the
        eaves; breaks: the t of each fold in it, a black line along each, as
        along the ridge, the eaves and every six back. trim: two pixels of it
        (M) up the raking edges and down the corners. side(z): the east side's
        letter at height z (default the shade). end: 'plain' the gable in the
        base tone, 'tone' the wall's own units carried up into it."""
        B = self.B
        side = side or (lambda z: 'S')
        xm, half = (x0 + x1) / 2.0, (x1 - x0) / 2.0
        hz = lambda x: top(min(1.0, abs(x - xm) / half))
        yt = B - wall + 1
        self.yt, self.xm, self.ridge = yt, xm, wall + top(0)
        for y in range(yt, B + 1):                           # the wall
            for x in range(x0, x1 + 1):
                c = 'K' if x in (x0, x1) or y == B else self.tone(x - x0, y - yt)
                if trim and (x0 < x <= x0 + 2 or x1 - 2 <= x < x1):
                    c = 'M'
                self.put(x, y, c, B)
        for x in range(x0, x1 + 1):                          # the end above it
            zt = wall + hz(x)
            for z in range(wall, int(zt) + 1):
                c = self.tone(x - x0, B - z - yt) if end == 'tone' else 'B'
                if trim and zt - z < 2.5:
                    c = 'M'
                if z == int(zt) or x in (x0, x1):
                    c = 'K'
                self.put(x, B - z, c, B)
        for d in range(1, depth + 1):                        # the roof, back from the front edge
            for i in range(2 * (x1 - x0) + 1):
                x = x0 + i * 0.5
                z = wall + hz(x)
                t = abs(x - xm) / half
                sx, sy = int(round(x + d)), int(round(B - z - d))
                line = (x <= x0 or x >= x1 or abs(x - xm) < 1 or d == depth or d % 6 == 0
                        or any(abs(t - b) * half < 1 for b in breaks))
                c = 'K' if line else 'R'
                self.put(sx, sy, c, B - d)
                self.put(sx, sy + 1, c, B - d)
            for x in (x0, x1):
                self.put(x + d, B - wall - d + 1, 'K', B - d)
            for z in range(wall):                            # the side, up to the eave
                self.put(x1 + d, B - z - d, 'K' if z == 0 or d == depth else side(z), B - d)
        self.stood({(x + d, B - d) for x in range(x0, x1 + 1) for d in range(depth + 1)})

    def fill_holes(self):
        """Pixels the parts left empty inside the silhouette (where a raking edge meets the
        roof's half steps) are filled black, as the line between them."""
        ink = set(self.c)
        out, stack = set(), [(-1, -1)]
        while stack:
            x, y = stack.pop()
            if (x, y) in out or (x, y) in ink or not (-1 <= x <= self.w and -1 <= y <= self.h):
                continue
            out.add((x, y))
            stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        for y in range(self.h):
            for x in range(self.w):
                if (x, y) not in ink and (x, y) not in out:
                    self.c[(x, y)], self.f[(x, y)] = 'K', self.B

    def frame(self, x0, y0, w, h, inner='K'):
        """An opening w x h at x0, y0: black round it, filled with `inner`."""
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                edge = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
                self.put(x, y, 'K' if edge else inner, self.B)

    def loft_window(self, cx, y0, w=14, h=12):
        """A four-pane hayloft window in the trim: black frame and cross, panes of the trim."""
        x0 = int(round(cx - w / 2.0))
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                lx, ly = x - x0, y - y0
                bar = lx in (0, w - 1, w // 2) or ly in (0, h - 1, h // 2)
                self.put(x, y, 'K' if bar else 'M', self.B)

    def door_at(self, x0, w, h, frame='M', plank='S'):
        """Barn doors: planks with black between, a frame and an X brace in `frame`."""
        B = self.B
        for y in range(B - h, B):
            for x in range(x0, x0 + w):
                lx, ly = x - x0, y - (B - h)
                edge = lx in (0, w - 1) or ly in (0, h - 1)
                cross = abs(lx * (h - 1) - ly * (w - 1)) < w - 1 or abs((w - 1 - lx) * (h - 1) - ly * (w - 1)) < w - 1
                self.put(x, y, frame if edge or cross else 'K' if lx % 4 == 0 else plank, B)

    def silo(self, cx, A, wall, cap):
        """A round silo, round as the landmark well is (landmarks/well_design.py: "well
        should be round shape and still oblique projection"): its top a level ellipse
        A wide each way of cx and half that deep, its wall the front of the drum under it,
        standing on the ground line. White paint (W), a hoop of its shade (w) every eight
        down, its lit left edge white and the right third in flat shade; on it a slate
        cone (Z) `cap` high over the top ellipse."""
        import math
        B, Bb = self.B, A / 2.0
        cy = B - Bb - wall                                   # the top ellipse's centre
        front = lambda x: cy + Bb * math.sqrt(max(0.0, 1.0 - ((x - cx) / A) ** 2))
        for X in range(int(cx - A) - 1, int(cx + A) + 2):
            if abs(X + 0.5 - cx) > A:
                continue
            u = (X + 0.5 - cx) / A
            f0 = front(X + 0.5)
            for Y in range(int(cy - Bb) - cap - 1, B + 1):
                ground = int(f0 + wall)
                if Y > f0 and Y <= f0 + wall:                # the drum
                    zz = int(Y - f0 - 0.5)
                    c = 'w' if u > 0.35 or zz % 8 == 7 else 'W'
                    self.put(X, Y, c, ground)
                elif Y <= f0 + 0.5:                          # the cone over the top ellipse
                    apex = cy - cap
                    # the cone's outline: straight from the apex to the ellipse's ends
                    half = A * (Y - apex) / (cy - apex) if Y < cy else A
                    if Y >= apex and abs(X + 0.5 - cx) <= half:
                        self.put(X, Y, 'Z', ground)
        self.stood({(x, y) for x in range(int(cx - A), int(cx + A) + 1) for y in range(int(B - 2 * Bb), B + 1)
                    if ((x - cx) / A) ** 2 + ((y - (B - Bb)) / Bb) ** 2 <= 1})

    def lean_to(self, x0, x1, depth, hi, lo):
        """A shed against the barn's east side: its front square on x0..x1, its
        roof falling from hi at the barn to lo at its east wall and running back
        `depth`; the east wall in the shade."""
        B = self.B
        zt = lambda x: hi + (lo - hi) * (x - x0) / float(x1 - x0)
        for x in range(x0, x1 + 1):                          # the front
            top = int(zt(x))
            for z in range(top + 1):
                c = 'K' if x == x1 or z == 0 or z == top else self.tone(x - x0, top - z)
                self.put(x, B - z, c, B)
        for d in range(1, depth + 1):                        # the roof
            for x in range(x0, x1 + 1):
                c = 'K' if x == x1 or d == depth or d % 6 == 0 else 'R'
                y = int(round(B - zt(x) - d))
                self.put(x + d, y, c, B - d)
                self.put(x + d, y + 1, c, B - d)
            for z in range(lo + 1):                          # its east wall
                self.put(x1 + d, B - z - d, 'K' if z == 0 or d == depth else 'S', B - d)
        self.stood({(x + d, B - d) for x in range(x0, x1 + 1) for d in range(depth + 1)})


def letters(**tones):
    return dict(K='000000', **tones)


RED_PAL = letters(B=T('red paint'), S=T('red paint', 1), M=T('white paint'), R=T('wood', 1))


def barn_a():
    """Classic: red boards in clapboard courses, white trim, a gambrel in wood."""
    h = Barn(5, 5, clapboard_tone)
    h.body(4, 62, 12, 35, gambrel(14, 8), breaks=(0.5,))
    h.door_at(21, 12, 24); h.door_at(33, 12, 24)
    h.door = 33
    h.loft_window(h.xm, h.yt - 16)
    return h, RED_PAL


def barn_b():
    """White boards, red trim, a slate gambrel; wide and low."""
    h = Barn(5, 5, clapboard_tone)
    h.body(3, 66, 10, 32, gambrel(13, 9), breaks=(0.5,))
    h.door_at(21, 13, 24); h.door_at(34, 13, 24)
    h.door = 34
    h.loft_window(h.xm, h.yt - 15, w=12, h=10)
    return h, letters(B=T('white paint'), S=T('white paint', 1), M=T('red paint'), R=T('slate'))


def barn_c():
    """Weathered bare wood in upright boards, a plain gable in wood, no trim: one sliding
    door off to the side and a small loft hatch."""
    h = Barn(5, 5, boards_tone)
    h.body(5, 58, 14, 34, gable(22), trim=False, side=lambda z: 'D', end='tone')
    h.door_at(10, 20, 26, frame='B', plank='S')
    h.door = 20
    h.frame(int(h.xm) - 5, h.yt - 16, 11, 11, inner='D')
    h.frame(40, h.B - 22, 10, 8, inner='D')
    return h, letters(B=T('wood'), S=T('wood', 1), D=T('wood', 2), R=T('wood', 1))


def barn_d():
    """Green boards, white trim, a slate gable; a tall white silo with a slate cap at its west."""
    h = Barn(6, 6, clapboard_tone)
    h.silo(17.5, 11.5, 58, 12)
    # the barn's west trim (white, as the silo is) stands in the silo's cell, its green from the next
    h.body(29, 80, 10, 34, gable(20))
    h.door_at(43, 12, 24); h.door_at(55, 12, 24)
    h.door = 55
    h.loft_window(h.xm, h.yt - 15, w=12, h=10)
    return h, letters(B=T('barn green'), S=T('barn green', 1), M=T('white paint'), R=T('slate'),
                      W=T('white paint'), w=T('white paint', 1), Z=T('slate'))


def barn_e():
    """Long and low: red upright boards, white trim, a wood gable running far back, a
    lean-to shed against its east side."""
    h = Barn(6, 5, boards_tone)
    h.lean_to(50, 70, 22, 27, 14)
    h.body(4, 50, 30, 31, gable(12))
    h.door_at(15, 18, 20)
    h.door = 24
    h.loft_window(h.xm, h.yt - 11, w=10, h=8)
    h.frame(56, h.B - 14, 9, 7)
    return h, RED_PAL


def barn_f():
    """Yellow boards, white trim, a thatched gable."""
    h = Barn(5, 5, clapboard_tone)
    h.body(4, 60, 14, 34, gable(22))
    h.door_at(20, 9, 24); h.door_at(29, 9, 24)
    h.door = 29
    h.loft_window(h.xm, h.yt - 16)
    return h, letters(B=T('yellow paint'), S=T('yellow paint', 1), M=T('white paint'), R=T('thatch'))


def barn_g():
    """Tall red gambrel: a cupola on the ridge, a hay hood over the loft door."""
    h = Barn(5, 6, clapboard_tone)
    h.body(4, 64, 12, 44, gambrel(16, 9), breaks=(0.5,))
    h.remap = {'B': 'M', 'S': 'K'}                          # the cupola: white, its louvres black
    h.belfry(int(h.xm) - 2, 10, int(h.ridge) + 9, 6, d=3, depth=5)
    h.remap = None
    B, xm, zr = h.B, h.xm, h.ridge
    for k in range(0, 7):                                    # the hood: a little gable standing out over the loft
        for i in range(-16, 17):
            dx = i * 0.5
            z = zr - 2 - abs(dx)
            c = 'K' if k == 6 or abs(dx) > 6.5 or abs(dx) < 0.5 else 'M'
            for dy in (0, 1):
                h.put(int(round(xm + dx - k)), int(round(B - z + k)) + dy, c, B + k)
    h.frame(int(xm) - 6, B - int(zr) + 12, 13, 13, inner='K')
    h.door_at(22, 12, 26); h.door_at(34, 12, 26)
    h.door = 34
    return h, RED_PAL


def barn_h():
    """A bank barn: a lower storey of stone with stable doorways, wood upright boards above
    with two windows, a slate gable."""
    def tone(rx, ry):
        return stone_tone(rx, ry - 26) if ry >= 26 else boards_tone(rx, ry)
    h = Barn(6, 6, tone)
    h.body(4, 76, 14, 58, gable(18), trim=False, side=lambda z: 'd' if z < 32 else 'D', end='tone')
    B = h.B
    for x0 in (12, 34, 56):
        h.frame(x0, B - 22, 12, 22, inner='K')
    h.door = 40                                              # the middle doorway
    h.frame(18, h.yt + 8, 12, 10, inner='S'); h.frame(52, h.yt + 8, 12, 10, inner='S')
    h.frame(int(h.xm) - 6, h.yt - 14, 13, 12, inner='S')
    return h, letters(B=T('wood'), S=T('wood', 1), D=T('wood', 2), R=T('slate'),
                      l=T('stone'), m=T('stone', 1), d=T('stone', 2))


BARNS = [('barn_a', barn_a), ('barn_b', barn_b), ('barn_c', barn_c), ('barn_d', barn_d),
         ('barn_e', barn_e), ('barn_f', barn_f), ('barn_g', barn_g), ('barn_h', barn_h)]


def render(name, make):
    """The barn as rows of letters in its slot (whole cells wide, STRIP_H high, standing on
    the bottom row) and its palette; checked as every building is (House.grid). It is set
    the fewest pixels right in its slot that keep every cell to four colours."""
    h, pal = make()
    h.fill_holes()
    g = h.grid(name)
    rows = g.rows()
    W, H = len(rows[0]), len(rows)
    assert H <= STRIP_H, name
    best = None
    for s in range(16):
        sw = (W + s + 15) // 16 * 16
        out = [['.'] * sw for _ in range(STRIP_H)]
        for y in range(H):
            for x in range(W):
                out[STRIP_H - H + y][x + s] = rows[y][x]
        n = len(cell_colours(out, pal, name))
        if best is None or n < best[0] or (n == best[0] and sw < len(best[1][0])):
            best = (n, out, s)
        if n == 0:
            break
    s = best[2]
    DOOR[name] = h.door + s
    FOOT[name] = {(x + s, STRIP_H - H + y) for x, y in h.foot if (x, y) in h.c}
    return best[1], pal


DOOR = {}    # each barn's door, its middle in pixels across its slot: a farm's lane ends there (props.py)
FOOT = {}    # each barn's ground stood on, in its slot (render): the feet meet it (props.py 'built')


def cell_colours(rows, pal, name):
    """Four colours at most in every 16 px cell (the sheet's rule)."""
    bad = []
    for cy in range(len(rows) // 16):
        for cx in range(len(rows[0]) // 16):
            cs = {pal[rows[y][x]] for y in range(cy * 16, cy * 16 + 16)
                  for x in range(cx * 16, cx * 16 + 16) if rows[y][x] != '.'}
            if len(cs) > 4:
                bad.append((cx, cy, len(cs)))
    return bad


if __name__ == '__main__':
    from PIL import Image
    want = sys.argv[1:]
    drawn = [(name,) + render(name, make) for name, make in BARNS]
    strip = Image.new('RGBA', (sum(len(r[0]) for _, r, _ in drawn), STRIP_H), (0, 0, 0, 0))
    foot = Image.new('RGBA', strip.size, (0, 0, 0, 0))
    ok, x0 = True, 0
    for name, rows, pal in drawn:
        bad = cell_colours(rows, pal, name)
        if bad:
            ok = False
        print(name, 'at x', x0, 'cells', len(rows[0]) // 16, 'x', STRIP_H // 16, 'over 4 colours:', bad or 'none')
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c != '.':
                    strip.putpixel((x0 + x, y), tuple(int(pal[c][k:k + 2], 16) for k in (0, 2, 4)) + (255,))
        for x, y in FOOT[name]:
            foot.putpixel((x0 + x, y), (0, 0, 0, 255))
        x0 += len(rows[0])
    strip.save(os.path.join(HERE, 'barns.png'))
    foot.save(os.path.join(HERE, 'barns_foot.png'))
    with open(os.path.join(HERE, 'barns_doors.txt'), 'w') as f:          # props.py door_px
        for name, rows, pal in drawn:
            f.write('%s %d\n' % (name, DOOR[name]))
    print('barns.png' + ('' if ok else '  (cells over 4 colours above)'))
