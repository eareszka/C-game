from pix import *

PAL = {
    'a': '4fa667',  # snake green, lit
    'b': '2c6c44',  # snake green, shade
    'h': 'a8f0bc',  # belly plates, pale jaw
    'd': 'f0bc3c',  # leopard, lit; snake eyes
    'e': 'c18a39',  # leopard, mid / leg lit
    'f': '815423',  # leopard, shade / leg shade
    's': '583518',  # spots, hooves
    'r': 'b6433d',  # tongue
}

rows = [
    #012345678901234567890123
    "......aaaaabbb..........",  # 0  viper head, wide at the jaw
    "....aaaaaaabbbbb........",
    "...aaaabbbbbbbbbbb......",
    "...aaddbbbbbbddbbb......",  # eyes
    "...aabbbbbbbbbbbbb......",
    "....abbbbbbbbbbbb.......",
    ".....abKbbbKbbbb........",  # nostrils
    "......bKKKKKKKb.........",  # mouth
    "........hhhhKahhb.......",  # pale jaw, neck starts behind it
    ".........r.r.ahhb.......",  # forked tongue
    "..........r...ahhb......",
    "..........r...aKKb......",
    "..............ahhb......",
    ".............ahhb.......",
    ".............aKKb.......",
    "............ahhb........",
    ".........dddKKKKe.......",  # 16 collar
    "......ddddddddddeee.....",
    "....ddssdddssdeessef....",  # spots, row one
    "...dddsKdddsKeeesKeff...",
    "...dddddddeeeeeeeeeff...",
    "...ssdddsseeesseeessf...",  # spots, row two
    "...sKeeesKeeesKeeesKf...",
    "...eeeeKeeeeeeeeKeeff...",  # shoulder lines
    "....sseKeesseeeKessff...",  # spots, row three
    "....efffKfffffKffffff...",  # belly, leg tops
    "....ef..ef....ef..ef....",  # 26
    "....ef..ef....ef..ef....",
    "...ef...ef....ef...ef...",
    "...ef...ef....ef...ef...",
    "..eff..eff...eff...eff..",  # knees
    "..ef....ef....ef....ef..",
    "..ef....ef....ef....ef..",
    ".ef.....ef....ef.....ef.",
    ".ef.....ef....ef.....ef.",
    ".ss....ss....ss......ss.",
]

im = grid(rows, PAL)
im = outline(im)
save(im)
