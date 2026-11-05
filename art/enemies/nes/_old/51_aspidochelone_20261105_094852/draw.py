from pix import *

SAND, SANDD = 'f4ce80', 'c18a39'
GL, GM, GD = '4fa667', '2c6c44', '235436'
BL, BM = '967448', '633e1b'
FIRE = 'fc9838'
W, H = 112, 84
OY = 4  # room above the palms


def over(im, part):
    """Lay a part on with its own black line round it."""
    im.alpha_composite(outline(part).crop((1, 1, W + 1, H + 1)))


def spans(im, y0, rows, c, dx=0, dy=0):
    for i, (a, b) in enumerate(rows):
        rect(im, a + dx, y0 + i + dy + OY, b - a + 1, 1, c)


def inset(part, y0, rows, c, dx, dy):
    """Paint the same runs shifted, only where the part already has colour."""
    px = part.load()
    for i, (a, b) in enumerate(rows):
        y = y0 + i + dy + OY
        for x in range(a + dx, b + dx + 1):
            if 0 <= x < W and 0 <= y < H and px[x, y][3]:
                px[x, y] = rgba(c)


def line(part, pts):
    """A black line, kept inside the part so it never pokes out into the air."""
    t = canvas(W, H)
    ImageDraw.Draw(t).line([(x, y + OY) for x, y in pts], fill=BLACK, width=1)
    a, b = t.load(), part.load()
    for y in range(H):
        for x in range(W):
            if a[x, y][3] and b[x, y][3]:
                b[x, y] = BLACK


def shape(pts, c):
    p = canvas(W, H)
    poly(p, [(x, y + OY) for x, y in pts], c)
    return p


im = canvas(W, H)

# ---- back flipper
p = shape([(20, 44), (10, 43), (3, 45), (0, 48), (2, 50), (9, 51), (20, 51)], BM)
poly(p, [(19, 44 + OY), (10, 44 + OY), (4, 46 + OY), (2, 48 + OY), (10, 48 + OY), (19, 47 + OY)], BL)
line(p, [(9, 44), (10, 50)])
over(im, p)

# ---- near front-left flipper
p = shape([(54, 50), (36, 53), (24, 57), (14, 62), (10, 66), (16, 67), (32, 67), (48, 66), (58, 60)], BM)
poly(p, [(50, 52 + OY), (36, 55 + OY), (25, 59 + OY), (15, 64 + OY), (30, 63 + OY), (46, 60 + OY)], BL)
for pts in (((22, 59), (26, 67)), ((33, 55), (38, 67))):
    line(p, pts)
over(im, p)

# ---- neck, wrinkled, coming out from under the shell
p = shape([(56, 48), (80, 48), (82, 54), (76, 62), (60, 62), (56, 56)], BM)
for pts in (((58, 50), (57, 58)), ((79, 50), (80, 56))):
    line(p, pts)
over(im, p)

# ---- shell rim, under the sand
SAND_ROWS = [(28, 70), (24, 74), (24, 78), (20, 78), (18, 81), (15, 81), (15, 84), (12, 84),
             (12, 87), (10, 87), (10, 89), (9, 89), (8, 90), (8, 90), (9, 90), (9, 88),
             (11, 88), (11, 86), (14, 86), (14, 83), (19, 83), (21, 78), (28, 74), (34, 66)]
RIM_ROWS = [(a - 1, b + 1) for a, b in SAND_ROWS]
p = canvas(W, H)
spans(p, 33, RIM_ROWS, BM)
inset(p, 33, RIM_ROWS, BL, -6, -3)
for x in range(18, 92, 11):
    lean = (x - 50) // 12
    line(p, [(x, 42), (x + lean, 57)])
over(im, p)

# ---- sand
p = canvas(W, H)
spans(p, 27, SAND_ROWS, SANDD)
inset(p, 27, SAND_ROWS, SAND, -2, -3)
over(im, p)
# ripples along the shore
for x, y, n in ((14, 41, 6), (24, 44, 7), (38, 46, 8), (76, 42, 6), (12, 36, 4)):
    rect(im, x, y + OY, n, 1, SANDD)

# ---- grass, with tufts biting into the sand
GRASS_ROWS = [(34, 64), (30, 70), (26, 70), (26, 77), (22, 77), (22, 81), (19, 81), (19, 82),
              (20, 82), (20, 80), (24, 80), (24, 76), (30, 76), (30, 70), (38, 62)]
p = canvas(W, H)
spans(p, 25, GRASS_ROWS, GD)
inset(p, 25, GRASS_ROWS, GM, -2, -2)
inset(p, 25, GRASS_ROWS, GL, -6, -8)
for x, y in ((23, 36), (28, 38), (34, 40), (42, 41), (50, 41), (74, 37), (78, 35)):
    rect(p, x, y + OY, 2, 1, GD)
    rect(p, x, y + 1 + OY, 1, 1, GD)
over(im, p)

