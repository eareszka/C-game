from pix import *

HI = '815423'   # lit hide
MID = '583518'  # hide
LO = '341e10'   # shaded hide
BONE = 'f4ce80'
RED = 'b6433d'
BLUE = '2850a0'
GRN = '4fa667'
GRD = '2c6c44'

W, H = 190, 150
DY = 14         # everything below the crown sits this far down
im = canvas(W, H)


def put(part, x=0, y=0):
    """Lay a part down with its black key line."""
    o = outline(part)
    src = o.load()
    dst = im.load()
    for yy in range(o.height):
        for xx in range(o.width):
            c = src[xx, yy]
            tx, ty = x + xx - 1, y + yy - 1
            if c[3] and 0 <= tx < W and 0 <= ty < H:
                dst[tx, ty] = c


def hide(points_list, right=(5, 3), left=(2, 2)):
    """A hide part: flat polygons with stepped light from the upper left."""
    lay = canvas(W, H)
    for pts in points_list:
        poly(lay, [(x, y + DY) for x, y in pts], MID)
    src = lay.copy().load()
    px = lay.load()

    def on(x, y):
        return 0 <= x < W and 0 <= y < H and src[x, y][3] > 0

    for y in range(H):
        for x in range(W):
            if not src[x, y][3]:
                continue
            j = ((x // 3) + (y // 3)) % 2 * 2
            if not on(x + right[0] + j, y + right[1] + j):
                px[x, y] = rgba(LO)
            elif not on(x - left[0], y - left[1] - j):
                px[x, y] = rgba(HI)
    return lay


# ---------- the boar head, half a face; column 15 is the centre line ----------
# a lit hide (mid on the right), b hide, e hide on the left / shade on the right,
# c shade, s snout, d snout underside, y bone, r mouth, E eye
HALF = [
    "............a..a",
    "c.........a.aa.a",
    "cc......aaaaaaaa",
    "ecc...aaaaaaKKKK",
    ".ecc.aaaaaKKyyyy",
    ".eccaaaaaKyyyyyy",
    "..ecaaaabKyyyyyy",
    ".eeaaabbbKyyyyyy",
    "eeaabbbbbbKyyyyy",
    "eeabbbbbbbbKKKKK",
    ".eebbbKKbbbbbbbb",
    ".ebbbbbEEbKKKKKK",
    ".ybbbbbbbKssssss",
    ".yKbbbbbKsssssss",
    ".yyKbbbbKsssKKss",
    "yyyKebbbKsssKKss",
    "yyyKebbbKsssssss",
    "yyyyKebbKsssssss",
    ".yyyyKebbKdddddd",
    "..yyyyKKKKKKKKKK",
    "...yyyyyKyyKyyKy",
    "....KKKKrKyKrKyK",
    ".....ebKrrrrrrrr",
    ".....ebKrrrrrrKK",
    ".....ebKrrrrrKrr",
    "......eKyrKyrKyr",
    "......ebKyKyKyKy",
    ".......ebKKKKKKK",
    ".........ebbbbbb",
    "...........ebbbb",
    ".............ebb",
]
LEFT = {'a': HI, 'b': MID, 'e': MID, 'c': LO, 's': HI, 'd': MID, 'y': BONE, 'r': RED, 'E': BONE}
RIGHT = {'a': MID, 'b': MID, 'e': LO, 'c': LO, 's': HI, 'd': LO, 'y': BONE, 'r': RED, 'E': BONE}


def head(drool=None, lean=0.0):
    """lean shifts the rows sideways in clear steps, so each head tilts its own way."""
    rows = HALF
    n = len(rows[0])
    pad = 4
    part = canvas(n * 2 - 1 + pad * 2, len(rows) + 8)
    px = part.load()
    for y, row in enumerate(rows):
        s = round((y - 15) * lean)
        full = row + row[-2::-1]
        for x, ch in enumerate(full):
            if ch == '.':
                continue
            tx = x + s + pad
            if ch == 'K':
                px[tx, y] = BLACK
            else:
                px[tx, y] = rgba((LEFT if x < n else RIGHT)[ch])
    for dx, y0, y1 in (drool or []):
        for y in range(y0, y1):
            px[dx + pad + round((y - 15) * lean), y] = rgba(BONE)
    return part


def put_head(part, x, y):
    put(part, x - 4, y + DY)


# ---------- green spines ----------
def spine(x, top, base, w=4):
    lay = canvas(W, H)
    rect(lay, x, top + 3, w, base - top - 3, GRD)
    rect(lay, x, top + 3, w - 2, base - top - 3, GRN)
    rect(lay, x + 1, top, 1, 3, GRN)
    rect(lay, x + 2, top + 1, 1, 2, GRD)
    y = top + 7
    while y < base - 2:
        rect(lay, x, y, w, 1, BLACK)
        y += 7
    return lay


for sx, top, base in ((62, 22, 52), (70, 12, 48), (78, 4, 42), (86, 11, 40), (94, 0, 38),
                      (102, 8, 40), (110, 2, 42), (118, 13, 48), (126, 6, 48), (134, 22, 54)):
    put(spine(sx, top, base))

# ---------- tail ----------
put(hide([[(26, 70), (29, 74), (13, 90), (10, 88)]], right=(2, 1), left=(1, 1)))
put(hide([[(9, 86), (14, 88), (16, 96), (15, 108), (12, 102), (10, 110), (8, 103), (5, 109), (5, 98)]],
         right=(2, 1), left=(1, 1)))

# ---------- far legs ----------
put(hide([[(128, 84), (152, 80), (153, 96), (147, 104), (147, 110), (149, 118), (135, 118), (138, 108), (136, 100)]]))

# ---------- the mound with its ridge ----------
body = [
    (50, 36), (60, 22), (70, 26), (78, 14), (86, 20), (94, 10), (102, 18), (110, 12),
    (118, 21), (126, 22), (140, 38), (152, 60), (152, 86), (136, 92), (120, 92), (112, 104),
    (106, 96), (100, 110), (96, 98), (90, 106), (84, 94), (60, 92), (38, 90), (24, 84), (22, 78), (28, 68),
    (34, 54),
]
# near legs are one piece with the body, so no cut line crosses the hide
put(hide([
    body,
    [(30, 66), (40, 64), (50, 84), (44, 96), (44, 108), (49, 122), (32, 122), (34, 110), (28, 100), (20, 86), (20, 78)],
    [(52, 86), (78, 86), (77, 100), (72, 108), (72, 114), (77, 122), (60, 122), (64, 112), (60, 104)],
    [(110, 86), (134, 86), (133, 98), (127, 108), (127, 114), (131, 122), (114, 122), (117, 112), (115, 104)],
]))


# ---------- hooves ----------
def hoof(x, y, w):
    y += DY
    rect(im, x, y, w, 4, LO)
    rect(im, x, y, w // 2, 1, MID)
    rect(im, x + w // 2, y + 1, 1, 3, BLACK)
    rect(im, x, y - 1, w, 1, BLACK)


hoof(32, 120, 18)
hoof(60, 120, 17)
hoof(114, 120, 18)
hoof(135, 116, 15)


# ---------- blue veins ----------
def vein(pts, w=2):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        x, y = x0, y0
        while (x, y) != (x1, y1):
            rect(im, x, y + DY, w, w, BLUE)
            if abs(x1 - x) >= abs(y1 - y):
                x += 1 if x1 > x else -1
            else:
                y += 1 if y1 > y else -1
        rect(im, x1, y1 + DY, w, w, BLUE)


vein([(86, 20), (84, 30), (87, 38), (81, 46), (80, 56)])
vein([(84, 30), (74, 38), (72, 48)], 1)
vein([(72, 24), (68, 38), (60, 44), (54, 56)])
vein([(112, 16), (116, 30), (113, 40), (120, 48), (122, 58)])
vein([(116, 30), (126, 38), (128, 46)], 1)

# ---------- fur marks and muscle lines on the open hide ----------
for fx, fy in ((64, 72), (72, 82), (56, 84), (30, 72), (24, 82), (34, 84), (112, 78), (122, 76),
               (92, 28), (102, 24), (98, 38), (104, 44), (124, 86), (66, 100), (146, 92), (38, 100)):
    rect(im, fx, fy + DY, 3, 1, BLACK)
    rect(im, fx - 1, fy + 1 + DY, 1, 2, BLACK)

# haunch crease on the rear leg
vein_black = [(40, 70), (41, 71), (42, 72), (43, 74), (44, 76), (45, 78), (46, 80), (47, 83), (48, 86), (48, 89), (47, 92)]
for vx, vy in vein_black:
    dot(im, vx, vy + DY, BLACK[:3])

# ---------- heads, back to front ----------
put_head(head(lean=-0.06), 43, 18)
put_head(head(lean=0.06), 123, 18)
put_head(head([(9, 27, 34)], lean=-0.1), 18, 42)
put_head(head([(21, 27, 33)], lean=0.1), 137, 44)
put_head(head([(11, 27, 36), (13, 27, 31)]), 84, 50)
put_head(head([(19, 27, 33)], lean=0.06), 47, 60)
put_head(head(lean=-0.06), 115, 65)

im = strip_outline(im)
im = outline(im)
save(im)
