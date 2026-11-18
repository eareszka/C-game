"""Cactus Cat's animation (the user's picks, 2026-11-18 -- "keep it very simple", three things):
  phase 1  the DRUNK idle: key-drunk2 (leaning, eyes shut, grin), front only; its ONE branched cactus tail -- the
           still's own, cut from pixellab/base.png -- swings lazily, drawn by hand (a shear about its root) behind
           the tail-less drunk body (k-drunk-notail), the body swaying the other way
  phase 2  the DASH: k-run-notail (side, facing right; L mirrored) with the side view's saguaro tail (rot-east-02)
           standing up from its rump, raked back
  phase 2  the FRONT SLASH: key-slash2 (both forearm blades swept out, mouth open) with the still's tail behind it
PixelLab bodies, the tails pasted from the still / its rotate view, all snapped to the still's 8 colours + black.
Run: python -B art/enemies/anim/22_cactus_cat/build.py [--keys]"""
import os, sys, math
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common'))
import pixtools as pt
PL = os.path.join(HERE, 'pixellab')
P = pt.palette_of(os.path.join(HERE, 'original_sprite.png'))

def load(n): return pt.snap(Image.open(os.path.join(PL, n + '.png')), P)

def cut(im, keep):
    """The pixels of im where keep(x, y)."""
    out = Image.new('RGBA', im.size, pt.CLEAR); src, px = im.load(), out.load()
    for y in range(im.height):
        for x in range(im.width):
            if keep(x, y): px[x, y] = src[x, y]
    return out

def shear(im, root_y, top_y, dx):
    """Rows moved sideways in proportion to their height above root_y: dx px at top_y, none at the root."""
    out = Image.new('RGBA', im.size, pt.CLEAR)
    for y in range(im.height):
        s = round(dx * (root_y - y) / (root_y - top_y)) if y < root_y else 0
        out.paste(im.crop((0, y, im.width, y + 1)), (s, y))
    return out

