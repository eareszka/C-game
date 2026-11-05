from pix import *

LT, MD, SH, UM = 'a4aaba', '848694', '595965', '474751'   # four greys, lit to shadowed
RL, RM, RD = 'b6433d', '792727', '531b1c'                 # red binding
K = '000000'

W, H = 268, 150
im = canvas(W, H)
d = ImageDraw.Draw(im)


def line(pts, c=K):
    d.line(pts, fill=rgba(c))


def fill(pts, c):
    d.polygon(pts, fill=rgba(c))


def edge(pts):
    d.polygon(pts, outline=rgba(K))


def part(pts, c):
    d.polygon(pts, fill=rgba(c), outline=rgba(K))


def crack(pts, lip=True):
    # a black split, with a lit lip on its right side where the stone has shifted
    if lip:
        line([(x + 1, y) for x, y in pts], LT)
    line(pts)


def foot(xl, xr, y, s, n):
    h1, h2, h3 = round(13 * s), round(8 * s), round(15 * s)
    fl, fr = xl - round(8 * s), xr + round(8 * s)
    tw = (fr - fl) / n
    top = y + h1
    # claws first, so the toes sit over their roots
    for i in range(n):
        a = fl + round(i * tw)
        b = fl + round((i + 1) * tw)
        c = (a + b) // 2
        mid = c + round((i - (n - 1) / 2) * 5 * s)
        by = top + h2 - 2
        tip = by + h3
        shape = [(a + 1, by), (b - 1, by), (mid, tip)]
        fill(shape, MD)
        fill([(a + 1, by), (a + max(2, round(4 * s)), by), (mid, tip)], LT)
        fill([(c + 1, by), (b - 1, by), (mid, tip)], SH)
        edge(shape)
    # ankle block
    outer = [(xl, y), (xr, y), (fr, top), (fl, top)]
    fill(outer, MD)
    fill([(xl + round((xr - xl) * .72), y), (xr, y), (fr, top), (fl + round((fr - fl) * .74), top)], SH)
    fill([(xl, y), (xl + max(2, round(5 * s)), y), (fl + max(3, round(9 * s)), top), (fl, top)], LT)
    edge(outer)
    # plinth ledge across the ankle
    ly = y + max(2, round(4 * s))
    line([(xl - round(2 * s), ly), (xr + round(2 * s), ly)])
    # toes
    for i in range(n):
        a = fl + round(i * tw)
        b = fl + round((i + 1) * tw)
        c = max(1, round(2 * s))
        toe = [(a, top), (b, top), (b, top + h2 - c), (b - c, top + h2), (a + c, top + h2), (a, top + h2 - c)]
        fill(toe, MD)
        sx = b - max(2, round((b - a) * .3))
        rect(im, sx, top + 1, b - sx, h2 - c, SH)
        rect(im, a + 1, top + 1, max(1, round((b - a) * .25)), max(1, h2 - c - 1), LT)
        edge(toe)
        if i:
            line([(a, top), (a + round(i - (n - 1) / 2), top - round(6 * s))])


