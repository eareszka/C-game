"""56 Moskitto, big tier, to art/direction/SPRITE_STYLE.md: front-facing only.

    python art/enemies/56_moskitto_design.py        # writes 56_idle.json, 56_grab.json, 56_moskitto.txt, draft.png

Two sheets, both seen from the front (the user, 2026-10-10: no 8 directions):
the idle -- flying, a 5-frame wingbeat, the needle thrust furthest on frame 4
(the fight fires on frames 0 and 4) -- and the grab of phase 2 -- 4 frames,
the legs snapping open and shut.

Paul Bunyan's moskitto crossed with a fighting bumblebee: a round thorax, a
dark head that is mostly two red eyes, a banded abdomen hanging behind, a
long pale needle straight down at us, thin hooked amber legs (neither black:
they must show on the battle's black background), and two long glassy wings
that grow out of the thorax (no line across the root) with a vein down each.

Drafted as shapes (silhouette, then outline, then tones by form), then drawn
into the .aseprite through the pixel plugin by tools/draw_views.py."""
import json, io, math
from PIL import Image, ImageDraw
PAL = {'K': '000000', 'G': '292931', 'D': 'c9a433', 'M': 'f0bc3c', 'L': 'fae488', 'R': 'b6433d', 'B': '84a7e9', 'b': 'c6ccda'}
W, H = 98, 65
MIR = lambda p: (W - 1 - p[0], p[1])

def mask(draw_fn):
    im = Image.new('1', (W, H), 0); draw_fn(ImageDraw.Draw(im)); px = im.load()
    return {(x, y) for y in range(H) for x in range(W) if px[x, y]}

def both(s): return s | {MIR(p) for p in s}

def line(a, b):
    (x0, y0), (x1, y1) = a, b; n = max(abs(round(x1 - x0)), abs(round(y1 - y0))) or 1
    return [(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)]

