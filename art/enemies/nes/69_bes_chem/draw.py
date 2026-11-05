from pix import *

PAL = {
    'a': '633e1b',  # hide, shade
    'b': '94703d',  # hide, mid
    'c': 'c18a39',  # hide, lit
    'p': '3b2a58',  # mouth
    't': 'fcfcfc',  # teeth
    's': 'bcbeca',  # teeth, shade
    'y': 'fae488',  # eyes
    'f': 'd7a175',  # legs
}

W = 31

BODY = {  # x = 7..23
    0: "......c...b......",
    1: ".....ccbbbba.....",
    2: "....ccbbbbbba....",
    3: "...cayabbbayaa...",
    4: "..caayabbbayaaa..",
    5: "..cbbbbaaabbbba..",
    6: ".ccbbbbKaKbbbbaa.",
    7: ".ccbbbKKKKKbbbaa.",
    8: ".ccbKKttpttKKbaa.",
    9: "ccbKKtptptpsKKbaa",
    10: "ccbK" + "ptptpspsp" + "Kbaa",
    11: "cbK" + "tpppppppppt" + "Kaa",
    12: "cbK" + "ttpppppppss" + "Kaa",
    13: "cbK" + "ppppppppppp" + "Kaa",
    14: "cbK" + "ttpppppppss" + "Kaa",
    15: "bbK" + "tpppppppppt" + "Kaa",
    16: "bbbK" + "ptptpspsp" + "Kaaa",
    17: "bbbKKtptptpsKKaaa",
    18: ".bbbKKttpssKKaaa.",
    19: "..bbbbKKKKKaaaa..",
    20: "...babbabaaaaa...",
    21: ".....bbaaaa......",
}

WING = {  # x = 0..7
    6:  ".......c",
    7:  "......cc",
    8:  ".....ccb",
    9:  "....ccb.",
    10: "...ccba.",
    11: "..ccbab.",
    12: ".ccbabK.",
    13: "ccbabKb.",
    14: "cbabKba.",
    15: "cababKa.",
    16: "c.b.ab..",
    17: "b.b.a...",
    18: "..a.....",
}

LEGS = {
    22: "............f.....f............",
    23: "............f.....f............",
    24: "............f.....f............",
    25: "............f.....f............",
    26: "..........ffff...ffff..........",
}

DARKER = {'c': 'b', 'b': 'a', 'a': 'K', 'K': 'K', '.': '.'}

rows = [['.'] * W for _ in range(27)]

for y, r in WING.items():
    for i, ch in enumerate(r):
        if ch != '.':
            rows[y][i] = ch
            rows[y][W - 1 - i] = DARKER[ch]

for y, r in BODY.items():
    for i, ch in enumerate(r):
        if ch != '.':
            rows[y][7 + i] = ch

for y, r in LEGS.items():
    for i, ch in enumerate(r):
        if ch != '.':
            rows[y][i] = ch

im = grid([''.join(r) for r in rows], PAL)
im = outline(im)
save(im)
