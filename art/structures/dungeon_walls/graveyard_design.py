"""The graveyard: walkways floating in complete darkness (the user's reference:
Mother 1's caves -- the idea, not their shapes or texture), red brick and
boardwalk giving way to one another, with a parallax of death imagery
drifting far behind.

    python art/structures/dungeon_walls/graveyard_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/graveyard

Each walkway top is a swatch sampled by where it is in the world, so a path
runs on seamless; under every south edge hangs that material's underside.

    brick, board          64 x 64 tops: old red pavers in running bond, 16 x 8
                          (a plank's height, so planks lay over them cell for
                          cell where the two meet); weathered planks, nail heads
    face_*_s, face_*_e    64 x 8: the walkway's thickness, its south face lit
                          and its east face in shade (the faces the oblique
                          view shows). Brick: two courses, 16 long on the
                          south face (joints at x % 16 == 15, the lower course
                          8 on), the bricks' 8-deep ends on the east (joints
                          at x % 8 == 0). Board: the last plank's side and the
                          stringer; the planks' cut ends every 8 on the east.
                          The bottom row is the black foot.
    wall_brick, wall_board  72 x 64: the wall at the back of a way out's landing,
                          in oblique: a 64 x 48 front face, its top 8 deep,
                          its east end in shade. The way out's doorway or a
                          ladder up into the dark stands on its front.
    under_*               64 x 24: what hangs below each -- soil and broken
                          brick; posts and a cross-beam
    ghosts                faint sheet-ghosts and a wisp, for the far layer
    skulls                faint skulls (two frames, turning) and loose bones,
                          for the near layer

Tones -- four a 16px cell, one palette.
"""
import json, math, random, sys

PAL = {'K': '000000',
       'M': '9797aa', 'D': '595965', 'L': 'c6ccda', 'T': '235436',          # stone, moss
       'W': '967448', 'V': '785830', 'E': '493712',                          # wood, its shade, earth
       'B': 'e8e0c0', 'S': 'b2966a',                                         # bone, its shade
       'R': 'b6433d', 'r': '792727', 'm': '531b1c', 'n': '5d1e1f',           # brick (the houses'), its shade, mortar, the shaded face
       'g': '1e1e24', 'h': '292931', 'j': '34343e'}                          # the dark's faint greys
VW, VH = 128, 64


def blank(w, h):
    return [['.'] * w for _ in range(h)]


def brick():
    """Red pavers in running bond, tiling 64: each 16 x 8, its lower row and
    right column in shade, the mortar dark; some bricks worn darker, a few
    chipped corners."""
    g = [['R'] * 64 for _ in range(64)]
    rng = random.Random(5)
    for row in range(8):
        off = 8 * (row % 2)
        for b in range(4):
            x0, y0 = (b * 16 + off) % 64, row * 8
            worn = rng.random() < 0.25
            for y in range(y0, y0 + 8):
                for i in range(16):
                    x = (x0 + i) % 64
                    if y == y0 + 7 or i == 15:
                        g[y][x] = 'm'                            # the mortar
                    elif worn or y == y0 + 6 or i == 14:
                        g[y][x] = 'r'                            # shade
            if rng.random() < 0.3:                               # a chipped corner
                for dy, w in ((0, 3), (1, 2), (2, 1)):
                    for i in range(w):
                        g[y0 + dy][(x0 + i) % 64] = 'K'
    return g


