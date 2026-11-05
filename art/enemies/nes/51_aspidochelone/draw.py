from pix import *
import os

C = '967448'  # shell brown, lit
E = '633e1b'  # shell brown, shaded
K = '000000'
ROOM = 8

src = Image.open('before.png').convert('RGBA')
im = load('before.png')

# How far right the flipper's area reaches on each row, in before.png pixels.
# Past this is the head and its outline, which stay as they are.
REACH = {57: 54, 58: 55, 59: 56, 60: 58, 61: 57}


def in_area(x, y):
    return y >= 57 and x <= REACH.get(y, 59)


# Take the old flipper away.
for y in range(57, src.height):
    for x in range(src.width):
        if in_area(x, y):
            dot(im, x + ROOM, y + ROOM, None)

im = strip_outline(im)

# The new flipper, row by row: a shoulder coming out of the shell, a narrower
# arm, then a broad paddle with a rounded leading edge, ending in a blunt point.
SPANS = {
    57: (42, 54),
    58: (39, 55),
    59: (36, 56),
    60: (31, 58),
    61: (26, 57),
    62: (21, 55),
    63: (17, 54),
    64: (15, 52),
    65: (12, 50),
    66: (13, 47),
    67: (18, 40),
}


def inside(x, y):
    return y in SPANS and SPANS[y][0] <= x <= SPANS[y][1]


for y, (a, b) in SPANS.items():
    for x in range(a, b + 1):
        shaded = y == 57 or not inside(x, y + 2) or not inside(x + 4, y)
        dot(im, x + ROOM, y + ROOM, E if shaded else C)

# Black joints across the blade, leaning the same way as the shell's plates.
JOINTS = [
    [(41, 58), (41, 59), (42, 60), (42, 61), (43, 62), (43, 63), (44, 64), (45, 65), (46, 66)],
    [(32, 60), (32, 61), (33, 62), (33, 63), (34, 64), (34, 65), (35, 66), (35, 67)],
    [(22, 62), (22, 63), (23, 64), (23, 65), (24, 66), (24, 67)],
]
for joint in JOINTS:
    for x, y in joint:
        dot(im, x + ROOM, y + ROOM, K)

im = outline(im)

# Everything outside the flipper's area goes back exactly as it was.
OFF = ROOM + 1
for y in range(src.height):
    for x in range(src.width):
        if not in_area(x, y):
            im.load()[x + OFF, y + OFF] = src.load()[x, y]

save(im)

# Clear away the working notes from the earlier passes.
if os.path.exists('dump.txt'):
    os.remove('dump.txt')
