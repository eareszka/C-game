from pix import *

G1, G2, G3 = 'a4aaba', '848694', '595965'   # grey hide
C1, C2 = 'e8e0c0', 'cebe82'                 # cream belly, teeth
R1, R2, R3 = 'b6433d', '792727', '421618'   # crimson arms, gum, throat
K = '000000'

W, H = 78, 72
im = canvas(W + 2, H + 2)
CX = 40  # head columns are CX - hw .. CX - 1 + hw


def table(spec):
    out = {}
    for a, b, hw in spec:
        for y in range(a, b + 1):
            out[y] = hw
    return out


def span(y, hw, colour):
    rect(im, CX - hw, y, hw * 2, 1, colour)


# ---------- arms, behind the head ----------
def stroke(path, r0, r1):
    """Every pixel of a tapered, blocky stroke along a polyline."""
    pts = []
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        n = max(abs(bx - ax), abs(by - ay), 1)
        for i in range(n):
            pts.append((ax + (bx - ax) * i / n, ay + (by - ay) * i / n))
    pts.append(path[-1])
    cells = set()
    for i, (x, y) in enumerate(pts):
        t = i / max(len(pts) - 1, 1)
        r = round(r0 + (r1 - r0) * t)
        x, y = round(x), round(y)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if abs(dx) + abs(dy) <= r + (r // 2):
                    cells.add((x + dx, y + dy))
    return cells


def arm(path, r0, r1, suckers=()):
    cells = stroke(path, r0, r1)
    px = im.load()
    # a black line wherever this arm crosses one already drawn
    for x, y in cells:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + a, y + b)
            if p not in cells and 0 <= p[0] < im.width and 0 <= p[1] < im.height and px[p][3]:
                dot(im, p[0], p[1], K)
    for x, y in cells:
        if x < 0 or y < 0 or x >= im.width or y >= im.height:
            continue
        dark = (x, y + 1) not in cells or (x + 1, y) not in cells
        deep = dark and ((x, y + 2) not in cells and (x + 2, y) not in cells)
        dot(im, x, y, R3 if deep and False else R2 if dark else R1)
    for x, y in suckers:
        rect(im, x, y, 2, 1, C2)


def m(path):
    return [(W + 1 - x, y) for x, y in path]


# left side
A_top = [(24, 44), (16, 48), (9, 47), (4, 42), (4, 35), (9, 31), (14, 33), (15, 38), (11, 39)]
A_low = [(24, 53), (16, 57), (9, 59), (4, 57), (2, 52)]
A_in = [(28, 60), (27, 66), (24, 70), (20, 70), (18, 67)]
# right side: the same arms, tips turned a little differently
B_top = [(24, 45), (16, 49), (9, 48), (4, 43), (4, 36), (9, 32), (14, 34), (15, 39), (11, 40)]
B_low = [(24, 54), (16, 58), (10, 60), (5, 60), (2, 56)]
B_in = [(28, 60), (28, 66), (25, 70), (21, 71), (19, 68)]

arm(A_in, 3, 1)
arm(m(B_in), 3, 1)
arm(A_low, 4, 1, [(14, 57), (9, 58)])
arm(m(B_low), 4, 1, [(64, 58), (69, 59)])
arm(A_top, 4, 1, [(16, 48), (11, 47), (4, 41)])
arm(m(B_top), 4, 1, [(62, 49), (67, 48), (74, 42)])

# ---------- head ----------
HEAD = table([(0, 2, 1), (3, 5, 2), (6, 8, 3), (9, 9, 4), (10, 10, 6), (11, 11, 8), (12, 13, 10),
              (14, 15, 12), (16, 17, 14), (18, 20, 16), (21, 23, 17), (24, 27, 18), (28, 30, 19),
              (31, 36, 20), (37, 52, 21), (53, 54, 20), (55, 56, 19), (57, 58, 17),
              (59, 60, 15), (61, 61, 13), (62, 63, 10), (64, 64, 6)])
