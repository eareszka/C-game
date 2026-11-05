from pix import *

L = 'cebe82'   # shell light
M = 'b29e5c'   # shell mid
D = '785830'   # shell dark
B = 'e8e0c0'   # bone: spike tips, tusks, teeth
R = 'b6433d'   # face
RD = '7c0a1b'  # face shade
RL = 'ec8476'  # face light
G = '9797aa'   # lip of the shell
K = '000000'

SHELL = {tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for c in (L, M, D)}

im = canvas(70, 70)
CX = 33


def whorl(y0, y1, hw, inset=2):
    """A stepped band of shell, lit upper left, shaded lower right."""
    h = y1 - y0 + 1
    for i in range(h):
        y = y0 + i
        cut = max(0, inset - i, inset - (h - 1 - i))
        half = hw - cut
        for x in range(CX - half, CX + half + 1):
            t = (x - (CX - half)) / (2 * half + 1)
            c = M
            if t < 0.32 and i < h - 2:
                c = L
            if i == 0 and t < 0.75:
                c = L
            if t > 0.74 or i >= h - 2:
                c = D
            if i >= h - 2 and t < 0.25:
                c = M
            dot(im, x, y, c)


def spike(x, y, dx, n, rise=1, thick=3):
    """A chunky spike growing sideways from x,y. Bone tip, dark underside."""
    for i in range(n):
        h = max(1, round(thick * (n - i) / n))
        col = x + dx * i
        top = y - (i * rise) // 2 - h // 2
        tip = i >= n - 3
        for j in range(h):
            c = B if tip else M
            if j == 0 and not tip:
                c = L
            if j == h - 1 and h > 1:
                c = M if tip else D
            dot(im, col, top + j, c)


def up_spike(x, y, n):
    """A spike pointing up, lit on its left."""
    for i in range(n):
        h = max(0, (n - i - 1) // 2)
        for xx in range(x - h, x + h + 1):
            c = B if i >= n - 3 else M
            if xx == x - h and i < n - 3:
                c = L
            if xx == x + h and h > 0 and i < n - 3:
                c = D
            dot(im, xx, y - i, c)


# --- spikes behind the shell ---
# tower spikes
spike(CX - 7, 12, -1, 5, 1, 3)
spike(CX + 7, 12, 1, 5, 1, 3)
spike(CX - 11, 18, -1, 6, 1, 4)
spike(CX + 11, 18, 1, 6, 1, 4)
# big horns on the shoulders
spike(CX - 15, 25, -1, 13, 2, 6)
spike(CX + 15, 25, 1, 13, 2, 6)
# flank spikes
spike(CX - 21, 33, -1, 7, 1, 5)
spike(CX + 21, 33, 1, 7, 1, 5)
spike(CX - 21, 43, -1, 7, 0, 5)
spike(CX + 21, 43, 1, 7, 0, 5)

# --- apex and tower ---
up_spike(CX, 5, 5)
whorl(5, 9, 4, 1)
whorl(9, 14, 8, 2)
whorl(14, 20, 12, 2)

# --- body whorl ---
whorl(20, 51, 22, 7)
up_spike(CX - 13, 21, 5)
up_spike(CX + 13, 21, 5)

# spiral sutures: black, stepped, sinking to the right
for x in range(CX - 3, CX + 4):
    dot(im, x, 9 + (x - CX + 3) // 3 - 1, K)
for x in range(CX - 7, CX + 8):
    dot(im, x, 14 + (x - CX + 7) // 5 - 1, K)
for x in range(CX - 11, CX + 12):
    dot(im, x, 20 + (x - CX + 11) // 7 - 2, K)

# raised rim round the aperture: a flat tone band, no line
px = im.load()
for y in range(22, 52):
    for x in range(CX - 21, CX + 22):
        if ((x - CX) / 20.5) ** 2 + ((y - 37) / 15.5) ** 2 <= 1 and px[x, y][:3] in SHELL:
            dot(im, x, y, M if x < CX + 8 else D)

# plate ticks on the flanks, each with a lit edge under it
for y, w in ((29, 3), (35, 4), (41, 4), (47, 3)):
    rect(im, CX - 22, y, w, 1, K)
    rect(im, CX + 23 - w, y, w, 1, K)
    rect(im, CX - 22, y + 1, w, 1, L)
    rect(im, CX + 23 - w, y + 1, w, 1, M)
# ticks across the top of the rim
for dx in (-12, -6, 6, 12):
    rect(im, CX + dx, 21, 1, 2, K)

# --- aperture: black rim, grey lip, red face ---
oval(im, CX - 16, 23, 33, 29, K)
oval(im, CX - 15, 26, 31, 26, G)
oval(im, CX - 15, 24, 31, 24, K)
oval(im, CX - 14, 24, 29, 24, R)
# face shade down the right and under
for y in range(24, 48):
    for x in range(CX - 14, CX + 15):
        p = im.getpixel((x, y))
        if p[:3] == (0xb6, 0x43, 0x3d):
            q = im.getpixel((x + 2, y + 1))
            if q[:3] == (0, 0, 0) or q[3] == 0 or im.getpixel((x, y + 2))[:3] == (0, 0, 0):
                dot(im, x, y, RD)
# brow light
rect(im, CX - 9, 26, 6, 1, RL)
rect(im, CX - 11, 27, 3, 1, RL)
rect(im, CX - 4, 25, 5, 1, RL)

# brows: heavy V, black
for i in range(7):
    rect(im, CX - 10 + i, 29 + i // 2, 2, 2, K)
    rect(im, CX + 9 - i, 29 + i // 2, 2, 2, K)
# eyes: 2 px marks under the brows
rect(im, CX - 8, 34, 2, 1, K)
rect(im, CX + 7, 34, 2, 1, K)
# nose
rect(im, CX - 1, 35, 3, 1, RD)
dot(im, CX - 1, 36, K)
dot(im, CX + 1, 36, K)

# mouth
rect(im, CX - 9, 39, 19, 6, K)
rect(im, CX - 10, 40, 1, 4, K)
rect(im, CX + 10, 40, 1, 4, K)
# upper teeth
for x in range(CX - 5, CX + 5, 3):
    rect(im, x, 39, 2, 2, B)
# lower teeth
for x in (CX - 4, CX - 1, CX + 2):
    rect(im, x, 43, 2, 2, B)
# tusks rising from the lower jaw, past the lip
for dx in (-8, 8):
    rect(im, CX + dx - 1, 41, 3, 5, B)
    rect(im, CX + dx - 1, 38, 3, 3, B)
    rect(im, CX + dx + 1, 41, 1, 5, M)
    dot(im, CX + dx + (1 if dx < 0 else -1), 38, RD if dx < 0 else R)
# chin
rect(im, CX - 5, 46, 11, 1, RD)

# --- foot ---
rect(im, CX - 19, 52, 39, 4, D)
rect(im, CX - 21, 53, 43, 3, D)
rect(im, CX - 19, 52, 26, 1, M)
rect(im, CX - 21, 53, 8, 1, M)
for x in range(CX - 18, CX + 19, 6):
    rect(im, x, 54, 1, 2, K)

im = outline(im)
save(im)
