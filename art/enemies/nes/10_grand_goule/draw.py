from pix import *

W, H = 90, 84
L, M, D = '5c94fc', '2850a0', '301b5a'   # blue hide
MEM = '595965'                           # wing skin (folds use D)
T, TD = 'b2966a', '8d6b4f'               # tan chest
G, R = 'f0bc3c', 'b70000'                # gold, red

im = canvas(W, H)
ids = canvas(W, H)
count = [0]


def part(pts, c):
    """A new part: filled, and black-lined later where it meets other parts."""
    count[0] += 1
    n = count[0]
    poly(im, pts, c)
    poly(ids, pts, (n, 0, 0))
    return n


def shade(pts, c, n=None):
    """A tone inside a part: clipped to that part, no line round it."""
    n = n or count[0]
    tmp = canvas(W, H)
    poly(tmp, pts, c)
    a, b, i = tmp.load(), im.load(), ids.load()
    for y in range(H):
        for x in range(W):
            if a[x, y][3] and i[x, y][3] and i[x, y][0] == n:
                b[x, y] = a[x, y]


def seams():
    i, b = ids.load(), im.load()
    hits = []
    for y in range(H):
        for x in range(W):
            if not i[x, y][3]:
                continue
            for dx, dy in ((1, 0), (0, 1)):
                xx, yy = x + dx, y + dy
                if xx < W and yy < H and i[xx, yy][3] and i[xx, yy][0] != i[x, y][0]:
                    hits.append((x, y) if i[x, y][0] < i[xx, yy][0] else (xx, yy))
    for p in hits:
        b[p] = BLACK


def sym(pts):
    return pts + [(W - 1 - x, y) for x, y in reversed(pts)]


def flipper(s):
    return (lambda pts: pts) if s == 0 else (lambda pts: [(W - 1 - x, y) for x, y in pts])


def wing(s):
    F = flipper(s)
    # skin, with deep scallops between the finger tips
    part(F([(20, 6), (12, 8), (5, 15), (1, 26), (0, 40), (0, 60), (2, 53), (5, 51), (7, 53), (9, 63),
            (11, 54), (14, 52), (17, 54), (19, 65), (21, 56), (25, 51), (29, 46), (34, 39), (36, 24)]), MEM)
    # thin fold shadow beside each finger, leaving most of the skin slate
    shade(F([(14, 12), (8, 20), (5, 29), (4, 40), (5, 52), (6, 52), (6, 40), (7, 29), (10, 21), (16, 13)]), D)
    shade(F([(20, 11), (14, 26), (12, 40), (12, 53), (14, 52), (13, 40), (15, 27), (21, 12)]), D)
    shade(F([(24, 12), (22, 27), (21, 42), (21, 56), (23, 53), (22, 42), (24, 27), (25, 13)]), D)

    # fingers, painted into the skin so no black doubles up round them
    shade(F([(20, 8), (11, 24), (8, 39), (9, 63), (10, 39), (12, 25), (21, 10)]), M)
    if s == 0:
        shade([(20, 8), (11, 24), (8, 39), (9, 63), (8, 39), (11, 25), (20, 9)], L)
    shade(F([(21, 9), (18, 26), (17, 42), (19, 65), (19, 42), (20, 27), (23, 11)]), M)
    if s == 0:
        shade([(21, 9), (18, 26), (17, 42), (19, 65), (17, 42), (18, 27), (21, 10)], L)

    # leading edge of the wing, gold stripes on it
    part(F([(21, 3), (12, 5), (5, 12), (1, 24), (0, 38), (0, 60), (3, 42), (4, 29), (8, 20), (14, 12), (22, 9)]), M)
    if s == 0:
        shade([(21, 3), (12, 5), (5, 12), (1, 24), (0, 38), (0, 60), (1, 40), (2, 27), (6, 15), (13, 7), (22, 5)], L)
    else:
        shade(F([(0, 30), (0, 60), (3, 42), (3, 30)]), D)
    d = ImageDraw.Draw(im)
    for a, b in (((17, 7), (12, 9)), ((9, 12), (5, 17)), ((3, 21), (2, 27)), ((1, 33), (1, 40))):
        shade(F([a, b, (b[0] + 1, b[1] + 1), (a[0] + 1, a[1] + 1)]), G)

    # wrist hook, then the wing arm from shoulder to wrist
    part(F([(19, 4), (15, 0), (23, 3)]), G)
    part(F([(35, 25), (25, 3), (19, 4), (19, 9), (30, 27)]), M)
    shade(F([(30, 27), (19, 9), (19, 4), (21, 4), (32, 26)]), L if s == 0 else M)
    shade(F([(35, 25), (25, 3), (23, 3), (33, 26)]), D if s == 0 else L)


def leg(s):
    F = flipper(s)
    OUT, INN = (L, D) if s == 0 else (D, L)
    for pts in ([(30, 75), (26, 83), (33, 77)], [(34, 76), (34, 84), (38, 76)], [(39, 76), (42, 83), (42, 74)]):
        part(F(pts), R)
    part(F([(32, 63), (33, 72), (39, 73), (40, 69), (37, 61)]), M)
    shade(F([(32, 63), (33, 72), (35, 72), (34, 63)]), OUT)
    shade(F([(40, 69), (39, 73), (38, 73), (38, 62)]), INN if s == 0 else M)
    part(F([(30, 72), (41, 71), (43, 77), (29, 77)]), M)
    shade(F([(30, 72), (41, 71), (41, 73), (30, 74)]), L if s == 0 else M)
    shade(F([(29, 76), (43, 76), (43, 78), (29, 78)]), D)
    part(F([(37, 51), (32, 54), (30, 60), (32, 66), (38, 65), (42, 58)]), M)
    shade(F([(37, 51), (32, 54), (30, 60), (32, 62), (34, 56), (38, 53)]), OUT)
    shade(F([(32, 66), (38, 65), (42, 58), (39, 59), (35, 63)]), INN if s == 0 else D)


