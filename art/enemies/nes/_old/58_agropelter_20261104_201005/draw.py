from pix import *

PAL = {
    'a': 'f0b890',  # skin
    'b': 'd7a175',  # skin shade
    'e': 'b2966a',  # tan chest and fur light
    'c': '8d6b4f',  # fur
    'd': '633e1b',  # fur dark
    'f': 'e8e0c0',  # teeth
}

HEAD = [
    '..e...e...c..',
    '..ec.ecc.cd..',
    '.eeccccccccd.',
    '.ecccccccccd.',
    'eccddaaaddccd',
    '.caaKaaaKabd.',
    'ecaaKaaaKabcd',
    '.caaaKaKaabd.',
    'ecaKKKKKKKbcd',
    '.caKfffffKbd.',
    'ecaaKKKKKabcd',
    '.ccaaaaabbdd.',
    '..cccccdddd..',
]

BODY = [
    '...ceeeeeeed...',
    '..cceeeeeeedd..',
    '..ccKeeeeeKdd..',
    '..cccKeeeKddd..',
    '..ccccKeKdddd..',
    '..ccccdKddddd..',
    '..KKKKdddKKKK..',
    '.eccccKdKeccdd.',
    'ecccccKdKecccdd',
    'ecccddK.Kecccdd',
    '.cdddK...Kcddd.',
    '..aab.....aab..',
    '.aaKab...aaKab.',
]

im = canvas(35, 26)
stamp(im, grid(BODY, PAL), 10, 13)
stamp(im, grid(HEAD, PAL), 11, 0)


def arm(cols, light='f0b890', shade='d7a175'):
    for x, y, h in cols:
        rect(im, x, y, 1, 1, light)
        if h > 1:
            rect(im, x, y + 1, 1, h - 1, shade)


# left arm: rises off the shoulder, peaks, then falls away to the hand
arm([(12, 14, 2), (11, 13, 2), (10, 12, 2), (9, 11, 2), (8, 10, 2), (7, 10, 2),
     (6, 10, 2), (5, 11, 2), (4, 12, 2), (3, 13, 1), (2, 14, 1)])
# left hand
rect(im, 1, 14, 2, 2, 'f0b890')
rect(im, 0, 13, 1, 1, 'f0b890')
rect(im, 0, 15, 1, 1, 'd7a175')
rect(im, 1, 17, 1, 1, 'd7a175')
rect(im, 1, 16, 1, 1, 'd7a175')

# right arm: dips off the shoulder, runs low, then whips up to the hand
arm([(22, 14, 2), (23, 15, 2), (24, 16, 2), (25, 17, 2), (26, 18, 2), (27, 18, 2),
     (28, 18, 2), (29, 17, 2), (30, 16, 2), (31, 15, 1), (32, 14, 1)])
# right hand
rect(im, 32, 12, 2, 2, 'f0b890')
rect(im, 34, 11, 1, 1, 'f0b890')
rect(im, 34, 13, 1, 1, 'd7a175')
rect(im, 32, 10, 1, 2, 'f0b890')

im = outline(im)
save(im)
