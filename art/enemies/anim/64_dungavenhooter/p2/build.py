"""64 Dungavenhooter phase 2: walks at the player, champing, slamming its tail mid-stride. One 4-frame cycle, 260 ms:
    f0 left step  / ball rising   / jaws open        f1 passing / ball at the top / jaws shut
    f2 right step / swinging down / jaws open        f3 passing / IMPACT, dust    / jaws shut
The body: PixelLab's walk ("walking", from the old-path D frame 0) and its jaw-open frames; the tail and ball: the
old-path sheet's own slam frames (f2 f4 f5 f6), the px where they differ from its frame 0, moved with the body's bob.
Both snapped to the old-path sheet's colours (plus a mouth red and white teeth), then oldpath/restyle.py's recolour.
Views D DR R get the jaws; UR U face away (the mouth out of sight: PixelLab drew it on the ball), walk only.
UL L DL are UR R DR mirrored, as in the idle sheet.
Run: python -B build.py [--install]   writes p2/64_dungavenhooter_walk.png (8 views x 4) + review/;
--install puts it in assets/enemies/redraws/ (backup, .aseprite packed at 260 ms, built.json)."""
import os, sys, glob, time
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, *['..'] * 5))
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, os.path.join(HERE, '..', 'oldpath'))
import enemy_sheet as es, enemy_style as st, restyle as rs
W, H = 98, 65
OLD = Image.open(os.path.join(ROOT, 'assets/enemies/64_dungavenhooter.png')).convert('RGBA')
MOUTH, TEETH = (183, 0, 0, 255), (220, 240, 255, 255)        # palette red; teeth share the ball's shine (no new colour)
rs.ACROSS[(183, 0, 0)] = MOUTH; rs.ACROSS[(248, 250, 247)] = TEETH
KEYS = list(rs.SCALES) + list(rs.ACROSS)
def G(pat):
    got = glob.glob(os.path.join(HERE, pat)); assert len(got) == 1, (pat, got); return got[0]
SLAM = [2, 4, 5, 6]          # the old-path frames whose tail each beat takes: rising, top, swinging down, IMPACT
# per view: the walk frames of the beat (left step + jaws open, passing, right step + jaws open, passing)
VIEWS = {'D':  [G('*k02-only-its-jaws*mouth/jawb1-02.png'), G('*d0-orig-walking/wk-04.png'),
                G('*k06-the-lizard-opens*/jaw-03.png'), G('*d0-orig-walking/wk-08.png')],
         'DR': [G('*dr02-only*/jaw-02.png'), G('*v1-orig-walking/wk1-04.png'), G('*dr06-only*/jaw-03.png'), G('*v1-orig-walking/wk1-08.png')],
         'R':  [G('*-r02-only*/jaw-03.png'), G('*v2-orig-the-heavy*-f/q2b-04.png'), G('*-r06-the-lizard*/jawr1-02.png'), G('*v2-orig-the-heavy*-f/q2b-08.png')],
         'UR': [G('*v3-orig-walking/wk3-0%d.png' % k) for k in (2, 4, 6, 8)],
         'U':  [G('*v4-orig-the-heavy*-f/q4b-0%d.png' % k) for k in (2, 4, 6, 8)]}
OUT = os.path.join(HERE, '64_dungavenhooter_walk.png')
GAME = os.path.join(ROOT, 'assets/enemies/redraws/64_dungavenhooter_walk.png')
IMPACT = 6                                             # the old-path frame of the club down
GREYS = {(164, 170, 186), (89, 89, 101)}

def snap(im):
    """Every drawn px to the nearest of the old-path colours (+ mouth, teeth); alpha to 0/255."""
    out = Image.new('RGBA', im.size, (0, 0, 0, 0)); p, o = im.load(), out.load()
    for y in range(im.height):
        for x in range(im.width):
            c = p[x, y]
            if c[3] < 128: continue
            if c[:3] not in KEYS and c[0] > 120 and c[0] - c[1] > 70 and c[0] - c[2] > 40: o[x, y] = MOUTH; continue   # the mouth's reds and pinks
            o[x, y] = min(KEYS, key=lambda k: sum((a - b) ** 2 for a, b in zip(k, c[:3]))) + (255,)
    return out

