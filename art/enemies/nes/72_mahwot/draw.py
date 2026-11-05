from pix import *

PAL = {
    'g': '4fa667',  # lit green
    'm': '2c6c44',  # mid green
    'd': '235436',  # shade green
    'b': 'cebe82',  # belly
    'c': 'b29e5c',  # belly shade
    's': 'dcf0ff',  # spine
    't': 'a4aaba',  # spine shade
}

rows = [
    #0         1         2         3         4
    #012345678901234567890123456789012345678901
    '....................s.....................',
    '...............s....st....................',
    '...............st..sst.....s..............',
    '..............sst..sst....st.......gggg...',
    '.........s....sst.sstt...sst..s...gggggg..',
    '........st...sstt.sstt..sstt.st..ggKKgggg.',
    '....s...stt.ssttt.sttt.ssttt.sttgggggggKg.',
    '...st..ggggggggggggggggggggggggggggggggmmg',
    'gg.stggggggggggKggggggggKgggggggggmmmmmmmm',
    '.ggggggmmmmmmmmKmmmmmmmmKmmmmmmmKsKsKsKsK.',
    '...gmmmmmmmmmmmmmmmmmmmmmmmmmmmmmKbbbbbbbb',
    '.....ddmmmdddddddddddddddddmmmmdKcccccc...',
    '......ddgmmmdKbbbKbbKbbKbbbKgmmmd.........',
    '.......ggmmmdKKbbKbbKbbKbcKKgmmmd.........',
    '......ggmmdd....ccccccccc..gmmmd..........',
    '.....gmmmd..................gmmmd.........',
    '....gmmd.....................gmmdd........',
    '...s.s.s.......................s.s.s......',
]
im = grid(rows, PAL)
im = outline(im)
save(im)
