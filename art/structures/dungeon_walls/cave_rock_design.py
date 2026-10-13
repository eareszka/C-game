"""The cave's rock, in 16 x 16 pieces (the user's reference: an EarthBound
cave, Desktop/reference/1.PNG -- floors on several levels, tall rock bands
between them whose edges run flat or in slopes, dark arches, a jagged lip
along the bottom).

    python art/structures/dungeon_walls/cave_rock_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/cave_rock

For the user to edit in Aseprite. Run this only to make the sheet afresh:
draw_views overwrites cave_rock.aseprite. Ask first.

The rock is the user's own (2026-10-12: "have them look like the stone sprite
i handrew on tileset but fitting the games pallete and sprite bible"): the
hand-drawn cave wall in assets/tileset.png, the master block's 16 x 48 strip
of cobbles -- a row of round stones along its top, lit above, dark at its foot.
It is brought to the interior bible's tones (the user's pick of two, "B is
correct"): base, shade, deep, black joints, nothing lighter than the base but
the gems, no lone pixels.

A cave is laid from whole cells on the 16px grid, never by bending a texture:
every piece is the strip, upright, cut to the piece's shape. A band's edges are
level or at 45 degrees and meet the grid at a cell's corners or its middle, so
a cell's four quarters (the triangles its diagonals cut) are each wholly rock
or not, and one piece serves each way they can fall (CELLS: where each piece
is, in cells).

Two kinds of wall (the user: "make it obvious which is a corner tile and whats
a straight up and down tile"):

  a level run faces you: the strip as drawn
    face0..2     rock inside the band (the strip's middle); face2 with the ore's gem
    top_flat     the band's top: the strip's top, its row of round stones
    foot_flat    its foot on the floor: the strip's dark foot
    hang_flat    the ragged underside of rock over the dark: the lowest floor
                 is a ledge, a face of rock hanging under its edge
    arch         2 x 2 cells: a mouth, its foot on the floor
    hatch        the dark a ladder out climbs into, four cells up the wall

  a sloped run is turned away: the same stones a tone down
    lean_up/down rock inside the band, where it rises / falls to the right
    top_up       the top edge rising to the right: rock is the lower right half
    top_down     ... falling: the lower left half
    foot_up      the foot rising: rock is the upper left half
    foot_down    ... falling: the upper right half
    hang_up/down the ragged underside, rising / falling
    tip_l, tip_r a floor's pointed end: rock but for the right / the left quarter
    valley       a top falls and rises again: rock but for the top quarter
    vault        a foot rises and falls again: rock but for the bottom quarter
    peak         a top's point: rock in the bottom quarter only
    fang         a foot's point: rock in the top quarter only

    floor0..1    the ground, plain and with a stalagmite

The game (src/dungeon.cpp cave_bake) draws a black line where a level cell
meets a sloped one: the corner where a front turns to a side.

The way between levels is the dungeons' own ladder (sheet row 14, a column an
ore), not drawn here. Nothing is mirrored: the light is from the upper left.
"""
import json, math, os, sys

PAL = {'K': '000000', 'M': '9797aa', 'D': '474751', 'S': '292931',     # line; rock: base, shade, deep
       'F': '595965', 'G': 'dcf0ff'}                                   # floor; a gem (in the game its ore's lit tone)
# Each piece is where the game's sheet has it in a cave's block (5 x 8 cells an
# ore; tools/gen_cave_tiles.py lays this sheet into each, in the ore's tones).
# (4, 0) and (3, 7) there are the crystal and the gem, hand-painted: left clear.
CELLS = {'face0': (0, 0), 'face1': (1, 0), 'face2': (2, 0), 'top_flat': (3, 0),
         'top_up': (0, 1), 'top_down': (1, 1), 'foot_flat': (2, 1), 'foot_up': (3, 1), 'foot_down': (4, 1),
         'hang_flat': (0, 2), 'hang_up': (1, 2), 'hang_down': (2, 2), 'tip_l': (3, 2), 'tip_r': (4, 2),
         'valley': (0, 3), 'vault': (1, 3), 'peak': (2, 3), 'fang': (3, 3), 'floor1': (4, 3),
         'arch': (0, 4), 'floor0': (2, 4), 'hatch': (3, 4), 'lean_up': (4, 4), 'lean_down': (2, 5)}
