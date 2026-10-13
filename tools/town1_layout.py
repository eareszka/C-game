"""Town 1's blueprint, laid out from the road pieces town_0 uses and the
coastal town's buildings on the sheet.

    python tools/town1_layout.py . <preview.png> [--write]

Roads are the start town's own cells, joined the way town_0 joins them: a
street runs across (two rows) or back at 45 degrees, up and to the right
(three cells a row), as the houses' depth does. A street across is named by
its top row y; one going back by k = x + y of its left cell. --write puts the
result in include/towns.h as town_1 and its wharves (the lighthouse and the
fishing sheds on a boardwalk, which the game lays toward the sea), and the
boardwalk's skirt cells on the sheet; without it only the previews are drawn.
The town is edited by hand in the tile editor after this (tile_editor town_1):
--write lays it out afresh and throws those edits away.
"""
import math, re, runpy, sys
from PIL import Image
ROOT, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, ROOT + '/tools')
import overworld_style as ow

N = 156
GRASS, TREE = 1, 5
cell = lambda code: int(code[0], 16) + int(code[1], 16) * 256 + 6     # 'cr' in hex: sheet col, row
g = [[GRASS] * N for _ in range(N)]


def put(x, y, codes):
    for i, c in enumerate(codes.split()):
        g[y][x + i] = cell(c)


def back(k, r0, r1):
    """A street going back, rows r0..r1."""
    for r in range(r0, r1 + 1):
        put(k - r, r, '46 56 66')


def across(y, left, right):
    """A street across at rows y, y+1, from its left end to its right:
    ('cap', x), or a corner onto the street going back with that k --
    left ('d', k) up from below, ('c', k) down from above; right ('b', k)
    turning down, ('g', k) turning up."""
    kind, v = left
    if kind == 'cap':
        x0 = v + 1
        put(v, y, '17'); put(v - 1, y + 1, '08 18')
    elif kind == 'd':
        x0 = v - y + 2
        put(v - y, y, 'a6 b6'); put(v - y - 1, y + 1, '46 a7 b7'); put(v - y + 1, y + 2, 'b8')
    else:
        x0 = v - y + 3
        put(v - y, y, '79 89 99'); put(v - y - 1, y + 1, '6a 7a 8a 9a')
    kind, v = right
    if kind == 'cap':
        t1, b1 = v - 1, v - 1
        put(v, y, '49 59 69'); put(v, y + 1, '4a 5a')
    elif kind == 'b':
        t1, b1 = v - y - 2, v - y - 3
        put(v - y - 1, y, 'b9 c9 d9 e9'); put(v - y - 2, y + 1, '78 ba ca da'); put(v - y - 3, y + 2, '36')
    else:
        t1, b1 = v - y - 1, v - y - 1
        put(v - y, y, 'c6 d6 e6'); put(v - y, y + 1, 'c7 d7')
    for x in range(x0, t1 + 1):
        g[y][x] = cell('67')
    for x in range(x0, b1 + 1):
        g[y + 1][x] = cell('68')


def tee(k, y):
    """A street going back leaves the top of the one across at y."""
    put(k - y, y, '37 47 57')


def cross(k, y):
    """A street going back crosses the one across at y."""
    tee(k, y)
    put(k - y - 1, y + 1, '88 ba b7 9a'); put(k - y - 2, y + 2, '79 89 a8 b8')


MAIN, TOP, NORTH, SOUTH, WEST_ROW, EAST_ROW = 96, 68, 44, 126, 76, 80     # the streets across, by top row
LEFT, RIGHT, CHURCH, MILL = 146, 182, 108, 216                          # the streets going back, by x + y

# the ring round the green: Main below it, Top behind it, a street up each side
across(MAIN, ('cap', 6), ('cap', 148))
across(TOP, ('d', LEFT), ('cap', 128))
back(LEFT, TOP + 2, MAIN - 1)
back(RIGHT, TOP + 3, MAIN - 1)
across(TOP, ('d', LEFT), ('cap', 128))             # its corner, over the end of the street up
# out from it, each a different way
back(RIGHT, NORTH + 2, TOP - 1)                    # the east side carries on over Top to North Street,
across(NORTH, ('cap', 64), ('b', RIGHT))           # which runs back west to a dead end
back(LEFT, MAIN + 3, SOUTH - 1)                    # the west side carries on over Main down to South Street
across(SOUTH, ('c', LEFT), ('cap', 97))
back(CHURCH, WEST_ROW + 2, MAIN - 1)               # a lane off Main's west end to a short row
across(WEST_ROW, ('d', CHURCH), ('cap', 56))
back(MILL, EAST_ROW + 2, MAIN - 1)                 # and one over Main's east end: up to a short row, down to South
across(EAST_ROW, ('d', MILL), ('cap', 150))
back(MILL, MAIN + 3, SOUTH - 1)
tee(RIGHT, MAIN); tee(CHURCH, MAIN); tee(MILL, SOUTH)
cross(LEFT, MAIN); cross(RIGHT, TOP); cross(MILL, MAIN)

