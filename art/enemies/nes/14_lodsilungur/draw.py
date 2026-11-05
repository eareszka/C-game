from pix import *

PAL = {
    'a': 'dcf0ff',  # lit pale hide
    'b': 'bcbeca',  # pale hide
    'c': '848694',  # shaded hide, crest
    'd': '595965',  # deep crest and fin rays
    'm': '7c0a1b',  # mouth inside
    'r': 'b70000',  # tongue
    't': 'ec8476',  # tongue light
}

# Left half and centre column. 'a' is lit on the left and base on the right,
# 'e' is base on the left and shade on the right, 'h' is lit on both sides.
HALF = [
    "...............c",
    "..............cc",
    "..............cb",
    ".............ccb",
    ".............cdb",
    "............ccdb",
    "............cdcb",
    "...........ccdcb",
    "..........cccdcb",
    ".........ccdccdc",
    "........aKaaKaaK",
    "......aaaaaaaahh",
    "......a.aaaaahhh",
    "....aaaaaaaaaahh",
    "....a.aaKaaahhhh",
    "..aaaaaaKaaaaahh",
    "..a.aaaaaaaaahhh",
    "....eaaaaaaaaahh",
    "cc..eaaaeKKKKKKK",
    "cdcKeaaaKmKKKmKK",
    "ccdcKaaemmmKmmmK",
    "cdccKaaemmmmmmmm",
    ".cdcKeaemmmmmmmm",
    ".ccdcKeemmmmmmmm",
    "..cdcKeemmKmmmmm",
    "..ccKeeemKKKmmmm",
    "...c.eeeeKKKKKKK",
    "...eeeebbbbbbbbb",
    "...e.eeebbbbbbbb",
    ".....eeeebbbbbbb",
    ".....e.e.ccbbbbb",
    ".........c.cc.cc",
]

TONGUE = [
    ".....rr....",
    "....rrrr...",
    "...rtrrrr..",
    "...rtrmrr..",
    "..rttrmrrr.",
    "..rtrrmrrr.",
    ".KrtrrmrrK.",
    ".KrrrrrrrK.",
    "..KrrrrrK..",
    "...KKKKK...",
]

# Hair strokes on the left half; each is mirrored in a darker tone on the right.
HAIR = [
    [(13, 11), (12, 12), (12, 13), (11, 14)],
    [(10, 11), (9, 12), (8, 12)],
    [(6, 13), (6, 14), (6, 15), (5, 16)],
    [(10, 16), (10, 17), (9, 17)],
    [(13, 15), (12, 16), (12, 17)],
    [(6, 21), (6, 22), (7, 23)],
]

LEFT = str.maketrans({'e': 'b', 'h': 'a'})
RIGHT = str.maketrans({'a': 'b', 'e': 'c', 'h': 'a'})

rows = []
for r in HALF:
    rows.append(r.translate(LEFT) + r[-2::-1].translate(RIGHT))

im = canvas(31, 32)
stamp(im, grid(rows, PAL), 0, 0)

for stroke in HAIR:
    for x, y in stroke:
        dot(im, x, y, PAL['b'])
        dot(im, 30 - x, y, PAL['c'])

stamp(im, grid(TONGUE, PAL), 10, 21)

im = outline(im)
save(im)
