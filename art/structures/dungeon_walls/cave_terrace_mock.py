"""Mock only: terraced caves laid from the rock pieces in the sheet (an ore's block; --sheet a copy). Nothing
in the game is changed.

    python art/structures/dungeon_walls/cave_terrace_mock.py out.png [--sheet copy.png] [levels seed ore ...]

The terraces are the giant tree's model (src/dungeon.cpp carve_tree_terraces):
tier 0 is the highest floor, at the back; each tier has a back edge per column,
flat on a 64px grid or a 45-degree ramp across a 64px column; the rock band
behind a floor is Z tall, so its top edge is its foot edge moved up Z and the
two stay parallel; past a tier's ends its edge runs down at 45 degrees until it
meets the band in front. Every edge therefore lies on the 16px grid or on a
cell's diagonal, and the picture is laid a whole cell at a time.

Ways are the tree's too: a floor too shallow to stand on is closed; ladders
(the dungeons' own, sheet row 14) go where both edges are level for a cell; a
spanning tree of them from the lowest mouth reaches every floor, and a floor it
cannot reach is closed and the cave built again. Every level then gets its
mouth on a floor that is left.
"""
import os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cave_rock_design import CELLS, SIZE

C, U, P, TOP, Z = 16, 64, 3, 3, 80      # cell; unit column; tier pitch and top margin in units; a band's height
UNDER = 32                              # how far the rock hangs under the lowest floor's edge
BELOW = 4                               # cells of the dark shown under the lowest floor's front
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
ROCK, FLOOR, DARK = 1, 2, 0
LADDER_COL0, LADDER_ROW = 7, 14         # src/dungeon.cpp: a length, its foot below; a column an ore
ORES = ('stone', 'bronze', 'emerald', 'veyrite', 'dravium', 'kharvite', 'reality shard')


def h32(*k):
    v = 0x9E3779B1
    for n in k:
        v = ((v ^ (int(n) & 0xffffffff)) * 0x85EBCA6B) & 0xffffffff
        v ^= v >> 13
    return v


