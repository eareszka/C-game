from pix import *

L = 'a8f0bc'
G = '4fa667'
D = '2c6c44'
Y = 'f0bc3c'
O = 'fc9838'
R = 'b6433d'
B = '94703d'
S = '633e1b'
PAL = {'L': L, 'G': G, 'g': D, 'Y': Y, 'O': O, 'R': R, 'B': B, 'S': S}

im = canvas(32, 40)

# tail first, so the legs sit in front of it: a thin whip, ringed like a pipefish
tail = [
    (5, 14), (4, 15), (4, 16), (3, 17), (3, 18), (2, 19), (2, 20), (2, 21),
    (1, 22), (1, 23), (1, 24), (1, 25), (1, 26), (1, 27), (1, 28), (2, 29),
    (2, 30), (3, 31), (4, 32),
]
for i, (x, y) in enumerate(tail):
    ring = i % 3 == 2
    rect(im, x, y, 1, 1, D if ring else G)
    rect(im, x + 1, y, 1, 1, D)
rect(im, 5, 33, 5, 1, G)
rect(im, 5, 32, 2, 1, D)
stamp(im, grid(['..gG', 'GGgg'], PAL), 8, 31)   # tail tip, curling back past the leg

# left stilt: thick sleeve, collar, thin sleeve, collar, thinnest rod
for x, y, h in [(8, 16, 3), (7, 19, 4)]:
    rect(im, x, y, 1, h, B)
    rect(im, x + 1, y, 1, h, S)
rect(im, 6, 23, 3, 1, Y)
rect(im, 7, 24, 1, 3, B)
rect(im, 6, 27, 1, 3, B)
rect(im, 5, 30, 3, 1, Y)
rect(im, 6, 31, 1, 5, B)
stamp(im, grid(['.YOO..', 'OOOOOO'], PAL), 4, 36)

# right stilt, kicked out wide
for x, y, h in [(12, 16, 2), (13, 18, 2), (14, 20, 2), (15, 22, 1)]:
    rect(im, x, y, 1, h, B)
    rect(im, x + 1, y, 1, h, S)
rect(im, 15, 23, 3, 1, Y)
for x, y in [(16, 24), (17, 26), (18, 28)]:
    rect(im, x, y, 1, 2, B)
rect(im, 18, 30, 3, 1, Y)
for x, y in [(19, 31), (20, 33)]:
    rect(im, x, y, 1, 2, B)
rect(im, 21, 35, 1, 1, B)
stamp(im, grid(['.YOO..', 'OOOOOO'], PAL), 20, 36)

# head, snout, small body
top = [
    '........GGGGG...........',
    '......GGLLLLGGg.........',
    '.....GLLLKLGGGGg........',
    '.....GLLLKGGGGGgg.......',
    '.....GGGGGGGGGGGGGGg....',
    '.....OOKKKKKKKKGGGGGg...',
    '......OOOOOOKgg..gGGg...',
    '.........YOOOR....GGg...',
    '........YYOOOOR...ggg...',
    '.......YYOOOOOR...GGg...',
    '.......YOOOOOOR....GGg..',
    '.......YOOOOOOR....ggg..',
    '.......OKKKKKKR....GGg..',
    '.......RRRRRRRS...GLLGg.',
    '.......RRRRRRSS...g..g..',
    '........RKKKKS..........',
    '........SSSSSS..........',
]
stamp(im, grid(top, PAL), 0, 0)

im = outline(im)
save(im)
