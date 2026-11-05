from pix import *

PAL = {
    'l': 'f0b890',  # lit skin
    't': 'd7a175',  # skin
    's': '8d6b4f',  # skin shade
    'h': '815423',  # hair
    'w': 'e8e0c0',  # teeth
}

im = grid([
    '................h....h.',
    '...............hh....hh',
    '.hh............lt....ts',
    'hhhh...........lttlltss',
    'hhhh...........ltKttKts',
    '.hh.............ltttts.',
    '..t.............tlKKts.',
    '..t............Khhhhhh.',
    '..tt.......llllthKKKKh.',
    '...tllllllltttttthwKwh.',
    '...lttttttttttttKhhhh..',
    '...ttttttttttttttlKts..',
    '...ltKttttttsssssKts...',
    '...tttKsss....sssKts...',
    '..ttsK.sK.....sK.ts....',
    '..ts...sK.....sK.ts....',
    '..ts...s......s..ts....',
    '...ts..s......s..ts....',
    '..hhh.hh.....hh.hhh....',
    '..hhK.hK.....hK.hhK....',
], PAL)

im = outline(im)
save(im)
