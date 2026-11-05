from pix import *

W, S, G = 'fcfcfc', 'c6ccda', '848694'
L, B, D = '84a7e9', '5c94fc', '2850a0'
P = 'ec8476'
K = '000000'
PAL = {'w': W, 's': S, 'g': G, 'p': P, 'd': D}

im = canvas(60, 60)
cx = 22


def span(y, x0, x1, c):
    rect(im, x0, y, x1 - x0 + 1, 1, c)


# --- wind blades either side: two stepped crescents per side
ARC = {12: (12, 13), 13: (10, 13), 14: (8, 12), 15: (6, 10), 16: (4, 8), 17: (3, 7),
       18: (2, 6), 19: (1, 4), 20: (1, 3), 21: (0, 3),
       24: (0, 2), 25: (0, 3), 26: (0, 3), 27: (1, 4), 28: (1, 5), 29: (2, 6),
       30: (3, 7), 31: (5, 9), 32: (7, 10), 33: (9, 10)}
for y, (a, b) in ARC.items():
    span(y, a, b, G)
    span(y, a, a + 1, S)
    ra, rb = 2 * cx - b, 2 * cx - a
    span(y, ra, rb, G)
    span(y, ra, ra, S)

# --- stray wind chunks behind the lower funnel
for y, a, b in ((38, 9, 13), (39, 8, 14), (40, 10, 14)):
    span(y, a, b, G)
    span(y, a, a + 1, S)
for y, a, b in ((44, 27, 32), (45, 26, 33), (46, 26, 30)):
    span(y, a, b, G)

# --- funnel mouth, wide and dark behind the weasel
BACK = {16: 9, 17: 12, 18: 14, 19: 16, 20: 17, 21: 17, 22: 17, 23: 17, 24: 17, 25: 17}
for y, h in BACK.items():
    span(y, cx - h, cx + h, D)
span(16, cx - 9, cx + 9, L)
span(17, cx - 12, cx - 8, L)
span(17, cx + 8, cx + 12, B)
span(18, cx - 14, cx - 12, L)
span(18, cx + 12, cx + 14, B)
span(19, cx - 16, cx - 15, L)
span(19, cx + 15, cx + 16, B)
for y in (20, 21, 22, 23):
    span(y, cx - 17, cx - 17, L)
    span(y, cx + 17, cx + 17, B)

# --- weasel: long neck, shoulders, arms split off by black lines, two chest tufts
BODY = [
    '......wwwwwss......',
    '.....wwwwwwwss.....',
    '.....wwwwwwwss.....',
    '....wwwwwwwwwss....',
    '...wwwwwwwwwwwss...',
    '..wwwKwwwwwwKwwss..',
    '..wwKwswwwswwKwss..',
    '.wwwKwwswswwwKwwss.',
    '.wwKwwwwswwwwwKwss.',
    '.wwKwswwwwwswwKwss.',
    'wwwKwwswwwswwwKwwss',
    'wwwKwwwswswwwwKwwss',
    'wwwKwwwwswwwwwKwwss',
    'wwwKwwwwwwwwwwKwwss',
]
stamp(im, grid(BODY, PAL), cx - 9, 14)

# --- sickles held up from the forepaws, curling in over the dark mouth
SICKLE = {18: (-13, -11), 19: (-15, -13), 20: (-16, -14), 21: (-16, -15), 22: (-16, -15),
          23: (-15, -14)}
for y, (a, b) in SICKLE.items():
    span(y, cx + a, cx + b, W)
    span(y, cx - b, cx - a, S)
# grey hafts running down into the paws
for y, a, b in ((24, -14, -11), (25, -12, -10)):
    span(y, cx + a, cx + b, G)
    span(y, cx - b, cx - a, G)

# --- funnel front: stepped taper, stripes curve with the lip and slant a little
FRONT = {24: (17, 0), 25: (17, 0), 26: (16, 0), 27: (15, 0),
         28: (14, 0), 29: (13, 1), 30: (13, 1), 31: (12, 1), 32: (11, 1), 33: (11, 0),
         34: (10, 0), 35: (10, 0), 36: (9, -1), 37: (9, -1), 38: (8, -1), 39: (7, -1),
         40: (7, 0), 41: (6, 0), 42: (6, 0), 43: (5, 1), 44: (5, 1), 45: (4, 1),
         46: (3, 1), 47: (3, 0), 48: (2, 0), 49: (1, -1)}


def lip(dx):
    a = abs(dx)
    if a >= 15:
        return 24
    if a >= 12:
        return 25
    return 26


px = im.load()
for y, (h, off) in FRONT.items():
    c0 = cx + off
    for x in range(c0 - h, c0 + h + 1):
        dx = x - cx
        top = lip(dx)
        if y < top:
            continue
        if y == top:
            px[x, y] = rgba(K)
            continue
        t = (y - top - 1 + (dx + 20) // 8) % 7
        rel = (x - (c0 - h)) / (2 * h + 1)
        if t == 3:
            c = K
        elif t < 3:
            c = L if rel < 0.3 else (B if rel < 0.72 else D)
        else:
            c = W if rel < 0.68 else S
        px[x, y] = rgba(c)

# --- forepaws gripping the lip
PAW_L = [
    '.www.',
    'wwwww',
    'wKwKw',
    'wKwKw',
]
PAW_R = [
    '.wws.',
    'wwwss',
    'wKwKs',
    'wKwKs',
]
stamp(im, grid(PAW_L, PAL), cx - 12, 24)
stamp(im, grid(PAW_R, PAL), cx + 8, 24)

# --- head: flat skull, small round ears, tapering muzzle
HEAD = [
    '...ww.....ws...',
    '..wwww...wwss..',
    '..wppw...wpps..',
    '.wwppw...wppss.',
    '.wwppwwwwwppss.',
    '.wwwwwwwwwwwss.',
    'wwwwwwwwwwwwwss',
    'wwKwwwwwwwwKwss',
    'wwwKwwwwwwKwwss',
    'wwwwwwwwwwwwwss',
    '.wwwwKpppKwwss.',
    '.wwwwwKpKwwwss.',
    '..wwwwwKwwwss..',
    '...wwKKwKKss...',
    '....wwwwwss....',
    '.....sssss.....',
]
final = canvas(60, 62)
stamp(final, im, 0, 2)
stamp(final, grid(HEAD, PAL), cx - 7, 0)
im = final

im = outline(im)
save(im)
