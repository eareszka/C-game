"""Hidebehind's idle, PixelLab version (the user, 2026-11-18: "its not animating. use pixellab and make sure its
animating properly"): the user's 49x46 still animated by PixelLab (animate base.png, 8 frames, 1 generation:
the fur breathing, the eyes blinking shut, the claws curling into fists), snapped to the still's colours.
Cut to 4 frames x 260 ms = 1.04 s, played in order:
  0 rest (the still, eyes open, claws open)   1 breathing in (PL 03: risen, claws curling)
  2 FISTS, eyes shut (PL 05)                  3 breathing out (PL 07: eyes shut, claws opening)
D DR R UR U the drawing, UL L DL its mirror. The hand-drawn version is build_hand.py.
Run: python -B art/enemies/anim/63_hidebehind/build.py [--install]"""
import os, sys
from PIL import Image, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common')); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import pixtools as pt
import enemy_sheet as es
PL = os.path.join(HERE, 'pixellab')
SHEET = os.path.join(ROOT, 'assets/enemies/redraws/63_hidebehind.png')
MS = 260
PICK = (0, 3, 5, 7)                  # PixelLab frames kept (00 is the still itself)
CREAM = (232, 224, 192, 255)

def frames():
    P = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    fs = [Image.open(os.path.join(PL, 'base.png')).convert('RGBA')] + \
         [pt.tidy(pt.snap(Image.open(os.path.join(PL, 'breathe-%02d.png' % i)), P)) for i in PICK[1:]]
    bs = [f.getbbox() for f in fs]; box = [min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)]
    W, H = box[2] - box[0], box[3] - box[1]; W += W % 2; H += H % 2
    box = (box[0], box[3] - H, box[0] + W, box[3])
    return [f.crop(box) for f in fs], box

def fans(f):
    """Each hand's claw fan centre: the middle of its cream px (the upper corners, above the eyes)."""
    W, H = f.size; p = f.load(); out = []
    for side in (lambda x: x < W // 2 - 8, lambda x: x >= W // 2 + 8):
        c = [(x, y) for y in range(H // 2) for x in range(W) if side(x) and p[x, y] == CREAM]
        out.append((sum(x for x, _ in c) / len(c), sum(y for _, y in c) / len(c)))
    return out

def full_sheet(fs):
    W, H = fs[0].size; sh = Image.new('RGBA', (8 * len(fs) * W, H), pt.CLEAR)
    for d in range(8):
        for i, f in enumerate(fs): sh.paste(f.transpose(Image.FLIP_LEFT_RIGHT) if d in (5, 6, 7) else f, ((d * len(fs) + i) * W, 0))
    return sh

def on_bg(f): return Image.alpha_composite(Image.new('RGBA', f.size, (24, 24, 32, 255)), f)

def gif(fs, path, s=6, box=None):
    """Full frames, no optimizing; then reopened fresh for each frame (seek + load) and checked to differ."""
    g = [on_bg(f).crop(box or (0, 0) + f.size).convert('RGB') for f in fs]
    g = [x.resize((x.width * s, x.height * s), Image.NEAREST) for x in g]
    g[0].save(path, save_all=True, append_images=g[1:], duration=MS, loop=0, disposal=1, optimize=False)
    back = []
    for i in range(len(g)):
        r = Image.open(path); r.seek(i); r.load(); back.append(r.convert('RGB'))
    diffs = [ImageChops.difference(back[0], b).getbbox() for b in back]
    assert all(d is not None for d in diffs[1:]), (path, diffs)
    return diffs

if __name__ == '__main__':
    fs, box = frames(); W, H = fs[0].size
    rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
    for i, f in enumerate(fs): on_bg(f).resize((W * 6, H * 6), Image.NEAREST).save(os.path.join(rv, 'frame_%d.png' % i))
    gap = 3; st = Image.new('RGBA', (len(fs) * (W + gap) + gap, H + 2 * gap), (24, 24, 32, 255))
    for i, f in enumerate(fs): st.alpha_composite(f, (gap + i * (W + gap), gap))
    st.resize((st.width * 6, st.height * 6), Image.NEAREST).save(os.path.join(rv, 'strip_6x.png'))
    print('idle gif diffs vs f0', gif(fs, os.path.join(rv, 'idle_260.gif')))
    print('close-up diffs vs f0', gif(fs, os.path.join(rv, 'closeup_260.gif'), 12, (0, 0, W, H * 3 // 5)))
    print('frame %dx%d, box in the 64x64 canvas' % (W, H), box, '| px changed vs f0:',
          [sum(1 for a, b in zip(fs[0].getdata(), f.getdata()) if a != b) for f in fs])
    t = os.path.join(rv, 'check.png'); full_sheet(fs).save(t)
    print(*pt.check_frames(t, len(fs), W, H, views=(('D', 0),)), sep=chr(10)); os.remove(t)
    off = lambda p: '(%+.0f,%+.0f)' % ((p[0] + .5 - W / 2) * 2, (p[1] + .5 - H / 2) * 2)
    for i, f in enumerate(fs):
        l, r = fans(f); print('f%d fan L art (%.1f,%.1f) %s  R art (%.1f,%.1f) %s' % (i, *l, off(l), *r, off(r)))
    if '--install' in sys.argv:
        sh = full_sheet(fs); sh.save(SHEET)
        es.pack(sh, SHEET[:-4] + '.aseprite', len(fs), False); es.built(SHEET); os.utime(SHEET, None)
