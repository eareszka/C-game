from pix import *

L, M, D = '4fa667', '2c6c44', '163623'
T, U = 'c18a39', '815423'
C, A, B = 'f0b890', 'ec8476', 'b6433d'
K = '000000'
PAL = {'a': A, 'b': B, 'c': C}

im = canvas(56, 58)

# Far legs: darker, set back. Dead straight, no joints. Blunt hooves.
for x in (10, 30):
    rect(im, x, 30, 2, 22, T)
    rect(im, x + 1, 30, 1, 22, U)
    rect(im, x - 1, 51, 4, 1, T)
    rect(im, x - 1, 52, 2, 1, U); rect(im, x + 2, 52, 1, 1, U)

# Near legs: three px, lit on the left.
for x in (3, 23):
    rect(im, x, 30, 3, 24, C)
    rect(im, x + 2, 30, 1, 24, T)
    rect(im, x - 1, 54, 5, 1, T)
    rect(im, x - 1, 55, 2, 1, U); rect(im, x + 2, 55, 2, 1, U)

# Neck: stiff stepped diagonal from the shoulder up behind the head.
for i, y in enumerate(range(26, 13, -1)):
    x = 34 + (i * 3) // 4
    rect(im, x, y, 4, 1, A)
    dot(im, x, y, C)
    dot(im, x + 3, y, B)

# Jagged crest: low rump rising to high withers, tufts blown back to the left.
TOPS = [25, 20, 21, 19, 20, 17, 18, 16, 18, 15, 17, 15, 16, 14, 16, 15, 13, 15, 14, 12,
        14, 14, 12, 14, 13, 12, 14, 13, 15, 14, 16, 17, 19, 18, 21, 23, 26]


def tier(start, locks, light, mid, dark, line, first):
    """Long hanging locks. Each lock is (width, tip y)."""
    x = start
    for w, tip in locks:
        for i in range(w):
            cx = x + i
            if not 0 <= cx < len(TOPS):
                continue
            bottom = tip - abs(2 * i - (w - 1)) // 2 * 2
            top = max(TOPS[cx], first)
            for y in range(top, bottom + 1):
                if i == 0:
                    c = light
                elif i >= w - 1:
                    c = dark
                else:
                    c = mid
                dot(im, cx, y, c)
            # a black line down the lock's right edge
            if line and i == w - 1:
                for y in range(max(top + 2, bottom - line), bottom):
                    dot(im, cx, y, K)
            # black under the tip, only where it lands on hide
            if line and im.getpixel((cx, bottom + 1))[3] and im.getpixel((cx, bottom + 1))[:3] != (0, 0, 0):
                dot(im, cx, bottom + 1, K)
        x += w


# Tan fringe, hanging well below the green.
tier(0, [(4, 32), (5, 34), (4, 31), (6, 34), (4, 32), (5, 34), (4, 31), (5, 33)], T, T, U, 0, 26)
# Lower hide.
tier(-1, [(5, 28), (4, 26), (6, 29), (5, 27), (4, 28), (6, 29), (4, 26), (5, 28), (4, 25)], M, M, D, 6, 12)
# Upper cape, lit.
tier(1, [(4, 25), (6, 26), (4, 24), (5, 24), (6, 23), (4, 22), (5, 22), (3, 20)], L, M, D, 4, 10)
# Sun on the crest.
for x, top in enumerate(TOPS):
    if x < 29:
        dot(im, x, top, L)
        if x % 2:
            dot(im, x, top + 1, L)

# Head: narrow brow, and the great lip flaring wider and hanging over a small chin.
HEAD = grid([
    '....aaa.......aaa....',
    '...acccaa...aaaaab...',
    '..acccaaaa.aaaaaaab..',
    '..accaaaaaaaaaaaaab..',
    '..acaaaaaaaaaaaaaab..',
    '..aaaKKaaaaaaaKKaab..',
    '...aaaaaaaaaaaaaab...',
    '...aaaaaKaaaKaaabb...',
    '..baaaaaaaaaaaaabbb..',
    '.bbbKKbbbbbbbbbKKbbb.',
    'acccccaaaaaaaaaaaaaab',
    'accaaaaaaaaaaaaaaaaab',
    'aaaaaaaaaaaaaaaaaaabb',
    'baaaaaaaaabaaaaaaabbb',
    '.baaaaaaabbbaaaaabbb.',
    '.bbaaaaabbKbbaaabbb..',
    '..bb.bbbbKKKbbbb.bb..',
    '..b...b.KKKKK.b...b..',
    '..b....bbaaabb....b..',
    '........bbbbb........',
], PAL)
stamp(im, HEAD, 35, 0)

im = outline(im)
save(im)
