from pix import *
# Cu Sith, sitting up and facing the player. Parts, back to front:
# tail: starts behind the right hind leg and shoulder, rises up the right side, over
#       the top, down the left and along the bottom into the tip lobe in the coil.
# left hind leg, right hind leg: thigh at the coat's lower corner, then sock, then toes.
# coat: across the neck and shoulders, behind the chest and ears.
# left foreleg, right foreleg: from under the chest down to the paws and toes.
# chest: on the coat, under the chin, over the tops of the forelegs.
# left ear, right ear: from the top corners of the head, hanging beside it.
# head: on top of the ears and chest, with both eyes, the nose and a mouth line.

PAL = {'a': '2c6c44', 'b': '163623', 'c': 'a8f0bc', 'd': '4fa667', 'n': '848694', 'e': 'f0e880'}

tail = grid([
    '..........KKKKKKK.....',
    '........KKaaaaaaaKK...',
    '.......KaaaaaaaaaabK..',
    '......KaaaaaaaaaaaabK.',
    '......KaaaaKKKKKaabbK.',
    '.....KaaaaKbbbbbKaabbK',
    '.....KaaaKbbbbbbbKabbK',
    '.....KaaaKbbKKKbbKabbK',
    '.....KaaaKKKaaaKbKabbK',
    '.....KaaaKaaaabKbKabbK',
    '.....KaaaKaaaabKbKabbK',
    '.....KaaaaKaabbKKKabbK',
    '.....KaaaaaKKKKKaKabbK',
    '......KaaaaaaaaaaKabbK',
    '......KaaaaaaaabbKabbK',
    '.......KaaaaaabbbKabbK',
    '........KKKKKKKKKaabbK',
    '..............KaaabbbK',
    '.............KaaaabbbK',
    '............KaaaabbbK.',
    '...........KaaaaabbbK.',
    '..........KaaaaabbbK..',
    '.........KaaaaaabbbK..',
    '........KaaaaaabbbK...',
    '.......KaaaaaabbbbK...',
    '......KaaaaaabbbbK....',
    '.....KaaaaaabbbbK.....',
    '....KaaaaabbbbbK......',
    '...KaaaaabbbbK........',
    '..KaaaaabbbbK.........',
    '.KaaaaabbbbK..........',
    'KaaaaabbbbK...........',
    'KaaaabbbbK............',
    'KKKKKKKKK.............',
], PAL)

left_hind = grid([
    '...KKKKKKK...',
    '..KaaaaaaaK..',
    '.KaaaaaaaaaK.',
    'KaaaaaaaaaabK',
    'KaaaaaaaaaabK',
    'KaaaaaaaaabbK',
    'KaaaaaaaaabbK',
    'KaaaaaaaabbbK',
    'KaaaaaaabbbbK',
    '.KaaaaabbbbK.',
    '..KKKKKKKKK..',
    '..KcccccddK..',
    '..KccccdddK..',
    'KKKKKKKKKK...',
    'KccccKcddK...',
    'KccccKcddK...',
    'KccncKcndK...',
    'KKKKK.KKKK...',
], PAL)

right_hind = grid([
    '...KKKKKKK...',
    '..KaaaaabbK..',
    '.KaaaaaabbbK.',
    'KaaaaaaabbbbK',
    'KaaaaaaabbbbK',
    'KaaaaaabbbbbK',
    'KaaaaaabbbbbK',
    'KaaaaabbbbbbK',
    'KaaaabbbbbbbK',
    '.KaaabbbbbbK.',
    '..KKKKKKKKK..',
    '...KccccddK..',
    '...KcccdddK..',
    '...KKKKKKKKKK',
    '...KcccKccddK',
    '...KcccKccddK',
    '...KcncKcnddK',
    '...KKKKK.KKKK',
], PAL)

coat = grid([
    '.......KKKKKKKKKKKKKKKKKK.......',
    '.....KKaaaaaaaaaaaaaaaaaaKK.....',
    '...KKaaaaaaaaaaaaaaaaaaaaaaKK...',
    '..KaaaaaaaaaaaaaaaaaaaaaaaaaaK..',
    '.KaaaaaaaaaaaaaaaaaaaaaaaaaabbK.',
    '.KaaaaaaaaaaaaaaaaaaaaaaaaaabbK.',
    'KaaaaaaaaaaaaaaaaaaaaaaaaaaabbbK',
    'KaaaaaaaaaaaaaaaaaaaaaaaaaaabbbK',
    'KaaaaaaaaaaaaaaaaaaaaaaaaaaabbbK',
    'KaaaaaaaaaaaaaaaaaaaaaaaaaabbbbK',
    'KaaaaaaabbaaaaaaaaaaaaaaaaabbbbK',
    'KaaaaaabbbaaaaaaaaaaaaaaaaabbbbK',
    'KaaaaaabbbaaaaaaaaaaaaaaaabbbbbK',
    '.KaaaabbbaaaaaaaaaaaaaaaabbbbbK.',
    '.KaaabbbbaaaaaaaaaaaaaaaabbbbbK.',
    '..KaaabbbaaaaaaaaaaaaaaabbbbbK..',
    '...KaabbbaaaaaaaaaaaaaaabbbbK...',
    '....KKKKKKKKKKKKKKKKKKKKKKKK....',
], PAL)