class Cave:
    def __init__(self, N, seed, units=28):
        self.N, self.W = N, units * U
        rng = self.rng = random.Random(seed)
        self.ends = [(4 + rng.randrange(0, 3), units - 4 - rng.randrange(0, 3)) for _ in range(N)] + [(0, units)]
        self.offs = []
        for t in range(N + 1):
            o, cur = [], rng.randrange(3) - 1
            for i in range(units):
                if rng.random() < 0.35:
                    cur = max(-1, min(1, cur + rng.choice((-1, 1))))
                o.append(cur)
            self.offs.append(o)
        self.pin = np.zeros((N, self.W), bool)             # floors closed: too shallow, or out of reach
        self.rounds = 0
        while True:
            self.build()
            self.rounds += 1
            if not (self.close_shallow() or self.join()):
                break
        self.mouths()

    def back(self, t, x):
        a, b = self.ends[t]
        row = lambda i: TOP + t * P + self.offs[t][i]
        if x < a * U:
            return row(a) * U + (a * U - x)
        if x >= b * U:
            return row(b - 1) * U + (x - b * U + 1)
        i, lx = x // U, x % U
        r0, r1 = (row(i - 1) if i > a else row(i)), row(i)
        return r1 * U if r0 == r1 else r0 * U + (lx + 1 if r1 > r0 else -lx)

    def build(self):
        N, W = self.N, self.W
        b = self.b = np.zeros((N + 1, W), int)
        for x in range(W):
            bf = b[N][x] = self.back(N, x)
            for t in range(N - 1, -1, -1):
                bf = b[t][x] = bf - Z if self.pin[t][x] else min(self.back(t, x), bf - Z)
        self.depth = np.array([b[t + 1] - Z - b[t] for t in range(N)])
        self.floors = []                                   # (tier, x0, x1): a tier's columns that show, together
        self.comp = np.full((N, W), -1)
        for t in range(N):
            x = 0
            while x < W:
                if self.depth[t][x] < 1:
                    x += 1
                    continue
                x0 = x
                while x < W and self.depth[t][x] >= 1:
                    x += 1
                self.comp[t][x0:x] = len(self.floors)
                self.floors.append((t, x0, x))

    def close_shallow(self):
        """A floor never 48 deep is a pinch's tip: closed."""
        shut = False
        for t, x0, x1 in self.floors:
            if self.depth[t][x0:x1].max() < 48:
                self.pin[t][x0:x1] = True
                shut = True
        return shut

    def join(self):
        """Ladders: a spanning tree over the floors from the lowest tier's widest, and one loop in five;
        never two ladders between the same two floors.
        True if a floor was out of reach (it is closed; the cave is built again)."""
        N, W, b, rng = self.N, self.W, self.b, self.rng
        cand = {}
        for x0 in range(C, W - C, C):
            cols = range(x0, x0 + C)
            shown = [t for t in range(N) if all(self.depth[t][x] >= C for x in cols)]
            for up, lo in zip(shown, shown[1:]):           # neighbours in the stack here, back to front
                if len({b[lo][x] for x in cols}) == 1 and len({b[up + 1][x] for x in cols}) == 1:
                    cand.setdefault((self.comp[up][x0], self.comp[lo][x0]), []).append((x0, b[up + 1][x0] - Z, b[lo][x0]))
        low = [i for i, f in enumerate(self.floors) if f[0] == N - 1]
        if not low:
            raise ValueError('no lowest floor')
        start = max(low, key=lambda i: self.floors[i][2] - self.floors[i][1])
        reached, joined, self.ladders = {start}, set(), []
        while True:
            edges = [e for e in cand if (e[0] in reached) != (e[1] in reached)]
            if not edges:
                break
            e = rng.choice(edges)
            self.ladders.append(rng.choice(cand[e]))
            reached |= set(e)
            joined.add(e)
        for e in cand:                                     # a loop: two floors with no ladder between them yet (user: never two the same way)
            if e not in joined and e[0] in reached and e[1] in reached and rng.random() < 0.2:
                lad = rng.choice(cand[e])
                if all(abs(lad[0] - l[0]) >= 2 * C for l in self.ladders):
                    self.ladders.append(lad)
                    joined.add(e)
        lost = [i for i in range(len(self.floors)) if i not in reached]
        for i in lost:
            t, x0, x1 = self.floors[i]
            self.pin[t][x0:x1] = True
        self.start = start
        return bool(lost)

    def mouths(self):
        """A mouth a level: on a flat 64px stretch 48 deep, a cell clear of any ladder."""
        self.arches = {}
        for t in range(self.N):
            spots = [x0 for x0 in range(U, self.W - 2 * U, U)
                     if len(set(self.b[t][x0:x0 + U])) == 1 and self.depth[t][x0:x0 + U].min() >= 48
                     and all(not (l[2] == self.b[t][x0] and x0 - C < l[0] < x0 + U) for l in self.ladders)]
            if not spots:
                raise ValueError('level %d has nowhere for a mouth' % (self.N - 1 - t))
            self.arches[t] = self.rng.choice(spots) + C

    def lean(self, x, y):
        """How the band the rock at (x, y) is in runs across that cell: -1 its foot
        (and its top, parallel) rises to the right, 1 falls, 0 level."""
        b, N = self.b, self.N
        t = 0 if y < b[0][x] else next((t for t in range(N) if b[t][x] - Z <= y < b[t][x]), N)
        x0 = x - x % C
        d = int(b[t][min(x0 + C - 1, self.W - 1)]) - int(b[t][x0])
        return 1 if d >= 12 else -1 if d <= -12 else 0

    def classes(self, H):
        """What each pixel is: rock behind a floor, floor, or the dark."""
        b, N, W = self.b, self.N, self.W
        px = np.zeros((H, W), 'uint8')
        y = np.arange(H)[:, None]
        for t in range(N):
            px[(y >= b[t][None, :]) & (y < b[t + 1][None, :] - Z)] = FLOOR
        for t in range(N):
            px[(y >= b[t][None, :] - Z) & (y < b[t][None, :])] = ROCK
        px[y < b[0][None, :]] = ROCK                       # the back wall runs on up to the top of the map (user)
        front = b[N][None, :] - Z                          # the lowest floor is a ledge: a face of rock hangs under its edge (user)
        px[(y >= front) & (y < front + UNDER)] = ROCK
        return px


SHEET = os.path.join(ROOT, 'assets', 'tileset.png')     # --sheet: a copy a draft was laid into (tools/gen_cave_tiles.py --sheet --rock)
FLOORS = ((89, 89, 101), (96, 80, 40), (41, 99, 62), (89, 89, 101), (88, 53, 24), (123, 96, 29), (30, 30, 36))   # the game's fill, an ore


def sheet(ore):
    """The rock's pieces as the game has them: the ore's block of the sheet."""
    out = {k: tiles(33 + 5 * ore + cx, cy, *SIZE.get(k, (1, 1))) for k, (cx, cy) in CELLS.items()}
    out['floor0'] = np.zeros((C, C, 4), 'uint8')
    out['floor0'][..., :3] = FLOORS[ore]
    return out


def tiles(cx, cy, w=1, h=1):
    """Cells of the game's sheet, its key colour made clear."""
    a = np.array(Image.open(SHEET).convert('RGBA').crop((cx * C, cy * C, (cx + w) * C, (cy + h) * C)))
    a[(a[..., :3] == (255, 0, 0)).all(axis=2), 3] = 0
    return a


