from pix import *

D, M, L = '5c4616', '876a1f', 'b29e5c'
G0, G1, G2 = '595965', '9797aa', 'dcf0ff'
AMBER, CLAW = 'f0bc3c', 'cebe82'
W, H = 64, 48


def on(layer, x, y):
    return 0 <= x < W and 0 <= y < H and layer.load()[x, y][3] > 0


def shade(layer, base=M, lit=L, dark=D):
    src = layer.copy()
    px = layer.load()
    for y in range(H):
        for x in range(W):
            if not on(src, x, y) or px[x, y] != rgba(base):
                continue
            if not on(src, x, y + 1) or not on(src, x + 1, y) or not on(src, x, y + 2):
                px[x, y] = rgba(dark)
            elif not on(src, x, y - 1) or not on(src, x - 1, y):
                px[x, y] = rgba(lit)


def comp(im, layer):
    """Paste a part; a black line appears only where it overlaps what is behind it."""
    src, dst = layer.load(), im.load()
    for y in range(H):
        for x in range(W):
            if src[x, y][3]:
                continue
            near = any(on(layer, x + a, y + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if near and dst[x, y][3]:
                dst[x, y] = BLACK
    im.alpha_composite(layer)


def run(im, y, x0, x1, c):
    rect(im, x0, y, x1 - x0 + 1, 1, c)


def line(im, a, b, c):
    ImageDraw.Draw(im).line((a, b), fill=rgba(c))


im = canvas(W, H)

# far leg, behind the body
far = canvas(W, H)
rect(far, 25, 30, 4, 5, D)
rect(far, 24, 34, 6, 2, D)
comp(im, far)
for x in (24, 26, 29):
    dot(im, x, 36, CLAW)

# body slab with a low hump
body = canvas(W, H)
poly(body, [(12, 23), (16, 20), (22, 19), (32, 19), (38, 21), (42, 25), (42, 31), (12, 31)], M)
shade(body)
comp(im, body)

# back spines follow the top of the hump
for x in range(15, 39, 4):
    top = next(y for y in range(H) if on(body, x + 1, y))
    run(im, top - 1, x, x + 2, M)
    dot(im, x, top - 1, L)
    dot(im, x + 2, top - 1, D)
    dot(im, x + 1, top - 2, L)

# a stepped line under the spines
run(im, 23, 14, 21, BLACK)
run(im, 22, 21, 33, BLACK)
run(im, 23, 33, 38, BLACK)

# flank plates between the legs
for x in (22, 26, 30):
    rect(im, x, 23, 1, 5, BLACK)
for x in (23, 27, 31):
    run(im, 23, x, x + 2, L)
run(im, 28, 21, 33, BLACK)
run(im, 29, 21, 33, D)

# hind leg
hind = canvas(W, H)
oval(hind, 33, 25, 9, 8, M)
rect(hind, 34, 31, 5, 3, M)
rect(hind, 32, 34, 9, 2, M)
shade(hind)
comp(im, hind)
for x in (32, 35, 38):
    dot(im, x, 36, CLAW)

# front leg
front = canvas(W, H)
oval(front, 14, 26, 7, 7, M)
rect(front, 15, 31, 4, 3, M)
rect(front, 14, 34, 7, 2, M)
shade(front)
comp(im, front)
for x in (14, 17, 20):
    dot(im, x, 36, CLAW)

# head, face on, no mouth
half = [
    '..h.....',
    '..g.....',
    '.LLLL...',
    'LMMMML..',
    'LMMMMML.',
    'MMAAMMMM',
    'MDDDMMLM',
    'DMMMMMLM',
    '.DMMMMLM',
    '..MMMMLM',
    '..DMMMMM',
    '...MMMMM',
    '..LMMMMM',
    '..MMKMMM',
    '..MMMMMM',
    '..DMMMMM',
    '...DDDDD',
]
rows = []
for r in half:
    rows.append(r + r[-2::-1].replace('L', 'D'))
head = canvas(W, H)
stamp(head, grid(rows, {'L': L, 'M': M, 'D': D, 'A': AMBER, 'h': G2, 'g': G1}), 0, 15)
comp(im, head)

# everything so far sits 2 px lower, so the club clears the back spines
low = canvas(W, H)
stamp(low, im, 0, 2)

# tail, a chunky stepped hook from the rump, up and over the back
tail = canvas(W, H)
for x, y, w, h in [
    (35, 28, 10, 8), (38, 26, 9, 8), (40, 22, 9, 9), (41, 18, 8, 8), (41, 14, 8, 7),
    (40, 11, 8, 6), (38, 8, 8, 6), (36, 6, 8, 6), (33, 5, 7, 6), (30, 6, 6, 5),
    (28, 7, 4, 4),
]:
    rect(tail, x, y, w, h, M)
shade(tail)
for a, b in [((43, 28), (46, 31)), ((43, 23), (47, 24)), ((42, 16), (46, 17)), ((38, 11), (41, 8)), ((34, 6), (34, 9))]:
    line(tail, a, b, D)

im = canvas(W, H)
comp(im, tail)
comp(im, low)

# club, the grey spiked ball
club = canvas(W, H)
oval(club, 16, 3, 12, 12, G1)
shade(club, G1, G2, G0)
rect(club, 19, 6, 2, 2, G2)
dot(club, 24, 10, G0)
dot(club, 23, 11, G0)
# spikes: a grey base and a pale tip
rect(club, 21, 2, 2, 1, G1)
rect(club, 21, 0, 1, 2, G2)
rect(club, 21, 15, 2, 1, G1)
dot(club, 22, 16, G2)
rect(club, 15, 8, 1, 2, G1)
rect(club, 13, 8, 2, 1, G2)
dot(club, 16, 4, G1)
line(club, (15, 3), (14, 2), G2)
dot(club, 16, 13, G1)
dot(club, 15, 14, G2)
dot(club, 27, 4, G1)
dot(club, 28, 3, G2)
dot(club, 27, 13, G1)
line(club, (28, 14), (29, 15), G2)
comp(im, club)

# collar joining the tail to the club
rect(im, 28, 7, 2, 4, G0)
rect(im, 28, 7, 2, 1, G1)

im = outline(im)
save(im)