SIZE = {'arch': (2, 2)}                                                # in cells; the rest are 1 x 1
JAG = (1, 0, 0, 1, 1, 2, 1, 0, 0, 1, 2, 2, 1, 0, 1, 2)                 # a ragged edge: how far each column hangs back
HANG = (2, 4, 6, 5, 3, 1, 0, 2, 5, 7, 6, 4, 2, 1, 3, 4)                # a hanging edge: how far short of the cell's bottom each column ends
TOP, MID, FOOT = 0, 16, 32                                             # the strip's rows a cell takes: its top, its middle, its foot
SHEET = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'assets', 'tileset.png')
STRIP_COL = 28                                                         # tools/gen_cave_tiles.py MASTER_COL0: the hand-drawn block


def mend(g, wrap=False):
    """No tone alone: a pixel with none of its own round it takes what is most round it.
    wrap: the rows run on round the sides, as a strip laid side by side does."""
    h, w = len(g), len(g[0])

    def near(x, y):
        return [g[y + j][(x + i) % w] for i in (-1, 0, 1) for j in (-1, 0, 1)
                if (i or j) and 0 <= y + j < h and (wrap or 0 <= x + i < w) and g[y + j][(x + i) % w] != '.']
    while True:
        lone = [(x, y) for y in range(h) for x in range(w) if g[y][x] != '.' and near(x, y) and g[y][x] not in near(x, y)]
        if not lone:
            return g
        for x, y in lone:
            n = near(x, y)
            g[y][x] = max(sorted(set(n)), key=n.count)


def strip():
    """The hand-drawn rock in the bible's tones, 16 x 48 letters."""
    from PIL import Image
    im = Image.open(SHEET).convert('RGB')
    px = [[im.getpixel((STRIP_COL * 16 + x, y)) for x in range(16)] for y in range(48)]
    lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    # a cell of the strip at a time (it darkens toward its foot, and a tone is a
    # plane's, not a height's): its lightest third the base, its darkest fifth
    # the black joint, the rest the shade
    g = []
    for r0 in (0, 16, 32):
        ranked = sorted(lum(c) for r in px[r0:r0 + 16] for c in r)
        hi, lo = ranked[int(len(ranked) * 0.65)], ranked[int(len(ranked) * 0.20)]
        g += [['M' if lum(c) >= hi else 'K' if lum(c) <= lo else 'D' for c in r] for r in px[r0:r0 + 16]]
    return mend(g, wrap=True)


