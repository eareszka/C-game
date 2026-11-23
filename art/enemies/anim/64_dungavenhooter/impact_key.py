"""The IMPACT key (f6): PixelLab's k-impact4 (the tail arched over, the ball slammed down at the bottom left with
dust) + the tail's missing stretch drawn by hand: from its hanging end (row 26) down to the ball's top, in the
tail's own colours and pattern (outline, lit left edge, mid, dark right edge, a dark band every 5 rows); the ball
repainted over its end."""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
P = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
LIT, MID, DARK = (178, 158, 92, 255), (135, 106, 31, 255), (92, 70, 22, 255)
BALL = {(220, 240, 255, 255), (151, 151, 170, 255), (89, 89, 101, 255)}
TOP, BOT = 26, 50                       # the drawn stretch's rows
BEND = 37                               # by here it has swung left of the head (the head's left edge: x 13)
C0, CB, C1 = 22.5, 9.5, 11.0            # its centre at TOP, at BEND, at BOT (the ball's top)
W0, W1 = 8, 6                           # its width (outline included) at TOP and at BOT

def centre(y):
    import math
    if y <= BEND: t = (y - TOP) / (BEND - TOP); return C0 + (CB - C0) * math.sin(t * math.pi / 2)
    return CB + (C1 - CB) * (y - BEND) / (BOT - BEND)

def key():
    src = pt.snap(Image.open(os.path.join(HERE, 'pixellab', 'k-impact4.png')), P); im = src.copy(); px, sp = im.load(), src.load()
    for y in range(TOP, 31):                                   # the old rounded tip goes
        for x in range(16, 30):
            if sp[x, y][3] and y >= TOP: px[x, y] = pt.CLEAR
    for y in range(TOP, BOT + 1):
        t = (y - TOP) / (BOT - TOP); c = centre(y); w = round(W0 + (W1 - W0) * t)
        x0 = round(c - w / 2)
        band = (y - TOP) % 5 == 4
        for k in range(w):
            x = x0 + k
            px[x, y] = pt.BLACK if k in (0, w - 1) else (DARK if band or k == w - 2 else (LIT if k == 1 else MID))
    for y in range(BOT - 3, 64):                               # the ball over the tail's end
        for x in range(0, 20):
            if sp[x, y] in BALL: px[x, y] = sp[x, y]
    return im

if __name__ == '__main__':
    k = key(); k.save(os.path.join(HERE, 'pixellab', 'k-impact-hand.png'))
    b = Image.open(os.path.join(HERE, 'pixellab', 'base.png')).convert('RGBA')
    o = Image.new('RGBA', (130, 64), (24, 24, 32, 255)); o.alpha_composite(b, (0, 0)); o.alpha_composite(k, (66, 0))
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    o.resize((130 * 7, 64 * 7), Image.NEAREST).save(os.path.join(HERE, 'review', 'key_impact.png'))
