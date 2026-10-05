"""The walls round a graveyard's yard, laid out for tools/draw_views.py.

    python art/structures/entrances/yard_walls_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/yard_walls

Two strips of sixteen pieces, 16 wide and two cells tall: a wooden fence (the
large graveyard's) and a wall of stone brick (the catacombs'). The yard is a
parallelogram in the houses' oblique projection -- its front and back walls
run across, its sides run back and up to the right at 45 degrees, one cell up
for every cell across -- so each wall cell is a post with up to four arms:
across to the left and right, and back along the side, down-left toward the
viewer and up-right away. Piece n has arm W if n & 1, E if n & 2, SW if n & 4,
NE if n & 8; the game picks it from which neighbours are wall (draw_yard_wall
in src/tilemap.cpp). A side arm stands taller than its cell is high, so every
piece is two cells: the bottom one drawn on the wall's cell, the top one over
the cell above in the depth pass, the player walking behind it as behind a
tree's crown.

Each piece is cut from one continuous wall drawn through its cell, so pieces
meet without a seam; check_tiling() lays a small yard of pieces and compares
it with the same yard drawn whole.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Scene, Grid, depth_layers

PAL = {'K': '000000',
       'D': '463422', 'M': '8d6b4f', 'L': 'b2966a',          # weathered wood (the oak's bark)
       'd': '595965', 'm': '9797aa', 'l': 'c6ccda'}          # the ruins' stone
STONE = {'D': 'd', 'M': 'm', 'L': 'l'}
CELL, PIECES = 16, 16
P = 2                      # the post: this far into its cell across, at the cell's d = 0
GROUND = 12                # and the ground it stands on, this far down its cell
FAR = 400                  # a piece's arm runs this far, so its window never sees the end
W_, E_, SW_, NE_ = 1, 2, 4, 8


def wood(sc, x, d, arms, reach=None):
    """A rail fence: square posts every half cell, two rails nailed across
    their faces. The rails across are pid 1, the ones along the side pid 2, so
    a line parts them where one passes in front of the other. An arm runs
    `reach` (to the next post in a yard drawn whole, else far)."""
    R = reach or FAR
    def post(pid, px, pd):
        sc.box(pid, px - 1, px, pd - 1, pd, 0, 11, 'M')
    def rails_across(x0, x1):
        for z in (2, 7):
            sc.box(1, x0, x1, d - 2, d - 2, z, z + 1, 'M')
    def rails_back(d0, d1):
        for z in (2, 7):
            sc.box(2, x + 1, x + 1, d0, d1, z, z + 1, 'M')
    if arms in (W_ | E_, SW_ | NE_):
        post(1, x, d)
    else:                                       # a corner or an end: a stout post
        sc.box(3, x - 1, x + 1, d - 1, d + 1, 0, 13, 'M')
    if arms & W_:
        rails_across(x - R, x)
        for k in range(1, R // 8):
            post(1, x - 8 * k, d)
    if arms & E_:
        rails_across(x, x + R)
        for k in range(1, R // 8):
            post(1, x + 8 * k, d)
    if arms & SW_:
        rails_back(d - R, d)
        for k in range(1, R // 8):
            post(2, x, d - 8 * k)
    if arms & NE_:
        rails_back(d, d + R)
        for k in range(1, R // 8):
            post(2, x, d + 8 * k)


def stone(sc, x, d, arms, reach=None):
    """A wall of brick courses, three deep, its top lit; a pier where it turns
    or ends, kept inside its own cell."""
    R = reach or FAR
    def across(x0, x1):
        sc.box(1, x0, x1, d - 2, d, 0, 10, 'courses', block_w=8)
    def back(d0, d1):
        sc.box(2, x - 2, x, d0, d1, 0, 10, 'courses', block_w=8)
    if arms & W_:
        across(x - R, x)
    if arms & E_:
        across(x, x + R)
    if arms & SW_:
        back(d - R, d)
    if arms & NE_:
        back(d, d + R)
    if arms not in (W_ | E_, SW_ | NE_):
        sc.box(3, x - 1, x + 2, d - 1, d + 2, 0, 12, 'courses', block_w=8)


def scene(build, walls, w, h, base, reach=None):
    """walls: [(x, d, arms)] -- each a post and its arms, all in one picture."""
    sc = Scene(w, h, base)
    for x, d, arms in walls:
        build(sc, x, d, arms, reach)
    return sc.render()


# a piece is drawn in a canvas with its cell's window at WX.., WY.. (top cell)
WX, WY, CW, CH = 48, 48, 112, 112
BASE = WY + CELL + GROUND                      # the ground under the post, d = 0


def piece(build, arms, recolour={}):
    """The piece's window cut from its wall drawn whole, with the wall's ground
    rows and the ground it stands on cut the same way."""
    g = scene(build, [(WX + P, 0, arms)], CW, CH, BASE)
    p = Grid(CELL, 2 * CELL)
    p.g = [[recolour.get(c, c) for c in g.g[WY + y][WX:WX + CELL]] for y in range(2 * CELL)]
    p.footy = [[None if f is None else f - WY for f in g.footy[WY + y][WX:WX + CELL]] for y in range(2 * CELL)]
    p.foot = {(x - WX, y - WY) for x, y in g.foot if WX <= x < WX + CELL and WY <= y < WY + 2 * CELL}
    return p


def strip(build, recolour):
    return [piece(build, n, recolour) for n in range(PIECES)]


def rows(pieces):
    return [''.join(''.join(p.g[y]) for p in pieces) for y in range(2 * CELL)]


def arms_at(cells, cx, cy):
    has = lambda dx, dy: (cx + dx, cy + dy) in cells
    return has(-1, 0) * W_ | has(1, 0) * E_ | has(-1, 1) * SW_ | has(1, -1) * NE_


def yard(span, h, gate):
    """The wall cells of a yard as stamp_graveyard_yard lays them."""
    L, T = 0, 1
    B = T + h
    lx = lambda ty: L + (B - ty)
    cells = set()
    for tx in range(lx(T), lx(T) + span + 1):
        cells.add((tx, T))
    mid = (2 * L + span) // 2
    for tx in range(L, L + span + 1):
        if not (gate and tx in (mid, mid + 1)):
            cells.add((tx, B))
    for ty in range(T, B + 1):
        cells.add((lx(ty), ty)); cells.add((lx(ty) + span, ty))
    return cells, B


def check_tiling(build, view):
    """Lay a small yard of pieces the way the game does -- every bottom cell,
    then every top over the cell above -- and draw the same yard whole, each
    arm reaching the next post: (pixels inked in one and not the other,
    pixels of another tone, the two pictures)."""
    cells, B = yard(6, 3, True)
    gw, gh = 12 * CELL, (B + 2) * CELL
    # row cy stands CELL * (B - cy) back; its post lands at screen x cx*CELL + P
    whole = scene(build, [(cx * CELL + P - (B - cy) * CELL, (B - cy) * CELL, arms_at(cells, cx, cy))
                          for cx, cy in cells], gw, gh, B * CELL + GROUND, reach=CELL)
    laid = Grid(gw, gh)
    for half in (1, 0):                                      # bottoms, then tops
        for cx, cy in sorted(cells, key=lambda c: (c[1], c[0])):
            n = arms_at(cells, cx, cy)
            for y in range(half * CELL, (half + 1) * CELL):
                for x in range(CELL):
                    c = view[y][n * CELL + x]
                    if c != '.':
                        laid.put(cx * CELL + x, (cy - 1) * CELL + y, c)
    ink = sum(1 for y in range(gh) for x in range(gw) if (whole.g[y][x] == '.') != (laid.g[y][x] == '.'))
    tone = sum(1 for y in range(gh) for x in range(gw) if whole.g[y][x] != laid.g[y][x]) - ink
    return ink, tone, whole, laid


def design():
    fence, wall = strip(wood, {}), strip(stone, STONE)
    views = {'fence': rows(fence), 'wall': rows(wall)}
    for name, build in (('fence', wood), ('wall', stone)):
        ink, tone, *_ = check_tiling(build, [r.translate(str.maketrans('dml', 'DML')) for r in views[name]])
        print('%s: against the yard drawn whole, %d pixels inked differently, %d toned differently'
              % (name, ink, tone), file=sys.stderr)
    return {'pal': PAL, 'view_w': PIECES * CELL, 'order': ['fence', 'wall'], 'views': views,
            'depth': depth_layers(2 * PIECES * CELL, 2 * CELL,
                                  [(i * CELL, 0, p) for i, p in enumerate(fence + wall)])}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