def board():
    """Planks across, 8 tall, a dark gap between, their ends staggered,
    nail heads at each end, grain in the shade."""
    g = [['W'] * 64 for _ in range(64)]
    for y in range(64):
        r = y % 8
        if r == 7:
            for x in range(64):
                g[y][x] = 'E'                                # the gap
        elif r == 6:
            for x in range(64):
                g[y][x] = 'V'                                # its shadowed edge
    for p in range(8):
        end = (p * 23) % 64                                  # each plank's butt joint
        for y in range(p * 8, p * 8 + 7):
            g[y][end] = 'E'
        for nx in ((end + 2) % 64, (end - 3) % 64):
            g[p * 8 + 2][nx] = 'K'; g[p * 8 + 3][nx] = 'K'   # nail heads
        for x in range(0, 64, 9):                            # grain
            g[p * 8 + 1 + (x // 9) % 4][(x + p * 5) % 64] = 'V'
            g[p * 8 + 1 + (x // 9) % 4][(x + p * 5 + 1) % 64] = 'V'
            g[p * 8 + 1 + (x // 9) % 4][(x + p * 5 + 2) % 64] = 'V'
    return g


def under(kind):
    """What hangs under a south edge, 24 deep, its foot ragged."""
    g = blank(64, 24)
    rng = random.Random({'brick': 1, 'board': 2}[kind])
    if kind == 'board':
        for px in range(4, 64, 16):                          # posts down into the dark (the
            ln = rng.randrange(10, 24)                       # stringer is in the face above)
            for y in range(0, ln):
                for dx in range(3):
                    g[y][px + dx] = 'W' if dx == 0 else 'V'
            for dx in range(3):
                g[ln - 1][px + dx] = 'K'
        return g
    base = 'E'
    depth = [0] * 64
    d = 10
    for x in range(64):
        d = max(5, min(20, d + rng.choice((-2, -1, 0, 1, 2))))
        depth[x] = d
    for x in range(64):
        for y in range(depth[x]):
            g[y][x] = base
        g[depth[x] - 1][x] = 'K'
    for _ in range(9):                                       # broken bricks caught in the clod
        x0, y0 = rng.randrange(60), rng.randrange(2, 9)
        for dx in range(4):
            for dy in range(3):
                if g[y0 + dy][(x0 + dx) % 64] == base:
                    g[y0 + dy][(x0 + dx) % 64] = 'R' if dy < 2 else 'r'
    roots = []                                               # roots dangling below, long and thin,
    while len(roots) < 10:                                   # in the soil's brown so they show on the
        x = rng.randrange(64)                                # dark; 3 apart (round the wrap too), so
        if all(min((x - r) % 64, (r - x) % 64) >= 3 for r in roots):   # swaying they never cross
            roots.append(x)
    for x in roots:
        for y in range(depth[x], min(24, depth[x] + rng.randrange(5, 14))):
            g[y][x] = 'E'
    return g


def face(kind, side):
    """The walkway's thickness, 64 x 8, read at (depth below the top's edge,
    along); the last row is the foot's outline."""
    g = [['K'] * 64 for _ in range(8)]
    for y in range(7):
        for x in range(64):
            if kind == 'brick':
                course, r = divmod(y, 4)                     # two courses, rows 0-2 and 4-6
                if r == 3:
                    c = 'm'
                elif side == 's':
                    joint = (x + 8 * course) % 16 == 15
                    c = 'm' if joint else ('r' if r == 2 or (x + 8 * course) % 16 == 14 else 'R')
                else:
                    joint = (x + 4 * course) % 8 == 0
                    c = 'm' if joint else ('n' if r == 2 or (x + 4 * course) % 8 == 7 else 'r')
            elif side == 's':                                # the last plank's side, the stringer
                c = 'W' if y < 3 else ('E' if y == 3 else 'V')
                if y == 1 and x % 9 in (2, 3, 4):
                    c = 'V'                                  # grain
                if y == 5 and x % 16 == 6:
                    c = 'K'                                  # a bolt through the stringer
            else:                                            # the planks' cut ends
                c = 'E' if x % 8 == 7 or y == 4 else ('V' if y > 4 else 'W')
                if y == 1 and x % 8 in (2, 3):
                    c = 'V'                                  # end grain
            g[y][x] = c
    return g


def wall(kind):
    """A wall 64 wide, 8 deep, 48 tall, drawn as the oblique view shows it:
    the front face (x 0-63, y 16-63), its top above (each row back one up and
    one right), its east end (x 64-71) in shade. Outlined in black."""
    g = blank(72, 64)
    rng = random.Random(7)
    worn = {(c, b): rng.random() < 0.25 for c in range(6) for b in range(5)}   # dark bricks, as the path's
    for y in range(16, 64):                                  # the front face
        z = 63 - y
        for x in range(64):
            if kind == 'brick':
                course = z // 8
                if z % 8 == 7:
                    c = 'm'
                elif (x + 8 * (course % 2)) % 16 == 15:
                    c = 'm'
                elif z % 8 == 0 or (x + 8 * (course % 2)) % 16 == 14 or                         worn[(course, (x + 8 * (course % 2)) // 16)]:
                    c = 'r'
                else:
                    c = 'R'
            else:                                            # boards across, a post at each end and the middle
                if x in (0, 1, 2, 30, 31, 32, 61, 62, 63):
                    c = 'W' if x in (0, 30, 61) else 'V'
                else:
                    c = 'E' if z % 8 == 7 else ('V' if z % 8 == 0 else 'W')
                    if z % 8 == 4 and x % 11 in (3, 4, 5):
                        c = 'V'                              # grain
            g[y][x] = c
    if kind == 'brick':                                      # chipped corners, as the path's bricks
        for course in range(6):
            for bx in range(-8 * (course % 2), 64, 16):
                if bx < 0 or rng.random() >= 0.3:
                    continue
                for dz, w in ((0, 3), (1, 2), (2, 1)):
                    for i in range(w):
                        g[63 - (course * 8 + 6 - dz)][bx + i] = 'K'
    if kind == 'board':                                      # the boardwalk's marks: each board's
        for b in range(6):                                   # butt joint and the slashed nail pair by it
            y0 = 63 - b * 8 - 6                              # the board's top row
            end = rng.randrange(5, 25)
            for x in (end, end + 30):
                if x in (30, 31, 32) or x > 60:
                    continue
                for y in range(y0, y0 + 6):
                    g[y][x] = 'E'
                for nx in (x + 3, x - 4):
                    if 3 <= nx < 60 and nx not in (29, 30, 31, 32, 33):
                        g[y0 + 2][nx + 1] = 'K'; g[y0 + 3][nx] = 'K'
    for dv in range(1, 9):                                   # the top, 8 back
        y = 16 - dv
        for x in range(dv, 64 + dv):
            if kind == 'brick':
                c = 'm' if dv == 4 or (x - dv) % 16 == 15 else 'R'
            else:
                c = 'E' if dv == 4 else 'W'                  # the cap beam, its join
            g[y][x] = c
        for y in range(16 - dv + 1, 64 - dv + 1):            # the east end
            z = 63 - dv - y + 1
            if kind == 'brick':
                c = 'm' if z % 8 == 7 else ('K' if z % 8 == 0 and dv > 6 else 'n')
            else:
                c = 'E' if z % 8 == 7 else 'V'
            g[y][63 + dv] = c
    out = [r[:] for r in g]
    for y in range(64):
        for x in range(72):
            if g[y][x] != '.' and any(not (0 <= x + i < 72 and 0 <= y + j < 64) or g[y + j][x + i] == '.'
                                      for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = 'K'
    for y in range(16, 64):                                  # the corner where the front turns east
        out[y][63] = 'K'
    return out


GHOST = ["....hhhh....",
         "..hhhhhhhh..",
         ".hhhhhhhhhh.",
         "hhhgghhgghhh",
         "hhhgghhgghhh",
         "hhhhhhhhhhhh",
         "hhhhhggghhhh",
         "hhhhhhhhhhhh",
         "hhhhhhhhhhhh",
         "hhhhhhhhhhhh",
         "hhhhhhhhhhhh",
         "hh.hhh.hhh.h",
         "h...h...h..."]


def ghosts():
    g = blank(VW, VH)
    for y, row in enumerate(GHOST):
        for x, c in enumerate(row):
            if c != '.':
                g[y][x] = c
    for x in range(20, 60):                                  # a wisp
        y = 30 + int(3 * math.sin(x / 6))
        g[y][x] = 'g'
        if x % 3:
            g[y + 1][x] = 'g'
    return g


def skulls():
    """Two frames of a faint skull turning, and loose bones."""
    g = blank(VW, VH)
    face = ["..jjjj..", ".jjjjjj.", "jjjjjjjj", "jhhjjhhj", "jhhjjhhj", "jjjjjjjj", ".jjhhjj.", "..jjjj.."]
    side = ["..jjjj..", ".jjjjjj.", "jjjjjjjj", "jjjjjhhj", "jjjjjhhj", "jjjjjjjj", ".jjjjhj.", "..jjjj.."]
    for f, spr in enumerate((face, side)):
        for y, row in enumerate(spr):
            for x, c in enumerate(row):
                if c != '.':
                    g[y][f * 10 + x] = c
    for y, row in enumerate(["jj......jj", "jjjjjjjjjj", "jj......jj"]):
        for x, c in enumerate(row):
            if c != '.':
                g[12 + y][x] = c
    return g


def design():
    def pad(rows):
        return [''.join(r) + '.' * (VW - len(r)) for r in rows] + ['.' * VW] * (VH - len(rows))
    v = {'brick': pad(brick()), 'board': pad(board()),
         'under_brick': pad(under('brick')), 'under_board': pad(under('board')),
         'face_brick_s': pad(face('brick', 's')), 'face_brick_e': pad(face('brick', 'e')),
         'face_board_s': pad(face('board', 's')), 'face_board_e': pad(face('board', 'e')),
         'wall_brick': pad(wall('brick')), 'wall_board': pad(wall('board')),
         'ghosts': pad(ghosts()), 'skulls': pad(skulls())}
    for name, rows in v.items():                         # four colours a cell, as the game holds them
        for cy in range(0, VH, 16):
            for cx in range(0, VW, 16):
                cell = {c for r in rows[cy:cy + 16] for c in r[cx:cx + 16]} - {'.'}
                assert len(cell) <= 4, (name, cx, cy, cell)
    return {'pal': PAL, 'view_w': VW, 'order': list(v), 'views': v}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
