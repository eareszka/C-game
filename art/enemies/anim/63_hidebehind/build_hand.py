"""Hidebehind's idle (the user, 2026-11-18: the NEW 49x46 still, animated -- the claw fans flexing open and shut,
loop {0,1,0,2} at 260 ms). By hand from the still's own pixels and colours:
  f0 the still (fans open)   f2 THE KEY: both fans shut (each hand's three claws curled over onto its knuckles)
  f1 the in-between (not built until the key is approved)
Only the fingers above the knuckle row (rows 0-8, each hand's box) are redrawn; the outer hooked thumb claw, the
arms and the body are the still's. The right hand is the left's drawing mirrored (x -> 49 - x).
Run: python -B art/enemies/anim/63_hidebehind/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', '_common')); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import pixtools as pt
import enemy_sheet as es
MS, W, H = 260, 49, 46
SHEET = os.path.join(ROOT, 'assets/enemies/redraws/63_hidebehind.png')
CREAM = (232, 224, 192, 255)
KNUCKLE = 9                          # the knuckle row (cream / tan), kept; the fingers are above it
LEFT, RIGHT = (0, 0, 17, KNUCKLE), (32, 0, W, KNUCKLE)   # each hand's finger box
ROOTS = (3, 7, 11)                   # the left hand's three claw roots (x), on its knuckles
TOPS = (5, 4, 5)                     # their turns' rows: the middle claw a little higher (still a fan)

def still(): return es.cells_of(Image.open(SHEET).convert('RGBA'), 3, False)['D'][0]

def shut_claw(a, top, tip=2):
    """A claw curled shut, rooted at x a: its stem up to `top`, a rounded turn, the tip hanging 2 px down on the
    right (inward). {(x, y): colour} in the left hand's coords."""
    px = {(a + 1, top - 1): pt.BLACK, (a, top): pt.BLACK, (a + 2, top): pt.BLACK, (a + 1, top): CREAM}
    for y in range(top + 1, KNUCKLE):
        px[(a - 1, y)] = px[(a + 1, y)] = pt.BLACK; px[(a, y)] = CREAM
    for y in range(top + 1, top + 1 + tip): px[(a + 2, y)] = CREAM; px[(a + 3, y)] = pt.BLACK
    px[(a + 2, top + 1 + tip)] = pt.BLACK
    return px

def hands(claws):
    """The still with both hands' fingers replaced by `claws` ({(x, y): colour} drawn for the left hand)."""
    f = still(); f.paste(pt.CLEAR, LEFT); f.paste(pt.CLEAR, RIGHT); px = f.load()
    for (x, y), c in claws.items():
        px[x, y] = c; px[W - x, y] = c    # mirrored: x -> 49 - x (the knuckles x 3-10 <-> 39-46)
    return f

def key():
    c = {}
    for a, t in zip(ROOTS, TOPS): c.update(shut_claw(a, t))
    return hands(c)

def half():
    """f1: the claws half-curled -- standing 2 px taller than shut, the tips only just turned (1 px)."""
    c = {}
    for a, t in zip(ROOTS, TOPS): c.update(shut_claw(a, t - 2, 1))
    return hands(c)

CUT = 19                             # the arms' plain shaft row (below the hands and thumb claws, above the shoulders)
LIFT = (0, 1, 2)                     # the hands and forearms rise as the claws close (the user, 2026-11-18)
BREATH = (None, 36, 28)              # the coat swells 1 px each side from this row down (f1 the hem, f2 the lower half)
QL, QR = 17, 31                      # the coat's quarter columns, doubled to swell it

def arm(x, y):
    """In the moving block: the hands (finger boxes) and forearms down to CUT, either side of the body."""
    return (y < KNUCKLE and (x < LEFT[2] or x >= RIGHT[0])) or (KNUCKLE <= y <= CUT and (x <= 12 or x >= 36))

def lifted(f, dy):
    """The hands and forearms dy px up, the shaft stretched by repeating row CUT."""
    if not dy: return f
    src, out = f.load(), f.copy(); px = out.load()
    for y in range(CUT + 1):
        for x in range(W):
            if arm(x, y): px[x, y] = pt.CLEAR
    for y in range(CUT + 1):
        for x in range(W):
            if arm(x, y) and y - dy >= 0 and src[x, y][3]: px[x, y - dy] = src[x, y]
    for y in range(CUT - dy + 1, CUT + 1):
        for x in range(W):
            if arm(x, y) and src[x, CUT][3]: px[x, y] = src[x, CUT]
    return out

