"""19 Skeljaskrimsli's head is all mouth (the user, 2026-10-29: "like the entire head is the mouth no eye sockets
too"). Drawn by hand over the turned head of frame 0: a round maw facing the viewer -- a thin plated rim lit on
top, a ring of pale green teeth pointing in, a dark throat. Painted over whatever was there inside the head's
oval (it is in front of the body), one black outline round it. paste(frame) puts the same head on an
animated frame, so it never changes as the body moves.

    python art/enemies/pixellab/19_skeljaskrimsli/maw.py   (frame 0, from idle_frame0_eyedhead.png)
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
K, RIM, LIT, TOOTH, TOOTH_D, THROAT = (0, 0, 0), (0x47, 0x47, 0x51), (0x84, 0x86, 0x94), (0xa8, 0xf0, 0xbc), (0x2c, 0x6c, 0x44), (0x29, 0x29, 0x31)
X0, X1, Y0, Y1 = 4, 25, 19, 40                  # the head's box on the 86x43 canvas
JAW = 4                                         # each jaw's plated depth, rows
FANG = 4                                        # how far a fang reaches into the throat, rows
TEETH = 5                                       # fangs along each jaw


def maw():
    """{(x, y): colour} of the head: wide-open jaws (a ring of teeth read as an eye's iris) -- a plated upper jaw,
    its fangs hanging down, a plated lower jaw, its fangs pointing up, the dark throat between, corners rounded."""
    g = {}
    w, h = X1 - X0, Y1 - Y0
    for y in range(Y0, Y1):
        for x in range(X0, X1):
            u, v = x - X0, y - Y0
            corner = min(u, w - 1 - u) + min(v, h - 1 - v)
            if corner < 2:                                                    # rounded corners
                continue
            if v < JAW:
                g[x, y] = LIT if v == 0 or (v == 1 and corner > 3) else RIM          # the upper jaw, lit along its top
            elif v >= h - JAW:
                g[x, y] = RIM                                                         # the lower jaw
            else:
                span = w / TEETH
                k = ((u + 0.5) % span) / span                                         # across a fang: 0.5 its point
                long = FANG * (1 - abs(k - 0.5) * 2)                                  # a triangle
                if v - JAW < long:
                    g[x, y] = TOOTH                                                   # upper fangs, hanging
                elif (h - JAW - 1) - v < long * 0.85:
                    g[x, y] = TOOTH_D                                                 # lower fangs, in shade
                else:
                    g[x, y] = K if abs(u - w / 2) < w * 0.3 and abs(v - h / 2) < 3 else THROAT   # the throat, black at its depth
    return g


def paste(im):
    out = im.copy()
    g = maw()
    for p, c in g.items():
        out.putpixel(p, c + (255,))
    for (x, y) in g:
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + ddx, y + ddy)
            if q not in g and 0 <= q[0] < out.width and 0 <= q[1] < out.height:
                out.putpixel(q, K + (255,))
    return out


if __name__ == '__main__':
    paste(Image.open(HERE / 'idle_frame0_eyedhead.png').convert('RGBA')).save(HERE / 'idle_frame0_clean.png')
    print('maw on frame 0')