left_fore = grid([
    '.KKKKKKKKK',
    '.KccccccdK',
    '.KccccccdK',
    '.KccccccdK',
    '.KccccccdK',
    '.KccccccdK',
    '.KcccccddK',
    '.KcccccddK',
    '.KcccccddK',
    '.KcccccddK',
    '.KcccccddK',
    '.KcccccddK',
    '.KccccdddK',
    '.KccccdddK',
    '.KccccdddK',
    '.KcccddddK',
    'KKKKKKKKKK',
    'KcccKccKcK',
    'KcccKccKdK',
    'KcncKcnKnK',
    'KKKK.KK.KK',
], PAL)

right_fore = grid([
    'KKKKKKKKK.',
    'KcccccddK.',
    'KcccccddK.',
    'KcccccddK.',
    'KcccccddK.',
    'KcccccddK.',
    'KccccdddK.',
    'KccccdddK.',
    'KccccdddK.',
    'KccccdddK.',
    'KccccdddK.',
    'KcccddddK.',
    'KcccddddK.',
    'KcccddddK.',
    'KcccddddK.',
    'KcccddddK.',
    'KKKKKKKKKK',
    'KccKcccKdK',
    'KccKccdKdK',
    'KcnKcndKnK',
    'KKK.KKK.KK',
], PAL)

chest = grid([
    '......KKKKKK......',
    '....KKccccccKK....',
    '...KcccddddcccK...',
    '..KccccccdddcccK..',
    '.KccccccccccccccK.',
    'KcccccccccccccccdK',
    'KcccccccccccccccdK',
    'KccccccccccccccddK',
    'KccccccccccccccddK',
    'KcccccccccccccdddK',
    'KccccccccccccddddK',
    '.KcccccccccccdddK.',
    '.KccccccccccddddK.',
    '..KcccccccccdddK..',
    '..KccccccccddddK..',
    '...KcccccccdddK...',
    '....KcccccdddK....',
    '.....KKccddKK.....',
    '.......KKKK.......',
], PAL)

left_ear = grid([
    '......KKKKK',
    '....KKaaaaK',
    '...KaaaaaaK',
    '..KaaaaaabK',
    '..KaaaaaabK',
    '.KaaaaaaabK',
    '.KaaaaaabbK',
    '.KaaaaaabbK',
    '.KaaaaaabbK',
    'KaaaaaaabbK',
    'KaaaaaaabbK',
    'KaaaaaabbbK',
    'KaaaaaabbbK',
    'KaaaaaabbbK',
    'KaaaaaabbbK',
    'KaaaaaabbbK',
    'KaaaaaabbbK',
    'KaaaaaabbbK',
    'KaaaaaabbbK',
    'KaaaaabbbbK',
    '.KaaaabbbbK',
    '.KaaaabbbbK',
    '..KaabbbbbK',
    '...KabbbbK.',
    '....KKKKK..',
], PAL)

right_ear = grid([
    'KKKKK......',
    'KaaaaKK....',
    'KaaaaaaK...',
    'KaaaaaabK..',
    'KaaaaaabK..',
    'KaaaaaabbK.',
    'KaaaaaabbK.',
    'KaaaaaaabK.',
    'KaaaaaaabbK',
    'KaaaaaaabbK',
    'KaaaaaaabbK',
    'KaaaaaaabbK',
    'KaaaaaabbbK',
    'KaaaaaabbbK',
    'KaaaaaabbbK',
    'KaaaaaabbbK',
    'KaaaaaabbbK',
    'KaaaaaabbbK',
    'KaaaaabbbbK',
    'KaaaaabbbbK',
    'KaaaabbbbK.',
    '.KaaabbbbK.',
    '.KaabbbbK..',
    '..KabbbK...',
    '...KKKKK...',
], PAL)

head = grid([
    '..KKKKKKKKKKKK..',
    '.KaaaaaaaaaaabK.',
    'KaaaaaaaaaaaabbK',
    'KaaaaaaaaaaaabbK',
    'KaaaaaaaaaaaabbK',
    'KaaaaaaaaaaaabbK',
    'KaaaaaaaaaaaabbK',
    'KaabbbaaaabbabbK',
    'KaaeeaaaaaaeebbK',
    'KaaaaaaaaaaaabbK',
    '.KaaaaaaaaaaabK.',
    '.KaaaaaaaaaabbK.',
    '..KaaaaaaaaabK..',
    '..KaaaaaaaabbK..',
    '..KaaaaaaaabbK..',
    '.KaaaaaaaaaabbK.',
    '.KaaaKKKKKKabbK.',
    '.KaaaaKKKKaabbK.',
    '..KaaaaKKaaabK..',
    '..KaaaaKKaabbK..',
    '...KaaaKKabbK...',
    '....KKKKKKKK....',
], PAL)

im = canvas(53, 58)
stamp(im, tail, 30, 6)
stamp(im, left_hind, 1, 37)
stamp(im, right_hind, 26, 37)
stamp(im, coat, 4, 25)
stamp(im, left_fore, 10, 36)
stamp(im, right_fore, 20, 36)
stamp(im, chest, 11, 21)
stamp(im, left_ear, 4, 2)
stamp(im, right_ear, 25, 2)
stamp(im, head, 12, 1)
im = strip_outline(im)
im = outline(im)
save(im)
