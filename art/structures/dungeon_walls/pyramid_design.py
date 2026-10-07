"""The pyramid's walls seen from inside: a tomb's sandstone, in the seven cells
every dungeon type's walls are built from (tools/dungeon_walls.py). Each face
carries a painted frieze of hieroglyphs across its middle cell, two glyphs to
a tile, a different pair in each of the three variants so a long wall reads
as writing rather than a stamp.

    python art/structures/dungeon_walls/pyramid_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/pyramid
    python art/structures/dungeon_walls/pyramid_design.py <design.json> maya
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/pyramid_maya

Sandstone is the pyramid entrance's (entrances/pyramid_design.py): K line,
D mortar, M lit sandstone, S shaded sandstone, laid as its stone() lays the
front face -- 4-row courses of 8-wide blocks, joints a half block along each
course. The glyphs are painted in the mortar brown.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from dungeon_walls import Grid, views, h32, sheet_rows
from entrance_shapes import Scene

PAL = {'K': '000000', 'D': '785830', 'M': 'f4ce80', 'S': 'b29e5c'}
# Anywhere but the desert the pyramid outside is a step pyramid in the ruins'
# grey stone (entrances/pyramid_design.py), and inside it is Mayan/Aztec: the
# same build, the same letters in their roles (D mortar and shade, M lit, S
# base), its own stone and its own carving -- corridor faces of stacked day-sign
# blocks and a crowded mural on every chamber's back wall (maya_murals.py).
VARIANTS = {
    'egypt': {'pal': PAL,
              'side': 'S'},
    'maya':  {'pal': {'K': '000000', 'D': '595965', 'M': 'c6ccda', 'S': '9797aa'},
              'bands': None,      # its walls: maya_murals.pattern, figures over it
              'side': 'D'},
}
# 'side': a chamber's slanted side walls are one flat darker tone (the user's
# rule) -- no texture, glyphs, figures or fret; only the floor's edge line.

# The frieze's hieroglyphs, solid carved bodies (D) with lit insides (M), 7 x
# 10. The black outline is cut round them by the pixel plugin's own outline
# tool when drawn (apply_outline, 1px), as the warriors and cryptids have
# theirs, so each comes out 9 x 12 in desert_hieroglyphs.png:
#     python pyramid_design.py --glyph-pixels <pixels.json>   -> draw_pixels on a
#     54 x 12 canvas, apply_outline #000000, save desert_hieroglyphs.aseprite + .png
GLYPHS = {
    'ankh': ["..DDD..",
             ".DMMMD.",
             ".DMMMD.",
             "..DMD..",
             "DDDDDDD",
             "DDDDDDD",
             "..DDD..",
             "..DDD..",
             "..DDD..",
             "..DDD.."],
    'eye': ["DDDDDD.",
            ".......",
            ".DDDDD.",
            "DMMDMMD",
            ".DDDDD.",
            "...DD..",
            "..DD.DD",
            ".DD..D.",
            ".......",
            "......."],
    'bird': ["..DD...",
             ".DMDD..",
             "DDDDD..",
             "..DDDD.",
             "..DDDDD",
             "..DDDD.",
             "...DDD.",
             "...D.D.",
             "..DD.DD",
             "......."],
    'water': [".DD..DD",
              "DDDDDD.",
              ".......",
              ".DD..DD",
              "DDDDDD.",
              ".......",
              ".DD..DD",
              "DDDDDD.",
              ".......",
              "......."],
    'feather': ["...DD..",
                "..DDDD.",
                "..DMMD.",
                "..DMMD.",
                "..DMMD.",
                "..DMMD.",
                "..DDDD.",
                "...DD..",
                "...D...",
                "...D..."],
    'sun': ["..DDD..",
            ".DMMMD.",
            "DMMMMMD",
            "DMMMMMD",
            ".DMMMD.",
            "..DDD..",
            ".DD.DD.",
            "DD...DD",
            ".......",
            "......."],
}
GLYPH_ORDER = list(GLYPHS)


def glyph_pixels():
    """The bodies for the plugin, laid side by side a 9-wide slot apiece with
    room for the outline."""
    return [{'x': i * 9 + 1 + x, 'y': y + 1, 'color': '#' + PAL[c]}
            for i, k in enumerate(GLYPH_ORDER) for y, row in enumerate(GLYPHS[k])
            for x, c in enumerate(row) if c != '.']


CART_W, CART_H = 36, 24        # a corridor's enemy glyph: a 32 x 20 cryptid in its cartouche
CART_Z = 12                     # its foot, above the face's floor line


def _cartouche(X, z):
    """The enemy glyph cartouche (X, z) lies in, one in every 96 columns of
    corridor in a half the hash picks: (tone or None, the cartouche's first
    column) -- the cryptids as hieroglyphs, hand-drawn through the plugin
    (desert_cryptids.png, maya_cryptids_design.py)."""
    Xp, k = X % 96, h32(X // 96, 3)
    x0 = (k & 1) * 48 + 6 + (k >> 4) % 7 - 3
    lx, lz = Xp - x0, CART_Z + CART_H - 1 - z
    if not (0 <= lx < CART_W and 0 <= lz < CART_H):
        return None
    if lx in (0, CART_W - 1) and lz in (0, CART_H - 1):
        return None                                # its rounded corners: the courses show
    if lx in (0, CART_W - 1) or lz in (0, CART_H - 1):
        return 'D', X - lx                         # its carved frame
    rows = sheet_rows(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'desert_cryptids.png'),
                      PAL, 32, 20, (k >> 8) % 6, flip=bool((k >> 12) & 1))
    c = rows[lz - 2][lx - 2] if 0 <= lz - 2 < 20 and 0 <= lx - 2 < 32 else '.'
    return ('M' if c == '.' else c), X - lx


def pattern(X, z, carved=False, fits=None, h=None, t=None, frieze=False):
    """The one face every desert-pyramid wall shares, as a function of the
    wall's screen column X and its height z above a fixed floor line, rows
    upright on every wall, so the courses run on unbroken round every corner
    and up every flight. The trim follows the wall's own edges: h above its
    floor line, t below its top (h = z and t = 47 - z on a face):
        h 0         the foot, against the floor
        t 0         the shadow under the cap
        r 13..30    frieze (back walls): an outlined hieroglyph to every 16 columns
        carved      a corridor face: the enemy glyphs, each placed only if
                    fits(first column, last column) -- whole on this face
        else        4-row courses of 8-wide blocks, joints a half block along
    """
    r = 47 - z
    if (z if h is None else h) <= 0:
        return 'K'
    if (r if t is None else t) <= 0:
        return 'D'
    if carved:
        cart = _cartouche(X, z)
        if cart is not None and (fits is None or fits(cart[1], cart[1] + CART_W - 1)):
            return cart[0]
    if frieze and 13 <= r <= 30:
        if r in (13, 30):
            return 'D'
        if r in (14, 29):
            return 'S'
        # one outlined glyph to every 16 columns, a different one each time
        gy, gx = r - 16, X % 16 - 3
        if 0 <= gy < 12 and 0 <= gx < 9:
            g = sheet_rows(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'desert_hieroglyphs.png'),
                           PAL, 9, 12, (X // 16 * 5 + 2) % len(GLYPH_ORDER))
            if g[gy][gx] != '.':
                return g[gy][gx]
        return 'M'
    rr = (r - 1) % 4
    off = ((r - 1) // 4) % 2 * 4
    return 'D' if rr == 3 or (X + off) % 8 == 7 else 'M'


def faces_from(pat):
    """Three 16 x 48 corridor faces: the shared pattern at three columns, so
    their glyphs differ and their rows line up."""
    return [[''.join(pat(16 * v + x, 47 - y) for x in range(16)) for y in range(48)] for v in range(3)]

def side(left, diag=False, end=False):
    g = Grid(16, 16)
    for y in range(16):
        for x in range(16):
            u = x + y if left else (15 - x) + y          # constant along the diagonal
            if diag and u > 15:
                continue                                 # below the diagonal: floor
            if diag and u == 15:
                g.put(x, y, 'K')                         # the floor's edge
                continue
            g.put(x, y, 'D' if u % 8 == 7 else 'S')      # courses run along the diagonal, 8px like the faces'
        if end:
            g.put(15 if left else 0, y, 'K')
    return g.rows()


# A staircase between chambers on different levels: a hall cut through the
# stone at 45 degrees, as the reference's are, with the chambers' own walls
# and outlines. One column of a flight is nine tiles, drawn as one 16x144
# strip and cut, so its diagonals cross tile edges unbroken; the next column
# is the same strip a tile higher (climbing right) or lower (climbing left),
# so they run unbroken from column to column too. Down the strip, along the
# diagonal u (x + y - 9 climbing right, y - x - 9 climbing left):
#     u  15        the wall's top edge, against the dark
#     u  15..22    its cap, as a straight rim's profile
#     u  23..70    the wall above the flight, the chambers' side-wall courses
#     u  71        the floor's edge line, as the chambers' diagonal
#     u  72..102   the flight: its steps, built in 3D (stair_steps)
#     u  103..110  the cap under the flight, then the dark
# Tiles 5 and 6 (rows y, y+1 of the column) are the walkable ones. A rising
# flight's cap climbs into tile 0 and a falling one's underside drops into
# tile 8; the tile either leaves empty is not laid.
RIM = ('K', 'M', 'M', 'M', 'M', 'S', 'D', 'K')      # a cap's profile, as a straight rim's
FLIGHT_TILES = 9


def stair_steps():
    """Only the steps are 3D: a descending flight of 4px steps (4 along, 4
    down), 16 deep, built in entrance_shapes.Scene and so drawn by the game's
    oblique projection (x + d, B - z - d) -- lit treads, the risers' shaded
    sides. 16 deep so its floor projects to the 32px the strip gives it. The
    steps repeat every 4px along the diagonal, so this one render is sampled
    for every column (flight_strip). Returns (sample(xs, ys), base)."""
    w, h, base = 512, 512, 128
    sc = Scene(w, h, base)
    for k in range(48):                                # 8px steps: chunky, as the NES draws a stair
        z = -8 * (k + 1)
        sc.box(1, 8 * k, 8 * k + 7, 0, 16, z - 8, z, front='S')
    g = sc.render()
    tone = {'L': 'M', 'M': 'M', 'D': 'D', 'S': 'S', 'K': 'K', '.': 'S'}
    return (lambda xs, ys: tone[g.g[ys][xs]]), base


def flight_strip(right):
    steps, base = stair_steps()
    C0 = 192                                           # where in the render to sample: mid-flight
    g = Grid(16, 16 * FLIGHT_TILES)
    for y in range(16 * FLIGHT_TILES):
        for x in range(16):
            # u = 15 meets the left edge at row 8, where a corridor's cap is, so a flight
            # leaves its corridor level and arrives level with the next (a column
            # further along is a tile further up or down)
            u = (x + y if right else y - x) + 7 - 16          # the strip starts a tile above the cap
            xx = x if right else 15 - x
            if u < 15 or u > 110:
                c = '.'
            elif u <= 22:
                c = RIM[u - 15]
            elif u < 71:
                c = 'D' if (u - 23) % 8 == 7 else 'S'           # courses counted from under the cap
            elif u == 71:
                c = 'K'
            elif u < 103:
                # the floor line u = 71 is the steps' back edge, base + X - 32 in the
                # render; a climbing flight samples it mirrored
                xs = C0 + (x if not right else -x)
                ys = y + base + C0 - 112          # row 80 + x lands on base + X - 32
                g.put(x, y, steps(xs, ys)); continue
            else:
                c = RIM[u - 103]
            g.put(x, y, c)
    rows = g.rows()
    return [rows[16 * i:16 * i + 16] for i in range(FLIGHT_TILES)]


def check_8bit(views):
    """The game's rules for a sprite: at most four colours a 16x16 cell, and
    no lone pixel with nothing of its colour round it, diagonals included -- a
    speck reads as noise at the game's scale, not as pixel art (a 1px diagonal
    line is a line). Textures only: a glyph's single-pixel eye is drawn on
    purpose."""
    for name, rows in views.items():
        for cy in range(0, len(rows), 16):
            for cx in range(0, len(rows[0]), 16):
                cell = {c for r in rows[cy:cy + 16] for c in r[cx:cx + 16]} - {'.'}
                assert len(cell) <= 4, (name, cx, cy, cell)
        specks = [(x, y) for y in range(1, len(rows) - 1) for x in range(1, len(rows[0]) - 1)
                  if rows[y][x] not in '.K' and all(rows[y + j][x + i] != rows[y][x]
                                                   for i in (-1, 0, 1) for j in (-1, 0, 1) if i or j)]
        if name.startswith(('flight', 'side', 'diag', 'end')):    # textures; a glyph's eye is drawn
            assert not specks, (name, specks[:5])


def design(variant='egypt'):
    pal = VARIANTS[variant]['pal']
    extra = {'flight%d_%s' % (i, 'r' if right else 'l'): t
             for right in (True, False) for i, t in enumerate(flight_strip(right))}
    extra.update({'side_l': side(True), 'side_r': side(False),
             'diag_l': side(True, diag=True), 'diag_r': side(False, diag=True),
             'end_l': side(True, end=True), 'end_r': side(False, end=True)})
    if variant == 'maya':
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import maya_murals
        faces = faces_from(maya_murals.pattern)
    else:
        faces = faces_from(lambda X, z: pattern(X, z, frieze=True))
    v = views(faces,
              extra, lit='M', base='S', shade='D')
    check_8bit(v)
    return {'pal': pal, 'view_w': 16, 'order': list(v), 'views': v}


if __name__ == '__main__':
    if sys.argv[1] == '--glyph-pixels':
        json.dump(glyph_pixels(), open(sys.argv[2], 'w')); sys.exit()
    # python pyramid_design.py <design.json> [egypt|maya]
    json.dump(design(sys.argv[2] if len(sys.argv) > 2 else 'egypt'), open(sys.argv[1], 'w'))
