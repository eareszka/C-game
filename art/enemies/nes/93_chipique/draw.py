from pix import *

# Parts and where they attach:
# - head: wedge facing right, sits on the top of the neck; white chin runs into the belly
# - blood drip: hangs from the mouth line, through the chin
# - neck: rises from inside the boat at the left; lilac back on the left, white belly on the right
# - belly run: the neck's belly bends right along the rim and climbs the far side of the loop,
#   so the belly is always on the inside of the curl and the back is hidden by the rim
# - loop: arch over the belly run; its left foot passes behind the belly run
# - tail: leaves from behind the stern at the right, bends up, ends in a fork
# - boat: hull in front of the neck, loop and rider
# - rider: hood and robe sit in the boat right of the loop, hollow cowl with two red eyes
# - paddle: upright, in front of the hull, held by the rider's sleeve

LILAC = 'b69cee'
LILACD = '664b95'
WHITE = 'fcfcfc'
TAN = 'd7a175'
TAND = '8d6b4f'
ROBE = '474751'
ROBED = '292931'
RED = 'b70000'
K = '000000'

PAL = {'a': LILAC, 's': LILACD, 'w': WHITE, 'r': ROBE, 'd': ROBED, 'e': RED}

im = canvas(82, 76)

# loop, drawn first so the neck and the rider overlap it
stamp(im, grid([
    '..........aaaaaaaa..........',
    '.......aaaaaaaaaaaaaa.......',
    '.....aaaaaaaaaaaaaaaaaa.....',
    '....aaaaaaaaaaaaaaaaaaass...',
    '...aaaaaaaaaaaaaaaaaaaasss..',
    '..aaaaaaaaaaaaaaaaaaaaasss..',
    '..aaaaaawwwwwwwwwwaaaasssss.',
    '.aaaaawwwwwwwwwwwwwwaaassss.',
    '.aaaawww........wwwwaaassss.',
    'aaaawww..........wwwaaassss.',
    'aaaaww...........wwwaaassss.',
    'aaaaww............wwaaassss.',
    'aaaaww............wwaaassss.',
    'aaasKKK...........wwaaassss.',
    '...wwwwwwwwwwwwwwwwwaaassss.',
    '...wwwwwwwwwwwwwwwwwaaassss.',
    '...wwwwwwwwwwwwwwwwwaaassss.',
    '...wwwwwwwwwwwwwwwwwaaassss.',
], PAL), 15, 36)

# neck: back, then belly
poly(im, [(9, 10), (7, 16), (6, 22), (5, 30), (4, 38), (3, 46), (2, 52), (6, 56), (24, 56), (24, 50), (19, 49), (16, 46), (15, 43), (14, 38), (14, 30), (15, 22), (16, 13)], LILAC)
poly(im, [(9, 15), (12, 15), (11, 18)], LILACD)
poly(im, [(4, 51), (8, 49), (11, 49), (14, 52), (14, 54), (5, 54)], LILACD)
poly(im, [(12, 13), (16, 13), (15, 22), (14, 30), (14, 38), (15, 43), (16, 46), (19, 49), (24, 50), (24, 54), (17, 54), (13, 50), (11, 44), (10, 38), (10, 30), (11, 22)], WHITE)
# line where the neck passes in front of the loop's left foot
rect(im, 16, 43, 1, 3, K)
rect(im, 17, 46, 1, 1, K)
rect(im, 18, 47, 1, 1, K)
rect(im, 19, 48, 1, 1, K)

# tail with fork
stamp(im, grid([
    '................as',
    '..........sa...aa.',
    '...........aa..aa.',
    '............aa.aa.',
    '.............aaaa.',
    '.............aaas.',
    '..............aas.',
    '..............was.',
    '..............was.',
    '..............was.',
    '..............was.',
    '.............wwas.',
    '.............wwas.',
    '............wwaas.',
    '..........wwwaas..',
    'wwwwwwwwwwwwaas...',
    'wwwwwwwwwwaaas....',
    'aaaaaaaaaaass.....',
    'ssssssssss........',
], PAL), 56, 41)