# sand bay for the fire
p = canvas(W, H)
spans(p, 33, [(60, 66), (58, 69), (57, 71), (57, 71), (59, 70), (62, 67)], SAND)
over(im, p)


def bush(part, x, y, w, h):
    y += OY
    oval(part, x, y, w, h, GD)
    oval(part, x, y, w - 1, h - 1, GM)
    oval(part, x + 1, y + 1, max(w // 2, 2), max(h // 2 - 1, 2), GL)
    # leaf steps, so the crown is not a smooth ball
    rect(part, x + w // 2, y - 1, 3, 1, GM)
    rect(part, x + w - 1, y + h // 2 - 1, 1, 2, GD)
    rect(part, x - 1, y + h // 2, 1, 2, GM)


p = canvas(W, H)
for b in ((44, 22, 12, 9), (65, 20, 11, 8), (23, 26, 10, 7)):
    bush(p, *b)
over(im, p)
p = canvas(W, H)
for b in ((73, 25, 8, 7),):
    bush(p, *b)
over(im, p)


def trunk(im, pts):
    """pts: (x, y) of the left column going up. Three wide with notches."""
    p = canvas(W, H)
    for x, y in pts:
        rect(p, x, y + OY, 2, 1, BL)
        rect(p, x + 2, y + OY, 1, 1, BM)
    over(im, p)
    for i, (x, y) in enumerate(pts):
        if i % 5 == 3:
            rect(im, x + 1, y + OY, 2, 1, BLACK)


def frond(p, cx, cy, s, n, rise, drop, top, low):
    for i in range(n + 1):
        t = i / n
        y = cy - round(rise * 4 * t * (1 - t)) + round(drop * t * t)
        x = cx + s * i
        thick = 3 if i < n * .5 else 2 if i < n * .85 else 1
        rect(p, x, y + OY, 1, 1, top)
        if thick > 1:
            rect(p, x, y + 1 + OY, 1, thick - 1, low)
        if i % 3 == 1 and i < n - 1:
            rect(p, x, y + thick + OY, 1, 2, low)


def crown(im, cx, cy, big=14):
    # one part, so the fronds split by tone and only the silhouette takes a line
    p = canvas(W, H)
    for s in (-1, 1):
        frond(p, cx, cy + 2, s, big - 4, 1, 7, GD, GD)
    for s in (-1, 1):
        frond(p, cx, cy, s, big, 3, 8, GL, GM)
    for s in (-1, 1):
        frond(p, cx, cy - 2, s, big - 6, 3, 1, GL, GM)
    rect(p, cx - 1, cy + OY, 3, 2, BL)
    over(im, p)


trunk(im, [(38 - (i > 5) - (i > 11) - (i > 15), 32 - i) for i in range(18)])
trunk(im, [(56 + (i > 6) + (i > 14), 27 - i) for i in range(21)])
crown(im, 36, 15, 12)
crown(im, 59, 6, 14)

# ---- campfire
p = canvas(W, H)
rect(p, 60, 37 + OY, 9, 2, BL)
rect(p, 61, 38 + OY, 7, 1, BM)
over(im, p)
q = canvas(W, H)
stamp(q, grid(['...a...',
               '...aa..',
               '..aaa..',
               '.aabaa.',
               '.abbba.',
               '.abbba.'], {'a': FIRE, 'b': SAND}), 61, 31 + OY)
over(im, q)

# ---- near flipper right
p = shape([(76, 47), (86, 47), (94, 46), (102, 42), (102, 46), (99, 50), (92, 54), (84, 57), (76, 57)], BM)
poly(p, [(78, 48 + OY), (86, 48 + OY), (94, 47 + OY), (101, 44 + OY), (98, 48 + OY), (88, 51 + OY), (78, 52 + OY)], BL)
for pts in (((85, 48), (87, 57)), ((93, 47), (95, 52))):
    line(p, pts)
over(im, p)

# ---- head
HEAD = ['........llllllllmmm..........',
        '.....lllllllllllllmmmm.......',
        '...lllllllKKKKKllllmmmm......',
        '..lllllllKlllllKllllmmmm.....',
        '.lllllllllllllllllllmmmm.....',
        '.llllllllllllllllllllmmmm....',
        'lKKKKKlllllllllllKKKKKmmm....',
        'llllllllllllllllllllllmmm....',
        'llllKllllllllllllKllllmmm....',
        '.lllKlllllllllllllKlllmmm....',
        '..lllllllllllllllllllllmmm...',
        '....llllllllllllllllllmmmm...',
        '......lllllllllllllllmmmm....',
        '.......llllllKlllKlllmmm.....',
        '........llllllllllllmmm......',
        '.........lllllllllllmm.......',
        '.........KKKKKlKKKKKKK.......',
        '..........sssssKsssss........',
        '...........ssssssss..........',
        '.............ssss............']
q = canvas(W, H)
stamp(q, grid(HEAD, {'l': BL, 'm': BM, 's': SANDD}), 54, 48 + OY)
over(im, q)

im = strip_outline(im)
im = outline(im)
save(im)