for y, hw in HEAD.items():
    span(y, hw, G2)
    lit = max(1, hw * 2 // 5)
    shade = max(1, hw * 2 // 7)
    rect(im, CX - hw, y, lit, 1, G1)
    rect(im, CX + hw - shade, y, shade, 1, G3)

# the fin runs down into the crown as one ridge
rect(im, CX - 1, 2, 1, 12, G3)
rect(im, CX - 1, 14, 1, 3, K)
# folds of hide over the snout
for x, w, y in [(36, 8, 28), (37, 6, 26)]:
    rect(im, x, y, w, 1, G3)
# old nicks on the crown
for x, y, w in [(30, 17, 3), (28, 19, 2), (47, 16, 3), (49, 18, 2)]:
    rect(im, x, y, w, 1, K)

# belly
BELLY = table([(31, 32, 8), (33, 34, 12), (35, 36, 15), (37, 39, 17), (40, 54, 19),
               (55, 56, 18), (57, 58, 17), (59, 60, 15), (61, 61, 13), (62, 63, 10), (64, 64, 6)])
for y, hw in BELLY.items():
    span(y, hw, C1)
    shade = max(1, hw // 4)
    rect(im, CX + hw - shade, y, shade, 1, C2)
# shaded under the chin
for y, hw in BELLY.items():
    if y >= 60:
        span(y, hw, C2)

# ---------- mouth ----------
MOUTH = table([(36, 36, 6), (37, 37, 9), (38, 38, 11), (39, 40, 13), (41, 42, 15),
               (43, 50, 16), (51, 52, 15), (53, 54, 13), (55, 55, 10), (56, 56, 6)])
for y, hw in MOUTH.items():
    span(y, hw, K)
ys = sorted(MOUTH)
inner = {y: min(MOUTH[y] - 1, MOUTH.get(y - 1, 0), MOUTH.get(y + 1, 0)) for y in ys}
inner = {y: hw - (0 if hw < MOUTH[y] else 1) for y, hw in inner.items() if hw > 0}
for y, hw in inner.items():
    span(y, hw, R2)
for y, hw in inner.items():
    if MOUTH.get(y - 3, 0) and MOUTH.get(y + 2, 0):
        span(y, max(hw - 2, 1), R3)
# tongue
oval(im, CX - 9, 49, 18, 7, R1)
rect(im, CX - 7, 54, 14, 1, R2)
rect(im, CX - 1, 50, 1, 5, R2)
rect(im, CX - 4, 49, 8, 1, R1)


def tooth(x, y, h, down=True, w=3):
    """Base w wide, narrowing to a 1 px tip, with a black line round it."""
    rows = []
    for i in range(h):
        wi = w if i < h // 2 else max(1, w - 2)
        rows.append(wi)
    step = 1 if down else -1
    for i, wi in enumerate(rows):
        yy = y + i * step
        left = x - wi // 2
        rect(im, left - 1, yy, wi + 2, 1, K)
    rect(im, x - rows[-1] // 2, y + h * step, rows[-1], 1, K)
    for i, wi in enumerate(rows):
        yy = y + i * step
        left = x - wi // 2
        rect(im, left, yy, wi, 1, C1)
        if wi > 1:
            dot(im, left + wi - 1, yy, C2)


# upper row hangs from the arch, biggest at the corners
for x, y, h in [(26, 41, 5), (30, 39, 6), (34, 38, 5), (38, 37, 4), (42, 37, 4),
                (46, 38, 5), (50, 39, 6), (54, 41, 5)]:
    tooth(x, y, h)
# lower row stands on the lip
for x, y, h in [(27, 52, 4), (31, 54, 4), (35, 55, 3), (39, 55, 3), (43, 55, 3),
                (47, 54, 4), (51, 52, 4)]:
    tooth(x, y, h, down=False)

# blood running off the lip
rect(im, CX - 11, 56, 2, 5, R1)
rect(im, CX - 10, 61, 1, 2, R2)
rect(im, CX + 6, 57, 1, 3, R1)

# ---------- face ----------
# brows: a lit ridge over a dark crease, sloping down to the snout
# eyes sit in a lit patch under the brow so they stay clear at game size
rect(im, 25, 24, 7, 5, G1)
rect(im, 48, 24, 7, 5, G2)
for x, y in [(24, 22), (26, 23), (28, 24), (30, 25)]:
    rect(im, x, y, 2, 1, K)
    rect(im, x, y - 1, 2, 1, G1)
for x, y in [(54, 22), (52, 23), (50, 24), (48, 25)]:
    rect(im, x, y, 2, 1, K)
    rect(im, x, y - 1, 2, 1, G2)
rect(im, 28, 27, 2, 1, K)
rect(im, 50, 27, 2, 1, K)
# gills
for x, y in [(21, 32), (21, 35), (22, 38)]:
    rect(im, x, y, 1, 2, K)
for x, y in [(58, 32), (58, 35), (57, 38)]:
    rect(im, x, y, 1, 2, K)

im = outline(im)
save(im)
