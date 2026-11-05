import os

from pix import *

im = load('before.png')
im = strip_outline(im)

C = {'f': '4fa667', 'g': 'e8e0c0', 'd': '815423', 'e': '633e1b', 'c': '2c6c44', 'K': '000000'}


def row(x, y, text):
    for i, ch in enumerate(text):
        dot(im, x + i, y, C[ch])


# Take the old trunk off the top of the head, and the old snout and mouth.
for y in range(17, 21):
    for x in range(30, 44):
        dot(im, x, y, None)
for y in range(21, 27):
    for x in range(29, 44):
        dot(im, x, y, None)

# Canopy underside where the old trunk went in.
row(33, 16, 'cc')

# Trunk: out of the mouth, round the front of the snout, up into the canopy.
row(37, 16, 'de')
row(36, 17, 'ddde')
row(37, 18, 'ddde')
row(38, 19, 'ddde')
row(39, 20, 'ddde')

# Upper jaw, top teeth, trunk in the mouth. The bottom teeth in row 27 stay.
row(29, 21, 'fffffffffKddde')
row(29, 22, 'fffffffffKddde')
row(29, 23, 'fKfffffffKddde')
row(29, 24, 'fKfffKgKgKddde')
row(29, 25, 'fffffKddddddde')
row(29, 26, 'fffffKeeeeeeee')
row(34, 27, 'K')

im = outline(im)

# Remove the working file left by the earlier pass.
if os.path.exists('dump.txt'):
    os.remove('dump.txt')

save(im)
