from pix import *

A = 'cebe82'  # light tan
B = 'b29e5c'  # tan
C = '94703d'  # tan shade
D = '815423'  # brown
E = '583518'  # dark brown
F = 'f0bc3c'  # rattle yellow
G = 'b70000'  # rattle red
PAL = {'a': A, 'b': B, 'c': C, 'd': D, 'e': E, 'f': F, 'g': G}

im = canvas(44, 58)


def path(points):
    out = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n):
            out.append((x0 + round((x1 - x0) * i / n), y0 + round((y1 - y0) * i / n)))
    out.append(points[-1])
    return out


def rope(points, phase=0, line=False):
    pts = path(points)
    cells = set()
    for x, y in pts:
        rect(im, x, y, 3, 3, B)
        cells |= {(x + a, y + b) for a in range(3) for b in range(3)}
    for x, y in pts:
        dot(im, x, y, A)
    for i, (x, y) in enumerate(pts):
        if (i + phase) % 4 == 0:
            rect(im, x, y, 3, 3, C)
            dot(im, x, y, B)
    if line:
        # black line where the rope crosses the body, never on the silhouette edge
        px = im.load()
        ring = {(x + a, y + b) for x, y in cells for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))} - cells
        for x, y in ring:
            if y < 16 or not px[x, y][3]:
                continue
            if all(px[x + a, y + b][3] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                dot(im, x, y, '000000')


# rattle, behind the hump: solid stripes so nothing drops out on black
RATTLE = [
    '.ff......',
    '.fff.....',
    '.ggg.....',
    '.gggg....',
    '..gggg...',
    '..ffff...',
    '...ffff..',
    '...ffff..',
    '....gggg.',
    '....ggggg',
    '.....ffff',
]
stamp(im, grid(RATTLE, PAL), 1, 8)

# far half of the rope, comes down behind the hump
rope([(26, 3), (22, 2), (18, 3), (15, 6), (14, 9), (14, 12), (15, 16)], 1)

BODY = [
    '................aaaaaaaa................',
    '.............aaaaaaaaaaabb..............',
    '...........aaaaaaaaaaaaabbbb............',
    '..........aaaaaabbbbbbbbbbbbb...........',
    '.........aaaaabbbbbKbbbbbKbbbc..........',
    '........aaaabbbbbbKbbbbbKbbbbcc.........',
    '.......aaaabbbbbbKbbbbbbbbbbbbcc........',
    '.......aaabbbbbbbbbbKKKKKKKbbbbcc.......',
    '......aaabbbbKbbbbKKaaaaaabKKbbcc.......',
    '......aabbbbKbbbbKaaaaaaaabbbKbccc......',
    '......aabbbbbbbbbKaaKKaaabKKbbKbcc......',
    '......aabbbbbbbbbKaaaaaaabbbbbKbcc......',
    '......abbbbbbbbbbbKaaaaaabbbbKbccc......',
    '......abbbcbbbcbbbbKaaaaabbbKbcccc......',
    '......bbbccbbcccbbbbKaaabbcKcbcccc......',
    '......cbcc.cbcc.cbcbKaabcKccc.cc........',
    '......cc.eKKccKKKcKKKKabKKKKc..c........',
    '......c..ddKKKddKKKddddddddeeeee........',
    '.........dddddddddddddddddeeeeeee.......',
    '.........dddddddddddddddddeeeeee........',
    '.........ddddddddKddddddddddeeee........',
    '.........ddddddddKdddddddeeeeee.........',
    '.........ddddddeKeeddddeeeeeee..........',
    '..........dddeeeKeeeKKKeeeeee............',
    '..........ddddee....ddddddee............',
    '...........dddee......ddKdddee..........',
    '...........dKKee........ddKKdee.........',
    '...........dddee.........dddee..........',
    '...........ddee..........ddddee.........',
    '..........dddee..........dddee..........',
    '..........dddee.........dddee...........',
    '..........ddee..........ddee............',
    '..........cdde..........cKKc............',
    '..........cKKc..........cbcc............',
    '..........cbcc..........abbcc...........',
    '.........abbcc..........aaKabbc.........',
    '........aabbbc..........a.ab.bc.........',
    '.......aabKabKbc........................',
    '.......ab.ab.bc.........................',
]
stamp(im, grid(BODY, PAL), 0, 13)

# near half: rope leaves the chin, swings right across the belly and climbs
rope([(22, 29), (22, 31), (24, 33), (28, 34), (32, 33), (34, 31), (36, 27), (36, 20), (36, 14), (35, 10), (32, 6), (29, 4), (26, 3)], line=True)

im = outline(im)
save(im)
