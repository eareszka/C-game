from pix import *

PAL = {
    'a': '664b95',  # hide, lit
    'b': '3b2a58',  # hide, mid
    'c': '301b5a',  # hide, shade
    'g': 'a4aaba',  # grid line, lit; claws
    'u': '848694',  # grid line, shade; tusk shade
    'r': 'b6433d',  # red, lit
    's': '792727',  # red, shade
    't': 'e8e0c0',  # tusks, eye
}

# Left half, column 17 is the centre. h = hide, tone comes from its plate below.
HALF = [
    '.............hhhhh',
    '..........hhhhghhh',
    '........hhhggggggg',
    '.......hhgghhghhhg',
    '......hhghhhhhgggg',
    '.....ggghhhhhghhhh',
    '....hhghhhhhghhhhh',
    '....hghhhhhhghhhhh',
    '...hhgggggggghhhhh',
    '...hghhhhhhhghhhhh',
    '..hhghhhhhhhhghhhh',
    '..hghhhhhghhhhgggg',
    '.ggghhhhhghhhhhhhg',
    '.hgggggggggggggggg',
    'hhhghhhhghhhhghhhh',
    '...sKKKKKKKKKKKKKK',
    '..bsrrrKrrrrKttsss',
    '.bbsrrrKrrrrKttKss',
    '.bbKsrrKrrrrKttKtK',
    '.bcKssKaabcKsttKtK',
    '.bc...KaabcK..tu..',
    '.bbc..acbacca.tu..',
    'accb.acccaccca.t..',
    'g..g.g...g...g....',
]

rows = [list(r) for r in mirror(HALF)]
W, H = len(rows[0]), len(rows)

# Eye: one solid mark, 2 px tall, on the centre plate.
rows[8][17] = 't'
rows[9][17] = 't'

# Tone each plate as one flat colour, lit towards the upper left.
seen = set()
for y in range(H):
    for x in range(W):
        if rows[y][x] != 'h' or (x, y) in seen:
            continue
        stack, cells = [(x, y)], []
        seen.add((x, y))
        while stack:
            cx, cy = stack.pop()
            cells.append((cx, cy))
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if 0 <= nx < W and 0 <= ny < H and rows[ny][nx] == 'h' and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    stack.append((nx, ny))
        mx = sum(c[0] for c in cells) / len(cells)
        my = sum(c[1] for c in cells) / len(cells)
        score = mx * 0.6 + my
        tone = 'a' if score < 16 else 'b' if score < 26 else 'c'
        for cx, cy in cells:
            rows[cy][cx] = tone

# Light from the upper left: right side and low rows take the shade tones.
for y in range(H):
    for x in range(W):
        ch = rows[y][x]
        if ch == 'g' and (x > 24 or y >= 13) and y < 20:
            rows[y][x] = 'u'
        if x > 17 and 15 <= y < 21:
            if ch == 'r' and x > 28:
                rows[y][x] = 's'
            if ch == 'a':
                rows[y][x] = 'b'
            if ch == 'b' and x > 24:
                rows[y][x] = 'c'

im = grid([''.join(r) for r in rows], PAL)
im = outline(im)
save(im)
