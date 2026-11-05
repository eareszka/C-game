from pix import *

R1, R2, R3 = 'b6433d', '792727', '531b1c'   # eagle reds
BR = '764c20'                               # flight feather tips, gold shade
G = 'f0bc3c'                                # beak, talons
C = 'e8e0c0'                                # chest bib, tusk, eye
GL, GD = '9797aa', '595965'                 # dugong
K = (0, 0, 0)


def line(im, x0, y0, x1, y1, c=K):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x1 > x0 else -1), (1 if y1 > y0 else -1)
    err = dx - dy
    while True:
        ImageDraw.Draw(im).point((x0, y0), fill=rgba(c))
        if (x0, y0) == (x1, y1):
            break
        e = 2 * err
        if e > -dy:
            err -= dy
            x0 += sx
        if e < dy:
            err += dx
            y0 += sy


def recolour_right_of(im, xcut, frm, to):
    px = im.load()
    for y in range(im.height):
        for x in range(xcut, im.width):
            if px[x, y] == rgba(frm):
                px[x, y] = rgba(to)


def wing(lit):
    """The bird's wing on the viewer's left, 36 wide. Mirrored for the other side."""
    w = canvas(36, 50)

    # primaries: broad fingers fanned from the wrist, brown tips, red roots.
    # Drawn bottom up so each overlaps the next; only the tips stand apart.
    prim = [(17, 19, 6, 26), (16, 16, 2, 21), (15, 13, 0, 16), (15, 10, 0, 11), (15, 7, 0, 6), (17, 4, 2, 1)]
    for i, (rx, ry, tx, ty) in enumerate(prim):
        mx, my = (rx + tx * 2) // 3, (ry + ty * 2) // 3
        f = canvas(36, 50)
        poly(f, [(rx, ry - 2), (mx, my - 2), (tx, ty), (mx, my + 1), (rx, ry + 2)], BR)
        recolour_right_of(f, 9 - i % 2, BR, R3 if i % 2 else R2)
        stamp(w, f, 0, 0)
    # one black line between neighbours, stopping where the tips part
    for (ax, ay, bx, by), (cx, cy, ex, ey) in zip(prim, prim[1:]):
        line(w, (ax + cx) // 2, (ay + cy) // 2, (bx + ex) // 2 + 4, (by + ey) // 2)

    # secondaries: hang from the arm, stepping in toward the body
    sec = [(18, 19, 11, 28), (21, 21, 15, 31), (24, 23, 19, 34), (27, 25, 23, 36), (30, 27, 27, 37)]
    for i, (rx, ry, tx, ty) in enumerate(sec):
        poly(w, [(rx - 2, ry), (rx + 2, ry), (tx + 2, ty - 2), (tx, ty), (tx - 1, ty - 2)], R2 if i % 2 == 0 else R3)
    # black only every other gap: the two reds already split the rest
    for rx, ry, tx, ty in sec[1::2]:
        line(w, rx + 3, ry + 3, tx + 2, ty - 1)

    # coverts: the broad red arm of the wing
    poly(w, [(33, 14), (25, 8), (19, 4), (14, 3), (11, 6), (12, 12), (15, 18), (22, 23), (30, 28), (33, 26)], R2)
    # lit leading edge, slimmer on the far wing
    if lit:
        poly(w, [(33, 14), (25, 8), (19, 4), (14, 3), (12, 5), (13, 8), (19, 8), (25, 11), (33, 17)], R1)
    else:
        poly(w, [(33, 14), (25, 8), (19, 4), (14, 3), (12, 5), (14, 6), (19, 6), (25, 10), (33, 15)], R1)
    # lower covert band in shade
    poly(w, [(14, 15), (17, 16), (22, 19), (31, 24), (30, 28), (22, 23), (15, 18)], R3)
    # covert rows: short black ticks, one per feather
    for x, y in [(16, 10), (21, 12), (26, 15)]:
        line(w, x, y, x - 1, y + 2)
    for x, y in [(18, 16), (24, 20)]:
        line(w, x, y, x - 1, y + 2)
    line(w, 22, 15, 32, 22)
    # feather edges: mid red on the shaded band, shade on the mid band
    for x, y in [(19, 18), (22, 20), (25, 22), (28, 24)]:
        line(w, x, y, x + 1, y + 1, R2)
    for x, y in [(17, 11), (22, 13), (27, 17)]:
        line(w, x, y, x + 1, y + 1, R3)
    # a bright pip on each upper covert
    for x, y in [(14, 12), (19, 14)]:
        line(w, x, y, x + 1, y, R1)
    return w


im = canvas(72, 48)

# ---- dugong, under everything: fat, round, drooping snout ----
poly(im, [(19, 37), (22, 35), (30, 33), (42, 34), (50, 37), (55, 41), (55, 44), (48, 46), (34, 47), (24, 46), (20, 45), (16, 45), (15, 42), (16, 39)], GL)
# belly shade
poly(im, [(21, 44), (28, 44), (38, 45), (48, 43), (55, 42), (55, 44), (48, 46), (34, 47), (24, 46)], GD)
# tail fluke, two wide lobes
poly(im, [(54, 41), (60, 39), (63, 38), (62, 41), (58, 43)], GL)
poly(im, [(54, 43), (58, 43), (63, 46), (62, 47), (57, 46), (54, 45)], GD)
line(im, 56, 42, 59, 43)
# broad snout, mouth, tusk, eye
line(im, 16, 43, 20, 43)
dot(im, 18, 44, C)
dot(im, 18, 45, C)
dot(im, 22, 38, K)
dot(im, 23, 38, K)
line(im, 25, 36, 26, 40)                    # neck fold
# flipper
poly(im, [(26, 42), (31, 41), (31, 45), (28, 47), (25, 46)], GD)
line(im, 25, 42, 31, 40)
# back crease, hide wrinkles and a darker flank stripe
line(im, 45, 37, 49, 40)
line(im, 46, 41, 53, 42, GD)
line(im, 18, 40, 21, 40, GD)
line(im, 42, 40, 43, 43, GD)
line(im, 49, 37, 51, 39, GD)

# ---- wings ----
stamp(im, wing(True), 0, 0)
stamp(im, wing(False).transpose(Image.FLIP_LEFT_RIGHT), 36, 0)

# ---- tail, between the legs ----
poly(im, [(32, 30), (40, 30), (39, 38), (36, 40), (33, 38)], R3)
line(im, 36, 34, 36, 39)

# ---- body ----
oval(im, 28, 15, 16, 18, R2)
poly(im, [(28, 21), (30, 17), (32, 16), (32, 22), (30, 30)], R1)
poly(im, [(40, 17), (43, 20), (43, 27), (40, 32), (39, 28)], R3)
# cream bib, wide at the top, coming to a point
poly(im, [(31, 20), (41, 20), (41, 23), (38, 26), (36, 28), (34, 26), (31, 23)], C)
# bib feather notches
line(im, 33, 22, 34, 23, G)
line(im, 38, 23, 39, 22, G)
dot(im, 36, 25, G)
# belly chevrons
line(im, 32, 28, 34, 30)
line(im, 40, 28, 38, 30)
line(im, 35, 30, 36, 31, R3)
line(im, 37, 30, 36, 31, R3)

# ---- thighs, legs, talons ----
for x, flip in ((29, 0), (38, 1)):
    poly(im, [(x, 28), (x + 5, 28), (x + 5, 32), (x + 3, 34), (x + 1, 33)], R2 if not flip else R3)
    line(im, x + (0 if flip else 5), 29, x + (0 if flip else 5), 32)
    rect(im, x + 1, 34, 3, 3, G)
    rect(im, x + 3, 34, 1, 3, BR)
    # toes hooked over the dugong
    rect(im, x - 1, 37, 7, 2, G)
    for tx in (x - 1, x + 2, x + 5):
        rect(im, tx, 39, 1, 3, G)
        dot(im, tx, 41, BR)
    dot(im, x + 1, 39, K)
    dot(im, x + 4, 39, K)

# ---- head, turned to the viewer's left ----
oval(im, 29, 3, 14, 13, R2)
poly(im, [(31, 5), (34, 3), (39, 3), (40, 5), (35, 6), (32, 8)], R1)
poly(im, [(39, 7), (42, 7), (42, 12), (39, 15)], R3)
# ruff under the head, jagged lower edge
poly(im, [(31, 13), (41, 13), (41, 16), (39, 18), (37, 16), (35, 18), (33, 16), (31, 18)], R3)
line(im, 33, 18, 35, 18)
line(im, 37, 18, 39, 18)
# beak: heavy hook, gold, shade below
poly(im, [(33, 7), (29, 7), (26, 9), (25, 12), (25, 14), (27, 13), (29, 12), (33, 12)], G)
poly(im, [(28, 13), (33, 13), (33, 15), (29, 15)], BR)
line(im, 28, 12, 33, 12)
line(im, 33, 7, 33, 11)
dot(im, 30, 9, K)
# brow and eye
line(im, 34, 6, 38, 8)
dot(im, 36, 9, C)
dot(im, 37, 9, C)

im = outline(im)
save(im)
