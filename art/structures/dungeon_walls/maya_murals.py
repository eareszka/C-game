"""The Mayan/Aztec pyramid's carved walls: every chamber's back wall is one
mural that fills it (BW x 3 tiles = 112 x 48), and every corridor face is a
stack of day-sign glyph blocks. Carved in the step pyramid's grey stone:
K line, D carved shadow, S the stone, M the lit relief.

    python art/structures/dungeon_walls/maya_murals.py <design.json>
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/pyramid_maya_murals

Every wall shares one carving, pattern(X, z): a step fret at the foot and
day-sign blocks above it on one grid, laid by screen column X and height z
above that wall's own floor line, so it runs on unbroken from side wall to
back wall to corridor to staircase (the user asked for it seamless). Over it,
crowded figures -- the Mesoamerican imagery (looked up: the Aztec Sun Stone's
face, four suns, day-sign ring and rays; Bonampak / Yaxchilan warriors with
plumed headdresses, spears and round shields) mixed with the game's own
cryptids, carved from their battle sprites' side views (art/enemies/NN_views.png).
  sun_stone   a sun-stone calendar between the Grootslang and the Myrmecoleon
  warriors    two warriors facing the Beast of the Charred Forests
  serpent     the Vatnaormur coiling the length of the wall, a warrior, the death worm
  glyph_wall  the Lusca, the boulder and others among the blocks round a sun stone
Side walls are plain (drawn darker), staircase walls upright masonry with the
small carved cryptids (maya_cryptids_small.png) set in where they fit whole.
"""
import json, math, os, sys
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from dungeon_walls import Grid, h32 as _h, sheet_rows
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')

PAL = {'K': '000000', 'D': '595965', 'M': 'c6ccda', 'S': '9797aa'}
W, H = 112, 48

def relief(g, pts, fill='M'):
    """Raised stone, lit from the upper left: the shape in the lit tone, its
    shadow falling one pixel down and right onto the stone."""
    pts = set(pts)
    for x, y in pts:
        for sx, sy in ((1, 0), (0, 1), (1, 1)):
            q = (x + sx, y + sy)
            if q not in pts and 0 <= q[0] < g.w and 0 <= q[1] < g.h and g.g[q[1]][q[0]] == 'S':
                g.put(*q, 'D')
    for x, y in pts:
        g.put(x, y, fill)


def disc(cx, cy, r0, r1):
    return {(x, y) for y in range(cy - r1 - 1, cy + r1 + 2) for x in range(cx - r1 - 1, cx + r1 + 2)
            if r0 * r0 <= (x - cx + .5) ** 2 + (y - cy + .5) ** 2 < r1 * r1}


def base(w=W, h=H, mask=None):
    g = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            if mask is None or (x, y) in mask:
                g.put(x, y, 'S')
    return g


WARRIOR = [  # 24 x 37, facing right: plumes swept back from the headband, a
             # profile face with its ear spool, jaguar tunic, belt and loincloth
    "M.......................",
    ".M..M...................",
    "..M..M..M...............",
    "...M..M..M..............",
    "....MM.MM.M.............",
    ".....MMMMMMM............",
    "......MMMMMMM...........",
    "......MDDDDDM...........",
    ".......MMMMMMM..........",
    ".......MMMMKMMM.........",
    ".......MMMMMMMMM........",
    "......DMMMMMMMM.........",
    ".......MMMMMMM..........",
    "........MMMMM...........",
    ".........MMM............",
    "......MMMMMMMMMMMM......",
    ".....MMDMMDMMMM.MMM.....",
    "....MMMMMMMMMMM..MM.....",
    "....MMDMMDMMDMM...MM....",
    "....MMMMMMMMMMM...MMM...",
    "....MMDMMDMMDMM.........",
    "....MMMMMMMMMMM.........",
    "....MMDMMDMMDMM.........",
    "....MDDDDDDDDDM.........",
    ".....MMMMMMMMM..........",
    "......MMDDDMM...........",
    "......MMM.MMM...........",
    ".....MMM...MMM..........",
    ".....MMM...MMM..........",
    ".....MMM...MMM..........",
    ".....MMM...MMM..........",
    ".....MMM...MMM..........",
    ".....MMM...MMM..........",
    ".....MMM...MMM..........",
    ".....MMM...MMM..........",
    "....MMMM...MMMM.........",
    "...MMMMM...MMMMM........",
]
SHIELD = ["..MMM..", ".MDDDM.", "MDMMMDM", "MDMKMDM", "MDMMMDM", ".MDDDM.", "..MMM.."]


