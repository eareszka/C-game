"""The plains' props: a farm country, and round each pyramid the ruins of the people who built it.

    python art/structures/props/plains/plains_design.py            # every prop
    python art/structures/props/plains/plains_design.py stele      # one

Each writes art/structures/props/plains/<name>.png. The list was approved by the
user on 2026-10-26 ("plains should be farming theme in some parts and
mesoamerican in others due to the pyramid"): nine farm things, nine
Mesoamerican. PixelLab drafts under pixellab-out/plains-*/ gave the designs.

The Mesoamerican pieces are the step pyramid's own stone (entrances/
pyramid_design.py step_pyramid: the ruins' grey, laid in its courses -- the
pyramid off the desert is Chichen Itza's, not the desert's sandstone), so they
read as fallen from it. Built things are in the houses' projection (Scene);
sculptures and small things are objects typed by hand. Objects keep three
colours and black; the tall grass is ground cover, drawn by the tuft ruling.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
sys.path.insert(0, os.path.join(HERE, '..', 'forest'))
from entrance_shapes import Scene, four_per_cell, rect, fill
from forest_design import blank, outline, typed, stroke, ellipse, write
from prop_paint import voxels

# tools/overworld_style.py MATERIALS
WOOD = ('967448', '785830', '493712')
STONE = ('c6ccda', '9797aa', '595965')
FOLIAGE = ('05c43a', '058f3a', '235436')
THATCH = ('c9a433', '876a1f')
RED = ('b70000', '7c0a1b')
WATER = '5c94fc'
GRASS_TUFT = '00881b'
BRICK = ('b6433d', '792727', '5d1e1f')
WHITE = 'fcfcfc'
WOOD_PAL = {'L': WOOD[0], 'M': WOOD[1], 'D': WOOD[2]}
STONE_PAL = {'L': STONE[0], 'M': STONE[1], 'D': STONE[2]}


def scene_grid(sc):
    g = sc.render()
    w = g.w
    assert all(c == '.' for c in g.g[0] + [r[0] for r in g.g] + [r[w - 1] for r in g.g]), 'drawn at the edge'
    return g.g


# ================================================================ farming
def round_bale(W, H, R, depth, fx, fy, rings):
    """A round bale lying on its side: its face square on, the straw rolled round in rings;
    its length running back up and to the right in the houses' projection, its top lit and
    its far side in shade. Lit straw and its shade."""
    g = blank(W, H)
    for k in range(depth, 0, -1):                                 # the body, back to front
        cx, cy = fx + k, fy - k
        for y in range(H):
            for x in range(W):
                if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= R:
                    g[y][x] = 'L' if (y + 0.5 - cy) < -R * 0.35 and (x + 0.5 - cx) < R * 0.6 else 'D'
    for y in range(H):                                            # the face
        for x in range(W):
            r = math.hypot(x + 0.5 - fx, y + 0.5 - fy)
            if r <= R:
                rolled = any(abs(r - q) < 0.45 for q in rings) or r < 0.8
                g[y][x] = 'D' if rolled or r > R - 0.7 and (x + 0.5 - fx) + (y + 0.5 - fy) > 2 else 'L'
    return outline(g), {'L': THATCH[0], 'D': THATCH[1]}


def hay_bale():
    """A square bale, built: its top lit straw, its front the straw in rows, its side in shade,
    two bands of twine round it (the user, 2026-10-26: the small one a cube)."""
    sc = Scene(16, 16, 13)
    sc.box(0, 3, 10, 0, 3, 0, 7, front='M')
    g = scene_grid(sc)
    for y in range(16):
        for x in range(16):
            if g[y][x] == 'M' and (y % 2 == 0 and (x + y // 2) % 3 == 0):
                g[y][x] = 'D'                                     # straw ends in its face
            if g[y][x] in 'ML' and x in (5, 9):
                g[y][x] = 'D'                                     # the twine
    g = [[{'L': 'L', 'M': 'L', 'D': 'D'}.get(c, c) for c in row] for row in g]
    return g, {'L': THATCH[0], 'D': THATCH[1]}


def haystack():
    """The big one: a round bale lying on its side, two cells square (the user, 2026-10-26:
    "the larger one" should be a cylinder)."""
    return round_bale(32, 32, 8.6, 6, 12.0, 20.5, (2.6, 5.4))


def scarecrow():
    g = typed([
        "................",
        "................",
        "................",
        "......DDDD......",
        ".....DDDDDD.....",
        "...DDDDDDDDDD...",
        "......tttt......",
        "......tKtK......",
        "......tttt......",
        "......tDDt......",
        ".......DD.......",
        "....rrrrrrrr....",
        "..trrrrrrrrrrt..",
        "..t.rrrrrrrr.t..",
        ".....rrrrrr.....",
        ".....rrKrrr.....",
        ".....rrrrrr.....",
        ".....rrrrKr.....",
        ".....tt.tt.t....",
        "....t...t...t...",
        ".......DD.......",
        ".......DD.......",
        ".......DD.......",
        ".......DD.......",
        ".......DD.......",
        ".......DD.......",
        ".......DD.......",
        ".......DD.......",
        "......DDDD......",
        "................",
        "................",
        "................"])
    return outline(g), {'t': THATCH[0], 'D': THATCH[1], 'r': RED[0]}


def wheel(cx, cy, r):
    def draw(t):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                dx, dy = x - cx, y - cy
                rr = math.hypot(dx, dy)
                if rr <= r:
                    t.put(x, y, 'L' if rr < 1.0 else 'M' if rr > r - 1.2 or dx == 0 or dy == 0 else 'D')
    return draw


def handcart():
    sc = Scene(32, 16, 13)
    sc.box(0, 9, 24, 0, 4, 4, 7, front='M')                      # the bed
    sc.flat(1, wheel(17, 10.5, 3.3), -1)
    sc.flat(2, lambda t: fill(t, rect(2, 9, 9, 10), 'M') or fill(t, rect(2, 9, 9, 9), 'L'), -0.5)   # handles, down to the ground
    sc.flat(3, lambda t: fill(t, rect(2, 11, 3, 13), 'D'), -0.4)
    g = scene_grid(sc)
    return g, WOOD_PAL


def wheelbarrow():
    sc = Scene(32, 16, 13)
    sc.box(0, 9, 21, 0, 3, 3, 7, front='M')                      # the tray, deep
    sc.flat(1, wheel(24, 9.5, 3.4), -1)
    sc.flat(2, lambda t: fill(t, rect(2, 6, 9, 7), 'M') or fill(t, rect(2, 6, 9, 6), 'L'), -0.5)    # handles, held up
    sc.flat(3, lambda t: fill(t, rect(11, 9, 11, 13), 'D') or fill(t, rect(18, 9, 18, 13), 'D'), -0.4)  # legs
    return scene_grid(sc), WOOD_PAL


def barrel():
    sc = Scene(16, 16, 13)
    sc.box(0, 4, 10, 0, 2, 0, 8, front='M')
    g = scene_grid(sc)
    for y in range(16):
        for x in range(16):
            if g[y][x] in 'MD' and y in (7, 11):
                g[y][x] = 'K'                                     # the iron hoops
            elif g[y][x] == 'M' and x == 4:
                g[y][x] = 'L'                                     # its staves lit down the left
    return g, WOOD_PAL


def trough():
    sc = Scene(32, 16, 13)
    sc.box(0, 3, 22, 0, 4, 0, 5, front='M')
    g = scene_grid(sc)
    top = {(x, y) for y in range(16) for x in range(32) if sc.pid[y][x] == 0 and g[y][x] == 'L'}
    for x, y in top:                                              # water within its rim
        if all((x + dx, y + dy) in top for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            g[y][x] = 'w'
    for y in range(16):
        for x in range(32):
            if g[y][x] == 'M' and y == 11:
                g[y][x] = 'D'                                     # the seam between its boards
    class G: pass
    gg = G(); gg.g, gg.w, gg.h = g, 32, 16
    four_per_cell(gg, [('L', 'M')])
    return g, dict(WOOD_PAL, w=WATER)


def field_gate():
    sc = Scene(32, 32, 29)
    sc.box(0, 3, 5, 0, 2, 0, 15, front='M')                      # the posts, the yard fence's stout post
    sc.box(1, 25, 27, 0, 2, 0, 15, front='M')
    for z in (3, 8, 12):                                          # the gate's rails
        sc.box(2, 6, 24, 0, 0, z, z + 1, front='M')
    for x in (6, 24):
        sc.box(2, x, x, 0, 0, 3, 13, front='M')                  # its stiles
    for i in range(17):                                           # the brace, foot of one stile to the head of the other
        sc.box(3, 7 + i, 7 + i, 0, 0, 4 + int(i * 8 / 16), 5 + int(i * 8 / 16), front='M')
    g = scene_grid(sc)
    return g, WOOD_PAL


def tall_grass():
    """Two tufts of long grass, drawn as the ground draws a tuft: blades a pixel wide, no line,
    a dot of shadow under the root. The grass cells' own tuft green over the foliage's dark."""
    sets = [[
        "................",
        "................",
        "....g.....g.....",
        "....g..g..g.....",
        ".....g.g.g...g..",
        ".g...g.g.g..g...",
        "..g..g.gg..g....",
        "..g..ggdg.g.....",
        "...g.gddgg......",
        "...ggdgdgd......",
        "....gddgdd......",
        ".....ddddd......",
        "......ddd.......",
        ".......K........",
        "................",
        "................"], [
        "................",
        "................",
        "................",
        "................",
        "................",
        ".......g........",
        "...g...g..g.....",
        "....g..g.g..g...",
        "....g.gg.g.g....",
        ".....ggdgdg.....",
        ".....gddgdd.....",
        "......dddd......",
        "......ddd.......",
        "........K.......",
        "................",
        "................"]]
    rows = [[] for _ in range(16)]
    for s in sets:
        for y in range(16):
            rows[y] += list(s[y])
    return rows, {'g': GRASS_TUFT, 'd': FOLIAGE[2]}


# ================================================================ Mesoamerican
def solid_grid(W, H, base, cells, tone=None, pieces=None, carve=()):
    """A statue as a solid in the houses' projection (tools/prop_paint.py voxels): tops lit, south
    faces mid, east faces dark; returned as rows, kept off the canvas's top and sides.

    carve: (x, z, tone) cut into the front face, laid on the screen after the render -- a cell's
    face is sampled at points that spill a pixel into its neighbour's, so carving a pixel or two
    wide through tone() is painted over and then cleaned away as a speck (as the slab's cracks
    were). On the front (d = 0), cell (x, z) shows at screen (x, base - z - 1)."""
    g = voxels(W, H, base, cells, tone, pieces).g
    for x, z, c in carve:
        y = base - z - 1
        if 0 <= y < H and g[y][x] not in '.K':
            g[y][x] = c
    assert all(c == '.' for c in g[0] + [r[0] for r in g] + [r[W - 1] for r in g]), 'drawn at the edge'
    return g


def courses_tone(x, z, x0=0):
    """The step pyramid's courses on a south face: a bed every 4 rows, joints 6 apart, offset."""
    return 'D' if z % 4 == 3 or (x - x0 + (z // 4) % 2 * 3) % 6 == 0 else None


def maize():
    g = blank(32, 32)
    stalks = [(8, 9), (13, 5), (18, 7), (23, 10)]                 # x, top
    for sx, top in stalks:
        for y in range(top, 30):
            g[y][sx] = 'g'
            g[y][sx + 1] = 'G'
        for k, (dy, side) in enumerate(((6, -1), (10, 1), (14, -1), (18, 1))):   # leaves arching off
            y0 = top + dy
            if y0 >= 27:
                continue
            pts = [(sx + 0.5 + side * 0.5, y0, 1.6), (sx + 0.5 + side * 3, y0 - 2.5, 1.2), (sx + 0.5 + side * 4.5, y0 + 1, 0.9)]
            stroke(g, pts, 'g', lambda x, y, t, s: 'G' if s > 0.2 else 'g')
        for y in range(top - 3, top):                             # the tassel
            g[y][sx] = 't'
        g[top - 2][sx - 1] = g[top - 2][sx + 1] = 't'
        cy = top + 11                                             # a cob, husk opening
        for y in range(cy, cy + 3):
            g[y][sx + 2] = 't'
        g[cy - 1][sx + 2] = 'g'
    return outline(g), {'g': FOLIAGE[1], 'G': FOLIAGE[2], 't': THATCH[0]}


def stele():
    """A carved slab, built: its face in two columns of glyph blocks cut in the stone's shade."""
    sc = Scene(16, 32, 29)
    sc.box(0, 3, 10, 0, 2, 0, 22, front='M')
    g = scene_grid(sc)
    face = [(x, y) for y in range(32) for x in range(16) if sc.pid[y][x] == 0 and g[y][x] == 'M']
    xs = [x for x, y in face]; ys = [y for x, y in face]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for y in range(y0 + 1, y1 - 1):
        for x in range(x0 + 1, x1):
            gy, gx = (y - y0 - 1) % 5, (x - x0 - 1) % 4
            if gy == 4 or gx == 3:
                g[y][x] = 'D'                                     # the grid the glyphs sit in
            elif (gy, gx) in ((1, 1), (2, 1), (2, 0)) and (y // 5 + x // 4) % 2 == 0:
                g[y][x] = 'D'                                     # a mark in a glyph
            elif (gy, gx) in ((1, 0), (1, 2), (2, 2)) and (y // 5 + x // 4) % 2 == 1:
                g[y][x] = 'D'
    return g, STONE_PAL


def serpent_head():
    """Kukulcan's head as the pyramid's stair ends in, a solid lying on the ground facing left
    (the user, 2026-10-26: oblique): its jaws open as a real gap through it, fangs hanging into
    it, a brow over the eye, the scroll of its nose, a crest of feathers standing along its top."""
    cells = set()
    for x in range(2, 24):
        snout = x < 12
        top = 6 if x >= 10 else 5
        for z in range(0, top + 1):
            if snout and z in (2, 3):
                continue                                          # the open mouth
            for d in range(0, 4):
                cells.add((x, d, z))
    for x in (4, 8):                                              # two fangs hanging into it
        cells.add((x, 0, 3))
    for x in (13, 14, 16, 17, 19, 20, 22, 23):                    # the feather crest along its top, feathers two wide
        for d in range(0, 4):
            cells.add((x, d, 7))
    carve = [(x, z, 'K') for x in range(3, 12) for z in (2, 3) if x not in (4, 8) or z == 2]   # the mouth
    carve += [(16, 4, 'K'), (17, 4, 'K')]                                                  # the eye
    carve += [(x, 5, 'D') for x in range(15, 19)] + [(5, 4, 'D'), (6, 4, 'D'), (6, 5, 'D'), (7, 5, 'D')]   # brow, nose scroll
    notch = lambda x, d, z, face: 'K' if face == 'east' and z == 7 else None   # a line between feathers
    return solid_grid(32, 16, 14, cells, notch, None, carve), STONE_PAL

def jaguar():
    """A jaguar sitting on a plinth, both solids (the user, 2026-10-26: oblique): the plinth in the
    pyramid's courses, the cat facing left -- haunch, chest, head, ears, the tail curled at its
    side -- its eye and the line of its foreleg cut in its south face."""
    cells, part = set(), {}
    def add(x0, x1, z0, z1, d0, d1, pid):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                for d in range(d0, d1 + 1):
                    cells.add((x, d, z)); part[(x, d, z)] = pid
    add(2, 9, 0, 4, 0, 2, 0)                                      # the plinth
    add(6, 9, 5, 11, 0, 2, 1)                                     # the haunch
    add(4, 7, 5, 15, 0, 2, 1)                                     # the chest and forelegs
    add(3, 7, 16, 19, 0, 2, 1)                                    # the head
    add(3, 4, 20, 22, 2, 2, 1); add(6, 7, 20, 22, 2, 2, 1)       # the ears, at the back, a gap between them
    add(2, 2, 16, 17, 0, 2, 1)                                    # the muzzle
    add(9, 9, 5, 8, 2, 2, 1)                                      # the tail, curled up its side
    def tone(x, d, z, face):
        return courses_tone(x, z) if face == 'south' and part[(x, d, z)] == 0 else None
    carve = [(3, 18, 'K'), (4, 18, 'K')] + [(5, z, 'D') for z in range(5, 12)]   # the eye, the foreleg
    return solid_grid(16, 32, 29, cells, tone, lambda x, d, z: part[(x, d, z)], carve), STONE_PAL

def altar():
    sc = Scene(32, 16, 13)
    sc.box(0, 4, 22, 0, 4, 0, 7, front='courses')
    g = scene_grid(sc)
    top = [(x, y) for y in range(16) for x in range(32) if sc.pid[y][x] == 0 and g[y][x] == 'L']
    cx = sum(x for x, y in top) / len(top); cy = sum(y for x, y in top) / len(top)
    bowl = ellipse(cx, cy - 0.5, 3.5, 1.6)
    for y in range(16):
        for x in range(32):
            if bowl(x, y):
                g[y][x] = 'K' if ellipse(cx, cy - 0.7, 2.2, 0.9)(x, y) else 'D'   # the offering bowl, dark within
    return g, STONE_PAL


def ball_ring():
    """A stub of the ball court's wall in the pyramid's courses, and its stone ring standing on it
    -- a solid ring three deep (the user, 2026-10-26: "oblique projected including the ring"):
    its face and top lit and mid by plane, its bore and east side in shade, the sand through it."""
    cells, part = set(), {}
    for x in range(3, 22):
        for d in range(0, 4):
            for z in range(0, 9):
                cells.add((x, d, z)); part[(x, d, z)] = 0
    cx, cz, R, r = 11.5, 15.5, 6.6, 3.0
    for x in range(3, 22):
        for z in range(9, 23):
            if r <= math.hypot(x + 0.5 - cx, z + 0.5 - cz) <= R:
                for d in range(1, 4):
                    cells.add((x, d, z)); part[(x, d, z)] = 1
    def tone(x, d, z, face):
        if part[(x, d, z)] == 0 and face == 'south':
            return courses_tone(x, z)
        return None
    return solid_grid(32, 32, 29, cells, tone, lambda x, d, z: part[(x, d, z)]), STONE_PAL


def clay_pots():
    """Two painted pots, a tall one and a squat one: lip, neck, a band of white round the
    shoulder, the right side in the clay's shade."""
    g = typed([
        "................",
        "................",
        "................",
        "................",
        ".....rrR........",
        "......rR........",
        "....rrrrRR......",
        "...rwwwwwRR.rR..",
        "...rrrrrrrR.rR..",
        "...rwrwrwrR.rwR.",
        "...rrrrrrrR.rrR.",
        "....rrrrrR..rRR.",
        ".....RRRR...RR..",
        "................",
        "................",
        "................"])
    return outline(g), {'r': BRICK[0], 'R': BRICK[1], 'w': WHITE}


def fallen_block():
    sc = Scene(32, 16, 13)
    sc.box(0, 4, 22, 0, 5, 0, 6, front='M')
    sc.break_off([0], 18, 30, 4, 1, 3)
    g = scene_grid(sc)
    for y in range(16):
        for x in range(32):
            if sc.pid[y][x] == 0 and g[y][x] == 'M':
                gy, gx = (y - 7) % 5, (x - 5) % 4
                if gx == 3 or (gy, gx) in ((1, 1), (2, 1), (2, 0)) and x % 8 < 4:
                    g[y][x] = 'D'                                 # its glyphs, as the stele's
    return g, STONE_PAL


def chacmool():
    """The reclining figure on its slab, solids (the user, 2026-10-26: oblique): head raised at the
    left, the torso propped back, knees drawn up at the right, and on its belly the offering
    bowl, a short drum dark within."""
    cells, part = set(), {}
    def put(x, d, z, pid):
        cells.add((x, d, z)); part[(x, d, z)] = pid
    for x in range(2, 24):
        for d in range(0, 4):
            for z in range(0, 2):
                put(x, d, z, 0)                                   # the slab
    for x in range(3, 23):
        for d in range(1, 4):
            if x <= 6:
                top = 7                                           # the head, raised
            elif x >= 17:
                top = int(7 - abs(x - 19.5) * 1.5)                # the knees, drawn up
            else:
                top = 4                                           # the torso
            for z in range(2, max(3, top) + 1):
                put(x, d, z, 1)
    for x in range(10, 15):                                       # the bowl on its belly
        for d in range(1, 4):
            for z in (5, 6):
                put(x, d, z, 2)
    def tone(x, d, z, face):
        if part[(x, d, z)] == 2 and face == 'top' and 11 <= x <= 13 and d == 2:
            return 'K'                                            # inside the bowl
        return None
    carve = [(4, 5, 'K'), (6, 5, 'K'), (5, 3, 'D')]                # its eyes, its mouth
    return solid_grid(32, 16, 14, cells, tone, lambda x, d, z: part[(x, d, z)], carve), STONE_PAL


PROPS = [
    ('hay_bale', hay_bale), ('haystack', haystack), ('scarecrow', scarecrow), ('handcart', handcart),
    ('wheelbarrow', wheelbarrow), ('barrel', barrel), ('trough', trough), ('field_gate', field_gate),
    ('tall_grass', tall_grass),
    ('maize', maize), ('stele', stele), ('serpent_head', serpent_head), ('jaguar', jaguar),
    ('altar', altar), ('ball_ring', ball_ring), ('clay_pots', clay_pots), ('fallen_block', fallen_block),
    ('chacmool', chacmool),
]

if __name__ == '__main__':
    want = sys.argv[1:]
    for name, make in PROPS:
        if want and name not in want:
            continue
        try:
            g, pal = make()
        except AssertionError as e:
            print(name, 'FAILED:', e)
            continue
        write(g, pal, os.path.join(HERE, name + '.png'))
        print(name)
