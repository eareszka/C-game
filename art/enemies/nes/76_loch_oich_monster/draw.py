from pix import *

E = '583518'   # hide shade, ears, flippers
M = '94703d'   # hide
H = 'c18a39'   # hide light
T = 'd7a175'   # belly
K = '000000'
PAL = {'e': E, 'm': M, 'h': H, 't': T}

im = canvas(60, 56)
G = 47  # lowest row of the body


def column(x, top, bottom, col):
    if bottom >= top:
        rect(im, x, top, 1, bottom - top + 1, col)


def hump(x0, tops, unders):
    n = len(tops)
    for i, (top, under) in enumerate(zip(tops, unders)):
        x = x0 + i
        column(x, top, under, M)
        # light along the upper left of the roll
        if i < n * 0.6:
            column(x, top, min(top + 1, under), H)
        # shade down the right flank
        if i >= n * 0.62:
            column(x, top + 2 if i < n - 2 else top, under, E)
        # shaded underside inside the arch
        if under < G:
            column(x, under - 1, under, E)
    # black seam at the right end, parting it from the next roll
    column(x0 + n - 1, tops[-1], G, K)


# tail, lying out to the left with its tip lifted
for x, (a, b) in zip(range(1, 7), [(41, 41), (41, 42), (42, 44), (43, 45), (43, 46), (43, 47)]):
    column(x, a, b, M)
    dot(im, x, a, H)
    dot(im, x, b, E)

hump(6, [42, 37, 34, 33, 32, 32, 32, 32, 32, 33, 34, 37, 42],
     [47, 47, 46, 44, 42, 41, 41, 41, 42, 44, 46, 47, 47])
hump(18, [42, 35, 31, 29, 28, 27, 27, 27, 27, 28, 29, 31, 35, 42],
     [47, 47, 46, 42, 39, 37, 36, 36, 37, 39, 42, 46, 47, 47])

# one stepped fold slanting across the top of each hump
for x, y in [(11, 34), (11, 35), (12, 36), (12, 37), (13, 38),
             (23, 29), (23, 30), (24, 31), (24, 32), (25, 33), (25, 34)]:
    dot(im, x, y, K)

# chest: the biggest roll, the neck grows out of it
tops = [40, 36, 33, 31, 29, 28, 27, 27, 27, 28, 29, 31, 33, 36, 40]
for i, top in enumerate(tops):
    x = 31 + i
    column(x, top, G, M)
    if i < 7:
        column(x, top, top + 1, H)
    if i >= 10:
        column(x, top + 1, G, E)
    column(x, G - 1, G, E)

# belly shield on the chest
for y, a, b in [(35, 35, 40), (36, 34, 40), (37, 34, 41), (38, 34, 41), (39, 34, 41),
                (40, 34, 41), (41, 34, 41), (42, 35, 40), (43, 36, 39)]:
    rect(im, a, y, b - a + 1, 1, T)
    dot(im, a - 1, y, K)
    dot(im, b + 1, y, K)
rect(im, 36, 44, 4, 1, K)
for y, a, n in [(38, 34, 4), (41, 34, 5)]:
    rect(im, a, y, n, 1, K)

# long neck, widening and stepping as it climbs down into the chest
neck = [(y, 33, 39) for y in range(15, 19)]
neck += [(y, 33, 40) for y in range(19, 23)]
neck += [(y, 34, 41) for y in range(23, 27)]
neck += [(y, 33, 41) for y in range(27, 30)]
neck += [(y, 32, 42) for y in range(30, 33)]
neck += [(y, 31, 43) for y in range(33, 36)]
for y, a, b in neck:
    rect(im, a, y, b - a + 1, 1, M)
    dot(im, a, y, H)
    rect(im, b - 1, y, 2, 1, E)
    rect(im, a + 2, y, b - a - 3, 1, T)
    dot(im, b - 2, y, K)
    if y % 4 == 2:
        rect(im, a + 2, y, 2, 1, K)
    if y % 4 == 0 and y > 24:
        dot(im, a + 1, y, K)

# dog's head, front on, with hanging ears and a tan cap
head = [
    ".........hhhmm.........",
    "......hhhhhhhhmmm......",
    ".....hhhhhhhhhmmmm.....",
    "..eeeeKhhhhhhmmmKeeee..",
    ".eemmeKhhhhhmmmmKeeeee.",
    ".emmmeKmmmmmmmmmKmmeee.",
    ".emmmeKmKmmmmmKmKmmeee.",
    ".emmeeKmKmmmmmKmKmmeee.",
    ".emmeeKmttKKKthmKmmeee.",
    ".emmeeKmtttKtthmKmmee..",
    "..emmeKttttKtthhKmee...",
    "..emmeKtKttKthKhKmee...",
    "..emee.ttKKKKKhh.eee...",
    "...ee...ttttth...ee....",
]
assert all(len(r) == 23 for r in head)
stamp(im, grid(head, PAL), 25, 1)

# flippers: a dark one out to the right, a small one under the humps
right = [
    "...eee....",
    ".mmeeeeee.",
    "mmmeeeeeee",
    "mmeeKeeKee",
    ".eee.ee.e.",
]
stamp(im, grid(right, PAL), 42, 43)
left = [
    ".mee..",
    "mmeee.",
    ".eKee.",
    "..e.e.",
]
stamp(im, grid(left, PAL), 27, 46)

im = outline(im)
save(im)
