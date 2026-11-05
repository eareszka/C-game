from pix import *

PAL = {
    'a': 'fcfcfc',  # hide light
    'b': 'c6ccda',  # hide mid
    'c': '848694',  # hide shade
    'd': '7c0a1b',  # mouth dark
    'r': 'b70000',  # tongue
    't': 'ec8476',  # tongue light
}

HALF = [
    #0123456789012345
    "...............b",
    "..............ab",
    "..............ab",
    ".............abc",
    ".............abc",
    "............abbc",
    "............abcc",
    "..........aaKKKK",
    ".........aaaaaaa",
    "........aaacaaaa",
    ".......aaaaaacaa",
    "......aacaaaaaaa",
    ".....baaacKaaaca",
    "....aabaaaKaaaaa",
    "...aaaaacaaaacaa",
    "..abbKaaaaaaaaaa",
    ".abbcKaaacaaaaab",
    "abbcc.aaaaaKKKKK",
    "abcc..baaaKKdKKd",
    "bcc...aaaKdKddKr",
    ".c.....aaKddddrr",
    "......baaKdddrrt",
    "......baaKKddrrr",
    "......bbaaKKdKrr",
    ".......baaKKKKrr",
    ".......bbbbaaKrr",
    ".........bbbbKrr",
    "...........cc.rr",
    "..............rr",
]


def shaded(row):
    """Mirror a half row, then push the right side down a tone for upper-left light."""
    right = list(row[::-1])
    filled = [i for i, ch in enumerate(right) if ch not in '.K']
    edge = filled[-1] if filled else -1
    for i, ch in enumerate(right):
        if i > edge - 3 and ch == 'a':
            right[i] = 'b'
        elif i > edge - 2 and ch == 'b':
            right[i] = 'c'
        elif ch == 't':
            right[i] = 'r'
    return row + ''.join(right)


im = grid([shaded(r) for r in HALF], PAL)
im = outline(im)
save(im)
