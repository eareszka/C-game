"""Town 2's blueprint: Xuelin, a walled town on the snowfield's edge.

    python tools/town2_layout.py . <preview.png> [--write]

A dense, low town inside one wall with one gate (the user, 2026-10-28:
"snowland edge. traditional chinese architecture", "very dense and compact
town but no tall buildings", "walled town, one main gate"; then "same idea but
2x as big" -- twice the area). The plan is the houses' projection, as town_1's
is: a street across is two rows, a street going back climbs up and to the
right at 45 degrees, three cells a row. So the wall, a rectangle on the
ground, is drawn as a parallelogram: the front and back walls across, the side
walls going back. Everything going back is named by k = x + y of its left
cell, as town1_layout.py names its streets, and a lot is a band k0..k1 on
every one of its rows.

The streets are town_0's own cells (the same pieces town1_layout.py lays).
Until a building is drawn its lot is 0, which the game shows as the
placeholder inside the cleared ground (stamp_town_blueprint), and the wall is
the hub. --write puts town_2 and its XUELIN_ defines into include/towns.h --
the cleared ground, the walls' extent and the street out of the gate, which
placement, the stamp and the road read -- without it only the preview is
drawn. The lots are listed in <preview>.json.
"""
import json, math, os, re, runpy, sys
from PIL import Image
ROOT, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import overworld_style as ow

N = 156
BLANK, SNOW, PATH, WALL, TREE = 0, 1, 2, 3, 5
cell = lambda code: int(code[0], 16) + int(code[1], 16) * 256 + 6     # 'cr' in hex: sheet col, row
g = [[BLANK] * N for _ in range(N)]


def put(x, y, codes):
    for i, c in enumerate(codes.split()):
        g[y][x + i] = cell(c)


def back(k, r0, r1):
    """A street going back, rows r0..r1."""
    for r in range(r0, r1 + 1):
        put(k - r, r, '46 56 66')


def across(y, left, right):
    """A street across at rows y, y+1, capped at both ends (town1_layout.py's
    across, its 'cap' ends only)."""
    put(left, y, '17'); put(left - 1, y + 1, '08 18')
    put(right, y, '49 59 69'); put(right, y + 1, '4a 5a')
    for x in range(left + 1, right):
        g[y][x] = cell('67')
        g[y + 1][x] = cell('68')


def tee(k, y):
    """A street going back leaves the top of the one across at y."""
    put(k - y, y, '37 47 57')


def cross(k, y):
    """A street going back crosses the one across at y (rows y..y+2)."""
    tee(k, y)
    put(k - y - 1, y + 1, '88 ba b7 9a'); put(k - y - 2, y + 2, '79 89 a8 b8')


# ---- the wall: front and back across, the sides going back ----
BACK = 50                           # the back wall's row (the sides two thick, the runs across one: 2026-10-30)
TIER = 9                            # a row of lots (7) and the street in front of it (2)
TIERS = 6
STREETS = [BACK + 2 + 7 + TIER * i for i in range(TIERS)]      # the streets across inside, by top row
MARGIN = 3                          # rows between the front street and the front wall: the wall, 32 high and
                                    # a row thick, rises two rows over what is behind it, and the
                                    # front street must stay in sight (2026-10-28); the rows it covers are its own
