from pix import *

PAL = {
    'l': 'fae488',  # yellow light
    'y': 'f0bc3c',  # yellow
    'd': 'c18a39',  # yellow shade, legs
    'g': '34343e',  # dark stripes and face
    'r': 'b6433d',  # eyes
    'w': 'dcf0ff',  # wing, needle
    'm': 'bcbeca',  # wing shade
    'v': '84a7e9',  # wing vein
}

# left half with the centre column, then the right half, so the light can stay upper left
LEFT = [
    '..www..........',
    '.wwwww.........',
    'wwvwwww........',
    'wwwvwwww.......',
    '.mwwvwww.......',
    '..mwwvwww......',
    '...mwwvww......',
    '....mwwvww.....',
    '.....mwwvw..lll',
    '......mwwvKllll',
    '........mwKylll',
    '..........yyyyy',
    '..........ygrgg',
    '..........ygrgg',
    '...........yggg',
    '......dddddggKw',
    '.....d...ddggKw',
    '....d...d.lyyKw',
    '....d...d.yyyKw',
    '...d....d.gggKw',
    '...d...d..gggKw',
    '.......d..lyyKw',
    '......d..dyyyKw',
    '.........dgggKw',
    '........d..ggKw',
    '........d...yKw',
    '..............w',
    '..............w',
    '..............m',
]
RIGHT = [
    '.........www..',
    '........wwwww.',
    '.......wwwwvww',
    '......wwwwvwwm',
    '......wwwvwwm.',
    '.....wwwvwwm..',
    '.....wwvwwm...',
    '....wwvwwm....',
    'yy..wvwwm.....',
    'yydKvwwm......',
    'yydKwm........',
    'yyyd..........',
    'grgd..........',
    'grgd..........',
    'ggd...........',
    'Kggddddd......',
    'Kggdd...d.....',
    'Kyyd.d...d....',
    'Kyyd.d...d....',
    'Kggg.d....d...',
    'Kggg..d...d...',
    'Kyyd..d.......',
    'Kyydd..d......',
    'Kgggd.........',
    'Kgg..d........',
    'Kd...d........',
    '..............',
    '..............',
    '..............',
]

im = grid([a + b for a, b in zip(LEFT, RIGHT)], PAL)
im = outline(im)
save(im)
