from pix import *

PAL = {
    'a': 'e8e0c0',  # pale face, belly, antlers
    'b': 'cebe82',  # lit wing edge
    'c': 'b2966a',  # body tan
    'd': '815423',  # wing brown
    'e': '583518',  # wing and body shade
    'g': '9797aa',  # feet
}

im = grid([
    '....a.a...a.a....',
    '....aaa...aaa....',
    '.....a.....a.....',
    '.....ccccccc.....',
    'bb...caaaaac...cc',
    'dbbb.caKaKad.cccd',
    'ddddbcaaKaadcdddd',
    '.dddddcaKadddddd.',
    '..dddKdcccdKddd..',
    '..eKddKcaadKddKe.',
    '...e.eKcaadKe.e..',
    '......KcaadK.....',
    '.......ccde......',
    '.......g.g.......',
], PAL)

im = outline(im)
save(im)