FRONT = STREETS[-1] + 2 + MARGIN    # the row behind the front wall (its own: once the wall's inner row)
GATE_Y = FRONT + 2                  # the street outside, across the front of the wall
KW, KE = 123, 189                   # the side walls' k: west k..k+1, east k-1..k
BLOCK = lambda i: (STREETS[i] - 7, STREETS[i] - 1)              # tier i's lots: the 7 rows behind its street
# what is drawn: the wall's extent, and the cleared ground round it
WALL_BOX = (KW - FRONT - 1, BACK, KE - BACK + 1, FRONT + 2)    # x0, y0, x1, y1 (ends exclusive)
BOX = (WALL_BOX[0] - 8, BACK - 10, WALL_BOX[2] + 8, GATE_Y + 12)
assert 0 <= BOX[0] and BOX[2] <= N and 0 <= BOX[1] and BOX[3] <= N, BOX
APRON = 4                           # snow laid round the wall and along the street outside
inside = lambda x, y: BACK <= y <= FRONT + 1 and KW - y <= x <= KE - y
for y in range(BOX[1], BOX[3]):
    for x in range(BOX[0], BOX[2]):
        near_wall = BACK - APRON <= y <= FRONT + 1 + APRON and KW - y - APRON <= x <= KE - y + APRON
        near_street = abs(y - GATE_Y - .5) <= APRON - .5
        if inside(x, y) or near_wall or near_street:
            g[y][x] = SNOW

MAIN = 156                          # the main street: from the gate to the drum tower's door
LANE_W, LANE_E = 137, 175           # the lanes: from the front street to a door at the back
for y in range(BACK, FRONT + 2):
    for x in (KW - y, KW - y + 1, KE - y - 1, KE - y):
        g[y][x] = WALL
for y in (BACK, FRONT + 1):                        # the runs across: their outer rows
    for x in range(KW - y, KE - y + 1):
        g[y][x] = WALL

# ---- streets ----
for y in STREETS:                   # each capped just inside the side walls
    across(y, KW + 2 - y, KE - 4 - y)
MAIN_X = BOX[0] + 1, BOX[2] - 3     # the street outside's caps: XUELIN_MAIN_W, XUELIN_MAIN_E
across(GATE_Y, *MAIN_X)


def street_back(k, top, door):
    """A street going back from the front street up over every street to
    `top` (the highest it crosses), then a cell more: the path under a door."""
    tee(k, STREETS[-1])
    ys = [y for y in STREETS[:-1] if y >= top]
    for y in ys:
        cross(k, y)
    below = STREETS[-1]
    for y in sorted(ys, reverse=True):
        back(k, y + 3, below - 1)
        below = y
    if door:
        back(k, top - 1, top - 1)


# the main street: in at the gate, over every street inside, through the
# square to the drum tower's door
tee(MAIN, GATE_Y); back(MAIN, STREETS[-1] + 2, FRONT + 1)
street_back(MAIN, STREETS[2], True)
# the lanes: up from the front street, over the rest, each to a door at the back
for k in (LANE_W, LANE_E):
    street_back(k, STREETS[0], True)
ROAD = {(x, y) for y in range(N) for x in range(N) if g[y][x] >= 6}

# ---- the square: either side of the main street, below the drum tower
# (the user, 2026-10-29: "should be like a courtyard", then "use the already
# existing road", then marked in red the roads and in green the walls): in
# each half a road of the town's own going back from the front street to the
# drum tower's, so the square is three roads going back -- those two and the
# main street -- and between them four walled yards of snow. Each yard is
# walled with the overworld's own stone yard wall ("the same walls already
# used in the overworld": the catacombs', entrances/yard_walls_design.py)
# across its back and its front and down its outer side, its side to its own
# road left open, so the two yards of a half face each other across it. A
# side runs back at 45 degrees unbroken, as the catacombs' do; the game picks
# each piece from its neighbours. A pine or two in each yard, stone lanterns
# by the roads at the front (drawn: town_design.py square). ----
SQ_TIER = 3
SQUARE = (LANE_W + 4, LANE_E - 1, *BLOCK(SQ_TIER))           # k from..to, rows
# west and east of the main street: the east one clear of the main street's
# crossings, whose foot is four cells wide
HALVES = [(SQUARE[0], MAIN - 1), (MAIN + 4, SQUARE[1])]
_sp = open(os.path.join(ROOT, 'src', 'sheet_sprites.inc')).read()
_at = lambda n: int(re.search(r'#define %s (\d+)' % n, _sp).group(1))
YARD_WALL = _at('YARD_WALL_SHEET_COL') + (_at('YARD_WALL_SHEET_ROW') + 1) * 256 + 6    # YARD_WALL_MARK
r0, r1 = SQUARE[2], SQUARE[3]


