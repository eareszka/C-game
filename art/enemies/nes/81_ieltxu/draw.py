from pix import *

PAL = {
    'a': '664b95',  # lit rim
    'b': '2b1f40',  # feather
    'c': '181224',  # shaded feather
    'r': 'b70000',  # ember
    'o': 'fc9838',  # flame
    'y': 'f0bc3c',  # flame, hot
}

half = [
    '................r.....o',
    '................ra...ry',
    '................aab..ry',
    '..........aaa...aabbbbr',
    '.......aaaabbaa.abbbbbb',
    '.....aaabbbbbbaaKabbbbb',
    '....aabbbbbbbbbaKbbrrbb',
    '...aabbbKbbbKbbbKcbbbyo',
    '..aabbbKbbbKbbbbKccbbbo',
    '..abbbKbbbKbbbbKKKccccr',
    '.abbKbbbKbbbKbbbKabbbrr',
    '.abKbbbKbbbKbbbKbabbrro',
    '.abKbbKbbbKbbbKKabbbroy',
    'abbKbbKbbKbbbKbKabbcroy',
    'abbKbbKbbKbbKbbKbbcrroy',
    'abb.bb.bbKbbKbb.abbcrro',
    'abb.bb.bb.bb.bb.abbcrro',
    'abr.br.br.br.rr.abcccrr',
    '.rr.rr.rr.rr.oo.abcccrr',
    '.ro.ro.ro.oo.y..abbcccr',
    '.oy..o.oy..y....abccccc',
    '..y.....y........bccccc',
    '................rrbcccc',
    '...............rr..bccr',
    '...............ro..bcrr',
    '..............oyo...rro',
    '..............y.y...rry',
    '....................roy',
    '....................r.o',
    '......................y',
]

rows = [list(r) for r in mirror(half)]

# Light from the upper left: the far side of the bird loses its lit tone.
for y, row in enumerate(rows):
    for x, ch in enumerate(row):
        if x > 22 and ch == 'a':
            if x <= 28 or y > 5:
                row[x] = 'b'
        elif x > 28 and y >= 10 and ch == 'b':
            row[x] = 'c'

im = grid([''.join(r) for r in rows], PAL)
im = outline(im)
save(im)