SHEET = {n: at for n, (at, _) in ow.COAST.items()}
SHEET.update({n: ow.PIECES[n][0] for n in ('bench', 'street lamp', 'fountain', 'picket fence', 'flower bed')})
DOOR = {n: runpy.run_path(ROOT + '/art/structures/coast/%s_design.py' % n)['design']().get('door', [2])[0] for n in ow.COAST}
PLACED = []
sheet = Image.open(ROOT + '/assets/tileset.png').convert('RGBA')
spx = sheet.load()
inked = lambda c, r: any(spx[c * 16 + i, r * 16 + j][:3] != (255, 0, 0) for j in range(0, 16) for i in range(0, 16))


def house(name, x, street, path=False):
    """A building on the north side of a street across: against it, or a
    row back with a path up to its door, as town_0's shop has."""
    PLACED.append((name, x, street - 2 if path else street - 1))
    if path:
        k = x + DOOR[name] + street - 2
        tee(k, street); back(k, street - 1, street - 1)


def stand():
    """PLACED onto the grid, over nothing but grass -> (its road cells, its built cells)."""
    road = {(x, y) for y in range(len(g)) for x in range(len(g[0])) if g[y][x] != GRASS}
    built = set()
    for name, x, yb in PLACED:
        c0, r0, w, h = SHEET[name]
        for j in range(h):
            for i in range(w):
                tx, ty = x + i, yb - h + 1 + j
                if inked(c0 + i, r0 + j):
                    assert (tx, ty) not in road, '%s at %d,%d lies on a road (%d,%d)' % (name, x, yb, tx, ty)
                    assert (tx, ty) not in built, '%s at %d,%d lies on another piece (%d,%d)' % (name, x, yb, tx, ty)
                    g[ty][tx] = c0 + i + (r0 + j) * 256 + 6
                    built.add((tx, ty))
    return road, built


def far(open_):
    """{cell: tiles to the nearest of open_}, eight ways, over the grid."""
    dist = {p: 0 for p in open_}
    ring = list(open_)
    while ring:
        nxt = []
        for x, y in ring:
            for i in (-1, 0, 1):
                for j in (-1, 0, 1):
                    q = (x + i, y + j)
                    if 0 <= q[0] < len(g[0]) and 0 <= q[1] < len(g) and q not in dist:
                        dist[q] = dist[(x, y)] + 1
                        nxt.append(q)
        ring = nxt
    return dist