def shaft(cx, ytop, ybot, w0, w1):
    xl0, xr0 = cx - w0 // 2, cx + w0 // 2
    xl1, xr1 = cx - w1 // 2, cx + w1 // 2
    outer = [(xl0, ytop), (xr0, ytop), (xr1, ybot), (xl1, ybot)]
    fill(outer, MD)
    # right face in shade, split from the front by a hard ridge
    r0, r1 = xl0 + round(w0 * .70), xl1 + round(w1 * .70)
    fill([(r0, ytop), (xr0, ytop), (xr1, ybot), (r1, ybot)], SH)
    line([(r0, ytop), (r1, ybot)])
    # lit left edge
    e = max(2, w0 // 9)
    fill([(xl0, ytop), (xl0 + e, ytop), (xl1 + e, ybot), (xl1, ybot)], LT)
    edge(outer)
    return xl1, xr1


def binding(cx, y0, n, sh, hw, sag):
    px = im.load()
    bulge = [0, 1, 2, 2, 1, 0, 1, 2]
    ticks = []
    for i in range(n):
        w = hw + bulge[i]
        for x in range(cx - w, cx + w + 1):
            if not 0 <= x < W:
                continue
            t = (x - cx) / w
            yy = y0 + i * sh + round(sag * (1 - t * t))
            base = RD if t > .6 else RM
            hi = RD if t > .6 else (RM if t > .25 else RL)
            rect(im, x, yy, 1, sh, base)
            rect(im, x, yy, 1, max(1, sh // 2), hi)
            # the twist of the rope: uneven dark ticks, so it never reads as brick
            if (x - cx + i * 13) % 37 in (0, 16, 23):
                ticks.append((x, yy))
            # dark seam between coils, black only where two bundles meet
            rect(im, x, yy + sh - 1, 1, 1, K if i in (1, n - 1) else RD)
            if i == n - 1:
                # the binding's shadow falls on the stone below
                for k in range(sh, sh + 4):
                    if 0 <= yy + k < H and px[x, yy + k][3] and px[x, yy + k][:3] != (0, 0, 0):
                        px[x, yy + k] = rgba(SH)
    # each tick leans, drawn over the finished coils so the slant survives
    for x, yy in ticks:
        for r in range(sh - 1):
            tx = x + 1 - r
            if 0 <= tx < W:
                px[tx, yy + r] = rgba(RD)
    # one strap lashed across the coils, tied off with a knot
    by = y0 + n * sh + sag - 2
    a, b = cx - hw // 2, cx + hw // 3
    u = max(3, sh - 1)
    strap = [(a, y0 + sag + sh), (a + u + 1, y0 + sag + sh), (b + u + 1, by), (b, by)]
    fill(strap, RL)
    fill([(a + u - 1, y0 + sag + sh), (a + u + 1, y0 + sag + sh), (b + u + 1, by), (b + u - 1, by)], RM)
    edge(strap)
    kx, ky = (a + b) // 2 + u // 2, (y0 + sag + sh + by) // 2
    knot = [(kx - u, ky - u + 1), (kx + u, ky - u), (kx + u + 1, ky + u - 1), (kx - u + 1, ky + u)]
    fill(knot, RM)
    fill([(kx - u, ky - u + 1), (kx + u, ky - u), (kx, ky)], RL)
    edge(knot)


def stone_detail(xl0, xr0, xl1, xr1, ytop, ybot, s):
    # chipped flakes down the shaded face, and breaks in the lit edge
    span = ybot - ytop
    for f in (.18, .33, .47, .62, .78, .9):
        y = ytop + round(span * f)
        k = (y - ytop) / span
        xr = round(xr0 + (xr1 - xr0) * k)
        wid = max(3, round((7 if round(f * 100) % 2 else 4) * s))
        hgt = max(3, round((8 if round(f * 100) % 3 else 5) * s))
        fill([(xr - 1, y), (xr - 1, y + hgt), (xr - wid, y + hgt // 2)], UM)
    for f in (.26, .55, .84):
        y = ytop + round(span * f)
        k = (y - ytop) / span
        xl = round(xl0 + (xl1 - xl0) * k)
        hgt = max(2, round(4 * s))
        fill([(xl + 1, y), (xl + max(3, round(6 * s)), y + hgt // 2), (xl + 1, y + hgt)], MD)
        line([(xl + 1, y + hgt + 1), (xl + max(3, round(5 * s)), y + hgt + 1)], SH)
    # short course lines where the pillar's blocks meet
    for f, a0, a1 in ((.42, .36, .62), (.7, .14, .34), (.87, .42, .66)):
        y = ytop + round(span * f)
        k = (y - ytop) / span
        xl = xl0 + (xl1 - xl0) * k
        wd = (xr0 + (xr1 - xr0) * k) - xl
        line([(round(xl + wd * a0), y), (round(xl + wd * a1), y)], SH)


def lumps(rows, c, dy):
    pts = [(4, 6)]
    for x0, x1, y in rows:
        pts += [(x0, y - 4 + dy), (x0 + 3, y - 1 + dy), (x1 - 3, y + dy), (x1, y - 4 + dy)]
    pts += [(W - 1, 0)]
    fill(pts, c)


# ---- underside, behind everything
rows = [(9, 22, 40), (20, 44, 46), (44, 66, 46), (64, 74, 50), (72, 84, 44), (82, 96, 49), (94, 120, 46), (120, 142, 46),
        (140, 152, 49), (150, 162, 43), (160, 170, 47), (170, 190, 44), (190, 202, 44), (200, 210, 46), (208, 220, 40),
        (218, 226, 44), (226, 246, 40), (246, 258, 37), (256, 268, 34)]
lumps(rows, UM, 0)
for x0, x1, y in rows:
    line([(x1, y - 4), (x1 - 2, y - 9), (x1 + 1, y - 14)])
    line([(x0 + 3, y - 4), (x1 - 4, y - 5)], SH)
    line([(x0 + 4, y - 9), ((x0 + x1) // 2, y - 10)], SH)
# red veins through the split hide
for pts in ([(14, 26), (14, 32), (11, 38)], [(14, 32), (16, 36)],
            [(74, 22), (74, 30), (78, 35), (78, 42)], [(74, 30), (70, 36)],
            [(91, 22), (91, 32), (88, 38)], [(91, 30), (94, 35), (94, 40)],
            [(161, 22), (161, 30), (158, 36)], [(161, 28), (165, 33), (165, 38)],
            [(218, 20), (218, 28), (215, 34)], [(218, 27), (222, 32)]):
    line([(x + 1, y) for x, y in pts], RM)
    line(pts, RL)

# ---- legs, back to front
LEGS = [
    # cx, binding top, coils, coil height, half width, sag, shaft w top, w bottom, shaft end, foot scale, toes
    (265, 20, 5, 4, 11, 3, 22, 26, 60, .5, 3),
    (236, 27, 5, 4, 15, 3, 24, 30, 80, .62, 3),
    (186, 30, 5, 5, 19, 4, 30, 37, 92, .8, 4),
    (44, 27, 6, 5, 25, 5, 42, 50, 100, 1, 4),
    (120, 31, 6, 5, 26, 5, 44, 52, 110, 1, 4),
]
CRACKS = {
    265: [[(258, 44), (261, 50), (259, 56)]],
    236: [[(230, 48), (233, 54), (229, 60), (231, 66), (236, 70)], [(233, 54), (238, 58), (241, 56)],
          [(226, 72), (231, 66)], [(236, 70), (235, 78)]],
    186: [[(192, 54), (188, 62), (191, 70), (186, 76), (178, 80)], [(191, 70), (197, 74), (199, 82)],
          [(188, 62), (180, 60)], [(186, 76), (187, 88)], [(178, 80), (173, 78)]],
    44: [[(40, 58), (44, 66), (40, 74), (48, 82), (52, 92)], [(44, 66), (54, 72), (58, 68)],
         [(40, 74), (30, 78), (28, 86)], [(48, 82), (42, 90), (44, 98)], [(30, 78), (25, 76)], [(54, 72), (56, 80)]],
    120: [[(116, 62), (112, 72), (118, 80), (112, 90), (116, 100), (112, 108)], [(118, 80), (130, 86), (134, 94)],
          [(112, 72), (102, 76), (100, 84)], [(112, 90), (104, 96)], [(130, 86), (132, 74)], [(116, 100), (124, 106)]],
}
# shifted slabs of stone beside the main cracks
CHIPS = {
    236: [[(233, 54), (238, 58), (236, 70), (231, 66)]],
    186: [[(191, 70), (197, 74), (199, 82), (187, 88), (186, 76)]],
    44: [[(44, 66), (54, 72), (56, 80), (48, 82), (40, 74)], [(30, 78), (40, 74), (42, 90), (28, 86)]],
    120: [[(118, 80), (130, 86), (134, 94), (116, 100), (112, 90)], [(102, 76), (112, 72), (112, 90), (104, 96), (100, 84)]],
}
# bites out of the shaft's edge
NOTCH = {
    44: [[(18, 80), (24, 83), (18, 88)], [(70, 76), (66, 80), (70, 86)]],
    120: [[(92, 88), (98, 92), (92, 98)], [(148, 70), (143, 75), (148, 82)]],
    186: [[(166, 76), (171, 79), (166, 84)], [(206, 66), (202, 70), (206, 76)]],
    236: [[(218, 62), (222, 65), (218, 70)]],
}
for cx, y0, n, sh, hw, sag, w0, w1, yb, s, toes in LEGS:
    xl, xr = shaft(cx, y0 + 8, yb, w0, w1)
    stone_detail(cx - w0 // 2, cx + w0 // 2, xl, xr, y0 + 8, yb, s)
    for pts in CHIPS.get(cx, []):
        fill(pts, SH)
        line(pts[:2], LT)
    for pts in CRACKS[cx]:
        crack(pts)
    foot(xl, xr, yb, s, toes)
    binding(cx, y0, n, sh, hw, sag)
    for pts in NOTCH.get(cx, []):
        d.polygon(pts, fill=CLEAR)

# ---- jagged stone belly
top = 3
back = [(2, 22, 8, 36), (20, 50, 34, 32), (44, 78, 62, 40), (72, 100, 86, 34), (94, 128, 108, 44),
        (122, 150, 138, 38), (144, 176, 160, 42), (170, 196, 182, 34), (190, 222, 208, 40),
        (216, 240, 226, 32), (234, 267, 252, 36)]
front = [(0, 30, 11, 22), (26, 58, 40, 18), (52, 86, 70, 26), (80, 112, 92, 16), (106, 140, 124, 24),
         (134, 166, 148, 18), (160, 190, 178, 26), (184, 214, 196, 16), (208, 238, 224, 24), (232, 267, 248, 19)]
for x0, x1, tx, ty in back:
    p = [(x0, top), (x1, top), (tx, ty)]
    fill(p, MD)
    fill([((x0 + x1) // 2 + 3, top), (x1, top), (tx, ty)], SH)
    # a chipped facet near the tip
    fill([(tx - 3, ty - 9), (tx, ty - 12), (tx, ty)], SH)
    # a lit flake and a deep split on each plate
    fill([(x0 + 5, top + 3), (x0 + 10, top + 3), (tx - 3, ty - 14)], LT)
    fill([(x1 - 6, top + 2), (x1 - 2, top + 2), (tx + 3, ty - 12)], UM)
    line([(tx + 1, ty - 16), (tx + 3, ty - 10), (tx + 1, ty - 6)])
    edge(p)
for x0, x1, tx, ty in front:
    p = [(x0, top), (x1, top), (tx, ty)]
    fill(p, MD)
    fill([((x0 + x1) // 2 + 2, top), (x1, top), (tx, ty)], SH)
    fill([(x0, top), (x0 + 7, top), (tx, ty)], LT)
    fill([(x1 - 5, top + 2), (x1 - 2, top + 2), (tx + 3, ty - 6)], UM)
    line([(tx - 2, ty - 10), (tx - 1, ty - 5)])
    edge(p)
# flat top slab with a broken lower edge
slab = [(0, 0), (W - 1, 0), (W - 1, 8), (240, 9), (232, 5), (210, 11), (196, 6), (170, 12), (150, 7), (128, 13), (112, 8),
        (84, 12), (64, 6), (40, 11), (24, 6), (0, 8)]
fill(slab, LT)
# darker chips along the slab's lower lip
for x0, x1, y in ((12, 30, 5), (46, 60, 7), (92, 110, 7), (132, 148, 6), (176, 192, 6), (214, 230, 6), (246, 264, 6)):
    fill([(x0, y + 2), (x1, y), (x1 - 4, y + 3)], MD)
edge(slab)
line([(150, 7), (154, 0)])
line([(64, 6), (60, 0)])
line([(210, 11), (214, 3)])
line([(112, 8), (108, 2)])

im = strip_outline(im)
im = outline(im)
save(im)
