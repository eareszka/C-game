from pix import *

PAL = {
    'a': '664b95',  # lit hide
    'b': '3b2a58',  # mid hide
    'c': '301b5a',  # shaded hide
    'g': '9797aa',  # grid lines, toes, tusk shade
    'r': 'b6433d',  # red edge
    'd': '7c0a1b',  # red edge shade
    't': 'e8e0c0',  # tusk
    'e': 'fcfcfc',  # eye
}

im = grid([
    '.......aaagbbb.......',
    '.....aagaaagbgbb.....',
    '...aaggaaagbbbggbb...',
    '..aagaagggggggbbgbb..',
    '.aagaagKKKKKKKgbbgbb.',
    '.aaaagcccceccccgbbbb.',
    '.gggggcccceccccggggg.',
    '.agaaaagggggggbbbgbc.',
    '.bbgbbbgbbbbbgcccgcc.',
    '..rrrKKKKKKKKKKKddd..',
    'aarrrKrrrrrrrrrKdddab',
    'aarrKrrKKKKKKKddKddab',
    'gg.aaa.tgKtKtg.aab.gg',
    '..aKaa.tg...tg.aaKa..',
    '.gagag..t...t..gagag.',
], PAL)

im = outline(im)
save(im)
