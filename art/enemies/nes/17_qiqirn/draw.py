from pix import *

PAL = {
    'a': 'f0b890',  # lit skin
    'b': 'd7a175',  # mid skin
    'c': '8d6b4f',  # shaded skin, hair highlight
    'd': '764c20',  # hair
    'w': 'e8e0c0',  # teeth
}

TAIL = [
    '..cd....',
    '.ccdd...',
    'ccddKd..',
    'cddKdd..',
    'cddddd..',
    '.dKdd...',
    '..add...',
    '..ab....',
    '..ab....',
    '..abb...',
    '...ab...',
    '...abb..',
    '....abb.',
    '.....abb',
]

BODY = [
    '.......aaaaaaaaaaaaaaaaaa',
    '...aaaaaaaaaaaaaaaaaaaaab',
    '.aaaaaaKaaaaaaaaaaKaaKabb',
    'aaaaaaKbbaaaaaaaaaKbaKbbc',
    'aaaaaKbbbbbbbbbbbbbKbbKcc',
    'abaaaKbbcccbbbbbbbbbbbbcc',
    '.bbbKbcc....KccccbbbbbccK',
    '..bbbc.........Kccbbbcc..',
]

NEAR_REAR = [
    'aabbK..',
    'aabbcK.',
    '.aabcK.',
    '.Kabc..',
    '..abc..',
    '...abc.',
    '...abc.',
    '....ac.',
    '....ac.',
    '....ac.',
    '...cdd.',
    '..cdddd',
    '..dddddd',
    '..dKdKdd',
]

FAR_REAR = [
    'bcc.',
    'bcc.',
    'bc..',
    'bc..',
    '.bc.',
    '.bc.',
    '.bc.',
    '.cc.',
    '.cdd',
    'cdddd',
    'dKdKd',
]

NEAR_FRONT = [
    'aabbK',
    'aabcK',
    'aabc.',
    '.abc.',
    '.Kac.',
    '..ac.',
    '..ac.',
    '..ac.',
    '..ac.',
    '..ac.',
    '.cdd.',
    'cdddd.',
    'dddddd',
    'dKdKdd',
]

FAR_FRONT = [
    'cc.',
    'bc.',
    'bc.',
    'bc.',
    'bc.',
    'bc.',
    'cc.',
    'cdd',
    'dddd',
    'KdKd',
]

NECK = [
    '.....aabb',
    '....aaabb',
    '...aaaabc',
    '..aaaabbc',
    '.aaaaabbc',
    'Kaaaaabbc',
    'aKaaabbbc',
    'aaKaabbcc',
]

HEAD = [
    '.c........c.',
    '.cd......dd.',
    '.cdd....ddd.',
    '.abd....dbc.',
    '.aabaaaabbc.',
    '.aaaaaaaabc.',
    '.aKKaaaKKbc.',
    '.aaaaaaabbc.',
    '..aaaaabbc..',
    '...aaaabc...',
    '...aaKKbc...',
    '..cdaabbdd..',
    '.cddKKKKddd.',
    '.ddwKwwKwdd.',
    '.dddddddddd.',
    '..dKddKddd..',
    '...d..d.....',
]

im = canvas(60, 50)
stamp(im, grid(FAR_REAR, PAL), 11, 25)
stamp(im, grid(FAR_FRONT, PAL), 28, 25)
stamp(im, grid(TAIL, PAL), 0, 3)
stamp(im, grid(BODY, PAL), 5, 17)
stamp(im, grid(NEAR_REAR, PAL), 4, 23)
stamp(im, grid(NEAR_FRONT, PAL), 23, 23)
stamp(im, grid(NECK, PAL), 22, 11)
stamp(im, grid(HEAD, PAL), 25, 0)

im = outline(im)
save(im)
