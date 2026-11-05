from pix import *

PAL = {
    'h': '848694',  # hide, lit edge
    'l': '595965',  # hide, mid
    'd': '34343e',  # hide, shade
    'r': 'b70000',  # stripe
    'q': '7c0a1b',  # stripe, shade
    'e': 'fc9838',  # eye
}

# body, x5..17
BODY = [
    "....hllld....",
    "...hlllldd...",
    "..hlllllldd..",
    "..hlKKKKKdd..",
    ".hlKlllllKdd.",
    ".hlllllllddd.",
    "hlellllllded d".replace(' ', ''),
    "hlellllllded d".replace(' ', ''),
    "hlKKlllllKKdd",
    "hllKKlllKKddd",
    "hlllKKrKKlddd",
    "hllllKrKldddd",
    "hllllrrqldddd",
    "hdKllrrqddKld",
    "hllllrrqldddd",
    "hlldlrrqdlddd",
    "hllllrrqldddd",
    "hdKllrrqddKld",
    ".hlllrrqlddd.",
    ".hldlrrqdldd.",
    ".hlllrrqlddd.",
    "..hllrrqldd..",
    "..hdlrrqdld..",
    "...hlrrqdd...",
    "...hllrqdd...",
    "....hlrdd....",
    "....hlrdd....",
    ".....hrd.....",
    "....hlrdd....",
    "...hlKrKdd...",
    "..hlKl.dKdd..",
    ".hlKl...dKdd.",
    ".hl.......dd.",
]

# left fins, x0..6: the tips reach for the head, the wrong way round
FIN = {
    6:  "..h....",
    7:  "..h....",
    8:  "h.l.h..",
    9:  "h.l.h..",
    10: "lKlKl..",
    11: "dlKlKl.",
    12: ".dlKlKl",
    13: ".ddlKlK",
    14: "...dlKl",
    15: "....dll",
    16: ".....dl",
    17: "......d",
    19: ".....h.",
    20: ".....hl",
    21: "......h",
}

SHADE = str.maketrans({'h': 'l', 'l': 'd'})
rows = []
for y, b in enumerate(BODY):
    f = FIN.get(y, ".......")
    rows.append(list(f + b + f[::-1].translate(SHADE)))


def both(y, x, left, right):
    rows[y][x] = left
    rows[y][26 - x] = right


# the lower fins run into the body
both(21, 7, 'l', 'd')
both(21, 8, 'd', 'd')
both(22, 7, 'l', 'd')
both(22, 8, 'd', 'd')
both(23, 8, 'd', 'd')
both(23, 9, 'd', 'd')

im = grid([''.join(r) for r in rows], PAL)
im = outline(im)
save(im)
