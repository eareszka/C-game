"""Opimachus's idle (the user, 2026-11-18: "keep design" -- this drawing, front only, 5 x 260 ms):
  0 rest (the still)  1 crest lifting  2 CREST BLOWN OUT (the ear rings)  3 head drawn back  4 THE PECK (head dips)
f1/f2: PixelLab (animate cr-01, edit k-crest) above the neck line, on the still's own body (rows from NECK down);
f3/f4: the still's head (crest + face) moved by hand: up 2 px, the neck stretched / down 4 px into the mantle.
Run: python -B art/enemies/anim/28_opimachus/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
PL = os.path.join(HERE, 'pixellab')
NECK = 33                       # the base canvas's first mantle row: the head (crest + face) is above it
HEAD = (22, 16, 44, 33)         # the still's head box in the 64x64 base
MS, CREST, PECK = 260, 2, 4
TIP = (32, 33, 35, 35)          # the beak's point, in the mantle rows (its very tip px (33,34))
BEAK_TIP = {0: 0, 1: 0, 2: 0, 3: 0, 4: 4}   # the tip's drop per frame (f3 the head rises, the beak stretched to its old tip)

def base(): return Image.open(os.path.join(PL, 'base.png')).convert('RGBA')

def top_from(n):
    """A PixelLab frame's head and crest on the still's body."""
    P = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))
    pl = pt.tidy(pt.snap(Image.open(os.path.join(PL, n + '.png')), P))
    out = base(); out.paste(pt.CLEAR, (0, 0, 64, NECK)); out.alpha_composite(pl.crop((0, 0, 64, NECK)), (0, 0))
    return out

def head_moved(dy):
    b = base(); head = b.crop(HEAD); out = b.copy(); out.paste(pt.CLEAR, HEAD)
    for k in range(-dy):        # drawn back: the face's bottom row repeated down the gap (the neck stretched)
        row = head.crop((0, head.height - 1, head.width, head.height)); out.alpha_composite(row, (HEAD[0], HEAD[3] - 1 - k))
    out.alpha_composite(head, (HEAD[0], HEAD[1] + dy))
    if dy > 0: tip = b.crop(TIP); out.alpha_composite(tip, (TIP[0], TIP[1] + dy))   # the beak's point, below the box, goes too
    return out

def frames():
    fs = [base(), top_from('cr-01'), top_from('k-crest'), head_moved(-2), head_moved(4)]
    bs = [f.getbbox() for f in fs]; box = (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))
    W, H = box[2] - box[0], box[3] - box[1]; W += W % 2; H += H % 2
    box = (box[0], box[3] - H, box[0] + W, box[3])
    return [f.crop(box) for f in fs], box

def beak_tip(i, box): return (33 - box[0], 34 + BEAK_TIP[i] - box[1])

def gif(fs, ms, path):
    W, H = fs[0].size
    g = [Image.alpha_composite(Image.new('RGBA', (W, H), (24, 24, 32, 255)), f).convert('RGB').resize((W * 5, H * 5), Image.NEAREST) for f in fs]
    g[0].save(path, save_all=True, append_images=g[1:], duration=ms, loop=0, disposal=2)

if __name__ == '__main__':
    fs, box = frames(); W, H = fs[0].size; gap = 4
    rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
    b = Image.new('RGBA', (5 * (W + gap) + gap, H + 2 * gap), (24, 24, 32, 255))
    for i, f in enumerate(fs): b.alpha_composite(f, (gap + i * (W + gap), gap))
    b.resize((b.width * 5, b.height * 5), Image.NEAREST).save(os.path.join(rv, 'board.png'))
    gif(fs, MS, os.path.join(rv, 'idle_260.gif'))
    off = lambda p: '(%+.0f,%+.0f)' % ((p[0] + .5 - W / 2) * 2, (p[1] + .5 - H / 2) * 2)
    print('frame %dx%d' % (W, H), 'box', box)
    for i, f in enumerate(fs): print('f%d beak tip' % i, off(beak_tip(i, box)))
    t = os.path.join(rv, 'check.png'); pt.sheet({v: {'i': fs} for v in ('down', 'right', 'up')}, 'i', t, W, H, front_only=True)
    print(*pt.check_frames(t, 5, W, H, views=(('D', 0),)), sep=chr(10)); os.remove(t)
    if '--install' in sys.argv:
        pt.sheet({v: {'i': fs} for v in ('down', 'right', 'up')}, 'i', os.path.join(ROOT, 'assets/enemies/28_opimachus.png'), W, H, front_only=True)
