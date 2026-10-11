"""57 Dingbat, big tier (the size of the sprite it replaces: its body about 36 px
tall), to art/direction/SPRITE_STYLE.md: one view, 3/4 front.

    python art/enemies/57_dingbat_design.py     # writes the .json and .txt of the three sheets, draft.png

The user, 2026-10-10, over four drafts: front facing, always at a 3/4 angle, less
blocky, wings more organic, the block covering its whole body and face; a draft
flying level was too far from the old sprite -- "have it be similar to the
original but better blocking, and better palette and follow bible rules". So:
the original's upright antlered owl, turned 3/4 to its left (our right; the left
views mirror it), talons tucked short under it, in owl buff and cream.

Three sheets, laid out and timed exactly as before (the fight fires on their
frames and is not the art session's to change):
  57_dingbat        5 frames, flying (it is moving): wings up / level / DOWN (frame 2, the downstroke) / down / level,
                    its mouth open / shut / open / shut / half
  57_dingbat_catch  5 frames, blocking: both wings wrapped across in front, hiding its body and face
  57_dingbat_stare  4 frames, the stare: wings flung up, then lowered as its eyes flare (frames 1-2), and back

The bible: one outline round the silhouette and between parts; three tones of
one feather ramp placed by form, plus cream for the face and chest; flat fills,
no feather texture (the wings' scalloped edge and a line between feathers say
feathers); 8 colours plus black; eyes a black pupil in a white (lit yellow only
for the stare); the head a good third of the height.

The body is the one the user redrew by hand in Aseprite on frame 0 of the stare
sheet (branching antlers, a cream face with cross-shaped eyes and a fanged open
mouth, grey legs hanging), taken pixel for pixel into BODY below and used for
every frame of all three sheets. A
wing is an arm bowed from shoulder to wrist to tip with a row of round-ended
feathers hung from it -- short by the body, long fingers at the tip. No line
across a wing's root: it grows out of the shoulder.

Then drawn into the .aseprite through the pixel plugin by tools/draw_views.py."""
import json, io, math
PAL = {'K': '000000', 'D': '633e1b', 'M': '967448', 'L': 'd0c078', 'C': 'e8e0c0', 'g': '474751', 'G': '848694', 'W': 'fcfcfc', 'Y': 'f0bc3c'}
W, H = 98, 65

BODY = [r.ljust(22, '.') for r in """
.....KK......KK
.KK.KCCK.KK.KCCK
KCCK.KKCKCCK.KKCK
.KKCK.KCKKKCK.KCK
..KKCKCK..KKCKCK
.KCKKCK..KCKKCK
..KCCCK...KCCCK
...KKCK....KKCK
....KKKKKKKKKKK
...KKMMMLLLLLLLK
..KMMMLLCCCCCCCLK
..KMMLCCCCCCCCCCKK
.KMMMLCCCCCCCCCCCK
.KMMMLCCCKCCCCKCCK
.KMMMLCCKKKCCKKKCK
KMMMMLCCCKCGGCKCCK
KMMMMMLCCCWKKWCCC
KMMMMMLCKWKKKKWKK
KMMMMMLCCKKKKKKCK
.KMMMMMLCCKWKWCCK
.KDMMMMMMLCCCCCK
..KKMMMMMMLLLLK
..KMMMMMMLCCCCCK
.KMMMMMMLCCCCCCCK
.KMMMMMMLCCCCCCCK
KMMMMMMMLCCCCCCCCK
KMMMMMMMLCCCCCCCCK
KMMMMMMMLLCCCCCCCK
KMMMMMMMMLCCCCCCCK
KMMMMMMMMLCCCCCCCK
KMMMMMMMMLLCCCCCCK
KDMMMMMMMMLCCCCCCK
KDMMMMMMMMLLCCCCK
.KDMMMMMMMMLLCCCK
.KDDMMMMMMMMLLLK
..KDDDMMMMMMMMK
...KKDDDDDDDKK
...KKGGK.KGGK
.KKGGGKKKGGKK
KGGGGKKGGGGK
.KKGK..KKGK
...K.....K
""".split()]
X0, Y0 = 44, 6
NEAR, FAR = (X0 + 2, Y0 + 25), (X0 + 15, Y0 + 25)         # where each wing leaves the shoulder
EYES = [(X0 + 9, Y0 + 14), (X0 + 14, Y0 + 14)]            # the middle of each cross-shaped eye

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
def rim(shape): return {(x + dx, y + dy) for (x, y) in shape for dx, dy in N4} - shape

