"""Shared pieces for a dungeon type's tiled walls (art/structures/dungeon_walls/
<type>_design.py). Every type draws the same seven 16px-wide cells, in order:

    band0..2  16x48  the north face, three cells tall: plain and two variants
    outer, vedge, hedge, inner   16x16  the wall top's rim, an autotile

The face has no cap of its own: the rim of the wall top above it is its cap.

The rim: a cap 8px wide along every side of a wall-top tile that meets floor
or a face. src/dungeon.cpp picks each 8x8 quarter of a tile on its own from
the quarter's two side neighbours and its corner neighbour (H = the west/east
one, V = the north/south one, D = the diagonal):
    H and V   OUTER  the rim turning round an outside corner
    H only    VEDGE  the rim running north-south
    V only    HEDGE  the rim running east-west
    D only    INNER  the rim turning round an inside corner
Each kind is one 16x16 cell whose four quarters are that kind's piece for each
quarter. Every piece is cut from one rule, so they all join: rim pixels are
those within 8px of the open side; a rim pixel touching anything else is
outline (even at a corner); then lit, base, shade toward the bottom-right.
The generator keeps every wall top at least 2 tiles wide and every wall
behind a face at least 5 thick, so two rims never meet without dark between.
"""

RIM_KINDS = ('outer', 'vedge', 'hedge', 'inner')
QUARTERS = ((0, 0, -1, -1), (8, 0, 1, -1), (0, 8, -1, 1), (8, 8, 1, 1))   # qx, qy, side x, side y


def h32(*k):
    """A small integer hash: the same stone for the same wall position."""
    v = 0x9E3779B1
    for n in k:
        v = ((v ^ (n & 0xffffffff)) * 0x85EBCA6B) & 0xffffffff
        v ^= v >> 13
    return v


_SHEETS = {}


def sheet_rows(png, pal, w, h, i, flip=False):
    """View i (w x h, side by side) of a plugin-drawn sheet, as tone rows by pal
    ('.' transparent) -- how a wall carves the hand-drawn figures in."""
    if (png, i) not in _SHEETS:
        from PIL import Image
        im = Image.open(png).convert('RGBA')
        tone = {tuple(int(v[k:k + 2], 16) for k in (0, 2, 4)): c for c, v in pal.items()}
        _SHEETS[(png, i)] = [''.join(tone[im.getpixel((i * w + x, y))[:3]] if im.getpixel((i * w + x, y))[3] else '.'
                                     for x in range(w)) for y in range(h)]
    rows = _SHEETS[(png, i)]
    return [r[::-1] for r in rows] if flip else rows


class Grid:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [['.'] * w for _ in range(h)]

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = c

    def rows(self):
        return [''.join(r) for r in self.g]


def rim_cell(kind, lit='L', base='M', shade='D', line='K'):
    g = Grid(16, 16)
    for qx, qy, sx, sy in QUARTERS:
        h, v = kind in ('outer', 'vedge'), kind in ('outer', 'hedge')
        d = kind == 'inner'
        open_t = set()                          # open tiles round the centre one, in tile steps
        if h: open_t |= {(sx, 0), (sx, sy)}
        if v: open_t |= {(0, sy), (sx, sy)}
        if d: open_t |= {(sx, sy)}
        # a 3x3-tile context in pixels, the centre tile at 16..31
        is_open = lambda x, y: ((x // 16) - 1, (y // 16) - 1) in open_t
        rim = {(x, y) for x in range(48) for y in range(48) if not is_open(x, y)
               and any(is_open(x + i, y + j) for i in range(-8, 9) for j in range(-8, 9)
                       if 0 <= x + i < 48 and 0 <= y + j < 48)}
        def col(x, y):
            nb = [(x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
            if any(n not in rim for n in nb):
                return line
            near = lambda k: any((x + i, y + j) not in rim for i, j in ((k, 0), (0, k)))
            return shade if near(2) else base if near(3) else lit
        for y in range(8):
            for x in range(8):
                px, py = 16 + qx + x, 16 + qy + y
                if (px, py) in rim:
                    g.put(qx + x, qy + y, col(px, py))
        # a joint between cap stones, once per tile along a straight run
        if kind == 'hedge' and qx == 8:
            for y in range(1, 7):
                if g.g[qy + y][10] != line:
                    g.put(10, qy + y, shade)
        if kind == 'vedge' and qy == 8:
            for x in range(1, 7):
                if g.g[11][qx + x] != line:
                    g.put(qx + x, 11, shade)
    return g.rows()


def recess(g, x0, y0, x1, y1, shade='D', line='K'):
    """A block fallen out of a face: the gap in shadow, the course above
    overhanging it and the light from the left leaving its left edge dark."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            g.put(x, y, shade)
    for x in range(x0, x1 + 1):
        g.put(x, y0, line)
    for y in range(y0, y1 + 1):
        g.put(x0, y, line)


def views(bands, extra=None, **tones):
    """The seven cells in the order src/dungeon.cpp reads them, then any
    cells only this type uses (extra: {name: 16x16 rows})."""
    assert len(bands) == 3 and all(len(b) == 48 and all(len(r) == 16 for r in b) for b in bands)
    v = {'band%d' % i: b for i, b in enumerate(bands)}
    v.update({k: rim_cell(k, **tones) for k in RIM_KINDS})
    v.update(extra or {})
    return v
