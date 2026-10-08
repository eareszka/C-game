"""Design for the Ofuguggi swimming backwards (assets/enemies/15_ofuguggi_swim.aseprite).

    python art/enemies/15_ofuguggi_swim_design.py <out.json>
    python tools/draw_views.py <out.json> assets/enemies/15_ofuguggi_swim   # through the pixel plugin

The Reverse-Fin Trout "swims backwards with its tail first and the head
following". In its fight it swims a loop across the top of the arena the
whole time, faced against its motion, so the tail leads. Laid out like the
idle sheet: one row, 32x23 frames, directions D DR R UR U UL L DL, four
frames each, a seamless loop (the battle's flap path).

Every frame is idle frame 0 of its direction (assets/enemies/15_ofuguggi.png)
bent by a travelling wave, whole columns moved up or down so the pixels stay
on the grid and the outline unbroken. In a fish the wave runs from head to
tail and pushes it forward; here it runs the other way, from the leading
tail back to the trailing head -- the push comes from the front -- growing
as it goes, so it reads as reversing through the water. Seen end-on (front
and back) the same wave sways the rows from side to side instead.
"""
import json, math, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IDLE = os.path.join(HERE, '..', '..', 'assets', 'enemies', '15_ofuguggi.png')
PAL = {'K': '000000', 'D': '474751', 'M': '34343e', 'S': '848694', 'R': 'b70000', 'r': '7c0a1b',
       'P': 'ec8476', 'G': '9797aa'}
ORDER = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
FW, FH, N_IDLE, FRAMES = 32, 23, 3, 4
WAVE = 2 * math.pi / 22              # one wavelength over about the body's length
AMP = 1.4                            # px, at the trailing head

def idle_frame0(d):
    im = Image.open(IDLE).convert('RGBA')
    letter = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)): k for k, v in PAL.items()}
    x0 = ORDER.index(d) * N_IDLE * FW
    return [[('.' if im.getpixel((x0 + x, y))[3] == 0 else letter[im.getpixel((x0 + x, y))[:3]])
             for x in range(FW)] for y in range(FH)]

def bent(g, k, lead_right):
    """Columns moved by a wave travelling from the leading tail to the trailing head."""
    xs = [x for x in range(FW) if any(g[y][x] != '.' for y in range(FH))]
    x0, x1 = min(xs), max(xs)
    out = [['.'] * FW for _ in range(FH)]
    for x in range(FW):
        back = (x1 - x) if lead_right else (x - x0)          # how far behind the leading tail this column is
        amp = AMP * (0.35 + 0.65 * back / max(1, x1 - x0))   # growing toward the trailing head
        dy = round(amp * math.sin(2 * math.pi * k / FRAMES - WAVE * back))   # moving back along the body
        for y in range(FH):
            if g[y][x] != '.' and 0 <= y + dy < FH: out[y + dy][x] = g[y][x]
    return out

def swayed(g, k):
    """End-on: the same wave sways the rows from side to side."""
    out = [['.'] * FW for _ in range(FH)]
    for y in range(FH):
        dx = round(1.0 * math.sin(2 * math.pi * k / FRAMES - WAVE * y * 1.6))
        for x in range(FW):
            if g[y][x] != '.' and 0 <= x + dx < FW: out[y][x + dx] = g[y][x]
    return out

def main(out):
    views, order = {}, []
    for d in ORDER:
        g = idle_frame0(d)
        for k in range(FRAMES):
            if d in ('D', 'U'):
                f = swayed(g, k)
            else:
                f = bent(g, k, lead_right=d in ('DR', 'R', 'UR'))   # faced right, its tail leads to the right
            views[f'{d}{k}'] = [''.join(r) for r in f]
            order.append(f'{d}{k}')
    json.dump({'pal': PAL, 'view_w': FW, 'order': order, 'views': views}, open(out, 'w'))

if __name__ == '__main__':
    main(sys.argv[1])