def backdrop(px, b, N, ore, shift=0):
    """The dark below the cave (user: "just glints of the material color"): glints
    in the rock's own two tones, one 16px cell in six, a 2 x 2 of the gem's lit
    tone or a cross of it with the base for arms (in the game they twinkle between
    the two and drift at half the camera's pace, as the stonehenge's stars)."""
    H, W = px.shape
    out = np.zeros((H, W, 3), 'uint8')
    lightest = lambda cell: max((tuple(int(n) for n in v) for v in cell[cell[..., 3] > 0][:, :3]),
                                key=lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])
    lit, base = lightest(tiles(33 + 5 * ore + 2, 0)), lightest(tiles(33 + 5 * ore, 0))   # the gem's face, a plain one
    for j in range(H // C):
        for i in range(W // C):
            k = h32(i, j, 9)
            if k % 6:
                continue
            x, y = i * C + shift + 2 + (k >> 12) % 11, j * C + 2 + (k >> 16) % 11
            if not 0 <= x < W - 3:
                continue
            if (k >> 4) & 1:
                out[y + 1, x:x + 3] = base
                out[y:y + 3, x + 1] = base
                out[y + 1, x + 1] = lit
            else:
                out[y:y + 2, x:x + 2] = lit
    return out


# which piece for which of a cell's quarters are rock: (top, bottom, left, right)
QUARTERS = {(1, 0, 1, 0): 'foot_up', (0, 1, 0, 1): 'top_up', (1, 0, 0, 1): 'foot_down', (0, 1, 1, 0): 'top_down',
            (1, 1, 1, 0): 'tip_l', (1, 1, 0, 1): 'tip_r', (0, 1, 1, 1): 'valley', (1, 0, 1, 1): 'vault',
            (0, 1, 0, 0): 'peak', (1, 0, 0, 0): 'fang'}
QUARTERS = {tuple(bool(v) for v in k): p for k, p in QUARTERS.items()}


KIND = {'top_flat': 0, 'foot_flat': 0, 'hang_flat': 0, 'face0': 0, 'face1': 0, 'face2': 0,      # faces you
        'lean_up': -1, 'top_up': -1, 'foot_up': -1, 'hang_up': -1,                             # turned, rising
        'lean_down': 1, 'top_down': 1, 'foot_down': 1, 'hang_down': 1}                         # turned, falling


def lay(px, S, out, cv):
    """The picture over `out`, a whole cell at a time; returns the cells that fit no piece."""
    H, W = px.shape
    floor_rgb = S['floor0'][0, 0, :3]
    odd = 0
    kind = {}                                              # a cell's wall: level, or turned which way (a turn's piece has both: none)

    def put(piece, cx, cy):
        a = S[piece]
        on = a[..., 3] > 0
        out[cy:cy + a.shape[0], cx:cx + a.shape[1]][on] = a[..., :3][on]

    at = lambda cx, cy, dx, dy: (ROCK if cy + dy < 0 else px[cy + dy, cx + dx] if cy + dy < H and 0 <= cx + dx < W else DARK)
    has = lambda cx, cy, what: 0 <= cy < H and 0 <= cx < W and (px[cy:cy + C, cx:cx + C] == what).any()
    for cy in range(0, H - C + 1, C):
        for cx in range(0, W - C + 1, C):
            cell = px[cy:cy + C, cx:cx + C]
            t, bt, l, r = at(cx, cy, 8, 3), at(cx, cy, 8, 12), at(cx, cy, 3, 8), at(cx, cy, 12, 8)
            # what shows where a piece is clear: the floor it stands by, else what is behind it
            ground = (cell == FLOOR).any() or (t == bt == l == r == ROCK and has(cx, cy - C, FLOOR))
            view = out[cy:cy + C, cx:cx + C]
            view[cell == FLOOR] = floor_rgb
            if ground:
                view[cell == ROCK] = floor_rgb
            rock = (t == ROCK, bt == ROCK, l == ROCK, r == ROCK)   # the cell's quarters: top, bottom, left, right
            if all(rock):
                up, down = at(cx, cy - C, 8, 12), at(cx, cy + C, 8, 3)
                way, k = cv.lean(cx + 8, cy + 8), h32(cx, cy) % 10
                piece = ('top_flat' if up != ROCK else 'hang_flat' if down == DARK else 'foot_flat' if down != ROCK
                         else 'lean_up' if way < 0 else 'lean_down' if way > 0
                         else 'face2' if k == 0 else 'face1' if k < 4 else 'face0')   # a gem in one in ten; face1 is face0 until a second is drawn
                put(piece, cx, cy)
                kind[cx, cy] = KIND[piece]
            elif any(rock):
                piece = QUARTERS.get(rock)
                if piece in ('foot_up', 'foot_down') and bt == DARK:
                    piece = 'hang' + piece[4:]             # over the dark a foot hangs ragged
                if piece:
                    put(piece, cx, cy)
                    if piece in KIND:
                        kind[cx, cy] = KIND[piece]
                else:
                    odd += 1
            elif t == bt == l == r == FLOOR and h32(cx, cy, 5) % 60 == 0:
                put('floor1', cx, cy)
    for (cx, cy), k in kind.items():                       # the corner where a front turns to a side: a black line
        if kind.get((cx + C, cy), k) != k:
            both = (px[cy:cy + C, cx + C - 1] == ROCK) & (px[cy:cy + C, cx + C] == ROCK)
            out[cy:cy + C, cx + C - 1][both] = 0
        if kind.get((cx, cy + C), k) != k:
            both = (px[cy + C - 1, cx:cx + C] == ROCK) & (px[cy + C, cx:cx + C] == ROCK)
            out[cy + C - 1, cx:cx + C][both] = 0
    return odd


def cave(N, seed, ore):
    while True:
        try:
            cv = Cave(N, seed)
            break
        except ValueError as e:
            print('   seed %d: %s; next seed' % (seed, e))
            seed += 1000
    b = cv.b
    H = (int(b[N].max()) // C + BELOW) * C
    S = sheet(ore)
    px = cv.classes(H)
    out = backdrop(px, b, N, ore)
    odd = lay(px, S, out, cv)

    def put(a, x, y):
        on = a[..., 3] > 0
        out[y:y + a.shape[0], x:x + a.shape[1]][on] = a[..., :3][on]
    length, foot = tiles(LADDER_COL0 + ore, LADDER_ROW), tiles(LADDER_COL0 + ore, LADDER_ROW + 1)
    for t, x in cv.arches.items():
        if t == N - 1:                                     # the mouth at the foot: an arch
            put(S['arch'], x, b[t][x] - 2 * C)
            continue
        put(S['hatch'], x, b[t][x] - 4 * C)                # a hole outside: a ladder up to its hatch
        for k in (1, 2, 3):
            put(foot if k == 1 else length, x, b[t][x] - k * C)
    for x0, y0, y1 in cv.ladders:
        for y in range(y0, y1, C):
            put(foot if y + C >= y1 else length, x0, y)
    node = tiles(33 + 5 * ore + 4, 0)
    rng = random.Random(seed * 7 + 1)
    for _ in range(9):
        t = rng.randrange(N)
        x0 = rng.randrange(2, cv.W // C - 2) * C
        y0 = (b[t][x0] // C + rng.randrange(1, 4)) * C
        if all(b[t][x] <= y0 and y0 + C <= b[t + 1][x] - Z for x in (x0, x0 + C - 1)):
            put(node, x0, y0)
    # the check: every floor that is left, and every mouth, reached from the lowest mouth by floors and ladders
    reach, grew = {cv.comp[N - 1][cv.arches[N - 1]]}, True
    links = [(cv.comp[np.argmax([(cv.depth[t][x0] >= C and b[t + 1][x0] - Z == y0) for t in range(N)])][x0],
              cv.comp[np.argmax([(cv.depth[t][x0] >= C and b[t][x0] == y1) for t in range(N)])][x0]) for x0, y0, y1 in cv.ladders]
    while grew:
        grew = False
        for a, c in links:
            if (a in reach) != (c in reach):
                reach |= {a, c}
                grew = True
    mouths_ok = all(cv.comp[t][x] in reach for t, x in cv.arches.items())
    print('levels %d seed %d %s: %dx%d, %d floors, %d ladders, floors reached %d/%d, mouths reached %s, cells fitting no piece %d, built %d times'
          % (N, seed, ORES[ore], cv.W, H, len(cv.floors), len(cv.ladders), len(reach), len(cv.floors),
             'all' if mouths_ok else 'NOT ALL', odd, cv.rounds))
    return Image.fromarray(out), ore


if __name__ == '__main__':
    if '--sheet' in sys.argv:
        SHEET = sys.argv.pop(sys.argv.index('--sheet') + 1)
        sys.argv.remove('--sheet')
    args = sys.argv[2:] or ['2', '3', '3', '3', '5', '1', '4', '2', '4']
    pics = [(int(args[i]),) + cave(int(args[i]), int(args[i + 1]), int(args[i + 2])) for i in range(0, len(args), 3)]
    board = Image.new('RGB', (max(p.width for _, p, _ in pics), sum(p.height + 24 for _, p, _ in pics)), (40, 40, 48))
    dr, y = ImageDraw.Draw(board), 0
    for n, p, ore in pics:
        dr.text((8, y + 6), 'A cave of %d levels, %s (mock, 1:1, the pieces as the sheet has them)' % (n, ORES[ore]),
                fill=(255, 255, 255))
        board.paste(p, (0, y + 22))
        y += p.height + 24
    board.save(sys.argv[1])