def figure(g, x0, y0, rows, flip=False):
    pts = {}
    w = len(rows[0])
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != '.':
                pts[(x0 + ((w - 1 - x) if flip else x), y0 + y)] = c
    relief(g, [p for p, c in pts.items() if c == 'M'])
    for p, c in pts.items():
        if c != 'M':
            g.put(*p, c)


FRET = ["DD......DD......",
        "DDDD....DDDD....",
        "DDDDDD..DDDDDD..",
        "DDDDDDDDDDDDDDDD",
        "..DDDDDD..DDDDDD",
        "....DDDD....DDDD",
        "......DD......DD"]



class Canvas(Grid):
    """A Grid that counts what is drawn off its edge (or onto its top and foot
    rows, which are the cap's shadow and the floor line): a figure cut off."""
    def __init__(self, w, h):
        super().__init__(w, h)
        self.lost = 0

    def put(self, x, y, c):
        if 0 <= x < self.w and 1 <= y < self.h - 1:
            self.g[y][x] = c
        else:
            self.lost += 1


class Mural:
    """A wall being carved, and what of it is already taken, so the next thing
    goes where there is still bare stone."""
    def __init__(self, w=W, h=H, mask=None):
        self.w, self.h, self.mask = w, h, mask
        self.g = base(w, h, mask)
        self.taken = set()

    def free(self, x0, y0, w, h, pad=1):
        if not (0 <= x0 and 1 <= y0 and x0 + w <= self.w and y0 + h <= self.h - 1):
            return False
        if self.mask is not None and not all((x, y) in self.mask for y in range(y0, y0 + h)
                                             for x in range(x0, x0 + w)):
            return False
        return not any((x, y) in self.taken for y in range(y0 - pad, y0 + h + pad)
                       for x in range(x0 - pad, x0 + w + pad))

    def take(self, x0, y0, w, h):
        self.taken |= {(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)}


