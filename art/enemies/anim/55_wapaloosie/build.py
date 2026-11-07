"""Wapaloosie's animation (Two-mode, a stance change: on all fours, then reared up at its side in phase 2).
From its approved 26x26 frames: on all fours (rest, HUMP, low) and reared (rest, CHEST UP, low).
Its views stay as drawn: front, and one side view for every other direction (it never faces up).
  all fours: rest, HUMP (frame 1: the spike fan leaves on it), rest, low, rest    5 x 260 ms = 1.3 s, the old loop
  reared:    rest, CHEST UP (frame 1: the spore ring), rest, low, rest           the alt sheet, same timing
  flap sheet (picked by Wapaloosie::flap_phase): 0 hump high, 1 crouched rear -- standing up as it arrives,
             a step each; 2 the spore burst (its spore dots bristled out), a step as phase 1's ring leaves
Run: python -B art/enemies/anim/55_wapaloosie/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W, H = 26, 26
CLEAR = (0, 0, 0, 0)

def cell(im, i): return im.crop((i * W, 0, i * W + W, H)).convert('RGBA')

def is_spore(p): return p[3] and p[0] > 200 and p[1] > 180 and p[2] < 140

def burst(fr):
    """The spore dots, each pushed a pixel out from the body's middle where there is room."""
    px = fr.load(); out = fr.copy(); po = out.load()
    box = fr.getbbox(); cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    for y in range(H):
        for x in range(W):
            if not is_spore(px[x, y]): continue
            dx = (x > cx) - (x < cx); dy = (y > cy) - (y < cy)
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and not px[nx, ny][3]:
                po[nx, ny] = px[x, y]; po[x, y] = CLEAR
    return out

def sheets():
    a = Image.open(os.path.join(HERE, 'original_idle.png')); u = Image.open(os.path.join(HERE, 'original_up.png'))
    S = {'idle': [], 'up': [], 'flap': []}
    for d in range(8):
        f = [cell(a, d * 3 + i) for i in range(3)]; g = [cell(u, d * 3 + i) for i in range(3)]
        S['idle'].append([f[0], f[1], f[0], f[2], f[0]])
        S['up'].append([g[0], g[1], g[0], g[2], g[0]])
        S['flap'].append([f[1], g[2], burst(f[0])])
    return S

def write(S, k, path):
    n = len(S[k][0]); im = Image.new('RGBA', (W * 8 * n, H))
    for d in range(8):
        for i, fr in enumerate(S[k][d]): im.paste(fr, ((d * n + i) * W, 0))
    im.save(path)

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    S = sheets(); gap = 4
    rows = [S['idle'][0] + S['flap'][0], S['idle'][2] + S['flap'][2], S['up'][0], S['up'][2]]
    board = Image.new('RGBA', (8 * (W + gap) + gap, 4 * (H + gap) + gap), (40, 40, 40, 255))
    for r, seq in enumerate(rows):
        for c, fr in enumerate(seq): board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board.resize((board.width * 6, board.height * 6), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def install():
    S = sheets(); d = os.path.join(ROOT, 'assets/enemies')
    write(S, 'idle', os.path.join(d, '55_wapaloosie.png'))
    write(S, 'up', os.path.join(d, '55_wapaloosie_up.png'))
    write(S, 'flap', os.path.join(d, '55_wapaloosie_flap.png'))

if __name__ == '__main__':
    if '--install' in sys.argv: install()
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
