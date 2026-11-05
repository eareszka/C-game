from pix import *

im = load('before.png')

L = 'bcbeca'  # grey base
M = '848694'  # grey shadow
V = '664b95'  # violet base
S = '3b2a58'  # violet shadow
B = '94703d'  # the one brown
K = '000000'


def b(x0, x1, y0, y1, c):
    # Coordinates are before.png pixels; load() adds 8 px of room on each side.
    rect(im, x0 + 8, y0 + 8, x1 - x0 + 1, y1 - y0 + 1, c)


# Head: only its dark grey becomes the grey shadow.
b(12, 16, 5, 5, M)
b(11, 11, 6, 6, M)
b(8, 8, 13, 14, M)
b(11, 19, 13, 14, M)

# Neck: one plain grey band, lit on the left, shadow on the right.
b(16, 21, 15, 15, L)
b(22, 26, 15, 15, M)
b(17, 22, 16, 16, L)
b(23, 26, 16, 16, M)
b(18, 23, 17, 17, L)
b(24, 26, 17, 17, M)
b(19, 24, 18, 22, L)
b(25, 27, 18, 22, M)
b(20, 25, 23, 28, L)
b(26, 28, 23, 28, M)
b(19, 24, 29, 31, L)
b(25, 27, 29, 31, M)
b(19, 23, 32, 33, L)
b(24, 27, 32, 33, M)
b(18, 22, 34, 34, L)
b(23, 24, 34, 34, M)
b(18, 21, 35, 37, L)
b(22, 24, 35, 37, M)
b(25, 25, 37, 37, M)
b(18, 21, 38, 38, L)
b(22, 25, 38, 38, M)
b(17, 21, 39, 39, L)
b(22, 24, 39, 39, M)
b(17, 21, 40, 42, L)
b(22, 25, 40, 42, M)

# Hood: plain violet with the shadow down its right side.
b(23, 33, 5, 5, V)
b(34, 35, 5, 5, S)
b(24, 34, 6, 6, V)
b(35, 36, 6, 6, S)
b(27, 36, 10, 10, V)
b(37, 38, 10, 10, S)
b(27, 36, 11, 11, V)
b(28, 36, 16, 17, V)
b(29, 36, 22, 22, V)
b(30, 36, 23, 23, V)
b(30, 35, 28, 28, V)
b(29, 35, 29, 29, V)
b(28, 33, 34, 35, V)

# Tail: plain violet, shadow down the outer right side, clean line along its belly.
b(61, 63, 14, 14, V)
b(55, 56, 15, 15, V)
b(67, 70, 16, 16, V)
b(71, 72, 16, 16, S)
b(53, 54, 17, 17, V)
b(56, 57, 17, 17, K)
b(66, 71, 17, 17, V)
b(72, 73, 17, 17, S)
b(70, 71, 18, 18, V)
dot(im, 72 + 8, 21 + 8, V)
b(50, 50, 22, 22, V)
b(51, 51, 22, 22, K)
b(50, 50, 23, 23, V)
b(49, 50, 27, 27, V)
b(58, 59, 34, 34, V)
b(64, 64, 34, 34, M)
b(68, 68, 37, 37, M)

# Rider: dark grey becomes the grey shadow.
b(56, 57, 32, 35, M)
b(51, 57, 36, 36, M)
b(56, 58, 37, 39, M)
b(45, 48, 38, 38, M)

# Boat and oar: the one brown.
b(42, 42, 28, 31, B)
b(27, 27, 37, 37, B)
b(28, 28, 38, 38, B)
b(61, 61, 37, 37, B)
b(60, 60, 38, 38, B)
b(33, 44, 39, 39, B)
b(46, 47, 39, 39, B)
b(31, 32, 44, 44, B)
b(34, 39, 44, 44, B)
b(41, 46, 44, 44, B)
b(48, 53, 44, 44, B)
b(55, 57, 44, 44, B)
b(27, 27, 42, 42, K)

# Coils above the bottom run: plain violet each side of the boat.
b(6, 16, 42, 42, V)
b(71, 72, 40, 42, S)

# Row by row: left violet, the grey band sweeping out of the neck and under the
# boat, the black line under the hull, right violet.
b(5, 14, 43, 43, V)
b(15, 21, 43, 43, L)
b(22, 26, 43, 43, M)
b(27, 27, 43, 43, K)
b(61, 71, 43, 43, V)
b(72, 73, 43, 43, S)

b(5, 14, 44, 44, V)
b(15, 22, 44, 44, L)
b(23, 27, 44, 44, M)
b(28, 28, 44, 44, K)
b(61, 71, 44, 44, V)
b(72, 73, 44, 44, S)

b(4, 14, 45, 45, V)
b(15, 23, 45, 45, L)
b(24, 28, 45, 45, M)
b(29, 29, 45, 45, K)
b(30, 58, 45, 45, B)
b(61, 71, 45, 45, V)
b(72, 73, 45, 45, S)

b(3, 14, 46, 46, V)
b(15, 25, 46, 46, L)
b(26, 29, 46, 46, M)
b(30, 31, 46, 46, K)
b(32, 56, 46, 46, B)
b(57, 58, 46, 46, K)
b(59, 71, 46, 46, V)
b(72, 73, 46, 46, S)

b(2, 15, 47, 47, V)
b(16, 28, 47, 47, L)
b(29, 31, 47, 47, M)
b(32, 34, 47, 47, K)
b(35, 53, 47, 47, B)
b(54, 56, 47, 47, K)
b(57, 72, 47, 47, V)
b(73, 74, 47, 47, S)

b(1, 17, 48, 48, V)
b(18, 34, 48, 48, L)
b(35, 53, 48, 48, K)
b(54, 69, 48, 48, L)
b(70, 72, 48, 48, V)
b(73, 74, 48, 48, S)

b(1, 19, 49, 49, V)
b(20, 70, 49, 49, L)
b(71, 72, 49, 49, V)
b(73, 74, 49, 49, S)

b(1, 22, 50, 50, V)
b(23, 71, 50, 50, L)
b(72, 72, 50, 50, V)
b(73, 74, 50, 50, S)

b(1, 25, 51, 51, S)
b(26, 71, 51, 51, M)
b(72, 74, 51, 51, S)

b(1, 29, 52, 52, S)
b(30, 69, 52, 52, M)
b(70, 74, 52, 52, S)

# Underside: one flat shadow to the outline.
b(1, 74, 53, 53, S)
b(2, 73, 54, 54, S)
b(4, 71, 55, 55, S)
b(8, 67, 56, 56, S)
b(14, 61, 57, 57, S)

save(im)