def cut(inside, rock, w=16, h=16):
    """w x h of rock(x, y) where inside(x, y), clear elsewhere, outlined where the two meet."""
    g = [[rock(x, y) if inside(x, y) else '.' for x in range(w)] for y in range(h)]
    if not any('.' in r for r in g):
        return g                                           # a whole cell: the strip as it is
    for y in range(h):
        for x in range(w):
            if g[y][x] != '.' and any(0 <= x + i < w and 0 <= y + j < h and g[y + j][x + i] == '.'
                                      for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 'K'
    return mend(g)                                         # the cut leaves no tone alone at its edge


def whole(x, y):
    return True


def floor(stalagmite):
    g = [['F'] * 16 for _ in range(16)]
    if stalagmite:
        for y, row in enumerate(('..K..', '.KSK.', '.KSK.', 'KSSSK', 'KKKKK')):
            for x, c in enumerate(row):
                if c != '.':
                    g[7 + y][5 + x] = c
    return g


def opening(g, cx, cy, half, r):
    """The dark of an arch or a hatch cut into g: round above (cx, cy), straight below, a deep rim."""
    def gap(x, y, grow=0.0):
        return (cx - half - grow <= x <= cx + half + grow and y >= cy) or math.hypot(x - cx, y - cy) <= r + grow
    for y in range(len(g)):
        for x in range(len(g[0])):
            if gap(x, y):
                g[y][x] = 'K'
            elif gap(x, y, 1.5):
                g[y][x] = 'S'
    return g


def ground_cobbles(cw=20, ch=14, gap=1.0):
    """Reality shard's floor (user, of four stone textures shown: the large
    rounded cobbles): rows of 0 / 1, 1 the line between stones. A seed to each
    cw x ch cell, jittered; a pixel is on a line where its two nearest seeds
    are within `gap` of as near as each other, which rounds every corner.
    The lines are thin (user: "be more thin"), so one is also drawn wherever a
    pixel's stone is not its right or lower neighbour's: thin, never broken.
    It tiles at 8 x 8 cells -- 160 x 112 -- and the game reads it in the
    oblique view (tools/gen_cave_tiles.py writes it to src/cave_rock.inc)."""
    W, H = cw * 8, ch * 8
    h32 = lambda i, j: (i * 73856093 ^ j * 19349663 ^ 0x51ed27) * 2654435761 % (1 << 32)
    near = [[None] * W for _ in range(H)]                # each pixel's (how much nearer its stone is than the next, its stone)
    for y in range(H):
        for x in range(W):
            d = []
            for i in range(x // cw - 2, x // cw + 3):
                for j in range(y // ch - 2, y // ch + 3):
                    h = h32(i % 8, j % 8)
                    sx, sy = i * cw + 2 + h % (cw - 3), j * ch + 2 + (h >> 8) % (ch - 3)
                    d.append((math.hypot(x - sx, (y - sy) * cw / ch), (i % 8, j % 8)))
            d.sort()
            near[y][x] = (d[1][0] - d[0][0], d[0][1])
    return [''.join('1' if near[y][x][0] < gap or near[y][x][1] != near[y][(x + 1) % W][1]
                    or near[y][x][1] != near[(y + 1) % H][x][1] else '0' for x in range(W)) for y in range(H)]


def design():
    S = strip()
    darker = {'M': 'D', 'D': 'S', 'S': 'S', 'K': 'K'}.get  # a wall turned away: every tone a step down
    rows = lambda r0: (lambda x, y: S[r0 + y % 16][x % 16])                 # a cell of the strip from its row r0
    turned = lambda x, y: darker(S[MID + y % 16][x % 16])
    arch_rock = lambda x, y: S[(MID if y < 16 else FOOT) + y % 16][x % 16]

    def standing(g):                                       # the line the rock stands on
        g[-1] = ['K'] * len(g[-1])
        return g
    face2 = cut(whole, rows(MID))                          # the gem: one of the strip's own round stones, in the ore's lit tone
    for y in range(8):
        for x in range(8):
            face2[4 + y][4 + x] = 'G' if S[y][x] == 'M' else S[y][x]
    art = {'face0': cut(whole, rows(MID)), 'face1': cut(whole, rows(MID)), 'face2': face2,
           'top_flat': cut(whole, rows(TOP)),
           'foot_flat': standing(cut(whole, rows(FOOT))),
           'hang_flat': cut(lambda x, y: y <= 15 - HANG[x], rows(FOOT)),
           'lean_up': cut(whole, turned), 'lean_down': cut(whole, turned),
           'top_up': cut(lambda x, y: x + y >= 15 + JAG[x], turned),
           'top_down': cut(lambda x, y: y - x >= JAG[x], turned),
           'foot_up': cut(lambda x, y: x + y <= 15 - JAG[x], turned),
           'foot_down': cut(lambda x, y: x - y >= JAG[x], turned),
           'hang_up': cut(lambda x, y: x + y <= 15 - HANG[x] // 2, turned),
           'hang_down': cut(lambda x, y: x - y >= HANG[x] // 2, turned),
           'tip_l': cut(lambda x, y: not (x + y >= 15 - JAG[y] and x - y >= -JAG[y]), turned),
           'tip_r': cut(lambda x, y: not (x + y <= 15 + JAG[y] and x - y <= JAG[y]), turned),
           'valley': cut(lambda x, y: not (x - y > JAG[x] and x + y < 15 - JAG[x]), turned),
           'vault': cut(lambda x, y: not (y - x > JAG[x] and x + y > 15 + JAG[x]), turned),
           'peak': cut(lambda x, y: y - x >= JAG[x] and x + y >= 15 + JAG[x], turned),
           'fang': cut(lambda x, y: x - y >= JAG[x] and x + y <= 15 - JAG[x], turned),
           'floor0': floor(False), 'floor1': floor(True),
           'arch': opening(standing(cut(whole, arch_rock, 32, 32)), 15.5, 14, 8, 8),
           'hatch': mend(opening(cut(whole, rows(MID)), 7.5, 8, 6, 6), wrap=True)}
    extras = []
    for k, (cx, cy) in CELLS.items():
        w, h = SIZE.get(k, (1, 1))
        lines = [''.join(r) for r in art[k]]
        assert len(lines) == 16 * h and all(len(r) == 16 * w for r in lines), k
        for y in range(0, 16 * h, 16):                       # four colours a cell
            for x in range(0, 16 * w, 16):
                cell = {c for r in lines[y:y + 16] for c in r[x:x + 16]} - {'.'}
                assert len(cell) <= 4, (k, x, y, cell)
        extras.append([cx * 16, cy * 16, lines])
    return {'pal': PAL, 'view_w': 16, 'order': [], 'views': {}, 'extras': extras}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
