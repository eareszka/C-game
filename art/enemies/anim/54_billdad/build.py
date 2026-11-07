"""Billdad: the user kept its animation ("almost perfect") and asked only for its volley
animations. Phase 1's tail flick (idle frame 1), the landing splash (jump sheet frame 2) and the
phase-2 shockwave (slap sheet frame 2) have their poses; phase 2's flick of 5 had none.
This adds it as slap-sheet frame 4: back view, the tail flicked half up behind it (lower
than the slam's wind-up, frame 1, so the two don't read alike).
Run: python -B art/enemies/anim/54_billdad/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W, H = 28, 27
CLEAR = (0, 0, 0, 0)
LIFT = 4
TAIL_ROWS, TAIL_COLS = range(17, 25), range(9, 19)   # the hanging tail on the standing frame (3), outline included

def flick(stand):
    px = stand.load()
    out = stand.copy(); po = out.load()
    body = px[13, 14]                                  # the back's colour (the neck, above the tail)
    tail = {(x, y): px[x, y] for y in TAIL_ROWS for x in TAIL_COLS if px[x, y][3]}
    for (x, y) in tail:
        po[x, y] = body if 10 <= x <= 17 else px[x, y]     # what the tail covered: its rump
    for (x, y), p in tail.items():
        po[x, y - LIFT] = p
    return out

def frames():
    slap = Image.open(os.path.join(HERE, 'original_slap.png')).convert('RGBA')
    f = [slap.crop((i * W, 0, i * W + W, H)) for i in range(4)]
    return f + [flick(f[3])]

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    f = frames(); board = Image.new('RGBA', (5 * (W + 4) + 4, H + 8), (40, 40, 40, 255))
    for i, fr in enumerate(f): board.paste(fr, (4 + i * (W + 4), 4), fr)
    board.resize((board.width * 8, board.height * 8), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def write_sheets(assets):
    f = frames()   # the slap sheet: 8 directions alike (Billdad faces down), 5 frames each now
    im = Image.new('RGBA', (W * 8 * 5, H))
    for d in range(8):
        for i, fr in enumerate(f): im.paste(fr, ((d * 5 + i) * W, 0))
    im.save(os.path.join(assets, '54_billdad_slap.png'))

if __name__ == '__main__':
    if '--install' in sys.argv: write_sheets(os.path.join(ROOT, 'assets/enemies'))
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
