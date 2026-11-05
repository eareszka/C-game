from pix import *

C = 'e8e0c0'   # bone
B = 'b2966a'   # tan
D = '474751'   # hide
F = '848694'   # hide light
H = '292931'   # hide dark
E = 'fc74b4'   # nose
G = 'b6433d'   # mouth, eye
K = '000000'

im = load('before.png')
im = strip_outline(im)


def clear(y, x1):
    for x in range(0, x1 + 1):
        dot(im, x + 8, y + 8, None)


def run(y, x0, x1, c):
    rect(im, x0 + 8, y + 8, x1 - x0 + 1, 1, c)


def spots(c, pts):
    for x, y in pts:
        dot(im, x + 8, y + 8, c)


# Take off the old horns and the old head.
for y in range(0, 26):
    clear(y, 17)
clear(26, 19)
clear(27, 15)
for y in range(28, 32):
    clear(y, 12)
for y in range(32, 38):
    clear(y, 16)
for y in range(38, 42):
    clear(y, 20)
clear(42, 19)
clear(43, 18)
clear(44, 19)
clear(45, 18)
clear(46, 18)
clear(47, 17)
clear(48, 17)
clear(49, 16)
clear(50, 15)
clear(51, 14)
clear(52, 13)
im = strip_outline(im)

# Near horn: sweeps up and out to the left, tip curling back.
near = [(8, 8, 9), (9, 7, 9), (10, 6, 9), (11, 5, 8), (12, 4, 8), (13, 4, 7), (14, 3, 7), (15, 3, 7),
        (16, 2, 6), (17, 2, 6), (18, 2, 6), (19, 2, 6), (20, 2, 6), (21, 2, 6), (22, 2, 7), (23, 2, 7),
        (24, 3, 8), (25, 3, 8), (26, 3, 9), (27, 4, 10)]
for y, a, b in near:
    run(y, a, b, C)
spots(B, [(9, 26), (8, 26), (10, 27), (9, 27), (8, 27)])
run(28, 4, 11, B)
run(29, 5, 12, B)
run(30, 6, 12, B)
run(31, 7, 12, B)

# Far horn: stands straight up behind it, with a clear gap between them.
far = [(11, 14, 15), (12, 13, 15), (13, 13, 15), (14, 12, 15), (15, 12, 15), (16, 12, 15), (17, 12, 15),
       (18, 11, 15), (19, 11, 15), (20, 11, 15), (21, 11, 15), (22, 11, 15), (23, 11, 15), (24, 12, 15),
       (25, 12, 15), (26, 13, 16), (27, 13, 15)]
for y, a, b in far:
    run(y, a, b, B)
    if y < 23:
        run(y, a, a + 1, C)

# Skull, tipped down: forehead on the left, muzzle pointing down.
run(28, 12, 15, F)
spots(F, [(13, 29)])
run(32, 7, 9, F); run(32, 10, 16, D)
run(33, 6, 8, F); run(33, 9, 16, D)
run(34, 6, 8, F); run(34, 9, 16, D)
run(35, 5, 7, F); run(35, 8, 16, D)
run(36, 5, 7, F); run(36, 8, 16, D)
run(37, 5, 7, F); run(37, 8, 14, D); run(37, 15, 15, K); run(37, 16, 16, D)
run(38, 4, 6, F); run(38, 7, 13, D); run(38, 14, 14, K); run(38, 15, 15, G); run(38, 16, 16, K); run(38, 17, 20, D)
run(39, 4, 6, F); run(39, 7, 13, D); run(39, 14, 14, K); run(39, 15, 16, G); run(39, 17, 17, K); run(39, 18, 20, D)
run(40, 3, 5, F); run(40, 6, 12, D); run(40, 13, 13, K); run(40, 14, 16, G); run(40, 17, 17, K); run(40, 18, 20, D)
run(41, 3, 5, F); run(41, 6, 11, D); run(41, 12, 12, K); run(41, 13, 15, G); run(41, 16, 16, K); run(41, 17, 18, D); run(41, 19, 20, H); run(41, 21, 21, K)
run(42, 3, 4, F); run(42, 5, 10, D); run(42, 11, 11, K); run(42, 12, 15, G); run(42, 16, 16, K); run(42, 17, 18, D); run(42, 19, 19, H); run(42, 20, 20, K)
run(43, 2, 4, F); run(43, 5, 10, D); run(43, 11, 11, K); run(43, 12, 15, G); run(43, 16, 16, K); run(43, 17, 17, D); run(43, 18, 18, H); run(43, 19, 19, K)
run(44, 2, 4, F); run(44, 5, 9, D); run(44, 10, 10, K); run(44, 11, 14, G); run(44, 15, 15, K); run(44, 16, 17, D); run(44, 18, 18, H); run(44, 19, 19, K)
run(45, 2, 3, F); run(45, 4, 8, D); run(45, 9, 9, K); run(45, 10, 14, G); run(45, 15, 15, K); run(45, 16, 16, D); run(45, 17, 17, H); run(45, 18, 18, K)
run(46, 1, 5, E); run(46, 6, 7, D); run(46, 8, 8, K); run(46, 9, 13, G); run(46, 14, 14, K); run(46, 15, 16, D); run(46, 17, 17, H); run(46, 18, 18, K)
run(47, 1, 5, E); run(47, 6, 6, D); run(47, 7, 7, K); run(47, 8, 13, G); run(47, 14, 14, K); run(47, 15, 15, D); run(47, 16, 16, H); run(47, 17, 17, K)
run(48, 1, 5, G); run(48, 6, 6, D); run(48, 7, 7, K); run(48, 8, 12, G); run(48, 13, 13, K); run(48, 14, 15, D); run(48, 16, 16, H); run(48, 17, 17, K)
run(49, 2, 5, G); run(49, 6, 13, K); run(49, 14, 14, D); run(49, 15, 15, H); run(49, 16, 16, K)
run(50, 7, 13, D); run(50, 14, 14, H); run(50, 15, 15, K)
run(51, 9, 12, D); run(51, 13, 13, H); run(51, 14, 14, K)
run(52, 10, 13, K)

spots(G, [(3, 46)])                                                     # nostril
spots(C, [(14, 40), (15, 40), (12, 43), (13, 43), (9, 46), (10, 46), (8, 48), (9, 48)])   # upper teeth
spots(C, [(15, 42), (13, 45), (14, 45), (12, 47), (13, 47)])            # lower teeth
spots(K, [(8, 38), (9, 37), (10, 37), (11, 36), (12, 36), (13, 35), (14, 35)])            # brow
spots(G, [(10, 38), (11, 38)])                                          # eye

im = outline(im)

# Everything away from the head goes back exactly as it was.
src = Image.open('before.png').convert('RGBA').load()
px = im.load()
w, h = Image.open('before.png').size
for y in range(h):
    for x in range(w):
        if x >= 23 or y >= 53:
            px[x + 9, y + 9] = src[x, y]

save(im)
