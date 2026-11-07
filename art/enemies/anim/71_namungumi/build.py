"""Namungumi's animation (lies where it is, shuffling; front view only). PixelLab from its approved 37x26 NES
sprite on a 52x40 canvas.
  idle (8 x 260 ms = 2.08 s; its old loop was 1.94): breath-00..04 (frame 2 the crest highest: the eye's ring),
        then its shuffle steps 5-7 (shuffle-01, -02, -01 mirrored; Namungumi::WALK_FROM = 5)
  EYE: the user -- "eye shooting laser should be a lot more obvious from a sprite animation standpoint, it should
        also be obvious what direction the laser goes in". Its beam runs both ways along a line, so the eye blazes
        white and the beam's LINE is drawn across its body, 15 px each way, in 8 angles (0, 22.5 ... 157.5 deg,
        screen y down) -- a slash inside the 9 px eye alone was too small to read:
  flap (16): for angle k, frame 2k = CHARGE (idle frame 0, the eye whitened, the line DASHED along the coming beam --
        blinking, then held, in the warning before it fires), 2k+1 = FIRE (the line SOLID, the body squashed a pixel in
        recoil, while the beam shoots out and holds).
  Prints the eye's middle on each idle frame for Namungumi::eye() (PUPIL_X/Y).
Run: python -B art/enemies/anim/71_namungumi/build.py [--install]"""
import os, sys, math
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
W, H = 52, 40
WHITE = (252, 252, 252, 255)

def idle():
    pal = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    L = lambda n: pt.tidy(pt.snap(Image.open(os.path.join(HERE, 'pixellab', n)), pal))
    b = [L('breath-%02d.png' % i) for i in range(5)]
    s1, s2 = L('shuffle-01.png'), L('shuffle-02.png')
    return b + [s1, s2, pt.mirror(s1)]

def eye_centre(fr):
    """The eye: its pale slit pixels in the upper half (the tusks, the other pale bit, are below)."""
    px = fr.load(); box = fr.getbbox(); mid = (box[1] + box[3]) / 2
    pts = [(x, y) for y in range(box[1], int(mid)) for x in range(W) if px[x, y][3] and sum(px[x, y][:3]) > 560]
    return sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)

def eye_frame(fr, k, recoil):
    """The eye blazing white, and the beam's LINE drawn across its body both ways: a white line, black-edged,
    REACH px each way along angle k -- dashed on the charge (the warning), solid on the fire."""
    out = fr.copy(); px = out.load(); cx, cy = eye_centre(fr)
    cx += 0.5; cy += 0.5
    th = k * math.pi / 8; ux, uy = math.cos(th), math.sin(th)
    RX, RY, REACH = 4.6, 3.1, 15.0
    for y in range(H):                                                # the eye, whitened
        for x in range(W):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            e = (dx / RX) ** 2 + (dy / RY) ** 2
            if e <= 1.0: px[x, y] = pt.BLACK if e > 0.62 else WHITE
    line, edge = set(), set()
    for i in range(-int(REACH * 4), int(REACH * 4) + 1):
        t = i / 4.0
        if not recoil and abs(t) > 4.5 and int(abs(t)) % 4 >= 2: continue   # dashed while charging
        x, y = int(cx + ux * t), int(cy + uy * t)
        if 0 <= x < W and 0 <= y < H: line.add((x, y))
    for (x, y) in line:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in line and 0 <= q[0] < W and 0 <= q[1] < H: edge.add(q)
    for q in edge: px[q] = pt.BLACK
    for q in line: px[q] = WHITE
    if recoil:
        b = out.getbbox(); c = out.crop(b); c = c.resize((c.width, c.height - 1), Image.NEAREST)
        r = Image.new('RGBA', (W, H), pt.CLEAR); r.paste(c, (b[0], b[1] + 1), c); out = r
    return out

if __name__ == '__main__':
    F = idle()
    flap = []
    for k in range(8):
        flap += [eye_frame(F[0], k, False), eye_frame(F[0], k, True)]
    gap = 4
    board = Image.new('RGBA', (8 * (W + gap) + gap, 3 * (H + gap) + gap), (40, 40, 40, 255))
    for i, fr in enumerate(F): board.paste(fr, (gap + i * (W + gap), gap), fr)
    for i, fr in enumerate(flap): board.paste(fr, (gap + (i // 2) * (W + gap), gap + (1 + i % 2) * (H + gap)), fr)
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(os.path.join(HERE, 'review', 'board.png'))
    cs = [eye_centre(f) for f in F]
    print('PUPIL_X = {%s}' % ', '.join('%.1ff' % ((c[0] + 0.5 - W / 2) * 2) for c in cs))
    print('PUPIL_Y = {%s}' % ', '.join('%.1ff' % ((c[1] + 0.5 - H / 2) * 2) for c in cs))
    if '--install' in sys.argv:
        d = os.path.join(ROOT, 'assets/enemies/redraws')
        P = {'down': {'idle': F, 'flap': flap}}
        pt.sheet(P, 'idle', os.path.join(d, '71_namungumi.png'), W, H, front_only=True)
        pt.sheet(P, 'flap', os.path.join(d, '71_namungumi_beam.png'), W, H, front_only=True)
        print(pt.check_frames(os.path.join(d, '71_namungumi.png'), 8, W, H, views=(('down', 0),))[0])