def breathed(f, top):
    """Rows top.. widened 1 px each side: the coat's left quarter column (QL) and right one (QR) doubled, the
    flanks pushed out -- the coat swelling."""
    if top is None: return f
    out = f.copy(); src, px = f.load(), out.load()
    for y in range(top, H):
        for x in range(1, QL + 1): px[x - 1, y] = src[x, y]
        for x in range(QR, W - 1): px[x + 1, y] = src[x, y]
    return out

EYES = ((22, 15), (26, 15))          # its two 1 px cream eyes, in the black slit under the hood
LIDS = (None, (178, 158, 92, 255), (88, 53, 24, 255))   # f1 dimmed (its knuckle tan: half-lidded), f2 the hood's fur (shut)
                                                           # (the user, 2026-11-18: the fur breathing and the eyes closing)

def lidded(f, c):
    if c is None: return f
    out = f.copy(); px = out.load()
    for e in EYES: px[e] = c
    return out

def frames(): return [lidded(breathed(lifted(f, d), b), e) for f, d, b, e in zip([still(), half(), key()], LIFT, BREATH, LIDS)]

def fan(i): return (7.5, 6 - LIFT[i]), (41.5, 6 - LIFT[i])

def full_sheet(fs):
    """D DR R UR U the drawing, UL L DL its mirror."""
    sh = Image.new('RGBA', (8 * len(fs) * W, H), pt.CLEAR)
    for d in range(8):
        for i, f in enumerate(fs): sh.paste(f.transpose(Image.FLIP_LEFT_RIGHT) if d in (5, 6, 7) else f, ((d * len(fs) + i) * W, 0))
    return sh

def gif(fs, path, s=6, box=None):
    """Full frames (no delta optimizing, disposal 1), checked to read back differing where the frames differ."""
    box = box or (0, 0, W, H); w, h = box[2] - box[0], box[3] - box[1]
    g = [Image.alpha_composite(Image.new('RGBA', (W, H), (24, 24, 32, 255)), f).crop(box).convert('RGB').resize((w * s, h * s), Image.NEAREST) for f in fs]
    g[0].save(path, save_all=True, append_images=g[1:], duration=MS, loop=0, disposal=1, optimize=False)
    from PIL import ImageSequence, ImageChops
    back = [f.convert('RGB') for f in ImageSequence.Iterator(Image.open(path))]
    assert [ImageChops.difference(back[0], f).getbbox() is None for f in back] == [ImageChops.difference(g[0], f).getbbox() is None for f in g], path

def board(fs, path, s=6, gap=4):
    b = Image.new('RGBA', (len(fs) * (W + gap) + gap, H + 2 * gap), (24, 24, 32, 255))
    for i, f in enumerate(fs): b.alpha_composite(f, (gap + i * (W + gap), gap))
    b.resize((b.width * s, b.height * s), Image.NEAREST).save(path)

def tips(f):
    """The topmost cream px of each hand (the claw tips) and the hands' outer thumb-claw tips (lowest cream px x<6 / x>42)."""
    p = f.load(); cream = [(x, y) for y in range(H) for x in range(W) if p[x, y] == CREAM]
    l = [q for q in cream if q[0] < 16 and q[1] < KNUCKLE + 1]; r = [q for q in cream if q[0] > 33 and q[1] < KNUCKLE + 1]
    return min(l, key=lambda q: q[1]), min(r, key=lambda q: q[1])

if __name__ == '__main__':
    rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
    fs = frames(); board(fs, os.path.join(rv, 'board.png')); L = [fs[i] for i in (0, 1, 0, 2)]; gif(L, os.path.join(rv, 'idle_260.gif')); gif(L, os.path.join(rv, 'claws_closeup_260.gif'), 12, (0, 0, W, 20))   # the claws and the face
    t = os.path.join(rv, 'check.png'); full_sheet(fs).save(t)
    print(*pt.check_frames(t, 3, W, H, views=(('D', 0),)), sep=chr(10)); os.remove(t)
    off = lambda p: '(%+.0f,%+.0f)' % ((p[0] + .5 - W / 2) * 2, (p[1] + .5 - H / 2) * 2)
    for i, f in enumerate(fs): print('f%d' % i, 'claw tips L R', *map(off, tips(f)), 'art', *tips(f), '| fan centre L R', *map(off, fan(i)), 'art', *fan(i))
    if '--install' in sys.argv:
        sh = full_sheet(fs); sh.save(SHEET)
        es.pack(sh, SHEET[:-4] + '.aseprite', 3, False); es.built(SHEET); os.utime(SHEET, None)
