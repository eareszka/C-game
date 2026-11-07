"""Ayotochtli's animation (Two-mode Walker + Blocker: stands, then curls into its ball and rolls; the ball is its guard).
From its approved 48x35 frames: standing (rest, HUNCH, low) and the ball's roll (4). Four views: down, right, up;
left = right mirrored (the code faces D R U L).
  idle: rest, HUNCH (frame 1: the plate ring leaves on it), rest, low, rest   5 x 260 ms = 1.3 s, the old loop
  roll sheet (flap, picked by Ayotochtli::flap_phase): 0 hunch, 1 ball -- guard in (hunch, ball) before a roll and
        guard out (ball, hunch) after; 2-5 the roll, 65 ms a pose fast, 130 ms slow (the user asked for faster spins, twice)
  The ball is drawn, not cut from the art (the user: "when rolling it should be a spinning ball without other
  features"): a plain shell sphere in its own four colours, plate seams as lines of latitude that scroll a
  sixteenth of a turn a pose -- down the ball rolling toward us, up away, sideways rolling right or left --
  crossed by two fixed seams.
Run: python -B art/enemies/anim/66_ayotochtli/build.py [out_dir] | --install"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
W, H = 48, 35
DIRS = {'down': 0, 'right': 2, 'up': 4}

def cell(im, i): return im.crop((i * W, 0, i * W + W, H)).convert('RGBA')

import math
OUT, SHELL, SHADE, LIGHT = (0, 0, 0, 255), (178, 158, 92, 255), (141, 107, 79, 255), (208, 192, 120, 255)
SEAM = (35, 84, 54, 255)               # the seams in its standing sprite's green (the user), not black
CX, CY, R = 23.5, 21.5, 11.6          # the old ball's middle and size (rows 9-33)

def ball(pose, view):
    """One pose of the spin. view: 'down' (seams roll down), 'up', 'right', 'left'."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); px = im.load()
    turn = pose * math.pi / 16 * (1 if view in ('down', 'right') else -1)
    lats = [turn + k * math.pi / 4 for k in range(-4, 5)]
    lines = [R * math.sin(t) for t in lats if -math.pi / 2 < t < math.pi / 2]
    fixed = [-R * math.sin(0.42), R * math.sin(0.42)]
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - CX, y + 0.5 - CY
            d = math.hypot(dx, dy)
            if d > R: continue
            if d > R - 1.0: px[x, y] = OUT; continue
            along, across = (dy, dx) if view in ('down', 'up') else (dx, dy)
            if any(abs(along - l) < 0.5 for l in lines) or any(abs(across - f) < 0.5 for f in fixed):
                px[x, y] = SEAM; continue
            if dx + dy > R * 0.62: px[x, y] = SHADE
            elif d > R - 2.0 and dx + dy < -R * 0.55: px[x, y] = LIGHT
            else: px[x, y] = SHELL
    return im

def poses():
    a = Image.open(os.path.join(HERE, 'original_idle.png')); r = Image.open(os.path.join(HERE, 'original_roll.png'))
    P = {}
    for v, d in DIRS.items():
        f = [cell(a, d * 3 + i) for i in range(3)]; g = [cell(r, d * 4 + i) for i in range(4)]
        P[v] = {'idle': [f[0], f[1], f[0], f[2], f[0]], 'roll': [f[1], ball(0, v)] + [ball(i, v) for i in range(4)]}
    return P

def mirror(im): return im.transpose(Image.FLIP_LEFT_RIGHT)

def sheet(P, k, path):
    n = len(P['down'][k]); im = Image.new('RGBA', (W * 8 * n, H))
    for d, dn in enumerate(['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']):
        seq = P['down'][k] if dn == 'D' else P['up'][k] if dn == 'U' else P['right'][k] if dn in ('DR', 'R', 'UR') else [mirror(x) for x in P['right'][k]]
        for i, fr in enumerate(seq): im.paste(fr, ((d * n + i) * W, 0))
    im.save(path)

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    P = poses(); gap = 4
    board = Image.new('RGBA', (11 * (W + gap) + gap, 3 * (H + gap) + gap), (40, 40, 40, 255))
    for r, v in enumerate(DIRS):
        for c, fr in enumerate(P[v]['idle'] + P[v]['roll']): board.paste(fr, (gap + c * (W + gap), gap + r * (H + gap)), fr)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(out_dir, 'board.png'))

def install():
    P = poses(); d = os.path.join(ROOT, 'assets/enemies/redraws')
    sheet(P, 'idle', os.path.join(d, '66_ayotochtli.png')); sheet(P, 'roll', os.path.join(d, '66_ayotochtli_roll.png'))

if __name__ == '__main__':
    if '--install' in sys.argv: install()
    else: build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'review'))
