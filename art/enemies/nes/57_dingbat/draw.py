from pix import *

PAL = {
    'a': 'e8e0c0',  # pale face, belly, antlers
    'b': 'cebe82',  # wing leading edge, belly shade
    'c': 'b2966a',  # light brown
    'd': '94703d',  # brown
    'e': '633e1b',  # dark brown
    'g': '848694',  # feet
}

WING = [
    "bb..........",
    "cbbbb.......",
    "dccbbbbb....",
    "edddccbbbbb.",
    ".eedddccbbbb",
    "...dKdddcccc",
    "..eddKdddKcc",
    "....edKddKdd",
    "...eddKdKddd",
    ".....edKdKdd",
    "....eedKdKde",
    "......edKdee",
    "......e.edee",
    "........e.e.",
]

BODY = [
    "...cccdd...",
    "..cccdddd..",
    ".ccaaeaadd.",
    "KcaKaaaKadK",
    "KcaKaeaKadK",
    "KcaaKeKaadK",
    "KcaaaeaaadK",
    "KdcaKaKadeK",
    "KcddcccddeK",
    "caaaabdddde",
    "cbababbddde",
    "cabababddde",
    ".caaaabdde.",
    ".ccaaabdde.",
    "..ddcddee..",
]

ANTLERS = [
    "a..a...a..a",
    ".a.a...a.a.",
    "..aa...aa..",
]

FEET = [
    "gg.g.g.gg",
    "g..g.g..g",
]

im = canvas(31, 20)
stamp(im, grid(WING, PAL), 0, 1)
stamp(im, grid([r[::-1].replace('b', 'c') for r in WING], PAL), 19, 1)
stamp(im, grid(ANTLERS, PAL), 10, 0)
stamp(im, grid(BODY, PAL), 10, 3)
stamp(im, grid(FEET, PAL), 11, 18)

im = outline(im)
save(im)
