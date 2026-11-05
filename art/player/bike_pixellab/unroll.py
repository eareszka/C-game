"""PixelLab's 24 px batches wrap the wheels' bottoms round to the top row. Roll the
image so the largest empty band of rows is at the top; the drawing ends on row 23."""
from PIL import Image, ImageChops
def unroll(im):
    H = im.height
    full = [im.crop((0, y, im.width, y + 1)).getchannel('A').getbbox() is not None for y in range(H)]
    best, at, y = 0, 0, 0
    for s in range(H):
        n = 0
        while n < H and not full[(s + n) % H]: n += 1
        if n > best: best, at = n, s
    end = (at + best) % H              # the first drawn row
    last = (end - 1 - best) % H        # the last drawn row
    return ImageChops.offset(im, 0, (23 - last) % H)