def no_black_islands(im):
    """PixelLab's stray black -- the shadow blob under the wind-up's feet, the speed streaks off the flung blades:
    black px with no coloured px among their 8 neighbours go (twice); tidy() then closes the outline again."""
    for _ in range(2):
        src = im.copy().load(); px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                if src[x, y] != pt.BLACK: continue
                if not any(src[q][3] and src[q] != pt.BLACK for q in ((x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                           if 0 <= q[0] < im.width and 0 <= q[1] < im.height): px[x, y] = pt.CLEAR
    src = im.load(); col = [x for y in range(im.height) for x in range(im.width) if src[x, y][3] and src[x, y] != pt.BLACK]
    lo, hi = min(col) - 1, max(col) + 1                          # the streaks stick out past the blade tips
    for y in range(im.height):
        for x in list(range(0, lo)) + list(range(hi + 1, im.width)): src[x, y] = pt.CLEAR
    return im

def over(*layers):
    out = Image.new('RGBA', layers[0].size, pt.CLEAR)
    for l in layers: out.alpha_composite(l)
    return out

FRONT_TAIL = lambda: cut(load('base'), lambda x, y: x <= 23 and y <= 57)          # the still's branched tail
TAIL_ROOT, TAIL_TOP = 50, 14            # the tail's shear pivot and top row (the still's coords)
FEET, HEAD_TOP = 61, 13                 # the body's sway pivot and top row
SWAY = [round(6 * math.sin(2 * math.pi * i / 8)) for i in range(8)]   # tail top px: 0 4 6 4 0 -4 -6 -4
LEAN = [-round(1.5 * math.sin(2 * math.pi * i / 8)) for i in range(8)] # body top px, the other way
SLASH = ['sl-02', 'key-slash2', 'sl-03', 'sl-01']   # WIND-UP (blades drawn in), BLADES OUT (fire; held while
BLADES_OUT = 1                                        # dashing), back (flung flat), back (straightening) -> the idle
IDLE_MS = SLASH_MS = 260                              # the one speed for non-boss enemies (the user, 2026-11-18)

def layers():
    """(body, tail) pairs: the 8 drunk frames, then the 6 slash frames."""
    tail = FRONT_TAIL(); out = []
    body = load('k-drunk-notail')
    for s_, l_ in zip(SWAY, LEAN): out.append((shear(body, FEET, HEAD_TOP, l_), shear(tail, TAIL_ROOT, TAIL_TOP, s_)))
    for n in SLASH: out.append((no_black_islands(load(n)), tail))
    return out

def frames():
    fs = [pt.tidy(over(t, b)) for b, t in layers()]
    bs = [f.getbbox() for f in fs]; box = (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))
    W, H = box[2] - box[0], box[3] - box[1]; W += W % 2; H += H % 2
    box = (box[0], box[3] - H, box[0] + W, box[3])
    return [f.crop(box) for f in fs[:8]], [f.crop(box) for f in fs[8:]], box

def parts(box):
    """Per frame: the blade tips (the tail-less body's outermost px below the head), the tail tip (its top px)
    and the ear tips (the topmost px either side of the head's middle), in frame px."""
    res = []
    for b, t in layers():
        b, t = b.crop(box), t.crop(box); bp, tp = b.load(), t.load()
        body = [(x, y) for y in range(b.height) for x in range(b.width) if bp[x, y][3] and bp[x, y] != pt.BLACK]
        top = min(y for _, y in body); head = [p for p in body if p[1] < top + 14]; mid = sorted(x for x, _ in head)[len(head) // 2]
        ears = [min((p for p in head if (p[0] < mid) == left), key=lambda p: p[1]) for left in (True, False)]
        low = [p for p in body if p[1] > top + 22]
        blades = (min(low, key=lambda p: (p[0], -p[1])), max(low, key=lambda p: (p[0], p[1])))
        tl = [(x, y) for y in range(t.height) for x in range(t.width) if tp[x, y][3] and tp[x, y] != pt.BLACK]
        res.append({'blades': blades, 'tail': min(tl, key=lambda p: p[1]), 'ears': ears})
    return res

def gif(fs, ms, path):
    W, H = fs[0].size
    g = [Image.alpha_composite(Image.new('RGBA', (W, H), (24, 24, 32, 255)), f).convert('RGB').resize((W * 4, H * 4), Image.NEAREST) for f in fs]
    g[0].save(path, save_all=True, append_images=g[1:], duration=ms, loop=0, disposal=2)

if __name__ == '__main__':
    idle, slash, box = frames(); W, H = idle[0].size; gap = 4
    rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
    b = Image.new('RGBA', (8 * (W + gap) + gap, 2 * (H + gap) + gap), (24, 24, 32, 255))
    for r, fs in enumerate((idle, slash)):
        for i, f in enumerate(fs): b.alpha_composite(f, (gap + i * (W + gap), gap + r * (H + gap)))
    b.resize((b.width * 4, b.height * 4), Image.NEAREST).save(os.path.join(rv, 'board.png'))
    gif(idle, IDLE_MS, os.path.join(rv, 'drunk.gif')); gif(slash, SLASH_MS, os.path.join(rv, 'slash.gif'))
    off = lambda p: '(%+.0f,%+.0f)' % ((p[0] + .5 - W / 2) * 2, (p[1] + .5 - H / 2) * 2)
    print('frame %dx%d' % (W, H))
    for i, p in enumerate(parts(box)):
        print(('drunk %d' % i) if i < 8 else ('slash %d' % (i - 8)), 'blades L', off(p['blades'][0]), 'R', off(p['blades'][1]),
              '| tail tip', off(p['tail']), '| ears', off(p['ears'][0]), off(p['ears'][1]))
    t = os.path.join(rv, 'check.png'); pt.sheet({v: {'i': idle} for v in ('down', 'right', 'up')}, 'i', t, W, H, front_only=True)
    print('drunk', *pt.check_frames(t, 8, W, H, views=(('D', 0),)), sep=chr(10) + '  ')
    pt.sheet({v: {'i': slash} for v in ('down', 'right', 'up')}, 'i', t, W, H, front_only=True)
    print('slash', *pt.check_frames(t, len(SLASH), W, H, views=(('D', 0),)), sep=chr(10) + '  ')
    os.remove(t)
    if '--install' in sys.argv:
        d = os.path.join(ROOT, 'assets/enemies')
        pt.sheet({v: {'i': idle} for v in ('down', 'right', 'up')}, 'i', os.path.join(d, '22_cactus_cat.png'), W, H, front_only=True)
        pt.sheet({v: {'i': slash} for v in ('down', 'right', 'up')}, 'i', os.path.join(d, '22_cactus_cat_slash.png'), W, H, front_only=True)