def arm(s):
    F = flipper(s)
    OUT, INN = (L, D) if s == 0 else (D, L)
    # talons
    for pts in ([(21, 64), (16, 74), (24, 67)], [(23, 66), (22, 77), (27, 66)], [(27, 64), (31, 74), (30, 63)]):
        part(F(pts), R)
    # hand
    part(F([(22, 59), (29, 59), (30, 65), (22, 67)]), M)
    shade(F([(22, 59), (29, 59), (29, 61), (22, 61)]), L if s == 0 else M)
    shade(F([(22, 65), (30, 64), (30, 68), (22, 68)]), D)
    # forearm, thick at the elbow and narrow at the wrist
    part(F([(23, 43), (28, 42), (30, 48), (29, 58), (23, 58), (21, 48)]), M)
    shade(F([(23, 43), (21, 48), (23, 58), (24, 58), (23, 48), (25, 43)]), OUT)
    shade(F([(28, 42), (30, 48), (29, 58), (28, 58), (28, 48), (27, 42)]), INN)
    # upper arm
    part(F([(33, 29), (27, 30), (22, 42), (25, 46), (30, 44)]), M)
    shade(F([(27, 30), (22, 42), (23, 44), (29, 31)]), OUT)
    shade(F([(33, 29), (30, 44), (28, 45), (31, 30)]), INN)
    # shoulder spur and plate
    part(F([(29, 22), (24, 15), (33, 20)]), G)
    part(F([(38, 26), (33, 21), (28, 22), (25, 28), (27, 34), (33, 33), (38, 30)]), M)
    shade(F([(33, 21), (28, 22), (25, 28), (27, 29), (30, 24), (35, 23)]), L)
    shade(F([(27, 34), (33, 33), (38, 30), (38, 28), (33, 31), (26, 32)]), D)


def horns(s):
    F = flipper(s)
    part(F([(39, 13), (37, 8), (34, 0), (39, 3), (43, 10)]), M)
    shade(F([(34, 0), (39, 3), (39, 5), (36, 5)]), G)
    shade(F([(39, 13), (37, 8), (36, 5), (38, 5), (40, 11)]), L if s == 0 else D)
    part(F([(37, 15), (29, 11), (32, 17), (37, 20)]), M)
    shade(F([(37, 15), (29, 11), (31, 15), (37, 18)]), L if s == 0 else D)


for s in (0, 1):
    wing(s)
for s in (0, 1):
    leg(s)

# torso
part(sym([(38, 26), (33, 33), (32, 43), (35, 52), (38, 58), (44, 62)]), M)
shade([(38, 26), (33, 33), (32, 43), (35, 52), (37, 52), (34, 43), (35, 33), (40, 26)], L)
shade([(W - 39, 26), (W - 34, 33), (W - 33, 43), (W - 36, 52), (W - 38, 52), (W - 35, 43), (W - 36, 33), (W - 41, 26)], D)

# tan chest, jagged at its edge and running up the throat
chest = part(sym([(42, 23), (41, 28), (37, 31), (38, 33), (35, 36), (36, 38), (34, 41), (37, 44), (37, 48), (39, 50),
                  (39, 54), (41, 55), (41, 58), (44, 60)]), T)
for s in (0, 1):
    F = flipper(s)
    shade(F([(34, 41), (37, 44), (43, 46), (43, 44), (38, 42)]), TD, chest)  # under the pec
    shade(F([(38, 48), (43, 49), (43, 50), (39, 50)]), TD, chest)
    shade(F([(40, 53), (43, 53), (43, 55), (41, 55)]), TD, chest)
shade([(W - 42, 30), (W - 38, 33), (W - 35, 41), (W - 39, 42), (W - 41, 36)], TD, chest)  # far pec turns away
shade([(46, 56), (W - 41, 56), (46, 60)], TD, chest)

for s in (0, 1):
    arm(s)
for s in (0, 1):
    horns(s)

# head
part(sym([(40, 10), (37, 14), (36, 19), (38, 24), (41, 28), (43, 31)]), M)
shade([(40, 10), (37, 14), (36, 19), (38, 19), (39, 15), (44, 12), (44, 10)], L)
shade([(W - 37, 19), (W - 39, 24), (W - 42, 28), (W - 44, 28), (W - 41, 24), (W - 39, 19)], D)
shade([(42, 22), (47, 22), (47, 24), (42, 24)], L)  # snout

seams()

# face and chest lines go on last, over the seams
d = ImageDraw.Draw(im)
for s in (0, 1):
    F = flipper(s)
    d.line(F([(37, 16), (42, 19)]), fill=BLACK)       # angry brow
    d.line(F([(39, 20), (42, 20)]), fill=BLACK)       # socket floor
    d.line(F([(39, 19), (39, 19)]), fill=BLACK)
    d.line(F([(40, 19), (41, 19)]), fill=rgba(G))     # eye
    d.line(F([(43, 25), (43, 25)]), fill=BLACK)       # nostril
    d.line(F([(36, 43), (42, 45)]), fill=BLACK)       # pec
    d.line(F([(38, 47), (43, 48)]), fill=BLACK)       # abs
    d.line(F([(40, 52), (43, 52)]), fill=BLACK)
rect(im, 41, 27, 8, 1, BLACK)                         # mouth
rect(im, 42, 28, 6, 1, BLACK)
for s in (0, 1):
    F = flipper(s)
    d.line(F([(42, 27), (42, 28)]), fill=rgba(T))     # fangs
d.line([(44, 32), (44, 57)], fill=BLACK)              # breastbone

im = outline(im)
save(im)
