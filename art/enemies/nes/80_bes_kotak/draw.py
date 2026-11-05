from pix import *

L = '967448'   # lit wood
M = '815423'   # mid wood
D = '583518'   # shaded wood
S = '341e10'   # slot interior
A = 'f0bc3c'   # amber eye
G = 'fc9838'   # amber glow in the mouth
K = '000000'

im = canvas(44, 40)


def hand(x0, flip):
    # x0 = left edge of a 7 wide strip; flip mirrors the part but keeps the light upper left
    def X(i, w=1):
        return x0 + (i if not flip else 7 - i - w)
    rect(im, X(2, 4), 14, 4, 6, M)          # arm stub
    rect(im, x0 + (2 if not flip else 1), 14, 1, 6, L)
    rect(im, x0 + (5 if not flip else 4), 14, 1, 6, D)
    rect(im, X(1, 5), 19, 5, 1, K)          # wrist line
    rect(im, x0, 20, 7, 11, M)              # palm and fingers
    rect(im, x0, 20, 7, 1, L)
    rect(im, x0, 21, 1, 9, L)               # lit left side
    rect(im, x0 + 6, 21, 1, 10, D)          # shaded right side
    rect(im, x0 + 1, 26, 5, 1, D)           # knuckle shadow
    rect(im, x0, 30, 7, 1, D)               # finger tips
    rect(im, x0 + 2, 27, 1, 4, K)           # finger slits run out of the bottom
    rect(im, x0 + 4, 27, 1, 4, K)
    dot(im, x0 + 2, 30, None)
    dot(im, x0 + 4, 30, None)
    dot(im, x0, 30, None)
    dot(im, x0 + 6, 30, None)


hand(0, False)
hand(37, True)

# --- body box ---
rect(im, 8, 15, 28, 25, M)
rect(im, 8, 15, 1, 22, L)                   # lit left edge
rect(im, 9, 37, 27, 3, D)                   # underside
rect(im, 33, 16, 3, 24, D)                  # right post in shade
rect(im, 11, 18, 1, 18, K)                  # post seams
rect(im, 32, 18, 1, 18, D)                  # right side falls into shade
rect(im, 8, 36, 28, 1, K)                   # base seam
rect(im, 9, 18, 2, 1, L)
rect(im, 11, 16, 22, 2, D)                  # shadow under the lid

# plank streaks
rect(im, 13, 19, 6, 1, L)
rect(im, 24, 19, 5, 1, D)
rect(im, 24, 25, 7, 1, D)
rect(im, 13, 25, 4, 1, D)
rect(im, 21, 34, 9, 1, D)
rect(im, 13, 34, 5, 1, L)
rect(im, 9, 24, 2, 1, D)
rect(im, 9, 31, 2, 1, D)
rect(im, 33, 25, 3, 1, M)
rect(im, 13, 38, 7, 1, M)
rect(im, 25, 38, 5, 1, M)

# --- eyes: black sockets with a single amber mark ---
rect(im, 15, 21, 4, 3, K)
rect(im, 25, 21, 4, 3, K)
rect(im, 16, 22, 2, 1, A)
rect(im, 26, 22, 2, 1, A)

# --- mouth slot ---
rect(im, 15, 27, 14, 1, K)
rect(im, 14, 28, 16, 3, K)
rect(im, 15, 31, 14, 1, K)
rect(im, 17, 32, 10, 1, K)
rect(im, 16, 28, 12, 3, S)
rect(im, 18, 31, 8, 1, S)
rect(im, 16, 28, 12, 1, G)
rect(im, 17, 33, 10, 1, L)                  # lower lip

# --- lid ---
rect(im, 3, 7, 38, 8, M)                    # front band
rect(im, 3, 7, 38, 1, L)
rect(im, 3, 8, 1, 7, L)
rect(im, 3, 14, 38, 1, D)
rect(im, 36, 8, 5, 7, D)
rect(im, 3, 15, 38, 1, K)                   # line under the lid
rect(im, 3, 6, 38, 1, K)                    # line between top and band
poly(im, [(8, 0), (35, 0), (37, 2), (38, 5), (5, 5), (6, 2)], L)  # sloped top
poly(im, [(30, 1), (35, 1), (37, 3), (38, 5), (28, 5)], M)
rect(im, 10, 2, 14, 1, M)
rect(im, 7, 4, 9, 1, M)
rect(im, 20, 4, 6, 1, M)

# band seams and streaks
rect(im, 11, 8, 1, 6, D)
rect(im, 32, 8, 1, 6, D)
rect(im, 14, 10, 8, 1, D)
rect(im, 24, 12, 6, 1, D)
rect(im, 5, 11, 4, 1, D)
rect(im, 38, 10, 2, 1, M)

im = outline(im)
save(im)
