"""Makalala, the horn-plate version (the lore: its wingtips end in hard horny plates that strike together -- the
'noisemaker'). PixelLab; the user's picks 2026-11-18: feathered wings, a LOW strike (wings curl forward round the
body, the plated tips up beside its head -- p-low2-d.png, hand-edited by the user), flying flaps only.
  idle (5 x 260 ms, 4 views, L = R mirrored; the spray leaves on frame 2 every loop):
      0 rest  1 wings opening  2 THE STRIKE (the key)  3 wings out  4 nearly folded
      D: a_rest_d sd-02 a_strike_d sd-03 sd-01  (likewise R with sr-, U with su-)
      a_strike_* are the strike keys moved so their club sits on the rest's club, cropped with the rest
      (the R and U keys came back shifted); sd/sr/su = animate a_rest -> --last a_strike
  fly  (4 frames per 0.28 s wingbeat, side only, left mirrored): pw-00 up, 02 level, 03 down, 02 level -- from
      p-flykey (flykey with plated tips); each frame moved so the club stays put (the hover ring leaves it)
Colours: the still's 8 + black, and one horn brown from the game palette (118,76,32); the plates' light tone is
the beak's shade (193,138,57). 10 with black: the giant-palette rule (the manager, 2026-11-18).
Body centred: each view's frames are cut round its rest pose's middle, the fly's round frame 0's.
Run: python -B art/enemies/anim/75_makalala/plates/build.py [--install]"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ANIM = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(ANIM, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ANIM, '..', '_common'))
import pixtools as pt
HORN = (118, 76, 32, 255)
IDLE = {v: ['a_rest_' + v[0], 's%s-02' % v[0], 'a_strike_' + v[0], 's%s-03' % v[0], 's%s-01' % v[0]]
        for v in ('down', 'up')}
IDLE['right'] = ['a_rest_r', 'sr-02', 'a_strike_r', 'sr-03', 'sr-01']
# The side as the user hand-edits it: pixellab/side_strip.png, the five side frames (snapped) side by side, 74 px
# apart; when it exists it replaces them. (The edited-out-wing try, a_strike2_r / sr2, was rejected: "side still
# looks off".)
STRIP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pixellab', 'side_strip.png')
FLY = ['pw-00', 'pw-02', 'pw-03', 'pw-02']
IDLE_MS, FLY_MS, STRIKE = 260, 70, 2
PL = os.path.join(HERE, 'pixellab')

def ivory(p): return p[3] and p[0] > 200 and p[1] > 190 and p[2] > 150
def horn(p): return p[3] and p in (HORN, (193, 138, 57, 255))

def centroid(fr, test):
    px = fr.load(); pts = [(x, y) for y in range(fr.height) for x in range(fr.width) if test(px[x, y])]
    return (sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)) if pts else None

def frames():
    P = pt.palette_of(os.path.join(ANIM, 'original_sprite.png')) + [HORN]
    L = lambda n: pt.tidy(pt.snap(Image.open(os.path.join(PL, n + '.png')), P), keep=lambda q: q == HORN)
    raw = {v: [L(n) for n in ns] for v, ns in IDLE.items()}
    if os.path.exists(STRIP):
        st = Image.open(STRIP).convert('RGBA'); n = len(IDLE['right']); w = st.width // n
        raw['right'] = [st.crop((i * w, 0, (i + 1) * w, st.height)) for i in range(n)]
    fly = [L(n) for n in FLY]
    c0 = centroid(fly[0], ivory)
    fly = [pt.jolt(f, round(c0[0] - c[0]), round(c0[1] - c[1])) for f in fly for c in [centroid(f, ivory)]]
    mids = {}
    for v, fs in raw.items():
        b = fs[0].getbbox(); mids[v] = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    b = fly[0].getbbox(); fmid = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    def need(fs, m):
        bs = [f.getbbox() for f in fs]
        return (2 * max(max(m[0] - q[0], q[2] - m[0]) for q in bs), 2 * max(max(m[1] - q[1], q[3] - m[1]) for q in bs))
    sizes = [need(fs, mids[v]) for v, fs in raw.items()] + [need(fly, fmid)]
    W = int(max(s[0] for s in sizes)) + 2; H = int(max(s[1] for s in sizes)) + 2
    W += W % 2; H += H % 2
    def cut(fs, m):
        out = []
        for f in fs:
            c = Image.new('RGBA', (W, H), pt.CLEAR); c.paste(f, (round(W / 2 - m[0]), round(H / 2 - m[1])), f); out.append(c)
        return out
    return {v: cut(fs, mids[v]) for v, fs in raw.items()}, cut(fly, fmid), W, H

# Three angles (the user, 2026-11-18: "the front facing is the left facing pose, and it mirrored is the right pose",
# "no down"): the front art faces left; the side drawing (R, the user's side_strip) is kept but unused.
VIEW3 = {'D': ('down', False), 'DR': ('down', True), 'R': ('down', True), 'UR': ('up', False), 'U': ('up', False),
         'UL': ('up', False), 'L': ('down', False), 'DL': ('down', False)}

def sheet3(idle, path, W, H):
    n = len(idle['down']); im = Image.new('RGBA', (W * 8 * n, H))
    for d, dn in enumerate(['D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL']):
        v, flip = VIEW3[dn]
        for i, fr in enumerate(idle[v]): im.paste(pt.mirror(fr) if flip else fr, ((d * n + i) * W, 0))
    im.save(path)

def gif(fs, ms, path):
    W, H = fs[0].size
    g = [Image.alpha_composite(Image.new('RGBA', (W, H), (24, 24, 32, 255)), f).convert('RGB').resize((W * 4, H * 4), Image.NEAREST) for f in fs]
    g[0].save(path, save_all=True, append_images=g[1:], duration=ms, loop=0, disposal=2)

if __name__ == '__main__':
    idle, fly, W, H = frames(); gap = 4
    views = {'left (front)': idle['down'], 'right (front mirrored)': [pt.mirror(f) for f in idle['down']], 'up (back)': idle['up']}
    rows = list(views.values()) + [fly]
    board = Image.new('RGBA', (5 * (W + gap) + gap, 4 * (H + gap) + gap), (24, 24, 32, 255))
    for r, fs in enumerate(rows):
        for i, fr in enumerate(fs): board.paste(fr, (gap + i * (W + gap), gap + r * (H + gap)), fr)
    rv = os.path.join(HERE, 'review_v4'); os.makedirs(rv, exist_ok=True)
    board.resize((board.width * 4, board.height * 4), Image.NEAREST).save(os.path.join(rv, 'board.png'))
    for v, fs in views.items(): gif(fs, IDLE_MS, os.path.join(rv, 'idle_%s.gif' % v.split()[0]))
    gif(fly, FLY_MS, os.path.join(rv, 'fly.gif'))
    off = lambda c: '(%.1f, %.1f)' % ((c[0] + 0.5 - W / 2) * 2, (c[1] + 0.5 - H / 2) * 2) if c else 'none'
    print('frame %dx%d' % (W, H))
    for v, fs in views.items():
        f = fs[STRIKE]; half = W // 2; px = f.load()
        pts = [(x, y) for y in range(H) for x in range(W) if horn(px[x, y])]
        left = [p for p in pts if p[0] < half]; right = [p for p in pts if p[0] >= half]
        mean = lambda s: (sum(x for x, _ in s) / len(s), sum(y for _, y in s) / len(s)) if s else None
        print('strike plates', v, 'left', off(mean(left)), 'right', off(mean(right)), 'mid', off(mean(pts)))
        print('club', v, [off(centroid(fr, ivory)) for fr in fs])
    print('club fly', [off(centroid(f, ivory)) for f in fly])
    if '--install' in sys.argv:
        d = os.path.join(ROOT, 'assets/enemies/redraws')
        sheet3(idle, os.path.join(d, '75_makalala.png'), W, H)
        pt.sheet({v: {'flap': fly} for v in ('down', 'right', 'up')}, 'flap', os.path.join(d, '75_makalala_fly.png'), W, H)
        for n, k in (('75_makalala.png', 5), ('75_makalala_fly.png', 4)):
            print(n, *pt.check_frames(os.path.join(d, n), k, W, H, views=(('DL', 7), ('DR', 1), ('U', 4))), sep='\n  ')