def seams(g, road):
    """Where a cell's paving runs to its edge and the cell beside it is clear
    there: a road cut off. (A road's own dark edge may lie on a cell's edge.)
    None, if the roads join as drawn."""
    vals = {g[y][x] for x, y in road}
    FILL = (215, 161, 117)
    def at(v, i, j):
        if v not in vals:
            return None
        p = spx[((v - 6) % 256) * 16 + i, ((v - 6) // 256) * 16 + j][:3]
        return None if p == (255, 0, 0) else p
    bad = []
    for x, y in sorted(road):
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            if not (0 <= x + dx < len(g[0]) and 0 <= y + dy < len(g)):
                continue
            a, b = g[y][x], g[y + dy][x + dx]
            edge = lambda v, far: [at(v, (15 if far else 0) if dx else i, i if dx else (15 if far else 0)) for i in range(16)]
            mine, theirs = edge(a, dx + dy > 0), edge(b, dx + dy < 0)
            n = sum(m == FILL and t is None for m, t in zip(mine, theirs))
            if n:
                bad.append((x, y, dx, dy, n))
    return bad


def checked(name, road, built):
    bad = seams(g, road)
    loose = [b for b in bad if (b[0] + b[2], b[1] + b[3]) not in built]     # a door path's end lies under its door, as town_0's do
    print('%s: %d road cells, %d path ends under doors, %d seams that do not meet' % (
        name, len(road), len(bad) - len(loose), len(loose)), loose[:12])
    assert not loose


# the green: the town hall at its back on a lane from Main, the bandstand and the fountain either side of the lane
HALL = (81, 80)
lane = HALL[0] + DOOR['townhall'] + HALL[1]
tee(lane, MAIN); back(lane, HALL[1] + 1, MAIN - 1)
PLACED += [('townhall', *HALL), ('gazebo', 66, 90), ('fountain', 79, 92),
           ('street lamp', 79, 82), ('street lamp', 91, 82), ('street lamp', 56, 94), ('street lamp', 86, 94),
           ('bench', 64, 90), ('bench', 72, 90), ('bench', 77, 92), ('bench', 82, 92),
           ('flower bed', 63, 87), ('flower bed', 73, 87), ('flower bed', 76, 94), ('flower bed', 84, 91)]
PLACED += [('picket fence', x, 94) for x in list(range(58, 68)) + list(range(78, 85))]
# North Street: the long row, the big houses and the meeting house
house('captain', 68, NORTH, True); house('cape', 80, NORTH); house('inn', 90, NORTH, True)
house('winged', 104, NORTH); house('meeting', 115, NORTH, True); house('cape', 125, NORTH)
# behind the green
house('winged', 82, TOP); house('store', 92, TOP, True); house('cape', 103, TOP); house('shack', 123, TOP)
# the west row and Main's west end
house('cape', 36, WEST_ROW); house('winged', 46, WEST_ROW, True)
house('inn', 26, MAIN, True); house('cape', 40, MAIN)
# Main east of the green, and the east row
house('captain', 101, MAIN, True); house('cape', 112, MAIN); house('winged', 134, MAIN)
house('cape', 140, EAST_ROW)
# South Street: large houses in the big block
house('captain', 34, SOUTH, True); house('inn', 46, SOUTH); house('winged', 59, SOUTH, True)
house('cape', 69, SOUTH); house('store', 79, SOUTH, True)
ROAD, BUILT = stand()

# ---- woods: wherever the ground is far from a street or a building, the edge wandering ----
# Main's two ends are kept open to the town's edge, for the roads that come in.
dist = far(ROAD | BUILT | {(x, y) for y in range(MAIN - 2, MAIN + 4) for x in list(range(0, 8)) + list(range(148, N))})
for y in range(N):
    for x in range(N):
        wander = 2.2 * math.sin(x * .29 + y * .13) + 1.8 * math.sin(y * .37 - x * .11) + 1.2 * math.sin((x + y) * .61)
        if g[y][x] == GRASS and dist[(x, y)] > 6 + wander:
            g[y][x] = TREE

t0 = [[int(v) for v in re.findall(r'-?\d+', r)] for r in re.search(
    r'static const int town_0\[.*?\};', open(ROOT + '/include/towns.h', encoding='utf-8').read(), re.S).group(0).splitlines()
    if r.strip().startswith('{')]
t0road = {(x, y) for y in range(N) for x in range(N) if t0[y][x] > 6 and (t0[y][x] - 6) // 256 in range(6, 11)}
print('town_0, for comparison: %d road cells, %d cut' % (len(t0road), len(seams(t0, t0road))))
checked('town', ROAD, BUILT)
print('pieces: %d, trees: %d' % (len(PLACED), sum(r.count(TREE) for r in g)))

# ---- the wharf: the one part not fixed in place ----
# The sea is on a different side in every seed (the user, 2026-10-12: "the
# lighthouse/fishing huts will always be closest to the water depending on the
# seed but the rest of the town is static"), and the way to it is a road that
# becomes boardwalk: "their is a road going towards the water. once over the
# water it turns into boardwalk like the one used in graveyards. on this
# boardwalk is the lighthouse and finishing huts ... make sure the boardwalk
# goes toward the direction of the world border that is water ... the pier
# needs to be oblique projected shape". So there is a wharf for each border
# the ocean can be on, each running out toward it with the lighthouse at its
# seaward tip, and the game lays the one for its seed at the end of a road
# (stamp_town_pier in src/tilemap.cpp).
#
# A deck is drawn as the graveyard dungeon bakes its boardwalk (graveyard_bake
# in src/dungeon.cpp), from the same pieces on the sheet: a floor in the
# houses' projection -- a point u across and v back lands at (u + v, -v), so a
# deck's sides run up and to the right at 45 degrees -- the planks read along
# that slant, a black line round the floor, the planks' face in the 8 px under
# every edge (lit where it looks south, shaded where it looks east) and the
# posts in the 24 px under that. It is then cut into cells for the sheet.
T = 16
SHEDS = ('boathouse', 'shack', 'shack', 'lighthouse')         # landward to seaward
size = lambda n: SHEET[n][2:]
BOARD = (232, 44)                                             # the graveyard's block: GY_TOP_BOARD, and below it
cut = lambda dy, h: [[sheet.getpixel((BOARD[0] * 16 + x, (BOARD[1] + dy) * 16 + y)) for x in range(64)] for y in range(h)]
TOP, UNDER, FACE_S, FACE_E = cut(0, 64), cut(4, 24), cut(6, 8), cut(7, 8)
KEY, BLACK = (255, 0, 0, 255), (0, 0, 0, 255)
assert all(p != KEY for r in TOP for p in r), 'the boardwalk is not where it was on the sheet'


def bake(rects):
    """The floor [(u0, u1, v0, v1)] in tiles -> (rows of pixels, rows of
    floor or not), v 0 on the bottom row of floor, 32 px of skirt under it."""
    W = max(u1 + v1 for u0, u1, v0, v1 in rects) * T
    V = max(r[3] for r in rects) * T
    H = V + 32
    fl = [[any(u0 * T <= x - (V - 1 - y) < u1 * T and v0 * T <= V - 1 - y < v1 * T for u0, u1, v0, v1 in rects)
           for x in range(W)] for y in range(H)]
    FL = lambda x, y: 0 <= x < W and 0 <= y < H and fl[y][x]
    out = [[KEY] * W for _ in range(H)]
    side = [[None] * W for _ in range(H)]
    for x in range(W):
        last = -1000
        for y in range(H):
            if fl[y][x]:
                last = y
                continue
            k = y - last
            if k <= 8:
                south = not FL(x - 1, last + 1)
                side[y][x] = south
                out[y][x] = FACE_S[k - 1][x & 63] if south else FACE_E[k - 1][(62 - last) & 63]
            elif k <= 32 and UNDER[k - 9][x & 63] != KEY:
                out[y][x] = UNDER[k - 9][x & 63]
    for y in range(H):
        for x in range(W):
            if x and side[y][x] is False and side[y][x - 1] is True:
                out[y][x] = BLACK                              # a south face turning east: its edge
            if fl[y][x]:
                edge = not (FL(x - 1, y) and FL(x + 1, y) and FL(x, y - 1) and FL(x, y + 1))
                out[y][x] = BLACK if edge else TOP[y & 63][(x + y) & 63]
    return out, fl


CELLS = {}                                                    # a cell's pixels -> its place in the deck's rows of the sheet
DECK_ROW0, DECK_COLS = 192, 256


def wharf(rects, placed, join):
    """A wharf: its floor in tiles (u, v), its buildings [(name, u, v)] --
    each standing on the two rows of floor from v, a tile in from u -- and
    the floor cell (u, v) that meets the way out. -> its grids, which have
    the buildings' height above the floor and two rows of skirt below it:
    cell (the deck's sheet cell), kind (1 floor, 2 floor the feet go round,
    3 skirt only), art (the buildings' sheet cells), and the join's cell."""
    px, fl = bake(rects)
    vmax = max(r[3] for r in rects)
    pad = max(0, max(v + size(n)[1] for n, u, v in placed) - vmax)
    w, h = len(px[0]) // T, pad + len(px) // T
    w = max([w] + [u + v + size(n)[0] for n, u, v in placed])
    cell = [[0] * w for _ in range(h)]
    kind = [[0] * w for _ in range(h)]
    art = [[0] * w for _ in range(h)]
    for cy in range(len(px) // T):
        for cx in range(len(px[0]) // T):
            block = tuple(tuple(px[cy * T + j][cx * T:cx * T + T]) for j in range(T))
            if all(p == KEY for r in block for p in r):
                continue
            n = CELLS.setdefault(block, len(CELLS))
            cell[pad + cy][cx] = n % DECK_COLS + (DECK_ROW0 + n // DECK_COLS) * 256 + 6
            floor = sum(fl[cy * T + j][cx * T + i] for j in range(T) for i in range(T))
            kind[pad + cy][cx] = 3 if not floor else 1 if floor >= 100 else 2    # a sliver of floor is not stood on
    row = lambda v: pad + vmax - 1 - v                          # the grid row of the floor's row v
    for name, u, v in placed:
        c0, r0, bw, bh = SHEET[name]
        for j in range(bh):
            for i in range(bw):
                if inked(c0 + i, r0 + j):
                    x, y = u + v + i, row(v) - (bh - 1 - j)
                    assert art[y][x] == 0, '%s lies on another building' % name     # over a skirt behind it, it hides it
                    art[y][x] = c0 + i + (r0 + j) * 256 + 6
                    if j >= bh - 2:                           # its foot: the two rows it stands on
                        assert kind[y][x] in (1, 2), '%s stands off the deck at %d,%d' % (name, x, y)
                        kind[y][x] = 2
    return cell, kind, art, (join[0] + join[1], row(join[1]))


def across_wharf(seaward_west):
    """Lying across, four tiles deep: the sheds on its back two rows, the walk
    along the front two, a clear landing at the landward end. It joins the
    street by the row Main Street's top row runs into."""
    long_, u, placed = 39, 6, []
    for n in SHEDS:
        placed.append((n, u, 2))
        u += size(n)[0] + 2
    if seaward_west:                                          # the same row, the other way round
        placed = [(n, long_ - u0 - size(n)[0], v) for n, u0, v in placed]
    return wharf([(0, long_, 0, 4)], placed, (long_ if seaward_west else 0, 2))


def along_wharf(seaward_north):
    """Running back: a walk two tiles across, as wide as the road it carries
    on from, and off its east side a bay of floor for each shed."""
    # (name, the row it stands from), from the near end: four rows of landing
    # first when that is the landward end (the sea to the north), last when
    # the sea is toward the viewer. Each stands clear of the one before it and
    # of the posts under the next one's bay.
    v, at = (4 if seaward_north else 0), []
    for n in (SHEDS if seaward_north else SHEDS[::-1]):
        at.append((n, v))
        v += size(n)[1] + 2
    long_ = at[-1][1] + 2 + (0 if seaward_north else 4)
    rects = [(0, 2, 0, long_)] + [(2, 3 + size(n)[0], v0, v0 + 2) for n, v0 in at]
    return wharf(rects, [(n, 3, v0) for n, v0 in at], (0, 0 if seaward_north else long_ - 1))


# by the game's ocean_side: 0 west, 1 east, 2 north, 3 south
WHARVES = [across_wharf(True), across_wharf(False), along_wharf(True), along_wharf(False)]
# The ways out. West and east: Main Street's end caps. North: North Street,
# carried on west of its cap and turned up a street going back (its x + y).
# South: the mill lane, carried on over South Street.
PIER = {'TOWN1_MAIN_Y': MAIN, 'TOWN1_MAIN_W': 6, 'TOWN1_MAIN_E': 148,
        'TOWN1_NORTH_Y': NORTH, 'TOWN1_NORTH_CAP': 64, 'TOWN1_NORTH_K': 97,
        'TOWN1_SOUTH_Y': SOUTH, 'TOWN1_SOUTH_K': MILL}
DECK_ROWS = (len(CELLS) + DECK_COLS - 1) // DECK_COLS
for block in CELLS:
    assert len({p for r in block for p in r} - {KEY}) <= 4, 'a deck cell has over four colours'


def unkey(t):
    t.putdata([(0, 0, 0, 0) if p[:3] == (255, 0, 0) else p for p in t.get_flattened_data()])
    return t


def sheet_cell(v):
    c, r = (v - 6) % 256, (v - 6) // 256
    if r >= DECK_ROW0:                                        # not on the sheet until it is written
        block = next(b for b, n in CELLS.items() if n == c + (r - DECK_ROW0) * DECK_COLS)
        t = Image.new('RGBA', (T, T))
        t.putdata([p for row in block for p in row])
        return unkey(t)
    return unkey(sheet.crop((c * 16, r * 16, c * 16 + 16, r * 16 + 16)))


def picture(grid, out, under=None, blank=(40, 40, 48, 255)):
    im = Image.new('RGBA', (len(grid[0]) * 16, len(grid) * 16), (92, 148, 252, 255) if under else (78, 220, 74, 255))
    for y, r in enumerate(grid):
        for x, v in enumerate(r):
            at = (x * 16, y * 16)
            if under and under[y][x]:
                im.alpha_composite(sheet_cell(under[y][x]), at)
            if v in (TREE, 0) and not under:
                im.paste((5, 143, 58, 255) if v else blank, at + (at[0] + 16, at[1] + 16))
            elif v >= 6:
                im.alpha_composite(sheet_cell(v), at)
    im.convert('RGB').save(out)
    return im


picture(g, OUT).convert('RGB').resize((N * 8, N * 8), Image.BILINEAR).save(OUT.replace('.png', '_small.png'))
for side, (cell, kind, art, join) in zip('wens', WHARVES):
    picture(art, OUT.replace('.png', '_wharf_%s.png' % side), under=cell)
    print('wharf %s: %d x %d, joins at %s' % (side, len(cell[0]), len(cell), join))
print('deck cells: %d, in %d rows of the sheet from row %d' % (len(CELLS), DECK_ROWS, DECK_ROW0))

if '--write' in sys.argv:
    # the deck's rows of the sheet are this script's own: cleared, then laid afresh
    sheet.paste(KEY, (0, DECK_ROW0 * 16, DECK_COLS * 16, (DECK_ROW0 + max(DECK_ROWS, 2)) * 16))
    for block, n in CELLS.items():
        t = Image.new('RGBA', (T, T))
        t.putdata([p for row in block for p in row])
        sheet.paste(t, (n % DECK_COLS * 16, (DECK_ROW0 + n // DECK_COLS) * 16))
    sheet.save(ROOT + '/assets/tileset.png')
    p = ROOT + '/include/towns.h'
    s = open(p, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in s else '\n'
    rows = lambda grid: ''.join('    {' + ','.join(map(str, r)) + '},' + nl for r in grid)
    flat = lambda grid: ''.join('    ' + ','.join(map(str, r)) + ',' + nl for r in grid)
    body = 'static const int town_1[%d][%d] = {%s' % (N, N, nl) + rows(g) + '};' + nl + nl
    body += ('// Town 1\'s wharf: the lighthouse, the boathouse and the fishing shacks on a' + nl +
             '// boardwalk over the sea, one for each border the ocean can be on (ocean_side:' + nl +
             '// west, east, north, south), each running out toward it. cell: the deck\'s sheet' + nl +
             '// cell, as a blueprint\'s; kind: 1 floor, 2 floor the feet go round, 3 the skirt' + nl +
             '// under an edge; art: the buildings\' sheet cells. join is the floor cell that' + nl +
             '// meets the way out from the town (stamp_town_pier), which the TOWN1_ values' + nl +
             '// below place. The deck\'s cells are rows TOWN1_DECK_ROW0.. of the sheet.' + nl +
             '// From tools/town1_layout.py.' + nl +
             'struct TownWharf { int w, h, join_x, join_y; const int* cell; const unsigned char* kind; const int* art; };' + nl)
    for side, (cell, kind, art, join) in zip('wens', WHARVES):
        body += 'static const int town_1_wharf_%s_cell[] = {%s' % (side, nl) + flat(cell) + '};' + nl
        body += 'static const unsigned char town_1_wharf_%s_kind[] = {%s' % (side, nl) + flat(kind) + '};' + nl
        body += 'static const int town_1_wharf_%s_art[] = {%s' % (side, nl) + flat(art) + '};' + nl
    body += 'static const TownWharf TOWN1_WHARF[4] = {' + nl + ''.join(
        '    { %d, %d, %d, %d, town_1_wharf_%s_cell, town_1_wharf_%s_kind, town_1_wharf_%s_art },%s' % (
            len(c[0]), len(c), j[0], j[1], side, side, side, nl) for side, (c, k, a, j) in zip('wens', WHARVES)) + '};' + nl
    body += ''.join('#define %s %d%s' % (k, v, nl) for k, v in PIER.items())
    body += '#define TOWN1_DECK_ROW0 %d%s#define TOWN1_DECK_ROWS %d%s// end of town 1\'s wharf' % (DECK_ROW0, nl, DECK_ROWS, nl)
    m = re.search(r'static const int town_1\[[^\]]*\]\[[^\]]*\] = \{.*?\};'
                  r'(\s*// Town 1\'s wharf.*?// end of town 1\'s wharf)?', s, re.S)
    open(p, 'w', encoding='utf-8', newline='').write(s[:m.start()] + body + s[m.end():])
    print('wrote town_1 and its wharves to', p, 'and the deck\'s cells to the sheet')
