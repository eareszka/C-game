"""The palm, laid out for tools/draw_views.py -- the user's own palm sprite,
brought into the game's art direction.

    python art/structures/entrances/palm_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/palm

ORIGINAL is that sprite exactly as it was drawn (the sheet's cell 17, rows 2-3
before the palette commit 830f1e1 pruned it): mint fronds weeping over a curved
tan trunk on spread roots, 16x32, as tall as the game's tall trees. What is
changed, and why:

  - black stays the outline only. Inside the crown the original is mostly black
    between the fronds; there those lines become the trees' dark green, so
    the crown reads as leaves the way the game's trees do;
  - the fronds take the trees' greens, lit along their upper-left edges;
  - the trunk keeps its tan, in shade on its right; where it rises into the
    crown's cell it is the dark green of the shade under the leaves, which is
    also what keeps that cell to four colours;
  - nothing touches the sprite's sides and no pixel stands alone: the strays
    at the crown's edge are gone and the crown is one pixel narrower a side.

Its oasis puts it in a cell column of its own.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, check

ORIGINAL = [            # d mint frond, c tan trunk, b a stray green, K black
    "...KKK...KKKK...",
    "..KdddK.KdddKK..",
    ".KddKKKKKKdddK..",
    "KdKKddKKKKKKddK.",
    "dKKddKKdKKKdKdK.",
    ".KddKddKKKKKdKK.",
    ".KdKddKKKKdKKddK",
    "KdKddKKdKKKddKdK",
    "KdKddKddKKdKdKKb",
    "KdKdKKdKddKKKdK.",
    "dKddKKdKKddKKdK.",
    ".KddKKdKKKdKdKdK",
    ".KdKdKKKcKdKKddK",
    ".KdKKKKcKKdKKdK.",
    ".KdKd.KccKK.KdKb",
    ".dKd..KKccK.dKd.",
    "......KKKcK.....",
    ".......KcKcK....",
    "......KccKcK....",
    "......KccKK.....",
    ".....KKcKcK.....",
    ".....KcKKcK.....",
    ".....KcKccK.....",
    ".....KKccK......",
    "......KKKK......",
    "......KKcK......",
    "...K.KKccKKK....",
    "..KcKcccKKccK...",
    "..KKccKKcKKK....",
    ".KccKKccKccK....",
    ".KcKKccK.KKcK...",
    "..KKcKK....K....",
]

PAL = {'K': '000000', 'G': '235436', 'g': '058f3a', 'l': '4edc4a',
       'T': 'd7a175', 't': '605028'}


def adapt():
    src = [list(r) for r in ORIGINAL]
    h, w = len(src), len(src[0])
    # the strays: the lone greens on the right edge, the mint outside the line
    for x, y in ((15, 8), (15, 14), (0, 4), (0, 10), (1, 15)):
        src[y][x] = '.'
    # one pixel in from each side: the crown's outer columns fold inward
    for y in range(h):
        if src[y][0] != '.':
            src[y][1] = 'K' if src[y][1] == '.' else src[y][1]
            src[y][0] = '.'
        if src[y][w - 1] != '.':
            src[y][w - 2] = 'K' if src[y][w - 2] == '.' else src[y][w - 2]
            src[y][w - 1] = '.'
    ink = lambda x, y: 0 <= x < w and 0 <= y < h and src[y][x] != '.'
    at = lambda x, y: src[y][x] if ink(x, y) else '.'
    out = [r[:] for r in src]
    for y in range(h):
        for x in range(w):
            c = src[y][x]
            if c == '.':
                continue
            crown = y < 16
            if any(not ink(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = 'K'                            # the outline, all the way round
            elif c == 'K':
                out[y][x] = 'G' if crown else 't'          # inner lines: shade, not black
            elif c == 'd':
                # a frond stroke stays bright, as the original's mint is; its
                # top-left pixel catches the light, the rest of it is mid green
                out[y][x] = 'g' if at(x - 1, y) == 'd' or at(x, y - 1) == 'd' else 'l'
            elif c == 'c':
                out[y][x] = 'G' if crown else 'T'
    g = Grid(w, h)
    g.g = out
    return g


def design():
    g = adapt()
    # a part laid into a block with room above it, so checked with that room
    room = Grid(16, 33)
    room.g = [['.'] * 16] + [r[:] for r in g.g]
    check(room, 'palm')
    return {'pal': PAL, 'view_w': 16, 'order': ['palm'], 'views': {'palm': g.rows()}}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
    for r in design()['views']['palm']: print(r)