def top(im, x0=40):
    """The body's top row (right of the ball)."""
    p = im.load()
    return min(y for y in range(im.height) for x in range(x0, im.width) if p[x, y][3])

def unball(f):
    """Delete the walk frame's resting ball: its grey px and the black around them that touches no fill."""
    p = f.load(); grey = {(x, y) for y in range(H) for x in range(W) if p[x, y][3] and p[x, y][:3] in GREYS}
    fill = lambda x, y: 0 <= x < W and 0 <= y < H and p[x, y][3] and p[x, y][:3] != (0, 0, 0) and (x, y) not in grey
    ring = {(x + dx, y + dy) for x, y in grey for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    for q in grey: p[q] = (0, 0, 0, 0)
    for x, y in ring:
        if 0 <= x < W and 0 <= y < H and p[x, y][:3] == (0, 0, 0) and p[x, y][3] and \
                not any(fill(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): p[x, y] = (0, 0, 0, 0)

def cell(j, i): return OLD.crop(((j * 8 + i) * W, 0, (j * 8 + i + 1) * W, H))

def tail(j, i):
    """The old-path frame i's tail, ball (and dust): its px that differ from frame 0, left of the head; and the px
    frame 0 had there that frame i cleared (the resting ball's place)."""
    a, b = cell(j, 0).load(), cell(j, i).load()
    steel = lambda x, y: 0 <= x < W and 0 <= y < H and b[x, y][3] and b[x, y][:3] in GREYS
    ball = lambda x, y: steel(x, y) or (b[x, y][:3] == (0, 0, 0) and any(steel(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)))
    put = {(x, y): b[x, y] for y in range(H) for x in range(W) if x < 46 and b[x, y][3] and (b[x, y] != a[x, y] or ball(x, y))}
    clear = {(x, y) for y in range(H) for x in range(W) if x < 46 and a[x, y][3] and not b[x, y][3]}
    return put, clear

def despeck(f):
    """Delete every px not in the drawing's largest piece (PixelLab's stray specks)."""
    p = f.load(); on = [(x, y) for y in range(H) for x in range(W) if p[x, y][3]]
    keep = max(rs.blobs_of(on), key=len)
    for q in set(on) - set(keep): p[q] = (0, 0, 0, 0)

def frame(walk, i, view):
    j = es.ORDER.index(view)
    f = snap(Image.open(walk).convert('RGBA')); despeck(f); unball(f)
    dy = top(f) - top(cell(j, 0))                     # the step's bob
    if i == IMPACT: dy = 0                             # the ball and the dust lie on the floor, not on the body
    put, clear = tail(j, i); p = f.load()
    for (x, y) in clear:
        if 0 <= y + dy < H and p[x, y + dy][:3] in GREYS: p[x, y + dy] = (0, 0, 0, 0)
    for (x, y), c in put.items():
        if 0 <= y + dy < H: p[x, y + dy] = c
    on = [(x, y) for y in range(H) for x in range(W) if p[x, y][3]]
    for c in rs.blobs_of(on):                          # crumbs the paste left loose (the dust's clumps are bigger)
        if len(c) < 6:
            for q in c: p[q] = (0, 0, 0, 0)
    f = rs.restyle(f, view); unlone(f)
    return f, dy

def unlone(f):
    """Delete black on the drawing's edge with no colour in its 8 neighbours (PixelLab's black-only scraps, shadows under
    the feet): invisible on the black arena anyway. Repeated, since each pass bares the next."""
    p = f.load(); on = lambda x, y: 0 <= x < W and 0 <= y < H and p[x, y][3]
    while True:
        gone = [(x, y) for y in range(H) for x in range(W) if p[x, y] == rs.BLACK
                and any(not on(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                and not any(on(x + dx, y + dy) and p[x + dx, y + dy] != rs.BLACK for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
        if not gone: return
        for q in gone: p[q] = (0, 0, 0, 0)

def gif(frames, path, z=2):
    big = []
    for f in frames:
        bg = Image.new('RGBA', f.size, (0, 0, 0, 255)); bg.alpha_composite(f); big.append(bg.convert('RGB').resize((f.width * z, f.height * z), 0))
    big[0].save(path, save_all=True, append_images=big[1:], duration=260, loop=0, disposal=1, optimize=False)
    g = Image.open(path)
    for k in range(len(frames)):
        g.seek(k); g.load(); assert g.convert('RGB').tobytes() == big[k].tobytes(), f'gif frame {k} does not read back'

def ball_at(f):
    """The ball's centre: its round core (the steel opened by 2 px, as restyle.ball finds it), left of the head."""
    from PIL import ImageFilter
    p = f.load(); g = [(x, y) for y in range(H) for x in range(50 if True else W) if p[x, y] in (rs.STEEL, rs.STEEL_DARK, rs.SHINE)]
    m = Image.new('L', f.size, 0)
    for q in g: m.putpixel(q, 255)
    o = m.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
    c = [q for q in g if o.getpixel(q)] or g
    return round(sum(x for x, _ in c) / len(c), 1), round(sum(y for _, y in c) / len(c), 1)

def splash_at(f):
    """The dust burst's centre: its cream px off the body (left of the body's cream belly)."""
    p = f.load(); d = [(x, y) for y in range(H) for x in range(46) if p[x, y] == rs.CREAM and y > 50]
    return round(sum(x for x, _ in d) / len(d), 1), round(sum(y for _, y in d) / len(d), 1)

def board(path, rows, z):
    sheet = Image.new('RGBA', (W * 4 * z, H * len(rows) * z), (0, 0, 0, 255))
    for r, fr in enumerate(rows):
        for k, f in enumerate(fr):
            bg = Image.new('RGBA', f.size, (0, 0, 0, 255)); bg.alpha_composite(f)
            sheet.paste(bg.resize((W * z, H * z), 0), (k * W * z, r * H * z))
    sheet.save(path)

if __name__ == '__main__':
    done = {}
    for view, walks in VIEWS.items():
        done[view] = []
        for walk, i in zip(walks, SLAM):
            f, dy = frame(walk, i, view); done[view].append(f)
            (_, bad), nes = st.check(f), st.check_nes(f)
            assert not bad and not nes, (view, os.path.basename(walk), bad, nes)
            print(view, os.path.basename(walk), 'tail f%d' % i, 'bob', dy, 'checker clean')
    for m, s_ in (('UL', 'UR'), ('L', 'R'), ('DL', 'DR')): done[m] = [x.transpose(Image.FLIP_LEFT_RIGHT) for x in done[s_]]
    sheet = Image.new('RGBA', (W * 4 * 8, H), (0, 0, 0, 0))
    for d, view in enumerate(es.ORDER):
        for k, f in enumerate(done[view]): sheet.paste(f, ((d * 4 + k) * W, 0))
    sheet.save(OUT)
    rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
    board(os.path.join(rv, 'all_views.png'), [done[v] for v in es.ORDER], 2)
    gif(done['D'], os.path.join(rv, 'D_walk_260.gif')); gif(done['R'], os.path.join(rv, 'R_walk_260.gif'))
    MIRROR = {'UL': 'UR', 'L': 'R', 'DL': 'DR'}
    for view in es.ORDER:      # a mirror's points: its source's, x flipped (x -> W - 1 - x)
        fr = done[MIRROR.get(view, view)]; fx = (lambda q: (round(W - 1 - q[0], 1), q[1])) if view in MIRROR else (lambda q: q)
        print(view, 'splash f3', fx(splash_at(fr[3])), 'ball f0-f3', [fx(ball_at(f)) for f in fr])
    print('wrote', OUT, 'review/all_views.png D_walk_260.gif R_walk_260.gif')
    if '--install' in sys.argv:
        bk = os.path.join(ROOT, 'art/_backup', '64_walk_' + time.strftime('%Y%m%d_%H%M%S'))
        print('installed', es.install(sheet, GAME, 4, ms=260, backup=bk), GAME, 'backup', bk)
