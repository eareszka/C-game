from pix import *

PAL = {
    'a': 'f0b890',  # face and neck, lit
    'b': 'd7a175',  # face and neck, shade
    'p': 'ec8476',  # collar and belly, lit
    'r': 'b6433d',  # collar and belly, shade
    'd': '34343e',  # hide, dark
    'g': '595965',  # hide, mid
    'h': '848694',  # hide, ridge tips
}
HALF = 34  # columns left of and including the centre column

# Upper body: right-aligned, the last character is the centre column.
UP = [
    'aaa......',
    'aKa......',
    'aKb......',
    'aab......',
    '.ab......',
    '.ab......',
    '.ab......',
    '.ab......',
    '.ab......',
    '..ab.....',
    '..ab.....',
    '..ab.....',
    '..ab.....',
    '..ab.....',
    '.....aab....',
    '....aaab.aaa',
    '....aaaaaaaa',
    '...aaaabbaaa',
    '..aaaaaaaaaa',
    '.aaabaaaaaaa',
    'aaaabaaaaaaa',
    '.aaaabaaaaaa',
    '.aaaaaabaaaa',
    'aaaKaaaaaaaa',
    '.aaaKKKKKKKK',
    'aabaaaaaaaaa',
    '.aabbaaaaaaa',
    '..aabbbbaaaa',
    '...bbbbbbbbb',
    '....KKKKKKKK',
    '....pppppppp',
    '....pppppppp',
    '.....rrrrrrr',
    '.....KKKKKKK',
    '......aaaaaa',
]

# Lower body: spreading hide on the left, neck and skirt on the right.
#       offset -33 .......................... -7
LOW = [
    ('....................h......', '.Kaaaaaa'),
    ('....................hg...h.', '.Kaaaaaa'),
    ('...............h....hg...hg', '.Kaaaaaa'),
    ('...............hg..hgg..hgg', '.Kaaaaaa'),
    ('..........h....hg..hgg..hgg', '.Kbbbbbb'),
    ('..........hg..hgg.hggg.hggg', '.Kpppppp'),
    ('.....h....hg..hgg.hggg.hggg', '.KKKKKKK'),
    ('.....hg..hgg.hggg.hgggKKggg', '.Kaaaaaa'),
    ('.....hg..hgg.hgggKKggdddKgg', '.Kaaaaaa'),
    ('.h..hgg.hgggKKgggddddggdddK', '.Kbbbbbb'),
    ('.hg.hggKKgggddddggggKKggddd', '.KKKKKKK'),
    ('.hgghgggddddggggKKdddggggKK', '.Kppppppp'),
    ('ggggggdddKKgggdddgggKKddddd', 'Kpppppppp'),
    ('dddggggKKdddddgggdddddggggd', 'Kpprppppp'),
    ('.KKKKKKKKKKKKKKKKKKKKKKKKKK', 'Kpprrpppp'),
    ('..ppppppppppppppppppppppppp', 'Krrpprppp'),
    ('....rrrrrrppppppppppppppppp', 'Krrrrrrrr'),
    ('.........rrrrrrrrrrrrrrrrrr', 'rr.rrr.rr'),
]


def left_half():
    rows = [r.rjust(HALF, '.') for r in UP]
    for wing, body in LOW:
        wing = wing.ljust(HALF, '.')
        body = body.rjust(HALF, '.')
        rows.append(''.join(b if b != '.' else w for w, b in zip(wing, body)))
    return rows


SKIN, PINK, HIDE = set('ab'), set('pr'), set('dgh')


def material(ch):
    for m in (SKIN, PINK, HIDE):
        if ch in m:
            return m
    return None


def relight(row):
    """Keep the light on the upper left: short runs on the right half keep their left-to-right order."""
    chars = list(row)
    mid = HALF - 1
    x = 0
    while x < len(chars):
        m = material(chars[x])
        if m is None:
            x += 1
            continue
        end = x
        while end + 1 < len(chars) and chars[end + 1] in m:
            end += 1
        if x > mid and end - x + 1 <= 3:
            chars[x:end + 1] = chars[x:end + 1][::-1]
        elif x <= mid < end and m is SKIN and end - x + 1 >= 5:
            for i in (end, end - 1):
                chars[i] = 'b'
        x = end + 1
    return ''.join(chars)


im = grid([relight(r) for r in mirror(left_half())], PAL)
im = outline(im)
save(im)