def sun_disc(m, cx, cy, r):
    """The Sun Stone, radius r: Tonatiuh's face and flint-knife tongue, the
    four suns, the ring of twenty day signs, its pointed rays."""
    g = m.g
    rays = set()
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        for t in range(0, max(3, r // 3)):
            w = max(0, 2 - t // 2)
            for s_ in range(-w, w + 1):
                rays.add((int(cx + math.cos(a) * (r * .72 + t) - math.sin(a) * s_ * .5),
                          int(cy + math.sin(a) * (r * .72 + t) + math.cos(a) * s_ * .5)))
    relief(g, rays)
    relief(g, disc(cx, cy, int(r * .68), int(r * .78)))
    relief(g, disc(cx, cy, int(r * .45), int(r * .68)))
    for k in range(20):
        a = k * math.pi / 10
        g.put(int(cx + math.cos(a) * r * .57), int(cy + math.sin(a) * r * .57), 'D')
    if r >= 14:
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            sx, sy = cx + int(dx * r * .4) - 1, cy + int(dy * r * .36) - 1
            for y in range(3):
                for x in range(3):
                    g.put(sx + x, sy + y, 'D' if (x, y) != (1, 1) else 'M')
    face = int(r * .36)
    relief(g, disc(cx, cy, 0, face))
    g.put(cx - face // 2, cy - face // 3, 'K'); g.put(cx + face // 2 - 1, cy - face // 3, 'K')
    for x in range(-face // 2, face // 2):
        g.put(cx + x, cy + face // 3, 'D')
    for y in range(face // 3 + 1, face // 3 + 3):
        g.put(cx, y + cy, 'K')                     # the flint-knife tongue
    m.take(cx - r, cy - r, 2 * r, 2 * r)


def warrior(m, x0, y0, flip=False):
    g = m.g
    figure(g, x0, y0, WARRIOR, flip)
    sx = x0 + (20 if not flip else 3)
    for y in range(y0 - 6, min(m.h - 1, y0 + 35)):
        g.put(sx, y, 'D')                          # the spear
    for y, half in ((y0 - 9, 0), (y0 - 8, 1), (y0 - 7, 1)):
        for t in range(-half, half + 1):
            g.put(sx + t, y, 'K')                  # its flint point
    figure(g, x0 + (0 if not flip else 17), y0 + 17, SHIELD)
    m.take(x0, y0 - 9, 24, 46)


# The cryptids as the carvers cut them: drawn by hand, through the pixel
# plugin, in maya_cryptids_design.py -> maya_cryptids.png (32 x 20 each)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from maya_cryptids_design import CRYPTIDS
CRYPTID_ORDER = list(CRYPTIDS)
HERE = os.path.dirname(os.path.abspath(__file__))


def carving(name, flip=False):
    """A cryptid's carving as tone rows, read back from the plugin's export."""
    return sheet_rows(os.path.join(HERE, 'maya_cryptids.png'), PAL, 32, 20, CRYPTID_ORDER.index(name), flip)


SMALL_W, SMALL_H = 18, 14


def small_carving(i, flip=False):
    """The small carving of cryptid i (maya_cryptids_small.png, outlined by the
    plugin), for the staircase walls."""
    return sheet_rows(os.path.join(HERE, 'maya_cryptids_small.png'), PAL, SMALL_W, SMALL_H, i % len(CRYPTID_ORDER), flip)


def cryptid(m, name, x0, y0, flip=False):
    for y, row in enumerate(carving(name, flip)):
        for x, c in enumerate(row):
            if c != '.' and 0 <= x0 + x < m.w and 1 <= y0 + y < m.h - 1:
                m.g.put(x0 + x, y0 + y, c)
    m.take(x0, y0, 32, 20)


PERIOD = 96          # the pattern repeats every 96 columns: a wall's tiles come in 6 column variants
ROWS = 4             # and every 4 stone rows (32 px) up: a side wall stands 96 px above the
                     # corridor beside it and a flight rises 256, so the upright masonry meets
                     # both seamlessly


def _stone(X, z):
    """Which stone of the masonry (X, z) lies in: the nearest of the seeds
    jittered one to each 12 x 8 cell, the distance warped a little so the
    joints curve -- interlocking stones of many sizes."""
    X %= PERIOD
    ci, cj = X // 12, (z - 8) // 8
    best = None
    for i in (ci - 1, ci, ci + 1):
        for j in (cj - 1, cj, cj + 1):
            h = _h(i % (PERIOD // 12), j % ROWS)
            sx = i * 12 + 6 + (h % 9) - 4
            sz = 8 + j * 8 + 4 + ((h >> 8) % 5) - 2
            dx = X - sx
            if dx > PERIOD // 2: dx -= PERIOD
            if dx < -PERIOD // 2: dx += PERIOD
            d = dx * dx * (0.8 + (h >> 16) % 5 * 0.1) + (z - sz) ** 2 * 1.3
            if best is None or d < best[0]:
                best = (d, (i % (PERIOD // 12), j % ROWS))
    return best[1]


def _big(X, z):
    """A large stone carrying a carved cryptid, one in every 96 columns of each
    36-high band of wall, in a half the hash picks: (rows, local x, local y,
    the stone's first column) if (X, z) is on one."""
    Xp = X % PERIOD
    si, sj = Xp // 48, (z - 8) // 36
    h = _h(si, sj, 7)
    if si != _h(sj, 11) % 2:
        return None
    cx = si * 48 + 24 + (h >> 4) % 9 - 4
    cz = 8 + sj * 36 + 18
    lx, lz = Xp - (cx - 17), (cz + 11) - z
    if not (0 <= lx < 34 and 0 <= lz < 22):
        return None
    if (lx in (0, 33) and lz in (0, 21)) or (lx in (0, 1, 32, 33) and lz in (0, 1, 20, 21) and (lx in (0, 33) or lz in (0, 21))):
        return None                                # its rounded corners
    # which cryptid: by the stretch of wall it is in, not repeating with the
    # stones (in the game these are overlays, so they need not tile)
    k = _h(X // PERIOD, sj, 5)
    name = CRYPTID_ORDER[k % len(CRYPTID_ORDER)]
    return carving(name, flip=bool((k >> 8) & 1)), lx, lz, X - lx


def pattern(X, z, carved=True, fits=None, h=None):
    """The one carving every Mayan wall shares, as a function of the wall's
    screen column X and its height z above its own floor line, so it runs on
    unbroken round every corner and up every flight. Rows are upright (z a
    screen row's height above a fixed floor), but the trim follows the wall's
    own floor line, h above it (h = z on a face; along the slant on a side or
    staircase wall), as a skirting does:
        h 0        the foot, against the floor
        h 1..7     the step fret
        z 8..      interlocking organic stones, every so often a large one
                   with a cryptid carved in it (carved=False: not on a
                   chamber's walls, which carry their scenes; fits(x0, x1):
                   whether a stone spanning those columns is whole on this
                   wall -- one that would be cut off is not carved)
    """
    h = z if h is None else h
    if h <= 0:
        return 'K'
    if h < 8:
        return 'D' if FRET[7 - h][X % 16] == 'D' else 'S'
    big = _big(X, z) if carved else None
    if big is not None and fits is not None and not fits(big[3], big[3] + 33):
        big = None                                 # it would run off this wall: plain masonry
    if big is not None:
        rows, lx, lz, _ = big
        if lx in (0, 33) or lz in (0, 21):
            return 'D'                             # its joint
        if lx == 1 or lz == 20:
            return 'M'                             # its lit edge
        c = rows[lz - 1][lx - 1] if 0 <= lz - 1 < 20 and 0 <= lx - 1 < 32 else '.'
        return 'S' if c == '.' else c
    here = _stone(X, z)
    if _stone(X + 1, z) != here or _stone(X, z - 1) != here:
        return 'D'                                 # a joint between stones
    if _stone(X - 1, z) != here or _stone(X, z + 1) != here:
        return 'M'                                 # the stone's lit edge, top and left
    return 'S'


VOLUTE = [".DDD.",            # a Maya scroll, curling out of a figure into the wall
          "D...D",
          "D.D.D",
          "D.DD.",
          ".D..."]


def plate(rows, seed=0):
    """Carve a figure into the wall rather than lay it on: round it a border of
    plain stone that follows its outline at a wavering distance, its edge cut
    as a carved line where the glyph blocks break off against it, scroll curls
    along that edge reaching out into the rows, and the figure's shadow on the
    stone -- one carving, not a picture pasted on (the user's call)."""
    import random
    rng = random.Random(seed)
    h, w = len(rows), len(rows[0])
    ink = {(x, y) for y in range(h) for x in range(w) if rows[y][x] != '.'}
    dist = {p: 0 for p in ink}                     # distance out from the figure
    frontier = list(ink)
    for d in range(1, 7):
        nxt = []
        for x, y in frontier:
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= q[0] < w and 0 <= q[1] < h and q not in dist:
                    dist[q] = d; nxt.append(q)
        frontier = nxt
    reach = lambda x, y: 3 + 1.5 * (math.sin(x * .45 + seed) + math.sin(y * .6 + x * .2 + seed * 2)) / 2
    halo = {p for p, d in dist.items() if 0 < d <= reach(*p)}
    out = [list(row) for row in rows]
    for x, y in halo:
        out[y][x] = 'S'
    edge = [p for p in halo if any(q not in halo and q not in ink and 0 <= q[0] < w and 0 <= q[1] < h
                                   for q in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)))]
    for x, y in edge:
        out[y][x] = 'D'                            # the blocks' broken edge, carved
    for x, y in ink:                               # the figure's shadow on the stone
        for q in ((x + 1, y), (x, y + 1), (x + 1, y + 1)):
            if q in halo and out[q[1]][q[0]] == 'S':
                out[q[1]][q[0]] = 'D'
    edge.sort(key=lambda p: (p[1], p[0]))
    placed = []
    for x, y in rng.sample(edge, len(edge)):       # scroll curls along the edge, spaced out
        if any(abs(x - a) < 9 and abs(y - b) < 9 for a, b in placed):
            continue
        fx, fy = (1 if dist.get((x - 1, y), 9) < dist.get((x + 1, y), 9) else -1), \
                 (1 if dist.get((x, y - 1), 9) < dist.get((x, y + 1), 9) else -1)
        cells = [(x + (i if fx > 0 else -i), y + (j if fy > 0 else -j)) for j in range(5) for i in range(5)]
        if not all(0 <= c[0] < w and 0 <= c[1] < h and c not in ink for c in cells):
            continue
        for (cx, cy), (i, j) in zip(cells, [(i, j) for j in range(5) for i in range(5)]):
            out[cy][cx] = 'D' if VOLUTE[j][i] == 'D' else 'S'
        placed.append((x, y))
    return [''.join(row) for row in out]


def whole(m, name):
    assert m.g.lost == 0, '%s: %d pixels of its figures cut off' % (name, m.g.lost)
    return m


def overlay():
    """A wall of figures with nothing behind them: the carving under them is
    the shared pattern."""
    return Mural(W, H, mask=set())


# The figures each back wall carries, over the shared pattern
def sun_stone():
    m = overlay()
    sun_disc(m, 56, 22, 20)
    cryptid(m, 'grootslang', 1, 14)
    cryptid(m, 'myrmecoleon', 79, 14, flip=True)
    return plate(whole(m, 'sun_stone').g.rows(), 1)


def warriors():
    m = overlay()
    warrior(m, 2, 10)
    warrior(m, 86, 10, flip=True)
    cryptid(m, 'charred_beast', 40, 18)
    sun_disc(m, 56, 9, 8)
    return plate(whole(m, 'warriors').g.rows(), 2)


def serpent():
    m = overlay()
    cryptid(m, 'vatnaormur', 4, 8)
    warrior(m, 44, 10, flip=True)
    cryptid(m, 'olgoi', 74, 10)
    return plate(whole(m, 'serpent').g.rows(), 3)


def glyph_wall():
    m = overlay()
    cryptid(m, 'lusca', 2, 4)
    cryptid(m, 'grootslang', 78, 2, flip=True)
    sun_disc(m, 56, 24, 12)
    cryptid(m, 'olgoi', 4, 26, flip=True)
    cryptid(m, 'charred_beast', 76, 26, flip=True)
    return plate(whole(m, 'glyph_wall').g.rows(), 4)


def gate():
    """A chamber with a doorway in its back wall: the doorway (32 wide, in the
    middle) would cover a scene's centre, so two warriors stand either side of
    it and a small sun stone is set above it -- nothing behind the door."""
    m = overlay()
    warrior(m, 14, 10)
    warrior(m, 74, 10, flip=True)
    sun_disc(m, 56, 8, 7)
    return plate(whole(m, 'gate').g.rows(), 5)


def design():
    v = {'sun_stone': sun_stone(), 'warriors': warriors(), 'serpent': serpent(), 'glyph_wall': glyph_wall(),
         'gate': gate()}
    for k, rows in v.items():
        assert len(rows) == H and all(len(r) == W for r in rows), k
    return {'pal': PAL, 'view_w': W, 'order': list(v), 'views': v}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
