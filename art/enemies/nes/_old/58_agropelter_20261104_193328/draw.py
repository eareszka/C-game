from pix import *

PAL = {
    'a': 'f0b890',  # skin
    'b': 'd7a175',  # skin shade
    'c': '967448',  # fur
    'd': '633e1b',  # fur shade
    'e': 'b2966a',  # chest
    'f': 'e8e0c0',  # teeth
}

im = grid([
    "........c.c.d........",
    "........ccccd........",
    ".......ccccddd.......",
    ".......cbbbbbd.......",
    "......ccaKaKadd......",
    ".......caaaaad.......",
    ".......cKfffKd.......",
    "...aaa.ccbbbdd.......",
    "..aa.aaabKKKbaa...a.a",
    ".aa.....ceeedaaaa..aa",
    "aa......ceeed...aa.a.",
    "a.a.....ccedd....aaa.",
    ".......cKKeKKd.......",
    "......ccccKccdd......",
    "......ccdd.dddd......",
    ".....aaa.....aaa.....",
], PAL)

im = outline(im)
save(im)
