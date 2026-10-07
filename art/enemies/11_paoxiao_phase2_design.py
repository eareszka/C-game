"""Design for Paoxiao's phase-2 sheets: the flank eye closed, and the leap.

    python art/enemies/11_paoxiao_phase2_design.py closed <out.json>
    python art/enemies/11_paoxiao_phase2_design.py leap   <out.json>
    python tools/draw_views.py <out.json> assets/enemies/11_paoxiao_closed   # (or _leap) through the pixel plugin

Both start from the idle sheet (assets/enemies/11_paoxiao.png: one row, 30x27
frames, directions D DR R UR U UL L DL, three idle frames each).

closed -- the idle sheet with the eye on its flank shut: every white pixel
  low on the body (rows 14-20; the face's eyes are higher) becomes the black
  of a closed lid, and the outline pixels just above and below it become body
  grey, so the eye reads as one dark line. Same layout as the idle sheet; it
  plays while phase 2 waits, and the eye opens (the normal idle) right
  before it charges.

leap -- each direction's idle frame 0 with the legs flung back level behind
  the body, floating, for the charge: rows 21 down are cleared and the four
  legs redrawn as bars trailing toward the tail -- left in the views whose
  head is right (D DR R UR U), right in their mirrors. Four identical frames a direction,
  the layout the battle's move sheet reads.
"""
import json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IDLE = os.path.join(HERE, '..', '..', 'assets', 'enemies', '11_paoxiao.png')
PAL = {'K': '000000', 'L': 'c6ccda', 'M': '9797aa', 'D': '595965', 'h': '34343e',
       'S': 'f0b890', 'W': 'fcfcfc', 'r': '7c0a1b'}
ORDER = ['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']
FW, FH, N_IDLE = 30, 27, 3
MIRRORED = {'UL', 'L', 'DL'}

def frame(d, f):
    im = Image.open(IDLE).convert('RGBA')
    letter = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)): k for k, v in PAL.items()}
    x0 = (ORDER.index(d) * N_IDLE + f) * FW
    return [[('.' if im.getpixel((x0 + x, y))[3] == 0 else letter[im.getpixel((x0 + x, y))[:3]])
             for x in range(FW)] for y in range(FH)]

def close_eye(g):
    whites = [(x, y) for y in range(14, 21) for x in range(FW) if g[y][x] == 'W']
    if not whites:
        return g
    x0 = min(x for x, y in whites) - 1
    x1 = max(x for x, y in whites) + 1
    ys = {y for x, y in whites}
    for x, y in whites:
        g[y][x] = 'K'
    for y in ys:
        for yy in (y - 1, y + 1):
            if yy in ys: continue
            for x in range(x0, x1 + 1):
                if g[yy][x] == 'K':
                    g[yy][x] = 'M'
    return g

# The legs in the head-right views, flung back level behind the body for the
# leap: each a bar three rows tall -- outline, fill, outline -- running from
# its toe at the back (left) to its joint at the body. The hind legs reach
# past the rump; the front legs, the creature's human skin, fold back under
# the belly. (x0, x1, middle row, fill, toe); drawn far legs first.
LEGS = [(0, 8, 21, 'D', 'h'), (11, 18, 22, 'S', 'S'),   # far hind, far front
        (2, 10, 23, 'D', 'h'), (13, 20, 24, 'S', 'S')]  # near hind, near front
CLEAR_FROM = 21   # rows below the belly line (row 20) are the standing legs

def leap(g, mirrored):
    if mirrored:
        g = [r[::-1] for r in g]
    for y in range(CLEAR_FROM, FH):
        for x in range(FW):
            g[y][x] = '.'
    for x0, x1, ym, fill, toe in LEGS:
        for x in range(x0, x1 + 1):
            g[ym - 1][x] = 'K'
            g[ym + 1][x] = 'K'
            g[ym][x] = toe if x == x0 else 'K' if x == x1 else fill
    if mirrored:
        g = [r[::-1] for r in g]
    return g

def main(kind, out):
    views, order = {}, []
    for d in ORDER:
        for f in range(N_IDLE if kind == 'closed' else 4):
            g = close_eye(frame(d, f)) if kind == 'closed' else leap(frame(d, 0), d in MIRRORED)
            key = f'{d}{f}'
            views[key] = [''.join(r) for r in g]
            order.append(key)
    json.dump({'pal': PAL, 'view_w': FW, 'order': order, 'views': views}, open(out, 'w'))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
