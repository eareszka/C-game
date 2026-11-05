from pix import *

W, H = 49, 38
DK, MD, LT = '2850a0', '5c94fc', '84a7e9'      # fish blue
BD, BR = '633e1b', '94703d'                    # ox brown
MZ = 'd7a175'                                  # muzzle
HL, HD = 'e8e0c0', 'b29e5c'                    # horn


def spans(im, rows, colour):
    for y, a, b in rows:
        rect(im, a, y, b - a + 1, 1, colour)


def over(im, part):
    """Lay a part on im, with a black line wherever it borders something already drawn."""
    src, dst = part.load(), im.load()
    for y in range(H):
        for x in range(W):
            if src[x, y][3]:
                continue
            if dst[x, y][3] and any(0 <= x + a < W and 0 <= y + b < H and src[x + a, y + b][3]
                                    for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                dst[x, y] = BLACK
    im.alpha_composite(part)


def flip(rows):
    return [(y, 65 - b, 65 - a) for y, a, b in rows]


im = canvas(W, H)

# tail, upper and lower lobes
tail = canvas(W, H)
up = [(9, 0, 0), (10, 0, 1), (11, 0, 1), (12, 1, 2), (13, 1, 3), (14, 2, 3), (15, 2, 4),
      (16, 3, 5), (17, 3, 6), (18, 4, 7), (19, 4, 8)]
lo = [(42 - y, a, b) for y, a, b in up]
spans(tail, up, MD)
spans(tail, lo, DK)
spans(tail, [(12, 1, 1), (13, 1, 1), (14, 2, 2), (15, 2, 2), (16, 3, 3), (17, 3, 3)], LT)
spans(tail, [(30, 1, 1), (29, 1, 1), (28, 2, 2), (27, 2, 2), (26, 3, 3)], MD)
im.alpha_composite(tail)

# dorsal and belly fins
fin = canvas(W, H)
spans(fin, [(6, 13, 13), (7, 13, 14), (8, 13, 15), (9, 14, 16), (10, 14, 17), (11, 15, 18),
            (12, 15, 20), (13, 16, 21), (14, 16, 21)], MD)
spans(fin, [(8, 13, 13), (9, 14, 14), (10, 14, 14), (11, 15, 15), (12, 15, 15)], LT)
spans(fin, [(10, 17, 17), (11, 18, 18), (12, 19, 20)], DK)
spans(fin, [(29, 15, 21), (30, 14, 20), (31, 14, 18), (32, 13, 17), (33, 13, 16),
            (34, 13, 15), (35, 13, 14), (36, 13, 13)], DK)
spans(fin, [(31, 14, 14), (32, 13, 13), (33, 13, 13), (34, 13, 13)], MD)
im.alpha_composite(fin)

# fish body
body = canvas(W, H)
rows = [(13, 17, 26), (14, 14, 26), (15, 12, 26), (16, 10, 26), (17, 8, 26), (18, 7, 26),
        (19, 6, 26), (20, 5, 26), (21, 5, 26), (22, 6, 26), (23, 7, 26), (24, 8, 26),
        (25, 9, 26), (26, 11, 26), (27, 13, 26), (28, 15, 26), (29, 18, 26)]
spans(body, rows, MD)
# lit back
spans(body, [(14, 15, 22), (15, 13, 20), (16, 11, 17), (17, 9, 13)], LT)
# pale side stripe, then shaded belly
spans(body, [(20, 8, 24), (21, 8, 24)], LT)
spans(body, [(24, 8, 26), (25, 9, 26), (26, 11, 26), (27, 13, 26), (28, 15, 26), (29, 18, 26)], DK)
spans(body, [(22, 6, 26), (23, 7, 26)], MD)
over(im, body)

# body line work: gill arc, stripe edge, scale ticks
for x, y in [(21, 15), (22, 16), (22, 17), (23, 18), (23, 19), (23, 20), (23, 21),
             (23, 22), (23, 23), (22, 24), (22, 25), (21, 26), (21, 27)]:
    dot(im, x, y, BLACK)
for x, y in [(9, 22), (12, 22), (15, 22), (18, 22), (11, 19), (14, 19), (17, 19), (20, 19),
             (13, 17), (16, 17), (19, 17)]:
    dot(im, x, y, BLACK)

# side fin
side = canvas(W, H)
spans(side, [(24, 17, 21), (25, 15, 20), (26, 14, 19), (27, 14, 17), (28, 14, 15)], MD)
spans(side, [(26, 16, 19), (27, 16, 17)], DK)
over(im, side)

# horns
horn = canvas(W, H)
left = [(0, 17, 17), (1, 17, 18), (2, 17, 18), (3, 17, 18), (4, 17, 19), (5, 17, 19), (6, 18, 20),
        (7, 18, 21), (8, 19, 22), (9, 20, 24), (10, 21, 26), (11, 23, 28), (12, 24, 28)]
spans(horn, left, HL)
spans(horn, flip(left), HL)
spans(horn, [(3, 18, 18), (5, 19, 19), (6, 20, 20), (7, 21, 21), (8, 22, 22), (9, 23, 24),
             (10, 25, 26), (11, 27, 28), (12, 27, 28)], HD)
spans(horn, [(1, 48, 48), (2, 48, 48), (3, 48, 48), (4, 47, 48), (5, 47, 48), (6, 46, 47),
             (7, 45, 47), (8, 44, 46), (9, 42, 45), (10, 40, 44), (11, 38, 42), (12, 37, 41)], HD)
over(im, horn)

# ears
ear = canvas(W, H)
el = [(13, 20, 22), (14, 18, 23), (15, 18, 23), (16, 19, 23), (17, 21, 23)]
spans(ear, el, BR)
spans(ear, flip(el), BR)
spans(ear, [(15, 20, 22), (16, 21, 22)], BD)
spans(ear, [(15, 43, 46), (16, 43, 45), (14, 45, 47), (17, 43, 44)], BD)
over(im, ear)

# head
head = canvas(W, H)
hd = [(9, 26, 39), (10, 25, 40), (11, 24, 41), (12, 23, 42), (13, 23, 42), (14, 23, 42),
      (15, 23, 42), (16, 23, 42), (17, 24, 41), (18, 24, 41), (19, 24, 41), (20, 24, 41),
      (21, 24, 41), (22, 24, 41)]
spans(head, hd, BR)
# dark crown, cut with a forelock, and shaded right side
spans(head, [(9, 26, 39), (10, 25, 40), (11, 27, 41), (12, 29, 42), (13, 30, 35), (14, 31, 34),
             (15, 32, 33)], BD)
spans(head, [(9, 28, 30), (10, 27, 29)], BR)
for y in range(13, 23):
    rect(head, 40 if y < 17 else 39, y, 3, 1, BD)
over(im, head)

# muzzle
mz = canvas(W, H)
mr = [(20, 26, 39), (21, 25, 40), (22, 23, 42), (23, 22, 43), (24, 22, 43), (25, 22, 43),
      (26, 22, 43), (27, 22, 43), (28, 23, 42), (29, 24, 41), (30, 26, 39), (31, 28, 37)]
spans(mz, mr, MZ)
spans(mz, [(29, 36, 41), (30, 33, 39), (31, 30, 37), (28, 40, 42), (27, 42, 43), (26, 43, 43)], BR)
over(im, mz)

# eyes and brows
rect(im, 28, 16, 2, 2, BLACK)
rect(im, 36, 16, 2, 2, BLACK)
spans(im, [(14, 27, 29), (15, 28, 29)], BD)
spans(im, [(14, 36, 38), (15, 36, 37)], BD)

# nostrils and mouth
rect(im, 27, 24, 3, 2, BLACK)
rect(im, 36, 24, 3, 2, BLACK)
spans(im, [(26, 28, 28), (26, 37, 37)], BR)
spans(im, [(28, 28, 37)], BLACK)
dot(im, 27, 27, BLACK)
dot(im, 38, 27, BLACK)

im = outline(im)
save(im)
