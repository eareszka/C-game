from pix import *

L = 'a4aaba'
M = '848694'
D = '595965'
W = 'fcfcfc'
C = 'e8e0c0'
S = 'cebe82'
P = 'ec8476'
R = 'b6433d'
K = '000000'
PAL = {'L': L, 'M': M, 'D': D, 'W': W, 'C': C, 'S': S, 'P': P, 'R': R}

im = canvas(60, 60)
cx = 27


def run(y, a, b, col):
    rect(im, a, y, b - a + 1, 1, col)


# tail, behind everything: long, pink, ringed, thin at the tip
pts = [(5, 38), (4, 39), (3, 40), (3, 41), (2, 42), (2, 43), (2, 44), (2, 45), (3, 46),
       (3, 47), (4, 48), (5, 49), (6, 49), (7, 49), (8, 48), (9, 48), (10, 47), (11, 47), (12, 46)]
for x, y in pts:
    rect(im, x, y, 2, 2, P)
for x, y in [(3, 41), (2, 45), (5, 50), (8, 49)]:
    rect(im, x, y, 2, 1, R)
dot(im, 6, 37, P)
dot(im, 7, 36, P)

# arms: thrown wide from the hunched shoulders
for side in (-1, 1):
    for n in range(10):
        x = cx + side * (13 + n)
        top = 19 + n * 3 // 4
        bot = 27 + n // 2
        if side < 0:
            run_col = [(top, top + 1, L), (top + 2, bot - 1, M), (bot, bot, D)]
        else:
            run_col = [(top, top + 1, M), (top + 2, bot, D)]
        for a, b, col in run_col:
            rect(im, x, a, 1, b - a + 1, col)

# paws: open, thumb claw up, three claws down
PAW = [
    "WW......",
    "WWC.LLL.",
    ".CLLLLMM",
    "..LLMMMM",
    ".LLMMMMM",
    ".LMMMMMD",
    "LLMMMMDD",
    "MMMMMDD.",
    "DDDDDD..",
    "WW.WW.WW",
    "WC.WC.WC",
    ".C..C..C",
]
TONE = {'L': 'M', 'M': 'D', 'W': 'C', 'C': 'S'}
for y, row in enumerate(PAW):
    for i, ch in enumerate(row):
        if ch == '.':
            continue
        dot(im, cx - 25 + i, 23 + y, PAL[ch])
        dot(im, cx + 25 - i, 23 + y, PAL[TONE.get(ch, ch)])

# body: hunched, heavy, bottom-weighted
widths = {17: 11, 18: 13, 19: 14, 20: 14, 21: 14, 22: 14, 23: 14, 24: 14, 25: 13, 26: 13, 27: 13, 28: 12,
          29: 12, 30: 13, 31: 13, 32: 13, 33: 14, 34: 14, 35: 15, 36: 15, 37: 15, 38: 15, 39: 15, 40: 15,
          41: 15, 42: 15, 43: 14, 44: 14}
for y, h in widths.items():
    run(y, cx - h, cx + h, M)
    run(y, cx - h, cx - h + 2, L)
    run(y, cx + h - 3, cx + h, D)

# pale belly
for y, h in {30: 5, 31: 6, 32: 7, 33: 8, 34: 9, 35: 9, 36: 10, 37: 10, 38: 10, 39: 10, 40: 10, 41: 9, 42: 8, 43: 6}.items():
    run(y, cx - h, cx + h - 2, L)
# blubber folds that sag with the belly
for y in (36, 40):
    run(y - 1, cx - 9, cx - 7, K)
    run(y, cx - 6, cx + 3, K)
    run(y - 1, cx + 4, cx + 6, K)

# chest and flank creases
for i in range(6):
    dot(im, cx - 12 + i // 2, 24 + i, K)
    dot(im, cx + 12 - i // 2, 24 + i, K)
run(41, cx - 14, cx - 12, D)
run(38, cx + 10, cx + 12, K)

# legs, splayed
for side in (-1, 1):
    for y, (i, o) in {45: (1, 14), 46: (2, 14), 47: (2, 14), 48: (3, 15), 49: (3, 16)}.items():
        a, b = (cx - o, cx - i) if side < 0 else (cx + i, cx + o)
        run(y, a, b, M)
        if side < 0:
            run(y, a, a + 2, L)
            run(y, b - 1, b, D)
        else:
            run(y, b - 3, b, D)
    a, b = (cx - 16, cx - 3) if side < 0 else (cx + 3, cx + 16)
    run(50, a, b, D)
    # three blunt claws on each foot
    for x in (a, a + 5, a + 10):
        rect(im, x, 50, 4, 2, W if side < 0 else C)
        run(51, x, x + 3, C if side < 0 else S)
    # knee crease
    if side < 0:
        run(46, cx - 10, cx - 7, K)
    else:
        run(46, cx + 7, cx + 10, K)
run(45, cx, cx, K)

# head
HEAD = [
    "..........LLLLL",
    "........LLLLLLL",
    ".WW....LLLLLLLL",
    "WWCC..LLLLLLCCC",
    "WCCCS.LLLLLWWCC",
    ".CCCCSMLLWWCCCS",
    ".SCCCCCCWWCCCCC",
    "..SSCCCCCCCCCCC",
    "....SSSSSSSSCCC",
    ".....MLLLLLSCCC",
    ".....MLLLLLSCCC",
    ".....MLLKLLSCCC",
    "....MLLLKLLSCCC",
    "....MLLLLLLSCCC",
    "....MLLLLKKKCCC",
    "....MLLLKCCCCCC",
    "....MLLLKWWCSCC",
    "....MLLLKWCCCSC",
    "....MMLLKSSSSSS",
    "....DMMMMKKKKKK",
    ".....DDDMMMMMMM",
]


def flip_tone(ch, off):
    if off < 3:
        return ch
    return {'L': 'M', 'M': 'D', 'W': 'C'}.get(ch, ch)


hx = cx - 14
for y, row in enumerate(HEAD):
    for i, ch in enumerate(row):
        if ch == '.':
            continue
        dot(im, hx + i, y, K if ch == 'K' else PAL[ch])
        if i < 14:
            ch2 = flip_tone(ch, 14 - i)
            dot(im, hx + 28 - i, y, K if ch2 == 'K' else PAL[ch2])

# tusks: long, reaching the belly
for side in (-1, 1):
    a = cx - 5 if side < 0 else cx + 2
    run(20, cx - 6, cx + 6, K)
    for y in range(21, 30):
        run(y, a, a + 3, C)
        dot(im, a, y, W)
        dot(im, a + 1, y, W)
        dot(im, a + 3, y, S)
        dot(im, a - 1, y, K)
        dot(im, a + 4, y, K)
    # taper
    run(30, a, a + 3, C)
    dot(im, a, 30, W)
    dot(im, a + 3, 30, S)
    dot(im, a - 1, 30, K)
    dot(im, a + 4, 30, K)
    run(31, a, a + 3, K)
    run(31, a + 1, a + 2, C)
    run(32, a, a + 3, K)
    run(32, a + 1, a + 2, S)
    run(33, a + 1, a + 2, K)
# mouth between the tusks
for y in range(21, 31):
    dot(im, cx, y, D)
run(31, cx - 1, cx + 1, K)

im = outline(im)
save(im)
