"""The way out of a dungeon entered through a built doorway, seen from inside:
the doorway in the north wall at the way out's foot, daylight beyond it, each
the size and in the stone of the overworld doorway it leads back to (measured
from art/structures/entrances/*_design.py, a dungeon tile 16 art pixels):

    ruins     3x3 tiles  the gate: two columns, a beam, a 22-wide opening
    pyramid   2x2        pillars under a lintel, a 14x19 opening
    tree      2x2        the hollow in the trunk, the overworld's own (dark within)
    grave     1x2        the mausoleum's 14x19 doorway, steps up to the light
    church    1x3        the church's arched door, 16x33

    python art/structures/dungeon_doors_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/dungeon_doors

Four tones a cell: black, two of the doorway's stone, and the daylight (the
tree's hollow: black and three of bark, dark within as outside).
"""
import json, sys

W_ = 48                           # every view's slot in the export
PAL = {'K': '000000', 'W': 'dcf0ff',
       'g': '9797aa', 'h': 'c6ccda',                 # the ruins' and the graveyards' stone: base, lit
       'a': 'f4ce80', 'b': 'b29e5c',                 # the pyramid's sandstone: lit, shade
       't': '8d6b4f', 'u': '463422', 'l': 'b2966a'}  # the tree's bark: base, shade, lit


def blank(w, h):
    return [['.'] * w for _ in range(h)]


def box(g, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            g[y][x] = c


def outline(g, x0, y0, x1, y1):
    for x in range(x0, x1 + 1):
        g[y0][x] = g[y1][x] = 'K'
    for y in range(y0, y1 + 1):
        g[y][x0] = g[y][x1] = 'K'


def stone(g, x0, y0, x1, y1, lit, base):
    """A block: base, lit along its top and left, black round it."""
    box(g, x0, y0, x1, y1, base)
    for x in range(x0, x1 + 1):
        g[y0 + 1][x] = lit
    for y in range(y0, y1 + 1):
        g[y][x0 + 1] = lit
    outline(g, x0, y0, x1, y1)


def steps(g, x0, x1, y0, y1, lit, base):
    """Steps climbing away toward the light: treads lit, risers in the base,
    black between, each narrower than the one below."""
    n = 0
    for y in range(y1, y0 - 1, -1):
        k = (y1 - y) % 3
        inset = (y1 - y) // 3
        for x in range(x0 + inset, x1 - inset + 1):
            g[y][x] = 'K' if k == 2 else lit if k == 1 else base
        n += 1


def ruins():
    g = blank(48, 48)
    box(g, 13, 11, 34, 44, 'W')                       # daylight through the gate
    stone(g, 6, 10, 12, 47, 'h', 'g')                 # the columns, six wide
    stone(g, 35, 10, 41, 47, 'h', 'g')
    stone(g, 3, 4, 44, 10, 'h', 'g')                  # the beam over them
    steps(g, 13, 34, 42, 47, 'h', 'g')                # the gate's step
    for y in range(11, 42):
        g[y][13] = g[y][34] = 'K'
    return g


def pyramid():
    g = blank(32, 32)
    box(g, 9, 8, 22, 26, 'W')                         # the 14x19 doorway's light
    stone(g, 5, 7, 8, 31, 'a', 'b')                   # side pillars
    stone(g, 23, 7, 26, 31, 'a', 'b')
    stone(g, 3, 3, 28, 7, 'a', 'b')                   # the lintel
    steps(g, 9, 22, 27, 31, 'a', 'b')
    for y in range(8, 27):
        g[y][9] = g[y][22] = 'K'
    return g


def tree():
    """The giant tree's hollow, exactly as the overworld draws it in the
    trunk's foot (large_tree_design.hollow), seen from inside: its lip of bark,
    the dark within, the inner right wall catching a little light."""
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'entrances'))
    from large_tree_design import hollow
    from entrance_shapes import Grid
    g = Grid(32, 32)
    g.g = [['x'] * 32 for _ in range(32)]             # all trunk, so the whole lip is drawn
    hollow(g, cx=16, bot=31)
    swap = {'x': '.', 'K': 'K', 'D': 'u', 'M': 't', 'L': 'l'}
    return [[swap[c] for c in r] for r in g.g]


def grave():
    g = blank(16, 32)
    box(g, 1, 12, 14, 30, 'W')                        # light at the stair's head
    stone(g, 0, 8, 15, 12, 'h', 'g')                  # the lintel
    for y in range(12, 32):
        g[y][0] = g[y][15] = 'K'
    steps(g, 1, 14, 18, 31, 'h', 'g')                 # steps up to it
    return g


def church():
    g = blank(16, 48)
    for y in range(9, 48):                            # the arch's stone
        for x in range(16):
            r = ((x + .5 - 8) / 8) ** 2 + ((y + .5 - 17) / 8) ** 2
            if y >= 17 or r <= 1:
                g[y][x] = 'g'
    for y in range(11, 48):                           # the door's light inside it
        for x in range(1, 15):
            r = ((x + .5 - 8) / 7) ** 2 + ((y + .5 - 18) / 7) ** 2
            if y >= 18 or r <= 1:
                g[y][x] = 'W'
    for y in range(48):                               # black round the arch, lit along its inner left
        for x in range(16):
            if g[y][x] == 'g':
                near_w = any(0 <= y + dy < 48 and 0 <= x + dx < 16 and g[y + dy][x + dx] == 'W'
                             for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                near_out = any(not (0 <= y + dy < 48 and 0 <= x + dx < 16) or g[y + dy][x + dx] == '.'
                               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if near_out or near_w:
                    g[y][x] = 'K'
                elif x < 8:
                    g[y][x] = 'h'
    steps(g, 1, 14, 38, 47, 'h', 'g')
    return g


VIEWS = {'ruins': ruins(), 'pyramid': pyramid(), 'tree': tree(), 'grave': grave(), 'church': church()}


def design():
    return {'pal': PAL, 'view_w': W_, 'order': list(VIEWS),
            'views': {k: [''.join(r) for r in g] for k, g in VIEWS.items()}}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