# rider
stamp(im, grid([
    '.......rr.......',
    '......rrrr......',
    '.....rrrrrdd....',
    '....rrrrrrrrd...',
    '..rrrrrrrrrrdd..',
    '..rrKKKKKKrrdd..',
    '.rrKKKKKKKKrdd..',
    '.rrKKKKKKKKrddd.',
    '.rrKeKKKKeKrddd.',
    '.rrKKeKKeKKrddd.',
    '.rrrKKKKKKrrdddd',
    '.rrrrKKKKrrrdddd',
    'rrrdddddddrrdddd',
    'rrrrrrrrrrrrdddd',
    'rrrrrrrrrrrddddd',
    'rrrrrrrrrdrrdddd',
    'rrrrrrrrrdrrdddd',
    'rrrrrrrrdrrrdddd',
    'rrrrrrrrdrrrdddd',
    'rrrrrrrrdrrrdddd',
    'rrrrrrrrdrrrdddd',
], PAL), 44, 34)

# boat: rim line, hull, shadow, planks
poly(im, [(0, 52), (8, 53), (18, 55), (42, 55), (50, 54), (58, 52), (58, 54), (55, 59), (48, 63), (40, 65), (14, 65), (6, 62), (2, 58)], TAN)
poly(im, [(9, 62), (22, 63), (30, 62), (42, 62), (49, 59), (54, 56), (57, 54), (55, 59), (48, 63), (40, 65), (14, 65)], TAND)
rect(im, 0, 51, 3, 1, K)
rect(im, 3, 52, 6, 1, K)
rect(im, 9, 53, 9, 1, K)
rect(im, 18, 54, 25, 1, K)
rect(im, 43, 53, 8, 1, K)
rect(im, 51, 52, 4, 1, K)
rect(im, 55, 51, 4, 1, K)
rect(im, 8, 57, 13, 1, TAND)
rect(im, 25, 59, 9, 1, TAND)
rect(im, 47, 56, 5, 1, TAND)

# paddle: shaft and blade in front of the hull
rect(im, 41, 41, 1, 16, K)
rect(im, 44, 41, 1, 16, K)
rect(im, 42, 41, 2, 19, TAN)
rect(im, 43, 41, 1, 19, TAND)
rect(im, 39, 57, 2, 1, K)
rect(im, 45, 57, 2, 1, K)
poly(im, [(40, 59), (45, 59), (45, 66), (43, 69), (42, 69), (40, 66)], TAN)
poly(im, [(43, 59), (45, 59), (45, 66), (43, 69)], TAND)
rect(im, 39, 58, 1, 8, K)
rect(im, 46, 58, 1, 8, K)
rect(im, 40, 58, 6, 1, K)

# rider's sleeve, gripping the shaft: robe tone, under-edge in shadow, dark cuff round the shaft
rect(im, 45, 47, 5, 3, ROBE)
rect(im, 45, 50, 5, 1, ROBED)
rect(im, 41, 47, 4, 4, ROBED)
rect(im, 45, 46, 6, 1, K)
rect(im, 45, 51, 5, 1, K)

# head, drawn over the top of the neck
stamp(im, grid([
    '.......aaaaaa...........',
    '.....aaaaaaaaaa.........',
    '...aaaaaaaaaaaaaaa......',
    '..aaaaaaaaaaaaaaaaaa....',
    '.aaaasssaaaaaaaaaaaaa...',
    '.aaaaaaasaaaaaaaaaaaaa..',
    'aaaaaaKKaaaaaaaaaaaaaaa.',
    'aaaaaaaaaaaaaaaaaaaasaaa',
    'aaaaaaaaaaaaaaaaaaaaaaaa',
    'aaaaaaaaaaaaaaaaaasssss.',
    'aaaaaaaaaKKKKKKKKKKKKK..',
    'aaaaaaaKKwwwwwwwwwwwss..',
    '.aaaaawwwwwwwwwwwwsss...',
    '..aaaawwwwwwww..........',
    '..aaawwwwww.............',
], PAL), 8, 0)

# blood: from the mouth, over the chin, hanging below
rect(im, 21, 11, 3, 3, RED)
rect(im, 21, 14, 2, 5, RED)
rect(im, 22, 19, 1, 3, RED)

im = outline(im)
save(im)