def edge(shape, within=None):
    within = within or shape
    return {(x, y) for (x, y) in shape if any((x + dx, y + dy) not in within for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}

LEAF = ((0, 1.6), (0.2, 3.8), (0.5, 5.8), (0.8, 5.4), (0.93, 3.4), (1, 0.8))
def wing(root, deg, length):
    """A long leaf from `root` along `deg` (90 = up, 180 = left): its pixels, and its midline."""
    a = math.radians(deg); ux, uy = math.cos(a), -math.sin(a); vx, vy = -uy, ux
    side = lambda s: [(root[0] + ux * t * length + vx * s * w, root[1] + uy * t * length + vy * s * w) for t, w in LEAF]
    return (mask(lambda d: d.polygon(side(1) + side(-1)[::-1], fill=1)),
            set(line((root[0] + ux * 4, root[1] + uy * 4), (root[0] + ux * length * 0.82, root[1] + uy * length * 0.82))))

def front(wing_deg, dy=0, thrust=0, legs_open=0.0, grab=False):
    """The front view: the left wing at wing_deg (the right mirrors it), the body dy px lower, the
    needle thrust px longer, the legs tucked (0) to flung wide (1); grab = the long hooked legs."""
    o = lambda x, y: (x, y + dy)
    thorax = mask(lambda d: d.ellipse(o(40, 19) + o(57, 36), fill=1))
    head = mask(lambda d: d.ellipse(o(41, 29) + o(56, 41), fill=1))
    eye = both(mask(lambda d: d.ellipse(o(41, 29) + o(47, 38), fill=1)))
    abdomen = mask(lambda d: d.ellipse(o(42, 34) + o(55, 49), fill=1))
    needle = {(x, y) for x in (48, 49) for y in range(40 + dy, 55 + dy + thrust)} | {(48, 55 + dy + thrust)}
    k = legs_open
    if grab:                                          # long, reaching down and out, hooked in at the tip
        paths = [(o(42, 33), o(34 - 8 * k, 38 - 2 * k), o(33 - 9 * k, 50 + 2 * k), o(37 - 7 * k, 54 + 2 * k)),
                 (o(43, 37), o(38 - 5 * k, 44), o(39 - 6 * k, 55), o(43 - 5 * k, 58))]
    else:                                             # tucked under
        paths = [(o(42, 33), o(36, 38), o(37, 45), o(40, 46)), (o(43, 37), o(40, 42), o(41, 50), o(44, 51))]
    legs = set()
    for pts in paths:
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            seg = set(line(a, b)); legs |= seg
            if grab and i < 2: legs |= {(x + 1, y) for x, y in seg}        # the grabbing legs: thick, tapering to the hook
    legs = both(legs)
    wl, mid = wing(o(44, 23), wing_deg, 36)
    wings, mids = both(wl), both(mid)
    yellow = abdomen | thorax
    body = yellow | head
    whole = body | needle | legs | wings
    g = {}
    for p in wings: g[p] = 'b'
    for (x, y) in wings:                              # glass, a tone darker along the trailing (lower) edge
        if any((x, y + j) not in wings for j in (1, 2)): g[(x, y)] = 'B'
    for p in mids & wings: g[p] = 'B'                 # a vein down each
    for p in edge(wings): g[p] = 'K'
    for p in legs: g[p] = 'D'                         # amber, not black: the battle's background is black (the user)
    for p in abdomen: g[p] = 'M'
    for (x, y) in abdomen:                            # round: dark down both sides
        if any((x + s * j, y) not in abdomen for s in (-1, 1) for j in (1, 2)): g[(x, y)] = 'D'
    for by in (41, 45):                               # two dark bands round it
        for p in abdomen:
            if by + dy <= p[1] <= by + dy + 1: g[p] = 'G'
    for p in edge(abdomen): g[p] = 'K'
    for p in thorax: g[p] = 'M'
    for (x, y) in thorax:                             # lit on top, dark underneath
        if any((x, y - j) not in thorax for j in (1, 2, 3)): g[(x, y)] = 'L'
    for p in edge(thorax): g[p] = 'K'
    for root in (o(44, 23), MIR(o(44, 23))):          # no line across a wing's root: it grows out of the thorax
        for (x, y) in thorax:
            if abs(x - root[0]) <= 2 and abs(y - root[1]) <= 2 and g[(x, y)] == 'K' and any((x + dx, y + e) in wings - thorax for dx in (-1, 0, 1) for e in (-1, 0, 1)):
                g[(x, y)] = 'L'
    for p in head: g[p] = 'G'
    for p in edge(head): g[p] = 'K'
    for p in eye & head: g[p] = 'R'
    for p in edge(eye) & head: g[p] = 'K'
    for p in needle: g[p] = 'b'                       # steel pale, for the same reason
    return g

IDLE = [front(142), front(172, dy=2), front(152), front(162, dy=1), front(182, dy=2, thrust=4)]
GRAB = [front(145, dy=2, legs_open=1.0, grab=True), front(175, dy=2, legs_open=0.5, grab=True),
        front(145, dy=2, legs_open=0.0, grab=True), front(175, dy=2, legs_open=0.5, grab=True)]
rows = lambda g: [''.join(g.get((x, y), '.') for x in range(W)) for y in range(H)]

if __name__ == '__main__':
    for name, fr in (('56_idle', IDLE), ('56_grab', GRAB)):
        json.dump({'pal': PAL, 'view_w': W, 'views': {str(i): rows(g) for i, g in enumerate(fr)}, 'order': [str(i) for i in range(len(fr))]}, open(name + '.json', 'w'))
    t = ['#PAL'] + [f'{k} {v}' for k, v in PAL.items()] + ['#BODY', '30', '#POSE', 'frames', '#DIRS', 'down']
    for i, g in enumerate(IDLE): t += ['#D' + ('@%d' % i if i else '')] + rows(g)[:-1]
    io.open('56_moskitto.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(t) + '\n')
    im = Image.new('RGBA', (W * 5, H * 2), (255, 170, 200, 255))
    for r, fr in enumerate((IDLE, GRAB)):
        for i, g in enumerate(fr):
            for (x, y), c in g.items(): im.putpixel((i * W + x, r * H + y), tuple(int(PAL[c][k:k + 2], 16) for k in (0, 2, 4)) + (255,))
    im.resize((im.width * 4, im.height * 4), Image.NEAREST).save('draft.png')
    ys = [y for g in IDLE + GRAB for x, y in g]; print('rows', min(ys), max(ys), 'colours', len({c for g in IDLE + GRAB for c in g.values()}))
