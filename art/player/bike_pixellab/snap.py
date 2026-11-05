"""Snap a PixelLab image to the sheet's six colours, alpha binary."""
from PIL import Image
PAL = {'K': (0, 0, 0), 'H': (0x63, 0x3e, 0x1b), 'R': (0xb6, 0x43, 0x3d), 'S': (0xf0, 0xb8, 0x90), 'B': (0x84, 0x86, 0x94), 'L': (0xbc, 0xbe, 0xca)}
def nearest(c):
    return min(PAL.values(), key=lambda p: sum((a - b) ** 2 for a, b in zip(p, c)))
def snap(im):
    out = Image.new('RGBA', im.size)
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a >= 128: out.putpixel((x, y), nearest((r, g, b)) + (255,))
    return out