def tee_below(k, y):
    """A street going back meets the one across at y from below, and stops:
    the lower rows of a crossing, the street across whole above it."""
    put(k - y - 1, y + 1, '88 ba b7 9a'); put(k - y - 2, y + 2, '79 89 a8 b8')


SQ_BACK, YARDS = [], []                                     # the roads' k; each yard (k0, k1, its walled side)
for k0, k1 in HALVES:
    kb = (k0 + k1) // 2 - 1                                 # its road going back, three wide
    SQ_BACK.append(kb)
    tee(kb, STREETS[SQ_TIER]); back(kb, r0, r1)             # from the front street to the drum tower's,
    tee_below(kb, STREETS[SQ_TIER - 1])                     # meeting it from below
    YARDS += [(k0, kb - 1, k0), (kb + 3, k1, k1)]
ROAD = {(x, y) for y in range(N) for x in range(N) if g[y][x] >= 6}
YARD = set()
for k0, k1, side in YARDS:
    for y in range(r0, r1 + 1):
        for k in range(k0, k1 + 1):
            if (y in (r0, r1) or k == side) and (k - y, y) not in ROAD:
                YARD.add((k - y, y))
# a pine in each yard toward the back, another toward the front by its outer
# wall; a stone lantern either side of each road at the front, clear of its
# foot (the cell over one on the screen is a step back and to the west: what
# rises into it may not stand where that is a wall, a pine or its canopy)
PINES = [(k - y, y) for k0, k1, side in YARDS
         for k, y in (((k0 + k1) // 2, r0 + 2), (side + (2 if side == k0 else -2), r1 - 1))]
LANTERNS = [(k - (r1 - 1), r1 - 1) for kb in SQ_BACK for k in (kb - 1, kb + 4)]
for y in range(r0, r1 + 1):
    for k in range(SQUARE[0], SQUARE[1] + 1):
        if (k - y, y) not in ROAD:
            g[y][k - y] = YARD_WALL if (k - y, y) in YARD else SNOW
assert not (set(PINES) | set(LANTERNS)) & (ROAD | YARD), 'a pine or lantern on a road or a wall'
assert not {(x, y - 1) for x, y in PINES + LANTERNS} & (YARD | set(PINES) | set(LANTERNS)), \
    'something rises into a wall, a pine or a lantern'
# a row of the square's pines inside the front wall, under the front street
# (the user, 2026-10-30: "have it be a row of those trees used in the
# middle"), a cell each, their canopies in the row over them; the main street
# and a cell either side of it left open, the way in from the gate
ENTRY_ROW = STREETS[-1] + 3
ENTRY_PINES = [(k - ENTRY_ROW, ENTRY_ROW) for k in range(KW + 2, KE - 1) if not MAIN - 1 <= k <= MAIN + 3]
assert not {(x, y - d) for x, y in ENTRY_PINES for d in (0, 1)} & ROAD, 'an entry pine on a road'

# ---- lots: (name, k0, k1, top row, bottom row) ----
# Between the walls and the streets going back, the four strips of a tier:
A = (KW + 2, LANE_W - 1)            # the wall to the west lane
B = (LANE_W + 4, MAIN - 1)          # the west lane to the main street
C = (MAIN + 4, LANE_E - 1)          # the main street to the east lane
D = (LANE_E + 4, KE - 2)            # the east lane to the wall


def split(span, widths):
    """span (k0, k1) cut into lots of these widths, the last taking what is left."""
    k, out = span[0], []
    for w in widths[:-1]:
        out.append((k, k + w - 1)); k += w
    out.append((k, span[1]))
    return out


LOTS = []
def lots(tier, strip, widths, names=None, rows=None):
    y0, y1 = rows or BLOCK(tier)
    for i, (k0, k1) in enumerate(split(strip, widths)):
        LOTS.append(((names or {}).get(i, 'house'), k0, k1, y0, y1))

# tier 0, under the back wall: each lane ends at the door of a wide house
# across it -- the shrine at the west lane, the elder's at the east
y0, y1 = BLOCK(0)
LOTS += [('house', A[0], A[0] + 6, y0, y1), ('shrine', A[0] + 7, LANE_W + 8, y0, y1 - 1),
         ('house', LANE_W + 9, LANE_W + 16, y0, y1), ('house', LANE_W + 17, MAIN + 6, y0, y1),
         ('house', MAIN + 7, LANE_E - 6, y0, y1), ('elder', LANE_E - 5, LANE_E + 7, y0, y1 - 1),
         ('house', LANE_E + 8, D[1], y0, y1)]
for t in (1, 4):                     # ordinary rows: two to a strip, one in the narrow east one
    lots(t, A, [6, 6]); lots(t, B, [8, 7]); lots(t, C, [7, 8]); lots(t, D, [9])
# tier 2, behind the square: the drum tower, the main street at its door
y0, y1 = BLOCK(2)
lots(2, A, [6, 6])
LOTS += [('house', B[0], B[0] + 8, y0, y1), ('drum tower', B[0] + 9, C[1] - 9, y0, y1 - 1),
         ('house', C[1] - 8, C[1], y0, y1)]
lots(2, D, [9])
# tier 3, either side of the square
lots(3, A, [6, 6]); lots(3, D, [9])
# tier 5, the first thing through the gate: the inn and the book shop face each other
lots(5, A, [6, 6]); lots(5, B, [15], {0: 'inn'}); lots(5, C, [15], {0: 'book shop'}); lots(5, D, [9])

BUILT = set()
for name, k0, k1, y0, y1 in LOTS:
    assert k1 - k0 >= 3, (name, k0, k1)
    for y in range(y0, y1 + 1):
        for k in range(k0, k1 + 1):
            p = (k - y, y)
            assert p not in ROAD, '%s at k %d-%d lies on a street (%d,%d)' % (name, k0, k1, *p)
            assert g[y][k - y] == SNOW, '%s at k %d-%d lies on %d at (%d,%d)' % (name, k0, k1, g[y][k - y], *p)
            assert p not in BUILT
            BUILT.add(p)
            g[y][k - y] = BLANK

# ---- the buildings drawn so far, each on its lot ----
# Every building and the wall are one drawing, art/structures/xuelin/
# town_design.py, laid at CANVAS (its top left cell in the footprint, its
# cells across and down), so where one stands in front of another the nearer
# wins pixel by pixel. That drawing is the overlay over the ground here
# (XUELIN_ART, laid by stamp_town_blueprint): what rises above a building's
# lot -- roofs, eaves -- free to hang over a street or the lot behind.
# layout.json hands town_design.py the plan; its export comes back here.
lot_at_k = lambda tier, k0: next(i for i, l in enumerate(LOTS) if l[1] == k0 and l[4] == BLOCK(tier)[1])
# (piece, lot, its options): the first courtyard house, on the west lane's row
# by the square; then every ordinary lot -- a courtyard house on every third
# wide one, the rest shops and deep blocks by turns, each its own sign or none
DRAWN = [('courtyard', lot_at_k(4, B[0]), {})]
SIGNS = ['TEA', 'NOODLES', 'CLOTH', 'HERBS', 'RICE', 'SALT', 'COAL']
n = 0
for i, (name, k0, k1, y0, y1) in enumerate(LOTS):
    if name != 'house' or i == DRAWN[0][1]:
        continue
    w = k1 - k0 + 1
    if w >= 8 and n % 3 == 1:
        DRAWN.append(('courtyard', i, {}))
    else:
        fits = [t for t in SIGNS[n % len(SIGNS):] + SIGNS if 4 * len(t) + 3 <= w * 16 - 40]
        near = {o.get('sign') for _, j, o in DRAWN               # no sign twice side by side, or a row behind or before
                if abs(LOTS[j][4] - y1) <= TIER and LOTS[j][1] - TIER <= k1 and k0 <= LOTS[j][2] + TIER}
        fits = [t for t in fits if t not in near] or fits
        DRAWN.append(('shophouse', i, {'kind': 'block' if n % 2 else 'shop', 'sign': None if n % 4 == 3 else fits[0]}))
    n += 1
DRAWN += [('bookshop', i, {}) for i, l in enumerate(LOTS) if l[0] == 'book shop']
DRAWN += [('inn', i, {}) for i, l in enumerate(LOTS) if l[0] == 'inn']
DRAWN += [('drumtower', i, {}) for i, l in enumerate(LOTS) if l[0] == 'drum tower']
DRAWN += [(n, i, {}) for i, l in enumerate(LOTS) for n in ('shrine', 'elder') if l[0] == n]
CANVAS = (BOX[0], BOX[1], BOX[2] - BOX[0], FRONT + 3 - BOX[1])      # down to the street outside's top row

# ---- the streets' dressing (the user, 2026-10-29: "moderate"): red lantern
# posts along the main street and at its crossings; firewood stacked on the
# street before every third house; a few hand carts; the snow country's own
# props here and there (art/structures/props/snow). Each in a cell of its
# own on a street's edge, drawn in the town's drawing (town_design.py
# dressing); none where another thing stands. (kind, x, y) ----
DRESS, _taken = [], set(PINES) | set(LANTERNS) | set(ENTRY_PINES) | YARD


def dress(kind, x, y):
    if (x, y) in _taken or (x, y) not in ROAD or (x, y - 1) in _taken:
        return
    _taken.update({(x, y), (x, y - 1)})
    DRESS.append((kind, x, y))


for t in (4, 5):                                     # the main street's runs between the streets across
    y0, y1 = BLOCK(t)
    for y in (y0 + 1, y1 - 2):
        dress('post_w', MAIN - y, y)                 # its west edge
        dress('post_e', MAIN + 2 - y, y)             # its east
for s_ in STREETS[2:]:                               # a post at each crossing, on the street across
    dress('post_w', MAIN - 1 - s_, s_)
for kb in SQ_BACK + [MAIN]:                          # and along the square's three roads, open to the sky
    for y in (r0 + 1, r1 - 2):
        dress('post_w', kb - y, y)
        dress('post_e', kb + 2 - y, y)
# (town_design.py leaves out any post whose lantern would share a cell with a
# roof past the cell's four colours: the main street's eaves take most of its own)
lot_of = {i: (n, o) for n, i, o in DRAWN}
for j, (name, k0, k1, y0, y1) in enumerate(LOTS):    # firewood before every third house, at its west end
    if j in lot_of and lot_of[j][0] in ('shophouse', 'courtyard') and j % 3 == 0:
        dress('firewood', k0 + 1 - y1, y1 + 1)
for name, near in (('inn', lambda k0, k1: k0 + 5), ('book shop', lambda k0, k1: k1 - 6)):
    for _, k0, k1, y0, y1 in [l for l in LOTS if l[0] == name]:
        dress('cart', near(k0, k1) - y1, y1 + 1)
shops = [(j, l) for j, l in enumerate(LOTS) if j in lot_of and lot_of[j][0] == 'shophouse']
for j, (_, k0, k1, y0, y1) in shops[1::7]:           # a cart by two shops, crates by others
    dress('cart', k1 - 2 - y1, y1 + 1)
for j, (_, k0, k1, y0, y1) in shops[3::5]:
    dress('crate', k1 - 1 - y1, y1 + 1)
for _, k0, k1, y0, y1 in [l for l in LOTS if l[0] == 'inn']:
    dress('sled', k0 + 8 - y1, y1 + 1)
for j, (_, k0, k1, y0, y1) in [(j, l) for j, l in enumerate(LOTS) if j in lot_of and j % 3 == 0][1::3]:
    dress('snowy_log', k0 + 3 - y1, y1 + 1)          # by some of the firewood
for k0, k1, side in YARDS[::3]:                      # a snowman in two of the square's yards
    x, y = (k0 + k1) // 2 + 1 - (r1 - 1), r1 - 1
    if (x, y) not in _taken and (x, y - 1) not in _taken and (x, y) not in ROAD:
        _taken.update({(x, y), (x, y - 1)})
        DRESS.append(('snowman', x, y))
XUELIN_AT = ow.XUELIN_AT['town']
json.dump({'canvas': CANVAS, 'lots': LOTS, 'drawn': DRAWN, 'dress': DRESS, 'walls': [KW, KE, BACK, FRONT], 'margin': MARGIN, 'main': MAIN,
           'square': {'halves': HALVES, 'rows': SQUARE[2:], 'pines': PINES, 'lanterns': LANTERNS,
                      'yard': sorted(YARD)}, 'entry_pines': ENTRY_PINES,
           'gate_y': GATE_Y}, open(os.path.join(ROOT, 'art', 'structures', 'xuelin', 'layout.json'), 'w'), indent=1)

for y in range(N):                                   # the wall is drawn: the ground under it the town's
    for x in range(N):
        if g[y][x] == WALL:
            g[y][x] = SNOW
for name, lot, _ in DRAWN:                           # a built lot: the town's ground all over it
    _, k0, k1, y0, y1 = LOTS[lot]
    for y in range(y0, y1 + 1):
        for k in range(k0, k1 + 1):
            g[y][k - y] = SNOW
ART = {}                                             # (x, y) -> sheet cell + 6
town_png = os.path.join(ROOT, 'art', 'structures', 'xuelin', 'town.png')
fresh = os.path.exists(town_png) and Image.open(town_png).size == (CANVAS[2] * 16, CANVAS[3] * 16)
assert fresh or '--write' not in sys.argv, 'town.png is not CANVAS: run town_design.py'
if fresh:                                            # (a plan that moved waits for town_design.py)
    tim = Image.open(town_png).convert('RGBA')
    for j in range(CANVAS[3]):
        for i in range(CANVAS[2]):
            if tim.crop((i * 16, j * 16, i * 16 + 16, j * 16 + 16)).getchannel('A').getbbox():
                x, y = CANVAS[0] + i, CANVAS[1] + j
                assert (x, y) not in YARD or '--write' not in sys.argv, 'the drawing covers a yard wall at (%d,%d)' % (x, y)
                ART[(x, y)] = XUELIN_AT[0] + i + (XUELIN_AT[1] + j) * 256 + 6
                if g[y][x] == BLANK:
                    g[y][x] = SNOW                   # its own ground under it, not the placeholder

# ---- outside the apron the cleared ground keeps its own country (0): its
# trees and ground as they lie, its hills taken away (stamp_town_blueprint) ----

# ---- the road cells must join ----
sheet = Image.open(ROOT + '/assets/tileset.png').convert('RGBA')
spx = sheet.load()


def seams():
    vals = {g[y][x] for x, y in ROAD}
    FILL = (215, 161, 117)
    def at(v, i, j):
        if v not in vals:
            return None
        p = spx[((v - 6) % 256) * 16 + i, ((v - 6) // 256) * 16 + j][:3]
        return None if p == (255, 0, 0) else p
    bad = []
    for x, y in sorted(ROAD):
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            a, b = g[y][x], g[y + dy][x + dx]
            edge = lambda v, far: [at(v, (15 if far else 0) if dx else i, i if dx else (15 if far else 0)) for i in range(16)]
            n = sum(m == FILL and t is None for m, t in zip(edge(a, dx + dy > 0), edge(b, dx + dy < 0)))
            if n and (x + dx, y + dy) not in BUILT:     # a path's end under a door, as town_0's
                bad.append((x, y, dx, dy, n))
    return bad


bad = seams()
print('xuelin: wall %d across x %d deep, %d road cells, %d lots, %d seams that do not meet' % (
    KE - KW - 1, FRONT + 2 - BACK, len(ROAD), len(LOTS), len(bad)), bad[:12])

# ---- preview ----
COL = {'house': (190, 120, 80), 'shrine': (200, 60, 60), 'elder': (160, 80, 160), 'drum tower': (230, 40, 40),
       'inn': (240, 180, 40), 'book shop': (60, 120, 220)}
lot_at = {}
for i, (name, k0, k1, y0, y1) in enumerate(LOTS):
    for y in range(y0, y1 + 1):
        for k in range(k0, k1 + 1):
            lot_at[(k - y, y)] = (name, i)
T = 16
im = Image.new('RGBA', (N * T, N * T), (150, 170, 190, 255))
for y in range(N):
    for x in range(N):
        v, at = g[y][x], (x * T, y * T, x * T + T, y * T + T)
        if (x, y) in lot_at:
            name, i = lot_at[(x, y)]
            c = COL[name]
            if name == 'house' and i % 2:
                c = tuple(int(v * .8) for v in c)                # neighbours told apart
            im.paste(c + (255,), at)
        elif v == SNOW:
            im.paste((245, 245, 250, 255), at)
        elif v == PATH:
            im.paste((200, 190, 170, 255), at)
        elif v == WALL:
            im.paste((90, 90, 100, 255), at)
        elif v == TREE:
            im.paste((245, 245, 250, 255), at); im.paste((30, 90, 60, 255), (at[0] + 4, at[1] + 2, at[0] + 12, at[1] + 14))
        elif v >= 6:
            c, r = (v - 6) % 256, (v - 6) // 256
            t = sheet.crop((c * T, r * T, c * T + T, r * T + T))
            t.putdata([(245, 245, 250, 255) if p[:3] == (255, 0, 0) else p for p in t.get_flattened_data()])
            im.paste(t, at[:2])
for (x, y), v in ART.items():
    c, r = (v - 6) % 256, (v - 6) // 256
    t = sheet.crop((c * T, r * T, c * T + T, r * T + T))
    t.putdata([(0, 0, 0, 0) if p[:3] == (255, 0, 0) else p for p in t.get_flattened_data()])
    im.alpha_composite(t, (x * T, y * T))
crop = im.crop((BOX[0] * T - 2 * T, BOX[1] * T - 2 * T, BOX[2] * T + 2 * T, BOX[3] * T + 2 * T))
crop.convert('RGB').save(OUT)
crop.convert('RGB').resize((crop.width // 4, crop.height // 4), Image.NEAREST).save(OUT.replace('.png', '_small.png'))
json.dump({'lots': LOTS, 'square': SQUARE, 'main': MAIN, 'lanes': [LANE_W, LANE_E], 'wall': [KW, KE, BACK, FRONT],
           'streets': STREETS, 'gate_y': GATE_Y, 'box': BOX}, open(OUT.replace('.png', '.json'), 'w'), indent=1)
print('preview', OUT)

# the lantern posts' other frames (town_design.py anim_design, town_anim.json):
# (the cell laid in the overlay, frame 0's -- 0 where the lantern only swings
# into it later -- frame 1's, frame 2's, the post's phase)
ANIM = []
anim_json = os.path.join(ROOT, 'art', 'structures', 'xuelin', 'town_anim.json')
if fresh and os.path.exists(anim_json):
    col, row = ow.XUELIN_AT['town_anim']
    assert row == XUELIN_AT[1] + CANVAS[3], 'XUELIN_AT town_anim is not under the town'
    for i, a in enumerate(json.load(open(anim_json))):
        x, y = CANVAS[0] + a['cell'][0], CANVAS[1] + a['cell'][1]
        f1, f2 = col + i + row * 256 + 6, col + i + (row + 1) * 256 + 6
        px, py = a['post']
        if (x, y) in ART:
            ANIM.append((ART[(x, y)], ART[(x, y)], f1, f2, (px * 7 + py * 13) % 3))
        else:                                        # empty at frame 0: laid as its frame 1, shown at 1 and 2
            ART[(x, y)] = f1
            ANIM.append((f1, 0, f1, f2, (px * 7 + py * 13) % 3))
            if g[y][x] == BLANK:
                g[y][x] = SNOW

if '--write' in sys.argv:
    assert not bad
    p = ROOT + '/include/towns.h'
    s = open(p, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in s else '\n'
    body = 'static const int town_2[%d][%d] = {%s' % (N, N, nl) + ''.join(
        '    {' + ','.join(map(str, r)) + '},' + nl for r in g) + '};' + nl
    body += nl.join([
        '// Xuelin\'s extents in its footprint, from tools/town2_layout.py. Its own',
        '// ground is the cleared ground, [BOX_X0, BOX_X1) x [BOX_Y0, BOX_Y1): the',
        '// country round it is left as it lies (town_box in src/tilemap.cpp), and',
        '// placement asks it to be free of water, river and highland that is no',
        '// island. The walls stand in [WALL_X0, WALL_X1) x [WALL_Y0, WALL_Y1), which',
        '// placement asks to be snow. The street outside the gate: its top row, and',
        '// the x of its west and east caps, which give way to street out to the',
        '// cleared ground\'s edge where the road comes in (town_gate).',
        '#define XUELIN_BOX_X0 %d' % BOX[0], '#define XUELIN_BOX_Y0 %d' % BOX[1],
        '#define XUELIN_BOX_X1 %d' % BOX[2], '#define XUELIN_BOX_Y1 %d' % BOX[3],
        '#define XUELIN_WALL_X0 %d' % WALL_BOX[0], '#define XUELIN_WALL_Y0 %d' % WALL_BOX[1],
        '#define XUELIN_WALL_X1 %d' % WALL_BOX[2], '#define XUELIN_WALL_Y1 %d' % WALL_BOX[3],
        '// The walls themselves: the side walls\' x + y (west k..k+1, east k-1..k)',
        '// and the back and front walls\' top rows (each two thick).',
        '#define XUELIN_KW %d' % KW, '#define XUELIN_KE %d' % KE,
        '#define XUELIN_BACK %d' % BACK, '#define XUELIN_FRONT %d' % FRONT,
        '#define XUELIN_MAIN_Y %d' % GATE_Y, '#define XUELIN_MAIN_W %d' % MAIN_X[0], '#define XUELIN_MAIN_E %d' % MAIN_X[1],
        '// Its buildings\' art, the overlay over the ground above: x, y in the',
        '// footprint and the sheet cell plus 6, as a blueprint names one.',
        'static const int XUELIN_ART[][3] = {'] + [
        '    {%d, %d, %d},' % (x, y, v) for (x, y), v in sorted(ART.items(), key=lambda a: (a[0][1], a[0][0]))] + [
        '};',
        '// Its lantern posts swaying (town_design.py anim): a cell of the art above',
        '// as laid in the overlay, as its sheet cell plus 6; the cell at frames 0, 1',
        '// and 2 (0: nothing then -- the lantern swings into it only later); and the',
        '// phase of its post, in whole frames -- played on the ambient beat (core.h).',
        'static const int XUELIN_ANIM[][5] = {'] + [
        '    {%d, %d, %d, %d, %d},' % a for a in ANIM] + [
        '};',
        '// end of town 2'])
    m = re.search(r'static const int town_2\[[^\]]*\]\[[^\]]*\] = \{.*?\};(\s*// (The street outside|Xuelin\'s extents).*?// end of town 2)?', s, re.S)
    open(p, 'w', encoding='utf-8', newline='').write(s[:m.start()] + body + s[m.end():])
    print('wrote town_2 to', p)
