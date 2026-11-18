"""Hugag's phase-1 WALK (the manager, 2026-11-18: the old 98x65 design, side view, 4 x 260 ms = one 1.04 s cycle,
a stiff stilt plod -- jointless legs swung straight from the hip, no knees -- the body and head bobbing slightly).
By hand from the restored idle's f0 (49d2e857): the body (rows < LEG_TOP) and its four legs cut apart; each leg
sheared about its hip (a rigid swing), diagonal pairs together (near-hind A + far-front D, far-hind B + near-front C):
  0 A,D forward / B,C back (contact)   1 B,C lifted, passing; A,D upright, the body up 1 (the plod's high point)
  2 A,D back / B,C forward (contact)   3 A,D lifted, passing; B,C upright, the body up 1
Faces right (as the idle); left facings mirror it.  Run: python -B art/enemies/anim/62_hugag/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common')); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import pixtools as pt
import enemy_sheet as es
MS, W, H = 260, 98, 65
LEG_TOP = 39                                        # the first row below the coat's hem: legs only
LEGS = {'A': (21, 30), 'B': (30, 39), 'C': (39, 48), 'D': (48, 56)}   # x ranges: near-hind, far-hind, near-front, far-front
SHAFT = 52                                          # a plain shaft row (no hem, no foot), repeated to stretch a leg
SWING, LIFT = 4, 2                                  # the foot's swing either side of the hip (px), a passing foot's lift
#        A      B      C      D       (dx at the foot, lifted?)       body dy
POSES = [({'A': 4, 'B': -4, 'C': -4, 'D': 4}, set(), 0),
         ({'A': 0, 'B': 0, 'C': 0, 'D': 0}, {'B', 'C'}, -1),
         ({'A': -4, 'B': 4, 'C': 4, 'D': -4}, set(), 0),
         ({'A': 0, 'B': 0, 'C': 0, 'D': 0}, {'A', 'D'}, -1)]

def idle0(): return es.cells_of(Image.open(os.path.join(ROOT, 'assets/enemies/62_hugag.png')).convert('RGBA'), 5, False)['D'][0]

def parts():
    f = idle0(); body = f.copy(); body.paste(pt.CLEAR, (0, LEG_TOP, W, H)); legs = {}
    for k, (x0, x1) in LEGS.items():
        l = Image.new('RGBA', (W, H), pt.CLEAR); l.paste(f.crop((x0, LEG_TOP, x1, H)), (x0, LEG_TOP)); legs[k] = l
    return body, legs

def leg(l, dx, stretch, up):
    """A rigid leg: `stretch` shaft rows added (the body rose, the foot stays down), then each row slid in proportion
    to its distance from the hip (dx px at the foot), then the whole leg raised `up` px."""
    if stretch:
        s = Image.new('RGBA', (W, H), pt.CLEAR); s.alpha_composite(l.crop((0, 0, W, SHAFT)), (0, -stretch))
        for k in range(stretch + 1): s.alpha_composite(l.crop((0, SHAFT, W, SHAFT + 1)), (0, SHAFT - stretch + k))
        s.alpha_composite(l.crop((0, SHAFT + 1, W, H)), (0, SHAFT + 1)); l = s
    bb = l.getbbox(); top, foot = bb[1], bb[3] - 1
    out = Image.new('RGBA', (W, H), pt.CLEAR)
    for y in range(top, foot + 1):
        out.alpha_composite(l.crop((0, y, W, y + 1)), (round(dx * (y - top) / (foot - top)), y - up))
    return out

def frames():
    body, legs = parts(); fs, feet = [], []
    for dxs, lifted, dy in POSES:
        f = Image.new('RGBA', (W, H), pt.CLEAR); pts = {}
        for k in ('B', 'D', 'A', 'C'):              # far legs behind the near ones
            up = (LIFT - dy) if k in lifted else 0   # a lifted leg rides up with the body, plus its lift
            l = leg(legs[k], dxs[k], 0 if k in lifted else -dy, up); f.alpha_composite(l)
            bb = l.getbbox(); px = l.load(); y = bb[3] - 1
            xs = [x for x in range(W) if px[x, y][3]]; pts[k] = ((xs[0] + xs[-1]) / 2, y)
        b = Image.new('RGBA', (W, H), pt.CLEAR); b.alpha_composite(body, (0, dy)); f.alpha_composite(b)
        fs.append(f); feet.append(pts)
    return fs, feet

def gif(fs, path, s=5):
    g = [Image.alpha_composite(Image.new('RGBA', (W, H), (24, 24, 32, 255)), f).convert('RGB').resize((W * s, H * s), Image.NEAREST) for f in fs]
    g[0].save(path, save_all=True, append_images=g[1:], duration=MS, loop=0, disposal=2)

def full_sheet(fs):
    """D DR R UR U the drawing, UL L DL its mirror (as the idle and stomp sheets)."""
    sh = Image.new('RGBA', (8 * len(fs) * W, H), pt.CLEAR)
    for d in range(8):
        for i, f in enumerate(fs): sh.paste(f.transpose(Image.FLIP_LEFT_RIGHT) if d in (5, 6, 7) else f, ((d * len(fs) + i) * W, 0))
    return sh

if __name__ == '__main__':
    fs, feet = frames(); gap = 4
    rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
    b = Image.new('RGBA', (5 * (W + gap) + gap, H + 2 * gap), (24, 24, 32, 255))
    b.alpha_composite(idle0(), (gap, gap))           # the idle's f0 first, for comparison
    for i, f in enumerate(fs): b.alpha_composite(f, (gap + (i + 1) * (W + gap), gap))
    b.resize((b.width * 5, b.height * 5), Image.NEAREST).save(os.path.join(rv, 'walk_board.png'))
    gif(fs, os.path.join(rv, 'walk_260.gif'))
    off = lambda p: '(%+.0f,%+.0f)' % ((p[0] + .5 - W / 2) * 2, (p[1] + .5 - H / 2) * 2)
    for i, p in enumerate(feet):
        print('f%d' % i, '  '.join('%s %s art(%.1f,%d)' % (k, off(p[k]), *p[k]) for k in 'ABCD'))
    t = os.path.join(rv, 'check.png'); full_sheet(fs).save(t)
    print(*pt.check_frames(t, 4, W, H, views=(('D', 0),)), sep=chr(10)); os.remove(t)
    if '--install' in sys.argv:
        png = os.path.join(ROOT, 'assets/enemies/62_hugag_walk.png'); sh = full_sheet(fs); sh.save(png)
        es.pack(sh, png[:-4] + '.aseprite', 4, False); es.built(png); os.utime(png, None)
