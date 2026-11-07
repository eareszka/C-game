"""Moskitto's animation (Flyer: always aloft, always faces down; front view only).
From its approved 31x31 NES sprite, on a 31x37 canvas (3 px pad top and bottom).
  idle (5 x 260 ms; the volleys leave on its frames, Moskitto::on_idle_frame):
     0 wings up (the cycle wraps: stings off the wings), 1 mid, 2 down, 3 mid,
     4 wings up, proboscis thrust 2 px (the needle)
  grab (flap sheet, swooping and chasing): the wingbeat with the legs snapping
     open, shut, open, shut
The wings are cut from the body and moved as layers: mid = slid down 3 px, down =
flipped about the shoulder; the body (legs included) is drawn over them.
Run: python -B art/enemies/anim/56_moskitto/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W, H0, PAD = 31, 31, 3
H = H0 + 2 * PAD
CLEAR = (0, 0, 0, 0)

def is_wing(x, y):
    if y > 11: return False
    return x <= (11 if y <= 9 else 10) or x >= 19

def layers():
    s = Image.open(os.path.join(HERE, 'original_sprite.png')).convert('RGBA'); px = s.load()
    wing, body = {}, {}
    for y in range(H0):
        for x in range(W):
            p = px[x, y]
            if not p[3]: continue
            (wing if is_wing(x, y) else body)[(x, y)] = p
    return wing, body

LEGS = lambda x, y: 15 <= y <= 27 and (x <= 10 or x >= 20)
PROBOSCIS_ROW = 28   # 'aba', repeated to thrust the tip down

def frame(wings='up', legs='open', thrust=False):
    wing, body = layers()
    g = [[CLEAR] * W for _ in range(H)]
    def put(x, y, p):
        if 0 <= x < W and 0 <= y < H: g[y][x] = p
    for (x, y), p in wing.items():
        ny = y if wings == 'up' else y + 3 if wings == 'mid' else 21 - y
        put(x, ny + PAD, p)
    for (x, y), p in body.items():
        if legs == 'shut' and LEGS(x, y):
            continue
        ny = y + (2 if thrust and y > PROBOSCIS_ROW else 0)
        put(x, ny + PAD, p)
    if thrust:
        for k in (1, 2):
            for x in range(14, 17): put(x, PROBOSCIS_ROW + k + PAD, body.get((x, PROBOSCIS_ROW), CLEAR))
    if legs == 'shut':   # legs drawn in 2 px toward the body, under it
        for (x, y), p in body.items():
            if not LEGS(x, y): continue
            nx = x + 2 if x <= 10 else x - 2
            if not g[y + PAD][nx][3]: put(nx, y + PAD, p)
    return g

def frames():
    return {'idle': [frame('up'), frame('mid'), frame('down'), frame('mid'), frame('up', thrust=True)],
            'grab': [frame('up', 'open'), frame('mid', 'shut'), frame('down', 'open'), frame('mid', 'shut')]}

def to_img(g):
    im = Image.new('RGBA', (W, H))
    for y in range(H):
        for x in range(W): im.putpixel((x, y), g[y][x])
    return im

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    F = frames(); seq = F['idle'] + F['grab']; gap = 4
    board = Image.new('RGBA', (len(seq) * (W + gap) + gap, H + 2 * gap), (40, 40, 40, 255))
    for i, g in enumerate(seq):
        fr = to_img(g); board.paste(fr, (gap + i * (W + gap), gap), fr)
    board.resize((board.width * 6, board.height * 6), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def install():
    F = frames(); d = os.path.join(ROOT, 'assets/enemies')
    for k, path in (('idle', '56_moskitto.png'), ('grab', '56_moskitto_grab.png')):
        n = len(F[k]); im = Image.new('RGBA', (W * 8 * n, H))
        for dd in range(8):
            for i, g in enumerate(F[k]):
                fr = to_img(g); im.paste(fr, ((dd * n + i) * W, 0))
        im.save(os.path.join(d, path))

if __name__ == '__main__':
    if '--install' in sys.argv: install()
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