def stroke(a, b, r):
    """A round-ended bar from a to b, r px thick each side."""
    (x0, y0), (x1, y1) = a, b; n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) or 1; k = int(r + 1); out = set()
    for i in range(n + 1):
        cx, cy = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
        out |= {(round(cx) + dx, round(cy) + dy) for dx in range(-k, k + 1) for dy in range(-k, k + 1) if dx * dx + dy * dy <= r * r}
    return out

def feathered(p0, p1, p2, hang, n=8, lo=7.0, hi=15.0):
    """Feathers hung from an arm bowed p0 -> p1 -> p2. `hang(t)` is the unit way a feather at t along the
    arm points; they run from `lo` px long at the root to `hi` at the tip. Returns (pixels, arm, quills)."""
    B = lambda t: ((1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * p1[1] + t * t * p2[1])
    arm = set()
    for i in range(24): arm |= stroke(B(i / 24), B((i + 1) / 24), 1.5)
    shape, tips = set(arm), []
    for i in range(n):
        t = (i + 0.5) / n; bx, by = B(t); hx, hy = hang(t); ln = lo + (hi - lo) * t ** 0.8
        tip = (bx + hx * ln, by + hy * ln)
        shape |= stroke((bx, by), tip, 2.3); tips.append(((bx, by), tip))
    quills = set()
    for (b0, t0), (b1, t1) in zip(tips, tips[1:]):        # a line up between each feather and the next, over its outer part
        m0 = ((b0[0] + b1[0]) / 2, (b0[1] + b1[1]) / 2); m1 = ((t0[0] + t1[0]) / 2, (t0[1] + t1[1]) / 2)
        quills |= stroke((m0[0] + (m1[0] - m0[0]) * 0.35, m0[1] + (m1[1] - m0[1]) * 0.35), (m0[0] + (m1[0] - m0[0]) * 0.92, m0[1] + (m1[1] - m0[1]) * 0.92), 0.0) & shape
    return shape, arm & shape, quills

def wing(root, way, deg, length, lo=8.0, hi=16.0):
    """A wing out to the left (way -1) or right (+1) along `deg` (0 = level, negative = up): the wrist
    bowed up above the straight line, the feathers hanging down, fanning to fingers at the tip."""
    sx, sy = root; a = math.radians(deg)
    tip = (sx + way * math.cos(a) * length, sy + math.sin(a) * length)
    mid = (sx + way * math.cos(a) * length * 0.5, sy + math.sin(a) * length * 0.5 - 6)
    def hang(t):                                           # straight down by the body, swinging out along the wing at the tip
        w = t ** 1.6 * 0.85
        x = way * 0.2 * (1 - w) + way * math.cos(a) * w; y = (1 - w) + (math.sin(a) + 0.35) * w
        n = math.hypot(x, y) or 1.0
        return x / n, y / n
    return feathered((sx, sy), mid, tip, hang, lo=lo, hi=hi)

def put_wing(g, body, parts, far=False, over=False):
    """Paint a wing: behind the body (its root lost under it: no line across it), or over it (the block).
    The far one a tone darker."""
    shape, arm, quills = parts
    lit, mid, dark = ('M', 'D', 'D') if far else ('L', 'M', 'D')
    for p in rim(shape):
        if p in body and not over: continue
        g[p] = 'K'
    for p in shape:
        if p in body and not over: continue
        g[p] = lit if p in arm else 'K' if p in quills else mid
    for (x, y) in shape:                                  # the underside of each feather tip
        if g.get((x, y)) == mid and (x, y + 1) not in shape and (over or (x, y) not in body): g[(x, y)] = dark

# Its mouth, for when it moves (the user: "have mouth open and close when moving"): BODY has it wide
# open; these rows of BODY drawn over it shut it part way, or all the way.
HALF = {16: 'KMMMMMLCCCCCCCCCC'}                         # its top lip down a row; the lower fangs still bare
SHUT = {16: 'KMMMMMLCCCCCCCCCC', 17: 'KMMMMMLCCKCKCKCCK', 18: 'KMMMMMLCCCKCKCKCK', 19: '.KMMMMMLCCCCCCCCK'}   # shut: fangs meshed in a zig-zag, never a straight line (the user)

def body_at(dy, mouth=None):
    rows = [(mouth or {}).get(i, r) for i, r in enumerate(BODY)]
    return {(X0 + x, Y0 + y + dy): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}

def frame(deg, length=30, flare=0, dy=0, mouth=None):
    """Flying or staring: both wings out at `deg`. flare: its eyes lit (1) and wide (2). dy: the body lower."""
    body = body_at(dy, mouth); g = {}
    off = lambda p: (p[0], p[1] + dy)
    put_wing(g, body, wing(off(FAR), 1, deg * 0.8 - 10, length * 0.66, 6, 12), far=True)
    put_wing(g, body, wing(off(NEAR), -1, deg, length))
    g.update(body)
    for ex, ey in (EYES if flare else ()):                # the stare: its cross eyes light (1), then blaze into squares (2)
        for dx in (-1, 0, 1):
            for dy2 in (-1, 0, 1):
                if flare == 2 or dx == 0 or dy2 == 0: g[(ex + dx, ey + dy2 + dy)] = 'Y'
    return g

def block(k):
    """Blocking: both wings wrapped across in front of it -- the far one low across its belly, the near
    one over that, from its shoulder up over its head and down the other side -- a curtain of long
    feathers hiding its whole body and face. Only its antlers show above and its talons below.
    k: 0-2, how far the wings have shifted (it breathes)."""
    body = body_at(0); g = dict(body)
    x, y = X0, Y0
    down = lambda t: (math.sin((t - 0.5) * 0.4), math.cos((t - 0.5) * 0.4))
    put_wing(g, body, feathered((x + 20, y + 23), (x + 12, y + 24 + k), (x + 1, y + 28), down, n=6, lo=9.0, hi=8.0), far=True, over=True)
    put_wing(g, body, feathered((x - 2, y + 26), (x + 4, y + 6 - k), (x + 20, y + 15), down, n=8, lo=11.0, hi=15.0 + k), over=True)
    return g

FLY = [frame(-40), frame(-14, mouth=SHUT), frame(30, dy=-1), frame(24, mouth=SHUT), frame(-6, mouth=HALF)]   # open, shut, open (the downstroke), shut, half
CATCH = [block(k) for k in (0, 1, 2, 1, 0)]
STARE = [frame(-40, 29), frame(30, 28, flare=1), frame(24, 30, flare=2), frame(-20)]
# The four pixels the user changed where the far wing meets the head on the frame they drew over
# (stare frame 0; design rows are one above the built sheet's): no stub of outline there.
STARE[0].pop((62, 21)); STARE[0].update({(61, 22): 'D', (62, 23): 'M', (61, 24): 'M'})
SHEETS = {'57_dingbat': FLY, '57_dingbat_catch': CATCH, '57_dingbat_stare': STARE}
rows = lambda g: [''.join(g.get((x, y), '.') for x in range(W)) for y in range(H)]

if __name__ == '__main__':
    from PIL import Image
    for name, fr in SHEETS.items():
        json.dump({'pal': PAL, 'view_w': W, 'views': {str(i): rows(g) for i, g in enumerate(fr)}, 'order': [str(i) for i in range(len(fr))]}, open(name + '.json', 'w'))
        head = ['#BODY', '30', '#POSE', 'frames', '#DIRS', 'quarter']
        t = ['#PAL'] + [f'{k} {v}' for k, v in PAL.items()] + head
        for i, g in enumerate(fr): t += ['#DR' + (f'@{i}' if i else '')] + rows(g)[:-1]
        io.open(name + '.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(t) + '\n')
    im = Image.new('RGBA', (W * 5, H * 3), (0, 0, 0, 255))
    for r, fr in enumerate(SHEETS.values()):
        for i, g in enumerate(fr):
            for (x, y), c in g.items():
                if 0 <= x < W and 0 <= y < H: im.putpixel((i * W + x, r * H + y), tuple(int(PAL[c][j:j + 2], 16) for j in (0, 2, 4)) + (255,))
    im.resize((im.width * 3, im.height * 3), Image.NEAREST).save('draft.png')
    allg = [g for fr in SHEETS.values() for g in fr]
    out = {(x, y) for g in allg for x, y in g if not (0 <= x < W and 0 <= y < H - 1)}
    assert not out, f'drawn outside the frame: {sorted(out)[:8]}'
    b = body_at(0); edge = {p for p in b if any((p[0] + dx, p[1] + dy) not in b for dx, dy in N4)}
    print('body', len(BODY), 'tall | head share %.0f%%' % (100 * 12 / (len(BODY) - 6)), '| interior black %.0f%%' % (100 * sum(1 for p, c in b.items() if c == 'K' and p not in edge) / len(b)),
          '| colours', len({c for g in allg for c in g.values()}) - 1, '+ K')
