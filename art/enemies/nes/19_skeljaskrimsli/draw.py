from pix import *

W, H = 60, 48
im = canvas(W, H)

S_HI, S_MID, S_LO = 'bcbeca', '848694', '595965'
H_MID = '474751'
G_HI, G_MID, G_DK = 'a8f0bc', '4fa667', '163623'


def mask_of(points):
    m = canvas(W, H)
    poly(m, points, 'ffffff')
    p = m.load()
    return {(x, y) for y in range(H) for x in range(W) if p[x, y][3]}


def part(cells, shade, seam=True):
    """Lay a part down, by default with a black seam on what it covers. shade(x, y) gives the colour."""
    px = im.load()
    for x, y in cells if seam else ():
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + a, y + b)
            if n in cells or not (0 < n[0] < W - 1 and 0 < n[1] < H - 1):
                continue
            if px[n][3] and all(px[n[0] + c, n[1] + d][3] for c, d in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[n] = BLACK
    for x, y in cells:
        dot(im, x, y, shade(x, y))


def hide(cells):
    def shade(x, y):
        if (x - 1, y) not in cells or (x, y - 1) not in cells:
            return S_LO
        return H_MID
    return shade


def toes(spots):
    for x, y in spots:
        rect(im, x, y, 3, 2, S_MID)
        dot(im, x, y, S_HI)
        dot(im, x + 1, y, S_HI)
        rect(im, x + 2, y + 1, 1, 1, S_LO)


# far legs, set back under the shell and ending higher up
for pts, feet in (([(30, 32), (38, 32), (38, 41), (31, 41)], [(30, 42), (34, 42)]),
                  ([(52, 30), (58, 30), (58, 41), (53, 41)], [(52, 42), (56, 42)])):
    c = mask_of(pts)
    part(c, hide(c))
    toes(feet)

# belly under the shell
c = mask_of([(20, 28), (57, 28), (55, 36), (24, 37)])
part(c, hide(c))

# near hind leg
c = mask_of([(40, 32), (50, 32), (51, 39), (50, 45), (41, 45), (40, 39)])
part(c, hide(c))
toes([(39, 46), (43, 46), (47, 46)])

# near front leg
c = mask_of([(13, 36), (27, 36), (27, 45), (15, 45)])
part(c, hide(c))
toes([(13, 46), (17, 46), (21, 46)])

# the shell: stone plates, split into cells round hand-placed centres
shell = mask_of([(2, 25), (3, 18), (6, 12), (10, 7), (15, 4), (21, 2), (30, 1), (37, 2),
                 (43, 5), (49, 9), (53, 13), (56, 18), (58, 24), (59, 31), (56, 33),
                 (50, 31), (44, 33), (38, 31), (33, 33), (30, 28), (20, 21), (8, 20)])
# each crown plate stands one step proud of the rim
for x0, x1 in ((7, 11), (17, 24), (28, 36), (41, 47), (50, 53)):
    for x in range(x0, x1):
        top = min(y for a, y in shell if a == x)
        shell.add((x, top - 1))
seeds = [(10, 14), (20, 7), (32, 6), (43, 10), (52, 18), (55, 28),
         (5, 22), (19, 17), (30, 17), (40, 20), (48, 27), (37, 29)]


def owner(x, y):
    return min(range(len(seeds)), key=lambda i: (seeds[i][0] - x) ** 2 + (seeds[i][1] - y) ** 2)


own = {p: owner(*p) for p in shell}

# notch the silhouette where two plates meet, so the rim is knobbly
for p in list(shell):
    x, y = p
    edge = any((x + a, y + b) not in shell for a, b in ((1, 0), (-1, 0), (0, -1)))
    seam = any((x + a, y + b) in own and own[(x + a, y + b)] != own[p] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    if edge and seam and y < 28:
        shell.discard(p)
own = {p: own[p] for p in shell}


def differs(x, y, me):
    return own.get((x, y), -1) != me


def stone(x, y):
    me = own[(x, y)]
    # seam on the lower right side of each plate
    for a, b in ((1, 0), (0, 1)):
        n = (x + a, y + b)
        if n in own and own[n] != me:
            return (0, 0, 0)
    sx, sy = seeds[me]
    far = sx + sy > 66   # plates low on the right sit in shade
    top = differs(x, y - 1, me) or differs(x - 1, y, me)
    top2 = differs(x, y - 2, me)
    low = differs(x + 1, y + 1, me) or differs(x + 2, y, me) or differs(x, y + 2, me)
    if low:
        return S_LO
    if top and not far:
        return S_HI
    if top2 and sx + sy < 36:
        return S_HI
    if far and top:
        return S_MID
    return S_LO if far and x + y > 80 else S_MID


part(shell, stone)

# cracks chipped into the plates, with a lit edge on the crown plates
px = im.load()
for colour, spots in ((S_LO, [(22, 9), (23, 10), (24, 10), (30, 7), (31, 8), (31, 9), (44, 11), (45, 12), (46, 12),
                              (12, 14), (12, 15), (13, 16), (20, 15), (21, 16), (21, 17), (32, 15), (33, 16), (34, 16),
                              (41, 19), (41, 20), (42, 21), (52, 17), (53, 18), (53, 19), (48, 25), (49, 26), (49, 27)]),
                      (S_HI, [(21, 9), (22, 8), (29, 7), (30, 6), (43, 11), (44, 10), (11, 14), (11, 15)])):
    for x, y in spots:
        if px[x, y] == rgba(S_MID):
            px[x, y] = rgba(colour)

# the head: all mouth
head = mask_of([(0, 28), (2, 23), (7, 20), (15, 18), (24, 19), (30, 22), (32, 28), (30, 35),
                (25, 39), (16, 42), (8, 41), (3, 37)])
part(head, hide(head))

mouth = mask_of([(2, 27), (6, 23), (15, 21), (24, 22), (29, 26), (30, 29), (27, 34), (20, 39), (10, 39), (5, 35)])
inner = mask_of([(5, 28), (8, 25), (15, 24), (23, 25), (27, 28), (27, 29), (24, 33), (19, 36), (11, 36), (7, 34)])


def lip(x, y):
    if (x - 1, y) not in mouth or (x, y - 1) not in mouth:
        return G_HI
    return G_MID


part(mouth, lip, seam=False)
part(inner, lambda x, y: G_DK, seam=False)


def column(x, want):
    ys = [y for a, y in inner if a == x]
    return want(ys)


# upper teeth hang from the gum, lower teeth stand on it
for x, h in ((7, 3), (11, 5), (15, 5), (19, 5), (23, 3)):
    y0 = min(column(x, min), column(x + 2, min))
    for i in range(h):
        if i < h - 2:
            rect(im, x, y0 + i, 3, 1, G_HI)
            dot(im, x + 2, y0 + i, G_MID)
        else:
            dot(im, x + 1, y0 + i, G_HI)
for x, h in ((9, 3), (13, 4), (17, 4), (21, 3)):
    y0 = max(column(x, max), column(x + 2, max))
    for i in range(h):
        if i < h - 2:
            rect(im, x, y0 - i, 3, 1, G_HI)
            dot(im, x + 2, y0 - i, G_MID)
        else:
            dot(im, x + 1, y0 - i, G_HI)

# hide folds on the legs that stand clear of the head
rect(im, 43, 37, 5, 1, S_LO)
rect(im, 44, 41, 5, 1, S_LO)
rect(im, 33, 38, 3, 1, S_LO)
rect(im, 54, 37, 3, 1, S_LO)

im = outline(im)
save(im)
