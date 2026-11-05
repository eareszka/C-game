from pix import *

PAL = {
    'h': 'a8f0bc',  # green highlight on the crown
    'a': '4fa667',  # green lit
    'b': '2c6c44',  # green shade
    'o': 'fc9838',  # orange chest and feet
    'r': 'b6433d',  # red belly
    'n': '815423',  # outer leg tube
    'p': 'cebe82',  # inner telescoping tube
}

ROWS = [
    "........hhaa.......",
    ".......hhaaaa......",
    ".......aKKaabb.....",
    ".......aaaabbbb....",
    "......oKKKbbabb....",
    ".....oooo...Kabb...",
    ".....ooooo....abb..",
    ".....ooorr.....abb.",
    ".....orrrr......Kb.",
    "..aabrrrrK.........",
    ".abbKKKKKK.........",
    ".ab..nn.nn.........",
    ".ab..nn..nn........",
    ".ab..nn..nn........",
    ".ab..nn...nn.......",
    "ab...Kp...nn.......",
    "ab....p....Kp......",
    "ab....p.....p......",
    "ab....p.....p......",
    ".ab...p.....p......",
    ".ab...p......p.....",
    "..aa..p......p.....",
    "...aa.p.......p....",
    "....a.oo......ooo..",
]

im = grid(ROWS, PAL)
im = outline(im)
save(im)
