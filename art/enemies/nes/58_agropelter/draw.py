from pix import *
import os

im = load('before.png')
im = strip_outline(im)

TONE = {'d': 'f0b890', 'e': 'd7a175'}


def run(y, x, tones):
    for i, t in enumerate(tones):
        dot(im, x + i, y, TONE[t])


# Left arm: wrist to shoulder, one row at a time.
run(18, 15, 'ddd')
run(19, 14, 'ddddd')
run(20, 13, 'dddddd')
run(21, 12, 'dddeeedd')
run(22, 12, 'dde')
run(22, 17, 'eddd')
run(23, 12, 'dde')
run(23, 18, 'edd')
run(24, 12, 'ee')

# Right arm: shoulder to wrist.
run(23, 32, 'd')
run(24, 33, 'd')
run(25, 34, 'dd')
run(26, 34, 'dddddde')
run(27, 34, 'edddde')
run(28, 35, 'edde')
run(29, 35, 'eee')
run(25, 38, 'ddde')
run(24, 39, 'ddde')
run(23, 40, 'dde')

im = outline(im)

# Remove the working map left by earlier passes.
if os.path.exists('dump.txt'):
    os.remove('dump.txt')

save(im)
